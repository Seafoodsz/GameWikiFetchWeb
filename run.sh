#!/bin/bash

echo "GameWiki Fetcher - 游戏Wiki资料获取工具"
echo "======================================"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python。请安装Python 3.6或更高版本。"
    exit 1
fi

# 检查是否需要安装依赖
if [ ! -d "venv" ]; then
    echo "首次运行，正在创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "正在安装依赖..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 运行程序
echo "正在启动Wiki抓取程序..."
python3 run.py "$@"

echo "程序执行完毕。" 