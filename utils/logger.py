"""
日志系统模块
提供统一的日志配置和管理功能
"""

import logging
import os
from typing import Optional


def setup_logger(
    logger_name: str = 'binance_square',
    log_file: Optional[str] = None,
    log_level: int = logging.INFO,
    log_dir: str = 'logs'
) -> logging.Logger:
    """
    设置并返回一个配置好的logger

    Args:
        logger_name: logger的名称
        log_file: 日志文件名，如果为None则使用默认名称
        log_level: 日志级别，默认为INFO
        log_dir: 日志文件目录，默认为'logs'

    Returns:
        配置好的logger对象
    """
    # 确保日志文件夹存在
    os.makedirs(log_dir, exist_ok=True)

    # 如果没有指定日志文件名，使用默认名称
    if log_file is None:
        log_file = f'{log_dir}/{logger_name}.log'
    else:
        log_file = f'{log_dir}/{log_file}'

    # 创建或获取logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 创建文件handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)

    # 创建控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 设置格式器
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加handler到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(logger_name: str = 'binance_square') -> logging.Logger:
    """
    获取已存在的logger，如果不存在则创建一个新的

    Args:
        logger_name: logger的名称

    Returns:
        logger对象
    """
    logger = logging.getLogger(logger_name)

    # 如果logger还没有被配置，则配置它
    if not logger.handlers:
        return setup_logger(logger_name)

    return logger
