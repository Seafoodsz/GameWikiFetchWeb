@echo off
echo 正在启动GameWiki Fetcher Web界面...

REM 检查Python是否安装
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到Python。请安装Python 3.6或更高版本。
    pause
    exit /b 1
)

REM 检查scripts目录是否存在
if not exist scripts (
    echo 错误: 未找到scripts目录。请确保您在正确的目录中运行此脚本。
    pause
    exit /b 1
)

REM 检查run_web.py是否存在
if not exist scripts\run_web.py (
    echo 错误: 未找到scripts\run_web.py文件。请确保项目文件完整。
    pause
    exit /b 1
)

REM 检查src/web/app.py是否存在
if not exist src\web\app.py (
    echo 错误: 未找到src\web\app.py文件。请确保项目文件完整。
    pause
    exit /b 1
)

REM 检查src/web/templates目录是否存在
if not exist src\web\templates (
    echo 错误: 未找到src\web\templates目录。请确保项目文件完整。
    pause
    exit /b 1
)

REM 检查必要的数据目录是否存在
if not exist data (
    echo 创建data目录...
    mkdir data
)

if not exist wiki_data (
    echo 创建wiki_data目录...
    mkdir wiki_data
)

if not exist data\input (
    echo 创建data\input目录...
    mkdir data\input
)

if not exist data\output (
    echo 创建data\output目录...
    mkdir data\output
)

if not exist logs (
    echo 创建logs目录...
    mkdir logs
)

REM 运行Web界面
echo 正在启动Web服务器，请稍候...
python scripts\run_web.py
if %ERRORLEVEL% neq 0 (
    echo 错误: Web服务器启动失败。请查看日志文件了解详情。
    pause
    exit /b 1
)

pause 