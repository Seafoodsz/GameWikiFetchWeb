#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 内容提取器
负责从Wiki页面中提取有用信息
"""

import logging
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class ContentExtractor:
    """内容提取器，负责从Wiki页面中提取有用信息"""
    
    def __init__(self, base_url):
        """
        初始化内容提取器
        
        Args:
            base_url (str): Wiki网站的基础URL
        """
        self.base_url = base_url
        self.logger = logging.getLogger('extractor')
    
    def extract_title(self, soup):
        """
        提取页面标题
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
            
        Returns:
            str: 页面标题
        """
        # 尝试从h1标签提取标题
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        # 尝试从title标签提取标题
        title = soup.find('title')
        if title:
            title_text = title.get_text().strip()
            # 移除网站名称后缀
            if ' - ' in title_text:
                return title_text.split(' - ')[0].strip()
            return title_text
        
        return "未知标题"
    
    def extract_content(self, soup, url):
        """
        提取页面主要内容
        
        Args:
            soup (BeautifulSoup): BeautifulSoup对象
            url (str): 页面URL
            
        Returns:
            dict: 包含提取内容的字典
        """
        result = {
            'title': self.extract_title(soup),
            'url': url,
            'content': '',
            'images': [],
            'tables': [],
            'links': []
        }
        
        # 尝试找到主要内容区域
        content_area = None
        
        # 常见的Wiki内容区域ID和类名
        content_selectors = [
            '#mw-content-text',  # MediaWiki
            '#bodyContent',      # MediaWiki
            '.mw-parser-output', # MediaWiki
            '#content',          # 通用
            '.content',          # 通用
            'article',           # HTML5
            '.article',          # 通用
            'main',              # HTML5
            '.main'              # 通用
        ]
        
        for selector in content_selectors:
            if selector.startswith('#'):
                element = soup.find(id=selector[1:])
            elif selector.startswith('.'):
                element = soup.find(class_=selector[1:])
            else:
                element = soup.find(selector)
            
            if element:
                content_area = element
                self.logger.debug(f"找到内容区域: {selector}")
                break
        
        # 如果没有找到内容区域，使用body
        if not content_area:
            content_area = soup.find('body') or soup
            self.logger.debug("未找到特定内容区域，使用body或整个文档")
        
        # 提取内容
        result['content'] = self._extract_text_content(content_area)
        
        # 提取图片
        result['images'] = self._extract_images(content_area)
        
        # 提取表格
        result['tables'] = self._extract_tables(content_area)
        
        # 提取链接
        result['links'] = self._extract_links(content_area, url)
        
        return result
    
    def _extract_text_content(self, element):
        """
        提取文本内容
        
        Args:
            element (Tag): BeautifulSoup标签对象
            
        Returns:
            str: 提取的文本内容
        """
        # 创建一个副本，避免修改原始对象
        content = element.__copy__()
        
        # 移除不需要的元素
        for unwanted in content.find_all(['script', 'style', 'nav', 'footer', 'aside']):
            unwanted.decompose()
        
        # 移除评论
        for comment in content.find_all(text=lambda text: isinstance(text, str) and text.strip().startswith('<!--')):
            comment.extract()
        
        # 获取文本内容
        text = content.get_text('\n', strip=True)
        
        # 清理文本
        text = re.sub(r'\n{3,}', '\n\n', text)  # 移除多余的空行
        
        return text
    
    def _extract_images(self, element):
        """
        提取图片
        
        Args:
            element (Tag): BeautifulSoup标签对象
            
        Returns:
            list: 图片URL列表
        """
        images = []
        
        # 查找所有img标签
        for img in element.find_all('img'):
            src = img.get('src')
            if src:
                # 如果是相对URL，转换为绝对URL
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(self.base_url, src)
                
                # 过滤掉小图标和装饰图片
                width = img.get('width')
                height = img.get('height')
                if width and height and (int(width) < 50 or int(height) < 50):
                    continue
                
                # 过滤掉常见的图标和装饰图片
                if any(x in src.lower() for x in ['icon', 'logo', 'button', 'bg', 'background']):
                    continue
                
                images.append(src)
        
        return images
    
    def _extract_tables(self, element):
        """
        提取表格
        
        Args:
            element (Tag): BeautifulSoup标签对象
            
        Returns:
            list: 表格数据列表
        """
        tables = []
        
        # 查找所有table标签
        for table in element.find_all('table'):
            table_data = {
                'caption': '',
                'headers': [],
                'rows': []
            }
            
            # 提取表格标题
            caption = table.find('caption')
            if caption:
                table_data['caption'] = caption.get_text().strip()
            
            # 提取表头
            headers = []
            thead = table.find('thead')
            if thead:
                th_elements = thead.find_all('th')
                if th_elements:
                    headers = [th.get_text().strip() for th in th_elements]
            
            # 如果没有找到thead，尝试从第一行提取表头
            if not headers:
                first_row = table.find('tr')
                if first_row:
                    th_elements = first_row.find_all('th')
                    if th_elements:
                        headers = [th.get_text().strip() for th in th_elements]
            
            table_data['headers'] = headers
            
            # 提取表格行
            rows = []
            for tr in table.find_all('tr'):
                # 跳过表头行
                if tr.find_parent('thead'):
                    continue
                
                # 提取单元格
                cells = []
                for td in tr.find_all(['td', 'th']):
                    cells.append(td.get_text().strip())
                
                if cells:
                    rows.append(cells)
            
            table_data['rows'] = rows
            
            # 只添加非空表格
            if table_data['rows']:
                tables.append(table_data)
        
        return tables
    
    def _extract_links(self, element, current_url):
        """
        提取链接
        
        Args:
            element (Tag): BeautifulSoup标签对象
            current_url (str): 当前页面URL
            
        Returns:
            list: 链接字典列表，每个字典包含url和text
        """
        links = []
        current_domain = urlparse(current_url).netloc
        
        # 查找所有a标签
        for a in element.find_all('a'):
            href = a.get('href')
            if not href:
                continue
            
            # 忽略锚点链接
            if href.startswith('#'):
                continue
            
            # 忽略JavaScript链接
            if href.startswith('javascript:'):
                continue
            
            # 如果是相对URL，转换为绝对URL
            if not href.startswith(('http://', 'https://')):
                href = urljoin(current_url, href)
            
            # 只保留同一域名下的链接
            if urlparse(href).netloc != current_domain:
                continue
            
            # 提取链接文本
            text = a.get_text().strip()
            if not text:
                # 如果没有文本，尝试使用title属性或alt属性
                text = a.get('title', '') or a.get('alt', '')
            
            # 只添加有文本的链接
            if text:
                links.append({
                    'url': href,
                    'text': text
                })
        
        return links 