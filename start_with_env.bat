@echo off
chcp 65001 >nul
echo ========================================
echo 黄金监控中台启动脚本（含环境变量）
echo ========================================
echo.

REM 设置FRED API密钥
set FRED_API_KEY=38b7f7dc5b334dfea2c32abdac59232f
echo [配置] FRED API密钥已设置

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo [提示] 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo [警告] 虚拟环境不存在，使用全局Python
)

echo [提示] 启动服务器...
echo.
cd backend
python main.py

pause
