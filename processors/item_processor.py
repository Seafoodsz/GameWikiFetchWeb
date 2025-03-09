#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
物品处理器模块
处理物品数据
"""

import os
import re
from bs4 import BeautifulSoup
from utils.logger import exception_handler
from processors.base_processor import BaseProcessor

class ItemProcessor(BaseProcessor):
    """物品处理器类"""
    
    def __init__(self, config, db_manager):
        """初始化物品处理器
        
        Args:
            config (Config): 配置对象
            db_manager (DatabaseManager): 数据库管理器
        """
        super().__init__(config, db_manager, "item")
        
        # 物品类别
        self.categories = self.processor_config.get("categories", ["武器", "护甲", "消耗品", "材料", "宝石"])
        
        # 关键词列表
        self.keywords = self.processor_config.get("keywords", ["类型", "伤害", "防御", "效果", "价值"])
    
    @exception_handler
    def _process_file(self, file_path):
        """处理物品文件
        
        Args:
            file_path (str): 文件路径
        
        Returns:
            dict: 处理后的物品数据
        """
        self.logger.info(f"处理物品文件: {file_path}")
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取物品名称
            item_name = soup.find('h1').text.strip()
            item_id = self._generate_id(item_name)
            
            # 提取物品描述
            description = soup.find('p').text.strip()
            
            # 提取物品类别和类型
            category, item_type = self._extract_item_type(soup)
            
            # 创建物品数据
            item_data = {
                "id": item_id,
                "name": item_name,
                "type": "item",
                "category": category,
                "item_type": item_type,
                "description": description,
                "attributes": self._extract_attributes(soup),
                "effects": self._extract_effects(soup),
                "requirements": self._extract_requirements(soup),
                "value": self._extract_value(soup),
                "weight": self._extract_weight(soup)
            }
            
            return item_data
        except Exception as e:
            self.logger.error(f"处理物品文件 {file_path} 时出错: {str(e)}")
            return None
    
    def _generate_id(self, name):
        """生成物品ID
        
        Args:
            name (str): 物品名称
        
        Returns:
            str: 物品ID
        """
        # 转换为小写，移除非字母数字字符
        return re.sub(r'[^a-z0-9]', '_', name.lower())
    
    def _extract_item_type(self, soup):
        """提取物品类别和类型
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            tuple: (类别, 类型)
        """
        category = "misc"  # 默认为杂项
        item_type = "general"  # 默认为通用类型
        
        # 查找类型部分
        type_section = soup.find('h2', text=re.compile('类型', re.IGNORECASE))
        if type_section and type_section.find_next('ul'):
            type_list = type_section.find_next('ul').find_all('li')
            if len(type_list) > 0:
                # 第一个项目通常是类别
                category_text = type_list[0].text.strip().lower()
                for cat in self.categories:
                    if cat.lower() in category_text:
                        category = cat.lower()
                        break
            
            if len(type_list) > 1:
                # 第二个项目通常是具体类型
                item_type = type_list[1].text.strip().lower()
        
        return category, item_type
    
    def _extract_attributes(self, soup):
        """提取物品属性
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            dict: 物品属性
        """
        attributes = {}
        
        # 查找伤害部分
        damage_section = soup.find('h2', text=re.compile('伤害', re.IGNORECASE))
        if damage_section and damage_section.find_next('ul'):
            damage_list = damage_section.find_next('ul').find_all('li')
            for damage in damage_list:
                damage_text = damage.text.strip()
                if ':' in damage_text:
                    name, value = damage_text.split(':', 1)
                    name = name.strip().lower()
                    value = value.strip()
                    
                    # 处理范围值（如8-12）
                    if '-' in value:
                        min_val, max_val = value.split('-', 1)
                        try:
                            attributes[f"{name}_min"] = int(min_val.strip())
                            attributes[f"{name}_max"] = int(max_val.strip())
                        except ValueError:
                            attributes[name] = value
                    else:
                        # 尝试转换为数字
                        try:
                            attributes[name] = int(value)
                        except ValueError:
                            attributes[name] = value
        
        # 查找防御部分
        defense_section = soup.find('h2', text=re.compile('防御', re.IGNORECASE))
        if defense_section and defense_section.find_next('ul'):
            defense_list = defense_section.find_next('ul').find_all('li')
            for defense in defense_list:
                defense_text = defense.text.strip()
                if ':' in defense_text:
                    name, value = defense_text.split(':', 1)
                    name = name.strip().lower()
                    value = value.strip()
                    
                    # 处理百分比值
                    if '%' in value:
                        try:
                            attributes[name] = float(value.replace('%', '')) / 100
                        except ValueError:
                            attributes[name] = value
                    else:
                        # 尝试转换为数字
                        try:
                            attributes[name] = int(value)
                        except ValueError:
                            attributes[name] = value
        
        return attributes
    
    def _extract_effects(self, soup):
        """提取物品效果
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            list: 物品效果列表
        """
        effects = []
        
        # 查找效果部分
        effect_section = soup.find('h2', text=re.compile('效果', re.IGNORECASE))
        if effect_section and effect_section.find_next('ul'):
            effect_list = effect_section.find_next('ul').find_all('li')
            for effect in effect_list:
                effect_text = effect.text.strip()
                if ':' in effect_text:
                    name, value = effect_text.split(':', 1)
                    effects.append({
                        "name": name.strip(),
                        "value": value.strip()
                    })
                else:
                    effects.append({
                        "name": effect_text,
                        "value": ""
                    })
        
        return effects
    
    def _extract_requirements(self, soup):
        """提取物品需求
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            dict: 物品需求
        """
        requirements = {}
        
        # 查找需求部分
        req_section = soup.find('h2', text=re.compile('需求', re.IGNORECASE))
        if req_section and req_section.find_next('ul'):
            req_list = req_section.find_next('ul').find_all('li')
            for req in req_list:
                req_text = req.text.strip()
                if ':' in req_text:
                    name, value = req_text.split(':', 1)
                    name = name.strip().lower()
                    value = value.strip()
                    
                    # 尝试转换为数字
                    try:
                        requirements[name] = int(value)
                    except ValueError:
                        requirements[name] = value
        
        return requirements
    
    def _extract_value(self, soup):
        """提取物品价值
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            int: 物品价值
        """
        value = 0
        
        # 查找价值部分
        value_section = soup.find('h2', text=re.compile('价值', re.IGNORECASE))
        if value_section and value_section.find_next('p'):
            value_text = value_section.find_next('p').text.strip()
            # 提取数字
            value_match = re.search(r'\d+', value_text)
            if value_match:
                value = int(value_match.group())
        
        return value
    
    def _extract_weight(self, soup):
        """提取物品重量
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            float: 物品重量
        """
        weight = 0.0
        
        # 查找重量部分
        weight_section = soup.find('h2', text=re.compile('重量', re.IGNORECASE))
        if weight_section and weight_section.find_next('p'):
            weight_text = weight_section.find_next('p').text.strip()
            # 提取数字（包括小数）
            weight_match = re.search(r'\d+(\.\d+)?', weight_text)
            if weight_match:
                weight = float(weight_match.group())
        
        return weight 