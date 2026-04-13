@echo off
chcp 65001 >nul

:: 一键启动后端服务脚本
:: 使用方法: 双击运行 start-backend.bat

set "PROJECT_ROOT=C:\Users\cry\Desktop\SmartSafetyGuardSystemForPark-main"
set "VENV_PATH=%PROJECT_ROOT%\venv"

echo ========================================
echo   园区智能安防系统 - 后端启动脚本
echo ========================================
echo.

:: 检查虚拟环境是否存在
if not exist "%VENV_PATH%" (
    echo 错误: 虚拟环境不存在于 %VENV_PATH%
    pause
    exit /b 1
)

echo 正在启动后端服务...
echo 虚拟环境: %VENV_PATH%
echo.

:: 激活虚拟环境并启动后端
cd /d "%PROJECT_ROOT%"
call "%VENV_PATH%\Scripts\activate.bat"

echo 虚拟环境已激活
echo 启动命令: python -m app.main
echo.

:: 启动后端服务
python -m app.main

pause
