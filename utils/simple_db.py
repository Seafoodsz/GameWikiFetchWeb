#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化版数据库管理模块
用于管理数据的存储和检索，不依赖ijson
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

class DatabaseManager:
    """简化版数据库管理器"""
    
    def __init__(self, config):
        """初始化数据库管理器
        
        Args:
            config (Config): 配置对象
        """
        self.config = config
        self.logger = logging.getLogger('stoneshard')
        self.logger.info("初始化简化版数据库管理器")
        
        # 内存中的数据缓存
        self.data = {
            "character": {},
            "skill": {},
            "item": {},
            "relation": {}
        }
    
    def save(self, collection, data, id_field="id"):
        """保存数据
        
        Args:
            collection (str): 集合名称
            data (dict): 要保存的数据
            id_field (str, optional): ID字段名称
        
        Returns:
            bool: 是否成功保存
        """
        data_id = data.get(id_field)
        if not data_id:
            self.logger.warning(f"保存数据失败: 缺少ID字段 {id_field}")
            return False
        
        # 保存到内存
        self.data[collection][data_id] = data
        return True
    
    def get(self, collection, data_id):
        """获取数据
        
        Args:
            collection (str): 集合名称
            data_id (str): 数据ID
        
        Returns:
            dict: 数据项
        """
        return self.data[collection].get(data_id)
    
    def get_all(self, collection):
        """获取集合中的所有数据
        
        Args:
            collection (str): 集合名称
        
        Returns:
            list: 数据项列表
        """
        return list(self.data[collection].values())
    
    def export_all(self, output_path):
        """导出所有数据
        
        Args:
            output_path (str): 输出文件路径
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 导出数据
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"已导出所有数据到 {output_path}")
    
    def close(self):
        """关闭数据库连接"""
        # 简化版不需要关闭连接
        pass 