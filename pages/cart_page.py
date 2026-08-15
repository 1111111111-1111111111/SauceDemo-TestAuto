# -*- coding: utf-8 -*-
"""
Cart Page
"""
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
        self.wait.until(EC.url_contains("cart"))

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
        # 短超时快速判空：remove_all_items 清空购物车后，最后一次轮询
        # 无需等满 EXPLICIT_WAIT（否则每个清空用例白等 10 秒）
        items = self.find_elements(self.CART_ITEM_NAME, timeout=2)
        return len(items)

    def remove_item_by_index(self, idx: int):
        items = self.find_elements(self.REMOVE_BTN_TPL)
        items[idx].click()

    def remove_all_items(self):
        while self.get_item_count() > 0:
            self.remove_item_by_index(0)

    def click_item_name(self, idx: int) -> "ProductDetailPage":
        names = self.find_elements(self.CART_ITEM_NAME)
        names[idx].click()
        from pages.product_detail_page import ProductDetailPage  # 延迟导入
        return ProductDetailPage(self.driver)

    def continue_shopping(self) -> "ProductsPage":
        self.click(self.CONTINUE_SHOPPING_BTN)
        self.wait.until(EC.url_contains("inventory"))
        # pageLoadStrategy=eager: URL 变更后等 React 渲染商品列表
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-test='inventory-list']")))
        from pages.products_page import ProductsPage  # 延迟导入
        return ProductsPage(self.driver)
        
    def checkout(self) -> "CheckoutStepOnePage":
        self.click(self.CHECKOUT_BTN)
        self.wait.until(EC.url_contains("checkout-step-one"))
        # pageLoadStrategy=eager: URL 变更后等 React 渲染表单
        self.wait.until(EC.presence_of_element_located((By.ID, "first-name")))
        from pages.checkout_step_one_page import CheckoutStepOnePage  # 延迟导入
        return CheckoutStepOnePage(self.driver)
