@echo off
echo Stoneshard Wiki 数据传输工具
echo ============================
echo.

REM 创建输入目录（如果不存在）
if not exist "StoneshardDataProcessor\input\characters" mkdir "StoneshardDataProcessor\input\characters"
if not exist "StoneshardDataProcessor\input\skills" mkdir "StoneshardDataProcessor\input\skills"
if not exist "StoneshardDataProcessor\input\items" mkdir "StoneshardDataProcessor\input\items"
if not exist "StoneshardDataProcessor\input\enemies" mkdir "StoneshardDataProcessor\input\enemies"
if not exist "StoneshardDataProcessor\input\locations" mkdir "StoneshardDataProcessor\input\locations"
if not exist "StoneshardDataProcessor\input\quests" mkdir "StoneshardDataProcessor\input\quests"

REM 复制角色数据
echo 复制角色数据...
copy "output\pages\characters\*.html" "StoneshardDataProcessor\input\characters\" /Y

REM 复制技能数据
echo 复制技能数据...
copy "output\pages\skills\*.html" "StoneshardDataProcessor\input\skills\" /Y

REM 复制物品数据
echo 复制物品数据...
copy "output\pages\items\*.html" "StoneshardDataProcessor\input\items\" /Y

REM 复制敌人数据
echo 复制敌人数据...
copy "output\pages\enemies\*.html" "StoneshardDataProcessor\input\enemies\" /Y

REM 复制地点数据
echo 复制地点数据...
copy "output\pages\locations\*.html" "StoneshardDataProcessor\input\locations\" /Y

REM 复制任务数据
echo 复制任务数据...
copy "output\pages\quests\*.html" "StoneshardDataProcessor\input\quests\" /Y

echo.
echo 数据传输完成，现在可以运行 StoneshardDataProcessor\run_processor.bat 进行数据处理。
pause 