# -*- coding: utf-8 -*-
"""
所有 Page Object 的基类
- 封装 Selenium 常用操作（点击、输入、获取文本、显式等待等）
- 加入日志 + 失败自动截图
- CI 稳定性治理：所有导航/等待都支持失败重试（RETRY_TIMES），
  网络抖动导致的瞬时超时自动重试后通常即可恢复，避免用例误报 FAILED
"""
import time
from typing import Callable, List, Tuple

import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.config import EXPLICIT_WAIT, NAV_WAIT, RETRY_TIMES, RETRY_INTERVAL
from utils.helpers import take_screenshot
from utils.logger import logger


class BasePage:
    """页面基类"""

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, EXPLICIT_WAIT)

    # ============= 弹性等待核心 =============
    def _wait_until(self, condition: Callable, timeout: float = None,
                    desc: str = "", retries: int = None) -> bool:
        """显式等待 + 失败重试（网络抖动兜底）。

        :param condition: EC 条件或可调用对象（返回 truthy 即成功）
        :param timeout:   单次等待超时（默认 EXPLICIT_WAIT）
        :param desc:      等待描述（用于日志/告警）
        :param retries:   重试次数（默认 RETRY_TIMES）
        :return: 成功返回 True，最终失败返回 False（不抛异常，由调用方决定）
        """
        timeout = timeout if timeout is not None else EXPLICIT_WAIT
        retries = RETRY_TIMES if retries is None else retries
        attempt = 0
        t_start = time.time()
        while True:
            attempt += 1
            try:
                wait = WebDriverWait(self.driver, timeout, poll_frequency=0.5)
                wait.until(condition)
                if attempt > 1:
                    logger.info(f"🔄 {desc or condition} 第 {attempt} 次等待成功")
                return True
            except TimeoutException as e:
                if attempt > retries:
                    logger.error(
                        f"❌ 等待超时 {desc or condition} "
                        f"(单次 {timeout}s × {attempt} 次共 {timeout * attempt}s，"
                        f"实际耗时 {time.time() - t_start:.1f}s)；"
                        f"URL={self.driver.current_url}, "
                        f"readyState={self._ready_state()}")
                    return False
                logger.warning(
                    f"⚠️ 等待超时 {desc or condition} 第 {attempt}/{retries + 1} 次"
                    f"（{timeout}s），{RETRY_INTERVAL}s 后重试…")
                time.sleep(RETRY_INTERVAL)
            except Exception as e:  # 其他异常（如 InvalidSelector）不重试
                logger.error(f"❌ 等待异常 {desc or condition}: {type(e).__name__}: {e}")
                return False

    def _ready_state(self) -> str:
        """当前页面 document.readyState（诊断用）"""
        try:
            return self.driver.execute_script("return document.readyState")
        except Exception:
            return "unknown"

    def wait_page_ready(self, timeout: float = None) -> bool:
        """等待页面 JS 就绪（document.readyState == 'complete'）。

        SPA 场景下 URL 已变但 React 尚未挂载，单纯等 URL 会导致后续
        find_element 扑空；这里先等 readyState 再等关键元素。
        """
        ok = self._wait_until(
            lambda d: d.execute_script("return document.readyState") == "complete",
            timeout=timeout or NAV_WAIT,
            desc="页面就绪(document.readyState=complete)",
        )
        if not ok:
            logger.warning(f"⚠️ 页面长时间未就绪，URL={self.driver.current_url}")
        return ok

    def wait_url_contains(self, keyword: str, timeout: float = None,
                          retries: int = None) -> bool:
        """等待 URL 包含关键字；失败自动重试（慢网络下跳转可能超时）。

        原实现一次超时即抛异常，CI 网络抖动时高频误报。
        新实现：单次 timeout 后自动重试 RETRY_TIMES 次，
        最终失败才抛 TimeoutException（同时保留截图诊断）。
        """
        ok = self._wait_until(
            EC.url_contains(keyword),
            timeout=timeout or NAV_WAIT,
            desc=f"URL 包含 '{keyword}'",
            retries=retries,
        )
        if not ok:
            take_screenshot(self.driver, name=f"url_timeout_{keyword.replace('/', '_')}")
            raise TimeoutException(
                f"等待 URL 包含 '{keyword}' 超时（{timeout or NAV_WAIT}s × {retries + 1} 次），"
                f"当前 URL={self.driver.current_url}")
        return True

    def wait_text_in_element(self, locator: Tuple[str, str], text: str,
                             timeout: float = None):
        """等待元素文本变化；失败重试后仍失败则抛异常（文本断言前置）"""
        ok = self._wait_until(
            EC.text_to_be_present_in_element(locator, text),
            timeout=timeout or EXPLICIT_WAIT,
            desc=f"元素 {locator} 文本包含 '{text}'",
        )
        if not ok:
            raise TimeoutException(f"等待元素文本 '{text}' 超时: {locator}")

    def wait_any(self, conditions: List[Tuple[str, Tuple]], timeout: float = None):
        """等待多个条件中任一满足（用于'页面可能是 A 或 B'的柔性断言场景）。

        用法：
            ok, which = page.wait_any([
                ("cart", (By.ID, "checkout")),
                ("products", (By.CSS_SELECTOR, "[data-test='inventory-list']")),
            ])
            assert ok, "页面既不是购物车也不是商品列表"
        """
        from selenium.webdriver.support.ui import WebDriverWait

        def _any_cond(driver):
            for name, loc in conditions:
                try:
                    if driver.find_elements(*loc):
                        return name
                except Exception:
                    continue
            return None

        wait = WebDriverWait(self.driver, timeout or EXPLICIT_WAIT)
        try:
            which = wait.until(_any_cond)
            logger.info(f"🎯 页面状态: {which}")
            return True, which
        except TimeoutException:
            logger.error(f"❌ 等待多个条件任一满足超时: {[c[0] for c in conditions]}")
            return False, None

    def wait_element_present(self, locator: Tuple[str, str], timeout: float = None,
                             desc: str = None) -> WebElement:
        """弹性等待元素出现（带失败重试 + 诊断），最终失败才抛 TimeoutException。

        与裸 self.wait.until(EC.presence_of_element_located(...)) 的区别：
        - 单次 timeout 后自动重试 RETRY_TIMES 次（网络抖动兜底）
        - 失败时输出 URL + readyState + 截图，便于 CI 排查
        所有页面对象的"导航后等关键元素"统一走这里，替代散落的裸 wait。
        """
        ok = self._wait_until(
            EC.presence_of_element_located(locator),
            timeout=timeout,
            desc=desc or f"元素出现 {locator}",
        )
        if not ok:
            take_screenshot(self.driver, name=f"element_timeout_{locator[0]}_{locator[1]}")
            raise TimeoutException(
                f"等待元素出现超时: {locator}（{timeout or EXPLICIT_WAIT}s × {RETRY_TIMES + 1} 次），"
                f"URL={self.driver.current_url}, readyState={self._ready_state()}")
        return self.driver.find_element(*locator)

    def find_elements_immediate(self, locator: Tuple[str, str]) -> List[WebElement]:
        """非阻塞即时读取所有匹配元素；不存在立即返回 []（不等待）。

        专用于"轮询式快速读取"场景（购物车角标数量、元素是否存在等）：
        旧实现 find_elements(locator, timeout=1) 每次轮询阻塞 1s，且 CI 慢 DOM
        更新下 1s 内读不到就误判为 0 → 角标断言高频误报。
        改为即时读取后，读取本身零阻塞，真正的等待由外层 _wait_until /
        WebDriverWait 的轮询驱动，既快又准。
        """
        try:
            return self.driver.find_elements(*locator)
        except Exception as e:
            logger.debug(f"即时读取元素异常 {locator}: {type(e).__name__}: {e}")
            return []

    def find_element_if_present(self, locator: Tuple[str, str]) -> WebElement | None:
        """即时检查元素是否存在；存在返回元素，不存在返回 None（不等待不抛异常）。"""
        eles = self.find_elements_immediate(locator)
        return eles[0] if eles else None

    def scroll_into_view(self, element: WebElement):
        """滚动元素到可视区域（避免被遮挡/懒加载导致点击超时）"""
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center', behavior:'instant'});", element)
        except Exception:
            pass

    # ============= 元素定位封装 =============
    def locator(self, locator: Tuple[str, str]):
        """返回定位器元组"""
        return locator

    def find_element(self, locator: Tuple[str, str]) -> WebElement:
        """显式等待 + 返回单个元素"""
        try:
            ele = self.wait.until(EC.presence_of_element_located(locator))
            logger.debug(f"✅ 找到元素 {locator}")
            return ele
        except TimeoutException:
            logger.error(f"❌ 元素未找到 {locator}, URL={self.driver.current_url}, "
                         f"readyState={self._ready_state()}")
            take_screenshot(self.driver, name=f"element_not_found_{locator[0]}_{locator[1]}")
            raise

    def find_elements(self, locator: Tuple[str, str], timeout: float = None):
        """返回所有匹配元素；不存在时等待出现，超时返回 []（不抛异常、不截图）。"""
        wait = WebDriverWait(self.driver, timeout if timeout is not None else EXPLICIT_WAIT)
        try:
            eles = wait.until(EC.presence_of_all_elements_located(locator))
            logger.debug(f"✅ 共找到 {len(eles)} 个元素 {locator}")
            return eles
        except TimeoutException:
            logger.warning(f"⚠️ 元素未找到（等待 {timeout if timeout is not None else EXPLICIT_WAIT}s）{locator}")
            return []

    def find_clickable_element(self, locator: Tuple[str, str]) -> WebElement:
        """等待元素可见且可点击"""
        try:
            ele = self.wait.until(EC.element_to_be_clickable(locator))
            return ele
        except TimeoutException:
            take_screenshot(self.driver, name=f"not_clickable_{locator[0]}_{locator[1]}")
            raise

    # ============= 基础操作 =============
    def click(self, locator: Tuple[str, str], expect_url: str = None):
        """点击元素（稳定性增强：滚动可见 + 区分页面加载超时与元素不可交互）

        pageLoadStrategy=eager 下 click() 触发导航时只在 DOMContentLoaded 即返回，
        不再阻塞等整页资源。但极端网络环境下仍可能抛 TimeoutException（页面加载超时）。

        错误处理策略：
          - TimeoutException + URL 已变更 → 导航其实成功了（只是资源慢），继续后续显式等待
          - TimeoutException + URL 未变更 → 导航未发生，JS 兜底点击
          - 其他异常（ElementNotInteractable 等）→ JS 兜底点击

        :param locator: 定位器
        :param expect_url: 可选，点击后预期 URL 关键字；提供后点击完成会自动等待
        """
        ele = self.find_clickable_element(locator)
        # 滚动到可视区域：避免元素被底部栏/懒加载遮挡导致点击交互超时
        self.scroll_into_view(ele)
        url_before = self.driver.current_url
        try:
            ele.click()
        except TimeoutException:
            # 页面加载超时（DOMContentLoaded 超过 PAGE_LOAD_TIMEOUT）
            url_after = self.driver.current_url
            if url_after != url_before:
                # URL 已变更 = 导航成功了，只是资源加载慢
                logger.info(f"🖱️ 点击 {locator} 触发导航（资源加载超时但 URL 已变更: {url_after}）")
            else:
                # URL 没变 = 导航未发生，可能元素不可交互，JS 兜底
                logger.warning(f"⚠️ 常规点击失败 {locator}（URL 未变更），改用 JS 点击")
                self.driver.execute_script("arguments[0].click();", ele)
        except Exception:
            logger.warning(f"⚠️ 常规点击失败 {locator}，改用 JS 点击")
            self.driver.execute_script("arguments[0].click();", ele)
        logger.info(f"🖱️ 已点击 {locator}")
        if expect_url:
            self.wait_url_contains(expect_url)

    def input_text(self, locator: Tuple[str, str], text: str):
        """输入文本"""
        ele = self.find_element(locator)
        ele.clear()
        ele.send_keys(text)
        logger.info(f"⌨️ 输入文本 '{text}' 到 {locator}")

    def get_text(self, locator: Tuple[str, str]) -> str:
        """获取元素文本"""
        ele = self.find_element(locator)
        text = ele.text
        logger.debug(f"📝 元素文本 {locator} = '{text}'")
        return text

    def get_attribute(self, locator: Tuple[str, str], attr: str) -> str:
        """获取属性"""
        ele = self.find_element(locator)
        value = ele.get_attribute(attr)
        logger.debug(f"🔖 属性 {locator}@{attr} = '{value}'")
        return value

    # ============= 浏览器操作 =============
    def get_current_url(self) -> str:
        return self.driver.current_url

    def get_title(self) -> str:
        return self.driver.title

    def page_contains(self, text: str) -> bool:
        """页面源码是否包含文本（用于宽松断言）"""
        return text in self.driver.page_source

    # ============= Allure 步骤 =============
    @allure.step("打开 URL: {url}")
    def open(self, url: str):
        self.driver.get(url)
        logger.info(f"🌐 已访问 {url}")
