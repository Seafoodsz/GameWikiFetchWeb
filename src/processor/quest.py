#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 任务数据处理器
"""

from .base import BaseProcessor
import re
import json
import logging
import os

class QuestProcessor(BaseProcessor):
    """任务数据处理器，处理任务相关数据"""
    
    def __init__(self, input_dir, output_dir, config=None):
        """初始化任务处理器"""
        super().__init__(input_dir, output_dir, config)
        self.keywords = config.get('keywords', ["目标", "奖励", "前置条件", "步骤", "Rewards", "Objectives", "Prerequisites"])
        self.logger.info(f"任务处理器初始化完成，关键词: {self.keywords}")
    
    def process(self):
        """处理任务数据"""
        self.logger.info("开始处理任务数据")
        
        # 获取输入文件
        input_files = self.get_input_files()
        if not input_files:
            self.logger.warning("没有找到任务数据文件")
            return False
        
        # 处理每个文件
        quests = []
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
            quest_data = self.extract_data(soup, file_path)
            if not quest_data:
                self.logger.warning(f"无法从文件中提取任务数据: {file_path}")
                continue
            
            # 清理数据
            quest_data = self.clean_data(quest_data)
            
            # 验证数据
            if not self.validate_data(quest_data):
                self.logger.warning(f"任务数据验证失败: {file_path}")
                continue
            
            quests.append(quest_data)
        
        # 保存处理结果
        if quests:
            output_file = "quest.json"
            self.save_output(quests, output_file)
            self.logger.info(f"任务数据处理完成，共处理 {len(quests)} 个任务")
            return True
        else:
            self.logger.warning("没有处理到任何任务数据")
            return False
    
    def extract_data(self, soup, file_path):
        """从HTML或Markdown中提取任务数据"""
        try:
            # 获取任务名称
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.md':
                # 从Markdown文件名或h1标签获取任务名称
                h1_tag = soup.find('h1')
                if h1_tag:
                    quest_name = h1_tag.text.strip()
                else:
                    quest_name = os.path.basename(file_path).replace('.md', '').replace('_', ' ')
            else:
                # 从HTML标题获取任务名称
                title = soup.find('title')
                quest_name = title.text.strip() if title else os.path.basename(file_path).replace('.html', '').replace('_', ' ')
            
            # 基本数据结构
            quest_data = {
                "id": self._generate_id(quest_name),
                "name": quest_name,
                "type": "quest",
                "quest_type": "",
                "description": "",
                "objectives": [],
                "rewards": [],
                "prerequisites": [],
                "locations": [],
                "npcs": [],
                "difficulty": ""
            }
            
            # 提取描述和其他数据
            if file_ext == '.md':
                # 从Markdown中提取描述（第一个非标题、非URL的段落）
                for p in soup.find_all(['p', 'div']):
                    if p.get('class') != 'url' and not p.find_parent('ul') and p.text.strip():
                        quest_data["description"] = p.text.strip()
                        break
                
                # 设置URL作为描述（如果没有找到更好的描述）
                if not quest_data["description"]:
                    url_elem = soup.find('div', class_='url')
                    if url_elem and url_elem.text.strip():
                        quest_data["description"] = url_elem.text.strip()
                
                # 查找奖励相关的标题
                reward_sections = []
                for heading in soup.find_all(['h2', 'h3']):
                    heading_text = heading.text.strip().lower()
                    if any(keyword.lower() in heading_text for keyword in ["奖励", "rewards", "loot", "items", "获得", "获取"]):
                        reward_sections.append(heading)
                
                # 从奖励相关的标题下的列表中提取奖励
                for section in reward_sections:
                    next_elem = section.find_next_sibling()
                    while next_elem and next_elem.name not in ['h2', 'h3']:
                        if next_elem.name in ['ul', 'ol']:
                            for li in next_elem.find_all('li'):
                                reward_text = li.text.strip()
                                if reward_text and reward_text not in quest_data["rewards"]:
                                    quest_data["rewards"].append(reward_text)
                        next_elem = next_elem.find_next_sibling()
                
                # 查找地点相关的标题
                location_sections = []
                for heading in soup.find_all(['h2', 'h3']):
                    heading_text = heading.text.strip().lower()
                    if any(keyword.lower() in heading_text for keyword in ["地点", "位置", "location", "place", "area", "region"]):
                        location_sections.append(heading)
                
                # 从地点相关的标题下的列表中提取地点
                for section in location_sections:
                    next_elem = section.find_next_sibling()
                    while next_elem and next_elem.name not in ['h2', 'h3']:
                        if next_elem.name in ['ul', 'ol']:
                            for li in next_elem.find_all('li'):
                                location_text = li.text.strip()
                                if location_text and location_text not in quest_data["locations"]:
                                    quest_data["locations"].append(location_text)
                        next_elem = next_elem.find_next_sibling()
                
                # 从列表项中提取任务类型、目标、奖励、前置条件、地点、NPC和难度
                for li in soup.find_all('li'):
                    li_text = li.text.strip()
                    
                    # 检查是否为任务类型或难度
                    if any(kw in li_text.lower() for kw in ["类型", "type", "category"]):
                        parts = li_text.split(':', 1)
                        if len(parts) == 2:
                            quest_data["quest_type"] = parts[1].strip()
                    elif any(kw in li_text.lower() for kw in ["难度", "difficulty", "level"]):
                        parts = li_text.split(':', 1)
                        if len(parts) == 2:
                            quest_data["difficulty"] = parts[1].strip()
                    
                    # 检查是否为关键词信息
                    for keyword in self.keywords:
                        if keyword.lower() in li_text.lower():
                            # 尝试提取值
                            parts = li_text.split(':', 1)
                            if len(parts) == 2:
                                key = parts[0].strip().lower()
                                value = parts[1].strip()
                                
                                # 根据关键词分类
                                if any(kw in key.lower() for kw in ["目标", "任务", "objective", "goal", "task"]):
                                    if value and value not in quest_data["objectives"]:
                                        quest_data["objectives"].append(value)
                                elif any(kw in key.lower() for kw in ["奖励", "reward", "loot", "item", "获得"]):
                                    if value:
                                        for reward in value.split(','):
                                            reward = reward.strip()
                                            if reward and reward not in quest_data["rewards"]:
                                                quest_data["rewards"].append(reward)
                                elif any(kw in key.lower() for kw in ["前置", "条件", "prerequisite", "requirement"]):
                                    if value and value not in quest_data["prerequisites"]:
                                        quest_data["prerequisites"].append(value)
                                elif any(kw in key.lower() for kw in ["地点", "位置", "location", "place", "area"]):
                                    if value:
                                        for location in value.split(','):
                                            location = location.strip()
                                            if location and location not in quest_data["locations"]:
                                                quest_data["locations"].append(location)
                                elif any(kw in key.lower() for kw in ["npc", "人物", "角色", "character"]):
                                    if value:
                                        for npc in value.split(','):
                                            npc = npc.strip()
                                            if npc and npc not in quest_data["npcs"]:
                                                quest_data["npcs"].append(npc)
                    
                    # 检查是否为目标、奖励、前置条件、地点或NPC（无冒号的情况）
                    if ":" not in li_text:
                        # 根据上下文或关键词判断类型
                        if li.find_parent('ul') and li.find_parent('ul').find_previous_sibling(['h2', 'h3']):
                            section_title = li.find_parent('ul').find_previous_sibling(['h2', 'h3']).text.strip().lower()
                            if any(kw in section_title.lower() for kw in ["目标", "任务", "objective", "goal", "task"]):
                                if li_text and li_text not in quest_data["objectives"]:
                                    quest_data["objectives"].append(li_text)
                            elif any(kw in section_title.lower() for kw in ["奖励", "reward", "loot", "item", "获得"]):
                                if li_text and li_text not in quest_data["rewards"]:
                                    quest_data["rewards"].append(li_text)
                            elif any(kw in section_title.lower() for kw in ["前置", "条件", "prerequisite", "requirement"]):
                                if li_text and li_text not in quest_data["prerequisites"]:
                                    quest_data["prerequisites"].append(li_text)
                            elif any(kw in section_title.lower() for kw in ["地点", "位置", "location", "place", "area"]):
                                if li_text and li_text not in quest_data["locations"]:
                                    quest_data["locations"].append(li_text)
                            elif any(kw in section_title.lower() for kw in ["npc", "人物", "角色", "character"]):
                                if li_text and li_text not in quest_data["npcs"]:
                                    quest_data["npcs"].append(li_text)
            else:
                # 原有的HTML提取逻辑
                description_elem = soup.find(['p', 'div'], class_=['description', 'intro', 'summary'])
                if description_elem:
                    quest_data["description"] = description_elem.text.strip()
                
                # 提取任务类型
                quest_type_elem = soup.find(['span', 'div'], class_=['quest-type', 'type'])
                if quest_type_elem:
                    quest_data["quest_type"] = quest_type_elem.text.strip()
                
                # 提取难度
                difficulty_elem = soup.find(['span', 'div'], class_=['difficulty', 'level'])
                if difficulty_elem:
                    quest_data["difficulty"] = difficulty_elem.text.strip()
                
                # 提取目标
                objectives_list = soup.find(['ul', 'ol'], class_=['objectives', 'goals'])
                if objectives_list:
                    for objective_item in objectives_list.find_all('li'):
                        objective_text = objective_item.text.strip()
                        quest_data["objectives"].append(objective_text)
                
                # 提取奖励
                rewards_list = soup.find(['ul', 'ol'], class_=['rewards', 'loot'])
                if rewards_list:
                    for reward_item in rewards_list.find_all('li'):
                        reward_text = reward_item.text.strip()
                        quest_data["rewards"].append(reward_text)
                
                # 提取前置条件
                prerequisites_list = soup.find(['ul', 'ol'], class_=['prerequisites', 'requirements'])
                if prerequisites_list:
                    for prerequisite_item in prerequisites_list.find_all('li'):
                        prerequisite_text = prerequisite_item.text.strip()
                        quest_data["prerequisites"].append(prerequisite_text)
                
                # 提取地点
                locations_list = soup.find(['ul', 'ol'], class_=['locations', 'places'])
                if locations_list:
                    for location_item in locations_list.find_all('li'):
                        location_text = location_item.text.strip()
                        quest_data["locations"].append(location_text)
                
                # 提取NPC
                npcs_list = soup.find(['ul', 'ol'], class_=['npcs', 'characters'])
                if npcs_list:
                    for npc_item in npcs_list.find_all('li'):
                        npc_text = npc_item.text.strip()
                        quest_data["npcs"].append(npc_text)
            
            # 如果没有找到奖励，尝试从文本中提取
            if not quest_data["rewards"]:
                # 查找包含奖励关键词的段落
                for p in soup.find_all(['p', 'div']):
                    p_text = p.text.strip().lower()
                    if any(kw.lower() in p_text for kw in ["奖励", "reward", "loot", "item", "获得", "获取"]):
                        # 尝试提取物品名称（通常在冒号后面）
                        if ":" in p_text:
                            items_text = p_text.split(":", 1)[1].strip()
                            for item in items_text.split(","):
                                item = item.strip()
                                if item and item not in quest_data["rewards"]:
                                    quest_data["rewards"].append(item)
            
            # 如果任务名称中包含物品名称，可能是该物品的奖励
            if "sword" in quest_name.lower() or "axe" in quest_name.lower() or "bow" in quest_name.lower() or "staff" in quest_name.lower() or "armor" in quest_name.lower() or "shield" in quest_name.lower():
                if quest_name not in quest_data["rewards"]:
                    quest_data["rewards"].append(quest_name)
            
            return quest_data
            
        except Exception as e:
            self.logger.error(f"提取任务数据时出错: {str(e)}", exc_info=True)
            return None
    
    def _generate_id(self, name):
        """根据名称生成ID"""
        # 移除非字母数字字符，转换为小写
        id_str = re.sub(r'[^\w]', '_', name.lower())
        # 确保ID不以数字开头
        if id_str[0].isdigit():
            id_str = 'q_' + id_str
        return id_str 