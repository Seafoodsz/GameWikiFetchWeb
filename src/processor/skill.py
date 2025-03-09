#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 技能数据处理器
"""

from .base import BaseProcessor
import re
import json
import logging
import os

class SkillProcessor(BaseProcessor):
    """技能数据处理器，处理技能相关数据"""
    
    def __init__(self, input_dir, output_dir, config=None):
        """初始化技能处理器"""
        super().__init__(input_dir, output_dir, config)
        self.keywords = config.get('keywords', ["技能", "效果", "冷却", "消耗"])
        self.logger.info(f"技能处理器初始化完成，关键词: {self.keywords}")
    
    def process(self):
        """处理技能数据"""
        self.logger.info("开始处理技能数据")
        
        # 获取输入文件
        input_files = self.get_input_files()
        if not input_files:
            self.logger.warning("没有找到技能数据文件")
            return False
        
        # 处理每个文件
        skills = []
        for file_path in input_files:
            self.logger.info(f"处理文件: {file_path}")
            
            # 加载HTML
            soup = self.load_html(file_path)
            if not soup:
                continue
            
            # 提取数据
            skill_data = self.extract_data(soup, file_path)
            if not skill_data:
                self.logger.warning(f"无法从文件中提取技能数据: {file_path}")
                continue
            
            # 清理数据
            skill_data = self.clean_data(skill_data)
            
            # 验证数据
            if not self.validate_data(skill_data):
                self.logger.warning(f"技能数据验证失败: {file_path}")
                continue
            
            skills.append(skill_data)
        
        # 保存处理结果
        if skills:
            output_file = "skill.json"
            self.save_output(skills, output_file)
            self.logger.info(f"技能数据处理完成，共处理 {len(skills)} 个技能")
            return True
        else:
            self.logger.warning("没有处理到任何技能数据")
            return False
    
    def extract_data(self, soup, file_path):
        """从HTML中提取技能数据"""
        try:
            # 获取技能名称
            title = soup.find('title')
            skill_name = title.text.strip() if title else os.path.basename(file_path).replace('.html', '')
            
            # 基本数据结构
            skill_data = {
                "id": self._generate_id(skill_name),
                "name": skill_name,
                "type": "skill",
                "skill_type": "",
                "skill_tree": "",
                "description": "",
                "effects": [],
                "requirements": {},
                "cooldown": 0,
                "energy_cost": 0,
                "level_requirements": []
            }
            
            # 提取描述
            description_elem = soup.find(['p', 'div'], class_=['description', 'intro', 'summary'])
            if description_elem:
                skill_data["description"] = description_elem.text.strip()
            
            # 提取技能类型
            skill_type_elem = soup.find(['span', 'div'], class_=['skill-type', 'type'])
            if skill_type_elem:
                skill_data["skill_type"] = skill_type_elem.text.strip()
            
            # 提取技能树
            skill_tree_elem = soup.find(['span', 'div'], class_=['skill-tree', 'tree'])
            if skill_tree_elem:
                skill_data["skill_tree"] = skill_tree_elem.text.strip()
            
            # 提取技能属性
            attributes_table = soup.find('table', class_=['attributes', 'stats', 'properties'])
            if attributes_table:
                for row in attributes_table.find_all('tr'):
                    cells = row.find_all(['th', 'td'])
                    if len(cells) >= 2:
                        attr_name = cells[0].text.strip()
                        attr_value = cells[1].text.strip()
                        
                        # 处理特殊属性
                        if "冷却" in attr_name:
                            try:
                                skill_data["cooldown"] = int(re.search(r'\d+', attr_value).group())
                            except (ValueError, AttributeError):
                                pass
                        elif "能量" in attr_name or "消耗" in attr_name:
                            try:
                                skill_data["energy_cost"] = int(re.search(r'\d+', attr_value).group())
                            except (ValueError, AttributeError):
                                pass
                        elif "类型" in attr_name:
                            skill_data["skill_type"] = attr_value
                        elif "技能树" in attr_name:
                            skill_data["skill_tree"] = attr_value
            
            # 提取效果
            effects_list = soup.find(['ul', 'ol'], class_=['effects', 'bonuses'])
            if effects_list:
                for effect_item in effects_list.find_all('li'):
                    effect_text = effect_item.text.strip()
                    skill_data["effects"].append(effect_text)
            
            # 提取需求
            requirements_table = soup.find('table', class_=['requirements', 'prereqs'])
            if requirements_table:
                for row in requirements_table.find_all('tr'):
                    cells = row.find_all(['th', 'td'])
                    if len(cells) >= 2:
                        req_name = cells[0].text.strip()
                        req_value = cells[1].text.strip()
                        # 尝试转换为数字
                        try:
                            req_value = int(req_value)
                        except ValueError:
                            try:
                                req_value = float(req_value)
                            except ValueError:
                                pass
                        skill_data["requirements"][req_name] = req_value
            
            # 提取等级需求
            level_reqs_list = soup.find(['ul', 'ol'], class_=['level-requirements', 'levels'])
            if level_reqs_list:
                for level_item in level_reqs_list.find_all('li'):
                    level_text = level_item.text.strip()
                    skill_data["level_requirements"].append(level_text)
            
            return skill_data
            
        except Exception as e:
            self.logger.error(f"提取技能数据时出错: {str(e)}", exc_info=True)
            return None
    
    def _generate_id(self, name):
        """根据名称生成ID"""
        # 移除非字母数字字符，转换为小写
        id_str = re.sub(r'[^\w]', '_', name.lower())
        # 确保ID不以数字开头
        if id_str[0].isdigit():
            id_str = 's_' + id_str
        return id_str 