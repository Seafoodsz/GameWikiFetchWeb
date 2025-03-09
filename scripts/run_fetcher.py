#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 抓取功能启动脚本
"""

import os
import sys
import argparse

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.append(root_dir)

from src.utils.config import ConfigManager
from src.utils.logger import setup_logging
from src.fetcher import WikiFetcher

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
    parser.add_argument('--config-file', type=str, help='配置文件路径')
    
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 加载配置
    config_manager = ConfigManager(args.config_file)
    config = config_manager.config
    
    # 设置日志
    log_config = config.get('logging', {})
    setup_logging(
        log_level=args.log_level or log_config.get('level', 'INFO'),
        log_file=log_config.get('file', 'logs/fetcher.log'),
        max_size=log_config.get('max_size', 10485760),
        backup_count=log_config.get('backup_count', 5)
    )
    
    # 获取抓取配置
    fetcher_config = config.get('fetcher', {})
    
    # 命令行参数优先级高于配置文件
    if args.wiki_url:
        fetcher_config['wiki_url'] = args.wiki_url
    if args.output_dir:
        fetcher_config['output_dir'] = args.output_dir
    if args.max_depth is not None:
        fetcher_config['max_depth'] = args.max_depth
    if args.download_images is not None:
        fetcher_config['download_images'] = args.download_images
    if args.download_tables is not None:
        fetcher_config['download_tables'] = args.download_tables
    if args.user_agent:
        fetcher_config['user_agent'] = args.user_agent
    if args.delay is not None:
        fetcher_config['delay'] = args.delay
    if args.threads is not None:
        fetcher_config['threads'] = args.threads
    if args.save_html is not None:
        fetcher_config['save_html'] = args.save_html
    if args.max_retries is not None:
        fetcher_config['max_retries'] = args.max_retries
    
    # 检查必要参数
    if not fetcher_config.get('wiki_url'):
        print("错误: 未指定Wiki URL。请通过命令行参数或配置文件设置wiki_url。")
        sys.exit(1)
    
    # 处理输出目录
    if not fetcher_config.get('output_dir'):
        # 如果未指定输出目录，根据Wiki URL自动生成
        wiki_url = fetcher_config['wiki_url']
        from urllib.parse import urlparse
        import re
        
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
        fetcher_config['output_dir'] = os.path.join(root_dir, 'wiki_data', wiki_name)
    elif not os.path.isabs(fetcher_config['output_dir']):
        # 如果是相对路径，转换为绝对路径
        fetcher_config['output_dir'] = os.path.join(root_dir, fetcher_config['output_dir'])
    
    # 确保输出目录存在
    os.makedirs(fetcher_config['output_dir'], exist_ok=True)
    
    # 创建并启动Wiki抓取器
    fetcher = WikiFetcher(fetcher_config)
    fetcher.start()
    
    print(f"Wiki抓取完成。数据已保存到: {os.path.abspath(fetcher_config.get('output_dir', 'wiki_data'))}")

if __name__ == "__main__":
    main() 