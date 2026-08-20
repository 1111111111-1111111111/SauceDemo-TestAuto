# -*- coding: utf-8 -*-
"""
商品主页测试（4 大模块之一）
1. 排序功能
2. 加入购物车
3. 移除购物车
4. 跳转详情页
5. 进入购物车页面
6. 退出登录

说明：
  - 使用本地 fixture + utils.app_flows.quick_login 按需组装前置
  - 登录失败只影响本模块，不连锁波及 cart / checkout
"""
import pytest
import allure

from data.test_data import SORT_OPTIONS, PRODUCTS
from utils.app_flows import quick_login


@pytest.fixture()
def products_page(driver_instance):
    """本地 fixture：登录并返回商品主页"""
    return quick_login(driver_instance)


@allure.epic("SauceDemo 电商网站自动化测试")
@allure.feature("商品管理")
@pytest.mark.products
class TestProducts:
    """商品主页"""

    # =========== 1. 排序功能 ===========
    @allure.story("排序功能")
    @allure.title("按商品名称 A→Z 排序")
    def test_sort_by_name_az(self, products_page):
        """Name (A to Z) 排序"""
        products_page.select_sort_option(SORT_OPTIONS["az"])
        names = products_page.get_all_item_names()
        assert names == sorted(names)

    @allure.story("排序功能")
    @allure.title("按商品名称 Z→A 排序")
    def test_sort_by_name_za(self, products_page):
        """Name (Z to A) 排序"""
        products_page.select_sort_option(SORT_OPTIONS["za"])
        names = products_page.get_all_item_names()
        assert names == sorted(names, reverse=True)

    @allure.story("排序功能")
    @allure.title("按价格低→高排序")
    def test_sort_by_price_lohi(self, products_page):
        """Price (low to high) 排序"""
        products_page.select_sort_option(SORT_OPTIONS["lohi"])
        prices = products_page.get_all_item_prices()
        assert prices == sorted(prices)

    @allure.story("排序功能")
    @allure.title("按价格高→低排序")
    def test_sort_by_price_hilo(self, products_page):
        """Price (high to low) 排序"""
        products_page.select_sort_option(SORT_OPTIONS["hilo"])
        prices = products_page.get_all_item_prices()
        assert prices == sorted(prices, reverse=True)

    # =========== 2. 加入购物车（每个商品一个 case）===========
    @allure.story("加入购物车")
    @allure.title("加入单个商品到购物车")
    @pytest.mark.parametrize("idx", range(6))
    def test_add_to_cart_each_product(self, products_page, idx):
        """每个商品一个用例：加入购物车"""
        before = products_page.get_cart_badge_count()
        products_page.add_to_cart_by_index(idx)
        # #47 修复：改为"先等待后断言"——旧实现立刻读角标，CI 慢 DOM 更新下
        # 读到过期 0 值导致误报 FAILED
        assert products_page.wait_cart_badge_count(before + 1), (
            f"加入购物车后角标应 +1（等待超时），实际 {before}→{products_page.get_cart_badge_count()}"
        )

    @allure.story("加入购物车")
    @allure.title("随机加入 3 件商品到购物车")
    def test_add_to_cart_random_multiple(self, products_page):
        """随机加购多个商品作为一个用例"""
        before = products_page.get_cart_badge_count()
        products_page.add_to_cart_random(count=3)
        assert products_page.wait_cart_badge_count(before + 3), (
            f"加购 3 件后角标应 +3（等待超时），实际 +{products_page.get_cart_badge_count() - before}"
        )

    # =========== 3. 移除购物车（基于已加购状态）===========
    @allure.story("移除购物车")
    @allure.title("从购物车移除单个商品")
    @pytest.mark.parametrize("idx", range(6))
    def test_remove_from_cart_each_product(self, products_page, idx):
        """每个商品一个用例：移除购物车"""
        for i in range(6):
            products_page.add_to_cart_by_index(i)
        assert products_page.wait_cart_badge_count(6), "预置加购 6 件超时"
        before = products_page.get_cart_badge_count()
        products_page.remove_from_cart_by_index(idx)
        # #47 修复：先等待后断言（同上）
        assert products_page.wait_cart_badge_count(before - 1), (
            f"移除 1 件后角标应 -1（等待超时），实际 {before}→{products_page.get_cart_badge_count()}"
        )

    @allure.story("移除购物车")
    @allure.title("从购物车随机移除 2 件商品")
    def test_remove_from_cart_random_multiple(self, products_page):
        """随机移除多个商品"""
        for i in range(6):
            products_page.add_to_cart_by_index(i)
        assert products_page.wait_cart_badge_count(6), "预置加购 6 件超时"
        before = products_page.get_cart_badge_count()
        products_page.remove_from_cart_random(count=2)
        assert products_page.wait_cart_badge_count(before - 2), (
            f"移除 2 件后角标应 -2（等待超时），实际 {before}→{products_page.get_cart_badge_count()}"
        )

    # =========== 4. 跳转商品详情页 ===========
    @allure.story("跳转详情页")
    @allure.title("点击商品标题进入详情页")
    @pytest.mark.parametrize("idx", range(6))
    def test_click_item_name_to_detail(self, products_page, idx):
        """点击商品标题 → 对应详情页"""
        detail = products_page.click_item_name(idx)
        assert "inventory-item" in detail.get_current_url()

    @allure.story("跳转详情页")
    @allure.title("点击商品图片进入详情页")
    @pytest.mark.parametrize("idx", range(6))
    def test_click_item_image_to_detail(self, products_page, idx):
        """点击商品图片 → 对应详情页"""
        detail = products_page.click_item_image(idx)
        assert "inventory-item" in detail.get_current_url()

    # =========== 5. 进入购物车 ===========
    @allure.story("进入购物车")
    @allure.title("点击购物车图标进入购物车页面")
    def test_navigate_to_cart(self, products_page):
        """点击购物车图标 → 进入购物车"""
        cart = products_page.go_to_cart()
        assert "cart" in cart.get_current_url()

    # =========== 6. 退出登录 ===========
    @allure.story("退出登录")
    @allure.title("点击 logout 回到登录页面")
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

    @allure.story("退出登录")
    @allure.title("退出后访问 inventory 重定向到登录页")
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
    @allure.story("商品信息与系统操作")
    @allure.title("商品信息完整性验证（图片/标题/描述/价格）")
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
    @allure.story("商品信息与系统操作")
    @allure.title("Reset App State 清空购物车")
    def test_reset_app_state_clears_cart(self, products_page):
        """SD-PRODUCT-013：Reset App State 功能验证
        Arrange: 登录并加购 3 件商品
        Act:     打开侧边栏菜单 → 点击 Reset App State
        Assert:  1. 购物车角标清零  2. 仍在商品列表页
        """
        products_page.add_to_cart_by_index(0)
        products_page.add_to_cart_by_index(1)
        products_page.add_to_cart_by_index(2)
        assert products_page.wait_cart_badge_count(3), "预置加购 3 件超时"

        products_page.reset_app_state()
        # #47 修复：先等待后断言——reset 后 React 重渲染需要时间
        assert products_page.wait_cart_badge_count(0), "Reset 后角标应清零（等待超时）"
        assert "inventory" in products_page.get_current_url()
