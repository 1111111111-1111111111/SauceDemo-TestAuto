# -*- coding: utf-8 -*-
"""
项目根 conftest.py
所有测试模块共享的 fixtures + Allure 钩子
设计：
  - 只保留 driver_instance（基础）和 login_page（简单页面对象）
  - 各测试模块通过 utils.app_flows 的 helper 函数按需组装前置条件
  - 好处：登录挂了只影响调了 quick_login 的模块，不再连锁失败 ~60 个用例
CI 稳定性治理（本版本新增）：
  - 会话开始时做一次网络诊断（DNS/TCP/TTFB），日志留痕
  - 每个用例计时，超过 SLOW_TEST_THRESHOLD 记 WARNING（慢用例 ≠ 失败用例）
  - 结束时输出最慢用例 Top 10 与整体耗时统计，便于 CI 排查超时
  - 失败时 attach 浏览器 console 日志，定位 JS 异常
"""
import os
import platform
import shutil
import time
from collections import OrderedDict

import allure
import pytest
from pytest import Item

from config.config import (
    BASE_URL,
    ALLURE_RESULTS_DIR,
    BROWSER,
    HEADLESS,
    LOG_DIR,
    SLOW_TEST_THRESHOLD,
)
from utils.driver import get_driver, kill_driver
from utils.helpers import take_screenshot, diagnose_network, format_duration
from utils.logger import logger
from pages.login_page import LoginPage


# ==================== 会话级：网络诊断 + 耗时统计 ====================
@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """会话开始时：记录起始时间 + 网络诊断（只做一次）"""
    session._wb_start_time = time.time()
    session._wb_test_durations = OrderedDict()
    logger.info("=" * 80)
    logger.info("🚀 测试会话开始")
    # CI 超时排查第一步：确认被测站点可达性
    diag = diagnose_network(BASE_URL)
    if not diag["ok"]:
        logger.warning(f"⚠️ 被测站点网络诊断未通过: {diag['error']}")


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """会话结束时：输出整体耗时统计 + 最慢用例 Top 10。

    稳定性治理：整个统计过程 try/except 兜底。
    原因：CI #43 曾出现"102 用例全过但 job 失败"，根因排查发现
    收尾阶段（sessionfinish）若抛异常会触发 pytest INTERNALERROR，
    pytest 退出码变 3，但 Allure 报告已生成完毕（全部 passed），
    造成"用例全过但流水线失败"的假象。收尾统计不得影响退出码。
    """
    try:
        elapsed = time.time() - getattr(session, "_wb_start_time", time.time())
        durations = getattr(session, "_wb_test_durations", {})
        logger.info("=" * 80)
        logger.info(f"📊 测试会话结束，总耗时 {format_duration(elapsed)}")
        if durations:
            total_case = sum(durations.values())
            logger.info(f"📊 用例执行总耗时（不含 fixture）: {format_duration(total_case)}")
            slowest = sorted(durations.items(), key=lambda kv: kv[1], reverse=True)[:10]
            logger.info("🐢 最慢用例 Top 10：")
            for name, dur in slowest:
                flag = " ⚠️超阈值" if dur > SLOW_TEST_THRESHOLD else ""
                logger.info(f"    {format_duration(dur):>10}  {name}{flag}")
        logger.info("=" * 80)
    except Exception as e:  # 收尾统计失败不影响 pytest 退出码
        logger.warning(f"⚠️ 会话统计输出异常（已忽略，不影响退出码）: {type(e).__name__}: {e}")


# ==================== 用例级：耗时监控 ====================
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """每个用例执行计时；超过 SLOW_TEST_THRESHOLD 记 WARNING。

    hookwrapper yield 之后的代码若抛异常，会覆盖用例原始结果
    （把"通过"改成"error"），因此整体 try/except 兜底。
    """
    t0 = time.time()
    outcome = yield
    try:
        elapsed = time.time() - t0
        session = item.session
        durations = getattr(session, "_wb_test_durations", None)
        if durations is not None:
            durations[item.nodeid] = elapsed
        if elapsed > SLOW_TEST_THRESHOLD:
            logger.warning(
                f"🐢 慢用例 [{format_duration(elapsed)} > 阈值 {format_duration(SLOW_TEST_THRESHOLD)}]: {item.nodeid}"
            )
            allure.attach(
                f"{format_duration(elapsed)}",
                name="test_duration",
                attachment_type=allure.attachment_type.TEXT,
            )
    except Exception as e:  # 计时/告警失败不影响用例结果
        logger.warning(f"⚠️ 用例计时记录异常（已忽略）: {type(e).__name__}: {e}")


# ==================== Driver Fixtures ====================
@pytest.fixture(scope="function")
def driver_instance():
    """每个测试函数一个全新的浏览器进程（隔离稳定）"""
    logger.info("=" * 80)
    logger.info("▶ 初始化 WebDriver")
    driver = get_driver()
    yield driver
    logger.info("◀ 清理 WebDriver")
    # 稳定性治理：teardown 异常不得传播——fixture teardown 抛异常会把用例
    # 标为 error，且可能连锁影响后续用例，导致"用例全过但退出码非 0"
    try:
        kill_driver(driver)
    except Exception as e:
        logger.warning(f"⚠️ 清理 WebDriver 异常（已忽略）: {type(e).__name__}: {e}")
    finally:
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
        f.write(f"URL={BASE_URL.rstrip('/')}\n")
        f.write("TestStack=Python+Pytest+Selenium+Allure\n")
        f.write(f"Python={platform.python_version()}\n")
        f.write(f"Platform={platform.system()} {platform.release()}\n")
        f.write(f"Browser={BROWSER}\n")
        f.write(f"Headless={HEADLESS}\n")


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


def _attach_browser_console_logs(driver):
    """失败诊断增强：抓取浏览器 console 日志（JS 异常/网络错误）"""
    try:
        logs = driver.get_log("browser")
        if logs:
            lines = [f"{l['level']} | {l['message']}" for l in logs[-50:]]
            allure.attach(
                "\n".join(lines),
                name="browser_console_logs",
                attachment_type=allure.attachment_type.TEXT,
            )
    except Exception:
        pass


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试结果写入 Allure + 失败自动截图"""
    outcome = yield  # 先包装，后释放
    try:
        rep = outcome.get_result()

        if rep.when in ("setup", "call") and rep.failed:
            driver = item.funcargs.get("driver_instance") or item.funcargs.get("driver_per_class")
            if driver is not None:
                # 稳定性治理：失败诊断增强 — 截图 + 当前URL + 页面源码 + console 日志
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
                _attach_browser_console_logs(driver)

        # 稳定性治理：仅失败用例 attach 日志尾部（而非每次 call 都 attach 完整日志）。
        # 旧逻辑 102 个用例 × 每次读整个 test_run.log（数 MB）→ allure-results 膨胀
        # 到数百 MB，收尾写入阶段可能触发 IO 异常 → INTERNALERROR → 退出码非 0，
        # 造成 "用例全过但流水线失败"（CI #43）。同时限 200KB 防止单附件过大。
        if rep.when == "call" and rep.failed:
            try:
                log_path = os.path.join(LOG_DIR, "test_run.log")
                if os.path.exists(log_path):
                    with open(log_path, "rb") as f:
                        content = f.read()
                    if len(content) > 200 * 1024:
                        content = content[-200 * 1024:]
                    allure.attach(
                        content,
                        name="full_log_tail",
                        attachment_type=allure.attachment_type.TEXT,
                    )
            except Exception as e:
                logger.warning(f"⚠️ attach 日志尾部失败（已忽略）: {type(e).__name__}: {e}")
    except Exception as e:  # hook 自身异常不得传播，避免用例被误标 error / INTERNALERROR
        logger.warning(f"⚠️ makereport 钩子异常（已忽略）: {type(e).__name__}: {e}")
