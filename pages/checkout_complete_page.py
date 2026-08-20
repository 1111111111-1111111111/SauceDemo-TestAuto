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
        # #47 修复：裸 wait.until 无重试 → 弹性 URL 等待
        self.wait_url_contains("checkout-complete")

    def get_complete_message(self) -> str:
        return self.get_text(self.COMPLETE_HEADER)

    def get_cart_badge_count(self) -> int:
        """获取购物车角标数量；badge 不存在（购物车为空）时返回 0。

        #47 修复：非阻塞即时读取（见 products_page.get_cart_badge_count 注释）。
        """
        eles = self.find_elements_immediate(self.SHOPPING_CART_BADGE)
        if not eles:
            return 0
        try:
            return int(eles[0].text)
        except ValueError:
            return 0

    def is_cart_reset(self) -> bool:
        """结账完成后购物车角标应消失（badge 不存在 = 已重置）"""
        return not self.find_elements_immediate(self.SHOPPING_CART_BADGE)

    def back_home(self) -> "ProductsPage":
        self.click(self.BACK_HOME_BTN, expect_url="inventory")
        # pageLoadStrategy=eager: URL 变更后等 React 渲染商品列表
        self.wait_element_present(
            (By.CSS_SELECTOR, "[data-test='inventory-list']"),
            desc="商品列表渲染完成",
        )
        from pages.products_page import ProductsPage  # 延迟导入
        return ProductsPage(self.driver)
