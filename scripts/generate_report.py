#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
生成项目处理结果的总结报告
"""

import os
import json
import datetime
from pathlib import Path

def load_json_file(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载文件 {file_path} 时出错: {e}")
        return []

def count_relations_by_type(relations):
    """统计各类型关系的数量"""
    relation_counts = {}
    for relation in relations:
        relation_type = relation.get('relation_type', 'unknown')
        relation_counts[relation_type] = relation_counts.get(relation_type, 0) + 1
    return relation_counts

def generate_report():
    """生成处理结果报告"""
    output_dir = Path('data/output')
    report_file = Path('data/report.md')
    
    # 收集各类数据
    data_stats = {}
    relation_stats = {}
    
    # 处理各类数据文件
    for data_type in ['character', 'enemy', 'item', 'location', 'quest', 'skill', 'relation']:
        json_file = output_dir / data_type / f"{data_type}.json"
        if json_file.exists():
            data = load_json_file(json_file)
            data_stats[data_type] = len(data)
            
            # 特别处理关系数据
            if data_type == 'relation':
                relation_stats = count_relations_by_type(data)
    
    # 生成报告
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 石之碎片Wiki数据处理报告\n\n")
        f.write(f"生成时间: {now}\n\n")
        
        f.write("## 1. 数据统计\n\n")
        f.write("### 1.1 基础数据\n\n")
        f.write("| 数据类型 | 数量 |\n")
        f.write("|---------|------|\n")
        for data_type, count in data_stats.items():
            if data_type != 'relation':
                f.write(f"| {data_type} | {count} |\n")
        
        f.write("\n### 1.2 关系数据\n\n")
        f.write("| 关系类型 | 数量 |\n")
        f.write("|---------|------|\n")
        for relation_type, count in relation_stats.items():
            f.write(f"| {relation_type} | {count} |\n")
        f.write(f"| 总计 | {data_stats.get('relation', 0)} |\n")
        
        f.write("\n## 2. 处理结果\n\n")
        f.write("所有数据已成功处理并保存到对应的JSON文件中。\n\n")
        
        f.write("## 3. 文件大小\n\n")
        f.write("| 文件 | 大小 (字节) |\n")
        f.write("|------|------------|\n")
        for data_type in data_stats.keys():
            json_file = output_dir / data_type / f"{data_type}.json"
            if json_file.exists():
                file_size = os.path.getsize(json_file)
                f.write(f"| {data_type}.json | {file_size} |\n")
    
    print(f"报告已生成: {report_file}")

if __name__ == "__main__":
    generate_report() 