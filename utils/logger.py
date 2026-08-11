# -*- coding: utf-8 -*-
"""
日志工具
- 控制台彩色输出（依赖 colorlog，如未安装则降级为普通输出）
- 文件持久化（logs/test_run.log，自动滚动）
- 暴露 get_logger 给业务层使用
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

try:
    import colorlog
    _HAS_COLORLOG = True
except ImportError:
    _HAS_COLORLOG = False

from config.config import LOG_LEVEL, LOG_FORMAT, LOG_FILE, LOG_DIR


def get_logger(name: str = "saucedemo") -> logging.Logger:
    """
    获取配置好的 logger 实例
    :param name: logger 名称（一般用 __name__）
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler（pytest 多次实例化场景）
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL.upper())
    logger.propagate = False

    # ---------- 控制台 ----------
    if _HAS_COLORLOG:
        color_formatter = colorlog.ColoredFormatter(
            "%(log_color)s" + LOG_FORMAT,
            log_colors={
                "DEBUG":    "cyan",
                "INFO":     "green",
                "WARNING":  "yellow",
                "ERROR":    "red",
                "CRITICAL": "bold_red",
            },
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(color_formatter)
        logger.addHandler(console_handler)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)

    # ---------- 文件（滚动 10MB × 5）----------
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


# 默认 logger，业务可直接 from utils.logger import logger
logger = get_logger()


if __name__ == "__main__":
    # 自测
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    print(f"日志文件位置: {LOG_FILE}")
    print(f"colorlog 可用: {_HAS_COLORLOG}")
