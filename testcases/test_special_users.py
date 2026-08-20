# -*- coding: utf-8 -*-
"""
异常账户缺陷回归测试（对应 Excel SD-USERS-001 ~ SD-USERS-004）
============================================================
SauceDemo 提供了 4 种异常用户账户，每种账户都有特定的已知缺陷。
这些用例验证缺陷是否仍然存在（回归保护），如果缺陷被修复则用例应该失败。

异常用户清单：
  - problem_user:          商品图片加载异常
  - error_user:            加购操作异常（部分按钮点击无效）
  - visual_user:           页面布局错位（价格与商品不匹配）
  - performance_glitch_user: 排序加载速度慢

注意：
  - 这些用例标记为 @pytest.mark.flaky，因为 performance_glitch_user 的耗时不稳定
  - 用例优先级 P1（已知缺陷的回归验证）
"""
import time

import pytest
import allure

from config.config import BASE_URL
from pages.login_page import LoginPage
from pages.products_page import ProductsPage


def _login_as(driver, username, password="secret_sauce"):
    """辅助：用指定用户登录并返回 ProductsPage"""
    login_page = LoginPage(driver)
    login_page.open_login(BASE_URL)
    return login_page.login(username, password)


@allure.epic("SauceDemo 电商网站自动化测试")
@allure.feature("异常账户缺陷验证")
@pytest.mark.special_users
class TestSpecialUsers:
    """异常账户缺陷验证"""

    @allure.story("已知缺陷回归")
    @allure.title("problem_user 商品图片加载异常")
    @pytest.mark.flaky(reruns=2)
    def test_problem_user_images_broken(self, driver_instance):
        """SD-USERS-001：problem_user 商品图片加载异常
        Arrange: 用 problem_user 登录
        Act:     获取所有商品图片 src
        Assert:  至少 1 张图片 src 异常（包含 slug/404 或与 standard_user 不同）
        """
        products = _login_as(driver_instance, "problem_user")
        images = products.get_all_item_images()
        assert len(images) == 6
        # problem_user 的图片 src 中包含 "sl-404" 或链接异常
        broken = [img for img in images if "404" in img or "jpg-with-broken" in img]
        assert len(broken) > 0, "problem_user 应有图片加载异常，但所有图片 src 看起来正常"

    @allure.story("已知缺陷回归")
    @allure.title("error_user 加购操作异常")
    @pytest.mark.flaky(reruns=2)
    def test_error_user_add_to_cart_defect(self, driver_instance):
        """SD-USERS-002：error_user 加购操作异常
        Arrange: 用 error_user 登录
        Act:     逐个点击 6 件商品的 Add to Cart 按钮
        Assert:  至少 1 次点击后按钮状态未变化（加购失败）
        """
        from config.config import SHORT_WAIT
        products = _login_as(driver_instance, "error_user")
        failures = 0
        for i in range(6):
            before = products.get_cart_badge_count()
            try:
                products.add_to_cart_by_index(i)
            except Exception:
                failures += 1
                continue
            # #47 修复：短窗口弹性等待角标 +1，避免 CI 慢 DOM 更新下
            # 立即读取误判"缺陷不存在"（该用例本质是验证缺陷存在性）
            if not products.wait_cart_badge_count(before + 1, timeout=SHORT_WAIT * 4):
                failures += 1
        assert failures > 0, "error_user 应有加购异常，但所有加购操作均成功"

    @allure.story("已知缺陷回归")
    @allure.title("visual_user 页面布局错位")
    @pytest.mark.flaky(reruns=2)
    def test_visual_user_layout_mismatch(self, driver_instance):
        """SD-USERS-003：visual_user 页面布局错位
        Arrange: 用 visual_user 登录
        Act:     获取商品名称列表和价格列表
        Assert:  与 standard_user 的数据不一致（布局错位导致数据不匹配）
        """
        # 先用 standard_user 获取基准数据
        standard_products = _login_as(driver_instance, "standard_user")
        standard_names = standard_products.get_all_item_names()
        standard_prices = standard_products.get_all_item_prices()

        # 退出后用 visual_user 登录
        standard_products.logout()
        from config.config import EXPLICIT_WAIT
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(driver_instance, EXPLICIT_WAIT).until(
            EC.url_contains("saucedemo.com/")
        )

        visual_products = _login_as(driver_instance, "visual_user")
        visual_names = visual_products.get_all_item_names()
        visual_prices = visual_products.get_all_item_prices()

        # visual_user 的布局错位导致名称或价格与 standard 不一致
        names_mismatch = visual_names != standard_names
        prices_mismatch = visual_prices != standard_prices
        assert names_mismatch or prices_mismatch, (
            "visual_user 应有布局错位，但名称和价格与 standard_user 一致"
        )

    @allure.story("已知缺陷回归")
    @allure.title("performance_glitch_user 登录/页面加载速度慢")
    @pytest.mark.flaky(reruns=2)
    def test_performance_glitch_user_slow_login(self, driver_instance):
        """SD-USERS-004：performance_glitch_user 登录/页面加载缓慢
        Arrange: 打开登录页
        Act:     执行登录并等待 inventory 页面加载完成，全程计时
        Assert:  登录+加载耗时 > 1 秒（正常用户约 0.2s）

        修复说明：SauceDemo 的 performance_glitch_user 人为延迟注入在
        登录/页面加载环节（实测约 5s），前端排序操作本身不慢（实测 ~0.1s）。
        因此计时点从"排序操作"改为"登录 + inventory 页面加载"。
        """
        login_page = LoginPage(driver_instance)
        login_page.open_login(BASE_URL)
        start = time.time()
        products = login_page.login("performance_glitch_user", "secret_sauce")
        products.find_element(ProductsPage.SORT_DROPDOWN)  # 等 inventory 页面渲染完成
        elapsed = time.time() - start

        assert elapsed > 1.0, (
            f"performance_glitch_user 登录/加载耗时 {elapsed:.2f}s，"
            f"预期应 > 1.0s（正常用户 < 1.0s）"
        )
