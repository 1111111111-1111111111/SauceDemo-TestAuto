# -*- coding: utf-8 -*-
"""
Product Detail Page
"""
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By

from pages.base_page import BasePage

if TYPE_CHECKING:
    from pages.cart_page import CartPage
    from pages.products_page import ProductsPage


class ProductDetailPage(BasePage):
    # ========== Locators ==========
    BACK_BUTTON = (By.ID, "back-to-products")
    ADD_REMOVE_BUTTON = (By.CSS_SELECTOR, "button[data-test^='add-to-cart'], button[data-test^='remove']")
    SHOPPING_CART_LINK = (By.CSS_SELECTOR, "[data-test='shopping-cart-link']")
    SHOPPING_CART_BADGE = (By.CSS_SELECTOR, "[data-test='shopping-cart-badge']")
    ITEM_NAME = (By.CSS_SELECTOR, "[data-test='inventory-item-name']")
    ITEM_PRICE = (By.CSS_SELECTOR, "[data-test='inventory-item-price']")

    def __init__(self, driver):
        super().__init__(driver)
        from selenium.webdriver.support import expected_conditions as EC
        self.wait.until(EC.url_contains("inventory-item"))

    # ========== 操作 ==========
    def add_to_cart(self):
        btn = self.find_element(self.ADD_REMOVE_BUTTON)
        if "Add to cart" in btn.text:
            btn.click()
        else:
            btn.click()

    def remove_from_cart(self):
        btn = self.find_element(self.ADD_REMOVE_BUTTON)
        if "Remove" in btn.text:
            btn.click()
        else:
            btn.click()

    def back_to_products(self) -> "ProductsPage":
        self.click(self.BACK_BUTTON)
        from selenium.webdriver.support import expected_conditions as EC
        self.wait.until(EC.url_contains("inventory"))
        from pages.products_page import ProductsPage  # 延迟导入
        return ProductsPage(self.driver)

    def open_cart(self) -> "CartPage":
        """进入购物车页面"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        link = self.find_clickable_element(self.SHOPPING_CART_LINK)
        href = link.get_attribute("href")
        if href:
            self.driver.get(href)
        else:
            self.click(self.SHOPPING_CART_LINK)
        self.wait.until(EC.url_contains("cart"))
        self.wait.until(EC.presence_of_element_located((By.ID, "checkout")))
        from pages.cart_page import CartPage  # 延迟导入
        return CartPage(self.driver)

    def get_cart_badge_count(self) -> int:
        """获取购物车角标数量；badge 不存在（购物车为空）时返回 0。 """
        eles = self.find_elements(self.SHOPPING_CART_BADGE, timeout=1)
        if not eles:
            return 0
        try:
            return int(eles[0].text)
        except ValueError:
            return 0

    def get_item_name(self) -> str:
        return self.get_text(self.ITEM_NAME)

    def get_item_price(self) -> float:
        import re
        text = self.get_text(self.ITEM_PRICE)
        m = re.search(r"\d+\.?\d*", text)
        return float(m.group()) if m else 0.0
