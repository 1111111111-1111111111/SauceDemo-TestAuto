# -*- coding: utf-8 -*-
"""utils.helpers 单元测试（无浏览器依赖）"""
import pytest

from utils.helpers import safe_filename


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("login_fail", "login_fail"),
        ('css selector [data-test="error"]', "css selector [data-test=_error_]"),
        ("path/with/slashes", "path_with_slashes"),
        ("bad:name|here", "bad_name_here"),
        ("", "screenshot"),
    ],
    ids=["plain", "css_selector", "slashes", "pipes_colons", "empty"],
)
def test_safe_filename_sanitizes_invalid_chars(raw, expected):
    assert safe_filename(raw) == expected


def test_safe_filename_truncates_long_names():
    long_name = "a" * 300
    assert len(safe_filename(long_name)) == 200
