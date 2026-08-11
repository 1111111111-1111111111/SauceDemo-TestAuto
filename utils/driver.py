# -*- coding: utf-8 -*-
"""
浏览器驱动工厂
- Selenium 4.x：使用 service=Service(executable_path=...)，废弃的 executable_path 参数已弃用
- 通过 selenium-manager（Selenium 4.10+ 自带）或 webdriver-manager 解决驱动版本匹配
- 支持 chrome / firefox / edge
- 容器友好：自动判断 /dev/shm 较小时启用 --disable-dev-shm-usage
"""


import os
import platform
import shutil

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService

# 设置 webdriver-manager 使用国内镜像
os.environ["WDM_SSL_VERIFY"] = "0"  # 关闭 SSL 验证（可选）

try:
    # 推荐：自动下载匹配浏览器版本的 driver
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    HAS_WDM = True
except ImportError:
    HAS_WDM = False

from config.config import (
    BROWSER,
    HEADLESS,
    WINDOW_SIZE,
    CHROME_DRIVER_PATH,
    PAGE_LOAD_TIMEOUT,
    IMPLICIT_WAIT,
)
from utils.logger import logger


def _is_container() -> bool:
    """是否运行在容器内（Docker / CI）"""
    if os.path.exists("/.dockerenv"):
        return True
    if os.environ.get("CONTAINER") in ("1", "true", "yes"):
        return True
    # GitHub Actions / Jenkins / GitLab Runner 标志
    if os.environ.get("CI") in ("1", "true"):
        return True
    return False


def _is_shm_limited() -> bool:
    """容器 /dev/shm 是否较小（< 2GB），需要 --disable-dev-shm-usage"""
    try:
        shm_stat = os.statvfs("/dev/shm")
        shm_size = shm_stat.f_bsize * shm_stat.f_blocks
        return shm_size < 2 * 1024 * 1024 * 1024  # < 2GB
    except Exception:
        return False


def _make_options(browser: str):
    """构造浏览器选项"""
    if browser.lower() == "chrome":
        options = ChromeOptions()
    elif browser.lower() == "firefox":
        options = FirefoxOptions()
    elif browser.lower() == "edge":
        options = EdgeOptions()
    else:
        raise ValueError(f"不支持的浏览器: {browser}")

    if HEADLESS:
        if browser.lower() == "firefox":
            options.add_argument("--headless")
        else:
            # Chrome 109+ 推荐用 --headless=new
            options.add_argument("--headless=new")

    # 通用选项
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--window-size={WINDOW_SIZE[0]},{WINDOW_SIZE[1]}")
    options.add_argument("--lang=en-US")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    # 容器内 /dev/shm 较小时必须启用，否则 Chrome 会频繁崩溃
    if _is_container() or _is_shm_limited():
        options.add_argument("--disable-dev-shm-usage")
        logger.info("🐳 检测到容器环境，启用 --disable-dev-shm-usage")

    # 屏蔽 Chrome "正受自动化软件控制" 提示
    if browser.lower() in ("chrome", "edge"):
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

    return options


def _resolve_chrome_service() -> ChromeService:
    """Selenium 4.x 正确方式：用 Service(executable_path=...)"""
    # 1. 显式路径优先
    if CHROME_DRIVER_PATH and os.path.exists(CHROME_DRIVER_PATH):
        logger.info(f"📌 使用显式 chromedriver 路径: {CHROME_DRIVER_PATH}")
        return ChromeService(executable_path=CHROME_DRIVER_PATH)

    # 2. PATH 中有 chromedriver
    if shutil.which("chromedriver"):
        logger.info("📌 使用 PATH 中的 chromedriver（容器镜像已内置）")
        return ChromeService()

    # 3. webdriver-manager 自动下载
    if HAS_WDM:
        logger.info("📌 通过 webdriver-manager 自动下载 chromedriver")
        return ChromeService(executable_path=ChromeDriverManager().install())

    # 4. Selenium 4.10+ 自带 selenium-manager 兜底
    logger.info("📌 由 selenium-manager 自动管理 chromedriver")
    return ChromeService()


def get_driver(browser: str = BROWSER):
    """创建 WebDriver 实例"""
    logger.info(f"📌 初始化浏览器: {browser}, headless={HEADLESS}")
    options = _make_options(browser)

    if browser.lower() == "chrome":
        driver = webdriver.Chrome(service=_resolve_chrome_service(), options=options)

    elif browser.lower() == "firefox":
        if HAS_WDM:
            service = FirefoxService(executable_path=GeckoDriverManager().install())
        else:
            service = FirefoxService()
        driver = webdriver.Firefox(service=service, options=options)

    elif browser.lower() == "edge":
        if HAS_WDM:
            service = EdgeService(executable_path=EdgeChromiumDriverManager().install())
        else:
            service = EdgeService()
        driver = webdriver.Edge(service=service, options=options)

    else:
        raise ValueError(f"不支持的浏览器: {browser}")

    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    # 稳定性治理：不再使用隐式等待，全用显式等待（BasePage WebDriverWait）
    # 隐式+显式混用会导致不可预测的等待时间（Selenium 官方警告）
    if IMPLICIT_WAIT:
        driver.implicitly_wait(IMPLICIT_WAIT)
    logger.info(
        f"✅ 浏览器启动成功, 版本: {driver.capabilities.get('browserVersion', 'unknown')}, "
        f"平台: {driver.capabilities.get('platformName', platform.system())}"
    )
    return driver


def kill_driver(driver):
    """安全关闭浏览器"""
    if driver is None:
        return
    try:
        driver.quit()
        logger.info("🛑 浏览器已安全退出")
    except Exception as e:
        logger.warning(f"关闭浏览器异常: {e}")


if __name__ == "__main__":
    # 自测：强制无头
    import config.config as cfg
    cfg.HEADLESS = True
    d = get_driver()
    d.get("https://www.saucedemo.com")
    print("title =", d.title)
    kill_driver(d)
