@echo off
echo GameWiki 数据传输工具
echo ============================
echo.

REM 获取游戏名称
set /p GAME_NAME=请输入游戏名称: 

REM 创建输入目录（如果不存在）
if not exist "data\processed\%GAME_NAME%\json" mkdir "data\processed\%GAME_NAME%\json"
if not exist "data\processed\%GAME_NAME%\csv" mkdir "data\processed\%GAME_NAME%\csv"
if not exist "data\processed\%GAME_NAME%\html" mkdir "data\processed\%GAME_NAME%\html"

REM 设置源目录和目标目录
set SOURCE_DIR=data\raw\%GAME_NAME%\pages
set TARGET_DIR=processor\input\%GAME_NAME%

REM 创建目标目录（如果不存在）
if not exist "%TARGET_DIR%\characters" mkdir "%TARGET_DIR%\characters"
if not exist "%TARGET_DIR%\skills" mkdir "%TARGET_DIR%\skills"
if not exist "%TARGET_DIR%\items" mkdir "%TARGET_DIR%\items"
if not exist "%TARGET_DIR%\enemies" mkdir "%TARGET_DIR%\enemies"
if not exist "%TARGET_DIR%\locations" mkdir "%TARGET_DIR%\locations"
if not exist "%TARGET_DIR%\quests" mkdir "%TARGET_DIR%\quests"

REM 复制数据
echo 复制角色数据...
copy "%SOURCE_DIR%\characters\*.html" "%TARGET_DIR%\characters\" /Y

echo 复制技能数据...
copy "%SOURCE_DIR%\skills\*.html" "%TARGET_DIR%\skills\" /Y

echo 复制物品数据...
copy "%SOURCE_DIR%\items\*.html" "%TARGET_DIR%\items\" /Y

echo 复制敌人数据...
copy "%SOURCE_DIR%\enemies\*.html" "%TARGET_DIR%\enemies\" /Y

echo 复制地点数据...
copy "%SOURCE_DIR%\locations\*.html" "%TARGET_DIR%\locations\" /Y

echo 复制任务数据...
copy "%SOURCE_DIR%\quests\*.html" "%TARGET_DIR%\quests\" /Y

echo.
echo 数据传输完成，现在可以运行处理模块进行数据处理。
echo 运行命令: scripts\run_processor.bat %GAME_NAME%
pause 