#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 日志工具
负责配置和管理日志
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logging(log_level='INFO', log_file=None, max_size=10485760, backup_count=5):
    """
    设置日志
    
    Args:
        log_level (str): 日志级别，可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_file (str): 日志文件路径，如果为None则只输出到控制台
        max_size (int): 日志文件最大大小，单位为字节
        backup_count (int): 备份文件数量
    """
    # 转换日志级别字符串为对应的常量
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加控制台处理器到根日志记录器
    root_logger.addHandler(console_handler)
    
    # 如果指定了日志文件，创建文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # 创建滚动文件处理器
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        
        # 添加文件处理器到根日志记录器
        root_logger.addHandler(file_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('chardet').setLevel(logging.WARNING)
    logging.getLogger('bs4').setLevel(logging.WARNING)
    
    # 记录初始日志消息
    logging.info(f"日志系统已初始化，级别: {log_level}")
    if log_file:
        logging.info(f"日志文件: {os.path.abspath(log_file)}")

def get_logger(name):
    """
    获取指定名称的日志记录器
    
    Args:
        name (str): 日志记录器名称
        
    Returns:
        Logger: 日志记录器
    """
    return logging.getLogger(name) 