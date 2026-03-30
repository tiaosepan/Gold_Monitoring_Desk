@echo off
chcp 65001 >nul
echo ========================================
echo 黄金监控中台启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查是否已安装依赖
if not exist "venv\" (
    echo [提示] 首次运行，正在创建虚拟环境...
    python -m venv venv
    echo [提示] 虚拟环境创建完成
)

echo [提示] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 检查依赖是否安装
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖包...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo [提示] 依赖安装完成
)

REM 加载环境变量（如果.env文件存在）
if exist ".env" (
    echo [提示] 正在加载环境配置...
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" (
            set "%%a=%%b"
        )
    )
)

echo [提示] 启动服务器（安全模式 - 自动清理旧进程）...
echo.
python safe_start.py

pause
