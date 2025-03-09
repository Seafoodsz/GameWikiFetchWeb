#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 配置管理工具
负责加载和管理配置
"""

import os
import json
import logging

class ConfigManager:
    """配置管理器，负责加载和管理配置"""
    
    def __init__(self, config_file=None):
        """
        初始化配置管理器
        
        Args:
            config_file (str): 配置文件路径，如果为None则使用默认路径
        """
        self.logger = logging.getLogger('config')
        self.config = {}
        
        # 如果未指定配置文件，尝试从环境变量获取
        if not config_file:
            config_file = os.getenv('CONFIG_FILE')
        
        # 如果环境变量中也没有指定，使用默认路径
        if not config_file:
            # 获取项目根目录
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_file = os.path.join(root_dir, 'config', 'config.json')
        
        self.config_file = config_file
        self.load_config()
    
    def load_config(self):
        """
        加载配置文件
        
        Returns:
            dict: 配置字典
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.logger.info(f"已加载配置文件: {self.config_file}")
            else:
                self.logger.warning(f"配置文件不存在: {self.config_file}，将使用默认配置")
                self.config = self._get_default_config()
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}，将使用默认配置")
            self.config = self._get_default_config()
        
        return self.config
    
    def save_config(self, config=None):
        """
        保存配置到文件
        
        Args:
            config (dict): 配置字典，如果为None则使用当前配置
            
        Returns:
            bool: 是否保存成功
        """
        if config:
            self.config = config
        
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"已保存配置到文件: {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}")
            return False
    
    def get(self, key, default=None):
        """
        获取配置项
        
        Args:
            key (str): 配置项键名，支持点号分隔的多级键名
            default: 默认值，如果配置项不存在则返回此值
            
        Returns:
            配置项的值
        """
        # 支持点号分隔的多级键名
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """
        设置配置项
        
        Args:
            key (str): 配置项键名，支持点号分隔的多级键名
            value: 配置项的值
            
        Returns:
            bool: 是否设置成功
        """
        # 支持点号分隔的多级键名
        keys = key.split('.')
        config = self.config
        
        # 遍历除最后一个键以外的所有键
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                # 如果当前键对应的值不是字典，无法继续设置子键
                self.logger.error(f"无法设置配置项 {key}，因为 {'.'.join(keys[:i+1])} 不是字典")
                return False
            config = config[k]
        
        # 设置最后一个键的值
        config[keys[-1]] = value
        return True
    
    def _get_default_config(self):
        """
        获取默认配置
        
        Returns:
            dict: 默认配置字典
        """
        return {
            "fetcher": {
                "wiki_url": "",
                "output_dir": "wiki_data/default",
                "max_depth": 3,
                "download_images": True,
                "download_tables": True,
                "user_agent": "GameWikiFetcher/1.0",
                "delay": 1.0,
                "threads": 3,
                "save_html": False,
                "max_retries": 3
            },
            "processor": {
                "input_dir": "data/input",
                "output_dir": "data/output",
                "processors": {
                    "character": {
                        "enabled": True,
                        "input_pattern": "characters/*.html"
                    },
                    "item": {
                        "enabled": True,
                        "input_pattern": "items/*.html"
                    },
                    "skill": {
                        "enabled": True,
                        "input_pattern": "skills/*.html"
                    }
                }
            },
            "storage": {
                "type": "json",
                "mongodb_uri": "mongodb://localhost:27017/",
                "mongodb_db": "gamewiki",
                "sqlite_path": "data/gamewiki.db"
            },
            "web": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False,
                "secret_key": ""
            },
            "logging": {
                "level": "INFO",
                "file": "logs/gamewiki.log",
                "max_size": 10485760,  # 10MB
                "backup_count": 5
            }
        } 