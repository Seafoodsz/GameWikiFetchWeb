#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GameWiki Fetcher - 运行脚本
用于快速启动Wiki抓取程序
"""

import os
import sys

# 确保src目录在Python路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# 导入主程序
from src.main import main

if __name__ == "__main__":
    main()