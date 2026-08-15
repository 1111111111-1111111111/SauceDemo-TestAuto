# -*- coding: utf-8 -*-
"""
Checkout Step One — 填写信息
"""
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage

if TYPE_CHECKING:
    from pages.cart_page import CartPage
    from pages.checkout_step_two_page import CheckoutStepTwoPage


class CheckoutStepOnePage(BasePage):
    FIRST_NAME_INPUT  = (By.ID, "first-name")
    LAST_NAME_INPUT   = (By.ID, "last-name")
    POSTAL_CODE_INPUT = (By.ID, "postal-code")
    CONTINUE_BTN      = (By.ID, "continue")
    CANCEL_BTN        = (By.ID, "cancel")
    ERROR_CONTAINER   = (By.CSS_SELECTOR, "[data-test='error']")

    def __init__(self, driver):
        super().__init__(driver)
        self.wait.until(EC.url_contains("checkout-step-one"))

    # ========== 操作 ==========
    def input_first_name(self, v: str):
        self.input_text(self.FIRST_NAME_INPUT, v)

    def input_last_name(self, v: str):
        self.input_text(self.LAST_NAME_INPUT, v)

    def input_postal_code(self, v: str):
        self.input_text(self.POSTAL_CODE_INPUT, v)

    def click_continue(self):
        self.click(self.CONTINUE_BTN)

    def click_cancel(self) -> "CartPage":
        self.click(self.CANCEL_BTN)
        self.wait.until(EC.url_contains("cart"))
        # pageLoadStrategy=eager: URL 变更后等 React 渲染购物车页
        self.wait.until(EC.presence_of_element_located((By.ID, "checkout")))
        from pages.cart_page import CartPage  # 延迟导入
        return CartPage(self.driver)

    def get_error_message(self) -> str:
        return self.get_text(self.ERROR_CONTAINER)

    def fill_information(self, first: str, last: str, postal: str) -> "CheckoutStepTwoPage":
        self.input_first_name(first)
        self.input_last_name(last)
        self.input_postal_code(postal)
        self.click_continue()
        self.wait.until(EC.url_contains("checkout-step-two"))
        # pageLoadStrategy=eager: URL 变更后等 React 渲染账单汇总
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-test='subtotal-label']")))
        from pages.checkout_step_two_page import CheckoutStepTwoPage  # 延迟导入
        return CheckoutStepTwoPage(self.driver)
