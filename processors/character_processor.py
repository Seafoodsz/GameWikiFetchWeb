#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
角色处理器模块
处理角色数据
"""

import os
import re
from bs4 import BeautifulSoup
from utils.logger import exception_handler
from processors.base_processor import BaseProcessor

class CharacterProcessor(BaseProcessor):
    """角色处理器类"""
    
    def __init__(self, config, db_manager):
        """初始化角色处理器
        
        Args:
            config (Config): 配置对象
            db_manager (DatabaseManager): 数据库管理器
        """
        super().__init__(config, db_manager, "character")
        
        # 关键词列表
        self.keywords = self.processor_config.get("keywords", ["职业", "属性", "技能树", "特性"])
    
    @exception_handler
    def _process_file(self, file_path):
        """处理角色文件
        
        Args:
            file_path (str): 文件路径
        
        Returns:
            dict: 处理后的角色数据
        """
        self.logger.info(f"处理角色文件: {file_path}")
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取角色名称
            character_name = soup.find('h1').text.strip()
            character_id = self._generate_id(character_name)
            
            # 提取角色描述
            description = soup.find('p').text.strip()
            
            # 创建角色数据
            character_data = {
                "id": character_id,
                "name": character_name,
                "type": "character",
                "description": description,
                "attributes": self._extract_attributes(soup),
                "skills": self._extract_skills(soup),
                "traits": self._extract_traits(soup),
                "starting_items": self._extract_starting_items(soup)
            }
            
            return character_data
        except Exception as e:
            self.logger.error(f"处理角色文件 {file_path} 时出错: {str(e)}")
            return None
    
    def _generate_id(self, name):
        """生成角色ID
        
        Args:
            name (str): 角色名称
        
        Returns:
            str: 角色ID
        """
        # 转换为小写，移除非字母数字字符
        return re.sub(r'[^a-z0-9]', '_', name.lower())
    
    def _extract_attributes(self, soup):
        """提取角色属性
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            dict: 角色属性
        """
        attributes = {}
        
        # 查找属性部分
        attr_section = soup.find('h2', text=re.compile('属性', re.IGNORECASE))
        if attr_section and attr_section.find_next('ul'):
            attr_list = attr_section.find_next('ul').find_all('li')
            for attr in attr_list:
                attr_text = attr.text.strip()
                if ':' in attr_text:
                    name, value = attr_text.split(':', 1)
                    try:
                        attributes[name.strip().lower()] = int(value.strip())
                    except ValueError:
                        attributes[name.strip().lower()] = value.strip()
        
        return attributes
    
    def _extract_skills(self, soup):
        """提取角色技能
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            list: 角色技能列表
        """
        skills = []
        
        # 查找技能树部分
        skill_section = soup.find('h2', text=re.compile('技能树', re.IGNORECASE))
        if skill_section and skill_section.find_next('ul'):
            skill_list = skill_section.find_next('ul').find_all('li')
            for skill in skill_list:
                skills.append(skill.text.strip())
        
        return skills
    
    def _extract_traits(self, soup):
        """提取角色特性
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            list: 角色特性列表
        """
        traits = []
        
        # 查找特性部分
        trait_section = soup.find('h2', text=re.compile('特性', re.IGNORECASE))
        if trait_section and trait_section.find_next('ul'):
            trait_list = trait_section.find_next('ul').find_all('li')
            for trait in trait_list:
                trait_text = trait.text.strip()
                if ':' in trait_text:
                    name, desc = trait_text.split(':', 1)
                    traits.append({
                        "name": name.strip(),
                        "description": desc.strip()
                    })
                else:
                    traits.append({
                        "name": trait_text,
                        "description": ""
                    })
        
        return traits
    
    def _extract_starting_items(self, soup):
        """提取角色起始装备
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
        
        Returns:
            list: 角色起始装备列表
        """
        items = []
        
        # 查找起始装备部分
        item_section = soup.find('h2', text=re.compile('起始装备', re.IGNORECASE))
        if item_section and item_section.find_next('ul'):
            item_list = item_section.find_next('ul').find_all('li')
            for item in item_list:
                items.append(item.text.strip())
        
        return items 