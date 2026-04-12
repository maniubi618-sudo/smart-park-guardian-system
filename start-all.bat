@echo off
chcp 65001 >nul

:: 一键启动前后端服务脚本
:: 使用方法: 双击运行 start-all.bat

set "PROJECT_ROOT=d:\新建文件夹\大数据\yolo"
set "FRONTEND_PATH=%PROJECT_ROOT%\park-safety-frontend"
set "VENV_PATH=%PROJECT_ROOT%\venv"

echo ========================================
echo   园区智能安防系统 - 一键启动脚本
echo ========================================
echo.

:: 检查虚拟环境是否存在
if not exist "%VENV_PATH%" (
    echo 错误: 虚拟环境不存在于 %VENV_PATH%
    pause
    exit /b 1
)

:: 启动后端服务
echo [1/2] 正在启动后端服务...
echo       虚拟环境: %VENV_PATH%

start "后端服务" cmd /k "cd /d "%PROJECT_ROOT%" && call "%VENV_PATH%\Scripts\activate.bat" && python -m app.main"

:: 等待后端启动
echo       等待后端服务启动 (3秒)...
timeout /t 3 /nobreak >nul

echo       后端服务已启动
echo.

:: 启动前端服务
echo [2/2] 正在启动前端服务...
echo       路径: %FRONTEND_PATH%

start "前端服务" cmd /k "cd /d "%FRONTEND_PATH%" && npm run dev"

:: 等待前端启动
echo       等待前端服务启动 (5秒)...
timeout /t 5 /nobreak >nul

echo       前端服务已启动
echo.

echo ========================================
echo   所有服务已启动成功!
echo ========================================
echo.
echo 后端地址: http://localhost:8089
echo 前端地址: http://localhost:5173
echo.
echo 关闭弹出的命令窗口即可停止服务
echo.

pause
