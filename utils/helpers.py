# -*- coding: utf-8 -*-
"""
共用工具方法
"""
import os
import time
from functools import wraps

import allure
from selenium.common.exceptions import TimeoutException

from utils.logger import logger


def take_screenshot(driver, name: str = None) -> str:
    """
    截图并返回路径，可被 Allure attach
    """
    ts = time.strftime("%Y%m%d_%H%M%S")
    name = name or f"screenshot_{ts}"
    from config.config import SCREENSHOT_DIR
    file_path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    try:
        driver.save_screenshot(file_path)
        logger.info(f"📸 截图保存: {file_path}")
        # 附加到 Allure
        with open(file_path, "rb") as f:
            allure.attach(
                f.read(),
                name=name,
                attachment_type=allure.attachment_type.PNG,
            )
        return file_path
    except Exception as e:
        logger.error(f"截图失败: {e}")
        return ""


def allure_step(title: str):
    """Allure 步骤装饰器"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with allure.step(title):
                return func(*args, **kwargs)

        return wrapper

    return decorator
