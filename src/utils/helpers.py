#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utils - 工具函数
提供各种辅助功能
"""

import os
import logging
import sys
from urllib.parse import urlparse

def setup_logging(log_level='INFO'):
    """设置日志
    
    Args:
        log_level (str): 日志级别
    """
    # 转换日志级别字符串为对应的常量
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    # 配置日志格式
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('wiki_fetcher.log', encoding='utf-8')
        ]
    )

def get_domain(url):
    """获取URL的域名
    
    Args:
        url (str): URL
        
    Returns:
        str: 域名
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc

def is_valid_url(url):
    """检查URL是否有效
    
    Args:
        url (str): URL
        
    Returns:
        bool: 是否有效
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def create_index_file(output_dir, pages):
    """创建索引文件
    
    Args:
        output_dir (str): 输出目录
        pages (list): 页面列表
    """
    index_content = ["# Wiki内容索引\n"]
    
    # 按标题排序
    sorted_pages = sorted(pages, key=lambda x: x['title'])
    
    for page in sorted_pages:
        # 获取相对路径
        rel_path = os.path.relpath(page['file_path'], output_dir)
        
        # 添加到索引
        index_content.append(f"- [{page['title']}]({rel_path})")
    
    # 写入索引文件
    index_path = os.path.join(output_dir, 'index.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(index_content))
    
    logging.info(f"索引文件已创建: {index_path}")

def get_file_size(file_path):
    """获取文件大小
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str: 格式化的文件大小
    """
    size_bytes = os.path.getsize(file_path)
    
    # 转换为可读格式
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.2f} TB"

def generate_summary(output_dir):
    """生成摘要信息
    
    Args:
        output_dir (str): 输出目录
        
    Returns:
        dict: 摘要信息
    """
    summary = {
        'total_pages': 0,
        'total_images': 0,
        'total_size': 0
    }
    
    # 统计页面数量
    pages_dir = os.path.join(output_dir, 'pages')
    if os.path.exists(pages_dir):
        md_files = [f for f in os.listdir(pages_dir) if f.endswith('.md')]
        summary['total_pages'] = len(md_files)
    
    # 统计图片数量
    images_dir = os.path.join(output_dir, 'images')
    if os.path.exists(images_dir):
        image_files = os.listdir(images_dir)
        summary['total_images'] = len(image_files)
    
    # 计算总大小
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            file_path = os.path.join(root, file)
            summary['total_size'] += os.path.getsize(file_path)
    
    # 转换总大小为可读格式
    for unit in ['B', 'KB', 'MB', 'GB']:
        if summary['total_size'] < 1024.0:
            summary['total_size_formatted'] = f"{summary['total_size']:.2f} {unit}"
            break
        summary['total_size'] /= 1024.0
    
    return summary 