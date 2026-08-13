# -*- coding: utf-8 -*-
"""
高频业务流封装（Flow 层）
========================
用 helper 函数替代链式 fixture，让测试用例按需调用、按需组装前置条件。

设计原则：
  1. 每个函数只负责一条业务路径，返回目标 Page Object
  2. 不依赖任何 fixture，只接收 driver 参数
  3. 内部使用延迟导入，避免循环依赖
  4. 调用方（测试用例）自己决定用哪个 flow，而非被全局 fixture 链绑定

新方案：
  每个测试模块在本地 fixture 中调用 quick_xxx，只影响自己
"""
from config.config import BASE_URL, DEFAULT_USER, DEFAULT_PASSWORD
from utils.logger import logger


def quick_login(driver, user: str = DEFAULT_USER, pwd: str = DEFAULT_PASSWORD):
    """
    打开网站并登录，返回 ProductsPage。

    用法:
        products_page = quick_login(driver)
    """
    from pages.login_page import LoginPage
    login = LoginPage(driver)
    login.open_login(BASE_URL)
    logger.info(f"🔑 quick_login: user={user}")
    return login.login(user, pwd)


def quick_setup_cart(driver, count: int = 3):
    """
    登录 → 加购 N 件商品 → 进入购物车，返回 CartPage。

    用法:
        cart_page = quick_setup_cart(driver, count=3)
    """
    products = quick_login(driver)
    products.add_to_cart_random(count=count)
    logger.info(f"🛒 quick_setup_cart: 加购 {count} 件，进入购物车")
    return products.go_to_cart()


def quick_setup_checkout(driver, count: int = 3):
    """
    登录 → 加购 N 件 → 进购物车 → 点击 Checkout，返回 CheckoutStepOnePage。

    用法:
        checkout_page = quick_setup_checkout(driver, count=3)
    """
    cart = quick_setup_cart(driver, count=count)
    logger.info(f"💳 quick_setup_checkout: 进入结账 step one")
    return cart.checkout()


def quick_setup_step_two(driver, count: int = 3, first: str = "Test",
                         last: str = "User", postal: str = "12345"):
    """
    登录 → 加购 N 件 → 进购物车 → 结账 → 填写信息 → 返回 CheckoutStepTwoPage。

    用法:
        step_two = quick_setup_step_two(driver)
    """
    checkout = quick_setup_checkout(driver, count=count)
    logger.info(f"📋 quick_setup_step_two: 填写结账信息，进入 step two")
    return checkout.fill_information(first, last, postal)


def quick_setup_complete(driver, count: int = 3, first: str = "Test",
                         last: str = "User", postal: str = "12345"):
    """
    完整下单流程：登录 → 加购 → 结账 → 填信息 → Finish，返回 CheckoutCompletePage。

    用法:
        complete = quick_setup_complete(driver)
    """
    step_two = quick_setup_step_two(driver, count=count, first=first,
                                    last=last, postal=postal)
    logger.info(f"✅ quick_setup_complete: 点击 Finish 完成订单")
    return step_two.click_finish()
