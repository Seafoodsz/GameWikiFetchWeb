#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理模块
负责加载、验证和管理配置
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable

# 默认配置
DEFAULT_CONFIG = {
    "input_dir": "input",
    "output_dir": "output",
    "temp_dir": "temp",
    "log_level": "INFO",
    "log_file": "stoneshard_processor.log",
    "concurrency": 4,
    
    "database": {
        "type": "json",
        "mongodb_uri": "mongodb://localhost:27017/",
        "mongodb_db": "stoneshard",
        "sqlite_path": "stoneshard.db"
    },
    
    "processors": {
        "character": {
            "enabled": True,
            "input_pattern": "characters/*.html",
            "keywords": ["职业", "属性", "技能树", "特性"]
        },
        "skill": {
            "enabled": True,
            "input_pattern": "skills/*.html",
            "keywords": ["技能", "效果", "冷却", "消耗"]
        },
        "item": {
            "enabled": True,
            "input_pattern": "items/*.html",
            "categories": ["武器", "护甲", "消耗品", "材料", "宝石"],
            "keywords": ["类型", "伤害", "防御", "效果", "价值"]
        },
        "enemy": {
            "enabled": True,
            "input_pattern": "enemies/*.html",
            "keywords": ["生命值", "攻击", "防御", "弱点", "掉落物"]
        },
        "location": {
            "enabled": True,
            "input_pattern": "locations/*.html",
            "keywords": ["区域", "NPC", "资源", "任务"]
        },
        "quest": {
            "enabled": True,
            "input_pattern": "quests/*.html",
            "keywords": ["目标", "奖励", "前置条件", "步骤"]
        },
        "relation": {
            "enabled": True,
            "relation_types": ["角色-技能", "物品-敌人", "地点-任务", "任务-奖励"]
        }
    },
    
    "analysis": {
        "enabled": True,
        "generate_graphs": True,
        "generate_stats": True,
        "export_formats": ["json", "csv", "html"]
    },
    
    "export": {
        "formats": ["json", "csv", "html"],
        "compress": False,
        "pretty_json": True
    }
}

# 配置验证规则
CONFIG_SCHEMA = {
    "input_dir": {"type": str, "required": True},
    "output_dir": {"type": str, "required": True},
    "temp_dir": {"type": str, "required": True},
    "log_level": {"type": str, "required": True, "choices": ["DEBUG", "INFO", "WARNING", "ERROR"]},
    "log_file": {"type": str, "required": False},
    "concurrency": {"type": int, "required": False, "min": 1, "max": 32},
    
    "database": {
        "type": {"type": str, "required": True, "choices": ["json", "mongodb", "sqlite"]},
        "mongodb_uri": {"type": str, "required": False},
        "mongodb_db": {"type": str, "required": False},
        "sqlite_path": {"type": str, "required": False}
    },
    
    "processors": {
        "character": {
            "enabled": {"type": bool, "required": True},
            "input_pattern": {"type": str, "required": True},
            "keywords": {"type": list, "required": True}
        },
        "skill": {
            "enabled": {"type": bool, "required": True},
            "input_pattern": {"type": str, "required": True},
            "keywords": {"type": list, "required": True}
        },
        "item": {
            "enabled": {"type": bool, "required": True},
            "input_pattern": {"type": str, "required": True},
            "categories": {"type": list, "required": True},
            "keywords": {"type": list, "required": True}
        },
        "enemy": {
            "enabled": {"type": bool, "required": True},
            "input_pattern": {"type": str, "required": True},
            "keywords": {"type": list, "required": True}
        },
        "location": {
            "enabled": {"type": bool, "required": True},
            "input_pattern": {"type": str, "required": True},
            "keywords": {"type": list, "required": True}
        },
        "quest": {
            "enabled": {"type": bool, "required": True},
            "input_pattern": {"type": str, "required": True},
            "keywords": {"type": list, "required": True}
        },
        "relation": {
            "enabled": {"type": bool, "required": True},
            "relation_types": {"type": list, "required": True}
        }
    },
    
    "analysis": {
        "enabled": {"type": bool, "required": True},
        "generate_graphs": {"type": bool, "required": True},
        "generate_stats": {"type": bool, "required": True},
        "export_formats": {"type": list, "required": True}
    },
    
    "export": {
        "formats": {"type": list, "required": True},
        "compress": {"type": bool, "required": True},
        "pretty_json": {"type": bool, "required": True}
    }
}

class ConfigError(Exception):
    """配置错误异常"""
    pass

class Config:
    """配置管理类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_path (str, optional): 配置文件路径
        """
        self.logger = logging.getLogger('stoneshard.config')
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 验证配置
        self._validate_config()
        
        # 设置属性
        for key, value in self.config.items():
            setattr(self, key, value)
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置
        
        配置加载优先级：
        1. 默认配置
        2. 配置文件
        3. 环境变量
        
        Args:
            config_path (str, optional): 配置文件路径
        
        Returns:
            Dict[str, Any]: 加载的配置
        """
        # 从默认配置开始
        config = DEFAULT_CONFIG.copy()
        
        # 如果提供了配置文件路径，从文件加载配置
        if config_path:
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # 递归合并配置
                config = self._merge_configs(config, file_config)
                self.logger.info(f"已从 {config_path} 加载配置")
            except Exception as e:
                self.logger.error(f"无法从 {config_path} 加载配置: {str(e)}")
        else:
            # 尝试从默认位置加载配置
            default_paths = [
                'config.json',
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            file_config = json.load(f)
                        
                        # 递归合并配置
                        config = self._merge_configs(config, file_config)
                        self.logger.info(f"已从 {path} 加载配置")
                        break
                    except Exception as e:
                        self.logger.error(f"无法从 {path} 加载配置: {str(e)}")
        
        # 从环境变量加载配置
        env_config = self._load_from_env()
        if env_config:
            config = self._merge_configs(config, env_config)
            self.logger.info("已从环境变量加载配置")
        
        return config
    
    def _load_from_env(self) -> Dict[str, Any]:
        """从环境变量加载配置
        
        环境变量格式：STONESHARD_SECTION_KEY
        例如：STONESHARD_DATABASE_TYPE
        
        Returns:
            Dict[str, Any]: 从环境变量加载的配置
        """
        env_config = {}
        
        # 遍历所有环境变量
        for key, value in os.environ.items():
            # 只处理STONESHARD_开头的环境变量
            if key.startswith('STONESHARD_'):
                # 移除前缀并分割路径
                path = key[11:].lower().split('_')
                
                # 转换值类型
                typed_value = self._convert_value(value)
                
                # 构建嵌套字典
                current = env_config
                for i, part in enumerate(path):
                    if i == len(path) - 1:
                        current[part] = typed_value
                    else:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
        
        return env_config
    
    def _convert_value(self, value: str) -> Any:
        """转换字符串值为适当的类型
        
        Args:
            value (str): 要转换的字符串值
        
        Returns:
            Any: 转换后的值
        """
        # 尝试转换为布尔值
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        
        # 尝试转换为整数
        try:
            return int(value)
        except ValueError:
            pass
        
        # 尝试转换为浮点数
        try:
            return float(value)
        except ValueError:
            pass
        
        # 尝试转换为列表（逗号分隔）
        if ',' in value:
            return [self._convert_value(item.strip()) for item in value.split(',')]
        
        # 保持为字符串
        return value
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """递归合并配置
        
        Args:
            base (Dict[str, Any]): 基础配置
            override (Dict[str, Any]): 覆盖配置
        
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        result = base.copy()
        
        for key, value in override.items():
            # 如果值是字典且基础配置中也是字典，递归合并
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                # 否则直接覆盖
                result[key] = value
        
        return result
    
    def _validate_config(self) -> None:
        """验证配置
        
        Raises:
            ConfigError: 如果配置无效
        """
        try:
            self._validate_object(self.config, CONFIG_SCHEMA, [])
        except ConfigError as e:
            self.logger.error(f"配置验证失败: {str(e)}")
            # 不抛出异常，使用默认值继续
    
    def _validate_object(self, obj: Dict[str, Any], schema: Dict[str, Any], path: List[str]) -> None:
        """验证对象
        
        Args:
            obj (Dict[str, Any]): 要验证的对象
            schema (Dict[str, Any]): 验证模式
            path (List[str]): 当前路径
        
        Raises:
            ConfigError: 如果对象无效
        """
        # 检查必需字段
        for key, field_schema in schema.items():
            if isinstance(field_schema, dict) and 'required' in field_schema and field_schema['required']:
                if key not in obj:
                    full_path = '.'.join(path + [key])
                    raise ConfigError(f"缺少必需字段: {full_path}")
        
        # 验证每个字段
        for key, value in obj.items():
            if key in schema:
                field_schema = schema[key]
                
                # 如果字段模式是字典且没有type字段，则它是一个嵌套对象
                if isinstance(field_schema, dict) and 'type' not in field_schema:
                    if not isinstance(value, dict):
                        full_path = '.'.join(path + [key])
                        raise ConfigError(f"字段 {full_path} 应该是一个对象")
                    
                    # 递归验证嵌套对象
                    self._validate_object(value, field_schema, path + [key])
                else:
                    # 验证字段值
                    self._validate_field(value, field_schema, path + [key])
    
    def _validate_field(self, value: Any, schema: Dict[str, Any], path: List[str]) -> None:
        """验证字段
        
        Args:
            value (Any): 要验证的值
            schema (Dict[str, Any]): 字段模式
            path (List[str]): 当前路径
        
        Raises:
            ConfigError: 如果字段无效
        """
        full_path = '.'.join(path)
        
        # 检查类型
        expected_type = schema.get('type')
        if expected_type:
            if expected_type == list and not isinstance(value, list):
                raise ConfigError(f"字段 {full_path} 应该是一个列表")
            elif expected_type == dict and not isinstance(value, dict):
                raise ConfigError(f"字段 {full_path} 应该是一个字典")
            elif expected_type == str and not isinstance(value, str):
                raise ConfigError(f"字段 {full_path} 应该是一个字符串")
            elif expected_type == int and not isinstance(value, int):
                raise ConfigError(f"字段 {full_path} 应该是一个整数")
            elif expected_type == float and not isinstance(value, (int, float)):
                raise ConfigError(f"字段 {full_path} 应该是一个浮点数")
            elif expected_type == bool and not isinstance(value, bool):
                raise ConfigError(f"字段 {full_path} 应该是一个布尔值")
        
        # 检查选项
        choices = schema.get('choices')
        if choices and value not in choices:
            raise ConfigError(f"字段 {full_path} 的值应该是以下之一: {', '.join(choices)}")
        
        # 检查最小值
        min_value = schema.get('min')
        if min_value is not None and value < min_value:
            raise ConfigError(f"字段 {full_path} 的值应该大于或等于 {min_value}")
        
        # 检查最大值
        max_value = schema.get('max')
        if max_value is not None and value > max_value:
            raise ConfigError(f"字段 {full_path} 的值应该小于或等于 {max_value}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key (str): 配置键
            default (Any, optional): 默认值
        
        Returns:
            Any: 配置值
        """
        # 支持点号分隔的路径
        parts = key.split('.')
        value = self.config
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key (str): 配置键
            value (Any): 配置值
        """
        # 支持点号分隔的路径
        parts = key.split('.')
        target = self.config
        
        # 遍历路径
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # 最后一部分，设置值
                target[part] = value
                # 同时更新实例属性
                if i == 0:
                    setattr(self, part, value)
            else:
                # 中间部分，确保路径存在
                if part not in target:
                    target[part] = {}
                target = target[part]
    
    def save(self, path: str) -> None:
        """保存配置到文件
        
        Args:
            path (str): 文件路径
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            
            # 保存配置
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"已保存配置到 {path}")
        except Exception as e:
            self.logger.error(f"无法保存配置到 {path}: {str(e)}")
    
    def __getitem__(self, key: str) -> Any:
        """获取配置值（字典访问语法）
        
        Args:
            key (str): 配置键
        
        Returns:
            Any: 配置值
        
        Raises:
            KeyError: 如果键不存在
        """
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value
    
    def __setitem__(self, key: str, value: Any) -> None:
        """设置配置值（字典访问语法）
        
        Args:
            key (str): 配置键
            value (Any): 配置值
        """
        self.set(key, value)
    
    def __contains__(self, key: str) -> bool:
        """检查键是否存在（in运算符）
        
        Args:
            key (str): 配置键
        
        Returns:
            bool: 如果键存在则为True
        """
        return self.get(key) is not None 