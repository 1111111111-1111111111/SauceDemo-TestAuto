# -*- coding: utf-8 -*-
"""
商品详情页测试

说明：
  - 使用本地 fixture + utils.app_flows.quick_login 按需组装前置
"""
import pytest
import allure

from utils.app_flows import quick_login
from utils.logger import logger


@pytest.fixture()
def products_page(driver_instance):
    """本地 fixture：登录并返回商品主页"""
    return quick_login(driver_instance)


@allure.epic("SauceDemo 电商网站自动化测试")
@allure.feature("商品详情")
@pytest.mark.product_detail
class TestProductDetail:
    """商品详情页面"""

    @allure.story("详情页加购")
    @allure.title("详情页加入购物车")
    @pytest.mark.parametrize("idx", range(6))
    def test_detail_add_to_cart(self, products_page, idx):
        """商品详情页加入购物车，购物车商品数目角标 + 1"""
        before = products_page.get_cart_badge_count()
        detail = products_page.click_item_name(idx)
        detail.add_to_cart()
        after = detail.get_cart_badge_count()
        assert after == before + 1, f"加购后角标应 {before + 1}，实际 {after}"

    @allure.story("详情页移除")
    @allure.title("详情页从购物车移除")
    @pytest.mark.parametrize("idx", range(6))  # 考虑原先购物车已加入 3 个商品
    def test_detail_remove_from_cart(self, products_page, idx):
        """商品详情页移除购物车，购物车商品数目角标 - 1"""
        detail = products_page.click_item_name(idx)
        detail.add_to_cart()
        before = products_page.get_cart_badge_count()
        # 购物车数量为 0,跳出测试
        if before == 0:
            pytest.skip(f"购物车为空，跳过测试（idx={idx}）")
        detail.remove_from_cart()
        after = detail.get_cart_badge_count()
        assert after == before - 1, f"加购后角标应 {before - 1}，实际 {after}"

    @allure.story("详情页导航")
    @allure.title("详情页返回商品列表")
    @pytest.mark.parametrize("idx", range(6))
    def test_detail_return_to_products(self, products_page, idx):
        """商品详情页返回所有商品页面"""
        detail = products_page.click_item_name(idx)
        back = detail.back_to_products()
        assert "inventory" in back.get_current_url()
        assert "inventory-item" not in back.get_current_url()

    @allure.story("详情页导航")
    @allure.title("详情页打开购物车页面")
    def test_detail_open_cart(self, products_page):
        """商品详情页打开购物车页面"""
        products_page.add_to_cart_by_index(0)
        products_page.add_to_cart_by_index(1)
        detail = products_page.click_item_name(0)
        cart = detail.open_cart()
        assert "cart" in cart.get_current_url()
        assert cart.get_item_count() == 2
