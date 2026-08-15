# -*- coding: utf-8 -*-
"""
Checkout Step Two — 核对账单
"""
import re
from typing import TYPE_CHECKING, List

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage

if TYPE_CHECKING:
    from pages.checkout_complete_page import CheckoutCompletePage
    from pages.products_page import ProductsPage


class CheckoutStepTwoPage(BasePage):
    SUMMARY_SUBTOTAL = (By.CSS_SELECTOR, "[data-test='subtotal-label']")
    SUMMARY_TAX      = (By.CSS_SELECTOR, "[data-test='tax-label']")
    SUMMARY_TOTAL    = (By.CSS_SELECTOR, "[data-test='total-label']")
    CART_ITEM_NAME   = (By.CSS_SELECTOR, "[data-test='inventory-item-name']")
    CART_ITEM_PRICE  = (By.CSS_SELECTOR, "[data-test='inventory-item-price']")
    FINISH_BTN       = (By.ID, "finish")
    CANCEL_BTN       = (By.ID, "cancel")

    def __init__(self, driver):
        super().__init__(driver)
        self.wait.until(EC.url_contains("checkout-step-two"))

    # ========== 操作 ==========
    def get_subtotal(self) -> float:
        text = self.get_text(self.SUMMARY_SUBTOTAL)
        m = re.search(r"\d+\.?\d*", text)
        return float(m.group()) if m else 0.0

    def get_tax(self) -> float:
        text = self.get_text(self.SUMMARY_TAX)
        m = re.search(r"\d+\.?\d*", text)
        return float(m.group()) if m else 0.0

    def get_total(self) -> float:
        text = self.get_text(self.SUMMARY_TOTAL)
        m = re.search(r"\d+\.?\d*", text)
        return float(m.group()) if m else 0.0

    def get_item_names(self) -> List[str]:
        items = self.find_elements(self.CART_ITEM_NAME)
        return [it.text for it in items]

    def get_item_prices(self) -> List[float]:
        items = self.find_elements(self.CART_ITEM_PRICE)
        prices = []
        for it in items:
            m = re.search(r"\d+\.?\d*", it.text)
            if m:
                prices.append(float(m.group()))
        return prices

    def click_item_name(self, idx: int):
        names = self.find_elements(self.CART_ITEM_NAME)
        names[idx].click()

    def click_finish(self) -> "CheckoutCompletePage":
        self.click(self.FINISH_BTN)
        self.wait.until(EC.url_contains("checkout-complete"))
        # pageLoadStrategy=eager: URL 变更后等 React 渲染完成页
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-test='complete-header']")))
        from pages.checkout_complete_page import CheckoutCompletePage  # 延迟导入
        return CheckoutCompletePage(self.driver)

    def click_cancel(self) -> "ProductsPage":
        self.click(self.CANCEL_BTN)
        self.wait.until(EC.url_contains("inventory"))
        # pageLoadStrategy=eager: URL 变更后等 React 渲染商品列表
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-test='inventory-list']")))
        from pages.products_page import ProductsPage  # 延迟导入
        return ProductsPage(self.driver)
