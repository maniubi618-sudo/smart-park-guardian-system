@echo off
chcp 65001 >nul

:: 一键启动前端服务脚本
:: 使用方法: 双击运行 start-frontend.bat

set "PROJECT_ROOT=d:\新建文件夹\大数据\yolo"
set "FRONTEND_PATH=%PROJECT_ROOT%\park-safety-frontend"

echo ========================================
echo   园区智能安防系统 - 前端启动脚本
echo ========================================
echo.

:: 检查前端目录是否存在
if not exist "%FRONTEND_PATH%" (
    echo 错误: 前端目录不存在于 %FRONTEND_PATH%
    pause
    exit /b 1
)

echo 正在启动前端服务...
echo 路径: %FRONTEND_PATH%
echo.

:: 切换到前端目录并启动
cd /d "%FRONTEND_PATH%"

echo 启动命令: npm run dev
echo.

:: 启动前端服务
npm run dev

pause
