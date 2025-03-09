#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - Web界面
提供用户友好的界面来配置和运行Wiki抓取工具
"""

import os
import sys
import json
import time
import threading
import logging
import shutil
import hashlib
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_from_directory
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, IntegerField, BooleanField, FloatField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange, URL, Optional
from urllib.parse import urlparse, urljoin
import re
from bs4 import BeautifulSoup
import random

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

try:
    # 导入日志设置模块
    from utils import setup_logging
except ImportError as e:
    print(f"导入模块错误: {str(e)}")
    print(f"Python路径: {sys.path}")
    raise

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # 使用随机生成的密钥
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

# 初始化扩展
bootstrap = Bootstrap(app)
csrf = CSRFProtect(app)  # 启用CSRF保护

# 全局变量
fetcher_thread = None
organize_thread = None
is_running = False
is_organizing = False
progress = {
    'total': 0,
    'current': 0,
    'status': '就绪',
    'start_time': None,
    'end_time': None,
    'log_messages': [],
    'pages_count': 0,
    'images_count': 0,
    'error_count': 0,
    'processing_speed': 0
}

# 自定义日志处理器
class WebLogHandler(logging.Handler):
    """将日志消息发送到Web界面"""
    
    def __init__(self, max_messages=100):
        """初始化处理器"""
        super().__init__()
        self.max_messages = max_messages
        self.messages = []
    
    def emit(self, record):
        """处理日志记录"""
        global progress
        
        # 格式化日志消息
        log_entry = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'level': record.levelname,
            'message': self.format(record)
        }
        
        # 添加到消息列表
        self.messages.append(log_entry)
        
        # 限制消息数量
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        # 更新全局进度信息
        progress['log_messages'] = self.messages

# 简化的Wiki爬虫类
class SimpleWikiFetcher:
    """简化的Wiki爬虫类，直接实现爬取功能"""
    
    def __init__(self, config):
        """初始化爬虫"""
        self.base_url = config['wiki_url']
        self.output_dir = config['output_dir']
        self.max_depth = config['max_depth']
        self.download_images = config['download_images']
        self.download_tables = config['download_tables']
        self.user_agent = config['user_agent'] or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.delay = config['delay']
        self.threads = config['threads']
        self.save_html = config['save_html']
        self.max_retries = config.get('max_retries', 3)
        
        # 解析基础URL
        parsed_url = urlparse(self.base_url)
        self.domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # 创建会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        })
        
        # 初始化URL队列和已访问URL集合
        self.url_queue = []
        self.visited_urls = set()
        
        # 创建必要的目录
        self._create_directories()
        
        logging.info(f"SimpleWikiFetcher初始化完成，基础URL: {self.base_url}, 输出目录: {self.output_dir}")
    
    def _create_directories(self):
        """创建必要的目录"""
        # 创建主输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 创建内容目录
        os.makedirs(os.path.join(self.output_dir, 'pages'), exist_ok=True)
        
        # 创建图片目录
        os.makedirs(os.path.join(self.output_dir, 'images'), exist_ok=True)
        
        # 创建表格目录
        os.makedirs(os.path.join(self.output_dir, 'tables'), exist_ok=True)
        
        # 创建HTML目录（如果需要保存HTML）
        if self.save_html:
            os.makedirs(os.path.join(self.output_dir, 'html'), exist_ok=True)
    
    def start(self):
        """开始爬取"""
        # 将起始URL添加到队列
        self.url_queue.append((self.base_url, 0))
        
        # 开始爬取
        self._crawl()
    
    def _crawl(self):
        """爬取Wiki页面"""
        global progress
        
        # 记录上次更新时间和处理数量，用于计算速度
        last_update_time = time.time()
        last_processed_count = 0
        
        logging.info(f"开始爬取，初始队列大小: {len(self.url_queue)}")
        
        # 使用线程池并发爬取
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            while self.url_queue and is_running:
                # 获取当前队列中的所有URL
                current_batch = self.url_queue.copy()
                self.url_queue.clear()
                
                logging.info(f"处理批次，大小: {len(current_batch)}")
                
                # 提交任务到线程池
                futures = [executor.submit(self._process_url, url, depth) 
                          for url, depth in current_batch]
                
                # 等待所有任务完成
                for future in futures:
                    try:
                        future.result()
                    except Exception as e:
                        logging.error(f"处理URL时发生错误: {str(e)}", exc_info=True)
                        progress['error_count'] += 1
                
                # 更新Web界面进度
                progress['current'] = len(self.visited_urls)
                progress['total'] = progress['current'] + len(self.url_queue)
                
                # 更新页面计数
                progress['pages_count'] = len(self.visited_urls)
                
                # 计算处理速度（每分钟处理的页面数）
                current_time = time.time()
                time_diff = current_time - last_update_time
                if time_diff >= 5:  # 每5秒更新一次速度
                    current_processed = progress['current']
                    count_diff = current_processed - last_processed_count
                    if time_diff > 0:
                        speed = (count_diff / time_diff) * 60  # 每分钟处理数量
                        progress['processing_speed'] = round(speed)
                    
                    last_update_time = current_time
                    last_processed_count = current_processed
                
                # 添加延迟，避免请求过于频繁
                time.sleep(0.1)
        
        logging.info(f"爬取完成，共处理 {len(self.visited_urls)} 个URL")
    
    def _process_url(self, url, depth):
        """处理单个URL"""
        global progress
        
        # 如果已经访问过或超出最大深度，则跳过
        if url in self.visited_urls or depth > self.max_depth:
            return
        
        # 标记为已访问
        self.visited_urls.add(url)
        
        try:
            logging.info(f"正在处理URL: {url}, 深度: {depth}")
            
            # 获取页面内容
            html_content = self._fetch_url(url)
            if not html_content:
                logging.warning(f"无法获取页面内容: {url}")
                return
            
            # 解析页面内容
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 获取页面标题
            title = self._get_title(soup, url)
            
            # 获取页面内容
            content = self._get_content(soup)
            
            # 获取页面链接
            links = self._get_links(soup, url)
            
            # 获取页面图片
            images = self._get_images(soup, url)
            
            # 获取页面表格
            tables = self._get_tables(soup)
            
            # 保存页面内容
            self._save_page(title, content, url, html_content)
            
            # 下载图片
            if self.download_images and images:
                for img_url in images:
                    self._download_image(img_url)
            
            # 保存表格
            if self.download_tables and tables:
                self._save_tables(title, tables)
            
            # 添加链接到队列
            if depth < self.max_depth:
                for link in links:
                    # 构建完整URL
                    full_link = urljoin(url, link)
                    # 只处理同一域名下的链接
                    if self.domain in full_link and full_link not in self.visited_urls:
                        self.url_queue.append((full_link, depth + 1))
            
            # 添加日志
            log_msg = f"已爬取: {title} ({url})"
            logging.info(log_msg)
            
            # 添加延迟
            delay_time = self.delay * (0.5 + random.random())
            time.sleep(delay_time)
            
        except Exception as e:
            logging.error(f"处理URL时发生错误: {url}, {str(e)}", exc_info=True)
            progress['error_count'] += 1
    
    def _fetch_url(self, url):
        """获取URL内容"""
        for retry in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logging.warning(f"获取URL失败: {url}, 重试 {retry+1}/{self.max_retries}, 错误: {str(e)}")
                time.sleep(1)  # 等待1秒后重试
        
        logging.error(f"获取URL失败，已达到最大重试次数: {url}")
        return None
    
    def _get_title(self, soup, url):
        """获取页面标题"""
        # 尝试从<title>标签获取
        title_tag = soup.find('title')
        if title_tag and title_tag.text:
            title = title_tag.text.strip()
            # 移除网站名称后缀
            title = re.sub(r'\s*[-|]\s*.*?$', '', title)
            return title
        
        # 尝试从<h1>标签获取
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.text:
            return h1_tag.text.strip()
        
        # 使用URL的最后部分作为标题
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        if path_parts and path_parts[-1]:
            return path_parts[-1].replace('_', ' ')
        
        # 使用域名作为标题
        return parsed_url.netloc
    
    def _get_content(self, soup):
        """获取页面内容"""
        # 尝试找到主要内容区域
        main_content = None
        
        # 常见的内容容器ID和类名
        content_selectors = [
            '#mw-content-text',  # MediaWiki
            '#bodyContent',      # MediaWiki
            '.mw-parser-output', # MediaWiki
            'article',           # 常见文章标签
            '.content',          # 常见内容类
            '#content',          # 常见内容ID
            'main',              # HTML5主要内容标签
        ]
        
        # 尝试找到主要内容区域
        for selector in content_selectors:
            if selector.startswith('#'):
                element = soup.find(id=selector[1:])
            elif selector.startswith('.'):
                element = soup.find(class_=selector[1:])
            else:
                element = soup.find(selector)
            
            if element:
                main_content = element
                break
        
        # 如果没有找到主要内容区域，使用<body>
        if not main_content:
            main_content = soup.find('body') or soup
        
        # 提取文本内容
        content = ""
        
        # 处理标题
        for i in range(1, 7):
            for heading in main_content.find_all(f'h{i}'):
                heading_text = heading.get_text().strip()
                if heading_text:
                    # 根据标题级别添加#
                    content += f"{'#' * i} {heading_text}\n\n"
        
        # 处理段落
        for p in main_content.find_all('p'):
            p_text = p.get_text().strip()
            if p_text:
                content += f"{p_text}\n\n"
        
        # 处理列表
        for ul in main_content.find_all('ul'):
            for li in ul.find_all('li'):
                li_text = li.get_text().strip()
                if li_text:
                    content += f"* {li_text}\n"
            content += "\n"
        
        for ol in main_content.find_all('ol'):
            for i, li in enumerate(ol.find_all('li')):
                li_text = li.get_text().strip()
                if li_text:
                    content += f"{i+1}. {li_text}\n"
            content += "\n"
        
        return content
    
    def _get_links(self, soup, base_url):
        """获取页面链接"""
        links = []
        
        # 获取所有<a>标签
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # 忽略空链接、锚点链接和JavaScript链接
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # 构建完整URL
            full_url = urljoin(base_url, href)
            
            # 只保留同一域名下的链接
            if self.domain in full_url:
                links.append(full_url)
        
        return links
    
    def _get_images(self, soup, base_url):
        """获取页面图片"""
        images = []
        
        # 获取所有<img>标签
        for img in soup.find_all('img', src=True):
            src = img['src']
            
            # 忽略数据URI和空链接
            if not src or src.startswith('data:'):
                continue
            
            # 构建完整URL
            full_url = urljoin(base_url, src)
            
            # 只保留图片URL
            if re.search(r'\.(jpg|jpeg|png|gif|webp|svg)(\?.*)?$', full_url, re.I):
                images.append(full_url)
        
        return images
    
    def _get_tables(self, soup):
        """获取页面表格"""
        tables = []
        
        # 获取所有<table>标签
        for table in soup.find_all('table'):
            # 提取表格数据
            table_data = []
            
            # 处理表头
            thead = table.find('thead')
            if thead:
                header_row = []
                for th in thead.find_all(['th', 'td']):
                    header_row.append(th.get_text().strip())
                if header_row:
                    table_data.append(header_row)
            
            # 处理表体
            tbody = table.find('tbody') or table
            for tr in tbody.find_all('tr'):
                row = []
                for td in tr.find_all(['td', 'th']):
                    row.append(td.get_text().strip())
                if row:
                    table_data.append(row)
            
            # 如果表格有数据，转换为CSV格式
            if table_data:
                csv_data = ""
                for row in table_data:
                    # 处理CSV中的特殊字符
                    escaped_row = []
                    for cell in row:
                        if '"' in cell:
                            cell = cell.replace('"', '""')
                        if ',' in cell or '"' in cell or '\n' in cell:
                            cell = f'"{cell}"'
                        escaped_row.append(cell)
                    csv_data += ",".join(escaped_row) + "\n"
                
                tables.append(csv_data)
        
        return tables
    
    def _save_page(self, title, content, url, html_content):
        """保存页面内容"""
        try:
            # 创建文件名
            file_name = self._sanitize_filename(title)
            if not file_name:
                file_name = hashlib.md5(url.encode()).hexdigest()
            
            # 保存Markdown内容
            md_path = os.path.join(self.output_dir, 'pages', f"{file_name}.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                f.write(f"URL: {url}\n\n")
                f.write(content)
            
            # 保存原始HTML
            if self.save_html:
                html_path = os.path.join(self.output_dir, 'html', f"{file_name}.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            logging.debug(f"已保存页面: {url} -> {file_name}")
            
        except Exception as e:
            logging.error(f"保存页面时出错: {url}, 错误: {str(e)}")
    
    def _download_image(self, img_url):
        """下载图片"""
        global progress
        
        try:
            # 获取图片文件名
            parsed_url = urlparse(img_url)
            file_name = os.path.basename(parsed_url.path)
            
            # 如果文件名为空或无效，使用URL的MD5哈希值
            if not file_name or not re.search(r'\.(jpg|jpeg|png|gif|webp|svg)$', file_name, re.I):
                file_name = f"{hashlib.md5(img_url.encode()).hexdigest()}.jpg"
            
            # 图片保存路径
            img_path = os.path.join(self.output_dir, 'images', file_name)
            
            # 如果图片已存在，跳过下载
            if os.path.exists(img_path):
                return
            
            # 下载图片
            for retry in range(self.max_retries):
                try:
                    response = self.session.get(img_url, timeout=30, stream=True)
                    response.raise_for_status()
                    
                    # 保存图片
                    with open(img_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # 更新图片计数
                    progress['images_count'] += 1
                    
                    logging.debug(f"已下载图片: {img_url} -> {file_name}")
                    return
                    
                except Exception as e:
                    logging.warning(f"下载图片失败: {img_url}, 重试 {retry+1}/{self.max_retries}, 错误: {str(e)}")
                    time.sleep(1)  # 等待1秒后重试
            
            logging.error(f"下载图片失败，已达到最大重试次数: {img_url}")
            
        except Exception as e:
            logging.error(f"下载图片时出错: {img_url}, 错误: {str(e)}")
    
    def _save_tables(self, title, tables):
        """保存表格"""
        try:
            # 创建文件名
            file_name = self._sanitize_filename(title)
            if not file_name:
                file_name = hashlib.md5(title.encode()).hexdigest()
            
            # 保存表格
            for i, table in enumerate(tables):
                table_path = os.path.join(self.output_dir, 'tables', f"{file_name}_table_{i+1}.csv")
                with open(table_path, 'w', encoding='utf-8') as f:
                    f.write(table)
            
            logging.debug(f"已保存表格: {title}, 数量: {len(tables)}")
            
        except Exception as e:
            logging.error(f"保存表格时出错: {title}, 错误: {str(e)}")
    
    def _sanitize_filename(self, name):
        """清理文件名"""
        # 移除非法字符
        name = re.sub(r'[\\/*?:"<>|]', '', name)
        # 将空格替换为下划线
        name = re.sub(r'\s+', '_', name)
        # 限制长度
        if len(name) > 100:
            name = name[:100]
        return name

# 表单类定义
class FetcherForm(FlaskForm):
    wiki_url = StringField('Wiki URL', 
        validators=[DataRequired(), URL()],
        description='要抓取的Wiki网站URL，例如：https://minecraft.fandom.com/zh/wiki/Minecraft_Wiki',
        render_kw={"placeholder": "https://example.com/wiki"})
    
    output_dir = StringField('输出目录',
        validators=[Optional()],
        description='保存抓取内容的目录，留空将自动根据Wiki名称创建目录',
        render_kw={"placeholder": "留空将自动创建目录"})
    
    max_depth = IntegerField('最大抓取深度', validators=[NumberRange(min=1, max=10)], default=2,
                            description='从起始页面开始，抓取链接的最大深度')
    download_images = BooleanField('下载图片', default=True,
                                 description='是否下载Wiki页面中的图片')
    download_tables = BooleanField('下载表格', default=True,
                                  description='是否保存Wiki页面中的表格数据')
    user_agent = StringField('User-Agent', 
                           description='HTTP请求的User-Agent头，留空使用默认值')
    delay = FloatField('请求延迟(秒)', validators=[NumberRange(min=0.5)], default=2.0,
                      description='两次请求之间的延迟时间，避免请求过于频繁')
    threads = IntegerField('并发线程数', validators=[NumberRange(min=1, max=10)], default=2,
                          description='同时进行抓取的线程数量')
    save_html = BooleanField('保存原始HTML', default=False,
                            description='是否保存页面的原始HTML内容')
    log_level = SelectField('日志级别', choices=[
        ('DEBUG', '调试'),
        ('INFO', '信息'),
        ('WARNING', '警告'),
        ('ERROR', '错误')
    ], default='INFO', description='日志记录的详细程度')
    max_retries = IntegerField('最大重试次数', validators=[NumberRange(min=1, max=10)], default=3,
                              description='请求失败时的最大重试次数')
    submit = SubmitField('开始抓取')

# 从环境变量或配置文件加载默认值
def load_default_config():
    """加载默认配置"""
    config = {}
    
    # 尝试从.env文件加载
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                try:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    # 转换键名格式
                    if key == 'WIKI_URL':
                        config['wiki_url'] = value
                    elif key == 'OUTPUT_DIR':
                        config['output_dir'] = value
                    elif key == 'MAX_DEPTH':
                        config['max_depth'] = int(value)
                    elif key == 'DOWNLOAD_IMAGES':
                        config['download_images'] = value.lower() == 'true'
                    elif key == 'DOWNLOAD_TABLES':
                        config['download_tables'] = value.lower() == 'true'
                    elif key == 'USER_AGENT':
                        config['user_agent'] = value
                    elif key == 'DELAY':
                        config['delay'] = float(value)
                    elif key == 'THREADS':
                        config['threads'] = int(value)
                    elif key == 'SAVE_HTML':
                        config['save_html'] = value.lower() == 'true'
                    elif key == 'LOG_LEVEL':
                        config['log_level'] = value
                    elif key == 'MAX_RETRIES':
                        config['max_retries'] = int(value)
                except (ValueError, TypeError):
                    pass  # 忽略格式不正确的行
    
    return config

# 创建并配置日志处理器
web_log_handler = WebLogHandler()
web_log_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
web_log_handler.setLevel(logging.INFO)

# 获取根日志记录器并添加处理器
root_logger = logging.getLogger()
root_logger.addHandler(web_log_handler)

# 内容整理功能
def organize_wiki_content(output_dir):
    """整理Wiki内容，按类型分类并优化结构"""
    global progress, is_organizing
    
    try:
        is_organizing = True
        logging.info(f"开始整理Wiki内容: {output_dir}")
        progress['status'] = '正在整理'
        
        # 创建整理后的目录结构
        organized_dir = os.path.join(output_dir, 'organized')
        os.makedirs(organized_dir, exist_ok=True)
        
        # 创建分类目录
        categories = {
            'pages': os.path.join(organized_dir, '页面'),
            'images': os.path.join(organized_dir, '图片'),
            'tables': os.path.join(organized_dir, '表格'),
            'other': os.path.join(organized_dir, '其他')
        }
        
        # 创建更详细的子分类
        subcategories = {
            'images': {
                'icons': os.path.join(categories['images'], '图标'),
                'screenshots': os.path.join(categories['images'], '截图'),
                'artwork': os.path.join(categories['images'], '插图'),
                'other': os.path.join(categories['images'], '其他')
            },
            'pages': {
                'main': os.path.join(categories['pages'], '主要页面'),
                'items': os.path.join(categories['pages'], '物品'),
                'characters': os.path.join(categories['pages'], '角色'),
                'locations': os.path.join(categories['pages'], '地点'),
                'mechanics': os.path.join(categories['pages'], '机制'),
                'other': os.path.join(categories['pages'], '其他')
            }
        }
        
        # 创建所有目录
        for category_dir in categories.values():
            os.makedirs(category_dir, exist_ok=True)
        
        for subcategory_dict in subcategories.values():
            for subcategory_dir in subcategory_dict.values():
                os.makedirs(subcategory_dir, exist_ok=True)
        
        # 统计信息
        stats = {
            'total_files': 0,
            'pages': 0,
            'images': 0,
            'tables': 0,
            'other': 0,
            'subcategories': {
                'images': {k: 0 for k in subcategories['images'].keys()},
                'pages': {k: 0 for k in subcategories['pages'].keys()}
            }
        }
        
        # 关键词映射，用于页面分类
        page_keywords = {
            'items': ['item', 'weapon', 'armor', 'tool', 'potion', 'equipment', '物品', '武器', '装备', '道具'],
            'characters': ['character', 'npc', 'enemy', 'boss', 'monster', '角色', '敌人', '怪物', 'villager'],
            'locations': ['location', 'place', 'map', 'area', 'region', 'biome', '地点', '区域', '地图'],
            'mechanics': ['mechanic', 'system', 'feature', 'gameplay', 'crafting', 'skill', '系统', '技能', '玩法']
        }
        
        # 遍历原始目录
        for root, dirs, files in os.walk(output_dir):
            # 跳过已整理的目录
            if 'organized' in root:
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                file_name = os.path.splitext(file)[0].lower()
                file_size = os.path.getsize(file_path)
                
                stats['total_files'] += 1
                
                # 根据文件类型分类
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']:
                    # 图片文件
                    stats['images'] += 1
                    
                    # 根据图片大小和名称进行子分类
                    if file_size < 10000 or 'icon' in file_name or file_name.startswith('icon_'):
                        dest_dir = subcategories['images']['icons']
                        stats['subcategories']['images']['icons'] += 1
                    elif 'screenshot' in file_name or 'screen' in file_name:
                        dest_dir = subcategories['images']['screenshots']
                        stats['subcategories']['images']['screenshots'] += 1
                    elif 'art' in file_name or 'illustration' in file_name:
                        dest_dir = subcategories['images']['artwork']
                        stats['subcategories']['images']['artwork'] += 1
                    else:
                        dest_dir = subcategories['images']['other']
                        stats['subcategories']['images']['other'] += 1
                
                elif file_ext in ['.md']:
                    # 页面文件
                    stats['pages'] += 1
                    
                    # 读取文件内容进行分类
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                        
                        # 根据内容关键词分类
                        category_found = False
                        for category, keywords in page_keywords.items():
                            if any(keyword in content for keyword in keywords):
                                dest_dir = subcategories['pages'][category]
                                stats['subcategories']['pages'][category] += 1
                                category_found = True
                                break
                        
                        if not category_found:
                            # 检查是否是主页
                            if 'main' in file_name or 'index' in file_name or 'home' in file_name:
                                dest_dir = subcategories['pages']['main']
                                stats['subcategories']['pages']['main'] += 1
                            else:
                                dest_dir = subcategories['pages']['other']
                                stats['subcategories']['pages']['other'] += 1
                    except:
                        dest_dir = subcategories['pages']['other']
                        stats['subcategories']['pages']['other'] += 1
                
                elif file_ext in ['.csv'] and 'table' in file.lower():
                    # 表格文件
                    dest_dir = categories['tables']
                    stats['tables'] += 1
                else:
                    # 其他文件
                    dest_dir = categories['other']
                    stats['other'] += 1
                
                # 复制文件到目标目录
                dest_path = os.path.join(dest_dir, file)
                try:
                    shutil.copy2(file_path, dest_path)
                    logging.info(f"已整理文件: {file} -> {dest_path}")
                except Exception as e:
                    logging.error(f"整理文件时出错: {file}, 错误: {str(e)}")
        
        # 创建索引文件
        index_path = os.path.join(organized_dir, 'index.html')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wiki内容索引</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; color: #333; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .category {{ margin-bottom: 30px; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .subcategory {{ margin: 15px 0; padding: 15px; background-color: #f9f9f9; border-radius: 5px; }}
        .category h2 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
        .subcategory h3 {{ color: #3498db; margin-top: 0; }}
        .file-list {{ list-style-type: none; padding: 0; }}
        .file-list li {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
        .file-list li:last-child {{ border-bottom: none; }}
        .file-list a {{ color: #3498db; text-decoration: none; }}
        .file-list a:hover {{ text-decoration: underline; }}
        .stats {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .stats h2 {{ margin-top: 0; color: #3498db; }}
        .stat-item {{ margin-bottom: 10px; }}
        .stat-value {{ font-size: 1.2em; font-weight: bold; color: #3498db; }}
        .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }}
        .stat-card {{ background-color: rgba(255,255,255,0.1); padding: 15px; border-radius: 5px; }}
        .stat-card h4 {{ margin-top: 0; color: #3498db; }}
        .search-box {{ margin-bottom: 20px; padding: 15px; background-color: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .search-box input {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }}
        @media (max-width: 768px) {{
            .stat-grid {{ grid-template-columns: 1fr 1fr; }}
        }}
        @media (max-width: 480px) {{
            .stat-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Wiki内容索引</h1>
        
        <div class="search-box">
            <input type="text" id="search-input" placeholder="搜索文件..." onkeyup="searchFiles()">
        </div>
        
        <div class="stats">
            <h2>统计信息</h2>
            <div class="stat-grid">
                <div class="stat-card">
                    <h4>总文件数</h4>
                    <div class="stat-value">{stats['total_files']}</div>
                </div>
                <div class="stat-card">
                    <h4>页面数量</h4>
                    <div class="stat-value">{stats['pages']}</div>
                </div>
                <div class="stat-card">
                    <h4>图片数量</h4>
                    <div class="stat-value">{stats['images']}</div>
                </div>
                <div class="stat-card">
                    <h4>表格数量</h4>
                    <div class="stat-value">{stats['tables']}</div>
                </div>
                <div class="stat-card">
                    <h4>其他文件</h4>
                    <div class="stat-value">{stats['other']}</div>
                </div>
                <div class="stat-card">
                    <h4>整理时间</h4>
                    <div class="stat-value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
            </div>
        </div>
""")
            
            # 页面分类
            f.write(f"""
        <div class="category">
            <h2>页面 ({stats['pages']})</h2>
""")
            
            for subcategory, subcategory_dir in subcategories['pages'].items():
                subcategory_files = os.listdir(subcategory_dir)
                if subcategory_files:
                    subcategory_title = os.path.basename(subcategory_dir)
                    f.write(f"""
            <div class="subcategory">
                <h3>{subcategory_title} ({len(subcategory_files)})</h3>
                <ul class="file-list">
""")
                    
                    for file in sorted(subcategory_files):
                        file_path = os.path.join('页面', subcategory_title, file)
                        f.write(f'                    <li><a href="{file_path}" target="_blank">{file}</a></li>\n')
                    
                    f.write("""                </ul>
            </div>
""")
            
            f.write("""        </div>
""")
            
            # 图片分类
            f.write(f"""
        <div class="category">
            <h2>图片 ({stats['images']})</h2>
""")
            
            for subcategory, subcategory_dir in subcategories['images'].items():
                subcategory_files = os.listdir(subcategory_dir)
                if subcategory_files:
                    subcategory_title = os.path.basename(subcategory_dir)
                    f.write(f"""
            <div class="subcategory">
                <h3>{subcategory_title} ({len(subcategory_files)})</h3>
                <ul class="file-list">
""")
                    
                    for file in sorted(subcategory_files):
                        file_path = os.path.join('图片', subcategory_title, file)
                        f.write(f'                    <li><a href="{file_path}" target="_blank">{file}</a></li>\n')
                    
                    f.write("""                </ul>
            </div>
""")
            
            f.write("""        </div>
""")
            
            # 表格分类
            table_files = os.listdir(categories['tables'])
            if table_files:
                f.write(f"""
        <div class="category">
            <h2>表格 ({stats['tables']})</h2>
            <ul class="file-list">
""")
                
                for file in sorted(table_files):
                    file_path = os.path.join('表格', file)
                    f.write(f'                <li><a href="{file_path}" target="_blank">{file}</a></li>\n')
                
                f.write("""            </ul>
        </div>
""")
            
            # 其他文件
            other_files = os.listdir(categories['other'])
            if other_files:
                f.write(f"""
        <div class="category">
            <h2>其他文件 ({stats['other']})</h2>
            <ul class="file-list">
""")
                
                for file in sorted(other_files):
                    file_path = os.path.join('其他', file)
                    f.write(f'                <li><a href="{file_path}" target="_blank">{file}</a></li>\n')
                
                f.write("""            </ul>
        </div>
""")
            
            # 添加搜索功能
            f.write("""
    </div>
    
    <script>
        function searchFiles() {
            const input = document.getElementById('search-input');
            const filter = input.value.toLowerCase();
            const fileItems = document.querySelectorAll('.file-list li');
            
            fileItems.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(filter)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
            
            // 隐藏空的子分类
            const subcategories = document.querySelectorAll('.subcategory');
            subcategories.forEach(subcategory => {
                const visibleItems = subcategory.querySelectorAll('li[style="display: none;"]');
                if (visibleItems.length === subcategory.querySelectorAll('li').length) {
                    subcategory.style.display = 'none';
                } else {
                    subcategory.style.display = '';
                }
            });
        }
    </script>
</body>
</html>""")
        
        logging.info(f"Wiki内容整理完成，索引文件已创建: {index_path}")
        progress['status'] = '整理完成'
        
    except Exception as e:
        logging.error(f"整理Wiki内容时出错: {str(e)}", exc_info=True)
        progress['status'] = '整理出错'
    finally:
        is_organizing = False

# 路由定义
@app.route('/', methods=['GET', 'POST'])
def index():
    """主页"""
    form = FetcherForm()
    if form.validate_on_submit():
        # 如果表单验证通过，直接启动抓取任务
        return start_fetcher_internal(form)
    
    # 加载默认配置
    default_config = load_default_config()
    
    # 创建表单并填充默认值
    form = FetcherForm()
    if default_config:
        for key, value in default_config.items():
            if hasattr(form, key):
                field = getattr(form, key)
                if value is not None:
                    field.data = value
    
    return render_template('index.html', form=form, progress=progress, is_running=is_running, is_organizing=is_organizing)

@app.route('/start', methods=['POST'])
def start_fetcher():
    """启动抓取任务"""
    # 验证表单
    form = FetcherForm()
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
        return redirect(url_for('index'))
    
    return start_fetcher_internal(form)

def start_fetcher_internal(form):
    """内部函数，启动抓取任务"""
    global fetcher_thread, is_running, progress
    
    # 如果已经在运行，则返回错误
    if is_running:
        flash('任务已在运行中，请等待完成或停止当前任务', 'warning')
        return redirect(url_for('index'))
    
    # 收集配置
    config = {
        'wiki_url': form.wiki_url.data,
        'output_dir': form.output_dir.data,
        'max_depth': form.max_depth.data,
        'download_images': form.download_images.data,
        'download_tables': form.download_tables.data,
        'user_agent': form.user_agent.data,
        'delay': form.delay.data,
        'threads': form.threads.data,
        'save_html': form.save_html.data,
        'log_level': form.log_level.data,
        'max_retries': form.max_retries.data
    }
    
    # 如果输出目录为空，根据Wiki URL自动生成
    if not config['output_dir']:
        wiki_url = config['wiki_url']
        parsed_url = urlparse(wiki_url)
        # 提取域名的第一部分作为Wiki名称
        wiki_name = parsed_url.netloc.split('.')[0]
        # 如果URL中包含wiki关键词，尝试提取更有意义的名称
        wiki_path = parsed_url.path.lower()
        if '/wiki/' in wiki_path:
            # 提取wiki/后面的第一个路径部分
            path_parts = [p for p in wiki_path.split('/') if p]
            if 'wiki' in path_parts:
                wiki_index = path_parts.index('wiki')
                if len(path_parts) > wiki_index + 1:
                    wiki_name = path_parts[wiki_index + 1]
        # 清理名称，只保留字母数字和下划线
        wiki_name = re.sub(r'[^\w\-]', '_', wiki_name)
        # 创建输出目录
        config['output_dir'] = os.path.join('output', wiki_name)
        logging.info(f"自动创建输出目录: {config['output_dir']}")
    
    # 保存配置到.env文件
    save_config_to_env(config)
    
    # 重置进度信息
    progress = {
        'total': 0,
        'current': 0,
        'status': '正在运行',
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': None,
        'log_messages': [],
        'pages_count': 0,
        'images_count': 0,
        'error_count': 0,
        'processing_speed': 0
    }
    
    # 设置日志级别
    setup_logging(config['log_level'])
    
    # 创建输出目录
    os.makedirs(config['output_dir'], exist_ok=True)
    
    # 在新线程中启动抓取任务
    def run_fetcher():
        global is_running, progress
        try:
            is_running = True
            logging.info(f"开始抓取Wiki: {config['wiki_url']}")
            
            # 创建并启动Wiki抓取器
            try:
                logging.info(f"初始化SimpleWikiFetcher，配置: {config}")
                fetcher = SimpleWikiFetcher(config)
                
                # 开始抓取
                logging.info("开始抓取过程")
                fetcher.start()
                
                logging.info(f"Wiki抓取完成。数据已保存到: {os.path.abspath(config['output_dir'])}")
                progress['status'] = '已完成'
            except Exception as e:
                logging.error(f"抓取器初始化或运行失败: {str(e)}", exc_info=True)
                progress['status'] = '出错'
                raise
        except Exception as e:
            logging.error(f"抓取过程中发生错误: {str(e)}", exc_info=True)
            progress['status'] = '出错'
        finally:
            is_running = False
            progress['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    fetcher_thread = threading.Thread(target=run_fetcher)
    fetcher_thread.daemon = True
    fetcher_thread.start()
    
    flash('抓取任务已启动', 'success')
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop_fetcher():
    """停止抓取任务"""
    global is_running, progress
    
    if is_running:
        is_running = False
        progress['status'] = '已停止'
        progress['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logging.info("抓取任务已手动停止")
        flash('抓取任务已停止', 'warning')
    else:
        flash('没有正在运行的任务', 'info')
    
    return redirect(url_for('index'))

@app.route('/organize', methods=['POST'])
def organize_content():
    """整理抓取内容"""
    global organize_thread, is_organizing
    
    # 如果已经在整理或抓取中，则返回错误
    if is_organizing or is_running:
        flash('无法整理内容，有任务正在运行', 'warning')
        return redirect(url_for('index'))
    
    # 获取输出目录
    default_config = load_default_config()
    output_dir = default_config.get('output_dir', '')
    
    # 如果输出目录为空，使用默认目录
    if not output_dir:
        output_dir = os.path.join('output', 'default')
        os.makedirs(output_dir, exist_ok=True)
        flash(f'使用默认输出目录: {output_dir}', 'info')
    
    # 确保目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        flash(f'创建输出目录: {output_dir}', 'info')
    
    # 检查目录是否为空
    is_empty = True
    for _, _, files in os.walk(output_dir):
        if files:
            is_empty = False
            break
    
    if is_empty:
        flash('输出目录为空，没有内容可以整理', 'warning')
        return redirect(url_for('index'))
    
    # 在新线程中启动整理任务
    organize_thread = threading.Thread(target=organize_wiki_content, args=(output_dir,))
    organize_thread.daemon = True
    organize_thread.start()
    
    flash('内容整理任务已启动', 'success')
    return redirect(url_for('index'))

@app.route('/progress')
def get_progress():
    """获取进度信息"""
    return jsonify(progress)

@app.route('/logs')
def get_logs():
    """获取日志消息"""
    return jsonify(progress['log_messages'])

@app.route('/download/<path:filename>')
def download_file(filename):
    """下载文件"""
    default_config = load_default_config()
    output_dir = default_config.get('output_dir', '')
    
    return send_from_directory(output_dir, filename, as_attachment=True)

@app.route('/view_index')
def view_index():
    """查看整理后的索引页面"""
    default_config = load_default_config()
    output_dir = default_config.get('output_dir', '')
    
    if not output_dir:
        flash('输出目录未设置', 'danger')
        return redirect(url_for('index'))
    
    index_path = os.path.join(output_dir, 'organized', 'index.html')
    if not os.path.exists(index_path):
        flash('索引文件不存在，请先整理内容', 'warning')
        return redirect(url_for('index'))
    
    return send_from_directory(os.path.join(output_dir, 'organized'), 'index.html')

def save_config_to_env(config):
    """保存配置到.env文件"""
    env_content = """# GameWiki Fetcher 配置文件
# 此文件由Web界面自动生成，也可以手动编辑

# Wiki URL
WIKI_URL="{wiki_url}"

# 输出目录
OUTPUT_DIR="{output_dir}"

# 最大抓取深度
MAX_DEPTH={max_depth}

# 是否下载图片
DOWNLOAD_IMAGES={download_images}

# 是否下载表格
DOWNLOAD_TABLES={download_tables}

# 用户代理
USER_AGENT="{user_agent}"

# 请求延迟(秒)
DELAY={delay}

# 并发线程数
THREADS={threads}

# 是否保存原始HTML
SAVE_HTML={save_html}

# 日志级别 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL="{log_level}"

# 最大重试次数
MAX_RETRIES={max_retries}
""".format(
        wiki_url=config['wiki_url'],
        output_dir=config['output_dir'],
        max_depth=config['max_depth'],
        download_images=str(config['download_images']).lower(),
        download_tables=str(config['download_tables']).lower(),
        user_agent=config['user_agent'] or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        delay=config['delay'],
        threads=config['threads'],
        save_html=str(config['save_html']).lower(),
        log_level=config['log_level'],
        max_retries=config['max_retries']
    )
    
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'服务器错误: {error}')
    return render_template('error.html', error=error), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error='页面未找到'), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 