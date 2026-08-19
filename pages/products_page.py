# -*- coding: utf-8 -*-
"""
Products Page（商品主页 / inventory.html）
"""
import re
from typing import TYPE_CHECKING, List

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from utils.logger import logger

if TYPE_CHECKING:
    from pages.cart_page import CartPage
    from pages.product_detail_page import ProductDetailPage


class ProductsPage(BasePage):
    # ========== Locators ==========
    SORT_DROPDOWN = (By.CSS_SELECTOR, "[data-test='product-sort-container']")
    TITLE_LABEL = (By.CSS_SELECTOR, "[data-test='title']")
    SHOPPING_CART_BADGE = (By.CSS_SELECTOR, "[data-test='shopping-cart-badge']")
    SHOPPING_CART_LINK = (By.CSS_SELECTOR, "[data-test='shopping-cart-link']")
    BURGER_MENU = (By.ID, "react-burger-menu-btn")
    LOGOUT_LINK = (By.ID, "logout_sidebar_link")
    RESET_LINK = (By.ID, "reset_sidebar_link")
    INVENTORY_ITEMS = (By.CSS_SELECTOR, "[data-test='inventory-item']")
    INVENTORY_ITEM_NAME = (By.CSS_SELECTOR, "[data-test='inventory-item-name']")
    INVENTORY_ITEM_PRICE = (By.CSS_SELECTOR, "[data-test='inventory-item-price']")
    INVENTORY_ITEM_DESC = (By.CSS_SELECTOR, "[data-test='inventory-item-desc']")
    INVENTORY_ITEM_IMG = (By.CSS_SELECTOR, "[data-test='inventory-item'] img")
    ADD_TO_CART_BTN = (By.CSS_SELECTOR, "button[data-test^='add-to-cart']")
    REMOVE_BTN = (By.CSS_SELECTOR, "button[data-test^='remove']")
    ABOUT_LINK = (By.ID, "about_sidebar_link")
    ALL_ITEMS_LINK = (By.ID, "inventory_sidebar_link")

    # ========== 操作 ==========
    def select_sort_option(self, visible_text: str):
        from selenium.webdriver.support.ui import Select
        ele = self.find_element(self.SORT_DROPDOWN)
        Select(ele).select_by_visible_text(visible_text)

    def get_all_item_names(self) -> List[str]:
        items = self.find_elements(self.INVENTORY_ITEM_NAME)
        return [it.text for it in items]

    def get_all_item_prices(self) -> List[float]:
        items = self.find_elements(self.INVENTORY_ITEM_PRICE)
        prices = []
        for it in items:
            m = re.search(r"\d+\.?\d*", it.text)
            if m:
                prices.append(float(m.group()))
        return prices

    def get_all_item_descriptions(self) -> List[str]:
        """获取所有商品描述文本"""
        items = self.find_elements(self.INVENTORY_ITEM_DESC)
        return [it.text for it in items]

    def get_all_item_images(self) -> List[str]:
        """获取所有商品图片 src 属性"""
        items = self.find_elements(self.INVENTORY_ITEM_IMG)
        return [it.get_attribute("src") for it in items]

    def get_product_button_id(self, product_index: int) -> str:
        items = self.find_elements(self.INVENTORY_ITEMS)
        if product_index >= len(items):
            raise IndexError("商品索引越界")
        btn = items[product_index].find_element(By.CSS_SELECTOR, "button[data-test^='add-to-cart']")
        return btn.get_attribute("data-test")

    def add_to_cart_by_index(self, product_index: int):
        items = self.find_elements(self.INVENTORY_ITEMS)
        btn = items[product_index].find_element(By.CSS_SELECTOR, "button[data-test^='add-to-cart']")
        btn.click()

    def remove_from_cart_by_index(self, product_index: int):
        items = self.find_elements(self.INVENTORY_ITEMS)
        btn = items[product_index].find_element(By.CSS_SELECTOR, "button[data-test^='remove']")
        btn.click()

    def add_to_cart_random(self, count: int = 3):
        import random
        indices = list(range(len(self.find_elements(self.INVENTORY_ITEMS))))
        random.shuffle(indices)
        for i in indices[:count]:
            self.add_to_cart_by_index(i)

    def remove_from_cart_random(self, count: int = 2):
        import random
        indices = list(range(len(self.find_elements(self.INVENTORY_ITEMS))))
        random.shuffle(indices)
        for i in indices[:count]:
            self.remove_from_cart_by_index(i)

    def click_item_name(self, product_index: int) -> "ProductDetailPage":
        items = self.find_elements(self.INVENTORY_ITEM_NAME)
        items[product_index].click()
        from pages.product_detail_page import ProductDetailPage  # 延迟导入
        return ProductDetailPage(self.driver)

    def click_item_image(self, product_index: int) -> "ProductDetailPage":
        """点击商品图片 → 对应详情页 """
        items = self.find_elements(self.INVENTORY_ITEMS)
        img = items[product_index].find_element(By.CSS_SELECTOR, "img")
        link = img.find_element(By.XPATH, "./parent::a")
        self.wait.until(EC.element_to_be_clickable(link)).click()
        logger.info(f"🖱️ 已点击商品 {product_index} 的图片（父级链接）")
        from pages.product_detail_page import ProductDetailPage  # 延迟导入
        return ProductDetailPage(self.driver)

    def wait_cart_badge_count(self, expected: int, timeout: float = None) -> bool:
        """等待购物车角标数量达到预期（确保加购操作全部落盘、页面状态稳定）。

        CI 慢网络下连续 add-to-cart 后立刻点购物车图标，可能因最后一次加购
        的 DOM 更新尚未完成导致点击事件丢失/导航不触发；先确认角标再跳转
        可显著降低 go_to_cart 的 URL 等待超时概率。
        """
        return self._wait_until(
            lambda d: self.get_cart_badge_count() == expected,
            timeout=timeout,
            desc=f"购物车角标数量 = {expected}",
        )

    def go_to_cart(self) -> "CartPage":
        """进入购物车页面"""
        # 稳定性（#44 修复）：click 传 expect_url 后内部走 wait_url_contains
        # 弹性等待（NAV_WAIT × RETRY_TIMES 次 + 截图诊断），替代原来的
        # 原生单次 self.wait.until —— CI 慢网络下一次性 20s 超时即 broken
        self.click(self.SHOPPING_CART_LINK, expect_url="cart")
        # pageLoadStrategy=eager: URL 变更后等 React 渲染购物车页关键元素
        # （CartPage.__init__ 也校验 URL，但元素等待确保页面真正就绪）
        self._wait_until(
            EC.presence_of_element_located((By.ID, "checkout")),
            desc="购物车页 checkout 按钮出现",
        )
        from pages.cart_page import CartPage  # 延迟导入
        return CartPage(self.driver)

    def get_cart_badge_count(self) -> int:
        """获取购物车角标数量；角标不存在（购物车为空）时返回 0。"""
        eles = self.find_elements(self.SHOPPING_CART_BADGE, timeout=1)
        if not eles:
            return 0
        try:
            return int(eles[0].text)
        except ValueError:
            return 0

    # ========== 登出 ==========
    def open_burger_menu(self):
        """打开左上角侧边栏菜单"""
        self.click(self.BURGER_MENU)
        self.find_clickable_element(self.LOGOUT_LINK)

    def reset_app_state(self):
        """点击侧边栏菜单的 Reset App State，重置购物车等状态"""
        self.open_burger_menu()
        self.click(self.RESET_LINK)

    def logout(self):
        self.open_burger_menu()
        self.click(self.LOGOUT_LINK)
