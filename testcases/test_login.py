# -*- coding: utf-8 -*-
"""
登录模块测试（数据驱动改造版 + 边界用例补充）
================================
- 测试数据外置到 data/login.yaml，消除硬编码用户名
- 成功用例和异常用例分别从 YAML 加载，参数化生成
- 每条 case 带唯一 id，Allure 报告中清晰可辨
- 改造前：5 个成功用例硬编码 + 5 个异常用例各写一个函数
- 改造后：2 个参数化函数（10 条）+ 3 条边界用例，覆盖 Excel SD-LOGIN-013/014/015
"""
import pytest
import allure

from config.config import BASE_URL
from utils.data_loader import load_yaml
from pages.products_page import ProductsPage

LOGIN_DATA = load_yaml("login.yaml")
SUCCESS_CASES = LOGIN_DATA["login_success"]
FAILURE_CASES = LOGIN_DATA["login_failure"]


@allure.epic("SauceDemo 电商网站自动化测试")
@allure.feature("用户认证")
@pytest.mark.login
class TestLogin:
    """登录页面"""

    @allure.story("合法账号登录")
    @allure.title("合法账号登录 → 进入主页")
    @pytest.mark.parametrize(
        "case", SUCCESS_CASES, ids=[c["id"] for c in SUCCESS_CASES]
    )
    def test_login_success_with_valid_user(self, driver_instance, login_page, case):
        """数据驱动：输入合法账号 → 登录成功进入主页"""
        login_page.open_login(BASE_URL)
        products_page = login_page.login(case["username"], case["password"])
        assert isinstance(products_page, ProductsPage)
        assert "inventory" in products_page.get_current_url()
        assert products_page.get_title() == "Swag Labs"

    @allure.story("异常登录场景")
    @allure.title("异常登录 → 显示错误文案")
    @pytest.mark.parametrize(
        "case", FAILURE_CASES, ids=[c["id"] for c in FAILURE_CASES]
    )
    def test_login_fail(self, driver_instance, login_page, case):
        """数据驱动：异常登录 → 断言错误文案 + 仍在登录页"""
        login_page.open_login(BASE_URL)
        err = login_page.login_expect_failure(case["username"], case["password"])
        assert case["expect_error"] in err
        assert login_page.is_at_login_page()

    # ========== 边界用例（Excel SD-LOGIN-013/014/015 补充）==========
    @allure.story("边界场景")
    @allure.title("密码输入框掩码显示验证")
    def test_login_password_masked(self, driver_instance, login_page):
        """SD-LOGIN-015：密码输入框类型验证_掩码显示
        Arrange: 打开登录页
        Act:     在密码框输入任意内容
        Assert:  密码框 type 属性为 password（内容以掩码显示，不显示明文）
        """
        login_page.open_login(BASE_URL)
        login_page.input_password("secret_sauce")
        assert login_page.get_password_input_type() == "password"

    @allure.story("边界场景")
    @allure.title("错误提示框关闭按钮")
    def test_login_close_error_button(self, driver_instance, login_page):
        """SD-LOGIN-013：错误提示框的关闭功能_错误提示消失
        Arrange: 打开登录页，触发一个错误（密码为空）
        Act:     点击红色错误提示框右上角的 × 按钮
        Assert:  1. 错误提示框消失  2. 用户名输入框内容保留
        """
        login_page.open_login(BASE_URL)
        login_page.input_username("standard_user")
        login_page.login_expect_failure("standard_user", "")
        assert login_page.is_error_displayed()
        login_page.close_error()
        assert not login_page.is_error_displayed()
        assert login_page.get_username_value() == "standard_user"

    @allure.story("边界场景")
    @allure.title("未登录直接访问 inventory 重定向到登录页")
    def test_login_direct_access_inventory_redirects(self, driver_instance, login_page):
        """SD-LOGIN-014：未登录直接访问 inventory.html_重定向到登录页
        Arrange: 打开登录页（未登录状态）
        Act:     直接访问 /inventory.html
        Assert:  页面被重定向回登录页（URL 不含 inventory）
        """
        login_page.open_login(BASE_URL)
        driver_instance.get(BASE_URL + "/inventory.html")
        assert "/inventory" not in driver_instance.current_url
