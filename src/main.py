#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 主程序入口
用于获取游戏Wiki资料并保存到本地的工具
"""

import os
import sys
import argparse
import logging
# from dotenv import load_dotenv

# 添加自定义的环境变量加载函数
def load_dotenv():
    """简单的环境变量加载函数，替代 python-dotenv"""
    try:
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    try:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"\'')
                    except ValueError:
                        pass  # 忽略格式不正确的行
            print("已加载.env文件")
        else:
            print(".env文件不存在")
    except Exception as e:
        print(f"无法加载.env文件: {e}")

from fetcher import WikiFetcher
from utils import setup_logging

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='获取游戏Wiki资料并保存到本地')
    
    parser.add_argument('--wiki-url', type=str, help='Wiki网站的基础URL')
    parser.add_argument('--output-dir', type=str, help='本地保存数据的目录')
    parser.add_argument('--max-depth', type=int, help='抓取的最大深度')
    parser.add_argument('--download-images', type=bool, help='是否下载图片')
    parser.add_argument('--download-tables', type=bool, help='是否下载表格数据')
    parser.add_argument('--user-agent', type=str, help='自定义User-Agent')
    parser.add_argument('--delay', type=float, help='请求之间的延迟（秒）')
    parser.add_argument('--threads', type=int, help='并发下载线程数')
    parser.add_argument('--save-html', type=bool, help='是否保存原始HTML')
    parser.add_argument('--log-level', type=str, help='日志级别')
    parser.add_argument('--max-retries', type=int, help='请求失败时的最大重试次数')
    
    return parser.parse_args()

def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    args = parse_args()
    
    # 配置参数优先级：命令行参数 > 环境变量 > 默认值
    config = {
        'wiki_url': args.wiki_url or os.getenv('WIKI_URL'),
        'output_dir': args.output_dir or os.getenv('OUTPUT_DIR', './wiki_data'),
        'max_depth': args.max_depth or int(os.getenv('MAX_DEPTH', 3)),
        'download_images': args.download_images if args.download_images is not None else os.getenv('DOWNLOAD_IMAGES', 'True').lower() == 'true',
        'download_tables': args.download_tables if args.download_tables is not None else os.getenv('DOWNLOAD_TABLES', 'True').lower() == 'true',
        'user_agent': args.user_agent or os.getenv('USER_AGENT', 'GameWikiFetcher/1.0'),
        'delay': args.delay or float(os.getenv('DELAY', 1)),
        'threads': args.threads or int(os.getenv('THREADS', 3)),
        'save_html': args.save_html if args.save_html is not None else os.getenv('SAVE_HTML', 'False').lower() == 'true',
        'log_level': args.log_level or os.getenv('LOG_LEVEL', 'INFO'),
        'max_retries': args.max_retries or int(os.getenv('MAX_RETRIES', 3)),
    }
    
    # 设置日志
    setup_logging(config['log_level'])
    
    # 检查必要参数
    if not config['wiki_url']:
        logging.error("错误: 未指定Wiki URL。请通过命令行参数或.env文件设置WIKI_URL。")
        sys.exit(1)
    
    # 创建输出目录
    os.makedirs(config['output_dir'], exist_ok=True)
    
    # 创建并启动Wiki抓取器
    fetcher = WikiFetcher(config)
    fetcher.start()
    
    logging.info(f"Wiki抓取完成。数据已保存到: {os.path.abspath(config['output_dir'])}")

if __name__ == "__main__":
    main() 