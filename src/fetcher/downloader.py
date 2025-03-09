#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 资源下载器
负责下载图片、文件等资源
"""

import os
import logging
import requests
from urllib.parse import urljoin, urlparse
import time
import random

class ResourceDownloader:
    """资源下载器，负责下载图片、文件等资源"""
    
    def __init__(self, base_url, output_dir, delay=1, user_agent=None, max_retries=3):
        """
        初始化资源下载器
        
        Args:
            base_url (str): Wiki网站的基础URL
            output_dir (str): 本地保存数据的目录
            delay (float): 请求之间的延迟（秒）
            user_agent (str): 自定义User-Agent
            max_retries (int): 请求失败时的最大重试次数
        """
        self.base_url = base_url
        self.output_dir = output_dir
        self.delay = delay
        self.max_retries = max_retries
        
        # 设置请求头
        self.headers = {
            'User-Agent': user_agent or 'GameWikiFetcher/1.0'
        }
        
        # 创建输出目录
        self.images_dir = os.path.join(output_dir, 'images')
        os.makedirs(self.images_dir, exist_ok=True)
        
        self.logger = logging.getLogger('downloader')
    
    def download_image(self, image_url, referer=None):
        """
        下载图片
        
        Args:
            image_url (str): 图片URL
            referer (str): 引用页面URL
            
        Returns:
            str: 本地保存的图片路径，下载失败则返回None
        """
        if not image_url:
            return None
        
        # 构建完整URL
        if not image_url.startswith(('http://', 'https://')):
            image_url = urljoin(self.base_url, image_url)
        
        # 解析URL，获取文件名
        parsed_url = urlparse(image_url)
        image_filename = os.path.basename(parsed_url.path)
        
        # 如果文件名为空或无效，使用URL的MD5哈希作为文件名
        if not image_filename or '?' in image_filename or len(image_filename) > 100:
            import hashlib
            image_filename = hashlib.md5(image_url.encode()).hexdigest() + '.jpg'
        
        # 本地保存路径
        local_path = os.path.join(self.images_dir, image_filename)
        
        # 如果文件已存在，直接返回路径
        if os.path.exists(local_path):
            self.logger.debug(f"图片已存在: {local_path}")
            return local_path
        
        # 设置请求头
        headers = self.headers.copy()
        if referer:
            headers['Referer'] = referer
        
        # 下载图片
        for retry in range(self.max_retries):
            try:
                self.logger.info(f"下载图片: {image_url}")
                response = requests.get(image_url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()
                
                # 保存图片
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.logger.info(f"图片已保存: {local_path}")
                
                # 添加延迟
                time.sleep(self.delay + random.uniform(0, 0.5))
                
                return local_path
                
            except Exception as e:
                self.logger.warning(f"下载图片失败 ({retry+1}/{self.max_retries}): {str(e)}")
                time.sleep(self.delay * (retry + 1))  # 指数退避
        
        self.logger.error(f"下载图片失败，已达到最大重试次数: {image_url}")
        return None
    
    def download_file(self, file_url, output_subdir=None, referer=None):
        """
        下载文件
        
        Args:
            file_url (str): 文件URL
            output_subdir (str): 输出子目录
            referer (str): 引用页面URL
            
        Returns:
            str: 本地保存的文件路径，下载失败则返回None
        """
        if not file_url:
            return None
        
        # 构建完整URL
        if not file_url.startswith(('http://', 'https://')):
            file_url = urljoin(self.base_url, file_url)
        
        # 解析URL，获取文件名
        parsed_url = urlparse(file_url)
        filename = os.path.basename(parsed_url.path)
        
        # 如果文件名为空或无效，使用URL的MD5哈希作为文件名
        if not filename or '?' in filename or len(filename) > 100:
            import hashlib
            filename = hashlib.md5(file_url.encode()).hexdigest() + '.bin'
        
        # 本地保存路径
        if output_subdir:
            output_dir = os.path.join(self.output_dir, output_subdir)
            os.makedirs(output_dir, exist_ok=True)
        else:
            output_dir = self.output_dir
        
        local_path = os.path.join(output_dir, filename)
        
        # 如果文件已存在，直接返回路径
        if os.path.exists(local_path):
            self.logger.debug(f"文件已存在: {local_path}")
            return local_path
        
        # 设置请求头
        headers = self.headers.copy()
        if referer:
            headers['Referer'] = referer
        
        # 下载文件
        for retry in range(self.max_retries):
            try:
                self.logger.info(f"下载文件: {file_url}")
                response = requests.get(file_url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()
                
                # 保存文件
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.logger.info(f"文件已保存: {local_path}")
                
                # 添加延迟
                time.sleep(self.delay + random.uniform(0, 0.5))
                
                return local_path
                
            except Exception as e:
                self.logger.warning(f"下载文件失败 ({retry+1}/{self.max_retries}): {str(e)}")
                time.sleep(self.delay * (retry + 1))  # 指数退避
        
        self.logger.error(f"下载文件失败，已达到最大重试次数: {file_url}")
        return None 