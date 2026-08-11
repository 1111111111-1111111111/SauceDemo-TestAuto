# -*- coding: utf-8 -*-
"""
Checkout Complete Page — 结账完成
"""
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage

if TYPE_CHECKING:
    from pages.products_page import ProductsPage


class CheckoutCompletePage(BasePage):
    COMPLETE_HEADER = (By.CSS_SELECTOR, "[data-test='complete-header']")
    COMPLETE_TEXT   = (By.CSS_SELECTOR, "[data-test='complete-text']")
    BACK_HOME_BTN   = (By.ID, "back-to-products")
    SHOPPING_CART_BADGE = (By.CSS_SELECTOR, "[data-test='shopping-cart-badge']")

    def __init__(self, driver):
        super().__init__(driver)
        self.wait.until(EC.url_contains("checkout-complete"))

    def get_complete_message(self) -> str:
        return self.get_text(self.COMPLETE_HEADER)

    def get_cart_badge_count(self) -> int:
        try:
            return int(self.get_text(self.SHOPPING_CART_BADGE))
        except Exception:
            return 0

    def is_cart_reset(self) -> bool:
        from selenium.common.exceptions import NoSuchElementException
        try:
            self.driver.find_element(*self.SHOPPING_CART_BADGE)
            return False
        except NoSuchElementException:
            return True

    def back_home(self) -> "ProductsPage":
        self.click(self.BACK_HOME_BTN)
        self.wait.until(EC.url_contains("inventory"))
        from pages.products_page import ProductsPage  # 延迟导入
        return ProductsPage(self.driver)
