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
        # #47 修复：裸 wait.until 无重试 → 弹性 URL 等待 + 弹性元素等待
        self.wait_url_contains("inventory-item")
        # pageLoadStrategy=eager: URL 变更后等 React 渲染商品名
        self.wait_element_present(self.ITEM_NAME, desc="详情页商品名出现")

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
        self.click(self.BACK_BUTTON, expect_url="inventory")
        # pageLoadStrategy=eager: URL 变更后等 React 渲染商品列表
        self.wait_element_present(
            (By.CSS_SELECTOR, "[data-test='inventory-list']"),
            desc="商品列表渲染完成",
        )
        from pages.products_page import ProductsPage  # 延迟导入
        return ProductsPage(self.driver)

    def open_cart(self) -> "CartPage":
        """进入购物车页面（#47 修复：弹性 URL 等待替代裸 wait）"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC

        link = self.find_clickable_element(self.SHOPPING_CART_LINK)
        href = link.get_attribute("href")
        if href:
            self.driver.get(href)
        else:
            self.click(self.SHOPPING_CART_LINK)
        self.wait_url_contains("cart")
        self.wait_element_present((By.ID, "checkout"), desc="购物车页 checkout 按钮出现")
        from pages.cart_page import CartPage  # 延迟导入
        return CartPage(self.driver)

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

    def get_item_name(self) -> str:
        return self.get_text(self.ITEM_NAME)

    def get_item_price(self) -> float:
        import re
        text = self.get_text(self.ITEM_PRICE)
        m = re.search(r"\d+\.?\d*", text)
        return float(m.group()) if m else 0.0
