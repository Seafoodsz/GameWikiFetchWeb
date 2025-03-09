#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WikiStorage - 本地存储管理
负责将Wiki内容保存到本地文件系统
"""

import os
import re
import json
import logging
from urllib.parse import urlparse, unquote
import hashlib

class WikiStorage:
    """Wiki存储器类"""
    
    def __init__(self, output_dir, save_html=False):
        """初始化存储器
        
        Args:
            output_dir (str): 输出目录
            save_html (bool): 是否保存原始HTML
        """
        self.output_dir = output_dir
        self.save_html = save_html
        
        # 创建必要的目录
        self._create_directories()
    
    def _create_directories(self):
        """创建必要的目录"""
        # 创建主输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 创建内容目录
        os.makedirs(os.path.join(self.output_dir, 'pages'), exist_ok=True)
        
        # 创建图片目录
        os.makedirs(os.path.join(self.output_dir, 'images'), exist_ok=True)
        
        # 创建HTML目录（如果需要保存HTML）
        if self.save_html:
            os.makedirs(os.path.join(self.output_dir, 'html'), exist_ok=True)
    
    def save_page(self, page_data):
        """保存页面内容
        
        Args:
            page_data (dict): 页面数据
        """
        try:
            # 获取URL路径
            url_path = self._get_url_path(page_data['url'])
            
            # 创建文件名
            file_name = self._sanitize_filename(url_path)
            
            # 如果文件名为空，使用URL的MD5哈希值
            if not file_name:
                file_name = self._get_url_hash(page_data['url'])
            
            # 保存页面内容
            self._save_page_content(page_data, file_name)
            
            # 保存原始HTML（如果配置了）
            if self.save_html:
                self._save_html(page_data['html'], file_name)
            
            # 保存表格数据
            if page_data['tables']:
                self._save_tables(page_data['tables'], file_name)
            
            logging.debug(f"已保存页面: {page_data['url']} -> {file_name}")
            
        except Exception as e:
            logging.error(f"保存页面时出错: {page_data['url']}, 错误: {str(e)}")
    
    def save_image(self, img_url, img_data):
        """保存图片
        
        Args:
            img_url (str): 图片URL
            img_data (bytes): 图片数据
        """
        try:
            # 获取URL路径
            url_path = self._get_url_path(img_url)
            
            # 创建文件名
            file_name = self._sanitize_filename(url_path)
            
            # 如果文件名为空，使用URL的MD5哈希值
            if not file_name:
                file_name = self._get_url_hash(img_url)
            
            # 确保文件有正确的扩展名
            file_name = self._ensure_image_extension(file_name, img_url)
            
            # 保存图片
            img_path = os.path.join(self.output_dir, 'images', file_name)
            with open(img_path, 'wb') as f:
                f.write(img_data)
            
            logging.debug(f"已保存图片: {img_url} -> {file_name}")
            
        except Exception as e:
            logging.error(f"保存图片时出错: {img_url}, 错误: {str(e)}")
    
    def _save_page_content(self, page_data, file_name):
        """保存页面内容
        
        Args:
            page_data (dict): 页面数据
            file_name (str): 文件名
        """
        # 构建Markdown内容
        md_content = self._build_markdown(page_data)
        
        # 保存Markdown文件
        md_path = os.path.join(self.output_dir, 'pages', f"{file_name}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # 保存元数据
        meta_data = {
            'url': page_data['url'],
            'title': page_data['title'],
            'links': page_data['links'],
            'images': page_data['images']
        }
        
        meta_path = os.path.join(self.output_dir, 'pages', f"{file_name}.json")
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, ensure_ascii=False, indent=2)
    
    def _save_html(self, html, file_name):
        """保存原始HTML
        
        Args:
            html (str): HTML内容
            file_name (str): 文件名
        """
        html_path = os.path.join(self.output_dir, 'html', f"{file_name}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def _save_tables(self, tables, file_name):
        """保存表格数据
        
        Args:
            tables (list): 表格数据列表
            file_name (str): 文件名
        """
        tables_path = os.path.join(self.output_dir, 'pages', f"{file_name}_tables.json")
        with open(tables_path, 'w', encoding='utf-8') as f:
            json.dump(tables, f, ensure_ascii=False, indent=2)
    
    def _build_markdown(self, page_data):
        """构建Markdown内容
        
        Args:
            page_data (dict): 页面数据
            
        Returns:
            str: Markdown内容
        """
        md = []
        
        # 添加标题
        md.append(f"# {page_data['title']}\n")
        
        # 添加原始URL
        md.append(f"原始URL: {page_data['url']}\n")
        
        # 添加内容
        md.append(page_data['content'])
        
        # 添加表格（如果有）
        if page_data['tables']:
            md.append("\n## 表格\n")
            
            for i, table in enumerate(page_data['tables']):
                md.append(f"\n### {table['title']}\n")
                
                # 如果有表头，添加表头
                if table['headers']:
                    md.append("| " + " | ".join(table['headers']) + " |")
                    md.append("| " + " | ".join(["---"] * len(table['headers'])) + " |")
                    
                    # 添加表格数据
                    for row in table['rows']:
                        # 确保行数据与表头数量一致
                        while len(row) < len(table['headers']):
                            row.append("")
                        md.append("| " + " | ".join(row) + " |")
                else:
                    # 没有表头的表格
                    for row in table['rows']:
                        md.append("| " + " | ".join(row) + " |")
        
        return "\n".join(md)
    
    def _get_url_path(self, url):
        """获取URL路径
        
        Args:
            url (str): URL
            
        Returns:
            str: URL路径
        """
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # 解码URL
        path = unquote(path)
        
        # 移除文件扩展名
        path = os.path.splitext(path)[0]
        
        # 移除开头的斜杠
        if path.startswith('/'):
            path = path[1:]
        
        return path
    
    def _sanitize_filename(self, filename):
        """清理文件名
        
        Args:
            filename (str): 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 替换非法字符
        filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
        
        # 替换空格
        filename = filename.replace(' ', '_')
        
        # 限制长度
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename
    
    def _get_url_hash(self, url):
        """获取URL的MD5哈希值
        
        Args:
            url (str): URL
            
        Returns:
            str: MD5哈希值
        """
        return hashlib.md5(url.encode()).hexdigest()
    
    def _ensure_image_extension(self, filename, url):
        """确保图片文件有正确的扩展名
        
        Args:
            filename (str): 文件名
            url (str): 图片URL
            
        Returns:
            str: 带有正确扩展名的文件名
        """
        # 获取URL中的扩展名
        ext = os.path.splitext(url)[1].lower()
        
        # 如果文件名已经有扩展名，则返回
        if os.path.splitext(filename)[1]:
            return filename
        
        # 如果URL中有有效的扩展名，则使用它
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp']:
            return f"{filename}{ext}"
        
        # 默认使用.jpg扩展名
        return f"{filename}.jpg" 