#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
关系处理器模块
处理数据之间的关系
"""

import os
import re
from utils.logger import exception_handler
from processors.base_processor import BaseProcessor

class RelationProcessor(BaseProcessor):
    """关系处理器类"""
    
    def __init__(self, config, db_manager):
        """初始化关系处理器
        
        Args:
            config (Config): 配置对象
            db_manager (DatabaseManager): 数据库管理器
        """
        super().__init__(config, db_manager, "relation")
        
        # 关系类型
        self.relation_types = self.processor_config.get("relation_types", ["角色-技能", "物品-敌人", "地点-任务", "任务-奖励"])
    
    @exception_handler
    def process(self):
        """处理关系数据
        
        Returns:
            int: 处理的关系数量
        """
        if not self.enabled:
            self.logger.info(f"{self.processor_name} 处理器已禁用")
            return 0
        
        self.logger.info(f"开始处理 {self.processor_name} 数据")
        
        # 关系处理器不处理文件，而是在generate_relations方法中生成关系
        return 0
    
    @exception_handler
    def generate_relations(self):
        """生成关系数据
        
        Returns:
            int: 生成的关系数量
        """
        self.logger.info("开始生成关系数据")
        
        relation_count = 0
        
        # 生成角色-技能关系
        if "角色-技能" in self.relation_types:
            relation_count += self._generate_character_skill_relations()
        
        # 生成物品-敌人关系
        if "物品-敌人" in self.relation_types:
            relation_count += self._generate_item_enemy_relations()
        
        # 生成地点-任务关系
        if "地点-任务" in self.relation_types:
            relation_count += self._generate_location_quest_relations()
        
        # 生成任务-奖励关系
        if "任务-奖励" in self.relation_types:
            relation_count += self._generate_quest_reward_relations()
        
        self.logger.info(f"完成生成关系数据，共生成 {relation_count} 个关系")
        return relation_count
    
    def _generate_character_skill_relations(self):
        """生成角色-技能关系
        
        Returns:
            int: 生成的关系数量
        """
        relation_count = 0
        
        # 获取所有角色
        characters = self.db_manager.data.get("character", {})
        
        # 获取所有技能
        skills = self.db_manager.data.get("skill", {})
        
        # 遍历所有角色
        for char_id, character in characters.items():
            # 获取角色的技能树
            char_skill_trees = character.get("skills", [])
            
            # 遍历所有技能
            for skill_id, skill in skills.items():
                # 获取技能所属的技能树
                skill_tree = skill.get("skill_tree", "").lower()
                
                # 如果技能所属的技能树在角色的技能树中，则创建关系
                if any(skill_tree in tree.lower() for tree in char_skill_trees):
                    # 创建关系ID
                    relation_id = f"{char_id}_{skill_id}"
                    
                    # 创建关系数据
                    relation_data = {
                        "id": relation_id,
                        "source_type": "character",
                        "source_id": char_id,
                        "target_type": "skill",
                        "target_id": skill_id,
                        "relation_type": "character_skill",
                        "data": {
                            "character_name": character.get("name", ""),
                            "skill_name": skill.get("name", ""),
                            "skill_tree": skill_tree
                        }
                    }
                    
                    # 保存关系数据
                    self.items[relation_id] = relation_data
                    relation_count += 1
        
        self.logger.info(f"生成了 {relation_count} 个角色-技能关系")
        return relation_count
    
    def _generate_item_enemy_relations(self):
        """生成物品-敌人关系
        
        Returns:
            int: 生成的关系数量
        """
        # 由于我们没有敌人数据，这里只是一个示例
        self.logger.info("跳过生成物品-敌人关系，因为没有敌人数据")
        return 0
    
    def _generate_location_quest_relations(self):
        """生成地点-任务关系
        
        Returns:
            int: 生成的关系数量
        """
        # 由于我们没有地点和任务数据，这里只是一个示例
        self.logger.info("跳过生成地点-任务关系，因为没有地点和任务数据")
        return 0
    
    def _generate_quest_reward_relations(self):
        """生成任务-奖励关系
        
        Returns:
            int: 生成的关系数量
        """
        # 由于我们没有任务数据，这里只是一个示例
        self.logger.info("跳过生成任务-奖励关系，因为没有任务数据")
        return 0 