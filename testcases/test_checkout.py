# -*- coding: utf-8 -*-
"""
结账流程测试（3 步）

说明：
  - 使用本地 fixture + utils.app_flows helper 函数按需组装前置
  - step one 用例用 quick_setup_checkout
  - step two / three 用例用 quick_setup_step_two / quick_setup_complete
  - 登录或加购失败只影响当前模块，不连锁波及其他模块
"""
import pytest
import allure

from data.test_data import CHECKOUT_INFO, CHECKOUT_ERRORS
from utils.app_flows import (
    quick_setup_cart,
    quick_setup_checkout,
    quick_setup_step_two,
    quick_setup_complete,
)


@pytest.fixture()
def cart_with_items(driver_instance):
    """本地 fixture：登录 → 加购 3 件 → 进购物车"""
    return quick_setup_cart(driver_instance, count=3)


@pytest.fixture()
def checkout_page(driver_instance):
    """本地 fixture：登录 → 加购 3 件 → 进购物车 → 点 Checkout"""
    return quick_setup_checkout(driver_instance, count=3)


@allure.epic("SauceDemo 电商网站自动化测试")
@allure.feature("结账流程")
@pytest.mark.checkout
class TestCheckout:
    """结账流程页面"""

    # =========== Step One：填写信息 ===========
    @allure.story("Step One 填写信息")
    @allure.title("Cancel 返回购物车")
    def test_step_one_cancel_back_to_cart(self, checkout_page):
        """Step one 点击 Cancel → 返回购物车"""
        cart = checkout_page.click_cancel()
        assert "cart" in cart.get_current_url()

    @allure.story("Step One 填写信息")
    @allure.title("完整信息填写成功进入 Step Two")
    def test_step_one_fill_information_success(self, checkout_page):
        """Step one 填写完整信息 → 进入 step two"""
        info = CHECKOUT_INFO["valid"]
        step_two = checkout_page.fill_information(
            info["first_name"], info["last_name"], info["postal_code"]
        )
        assert "checkout-step-two" in step_two.get_current_url()

    @allure.story("Step One 填写信息")
    @allure.title("First Name 为空校验")
    def test_step_one_empty_first_name(self, checkout_page):
        """First Name 空 → Error: First Name is required"""
        info = CHECKOUT_INFO["invalid"]
        checkout_page.input_last_name(info["last_name"])
        checkout_page.input_postal_code(info["postal_code"])
        checkout_page.click_continue()
        assert CHECKOUT_ERRORS["FIRST_NAME"] in checkout_page.get_error_message()

    @allure.story("Step One 填写信息")
    @allure.title("Last Name 为空校验")
    def test_step_one_empty_last_name(self, checkout_page):
        """Last Name 空 → Error: Last Name is required"""
        info = CHECKOUT_INFO["valid"]
        checkout_page.input_first_name(info["first_name"])
        checkout_page.input_postal_code(info["postal_code"])
        checkout_page.click_continue()
        assert CHECKOUT_ERRORS["LAST_NAME"] in checkout_page.get_error_message()

    @allure.story("Step One 填写信息")
    @allure.title("Zip/Postal Code 为空校验")
    def test_step_one_empty_postal_code(self, checkout_page):
        """Zip/Postal Code 空 → Error: Postal Code is required"""
        info = CHECKOUT_INFO["valid"]
        checkout_page.input_first_name(info["first_name"])
        checkout_page.input_last_name(info["last_name"])
        checkout_page.click_continue()
        assert CHECKOUT_ERRORS["POSTAL"] in checkout_page.get_error_message()

    @allure.story("Step One 填写信息")
    @allure.title("全部字段留空校验")
    def test_step_one_all_empty(self, checkout_page):
        """全部留空 → Error: First Name is required"""
        checkout_page.click_continue()
        assert CHECKOUT_ERRORS["FIRST_NAME"] in checkout_page.get_error_message()

    # =========== Step Two：核对账单 ===========
    @allure.story("Step Two 核对账单")
    @allure.title("Cancel 返回商品主页")
    def test_step_two_cancel_back_to_products(self, driver_instance):
        """Step two 点击 Cancel → 返回商品主页"""
        step_two = quick_setup_step_two(driver_instance)
        products = step_two.click_cancel()
        assert "inventory" in products.get_current_url()

    @allure.story("Step Two 核对账单")
    @allure.title("点击账单商品标题进入详情页")
    def test_step_two_click_item_name_to_detail(self, driver_instance):
        """Step two 点击账单商品标题 → 进入对应商品详情页"""
        step_two = quick_setup_step_two(driver_instance)
        first_name = step_two.get_item_names()[0]
        step_two.click_item_name(0)
        assert first_name in step_two.driver.page_source

    @allure.story("Step Two 核对账单")
    @allure.title("账单条目与购物车一致")
    def test_step_two_item_names_match_cart(self, driver_instance):
        """核对账单条目正确性（多商品）"""
        cart = quick_setup_cart(driver_instance, count=3)
        cart_names = cart.get_item_names()
        checkout = cart.checkout()
        info = CHECKOUT_INFO["valid"]
        step_two = checkout.fill_information(
            info["first_name"], info["last_name"], info["postal_code"]
        )
        assert step_two.get_item_names() == cart_names

    @allure.story("Step Two 核对账单")
    @allure.title("账单小计等于购物车商品总价")
    def test_step_two_total_price_correctness(self, driver_instance):
        """核对账单价格正确性"""
        cart = quick_setup_cart(driver_instance, count=3)
        cart_prices = cart.get_item_prices()
        checkout = cart.checkout()
        info = CHECKOUT_INFO["valid"]
        step_two = checkout.fill_information(
            info["first_name"], info["last_name"], info["postal_code"]
        )
        item_total = step_two.get_subtotal()
        expected = round(sum(cart_prices), 2)
        assert item_total == expected, f"账单小计 {item_total} ≠ 期望 {expected}"

    @allure.story("Step Two 核对账单")
    @allure.title("账单含税验证 (subtotal + tax = total)")
    def test_step_two_total_includes_tax(self, driver_instance):
        """账单含税：subtotal + tax = total（含一定四舍五入误差）"""
        step_two = quick_setup_step_two(driver_instance)
        sub = step_two.get_subtotal()
        tax = step_two.get_tax()
        tot = step_two.get_total()
        assert abs((sub + tax) - tot) < 0.05

    @allure.story("Step Two 核对账单")
    @allure.title("Finish 进入结账完成页")
    def test_step_two_finish_to_complete(self, driver_instance):
        """Step two Finish → 进入 step three（结账完毕）"""
        step_two = quick_setup_step_two(driver_instance)
        complete = step_two.click_finish()
        assert "checkout-complete" in complete.get_current_url()

    # =========== Step Three：结账完成 ===========
    @allure.story("Step Three 结账完成")
    @allure.title("Back Home 返回主页")
    def test_complete_back_home(self, driver_instance):
        """Step three 点击 Back Home → 返回主页"""
        complete = quick_setup_complete(driver_instance)
        products = complete.back_home()
        assert "inventory" in products.get_current_url()

    @allure.story("Step Three 结账完成")
    @allure.title("结账完成后购物车被重置")
    def test_complete_cart_is_reset(self, driver_instance):
        """结账完成后购物车被重置（角标消失）"""
        complete = quick_setup_complete(driver_instance)
        assert complete.is_cart_reset()
