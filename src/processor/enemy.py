#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 敌人数据处理器
"""

from .base import BaseProcessor
import re
import json
import logging
import os

class EnemyProcessor(BaseProcessor):
    """敌人数据处理器，处理敌人相关数据"""
    
    def __init__(self, input_dir, output_dir, config=None):
        """初始化敌人处理器"""
        super().__init__(input_dir, output_dir, config)
        self.keywords = config.get('keywords', ["生命值", "攻击", "防御", "弱点", "掉落物", "战利品", "Drops", "Loot"])
        self.logger.info(f"敌人处理器初始化完成，关键词: {self.keywords}")
    
    def process(self):
        """处理敌人数据"""
        self.logger.info("开始处理敌人数据")
        
        # 获取输入文件
        input_files = self.get_input_files()
        if not input_files:
            self.logger.warning("没有找到敌人数据文件")
            return False
        
        # 处理每个文件
        enemies = []
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
            enemy_data = self.extract_data(soup, file_path)
            if not enemy_data:
                self.logger.warning(f"无法从文件中提取敌人数据: {file_path}")
                continue
            
            # 清理数据
            enemy_data = self.clean_data(enemy_data)
            
            # 验证数据
            if not self.validate_data(enemy_data):
                self.logger.warning(f"敌人数据验证失败: {file_path}")
                continue
            
            enemies.append(enemy_data)
        
        # 保存处理结果
        if enemies:
            output_file = "enemy.json"
            self.save_output(enemies, output_file)
            self.logger.info(f"敌人数据处理完成，共处理 {len(enemies)} 个敌人")
            return True
        else:
            self.logger.warning("没有处理到任何敌人数据")
            return False
    
    def extract_data(self, soup, file_path):
        """从HTML或Markdown中提取敌人数据"""
        try:
            # 获取敌人名称
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.md':
                # 从Markdown文件名或h1标签获取敌人名称
                h1_tag = soup.find('h1')
                if h1_tag:
                    enemy_name = h1_tag.text.strip()
                else:
                    enemy_name = os.path.basename(file_path).replace('.md', '').replace('_', ' ')
            else:
                # 从HTML标题获取敌人名称
                title = soup.find('title')
                enemy_name = title.text.strip() if title else os.path.basename(file_path).replace('.html', '').replace('_', ' ')
            
            # 基本数据结构
            enemy_data = {
                "id": self._generate_id(enemy_name),
                "name": enemy_name,
                "type": "enemy",
                "enemy_type": "",
                "description": "",
                "stats": {
                    "health": 0,
                    "attack": 0,
                    "defense": 0
                },
                "resistances": {},
                "weaknesses": [],
                "abilities": [],
                "drops": []
            }
            
            # 提取描述和其他数据
            if file_ext == '.md':
                # 从Markdown中提取描述（第一个非标题、非URL的段落）
                for p in soup.find_all(['p', 'div']):
                    if p.get('class') != 'url' and not p.find_parent('ul') and p.text.strip():
                        enemy_data["description"] = p.text.strip()
                        break
                
                # 设置URL作为描述（如果没有找到更好的描述）
                if not enemy_data["description"]:
                    url_elem = soup.find('div', class_='url')
                    if url_elem and url_elem.text.strip():
                        enemy_data["description"] = url_elem.text.strip()
                
                # 查找掉落物相关的标题
                drop_sections = []
                for heading in soup.find_all(['h2', 'h3']):
                    heading_text = heading.text.strip().lower()
                    if any(keyword.lower() in heading_text for keyword in ["掉落", "战利品", "drops", "loot", "rewards", "items"]):
                        drop_sections.append(heading)
                
                # 从掉落物相关的标题下的列表中提取掉落物
                for section in drop_sections:
                    next_elem = section.find_next_sibling()
                    while next_elem and next_elem.name not in ['h2', 'h3']:
                        if next_elem.name in ['ul', 'ol']:
                            for li in next_elem.find_all('li'):
                                drop_text = li.text.strip()
                                if drop_text and drop_text not in enemy_data["drops"]:
                                    enemy_data["drops"].append(drop_text)
                        next_elem = next_elem.find_next_sibling()
                
                # 从列表项中提取敌人类型、属性、弱点、能力和掉落物
                for li in soup.find_all('li'):
                    li_text = li.text.strip()
                    
                    # 检查是否为敌人类型
                    if "类型" in li_text:
                        parts = li_text.split(':', 1)
                        if len(parts) == 2:
                            enemy_data["enemy_type"] = parts[1].strip()
                    
                    # 检查是否为属性信息
                    for keyword in self.keywords:
                        if keyword.lower() in li_text.lower():
                            # 尝试提取属性值
                            parts = li_text.split(':', 1)
                            if len(parts) == 2:
                                stat_name = parts[0].strip().lower()
                                stat_value = parts[1].strip()
                                
                                # 尝试转换为数字
                                try:
                                    stat_value = int(re.search(r'\d+', stat_value).group())
                                except (ValueError, AttributeError):
                                    try:
                                        stat_value = float(re.search(r'\d+(\.\d+)?', stat_value).group())
                                    except (ValueError, AttributeError):
                                        pass
                                
                                # 处理特殊属性
                                if any(kw in stat_name.lower() for kw in ["生命", "hp", "health"]):
                                    enemy_data["stats"]["health"] = stat_value
                                elif any(kw in stat_name.lower() for kw in ["攻击", "attack", "damage"]):
                                    enemy_data["stats"]["attack"] = stat_value
                                elif any(kw in stat_name.lower() for kw in ["防御", "defense", "armor"]):
                                    enemy_data["stats"]["defense"] = stat_value
                                elif any(kw in stat_name.lower() for kw in ["弱点", "weakness", "vulnerabilities"]):
                                    if isinstance(stat_value, str):
                                        for weak in stat_value.split(','):
                                            weak = weak.strip()
                                            if weak and weak not in enemy_data["weaknesses"]:
                                                enemy_data["weaknesses"].append(weak)
                                    else:
                                        enemy_data["weaknesses"].append(str(stat_value))
                                elif any(kw in stat_name.lower() for kw in ["能力", "技能", "ability", "skill", "abilities", "skills"]):
                                    if isinstance(stat_value, str):
                                        for ability in stat_value.split(','):
                                            ability = ability.strip()
                                            if ability and ability not in enemy_data["abilities"]:
                                                enemy_data["abilities"].append(ability)
                                    else:
                                        enemy_data["abilities"].append(str(stat_value))
                                elif any(kw in stat_name.lower() for kw in ["掉落", "战利品", "drop", "loot", "drops", "loots", "item", "items"]):
                                    if isinstance(stat_value, str):
                                        for drop in stat_value.split(','):
                                            drop = drop.strip()
                                            if drop and drop not in enemy_data["drops"]:
                                                enemy_data["drops"].append(drop)
                                    else:
                                        enemy_data["drops"].append(str(stat_value))
                                else:
                                    enemy_data["stats"][stat_name] = stat_value
                    
                    # 检查是否为弱点、能力或掉落物（无冒号的情况）
                    if ":" not in li_text:
                        # 根据上下文或关键词判断类型
                        if li.find_parent('ul') and li.find_parent('ul').find_previous_sibling(['h2', 'h3']):
                            section_title = li.find_parent('ul').find_previous_sibling(['h2', 'h3']).text.strip().lower()
                            if any(kw in section_title for kw in ["弱点", "weakness", "vulnerabilities"]):
                                if li_text not in enemy_data["weaknesses"]:
                                    enemy_data["weaknesses"].append(li_text)
                            elif any(kw in section_title for kw in ["能力", "技能", "ability", "skill", "abilities", "skills"]):
                                if li_text not in enemy_data["abilities"]:
                                    enemy_data["abilities"].append(li_text)
                            elif any(kw in section_title for kw in ["掉落", "战利品", "drop", "loot", "drops", "loots", "item", "items"]):
                                if li_text not in enemy_data["drops"]:
                                    enemy_data["drops"].append(li_text)
            else:
                # 原有的HTML提取逻辑
                description_elem = soup.find(['p', 'div'], class_=['description', 'intro', 'summary'])
                if description_elem:
                    enemy_data["description"] = description_elem.text.strip()
                
                # 提取敌人类型
                enemy_type_elem = soup.find(['span', 'div'], class_=['enemy-type', 'type'])
                if enemy_type_elem:
                    enemy_data["enemy_type"] = enemy_type_elem.text.strip()
                
                # 提取敌人属性
                stats_table = soup.find('table', class_=['stats', 'attributes'])
                if stats_table:
                    for row in stats_table.find_all('tr'):
                        cells = row.find_all(['th', 'td'])
                        if len(cells) >= 2:
                            stat_name = cells[0].text.strip().lower()
                            stat_value = cells[1].text.strip()
                            
                            # 尝试转换为数字
                            try:
                                stat_value = int(re.search(r'\d+', stat_value).group())
                            except (ValueError, AttributeError):
                                try:
                                    stat_value = float(re.search(r'\d+(\.\d+)?', stat_value).group())
                                except (ValueError, AttributeError):
                                    pass
                            
                            # 处理特殊属性
                            if "生命" in stat_name or "hp" in stat_name:
                                enemy_data["stats"]["health"] = stat_value
                            elif "攻击" in stat_name or "attack" in stat_name:
                                enemy_data["stats"]["attack"] = stat_value
                            elif "防御" in stat_name or "defense" in stat_name:
                                enemy_data["stats"]["defense"] = stat_value
                            else:
                                enemy_data["stats"][stat_name] = stat_value
                
                # 提取抗性
                resistances_table = soup.find('table', class_=['resistances', 'resistance'])
                if resistances_table:
                    for row in resistances_table.find_all('tr'):
                        cells = row.find_all(['th', 'td'])
                        if len(cells) >= 2:
                            res_name = cells[0].text.strip()
                            res_value = cells[1].text.strip()
                            # 尝试转换为数字
                            try:
                                res_value = int(res_value)
                            except ValueError:
                                try:
                                    res_value = float(res_value)
                                except ValueError:
                                    pass
                            enemy_data["resistances"][res_name] = res_value
                
                # 提取弱点
                weaknesses_list = soup.find(['ul', 'ol'], class_=['weaknesses', 'weakness'])
                if weaknesses_list:
                    for weakness_item in weaknesses_list.find_all('li'):
                        weakness_text = weakness_item.text.strip()
                        enemy_data["weaknesses"].append(weakness_text)
                
                # 提取能力
                abilities_list = soup.find(['ul', 'ol'], class_=['abilities', 'skills'])
                if abilities_list:
                    for ability_item in abilities_list.find_all('li'):
                        ability_text = ability_item.text.strip()
                        enemy_data["abilities"].append(ability_text)
                
                # 提取掉落物
                drops_list = soup.find(['ul', 'ol'], class_=['drops', 'loot'])
                if drops_list:
                    for drop_item in drops_list.find_all('li'):
                        drop_text = drop_item.text.strip()
                        enemy_data["drops"].append(drop_text)
            
            # 如果没有找到掉落物，尝试从文本中提取
            if not enemy_data["drops"]:
                # 查找包含掉落物关键词的段落
                for p in soup.find_all(['p', 'div']):
                    p_text = p.text.strip().lower()
                    if any(kw.lower() in p_text for kw in ["掉落", "战利品", "drops", "loot", "rewards", "items"]):
                        # 尝试提取物品名称（通常在冒号后面）
                        if ":" in p_text:
                            items_text = p_text.split(":", 1)[1].strip()
                            for item in items_text.split(","):
                                item = item.strip()
                                if item and item not in enemy_data["drops"]:
                                    enemy_data["drops"].append(item)
            
            # 如果敌人名称中包含物品名称，可能是该物品的掉落源
            if "sword" in enemy_name.lower() or "axe" in enemy_name.lower() or "bow" in enemy_name.lower() or "staff" in enemy_name.lower() or "armor" in enemy_name.lower() or "shield" in enemy_name.lower():
                if enemy_name not in enemy_data["drops"]:
                    enemy_data["drops"].append(enemy_name)
            
            return enemy_data
            
        except Exception as e:
            self.logger.error(f"提取敌人数据时出错: {str(e)}", exc_info=True)
            return None
    
    def _generate_id(self, name):
        """根据名称生成ID"""
        # 移除非字母数字字符，转换为小写
        id_str = re.sub(r'[^\w]', '_', name.lower())
        # 确保ID不以数字开头
        if id_str[0].isdigit():
            id_str = 'e_' + id_str
        return id_str 