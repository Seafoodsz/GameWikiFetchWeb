#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志模块
用于记录程序运行过程中的日志信息
"""

import os
import sys
import logging
import traceback
import functools
from pathlib import Path

def setup_logger(log_level="INFO", log_file=None, log_to_console=True):
    """设置日志记录器
    
    Args:
        log_level (str): 日志级别，可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_file (str, optional): 日志文件路径
        log_to_console (bool, optional): 是否输出到控制台
    
    Returns:
        logging.Logger: 日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger("stoneshard_processor")
    
    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # 清除现有的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 添加控制台处理器
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # 创建文件处理器，最大 10MB，保留 5 个备份
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger():
    """获取日志记录器
    
    Returns:
        logging.Logger: 日志记录器
    """
    return logging.getLogger("stoneshard_processor")

class LoggerAdapter(logging.LoggerAdapter):
    """日志适配器，用于添加上下文信息"""
    
    def __init__(self, logger, prefix=""):
        """初始化日志适配器
        
        Args:
            logger (logging.Logger): 日志记录器
            prefix (str, optional): 日志前缀
        """
        super().__init__(logger, {})
        self.prefix = prefix
    
    def process(self, msg, kwargs):
        """处理日志消息
        
        Args:
            msg (str): 日志消息
            kwargs (dict): 关键字参数
        
        Returns:
            tuple: (处理后的消息, 关键字参数)
        """
        if self.prefix:
            return f"[{self.prefix}] {msg}", kwargs
        return msg, kwargs 

# 新增：全局异常处理装饰器
def exception_handler(func):
    """全局异常处理装饰器
    
    捕获函数执行过程中的异常，记录详细日志，并可选择重新抛出
    
    Args:
        func: 要装饰的函数
    
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('stoneshard')
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 获取详细的异常信息
            exc_info = sys.exc_info()
            stack_trace = ''.join(traceback.format_exception(*exc_info))
            
            # 记录详细日志
            logger.error(
                f"异常发生在 {func.__name__}: {str(e)}\n"
                f"参数: args={args}, kwargs={kwargs}\n"
                f"堆栈跟踪:\n{stack_trace}"
            )
            
            # 重新抛出异常
            raise
    
    return wrapper

# 新增：上下文日志记录器
class ContextLogger:
    """上下文日志记录器
    
    在日志消息中添加上下文信息，如模块名、函数名等
    
    Example:
        logger = ContextLogger('processor', 'character')
        logger.info('处理角色数据')  # 输出: [processor:character] 处理角色数据
    """
    
    def __init__(self, module_name, component_name=None):
        """初始化上下文日志记录器
        
        Args:
            module_name (str): 模块名称
            component_name (str, optional): 组件名称
        """
        self.module_name = module_name
        self.component_name = component_name
        self.logger = logging.getLogger('stoneshard')
    
    def _format_message(self, message):
        """格式化消息，添加上下文信息"""
        context = self.module_name
        if self.component_name:
            context += f":{self.component_name}"
        return f"[{context}] {message}"
    
    def debug(self, message, *args, **kwargs):
        """记录调试级别日志"""
        self.logger.debug(self._format_message(message), *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        """记录信息级别日志"""
        self.logger.info(self._format_message(message), *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        """记录警告级别日志"""
        self.logger.warning(self._format_message(message), *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        """记录错误级别日志"""
        self.logger.error(self._format_message(message), *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        """记录严重错误级别日志"""
        self.logger.critical(self._format_message(message), *args, **kwargs) 