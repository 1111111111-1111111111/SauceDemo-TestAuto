# -*- coding: utf-8 -*-
"""
所有 Page Object 的基类
- 封装 Selenium 常用操作（点击、输入、获取文本、显式等待等）
- 加入日志 + 失败自动截图
"""
from typing import Tuple

import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.config import EXPLICIT_WAIT
from utils.helpers import take_screenshot
from utils.logger import logger


class BasePage:
    """页面基类"""

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, EXPLICIT_WAIT)

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
            logger.error(f"❌ 元素未找到 {locator}")
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
    def click(self, locator: Tuple[str, str]):
        """点击元素（稳定性增强：WebDriver 点击失败时用 JS 兜底）"""
        ele = self.find_clickable_element(locator)
        try:
            ele.click()
        except Exception:
            logger.warning(f"⚠️ 常规点击失败 {locator}，改用 JS 点击")
            self.driver.execute_script("arguments[0].click();", ele)
        logger.info(f"🖱️ 已点击 {locator}")

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

    # ============= 等待 =============
    def wait_url_contains(self, keyword: str, timeout: int = None):
        """等待 URL 包含某关键字"""
        wait = WebDriverWait(self.driver, timeout or EXPLICIT_WAIT)
        return wait.until(EC.url_contains(keyword))

    def wait_text_in_element(self, locator: Tuple[str, str], text: str):
        wait = WebDriverWait(self.driver, EXPLICIT_WAIT)
        return wait.until(EC.text_to_be_present_in_element(locator, text))

    # ============= Allure 步骤 =============
    @allure.step("打开 URL: {url}")
    def open(self, url: str):
        self.driver.get(url)
        logger.info(f"🌐 已访问 {url}")
