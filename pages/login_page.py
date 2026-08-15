# -*- coding: utf-8 -*-
"""
Login Page
https://www.saucedemo.com/
"""
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage

if TYPE_CHECKING:
    from pages.products_page import ProductsPage


class LoginPage(BasePage):
    # ========== Locators ==========
    USERNAME_INPUT = (By.ID, "user-name")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.ID, "login-button")
    ERROR_CONTAINER = (By.CSS_SELECTOR, "[data-test='error']")
    ERROR_BUTTON = (By.CSS_SELECTOR, ".error-button")
    LOGO_IMG = (By.CSS_SELECTOR, ".login_logo")

    # ========== 操作 ==========
    def open_login(self, url: str):
        self.open(url)

    def input_username(self, username: str):
        self.input_text(self.USERNAME_INPUT, username)

    def input_password(self, password: str):
        self.input_text(self.PASSWORD_INPUT, password)

    def click_login_button(self):
        self.click(self.LOGIN_BUTTON)

    # ========== 便捷流程 ==========
    def login(self, username: str, password: str) -> "ProductsPage":
        """完整登录流程；登录成功返回 ProductsPage（链式）"""
        self.input_username(username)
        self.input_password(password)
        self.click_login_button()
        self.wait_url_contains("inventory")
        # pageLoadStrategy=eager: URL 变更后 React 可能尚未渲染，
        # 等待商品列表容器出现确保页面真正就绪
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-test='inventory-list']")))
        from pages.products_page import ProductsPage  # 延迟导入，打断循环
        return ProductsPage(self.driver)

    # ========== 断言辅助 ==========
    def get_error_message(self) -> str:
        return self.get_text(self.ERROR_CONTAINER)

    def is_at_login_page(self) -> bool:
        return "saucedemo.com" in self.get_current_url() and "/inventory" not in self.get_current_url()

    def login_expect_failure(self, username: str, password: str) -> str:
        """登录并预期失败，返回错误文案"""
        self.input_username(username)
        self.input_password(password)
        self.click_login_button()
        self.find_element(self.ERROR_CONTAINER)
        return self.get_error_message()

    def close_error(self):
        """关闭错误提示框（点击 × 按钮）"""
        self.click(self.ERROR_BUTTON)

    def is_error_displayed(self) -> bool:
        """错误提示框是否仍然可见（快速判断，不等待不截图）"""
        return bool(self.find_elements(self.ERROR_CONTAINER, timeout=1))

    def get_password_input_type(self) -> str:
        """获取密码输入框的 type 属性（验证掩码显示）"""
        return self.find_element(self.PASSWORD_INPUT).get_attribute("type")

    def get_username_value(self) -> str:
        """获取用户名输入框当前值"""
        return self.find_element(self.USERNAME_INPUT).get_attribute("value")

    def get_password_value(self) -> str:
        """获取密码输入框当前值"""
        return self.find_element(self.PASSWORD_INPUT).get_attribute("value")
