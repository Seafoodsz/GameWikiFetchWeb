#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - Web界面测试脚本
用于验证Web应用是否能够正常启动
"""

import os
import sys
import importlib

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.append(root_dir)

def check_module(module_name):
    """检查模块是否可以导入"""
    try:
        module = importlib.import_module(module_name)
        print(f"✓ 模块 {module_name} 导入成功")
        return True
    except ImportError as e:
        print(f"✗ 模块 {module_name} 导入失败: {str(e)}")
        return False

def check_file(file_path):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        print(f"✓ 文件 {file_path} 存在")
        return True
    else:
        print(f"✗ 文件 {file_path} 不存在")
        return False

def check_directory(dir_path):
    """检查目录是否存在"""
    if os.path.isdir(dir_path):
        print(f"✓ 目录 {dir_path} 存在")
        return True
    else:
        print(f"✗ 目录 {dir_path} 不存在")
        return False

def main():
    """主函数"""
    print("开始测试Web应用...")
    
    # 检查必要的模块
    modules_ok = True
    modules_ok &= check_module('flask')
    modules_ok &= check_module('flask_bootstrap')
    modules_ok &= check_module('flask_wtf')
    modules_ok &= check_module('wtforms')
    modules_ok &= check_module('bs4')
    modules_ok &= check_module('requests')
    
    # 检查必要的文件和目录
    files_ok = True
    files_ok &= check_file(os.path.join(root_dir, 'src', 'web', 'app.py'))
    files_ok &= check_directory(os.path.join(root_dir, 'src', 'web', 'templates'))
    files_ok &= check_directory(os.path.join(root_dir, 'src', 'web', 'static'))
    files_ok &= check_file(os.path.join(root_dir, 'src', 'utils', 'logger.py'))
    files_ok &= check_file(os.path.join(root_dir, 'src', 'utils', 'config.py'))
    
    # 尝试导入Flask应用
    app_ok = False
    try:
        from src.web.app import app
        print(f"✓ Flask应用导入成功")
        app_ok = True
    except Exception as e:
        print(f"✗ Flask应用导入失败: {str(e)}")
    
    # 总结
    if modules_ok and files_ok and app_ok:
        print("\n✓ 所有检查通过，Web应用应该可以正常启动")
        return 0
    else:
        print("\n✗ 检查未通过，Web应用可能无法正常启动")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 