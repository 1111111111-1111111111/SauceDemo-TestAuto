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
        """点击商品标题 → 详情页（滚动可见 + 弹性等待 + JS 兜底）"""
        self._wait_until(
            lambda d: len(d.find_elements(*self.INVENTORY_ITEM_NAME)) > product_index,
            desc=f"商品列表就绪（≥{product_index + 1} 个标题）",
        )
        items = self.find_elements(self.INVENTORY_ITEM_NAME)
        ele = items[product_index]
        self.scroll_into_view(ele)
        try:
            ele.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", ele)
        from pages.product_detail_page import ProductDetailPage  # 延迟导入
        return ProductDetailPage(self.driver)

    def click_item_image(self, product_index: int) -> "ProductDetailPage":
        """点击商品图片 → 对应详情页

        CI 稳定性加固（#47 修复）：旧实现 6/6 失败——find_elements 只保证
        元素存在，不保证图片/父级链接可交互；且点击无滚动、无 JS 兜底、
        无重试。新实现：
          1. 弹性等待商品卡片就绪（≥ idx+1 个）
          2. 滚动到可视区域（避免懒加载/遮挡）
          3. 弹性等待父级 <a> 可点击（带重试）
          4. 点击失败自动 JS 兜底（React 事件冒泡可正常触发导航）
          5. ProductDetailPage.__init__ 内走弹性 URL 等待
        """
        self._wait_until(
            lambda d: len(d.find_elements(*self.INVENTORY_ITEMS)) > product_index,
            desc=f"商品列表就绪（≥{product_index + 1} 个卡片）",
        )
        items = self.find_elements(self.INVENTORY_ITEMS)
        card = items[product_index]
        self.scroll_into_view(card)
        img = card.find_element(By.CSS_SELECTOR, "img")
        link = img.find_element(By.XPATH, "./parent::a")
        try:
            ok = self._wait_until(
                EC.element_to_be_clickable(link),
                desc=f"商品 {product_index} 图片链接可点击",
            )
            if not ok:
                raise TimeoutException(f"商品 {product_index} 图片链接不可点击")
            link.click()
        except Exception:
            logger.warning(f"⚠️ 常规点击商品 {product_index} 图片失败，改用 JS 点击")
            self.driver.execute_script("arguments[0].click();", link)
        logger.info(f"🖱️ 已点击商品 {product_index} 的图片（父级链接）")
        from pages.product_detail_page import ProductDetailPage  # 延迟导入
        return ProductDetailPage(self.driver)

    def wait_cart_badge_count(self, expected: int, timeout: float = None) -> bool:
        """等待购物车角标数量达到预期（确保加购操作全部落盘、页面状态稳定）。

        CI 慢网络下连续 add-to-cart 后立刻点购物车图标，可能因最后一次加购
        的 DOM 更新尚未完成导致点击事件丢失/导航不触发；先确认角标再跳转
        可显著降低 go_to_cart 的 URL 等待超时概率。

        说明：get_cart_badge_count 已改为非阻塞即时读取，轮询由 WebDriverWait
        （poll_frequency=0.5s）驱动，等待精确且不浪费时间。
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
        self.wait_element_present((By.ID, "checkout"), desc="购物车页 checkout 按钮出现")
        from pages.cart_page import CartPage  # 延迟导入
        return CartPage(self.driver)

    def get_cart_badge_count(self) -> int:
        """获取购物车角标数量；角标不存在（购物车为空）时返回 0。

        #47 修复：改为非阻塞即时读取——旧实现 find_elements(timeout=1) 在
        CI 慢 DOM 更新下会读到过期 0 值导致角标断言误报；且每次轮询阻塞 1s
        拖慢 wait_cart_badge_count 的整体收敛速度。
        """
        eles = self.find_elements_immediate(self.SHOPPING_CART_BADGE)
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
