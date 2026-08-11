# -*- coding: utf-8 -*-
"""
全局配置
- 关键配置支持环境变量覆盖，方便 Docker / CI 注入
- 本地运行：直接修改下面的默认值即可
"""
import os

# ==================== 基础路径 ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ==================== 被测站点 ====================
BASE_URL = os.environ.get("BASE_URL", "https://www.saucedemo.com/")

# ==================== 浏览器配置 ====================
BROWSER = os.environ.get("BROWSER", "chrome")          # chrome / firefox / edge
HEADLESS = True  # os.environ.get("HEADLESS", "false").lower() in ("true", "1", "yes")
WINDOW_SIZE = (1920, 1080)

# ChromeDriver 路径（优先级：显式路径 > PATH > webdriver-manager > selenium-manager）
CHROME_DRIVER_PATH = os.environ.get("CHROME_DRIVER_PATH", "")

# ==================== 超时 ====================
PAGE_LOAD_TIMEOUT = int(os.environ.get("PAGE_LOAD_TIMEOUT", "30"))   # 页面加载超时（秒）
IMPLICIT_WAIT = int(os.environ.get("IMPLICIT_WAIT", "0"))            # 隐式等待(秒)·稳定性治理:保持0,全用显式等待
EXPLICIT_WAIT = int(os.environ.get("EXPLICIT_WAIT", "10"))           # 显式等待（秒）

# ==================== 默认账号 ====================
DEFAULT_USER = os.environ.get("DEFAULT_USER", "standard_user")
DEFAULT_PASSWORD = os.environ.get("DEFAULT_PASSWORD", "secret_sauce")

# ==================== 路径配置 ====================
LOG_DIR = os.path.join(BASE_DIR, "logs")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
ALLURE_RESULTS_DIR = os.path.join(BASE_DIR, "reports", "allure-results")
ALLURE_REPORT_DIR = os.path.join(BASE_DIR, "reports", "allure-report")

# ==================== 日志 ====================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_FILE = os.path.join(LOG_DIR, "test_run.log")

# ==================== 自动创建目录 ====================
for _d in (LOG_DIR, SCREENSHOT_DIR, ALLURE_RESULTS_DIR):
    os.makedirs(_d, exist_ok=True)
