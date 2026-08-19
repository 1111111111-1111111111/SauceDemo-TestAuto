# -*- coding: utf-8 -*-
"""
共用工具方法
- 截图 / Allure 步骤装饰器
- 网络延迟诊断（CI 超时排查关键工具）
- 通用重试装饰器
- 用例耗时记录
"""
import os
import re
import time
from functools import wraps

import allure
from selenium.common.exceptions import TimeoutException

from utils.logger import logger


def safe_filename(name: str, max_len: int = 200) -> str:
    """Strip characters that are invalid in file names (esp. Windows)."""
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", name)
    return cleaned[:max_len] if cleaned else "screenshot"


def take_screenshot(driver, name: str = None) -> str:
    """
    截图并返回路径，可被 Allure attach
    """
    ts = time.strftime("%Y%m%d_%H%M%S")
    name = safe_filename(name or f"screenshot_{ts}")
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


# ==================== CI 超时诊断工具 ====================

def diagnose_network(url: str = "https://www.saucedemo.com/", timeout: float = 10.0) -> dict:
    """测量目标站点网络延迟（CI 超时排查第一步）。

    在测试会话开始时调用，输出 DNS/连接/TTFB 数据并写入日志，
    便于判断"测试超时是网络问题还是代码问题"。

    :return: {"ok": bool, "dns_ms": float, "connect_ms": float, "ttfb_ms": float, "error": str}
    """
    import socket
    import time as _t
    from urllib.parse import urlparse

    result = {"ok": False, "dns_ms": 0.0, "connect_ms": 0.0, "ttfb_ms": 0.0, "error": ""}
    host = urlparse(url).hostname or url

    # 1. DNS 解析
    t0 = _t.time()
    try:
        ip = socket.gethostbyname(host)
        result["dns_ms"] = round((_t.time() - t0) * 1000, 1)
    except Exception as e:
        result["error"] = f"DNS 解析失败: {e}"
        logger.error(f"🌐 网络诊断失败: {result['error']}")
        return result

    # 2. TCP 连接
    t0 = _t.time()
    try:
        with socket.create_connection((host, 443), timeout=timeout) as sock:
            result["connect_ms"] = round((_t.time() - t0) * 1000, 1)
    except Exception as e:
        result["error"] = f"TCP 连接失败({host}:443): {e}"
        logger.error(f"🌐 网络诊断失败: {result['error']}")
        return result

    # 3. HTTPS 请求（测 TTFB）
    t0 = _t.time()
    try:
        import requests
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        result["ttfb_ms"] = round((_t.time() - t0) * 1000, 1)
        result["ok"] = resp.status_code < 500
        result["status"] = resp.status_code
    except Exception as e:
        result["error"] = f"HTTPS 请求失败: {e}"
        result["ttfb_ms"] = round((_t.time() - t0) * 1000, 1)

    logger.info(
        f"🌐 网络诊断 {url}: DNS={result['dns_ms']}ms, "
        f"TCP连接={result['connect_ms']}ms, TTFB={result['ttfb_ms']}ms, "
        f"状态={'OK' if result['ok'] else result['error']}"
    )
    return result


def retry_on_exception(retries: int = 2, interval: float = 2.0, exceptions=Exception):
    """通用重试装饰器：捕获指定异常并按间隔重试。

    用法：
        @retry_on_exception(retries=2, interval=1.5)
        def unstable_api_call():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, retries + 2):  # 1 次原始 + retries 次重试
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt <= retries:
                        logger.warning(
                            f"🔄 {func.__name__} 第 {attempt}/{retries + 1} 次失败: "
                            f"{type(e).__name__}: {e}，{interval}s 后重试")
                        time.sleep(interval)
                    else:
                        logger.error(f"❌ {func.__name__} 重试 {retries} 次后仍失败")
            raise last_exc
        return wrapper
    return decorator


def record_duration(func):
    """装饰器：记录函数执行耗时到日志（慢操作定位用）"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - t0
        logger.info(f"⏱️ {func.__name__} 耗时 {elapsed:.2f}s")
        return result
    return wrapper


def format_duration(seconds: float) -> str:
    """秒 → 可读时长字符串（m:ss / s.ms）"""
    if seconds >= 60:
        return f"{int(seconds // 60)}m{int(seconds % 60):02d}s"
    return f"{seconds:.1f}s"
