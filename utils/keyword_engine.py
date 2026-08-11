# -*- coding: utf-8 -*-
"""
关键字驱动引擎（Keyword-Driven Testing）
==========================================
将测试步骤外置为 YAML，引擎解析后调用 Page Object 层执行。

适用场景：
  - 冒烟测试 / 回归测试的可视化用例
  - 非技术同学可读、可改的用例描述
  - 不替代 PO + pytest 代码测试，是其补充层

支持的关键字：
  - open: 打开 URL
  - input: 在指定 page 的 locator 输入 text
  - click: 点击指定 page 的 locator
  - assert_url_contains: 断言当前 URL 含 text
  - assert_title: 断言页面标题等于 text
  - assert_text_visible: 断言指定 locator 元素可见
  - wait_url_contains: 等待 URL 含 text

YAML 格式：
  testcase: "用例名称"
  steps:
    - keyword: open
      url: "https://..."
    - keyword: input
      page: login
      locator: USERNAME_INPUT
      text: "standard_user"
"""
import importlib
from typing import Any, Dict, List

import allure

from utils.data_loader import load_yaml
from utils.logger import logger


class KeywordEngine:
    """关键字驱动引擎"""

    # page 名称 → PO 类的完整路径（延迟导入，避免循环依赖）
    PAGE_MODULE_MAP = {
        "login": "pages.login_page.LoginPage",
        "products": "pages.products_page.ProductsPage",
        "product_detail": "pages.product_detail_page.ProductDetailPage",
        "cart": "pages.cart_page.CartPage",
        "checkout_step_one": "pages.checkout_step_one_page.CheckoutStepOnePage",
        "checkout_step_two": "pages.checkout_step_two_page.CheckoutStepTwoPage",
        "checkout_complete": "pages.checkout_complete_page.CheckoutCompletePage",
    }

    def __init__(self, driver):
        self.driver = driver
        # 用 BasePage 做通用操作包装（复用显式等待、日志、截图）
        from pages.base_page import BasePage
        self._base = BasePage(driver)

    def _get_locator(self, page_name: str, locator_name: str):
        """从 PO 类属性获取定位器元组（locator_name 须与 PO 类常量名一致）"""
        if page_name not in self.PAGE_MODULE_MAP:
            raise ValueError(f"未注册的 page: {page_name}")
        module_path = self.PAGE_MODULE_MAP[page_name]
        module = importlib.import_module(".".join(module_path.split(".")[:-1]))
        cls = getattr(module, module_path.split(".")[-1])
        if not hasattr(cls, locator_name):
            raise AttributeError(f"{page_name} 页面无定位器 {locator_name}")
        return getattr(cls, locator_name)

    def run_step(self, step: Dict[str, Any]):
        """执行单个关键字步骤"""
        kw = step["keyword"]
        logger.info(f"▶ 关键字: {kw} | {step}")

        if kw == "open":
            self.driver.get(step["url"])

        elif kw == "input":
            locator = self._get_locator(step["page"], step["locator"])
            self._base.input_text(locator, step["text"])

        elif kw == "click":
            locator = self._get_locator(step["page"], step["locator"])
            self._base.click(locator)

        elif kw == "assert_url_contains":
            assert step["text"] in self.driver.current_url, (
                f"断言失败: URL 应含 '{step['text']}'，实际: {self.driver.current_url}"
            )

        elif kw == "assert_title":
            assert self.driver.title == step["text"], (
                f"断言失败: 标题应为 '{step['text']}'，实际: {self.driver.title}"
            )

        elif kw == "assert_text_visible":
            locator = self._get_locator(step["page"], step["locator"])
            self._base.find_element(locator)

        elif kw == "wait_url_contains":
            self._base.wait_url_contains(step["text"])

        else:
            raise ValueError(f"不支持的关键字: {kw}（可在 run_step 中扩展）")

    def run_testcase(self, yaml_file: str):
        """加载 YAML 用例并顺序执行所有步骤"""
        data = load_yaml(yaml_file)
        testcase_name = data.get("testcase", yaml_file)
        steps: List[Dict[str, Any]] = data["steps"]

        logger.info(f"🏷️ 关键字用例: {testcase_name}，共 {len(steps)} 步")
        with allure.step(f"关键字用例: {testcase_name}"):
            for i, step in enumerate(steps, 1):
                with allure.step(f"步骤 {i}/{len(steps)}: {step['keyword']}"):
                    self.run_step(step)
        logger.info(f"✅ 关键字用例通过: {testcase_name}")
