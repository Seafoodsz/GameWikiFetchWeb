#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基础处理器模块
提供所有处理器的基类
"""

import os
import json
import glob
from pathlib import Path
from utils.logger import ContextLogger, exception_handler

class BaseProcessor:
    """基础处理器类，所有处理器的基类"""
    
    def __init__(self, config, db_manager, processor_name="base"):
        """初始化基础处理器
        
        Args:
            config (Config): 配置对象
            db_manager (DatabaseManager): 数据库管理器
            processor_name (str): 处理器名称
        """
        self.config = config
        self.db_manager = db_manager
        self.processor_name = processor_name
        self.logger = ContextLogger('processor', processor_name)
        
        # 获取处理器配置
        self.processor_config = config.get(f"processors.{processor_name}", {})
        self.enabled = self.processor_config.get("enabled", True)
        
        # 输入模式
        self.input_pattern = self.processor_config.get("input_pattern", "*.html")
        
        # 处理的数据项
        self.items = {}
    
    @exception_handler
    def process(self):
        """处理数据
        
        Returns:
            int: 处理的数据项数量
        """
        if not self.enabled:
            self.logger.info(f"{self.processor_name} 处理器已禁用")
            return 0
        
        self.logger.info(f"开始处理 {self.processor_name} 数据")
        
        # 获取输入文件列表
        input_path = os.path.join(self.config.input_dir, self.input_pattern)
        input_files = glob.glob(input_path)
        
        self.logger.info(f"找到 {len(input_files)} 个输入文件")
        
        # 处理每个文件
        processed_count = 0
        for file_path in input_files:
            try:
                # 处理文件
                item = self._process_file(file_path)
                if item:
                    # 保存到内存
                    item_id = item.get("id")
                    if item_id:
                        self.items[item_id] = item
                        processed_count += 1
                    else:
                        self.logger.warning(f"文件 {file_path} 处理后没有ID")
            except Exception as e:
                self.logger.error(f"处理文件 {file_path} 时出错: {str(e)}")
        
        self.logger.info(f"完成处理 {self.processor_name} 数据，处理了 {processed_count} 个项目")
        return processed_count
    
    def _process_file(self, file_path):
        """处理单个文件
        
        Args:
            file_path (str): 文件路径
        
        Returns:
            dict: 处理后的数据项
        """
        # 这是一个基础方法，子类应该重写它
        self.logger.warning(f"_process_file 方法未实现，无法处理文件 {file_path}")
        return None
    
    @exception_handler
    def export(self, output_path):
        """导出处理后的数据
        
        Args:
            output_path (str): 输出文件路径
        """
        self.logger.info(f"导出 {self.processor_name} 数据到 {output_path}")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 导出数据
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(list(self.items.values()), f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"已导出 {len(self.items)} 个 {self.processor_name} 项目") 