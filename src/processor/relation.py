#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 关系数据处理器
"""

from .base import BaseProcessor
import re
import json
import logging
import os
import glob

class RelationProcessor(BaseProcessor):
    """关系数据处理器，处理不同数据类型之间的关系"""
    
    def __init__(self, input_dir, output_dir, config=None):
        """初始化关系处理器"""
        super().__init__(input_dir, output_dir, config)
        self.relation_types = config.get('relation_types', ["角色-技能", "物品-敌人", "地点-任务", "任务-奖励"])
        self.logger.info(f"关系处理器初始化完成，关系类型: {self.relation_types}")
    
    def process(self):
        """处理关系数据"""
        self.logger.info("开始处理关系数据")
        
        # 加载已处理的数据
        characters = self._load_processed_data('character.json')
        items = self._load_processed_data('item.json')
        skills = self._load_processed_data('skill.json')
        enemies = self._load_processed_data('enemy.json')
        locations = self._load_processed_data('location.json')
        quests = self._load_processed_data('quest.json')
        
        # 检查是否有足够的数据
        if not any([characters, items, skills, enemies, locations, quests]):
            self.logger.warning("没有找到已处理的数据，无法提取关系")
            return False
        
        # 提取关系
        relations = []
        
        # 处理角色-技能关系
        if "角色-技能" in self.relation_types and characters and skills:
            self.logger.info("处理角色-技能关系")
            char_skill_relations = self._extract_character_skill_relations(characters, skills)
            relations.extend(char_skill_relations)
        
        # 处理物品-敌人关系
        if "物品-敌人" in self.relation_types and items and enemies:
            self.logger.info("处理物品-敌人关系")
            item_enemy_relations = self._extract_item_enemy_relations(items, enemies)
            relations.extend(item_enemy_relations)
        
        # 处理地点-任务关系
        if "地点-任务" in self.relation_types and locations and quests:
            self.logger.info("处理地点-任务关系")
            location_quest_relations = self._extract_location_quest_relations(locations, quests)
            relations.extend(location_quest_relations)
        
        # 处理任务-奖励关系
        if "任务-奖励" in self.relation_types and quests and items:
            self.logger.info("处理任务-奖励关系")
            quest_reward_relations = self._extract_quest_reward_relations(quests, items)
            relations.extend(quest_reward_relations)
        
        # 保存处理结果
        if relations:
            output_file = "relation.json"
            self.save_output(relations, output_file)
            self.logger.info(f"关系数据处理完成，共处理 {len(relations)} 个关系")
            return True
        else:
            self.logger.warning("没有处理到任何关系数据")
            return False
    
    def _load_processed_data(self, filename):
        """加载已处理的数据"""
        try:
            # 首先尝试从根目录加载
            file_path = os.path.join(self.output_dir, filename)
            
            # 如果根目录不存在，尝试从子目录加载
            if not os.path.exists(file_path):
                # 获取文件名（不含扩展名）作为子目录名
                subdir = os.path.splitext(filename)[0]
                file_path = os.path.join(self.output_dir, subdir, filename)
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.logger.info(f"已加载 {len(data)} 条 {filename} 数据")
                return data
            else:
                self.logger.warning(f"文件不存在: {file_path}")
                return []
        except Exception as e:
            self.logger.error(f"加载数据失败: {filename}, 错误: {str(e)}")
            return []
    
    def _extract_character_skill_relations(self, characters, skills):
        """提取角色-技能关系"""
        relations = []
        
        # 创建技能名称到ID的映射
        skill_map = {skill['name']: skill['id'] for skill in skills}
        
        # 遍历角色数据
        for character in characters:
            char_id = character['id']
            char_name = character['name']
            
            # 检查角色的技能列表
            for skill_name in character.get('skills', []):
                # 查找对应的技能ID
                skill_id = None
                for s_name, s_id in skill_map.items():
                    if skill_name.lower() in s_name.lower() or s_name.lower() in skill_name.lower():
                        skill_id = s_id
                        break
                
                if skill_id:
                    # 创建关系数据
                    relation = {
                        "id": f"{char_id}_{skill_id}",
                        "source_type": "character",
                        "source_id": char_id,
                        "target_type": "skill",
                        "target_id": skill_id,
                        "relation_type": "character_skill",
                        "data": {
                            "character_name": char_name,
                            "skill_name": skill_name
                        }
                    }
                    relations.append(relation)
        
        self.logger.info(f"提取了 {len(relations)} 个角色-技能关系")
        return relations
    
    def _extract_item_enemy_relations(self, items, enemies):
        """提取物品-敌人关系"""
        relations = []
        
        # 创建物品名称到ID的映射
        item_map = {item['name']: item['id'] for item in items}
        
        # 遍历敌人数据
        for enemy in enemies:
            enemy_id = enemy['id']
            enemy_name = enemy['name']
            
            # 检查敌人的掉落物列表
            for drop in enemy.get('drops', []):
                # 查找对应的物品ID
                item_id = None
                for i_name, i_id in item_map.items():
                    if drop.lower() in i_name.lower() or i_name.lower() in drop.lower():
                        item_id = i_id
                        break
                
                if item_id:
                    # 创建关系数据
                    relation = {
                        "id": f"{enemy_id}_{item_id}",
                        "source_type": "enemy",
                        "source_id": enemy_id,
                        "target_type": "item",
                        "target_id": item_id,
                        "relation_type": "enemy_drop",
                        "data": {
                            "enemy_name": enemy_name,
                            "item_name": drop
                        }
                    }
                    relations.append(relation)
        
        self.logger.info(f"提取了 {len(relations)} 个物品-敌人关系")
        return relations
    
    def _extract_location_quest_relations(self, locations, quests):
        """提取地点-任务关系"""
        relations = []
        
        # 创建地点名称到ID的映射
        location_map = {location['name'].lower(): location['id'] for location in locations}
        location_ids = {location['id'] for location in locations}
        
        # 创建任务名称到ID的映射
        quest_map = {quest['name'].lower(): quest['id'] for quest in quests}
        quest_ids = {quest['id'] for quest in quests}
        
        # 遍历任务数据
        for quest in quests:
            quest_id = quest['id']
            quest_name = quest['name']
            
            # 检查任务的地点列表
            for location_name in quest.get('locations', []):
                location_name_lower = location_name.lower()
                # 查找对应的地点ID
                location_id = None
                
                # 直接匹配
                if location_name_lower in location_map:
                    location_id = location_map[location_name_lower]
                else:
                    # 模糊匹配
                    for l_name, l_id in location_map.items():
                        if location_name_lower in l_name or l_name in location_name_lower:
                            location_id = l_id
                            break
                
                if location_id:
                    # 创建关系数据
                    relation = {
                        "id": f"{location_id}_{quest_id}",
                        "source_type": "location",
                        "source_id": location_id,
                        "target_type": "quest",
                        "target_id": quest_id,
                        "relation_type": "location_quest",
                        "data": {
                            "location_name": location_name,
                            "quest_name": quest_name
                        }
                    }
                    relations.append(relation)
        
        # 检查任务ID是否与地点ID相同（可能是同名的地点和任务）
        common_ids = quest_ids.intersection(location_ids)
        for common_id in common_ids:
            # 找到对应的地点和任务
            location = next((loc for loc in locations if loc['id'] == common_id), None)
            quest = next((q for q in quests if q['id'] == common_id), None)
            
            if location and quest:
                # 创建关系数据
                relation = {
                    "id": f"{common_id}_{common_id}",
                    "source_type": "location",
                    "source_id": common_id,
                    "target_type": "quest",
                    "target_id": common_id,
                    "relation_type": "location_quest",
                    "data": {
                        "location_name": location['name'],
                        "quest_name": quest['name']
                    }
                }
                relations.append(relation)
        
        # 检查任务的描述中是否包含地点名称
        for quest in quests:
            quest_id = quest['id']
            quest_name = quest['name']
            description = quest.get('description', '')
            
            # 检查描述中是否包含地点名称
            for location in locations:
                location_id = location['id']
                location_name = location['name']
                
                # 如果地点名称出现在任务描述中，创建关系
                if location_name.lower() in description.lower() and len(location_name) > 5:  # 避免太短的名称导致误匹配
                    # 创建关系数据
                    relation = {
                        "id": f"{location_id}_{quest_id}",
                        "source_type": "location",
                        "source_id": location_id,
                        "target_type": "quest",
                        "target_id": quest_id,
                        "relation_type": "location_quest",
                        "data": {
                            "location_name": location_name,
                            "quest_name": quest_name
                        }
                    }
                    relations.append(relation)
        
        # 检查任务的奖励中是否包含地点名称
        for quest in quests:
            quest_id = quest['id']
            quest_name = quest['name']
            
            # 检查奖励中是否包含地点名称
            for reward in quest.get('rewards', []):
                for location in locations:
                    location_id = location['id']
                    location_name = location['name']
                    
                    # 如果地点名称出现在奖励中，创建关系
                    if location_name.lower() in reward.lower() and len(location_name) > 5:  # 避免太短的名称导致误匹配
                        # 创建关系数据
                        relation = {
                            "id": f"{location_id}_{quest_id}",
                            "source_type": "location",
                            "source_id": location_id,
                            "target_type": "quest",
                            "target_id": quest_id,
                            "relation_type": "location_quest",
                            "data": {
                                "location_name": location_name,
                                "quest_name": quest_name
                            }
                        }
                        relations.append(relation)
        
        # 去重
        unique_relations = []
        relation_ids = set()
        for relation in relations:
            relation_id = f"{relation['source_id']}_{relation['target_id']}"
            if relation_id not in relation_ids:
                relation_ids.add(relation_id)
                unique_relations.append(relation)
        
        self.logger.info(f"提取了 {len(unique_relations)} 个地点-任务关系")
        return unique_relations
    
    def _extract_quest_reward_relations(self, quests, items):
        """提取任务-奖励关系"""
        relations = []
        
        # 创建物品名称到ID的映射
        item_map = {item['name']: item['id'] for item in items}
        
        # 遍历任务数据
        for quest in quests:
            quest_id = quest['id']
            quest_name = quest['name']
            
            # 检查任务的奖励列表
            for reward in quest.get('rewards', []):
                # 查找对应的物品ID
                item_id = None
                for i_name, i_id in item_map.items():
                    if i_name.lower() in reward.lower():
                        item_id = i_id
                        break
                
                if item_id:
                    # 创建关系数据
                    relation = {
                        "id": f"{quest_id}_{item_id}",
                        "source_type": "quest",
                        "source_id": quest_id,
                        "target_type": "item",
                        "target_id": item_id,
                        "relation_type": "quest_reward",
                        "data": {
                            "quest_name": quest_name,
                            "reward_name": reward
                        }
                    }
                    relations.append(relation)
        
        self.logger.info(f"提取了 {len(relations)} 个任务-奖励关系")
        return relations
    
    def extract_data(self, soup, file_path):
        """从HTML中提取数据（关系处理器不使用此方法）"""
        return None 