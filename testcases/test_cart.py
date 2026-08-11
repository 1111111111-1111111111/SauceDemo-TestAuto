# -*- coding: utf-8 -*-
"""
购物车页面测试

改造说明：
  - 不再依赖 cart_with_items / logged_in_products 链式 fixture
  - 使用本地 fixture + utils.app_flows helper 函数按需组装前置
  - 需要购物车的用例用 quick_setup_cart，只需要商品主页的用例用 quick_login
"""
import pytest

from utils.app_flows import quick_login, quick_setup_cart


@pytest.fixture()
def products_page(driver_instance):
    """本地 fixture：登录并返回商品主页"""
    return quick_login(driver_instance)


@pytest.fixture()
def cart_with_items(driver_instance):
    """本地 fixture：登录 → 加购 3 件 → 进购物车"""
    return quick_setup_cart(driver_instance, count=3)


@pytest.mark.cart
class TestCart:
    """购物车页面"""

    def test_cart_continue_shopping_back_to_products(self, cart_with_items):
        """点击 Continue Shopping → 返回主页继续购物"""
        cart = cart_with_items
        assert cart.get_item_count() == 3
        back = cart.continue_shopping()
        assert "inventory" in back.get_current_url()

    def test_cart_checkout_to_step_one(self, cart_with_items):
        """点击 Checkout → 进入结账流程 step one"""
        checkout = cart_with_items.checkout()
        assert "checkout-step-one" in checkout.get_current_url()

    @pytest.mark.parametrize("idx", range(6))
    def test_cart_remove_one_item(self, products_page, idx):
        """移除一个商品"""
        for i in range(6):
            products_page.add_to_cart_by_index(i)
        cart = products_page.go_to_cart()
        before = cart.get_item_count()
        cart.remove_item_by_index(idx)
        after = cart.get_item_count()
        assert after == before - 1

    def test_cart_remove_multiple_items(self, products_page):
        """移除多个商品"""
        for i in range(6):
            products_page.add_to_cart_by_index(i)
        cart = products_page.go_to_cart()
        cart.remove_item_by_index(0)
        cart.remove_item_by_index(0)
        cart.remove_item_by_index(0)
        assert cart.get_item_count() == 3

    def test_cart_remove_all_items(self, products_page):
        """移除全部商品"""
        for i in range(6):
            products_page.add_to_cart_by_index(i)
        cart = products_page.go_to_cart()
        cart.remove_all_items()
        assert cart.get_item_count() == 0

    @pytest.mark.parametrize("idx", range(6))
    def test_cart_click_item_to_detail(self, products_page, idx):
        """点击购物车商品标题 → 进入对应商品的详情页"""
        for i in range(6):
            products_page.add_to_cart_by_index(i)
        cart = products_page.go_to_cart()
        detail = cart.click_item_name(idx)
        assert detail.get_item_name() is not None
