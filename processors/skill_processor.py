#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
技能处理器模块
处理技能数据
"""

import os
import re
from bs4 import BeautifulSoup
from utils.logger import exception_handler
from processors.base_processor import BaseProcessor

class SkillProcessor(BaseProcessor):
    """技能处理器类"""
    
    def __init__(self, config, db_manager):
        """初始化技能处理器
        
        Args:
            config (Config): 配置对象
            db_manager (DatabaseManager): 数据库管理器
        """
        super().__init__(config, db_manager, "skill")
        
        # 关键词列表
        self.keywords = self.processor_config.get("keywords", ["技能", "效果", "冷却", "消耗"])
    
    @exception_handler
    def _process_file(self, file_path):
        """处理技能文件
        
        Args:
            file_path (str): 文件路径
        
        Returns:
            dict: 处理后的技能数据
        """
        self.logger.info(f"处理技能文件: {file_path}")
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取技能名称
            skill_name = soup.find('h1').text.strip()
            skill_id = self._generate_id(skill_name)
            
            # 提取技能描述
            description = soup.find('p').text.strip()
            
            # 提取技能类型和技能树
            skill_type, skill_tree = self._extract_skill_info(soup)
            
            # 创建技能数据
            skill_data = {
                "id": skill_id,
                "name": skill_name,
                "type": "skill",
                "skill_type": skill_type,
                "skill_tree": skill_tree,
                "description": description,
                "effects": self._extract_effects(soup),
                "cooldown": self._extract_cooldown(soup),
                "energy_cost": self._extract_energy_cost(soup),
                "requirements": self._extract_requirements(soup)
            }
            
            return skill_data
        except Exception as e:
            self.logger.error(f"处理技能文件 {file_path} 时出错: {str(e)}")
            return None
    
    def _generate_id(self, name):
        """生成技能ID
        
        Args:
            name (str): 技能名称
        
        Returns:
            str: 技能ID
        """
        # 转换为小写，移除非字母数字字符
        return re.sub(r'[^a-z0-9]', '_', name.lower())
    
    def _extract_skill_info(self, soup):
        """提取技能类型和技能树
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            tuple: (技能类型, 技能树)
        """
        skill_type = "passive"  # 默认为被动技能
        skill_tree = "general"  # 默认为通用技能树
        
        # 查找技能部分
        skill_section = soup.find('h2', text=re.compile('技能', re.IGNORECASE))
        if skill_section and skill_section.find_next('ul'):
            skill_list = skill_section.find_next('ul').find_all('li')
            for skill in skill_list:
                skill_text = skill.text.strip()
                if ':' in skill_text:
                    name, value = skill_text.split(':', 1)
                    name = name.strip().lower()
                    value = value.strip()
                    
                    if name == "类型":
                        if "主动" in value:
                            skill_type = "active"
                        elif "被动" in value:
                            skill_type = "passive"
                    elif name == "技能树":
                        skill_tree = value
        
        return skill_type, skill_tree
    
    def _extract_effects(self, soup):
        """提取技能效果
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            list: 技能效果列表
        """
        effects = []
        
        # 查找效果部分
        effect_section = soup.find('h2', text=re.compile('效果', re.IGNORECASE))
        if effect_section and effect_section.find_next('ul'):
            effect_list = effect_section.find_next('ul').find_all('li')
            for effect in effect_list:
                effects.append(effect.text.strip())
        
        return effects
    
    def _extract_cooldown(self, soup):
        """提取技能冷却时间
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            int: 技能冷却时间
        """
        cooldown = 0
        
        # 查找冷却部分
        cooldown_section = soup.find('h2', text=re.compile('冷却', re.IGNORECASE))
        if cooldown_section and cooldown_section.find_next('p'):
            cooldown_text = cooldown_section.find_next('p').text.strip()
            # 提取数字
            cooldown_match = re.search(r'\d+', cooldown_text)
            if cooldown_match:
                cooldown = int(cooldown_match.group())
        
        return cooldown
    
    def _extract_energy_cost(self, soup):
        """提取技能能量消耗
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            int: 技能能量消耗
        """
        energy_cost = 0
        
        # 查找消耗部分
        cost_section = soup.find('h2', text=re.compile('消耗', re.IGNORECASE))
        if cost_section and cost_section.find_next('ul'):
            cost_list = cost_section.find_next('ul').find_all('li')
            for cost in cost_list:
                cost_text = cost.text.strip()
                if '能量' in cost_text and ':' in cost_text:
                    _, value = cost_text.split(':', 1)
                    # 提取数字
                    cost_match = re.search(r'\d+', value)
                    if cost_match:
                        energy_cost = int(cost_match.group())
        
        return energy_cost
    
    def _extract_requirements(self, soup):
        """提取技能需求
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            dict: 技能需求
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