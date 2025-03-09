#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - Web界面启动脚本
"""

import os
import sys
import argparse
import webbrowser
import threading
import time

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.append(root_dir)

from src.utils.config import ConfigManager
from src.utils.logger import setup_logging

# 导入Flask应用
try:
    from src.web.app import app
except ImportError as e:
    print(f"导入Flask应用失败: {str(e)}")
    print(f"Python路径: {sys.path}")
    sys.exit(1)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='启动GameWiki Fetcher Web界面')
    
    parser.add_argument('--host', type=str, help='主机地址')
    parser.add_argument('--port', type=int, help='端口号')
    parser.add_argument('--debug', action='store_true', help='是否启用调试模式')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
    parser.add_argument('--log-level', type=str, help='日志级别')
    parser.add_argument('--config-file', type=str, help='配置文件路径')
    
    return parser.parse_args()

def open_browser(host, port, delay=2):
    """
    在新线程中打开浏览器
    
    Args:
        host (str): 主机地址
        port (int): 端口号
        delay (int): 延迟时间（秒）
    """
    def _open_browser():
        time.sleep(delay)
        url = f"http://{host}:{port}"
        webbrowser.open(url)
        print(f"已在浏览器中打开: {url}")
    
    thread = threading.Thread(target=_open_browser)
    thread.daemon = True
    thread.start()

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
        log_file=log_config.get('file', 'logs/web.log'),
        max_size=log_config.get('max_size', 10485760),
        backup_count=log_config.get('backup_count', 5)
    )
    
    # 获取Web配置
    web_config = config.get('web', {})
    
    # 命令行参数优先级高于配置文件
    host = args.host or web_config.get('host', '0.0.0.0')
    port = args.port or web_config.get('port', 5000)
    debug = args.debug or web_config.get('debug', False)
    
    # 设置Flask应用密钥
    secret_key = web_config.get('secret_key')
    if secret_key:
        app.config['SECRET_KEY'] = secret_key
    else:
        # 如果没有设置密钥，使用随机生成的密钥
        app.config['SECRET_KEY'] = os.urandom(24)
    
    # 设置其他Flask配置
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    
    # 如果不是调试模式，自动打开浏览器
    if not debug and not args.no_browser:
        open_browser(
            '127.0.0.1' if host == '0.0.0.0' else host,
            port
        )
    
    # 启动Flask应用
    print(f"启动Web界面，请访问: http://{'127.0.0.1' if host == '0.0.0.0' else host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main() 