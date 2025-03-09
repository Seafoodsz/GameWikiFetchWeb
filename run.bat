@echo off
echo GameWiki Fetcher - 游戏Wiki资料获取工具
echo ======================================

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python。请安装Python 3.6或更高版本。
    pause
    exit /b 1
)

REM 检查是否需要安装依赖
if not exist venv (
    echo 首次运行，正在创建虚拟环境...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo 正在安装依赖...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM 运行程序
echo 正在启动Wiki抓取程序...
python run.py %*

echo 程序执行完毕。
pause 