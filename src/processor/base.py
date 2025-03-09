#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 基础处理器
定义数据处理器的基类
"""

import os
import logging
import glob
from bs4 import BeautifulSoup
import re

class BaseProcessor:
    """数据处理器基类，定义通用处理逻辑"""
    
    def __init__(self, input_dir, output_dir, config=None):
        """
        初始化基础处理器
        
        Args:
            input_dir (str): 输入数据目录
            output_dir (str): 输出数据目录
            config (dict): 处理器配置
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.config = config or {}
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取处理器名称（子类名称）
        self.name = self.__class__.__name__.replace('Processor', '').lower()
        
        # 创建日志记录器
        self.logger = logging.getLogger(f'processor.{self.name}')
    
    def get_input_files(self, pattern=None):
        """
        获取输入文件列表
        
        Args:
            pattern (str): 文件匹配模式，如果为None则使用配置中的pattern
            
        Returns:
            list: 输入文件路径列表
        """
        if pattern is None:
            pattern = self.config.get('input_pattern', '*.html')
            # 如果目录中没有HTML文件，尝试查找Markdown文件
            if not glob.glob(os.path.join(self.input_dir, pattern)):
                pattern = '*.md'
        
        # 构建完整的匹配模式
        full_pattern = os.path.join(self.input_dir, pattern)
        
        # 获取匹配的文件列表
        files = glob.glob(full_pattern)
        
        self.logger.info(f"找到 {len(files)} 个输入文件: {full_pattern}")
        
        # 如果没有找到文件，尝试查找子目录
        if not files:
            # 检查子目录
            subdirs = [d for d in os.listdir(self.input_dir) if os.path.isdir(os.path.join(self.input_dir, d))]
            self.logger.info(f"在 {self.input_dir} 中找到子目录: {subdirs}")
            
            # 尝试在子目录中查找文件
            for subdir in subdirs:
                subdir_pattern = os.path.join(self.input_dir, subdir, pattern)
                subdir_files = glob.glob(subdir_pattern)
                if subdir_files:
                    self.logger.info(f"在子目录 {subdir} 中找到 {len(subdir_files)} 个文件")
                    files.extend(subdir_files)
        
        return files
    
    def load_html(self, file_path):
        """
        加载HTML文件
        
        Args:
            file_path (str): HTML文件路径
            
        Returns:
            BeautifulSoup: BeautifulSoup对象，加载失败则返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            soup = BeautifulSoup(html, 'html.parser')
            return soup
        except Exception as e:
            self.logger.error(f"加载HTML文件失败: {file_path}, 错误: {str(e)}")
            return None
    
    def load_markdown(self, file_path):
        """
        加载Markdown文件
        
        Args:
            file_path (str): Markdown文件路径
            
        Returns:
            BeautifulSoup: BeautifulSoup对象，加载失败则返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                markdown = f.read()
            
            # 将Markdown转换为HTML格式
            # 简单处理：将标题转换为h标签，列表项转换为li标签
            html = markdown
            # 处理标题 (# 标题)
            html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            
            # 处理列表项 (* 列表项)
            html = re.sub(r'^\* (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
            
            # 处理URL行
            html = re.sub(r'^URL: (.+)$', r'<div class="url">\1</div>', html, flags=re.MULTILINE)
            
            # 将列表项包装在ul标签中
            html = re.sub(r'(<li>.+</li>\n)+', r'<ul>\n\g<0></ul>', html, flags=re.DOTALL)
            
            soup = BeautifulSoup(html, 'html.parser')
            return soup
        except Exception as e:
            self.logger.error(f"加载Markdown文件失败: {file_path}, 错误: {str(e)}")
            return None
    
    def save_output(self, data, filename, subdir=None):
        """
        保存输出数据
        
        Args:
            data: 要保存的数据
            filename (str): 文件名
            subdir (str): 子目录名，如果为None则使用处理器名称
            
        Returns:
            str: 保存的文件路径，保存失败则返回None
        """
        if subdir is None:
            subdir = self.name
        
        # 构建输出目录
        output_dir = os.path.join(self.output_dir, subdir)
        os.makedirs(output_dir, exist_ok=True)
        
        # 构建输出文件路径
        output_path = os.path.join(output_dir, filename)
        
        try:
            # 根据文件扩展名决定保存方式
            ext = os.path.splitext(filename)[1].lower()
            
            if ext == '.json':
                import json
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            elif ext == '.csv':
                import csv
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    if isinstance(data, list) and data and isinstance(data[0], dict):
                        # 如果是字典列表，使用DictWriter
                        fieldnames = data[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(data)
                    elif isinstance(data, list):
                        # 如果是普通列表，使用writer
                        writer = csv.writer(f)
                        writer.writerows(data)
                    else:
                        raise ValueError("CSV数据必须是列表")
            
            elif ext in ['.txt', '.md']:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(str(data))
            
            else:
                # 默认以文本方式保存
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(str(data))
            
            self.logger.info(f"已保存输出文件: {output_path}")
            return output_path
        
        except Exception as e:
            self.logger.error(f"保存输出文件失败: {output_path}, 错误: {str(e)}")
            return None
    
    def process(self):
        """
        处理数据的主方法，子类必须实现此方法
        
        Returns:
            bool: 处理是否成功
        """
        raise NotImplementedError("子类必须实现process方法")
    
    def extract_data(self, soup, file_path):
        """
        从BeautifulSoup对象中提取数据，子类必须实现此方法
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
            file_path (str): 源文件路径
            
        Returns:
            dict: 提取的数据
        """
        raise NotImplementedError("子类必须实现extract_data方法")
    
    def clean_data(self, data):
        """
        清理和规范化数据
        
        Args:
            data (dict): 原始数据
            
        Returns:
            dict: 清理后的数据
        """
        # 基本实现，子类可以覆盖此方法提供更复杂的清理逻辑
        if not data:
            return {}
        
        # 移除None值
        return {k: v for k, v in data.items() if v is not None}
    
    def validate_data(self, data):
        """
        验证数据是否有效
        
        Args:
            data (dict): 要验证的数据
            
        Returns:
            bool: 数据是否有效
        """
        # 基本实现，子类可以覆盖此方法提供更复杂的验证逻辑
        return bool(data)
    
    def run(self):
        """
        运行处理器
        
        Returns:
            bool: 处理是否成功
        """
        self.logger.info(f"开始运行处理器: {self.name}")
        
        try:
            result = self.process()
            
            if result:
                self.logger.info(f"处理器运行成功: {self.name}")
            else:
                self.logger.warning(f"处理器运行完成，但可能存在问题: {self.name}")
            
            return result
        
        except Exception as e:
            self.logger.error(f"处理器运行失败: {self.name}, 错误: {str(e)}", exc_info=True)
            return False 