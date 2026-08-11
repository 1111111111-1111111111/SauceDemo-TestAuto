# -*- coding: utf-8 -*-
"""
测试数据集中管理
支持 YAML、JSON、Python dict 三种方式
"""
# ======= 测试账号（与 SauceDemo 官方一致）=======
LOGIN_USERS = {
    "standard_user":          {"password": "secret_sauce", "expect_success": True},
    "problem_user":           {"password": "secret_sauce", "expect_success": True},
    "performance_glitch_user": {"password": "secret_sauce", "expect_success": True},
    "error_user":             {"password": "secret_sauce", "expect_success": True},
    "visual_user":            {"password": "secret_sauce", "expect_success": True},
    "locked_out_user":        {"password": "secret_sauce", "expect_success": False},
    "non_existing_user":      {"password": "secret_sauce", "expect_success": False},
}

# ======= 登录异常提示文案 =======
ERROR_MESSAGES = {
    "LOCKED_OUT":            "Epic sadface: Sorry, this user has been locked out.",
    "USERNAME_REQUIRED":     "Epic sadface: Username is required",
    "PASSWORD_REQUIRED":     "Epic sadface: Password is required",
    "NOT_MATCH":             "Epic sadface: Username and password do not match any user in this service",
}

# ======= SauceDemo 商品清单（6 个，按 A-Z）=======
PRODUCTS = [
    {"name": "Sauce Labs Backpack",  "price": 29.99},
    {"name": "Sauce Labs Bike Light", "price": 9.99},
    {"name": "Sauce Labs Bolt T-Shirt", "price": 15.99},
    {"name": "Sauce Labs Fleece Jacket", "price": 49.99},
    {"name": "Sauce Labs Onesie",     "price": 7.99},
    {"name": "Test.allTheThings() T-Shirt (Red)", "price": 15.99},
]

# ======= 结账校验信息 =======
CHECKOUT_INFO = {
    "valid":   {"first_name": "Test", "last_name": "User", "postal_code": "12345"},
    "invalid": {"first_name": "",     "last_name": "",     "postal_code": ""},
}

CHECKOUT_ERRORS = {
    "FIRST_NAME": "Error: First Name is required",
    "LAST_NAME":  "Error: Last Name is required",
    "POSTAL":     "Error: Postal Code is required",
}

# ======= 排序方式 =======
SORT_OPTIONS = {
    "az": "Name (A to Z)",
    "za": "Name (Z to A)",
    "lohi": "Price (low to high)",
    "hilo": "Price (high to low)",
}
