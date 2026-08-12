# -*- coding: utf-8 -*-
"""
项目根 conftest.py
所有测试模块共享的 fixtures + Allure 钩子

设计：
  - 只保留 driver_instance（基础）和 login_page（简单页面对象）
  - 各测试模块通过 utils.app_flows 的 helper 函数按需组装前置条件
  - 好处：登录挂了只影响调了 quick_login 的模块，不再连锁失败 ~60 个用例
"""
import os
import shutil

import allure
import pytest
from pytest import Item

from config.config import (
    BASE_URL,
    ALLURE_RESULTS_DIR,
    LOG_DIR,
)
from utils.driver import get_driver, kill_driver
from utils.helpers import take_screenshot
from utils.logger import logger
from pages.login_page import LoginPage


# ==================== Driver Fixtures ====================
@pytest.fixture(scope="function")
def driver_instance():
    """每个测试函数一个全新的浏览器进程（隔离稳定）"""
    logger.info("=" * 80)
    logger.info("▶ 初始化 WebDriver")
    driver = get_driver()
    yield driver
    logger.info("◀ 清理 WebDriver")
    kill_driver(driver)
    logger.info("=" * 80)


@pytest.fixture(scope="class")
def driver_per_class(request):
    """类级别共享一个 driver，提升速度（按需使用）"""
    driver = get_driver()
    yield driver
    if not getattr(request, "param", False):
        kill_driver(driver)


# ==================== Page Object Fixtures ====================
@pytest.fixture()
def login_page(driver_instance):
    """只提供 LoginPage 对象，不执行登录。
    登录等业务前置由各测试模块通过 utils.app_flows 按需调用。
    """
    return LoginPage(driver_instance)


# ==================== Allure 测试信息 ====================
def pytest_configure(config):
    """初始化时调用：清空 allure-results"""
    if os.path.exists(ALLURE_RESULTS_DIR):
        shutil.rmtree(ALLURE_RESULTS_DIR, ignore_errors=True)
    os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)

    env_path = os.path.join(ALLURE_RESULTS_DIR, "environment.properties")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("TestTarget=SauceDemo\n")
        f.write("URL=https://www.saucedemo.com\n")
        f.write("TestStack=Python+Pytest+Selenium+Allure\n")
        f.write(f"Python={os.popen('python --version').read().strip() or 'unknown'}\n")


def pytest_sessionfinish(session, exitstatus):
    """测试结束时调用：可用于最终化报告等"""
    pass


# ==================== 测试方法钩子（标题 + 失败截图）====================
def pytest_itemcollected(item: Item):
    """每个用例的标题前缀，加上所属 Behaviors 故事点"""
    epic = "SauceDemo"
    feature = item.cls.__doc__ if (item.cls and item.cls.__doc__) else "Automation"
    story = item.function.__doc__ or item.name
    if epic:
        allure.dynamic.epic(epic)
    if feature:
        allure.dynamic.feature(feature.strip())
    if story:
        allure.dynamic.story(story.strip())
    allure.dynamic.title(item.name)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试结果写入 Allure + 失败自动截图"""
    outcome = yield  # 先包装，后释放
    rep = outcome.get_result()

    if rep.when in ("setup", "call") and rep.failed:
        driver = item.funcargs.get("driver_instance") or item.funcargs.get("driver_per_class")
        if driver is not None:
            # 稳定性治理：失败诊断增强 — 截图 + 当前URL + 页面源码
            try:
                take_screenshot(driver, name=f"{item.name}_{rep.when}_FAIL")
            except Exception as e:
                logger.warning(f"截图失败: {e}")
            try:
                allure.attach(
                    driver.current_url,
                    name="failure_url",
                    attachment_type=allure.attachment_type.TEXT,
                )
            except Exception:
                pass
            try:
                allure.attach(
                    driver.page_source,
                    name="page_source",
                    attachment_type=allure.attachment_type.HTML,
                )
            except Exception:
                pass

    if rep.when == "call":
        log_path = os.path.join(LOG_DIR, "test_run.log")
        if os.path.exists(log_path):
            with open(log_path, "rb") as f:
                allure.attach(
                    f.read(),
                    name="full_log",
                    attachment_type=allure.attachment_type.TEXT,
                )
