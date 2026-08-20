# -*- coding: utf-8 -*-
"""
购物车页面测试

说明：
  - 使用本地 fixture + utils.app_flows helper 函数按需组装前置
  - 需要购物车的用例用 quick_setup_cart，只需要商品主页的用例用 quick_login
"""
import pytest
import allure

from utils.app_flows import quick_login, quick_setup_cart


@pytest.fixture()
def cart_with_items(driver_instance) -> "CartPage":
    """本地 fixture：登录 → 加购 6 件 → 进购物车

    返回类型注解：让 IDE 能推断 cart 是 CartPage，从而支持
    Ctrl+Enter 跳转到 continue_shopping() 等方法定义。
    """
    return quick_setup_cart(driver_instance, count=6)


@allure.epic("SauceDemo 电商网站自动化测试")
@allure.feature("购物车管理")
@pytest.mark.cart
class TestCart:
    """购物车页面"""

    @allure.story("跳转主页")
    @allure.title("Continue Shopping 返回主页")
    def test_cart_continue_shopping_back_to_products(self, cart_with_items):
        """点击 Continue Shopping → 返回主页继续购物"""
        cart = cart_with_items
        assert cart.get_item_count() == 6
        back = cart.continue_shopping()
        assert "inventory" in back.get_current_url()

    @allure.story("跳转结账页")
    @allure.title("Checkout 进入结账 Step One")
    def test_cart_checkout_to_step_one(self, cart_with_items):
        """点击 Checkout → 进入结账流程 step one"""
        checkout = cart_with_items.checkout()
        assert "checkout-step-one" in checkout.get_current_url()

    @allure.story("移除商品")
    @allure.title("购物车移除全部商品")
    def test_cart_remove_all_items(self, cart_with_items):
        """移除全部商品"""
        cart_with_items.remove_all_items()
        assert cart_with_items.get_item_count() == 0

    @allure.story("跳转详情页")
    @allure.title("点击购物车商品标题进入详情页")
    @pytest.mark.parametrize("idx", range(6))
    def test_cart_click_item_to_detail(self, cart_with_items, idx):
        """点击购物车商品标题 → 进入对应商品的详情页"""
        detail = cart_with_items.click_item_name(idx)
        assert detail.get_item_name() is not None
