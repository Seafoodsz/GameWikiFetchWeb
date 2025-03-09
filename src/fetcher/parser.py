#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WikiParser - HTML解析器
负责解析Wiki页面内容，提取文本、链接、图片等资源
"""

import re
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

class WikiParser:
    """Wiki页面解析器类"""
    
    def __init__(self):
        """初始化解析器"""
        pass
    
    def parse_page(self, html, url):
        """解析页面内容
        
        Args:
            html (str): 页面HTML内容
            url (str): 页面URL
            
        Returns:
            dict: 解析后的页面数据
        """
        try:
            # 创建BeautifulSoup对象
            soup = BeautifulSoup(html, 'lxml')
            
            # 获取页面标题
            title = self._get_title(soup)
            
            # 获取页面内容
            content = self._get_content(soup)
            
            # 获取页面链接
            links = self._get_links(soup, url)
            
            # 获取页面图片
            images = self._get_images(soup, url)
            
            # 获取页面表格
            tables = self._get_tables(soup)
            
            # 构建页面数据
            page_data = {
                'url': url,
                'title': title,
                'content': content,
                'links': links,
                'images': images,
                'tables': tables,
                'html': html
            }
            
            return page_data
            
        except Exception as e:
            logging.error(f"解析页面时出错: {url}, 错误: {str(e)}")
            # 返回空数据
            return {
                'url': url,
                'title': '',
                'content': '',
                'links': [],
                'images': [],
                'tables': [],
                'html': html
            }
    
    def _get_title(self, soup):
        """获取页面标题
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
            
        Returns:
            str: 页面标题
        """
        # 尝试从h1标签获取标题
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        # 尝试从title标签获取标题
        title = soup.find('title')
        if title:
            return title.get_text(strip=True)
        
        return "未知标题"
    
    def _get_content(self, soup):
        """获取页面内容
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
            
        Returns:
            str: 页面内容
        """
        # 尝试获取主要内容区域
        # 不同Wiki平台的内容区域ID或类名可能不同，这里列出常见的几种
        content_selectors = [
            '#mw-content-text',  # MediaWiki
            '#bodyContent',      # MediaWiki
            '.mw-parser-output', # MediaWiki
            'article',           # 一般文章
            'main',              # 主要内容
            '#content',          # 内容区域
            '.content'           # 内容区域
        ]
        
        for selector in content_selectors:
            content_area = soup.select_one(selector)
            if content_area:
                # 移除脚本和样式
                for script in content_area(["script", "style"]):
                    script.decompose()
                
                # 获取文本内容
                text = content_area.get_text(separator='\n', strip=True)
                return text
        
        # 如果没有找到内容区域，则返回body内容
        body = soup.find('body')
        if body:
            # 移除脚本和样式
            for script in body(["script", "style"]):
                script.decompose()
            
            # 获取文本内容
            text = body.get_text(separator='\n', strip=True)
            return text
        
        return ""
    
    def _get_links(self, soup, base_url):
        """获取页面链接
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
            base_url (str): 基础URL
            
        Returns:
            list: 链接列表
        """
        links = []
        
        # 获取所有a标签
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # 跳过空链接、锚点链接和javascript链接
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # 构建完整URL
            full_url = urljoin(base_url, href)
            
            # 只保留HTTP和HTTPS链接
            if full_url.startswith(('http://', 'https://')):
                links.append(full_url)
        
        return list(set(links))  # 去重
    
    def _get_images(self, soup, base_url):
        """获取页面图片
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
            base_url (str): 基础URL
            
        Returns:
            list: 图片URL列表
        """
        images = []
        
        # 获取所有img标签
        for img in soup.find_all('img', src=True):
            src = img['src']
            
            # 跳过数据URI
            if src.startswith('data:'):
                continue
            
            # 构建完整URL
            full_url = urljoin(base_url, src)
            
            # 只保留HTTP和HTTPS链接
            if full_url.startswith(('http://', 'https://')):
                images.append(full_url)
        
        return list(set(images))  # 去重
    
    def _get_tables(self, soup):
        """获取页面表格
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
            
        Returns:
            list: 表格数据列表
        """
        tables_data = []
        
        # 获取所有table标签
        for table in soup.find_all('table'):
            # 提取表格标题
            caption = table.find('caption')
            table_title = caption.get_text(strip=True) if caption else "未命名表格"
            
            # 提取表头
            headers = []
            thead = table.find('thead')
            if thead:
                th_tags = thead.find_all('th')
                if th_tags:
                    headers = [th.get_text(strip=True) for th in th_tags]
            
            # 如果没有找到表头，尝试从第一行获取
            if not headers:
                first_row = table.find('tr')
                if first_row:
                    th_tags = first_row.find_all('th')
                    if th_tags:
                        headers = [th.get_text(strip=True) for th in th_tags]
            
            # 提取表格数据
            rows = []
            for tr in table.find_all('tr')[1:] if headers else table.find_all('tr'):
                cells = []
                for td in tr.find_all(['td', 'th']):
                    cells.append(td.get_text(strip=True))
                if cells:
                    rows.append(cells)
            
            # 构建表格数据
            table_data = {
                'title': table_title,
                'headers': headers,
                'rows': rows
            }
            
            tables_data.append(table_data)
        
        return tables_data 