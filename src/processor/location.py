#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 地点数据处理器
"""

from .base import BaseProcessor
import re
import json
import logging
import os

class LocationProcessor(BaseProcessor):
    """地点数据处理器，处理地点相关数据"""
    
    def __init__(self, input_dir, output_dir, config=None):
        """初始化地点处理器"""
        super().__init__(input_dir, output_dir, config)
        self.keywords = config.get('keywords', ["区域", "NPC", "资源", "任务", "敌人", "Quests", "Enemies", "Resources"])
        self.logger.info(f"地点处理器初始化完成，关键词: {self.keywords}")
    
    def process(self):
        """处理地点数据"""
        self.logger.info("开始处理地点数据")
        
        # 获取输入文件
        input_files = self.get_input_files()
        if not input_files:
            self.logger.warning("没有找到地点数据文件")
            return False
        
        # 处理每个文件
        locations = []
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
            location_data = self.extract_data(soup, file_path)
            if not location_data:
                self.logger.warning(f"无法从文件中提取地点数据: {file_path}")
                continue
            
            # 清理数据
            location_data = self.clean_data(location_data)
            
            # 验证数据
            if not self.validate_data(location_data):
                self.logger.warning(f"地点数据验证失败: {file_path}")
                continue
            
            locations.append(location_data)
        
        # 保存处理结果
        if locations:
            output_file = "location.json"
            self.save_output(locations, output_file)
            self.logger.info(f"地点数据处理完成，共处理 {len(locations)} 个地点")
            return True
        else:
            self.logger.warning("没有处理到任何地点数据")
            return False
    
    def extract_data(self, soup, file_path):
        """从HTML或Markdown中提取地点数据"""
        try:
            # 获取地点名称
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.md':
                # 从Markdown文件名或h1标签获取地点名称
                h1_tag = soup.find('h1')
                if h1_tag:
                    location_name = h1_tag.text.strip()
                else:
                    location_name = os.path.basename(file_path).replace('.md', '').replace('_', ' ')
            else:
                # 从HTML标题获取地点名称
                title = soup.find('title')
                location_name = title.text.strip() if title else os.path.basename(file_path).replace('.html', '').replace('_', ' ')
            
            # 基本数据结构
            location_data = {
                "id": self._generate_id(location_name),
                "name": location_name,
                "type": "location",
                "location_type": "",
                "description": "",
                "region": "",
                "coordinates": {
                    "x": 0,
                    "y": 0
                },
                "npcs": [],
                "enemies": [],
                "resources": [],
                "quests": [],
                "connections": []
            }
            
            # 提取描述和其他数据
            if file_ext == '.md':
                # 从Markdown中提取描述（第一个非标题、非URL的段落）
                for p in soup.find_all(['p', 'div']):
                    if p.get('class') != 'url' and not p.find_parent('ul') and p.text.strip():
                        location_data["description"] = p.text.strip()
                        break
                
                # 设置URL作为描述（如果没有找到更好的描述）
                if not location_data["description"]:
                    url_elem = soup.find('div', class_='url')
                    if url_elem and url_elem.text.strip():
                        location_data["description"] = url_elem.text.strip()
                
                # 查找任务相关的标题
                quest_sections = []
                for heading in soup.find_all(['h2', 'h3']):
                    heading_text = heading.text.strip().lower()
                    if any(keyword.lower() in heading_text for keyword in ["任务", "quests", "missions", "objectives"]):
                        quest_sections.append(heading)
                
                # 从任务相关的标题下的列表中提取任务
                for section in quest_sections:
                    next_elem = section.find_next_sibling()
                    while next_elem and next_elem.name not in ['h2', 'h3']:
                        if next_elem.name in ['ul', 'ol']:
                            for li in next_elem.find_all('li'):
                                quest_text = li.text.strip()
                                if quest_text and quest_text not in location_data["quests"]:
                                    location_data["quests"].append(quest_text)
                        next_elem = next_elem.find_next_sibling()
                
                # 查找敌人相关的标题
                enemy_sections = []
                for heading in soup.find_all(['h2', 'h3']):
                    heading_text = heading.text.strip().lower()
                    if any(keyword.lower() in heading_text for keyword in ["敌人", "怪物", "enemies", "monsters", "foes"]):
                        enemy_sections.append(heading)
                
                # 从敌人相关的标题下的列表中提取敌人
                for section in enemy_sections:
                    next_elem = section.find_next_sibling()
                    while next_elem and next_elem.name not in ['h2', 'h3']:
                        if next_elem.name in ['ul', 'ol']:
                            for li in next_elem.find_all('li'):
                                enemy_text = li.text.strip()
                                if enemy_text and enemy_text not in location_data["enemies"]:
                                    location_data["enemies"].append(enemy_text)
                        next_elem = next_elem.find_next_sibling()
                
                # 从列表项中提取地点类型、区域、NPC、资源和任务
                for li in soup.find_all('li'):
                    li_text = li.text.strip()
                    
                    # 检查是否为地点类型或区域
                    if any(kw in li_text.lower() for kw in ["类型", "type", "category"]):
                        parts = li_text.split(':', 1)
                        if len(parts) == 2:
                            location_data["location_type"] = parts[1].strip()
                    elif any(kw in li_text.lower() for kw in ["区域", "地区", "region", "area"]):
                        parts = li_text.split(':', 1)
                        if len(parts) == 2:
                            location_data["region"] = parts[1].strip()
                    elif any(kw in li_text.lower() for kw in ["坐标", "coordinates", "position", "location"]):
                        parts = li_text.split(':', 1)
                        if len(parts) == 2:
                            coords_text = parts[1].strip()
                            # 尝试提取坐标值
                            x_match = re.search(r'x\s*[=:]\s*(-?\d+)', coords_text, re.IGNORECASE)
                            y_match = re.search(r'y\s*[=:]\s*(-?\d+)', coords_text, re.IGNORECASE)
                            if x_match:
                                location_data["coordinates"]["x"] = int(x_match.group(1))
                            if y_match:
                                location_data["coordinates"]["y"] = int(y_match.group(1))
                    
                    # 检查是否为关键词信息
                    for keyword in self.keywords:
                        if keyword.lower() in li_text.lower():
                            # 尝试提取值
                            parts = li_text.split(':', 1)
                            if len(parts) == 2:
                                key = parts[0].strip().lower()
                                value = parts[1].strip()
                                
                                # 根据关键词分类
                                if any(kw in key.lower() for kw in ["npc", "人物", "角色", "character"]):
                                    if value:
                                        for npc in value.split(','):
                                            npc = npc.strip()
                                            if npc and npc not in location_data["npcs"]:
                                                location_data["npcs"].append(npc)
                                elif any(kw in key.lower() for kw in ["敌人", "怪物", "enemy", "monster", "foe"]):
                                    if value:
                                        for enemy in value.split(','):
                                            enemy = enemy.strip()
                                            if enemy and enemy not in location_data["enemies"]:
                                                location_data["enemies"].append(enemy)
                                elif any(kw in key.lower() for kw in ["资源", "物品", "resource", "item", "material"]):
                                    if value:
                                        for resource in value.split(','):
                                            resource = resource.strip()
                                            if resource and resource not in location_data["resources"]:
                                                location_data["resources"].append(resource)
                                elif any(kw in key.lower() for kw in ["任务", "quest", "mission", "objective"]):
                                    if value:
                                        for quest in value.split(','):
                                            quest = quest.strip()
                                            if quest and quest not in location_data["quests"]:
                                                location_data["quests"].append(quest)
                                elif any(kw in key.lower() for kw in ["连接", "通往", "connection", "path", "route", "leads to"]):
                                    if value:
                                        for connection in value.split(','):
                                            connection = connection.strip()
                                            if connection and connection not in location_data["connections"]:
                                                location_data["connections"].append(connection)
                    
                    # 检查是否为NPC、敌人、资源或任务（无冒号的情况）
                    if ":" not in li_text:
                        # 根据上下文或关键词判断类型
                        if li.find_parent('ul') and li.find_parent('ul').find_previous_sibling(['h2', 'h3']):
                            section_title = li.find_parent('ul').find_previous_sibling(['h2', 'h3']).text.strip().lower()
                            if any(kw in section_title.lower() for kw in ["npc", "人物", "角色", "character"]):
                                if li_text and li_text not in location_data["npcs"]:
                                    location_data["npcs"].append(li_text)
                            elif any(kw in section_title.lower() for kw in ["敌人", "怪物", "enemy", "monster", "foe"]):
                                if li_text and li_text not in location_data["enemies"]:
                                    location_data["enemies"].append(li_text)
                            elif any(kw in section_title.lower() for kw in ["资源", "物品", "resource", "item", "material"]):
                                if li_text and li_text not in location_data["resources"]:
                                    location_data["resources"].append(li_text)
                            elif any(kw in section_title.lower() for kw in ["任务", "quest", "mission", "objective"]):
                                if li_text and li_text not in location_data["quests"]:
                                    location_data["quests"].append(li_text)
                            elif any(kw in section_title.lower() for kw in ["连接", "通往", "connection", "path", "route", "leads to"]):
                                if li_text and li_text not in location_data["connections"]:
                                    location_data["connections"].append(li_text)
            else:
                # 原有的HTML提取逻辑
                description_elem = soup.find(['p', 'div'], class_=['description', 'intro', 'summary'])
                if description_elem:
                    location_data["description"] = description_elem.text.strip()
                
                # 提取地点类型
                location_type_elem = soup.find(['span', 'div'], class_=['location-type', 'type'])
                if location_type_elem:
                    location_data["location_type"] = location_type_elem.text.strip()
                
                # 提取区域
                region_elem = soup.find(['span', 'div'], class_=['region', 'area'])
                if region_elem:
                    location_data["region"] = region_elem.text.strip()
                
                # 提取坐标
                coords_elem = soup.find(['span', 'div'], class_=['coordinates', 'coords'])
                if coords_elem:
                    coords_text = coords_elem.text.strip()
                    # 尝试提取坐标值
                    x_match = re.search(r'x\s*[=:]\s*(-?\d+)', coords_text, re.IGNORECASE)
                    y_match = re.search(r'y\s*[=:]\s*(-?\d+)', coords_text, re.IGNORECASE)
                    if x_match:
                        location_data["coordinates"]["x"] = int(x_match.group(1))
                    if y_match:
                        location_data["coordinates"]["y"] = int(y_match.group(1))
                
                # 提取NPC
                npcs_list = soup.find(['ul', 'ol'], class_=['npcs', 'characters'])
                if npcs_list:
                    for npc_item in npcs_list.find_all('li'):
                        npc_text = npc_item.text.strip()
                        location_data["npcs"].append(npc_text)
                
                # 提取敌人
                enemies_list = soup.find(['ul', 'ol'], class_=['enemies', 'monsters'])
                if enemies_list:
                    for enemy_item in enemies_list.find_all('li'):
                        enemy_text = enemy_item.text.strip()
                        location_data["enemies"].append(enemy_text)
                
                # 提取资源
                resources_list = soup.find(['ul', 'ol'], class_=['resources', 'items'])
                if resources_list:
                    for resource_item in resources_list.find_all('li'):
                        resource_text = resource_item.text.strip()
                        location_data["resources"].append(resource_text)
                
                # 提取任务
                quests_list = soup.find(['ul', 'ol'], class_=['quests', 'missions'])
                if quests_list:
                    for quest_item in quests_list.find_all('li'):
                        quest_text = quest_item.text.strip()
                        location_data["quests"].append(quest_text)
                
                # 提取连接
                connections_list = soup.find(['ul', 'ol'], class_=['connections', 'paths'])
                if connections_list:
                    for connection_item in connections_list.find_all('li'):
                        connection_text = connection_item.text.strip()
                        location_data["connections"].append(connection_text)
            
            # 如果没有找到任务，尝试从文本中提取
            if not location_data["quests"]:
                # 查找包含任务关键词的段落
                for p in soup.find_all(['p', 'div']):
                    p_text = p.text.strip().lower()
                    if any(kw.lower() in p_text for kw in ["任务", "quest", "mission", "objective"]):
                        # 尝试提取任务名称（通常在冒号后面）
                        if ":" in p_text:
                            quests_text = p_text.split(":", 1)[1].strip()
                            for quest in quests_text.split(","):
                                quest = quest.strip()
                                if quest and quest not in location_data["quests"]:
                                    location_data["quests"].append(quest)
            
            # 如果地点名称中包含任务相关词汇，可能是该任务的地点
            if any(kw in location_name.lower() for kw in ["quest", "mission", "task", "objective"]):
                if location_name not in location_data["quests"]:
                    location_data["quests"].append(location_name)
            
            return location_data
            
        except Exception as e:
            self.logger.error(f"提取地点数据时出错: {str(e)}", exc_info=True)
            return None
    
    def _generate_id(self, name):
        """根据名称生成ID"""
        # 移除非字母数字字符，转换为小写
        id_str = re.sub(r'[^\w]', '_', name.lower())
        # 确保ID不以数字开头
        if id_str[0].isdigit():
            id_str = 'l_' + id_str
        return id_str 