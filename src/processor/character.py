#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 角色数据处理器
"""

from .base import BaseProcessor
import re
import json
import logging
import os

class CharacterProcessor(BaseProcessor):
    """角色数据处理器，处理角色相关数据"""
    
    def __init__(self, input_dir, output_dir, config=None):
        """初始化角色处理器"""
        super().__init__(input_dir, output_dir, config)
        self.keywords = config.get('keywords', ["职业", "属性", "技能树", "特性"])
        self.logger.info(f"角色处理器初始化完成，关键词: {self.keywords}")
    
    def process(self):
        """处理角色数据"""
        self.logger.info("开始处理角色数据")
        
        # 获取输入文件
        input_files = self.get_input_files()
        if not input_files:
            self.logger.warning("没有找到角色数据文件")
            return False
        
        # 处理每个文件
        characters = []
        for file_path in input_files:
            self.logger.info(f"处理文件: {file_path}")
            
            # 加载HTML
            soup = self.load_html(file_path)
            if not soup:
                continue
            
            # 提取数据
            character_data = self.extract_data(soup, file_path)
            if not character_data:
                self.logger.warning(f"无法从文件中提取角色数据: {file_path}")
                continue
            
            # 清理数据
            character_data = self.clean_data(character_data)
            
            # 验证数据
            if not self.validate_data(character_data):
                self.logger.warning(f"角色数据验证失败: {file_path}")
                continue
            
            characters.append(character_data)
        
        # 保存处理结果
        if characters:
            output_file = "character.json"
            self.save_output(characters, output_file)
            self.logger.info(f"角色数据处理完成，共处理 {len(characters)} 个角色")
            return True
        else:
            self.logger.warning("没有处理到任何角色数据")
            return False
    
    def extract_data(self, soup, file_path):
        """从HTML中提取角色数据"""
        try:
            # 获取角色名称
            title = soup.find('title')
            character_name = title.text.strip() if title else os.path.basename(file_path).replace('.html', '')
            
            # 基本数据结构
            character_data = {
                "id": self._generate_id(character_name),
                "name": character_name,
                "type": "character",
                "description": "",
                "attributes": {},
                "skills": [],
                "traits": []
            }
            
            # 提取描述
            description_elem = soup.find(['p', 'div'], class_=['description', 'intro', 'summary'])
            if description_elem:
                character_data["description"] = description_elem.text.strip()
            
            # 提取属性
            attributes_table = soup.find('table', class_=['attributes', 'stats'])
            if attributes_table:
                for row in attributes_table.find_all('tr'):
                    cells = row.find_all(['th', 'td'])
                    if len(cells) >= 2:
                        attr_name = cells[0].text.strip()
                        attr_value = cells[1].text.strip()
                        # 尝试转换为数字
                        try:
                            attr_value = int(attr_value)
                        except ValueError:
                            try:
                                attr_value = float(attr_value)
                            except ValueError:
                                pass
                        character_data["attributes"][attr_name] = attr_value
            
            # 提取技能
            skills_list = soup.find(['ul', 'ol'], class_=['skills', 'abilities'])
            if skills_list:
                for skill_item in skills_list.find_all('li'):
                    skill_name = skill_item.text.strip()
                    character_data["skills"].append(skill_name)
            
            # 提取特性
            traits_list = soup.find(['ul', 'ol'], class_=['traits', 'perks'])
            if traits_list:
                for trait_item in traits_list.find_all('li'):
                    trait_name = trait_item.text.strip()
                    character_data["traits"].append(trait_name)
            
            return character_data
            
        except Exception as e:
            self.logger.error(f"提取角色数据时出错: {str(e)}", exc_info=True)
            return None
    
    def _generate_id(self, name):
        """根据名称生成ID"""
        # 移除非字母数字字符，转换为小写
        id_str = re.sub(r'[^\w]', '_', name.lower())
        # 确保ID不以数字开头
        if id_str[0].isdigit():
            id_str = 'c_' + id_str
        return id_str 