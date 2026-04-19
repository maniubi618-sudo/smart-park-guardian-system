@echo off
chcp 65001 >nul

:: 园区智能安防系统 - 基础启动脚本
:: 功能：启动基本的前后端服务（不包含HTTPS）
:: 使用方法: 双击运行 start-basic.bat

set "PROJECT_ROOT=%~dp0"
set "FRONTEND_PATH=%PROJECT_ROOT%park-safety-frontend"

echo ========================================
echo   园区智能安防系统 - 基础启动脚本
echo ========================================
echo.
echo 正在启动服务...
echo.

:: 启动后端服务（HTTP）
echo [1/2] 启动后端服务 (HTTP)...
start "后端服务 (HTTP)" cmd /k "cd /d %PROJECT_ROOT% && echo 启动 HTTP 后端 (端口: 8089) && python -m app.main"

:: 等待后端启动
echo 等待后端服务启动 (3秒)...
timeout /t 3 /nobreak >nul

:: 启动前端服务
echo [2/2] 启动前端服务...
start "前端服务" cmd /k "cd /d %FRONTEND_PATH% && echo 启动前端服务 (端口: 5173) && npm run dev"

:: 等待前端启动
echo 等待前端服务启动 (5秒)...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   所有服务已启动成功!
echo ========================================
echo.
echo 后端服务 (HTTP): http://localhost:8089
echo 前端服务: http://localhost:5173
echo.
echo API文档: http://localhost:8089/docs
echo.
echo 关闭弹出的命令窗口即可停止服务
echo.

pause
