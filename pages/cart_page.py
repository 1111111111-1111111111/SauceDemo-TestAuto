# -*- coding: utf-8 -*-
"""
Cart Page
"""
import time
from typing import TYPE_CHECKING, List

from selenium.webdriver.common import window
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from utils.logger import logger

if TYPE_CHECKING:
    from pages.checkout_step_one_page import CheckoutStepOnePage
    from pages.product_detail_page import ProductDetailPage
    from pages.products_page import ProductsPage


class CartPage(BasePage):
    # ========== Locators ==========
    CONTINUE_SHOPPING_BTN = (By.ID, "continue-shopping")
    CHECKOUT_BTN = (By.ID, "checkout")
    CART_ITEM_NAME = (By.CSS_SELECTOR, "[data-test='inventory-item-name']")
    CART_ITEM_PRICE = (By.CSS_SELECTOR, "[data-test='inventory-item-price']")
    REMOVE_BTN_TPL = (By.CSS_SELECTOR, "button[data-test^='remove']")

    def __init__(self, driver):
        super().__init__(driver)
        # #47 修复：裸 wait.until 无重试 → 换弹性 wait_url_contains（NAV_WAIT × 重试）
        self.wait_url_contains("cart")

    # ========== 操作 ==========
    def get_item_names(self) -> List[str]:
        items = self.find_elements(self.CART_ITEM_NAME)
        return [it.text for it in items]

    def get_item_prices(self):
        import re
        items = self.find_elements(self.CART_ITEM_PRICE)
        prices = []
        for it in items:
            m = re.search(r"\d+\.?\d*", it.text)
            if m:
                prices.append(float(m.group()))
        return prices

    def get_item_count(self) -> int:
        # #47 修复：非阻塞即时读取。旧实现 find_elements(timeout=2) 每次轮询
        # 阻塞 2s 且 CI 下易读到中间态；remove_all_items 循环依赖该计数，
        # 阻塞读取会让"清空购物车"类用例整体变慢甚至超时。
        return len(self.find_elements_immediate(self.CART_ITEM_NAME))

    def remove_item_by_index(self, idx: int):
        """移除指定索引商品（滚动可见 + JS 兜底，#47 加固）"""
        items = self.find_elements(self.REMOVE_BTN_TPL)
        ele = items[idx]
        self.scroll_into_view(ele)
        try:
            ele.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", ele)

    def remove_all_items(self):
        """清空购物车：每轮先等 remove 按钮存在（React 重渲染竞态兜底），
        再点第一个 remove；移除后 DOM 更新需时间，轮询由计数驱动。
        """
        while len(self.find_elements_immediate(self.REMOVE_BTN_TPL)) > 0:
            self.remove_item_by_index(0)
            # 短停让 React 完成本轮 DOM 更新，避免 StaleElement 竞态
            time.sleep(0.3)

    def click_item_name(self, idx: int) -> "ProductDetailPage":
        """点击购物车商品标题 → 详情页（滚动可见 + JS 兜底，#47 加固）"""
        names = self.find_elements(self.CART_ITEM_NAME)
        ele = names[idx]
        self.scroll_into_view(ele)
        try:
            ele.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", ele)
        from pages.product_detail_page import ProductDetailPage  # 延迟导入
        return ProductDetailPage(self.driver)

    def continue_shopping(self) -> "ProductsPage":
        """返回商品主页（#47 修复：点击带 expect_url 弹性等待 + 等列表元素）"""
        self.click(self.CONTINUE_SHOPPING_BTN, expect_url="inventory")
        # pageLoadStrategy=eager: URL 变更后等 React 渲染商品列表
        self.wait_element_present(
            (By.CSS_SELECTOR, "[data-test='inventory-list']"),
            desc="商品列表渲染完成",
        )
        from pages.products_page import ProductsPage  # 延迟导入
        return ProductsPage(self.driver)

    def checkout(self) -> "CheckoutStepOnePage":
        self.click(self.CHECKOUT_BTN, expect_url="checkout-step-one")
        # pageLoadStrategy=eager: URL 变更后等 React 渲染表单
        self.wait_element_present((By.ID, "first-name"), desc="结账表单 first-name 出现")
        from pages.checkout_step_one_page import CheckoutStepOnePage  # 延迟导入
        return CheckoutStepOnePage(self.driver)
