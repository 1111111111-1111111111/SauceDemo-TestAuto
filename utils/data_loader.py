# -*- coding: utf-8 -*-
"""
数据驱动加载器
================
统一加载 YAML / CSV / JSON 外置数据，供 pytest 参数化使用。

设计原则：
  1. 数据与代码分离：非技术人员可改 YAML/CSV 增减用例，无需碰 Python
  2. 统一入口：load_yaml() / load_csv() / load_json()
  3. 路径自适应：传入相对 data/ 目录的文件名即可
  4. 返回结构可直接用于 @pytest.mark.parametrize

用法：
    from utils.data_loader import load_yaml
    cases = load_yaml("login.yaml")["login_failure"]
    @pytest.mark.parametrize("case", cases, ids=lambda c: c["id"])
"""
import csv
import json
import os
from typing import Any, Dict, List

import yaml

from config.config import BASE_DIR

DATA_DIR = os.path.join(BASE_DIR, "data")


def _resolve_path(filename: str) -> str:
    """解析数据文件路径：支持绝对路径或相对 data/ 目录的文件名"""
    if os.path.isabs(filename):
        return filename
    return os.path.join(DATA_DIR, filename)


def load_yaml(filename: str) -> Any:
    """加载 YAML 文件，返回 Python 对象（通常是 dict 或 list）"""
    path = _resolve_path(filename)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(filename: str) -> Any:
    """加载 JSON 文件"""
    path = _resolve_path(filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(filename: str) -> List[Dict[str, str]]:
    """加载 CSV 文件，返回 dict 列表（首行为表头）"""
    path = _resolve_path(filename)
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)
