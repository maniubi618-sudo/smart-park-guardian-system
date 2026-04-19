@echo off
chcp 65001 >nul

:: 园区智能安防系统 - 简易启动脚本
:: 功能：启动所有服务

set "ROOT=%~dp0"
set "FRONTEND=%ROOT%park-safety-frontend"

echo ===========================
echo 园区智能安防系统
echo ===========================
echo.

:: 启动HTTP后端
echo [1/3] 启动后端服务 (HTTP)
start "后端 HTTP" cmd /k "cd /d %ROOT% && python -m app.main"

:: 等待
echo 等待2秒...
timeout /t 2 /nobreak >nul

:: 启动HTTPS后端
echo [2/3] 启动后端服务 (HTTPS)
start "后端 HTTPS" cmd /k "cd /d %ROOT% && python -m app.main_https"

:: 等待
echo 等待3秒...
timeout /t 3 /nobreak >nul

:: 启动前端
echo [3/3] 启动前端服务
start "前端" cmd /k "cd /d %FRONTEND% && npm run dev"

:: 等待
echo 等待5秒...
timeout /t 5 /nobreak >nul

echo.
echo ===========================
echo 服务启动成功！
echo ===========================
echo.
echo 后端 HTTP: http://localhost:8089
echo 后端 HTTPS: https://localhost:8443
echo 前端: http://localhost:5173
echo.
echo 手机摄像头: https://[本机IP]:8443/phone-camera
echo.
echo 关闭窗口停止服务
echo.

pause
