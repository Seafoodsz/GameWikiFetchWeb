#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WikiFetcher - Wiki抓取核心逻辑
负责抓取Wiki页面、解析内容并保存到本地
"""

import os
import time
import logging
import requests
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import random

from parser import WikiParser
from storage import WikiStorage

class WikiFetcher:
    """Wiki抓取器类"""
    
    def __init__(self, config):
        """初始化Wiki抓取器
        
        Args:
            config (dict): 配置参数
        """
        self.config = config
        self.base_url = config['wiki_url']
        self.output_dir = config['output_dir']
        self.max_depth = config['max_depth']
        self.download_images = config['download_images']
        self.download_tables = config['download_tables']
        self.user_agent = config['user_agent']
        self.delay = config['delay']
        self.threads = config['threads']
        self.save_html = config['save_html']
        self.max_retries = config.get('max_retries', 3)  # 最大重试次数
        
        # 设置请求头
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # 初始化解析器和存储器
        self.parser = WikiParser()
        self.storage = WikiStorage(self.output_dir, self.save_html)
        
        # 已访问的URL集合
        self.visited_urls = set()
        
        # 待访问的URL队列 (URL, depth)
        self.url_queue = []
        
        # 域名限制 - 只抓取同一域名下的内容
        self.domain = urlparse(self.base_url).netloc
        
        # 创建会话对象，重用连接
        self.session = requests.Session()
        
    def start(self):
        """开始抓取Wiki"""
        logging.info(f"开始抓取Wiki: {self.base_url}")
        
        # 将起始URL添加到队列
        self.url_queue.append((self.base_url, 0))
        
        # 开始抓取
        self._crawl()
        
    def _crawl(self):
        """抓取Wiki页面"""
        # 创建进度条
        progress_bar = tqdm(total=len(self.url_queue), desc="抓取进度")
        
        # 使用线程池并发抓取
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            while self.url_queue:
                # 获取当前队列中的所有URL
                current_batch = self.url_queue.copy()
                self.url_queue.clear()
                
                # 提交任务到线程池
                futures = [executor.submit(self._process_url, url, depth) 
                          for url, depth in current_batch]
                
                # 等待所有任务完成
                for future in futures:
                    future.result()
                
                # 更新进度条
                progress_bar.update(len(current_batch))
                progress_bar.total = len(self.url_queue) + progress_bar.n
        
        progress_bar.close()
        
    def _process_url(self, url, depth):
        """处理单个URL
        
        Args:
            url (str): 要处理的URL
            depth (int): 当前深度
        """
        # 如果URL已访问或深度超过限制，则跳过
        if url in self.visited_urls or depth > self.max_depth:
            return
        
        # 标记URL为已访问
        self.visited_urls.add(url)
        
        # 重试机制
        for retry in range(self.max_retries):
            try:
                # 添加随机延迟，避免请求过于规律
                delay_time = self.delay * (1 + random.random())
                time.sleep(delay_time)
                
                # 发送请求
                response = self.session.get(
                    url, 
                    headers=self.headers, 
                    timeout=30,
                    verify=True  # 验证SSL证书
                )
                response.raise_for_status()
                
                # 解析页面内容
                page_data = self.parser.parse_page(response.text, url)
                
                # 保存页面内容
                self.storage.save_page(page_data)
                
                # 如果配置了下载图片，则下载图片
                if self.download_images and page_data['images']:
                    for img_url in page_data['images']:
                        self._download_image(img_url)
                
                # 将新的URL添加到队列
                if depth < self.max_depth:
                    for link in page_data['links']:
                        # 构建完整URL
                        full_url = urljoin(url, link)
                        
                        # 只处理同一域名下的URL
                        if urlparse(full_url).netloc == self.domain:
                            # 添加到队列
                            if full_url not in self.visited_urls:
                                self.url_queue.append((full_url, depth + 1))
                
                # 成功处理，跳出重试循环
                break
            
            except requests.exceptions.SSLError as e:
                logging.warning(f"SSL错误 (尝试 {retry+1}/{self.max_retries}): {url}, 错误: {str(e)}")
                if retry == self.max_retries - 1:
                    logging.error(f"处理URL时出错: {url}, 错误: {str(e)}")
            
            except requests.exceptions.ConnectionError as e:
                logging.warning(f"连接错误 (尝试 {retry+1}/{self.max_retries}): {url}, 错误: {str(e)}")
                if retry == self.max_retries - 1:
                    logging.error(f"处理URL时出错: {url}, 错误: {str(e)}")
                # 连接错误时增加更长的延迟
                time.sleep(self.delay * 2)
            
            except requests.exceptions.Timeout as e:
                logging.warning(f"请求超时 (尝试 {retry+1}/{self.max_retries}): {url}, 错误: {str(e)}")
                if retry == self.max_retries - 1:
                    logging.error(f"处理URL时出错: {url}, 错误: {str(e)}")
                # 超时时增加更长的延迟
                time.sleep(self.delay * 2)
            
            except requests.exceptions.HTTPError as e:
                # 对于404等客户端错误，不进行重试
                if 400 <= e.response.status_code < 500:
                    logging.error(f"处理URL时出错: {url}, 错误: {e.response.status_code} {e.response.reason}")
                    break
                
                logging.warning(f"HTTP错误 (尝试 {retry+1}/{self.max_retries}): {url}, 错误: {str(e)}")
                if retry == self.max_retries - 1:
                    logging.error(f"处理URL时出错: {url}, 错误: {str(e)}")
            
            except Exception as e:
                logging.warning(f"未知错误 (尝试 {retry+1}/{self.max_retries}): {url}, 错误: {str(e)}")
                if retry == self.max_retries - 1:
                    logging.error(f"处理URL时出错: {url}, 错误: {str(e)}")
    
    def _download_image(self, img_url):
        """下载图片
        
        Args:
            img_url (str): 图片URL
        """
        # 如果图片URL已经处理过，则跳过
        if img_url in self.visited_urls:
            return
        
        # 标记图片URL为已访问
        self.visited_urls.add(img_url)
        
        # 重试机制
        for retry in range(self.max_retries):
            try:
                # 添加随机延迟
                delay_time = self.delay * (1 + random.random() * 0.5)
                time.sleep(delay_time)
                
                # 发送请求
                response = self.session.get(
                    img_url, 
                    headers=self.headers, 
                    timeout=30,
                    verify=True,  # 验证SSL证书
                    stream=True   # 流式下载大文件
                )
                response.raise_for_status()
                
                # 保存图片
                self.storage.save_image(img_url, response.content)
                
                # 成功下载，跳出重试循环
                break
                
            except requests.exceptions.SSLError as e:
                logging.warning(f"SSL错误 (尝试 {retry+1}/{self.max_retries}): {img_url}, 错误: {str(e)}")
                if retry == self.max_retries - 1:
                    logging.error(f"下载图片时出错: {img_url}, 错误: {str(e)}")
            
            except requests.exceptions.ConnectionError as e:
                logging.warning(f"连接错误 (尝试 {retry+1}/{self.max_retries}): {img_url}, 错误: {str(e)}")
                if retry == self.max_retries - 1:
                    logging.error(f"下载图片时出错: {img_url}, 错误: {str(e)}")
                # 连接错误时增加更长的延迟
                time.sleep(self.delay * 2)
            
            except requests.exceptions.Timeout as e:
                logging.warning(f"请求超时 (尝试 {retry+1}/{self.max_retries}): {img_url}, 错误: {str(e)}")
                if retry == self.max_retries - 1:
                    logging.error(f"下载图片时出错: {img_url}, 错误: {str(e)}")
                # 超时时增加更长的延迟
                time.sleep(self.delay * 2)
            
            except requests.exceptions.HTTPError as e:
                # 对于404等客户端错误，不进行重试
                if 400 <= e.response.status_code < 500:
                    logging.error(f"下载图片时出错: {img_url}, 错误: {e.response.status_code} {e.response.reason}")
                    break
                
                logging.warning(f"HTTP错误 (尝试 {retry+1}/{self.max_retries}): {img_url}, 错误: {str(e)}")
                if retry == self.max_retries - 1:
                    logging.error(f"下载图片时出错: {img_url}, 错误: {str(e)}")
            
            except Exception as e:
                logging.warning(f"未知错误 (尝试 {retry+1}/{self.max_retries}): {img_url}, 错误: {str(e)}")
                if retry == self.max_retries - 1:
                    logging.error(f"下载图片时出错: {img_url}, 错误: {str(e)}") 