#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 物品数据处理器
"""

from .base import BaseProcessor
import re
import json
import logging
import os

class ItemProcessor(BaseProcessor):
    """物品数据处理器，处理物品相关数据"""
    
    def __init__(self, input_dir, output_dir, config=None):
        """初始化物品处理器"""
        super().__init__(input_dir, output_dir, config)
        self.categories = config.get('categories', ["武器", "护甲", "消耗品", "材料", "宝石"])
        self.keywords = config.get('keywords', ["类型", "伤害", "防御", "效果", "价值"])
        self.logger.info(f"物品处理器初始化完成，分类: {self.categories}, 关键词: {self.keywords}")
    
    def process(self):
        """处理物品数据"""
        self.logger.info("开始处理物品数据")
        
        # 获取输入文件
        input_files = self.get_input_files()
        if not input_files:
            self.logger.warning("没有找到物品数据文件")
            return False
        
        # 处理每个文件
        items = []
        for file_path in input_files:
            self.logger.info(f"处理文件: {file_path}")
            
            # 根据文件扩展名选择加载方法
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.html':
                soup = self.load_html(file_path)
            elif file_ext == '.md':
                soup = self.load_markdown(file_path)
            else:
                self.logger.warning(f"不支持的文件类型: {file_ext}")
                continue
                
            if not soup:
                continue
            
            # 提取数据
            item_data = self.extract_data(soup, file_path)
            if not item_data:
                self.logger.warning(f"无法从文件中提取物品数据: {file_path}")
                continue
            
            # 清理数据
            item_data = self.clean_data(item_data)
            
            # 验证数据
            if not self.validate_data(item_data):
                self.logger.warning(f"物品数据验证失败: {file_path}")
                continue
            
            items.append(item_data)
        
        # 保存处理结果
        if items:
            output_file = "item.json"
            self.save_output(items, output_file)
            self.logger.info(f"物品数据处理完成，共处理 {len(items)} 个物品")
            return True
        else:
            self.logger.warning("没有处理到任何物品数据")
            return False
    
    def extract_data(self, soup, file_path):
        """从HTML或Markdown中提取物品数据"""
        try:
            # 获取物品名称
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.md':
                # 从Markdown文件名或h1标签获取物品名称
                h1_tag = soup.find('h1')
                if h1_tag:
                    item_name = h1_tag.text.strip()
                else:
                    item_name = os.path.basename(file_path).replace('.md', '').replace('_', ' ')
            else:
                # 从HTML标题获取物品名称
                title = soup.find('title')
                item_name = title.text.strip() if title else os.path.basename(file_path).replace('.html', '').replace('_', ' ')
            
            # 基本数据结构
            item_data = {
                "id": self._generate_id(item_name),
                "name": item_name,
                "type": "item",
                "category": "",
                "item_type": "",
                "description": "",
                "attributes": {},
                "effects": [],
                "requirements": {},
                "value": 0,
                "weight": 0
            }
            
            # 提取描述
            if file_ext == '.md':
                # 从Markdown中提取描述（第一个非标题、非URL的段落）
                for p in soup.find_all(['p', 'div']):
                    if p.get('class') != 'url' and not p.find_parent('ul') and p.text.strip():
                        item_data["description"] = p.text.strip()
                        break
                
                # 从列表项中提取分类和属性
                categories_found = []
                for li in soup.find_all('li'):
                    li_text = li.text.strip()
                    
                    # 检查是否为物品分类
                    for cat in self.categories:
                        if cat in li_text:
                            categories_found.append(cat)
                    
                    # 检查是否为属性信息
                    for keyword in self.keywords:
                        if keyword in li_text:
                            # 尝试提取属性值
                            parts = li_text.split(':', 1)
                            if len(parts) == 2:
                                attr_name = parts[0].strip()
                                attr_value = parts[1].strip()
                                
                                # 处理特殊属性
                                if "价值" in attr_name or "价格" in attr_name:
                                    try:
                                        item_data["value"] = int(re.search(r'\d+', attr_value).group())
                                    except (ValueError, AttributeError):
                                        pass
                                elif "重量" in attr_name:
                                    try:
                                        item_data["weight"] = float(re.search(r'\d+(\.\d+)?', attr_value).group())
                                    except (ValueError, AttributeError):
                                        pass
                                elif "类型" in attr_name:
                                    item_data["item_type"] = attr_value
                                else:
                                    # 尝试转换为数字
                                    try:
                                        attr_value = int(attr_value)
                                    except ValueError:
                                        try:
                                            attr_value = float(attr_value)
                                        except ValueError:
                                            pass
                                    item_data["attributes"][attr_name] = attr_value
                
                # 设置分类（如果找到多个，使用第一个）
                if categories_found:
                    item_data["category"] = categories_found[0]
            else:
                # 原有的HTML提取逻辑
                description_elem = soup.find(['p', 'div'], class_=['description', 'intro', 'summary'])
                if description_elem:
                    item_data["description"] = description_elem.text.strip()
                
                # 提取物品类别
                category_elem = soup.find(['span', 'div'], class_=['category', 'type'])
                if category_elem:
                    category_text = category_elem.text.strip()
                    for cat in self.categories:
                        if cat in category_text:
                            item_data["category"] = cat
                            break
                
                # 提取物品属性
                attributes_table = soup.find('table', class_=['attributes', 'stats', 'properties'])
                if attributes_table:
                    for row in attributes_table.find_all('tr'):
                        cells = row.find_all(['th', 'td'])
                        if len(cells) >= 2:
                            attr_name = cells[0].text.strip()
                            attr_value = cells[1].text.strip()
                            
                            # 处理特殊属性
                            if "价值" in attr_name or "价格" in attr_name:
                                try:
                                    item_data["value"] = int(re.search(r'\d+', attr_value).group())
                                except (ValueError, AttributeError):
                                    pass
                            elif "重量" in attr_name:
                                try:
                                    item_data["weight"] = float(re.search(r'\d+(\.\d+)?', attr_value).group())
                                except (ValueError, AttributeError):
                                    pass
                            elif "类型" in attr_name:
                                item_data["item_type"] = attr_value
                            else:
                                # 尝试转换为数字
                                try:
                                    attr_value = int(attr_value)
                                except ValueError:
                                    try:
                                        attr_value = float(attr_value)
                                    except ValueError:
                                        pass
                                item_data["attributes"][attr_name] = attr_value
                
                # 提取效果
                effects_list = soup.find(['ul', 'ol'], class_=['effects', 'bonuses'])
                if effects_list:
                    for effect_item in effects_list.find_all('li'):
                        effect_text = effect_item.text.strip()
                        item_data["effects"].append(effect_text)
                
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
                            item_data["requirements"][req_name] = req_value
            
            return item_data
            
        except Exception as e:
            self.logger.error(f"提取物品数据时出错: {str(e)}", exc_info=True)
            return None
    
    def _generate_id(self, name):
        """根据名称生成ID"""
        # 移除非字母数字字符，转换为小写
        id_str = re.sub(r'[^\w]', '_', name.lower())
        # 确保ID不以数字开头
        if id_str[0].isdigit():
            id_str = 'i_' + id_str
        return id_str 