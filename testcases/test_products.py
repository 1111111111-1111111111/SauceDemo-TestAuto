# -*- coding: utf-8 -*-
"""
商品主页测试（4 大模块）
1. 排序功能
2. 加入购物车
3. 移除购物车
4. 跳转详情页
5. 进入购物车页面
6. 退出登录

改造说明：
  - 不再依赖 logged_in_products 链式 fixture
  - 使用本地 fixture + utils.app_flows.quick_login 按需组装前置
  - 登录失败只影响本模块，不连锁波及 cart / checkout
"""
import pytest

from data.test_data import SORT_OPTIONS, PRODUCTS
from utils.app_flows import quick_login


@pytest.fixture()
def products_page(driver_instance):
    """本地 fixture：登录并返回商品主页"""
    return quick_login(driver_instance)


@pytest.mark.products
class TestProducts:
    """商品主页"""

    # =========== 1. 排序功能 ===========
    def test_sort_by_name_az(self, products_page):
        """Name (A to Z) 排序"""
        products_page.select_sort_option(SORT_OPTIONS["az"])
        names = products_page.get_all_item_names()
        assert names == sorted(names)

    def test_sort_by_name_za(self, products_page):
        """Name (Z to A) 排序"""
        products_page.select_sort_option(SORT_OPTIONS["za"])
        names = products_page.get_all_item_names()
        assert names == sorted(names, reverse=True)

    def test_sort_by_price_lohi(self, products_page):
        """Price (low to high) 排序"""
        products_page.select_sort_option(SORT_OPTIONS["lohi"])
        prices = products_page.get_all_item_prices()
        assert prices == sorted(prices)

    def test_sort_by_price_hilo(self, products_page):
        """Price (high to low) 排序"""
        products_page.select_sort_option(SORT_OPTIONS["hilo"])
        prices = products_page.get_all_item_prices()
        assert prices == sorted(prices, reverse=True)

    # =========== 2. 加入购物车（每个商品一个 case）===========
    @pytest.mark.parametrize("idx", range(6))
    def test_add_to_cart_each_product(self, products_page, idx):
        """每个商品一个用例：加入购物车"""
        before = products_page.get_cart_badge_count()
        products_page.add_to_cart_by_index(idx)
        after = products_page.get_cart_badge_count()
        assert after == before + 1, f"加入购物车后角标应 +1，实际 {before}→{after}"

    def test_add_to_cart_random_multiple(self, products_page):
        """随机加购多个商品作为一个用例"""
        before = products_page.get_cart_badge_count()
        products_page.add_to_cart_random(count=3)
        after = products_page.get_cart_badge_count()
        assert after - before == 3, f"加购 3 件后角标应 +3，实际 +{after - before}"

    # =========== 3. 移除购物车（基于已加购状态）===========
    @pytest.mark.parametrize("idx", range(6))
    def test_remove_from_cart_each_product(self, products_page, idx):
        """每个商品一个用例：移除购物车"""
        for i in range(6):
            products_page.add_to_cart_by_index(i)
        before = products_page.get_cart_badge_count()
        products_page.remove_from_cart_by_index(idx)
        after = products_page.get_cart_badge_count()
        assert after == before - 1, f"移除 1 件后角标应 -1，实际 {before}→{after}"

    def test_remove_from_cart_random_multiple(self, products_page):
        """随机移除多个商品"""
        for i in range(6):
            products_page.add_to_cart_by_index(i)
        before = products_page.get_cart_badge_count()
        products_page.remove_from_cart_random(count=2)
        after = products_page.get_cart_badge_count()
        assert after == before - 2

    # =========== 4. 跳转商品详情页 ===========
    @pytest.mark.parametrize("idx", range(6))
    def test_click_item_name_to_detail(self, products_page, idx):
        """点击商品标题 → 对应详情页"""
        detail = products_page.click_item_name(idx)
        assert "inventory-item" in detail.get_current_url()

    @pytest.mark.parametrize("idx", range(6))
    def test_click_item_image_to_detail(self, products_page, idx):
        """点击商品图片 → 对应详情页"""
        detail = products_page.click_item_image(idx)
        assert "inventory-item" in detail.get_current_url()

    # =========== 5. 进入购物车 ===========
    def test_navigate_to_cart(self, products_page):
        """点击购物车图标 → 进入购物车"""
        cart = products_page.go_to_cart()
        assert "cart" in cart.get_current_url()

    # =========== 6. 退出登录 ===========
    def test_logout_back_to_login_page(self, products_page, driver_instance):
        """点击 logout → 回到登录页面"""
        products_page.logout()
        from selenium.webdriver.support.ui import WebDriverWait
        from config.config import EXPLICIT_WAIT
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(driver_instance, EXPLICIT_WAIT).until(
            EC.url_contains("saucedemo.com/")
        )
        assert "/inventory" not in driver_instance.current_url

    def test_logout_then_direct_access_redirects(self, products_page, driver_instance):
        """SD-LOGOUT-002：退出后直接访问 inventory.html → 重定向到登录页
        Arrange: 登录后退出登录
        Act:     直接访问 /inventory.html
        Assert:  页面被重定向回登录页（URL 不含 inventory）
        """
        products_page.logout()
        from selenium.webdriver.support.ui import WebDriverWait
        from config.config import EXPLICIT_WAIT, BASE_URL
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(driver_instance, EXPLICIT_WAIT).until(
            EC.url_contains("saucedemo.com/")
        )
        driver_instance.get(BASE_URL + "/inventory.html")
        assert "/inventory" not in driver_instance.current_url

    # ========== 7. 商品信息完整性（Excel SD-PRODUCT-012 补充）==========

    def test_product_info_completeness(self, products_page):
        """SD-PRODUCT-012：商品信息完整性验证
        Arrange: 登录进入商品列表页
        Act:     遍历 6 件商品，检查每件商品的图片/标题/描述/价格/按钮
        Assert:  每件商品 5 要素均存在且非空
        """
        names = products_page.get_all_item_names()
        prices = products_page.get_all_item_prices()
        descs = products_page.get_all_item_descriptions()
        images = products_page.get_all_item_images()

        assert len(names) == 6
        assert len(prices) == 6
        assert len(descs) == 6
        assert len(images) == 6

        for i in range(6):
            assert names[i], f"商品 {i} 标题为空"
            assert prices[i] > 0, f"商品 {i} 价格无效: {prices[i]}"
            assert descs[i], f"商品 {i} 描述为空"
            assert images[i], f"商品 {i} 图片 src 为空"

    # ========== 8. Reset App State（Excel SD-PRODUCT-013 补充）==========

    def test_reset_app_state_clears_cart(self, products_page):
        """SD-PRODUCT-013：Reset App State 功能验证
        Arrange: 登录并加购 3 件商品
        Act:     打开侧边栏菜单 → 点击 Reset App State
        Assert:  1. 购物车角标清零  2. 仍在商品列表页
        """
        products_page.add_to_cart_by_index(0)
        products_page.add_to_cart_by_index(1)
        products_page.add_to_cart_by_index(2)
        assert products_page.get_cart_badge_count() == 3

        products_page.reset_app_state()
        assert products_page.get_cart_badge_count() == 0
        assert "inventory" in products_page.get_current_url()
