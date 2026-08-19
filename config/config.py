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
HEADLESS = os.environ.get("HEADLESS", "true").lower() in ("true", "1", "yes")
WINDOW_SIZE = (1920, 1080)

# ChromeDriver 路径（优先级：显式路径 > PATH > webdriver-manager > selenium-manager）
CHROME_DRIVER_PATH = os.environ.get("CHROME_DRIVER_PATH", "")

# ==================== 超时 ====================
# 注意：所有超时均支持环境变量覆盖，Docker / CI 通过环境变量注入即可，无需改代码。
# CI 场景（GitHub Actions / Jenkins 等）网络延迟显著高于本地，
# 通过 CI_TIMEOUT_SCALE 系数自动放大各等待阈值，避免固定超时导致误报。

def _is_ci_env() -> bool:
    """是否运行在 CI / 容器环境"""
    if os.environ.get("CI") in ("1", "true", "yes"):
        return True
    if os.environ.get("CONTAINER") in ("1", "true", "yes"):
        return True
    if os.path.exists("/.dockerenv"):
        return True
    return False


IS_CI = _is_ci_env()

# CI 环境下的超时放大系数（显式等待 ×2，页面加载 ×1.5；可被 CI_TIMEOUT_SCALE 覆盖）
CI_TIMEOUT_SCALE = float(os.environ.get("CI_TIMEOUT_SCALE", "2.0" if IS_CI else "1.0"))

PAGE_LOAD_TIMEOUT = int(float(os.environ.get("PAGE_LOAD_TIMEOUT", "30")) * (1.5 if IS_CI else 1.0))
IMPLICIT_WAIT = int(os.environ.get("IMPLICIT_WAIT", "0"))            # 隐式等待(秒)·稳定性治理:保持0,全用显式等待
EXPLICIT_WAIT = int(float(os.environ.get("EXPLICIT_WAIT", "10")) * CI_TIMEOUT_SCALE)   # 显式等待（秒）
NAV_WAIT = int(os.environ.get("NAV_WAIT", "20"))                      # 页面导航/URL 变更等待（秒），
                                                                     # 建议 ≥ EXPLICIT_WAIT × 2，登录后跳转常用

# ==================== 重试策略 ====================
# 应用层（BasePage）导航/等待失败后的重试次数与间隔
RETRY_TIMES = int(os.environ.get("RETRY_TIMES", "2"))                 # 失败重试次数（0=关闭）
RETRY_INTERVAL = float(os.environ.get("RETRY_INTERVAL", "2"))         # 重试间隔（秒）

# ==================== WebDriver Manager ====================
WDM_TIMEOUT = int(os.environ.get("WDM_TIMEOUT", "120"))               # 驱动下载超时（秒/次）
WDM_RETRIES = int(os.environ.get("WDM_RETRIES", "3"))                 # 驱动下载重试次数
WDM_VERSION = os.environ.get("WDM_VERSION", "")                       # 锁定 chromedriver 版本（留空=自动匹配）

# ==================== 性能监控 ====================
SLOW_TEST_THRESHOLD = float(os.environ.get("SLOW_TEST_THRESHOLD", "45"))  # 单用例耗时阈值（秒），超过记 WARNING
MAX_TEST_DURATION = float(os.environ.get("MAX_TEST_DURATION", "120"))     # 单用例最长允许时间（秒），超过强制中断

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
