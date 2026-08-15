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
        """获取购物车角标数量；badge 不存在（购物车为空）时返回 0。"""
        eles = self.find_elements(self.SHOPPING_CART_BADGE, timeout=1)
        if not eles:
            return 0
        try:
            return int(eles[0].text)
        except ValueError:
            return 0

    def is_cart_reset(self) -> bool:
        """结账完成后购物车角标应消失（badge 不存在 = 已重置）"""
        return not self.find_elements(self.SHOPPING_CART_BADGE, timeout=1)

    def back_home(self) -> "ProductsPage":
        self.click(self.BACK_HOME_BTN)
        self.wait.until(EC.url_contains("inventory"))
        # pageLoadStrategy=eager: URL 变更后等 React 渲染商品列表
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-test='inventory-list']")))
        from pages.products_page import ProductsPage  # 延迟导入
        return ProductsPage(self.driver)
