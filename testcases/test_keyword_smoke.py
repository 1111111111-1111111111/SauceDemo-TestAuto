# -*- coding: utf-8 -*-
"""
关键字驱动冒烟测试
==================
用 YAML 描述测试步骤，KeywordEngine 解析执行。
适合冒烟/回归的可视化用例，非技术同学可读可改。

特点：
  - 测试逻辑写在 YAML 里，代码只负责驱动
  - 新增冒烟用例只需加一个 YAML 文件 + 加入 SMOKE_FILES
  - Allure 报告中每一步都作为独立 step 展示
"""
import pytest
import allure

from utils.keyword_engine import KeywordEngine

SMOKE_FILES = [
    "keywords/smoke_login.yaml",
    "keywords/smoke_buy.yaml",
]


@allure.epic("SauceDemo 电商网站自动化测试")
@allure.feature("关键字驱动冒烟")
@pytest.mark.smoke
class TestKeywordSmoke:
    """关键字驱动冒烟测试"""

    @allure.story("冒烟用例")
    @allure.title("YAML 关键字驱动冒烟 - {yaml_file}")
    @pytest.mark.parametrize("yaml_file", SMOKE_FILES)
    def test_keyword_smoke(self, driver_instance, yaml_file):
        """数据驱动加载 YAML 用例，引擎执行步骤"""
        engine = KeywordEngine(driver_instance)
        engine.run_testcase(yaml_file)
