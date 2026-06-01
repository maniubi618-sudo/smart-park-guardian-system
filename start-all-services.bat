@echo off
chcp 65001 >nul

:: 园区智能安防系统 - 完整启动脚本
:: 功能：同时启动前端、后端HTTP、后端HTTPS服务
:: 使用方法: 双击运行 start-all-services.bat

set "PROJECT_ROOT=%~dp0"
set "FRONTEND_PATH=%PROJECT_ROOT%park-safety-frontend"

echo ========================================
echo   园区智能安防系统 - 完整启动
echo ========================================
echo.
echo 正在启动所有服务...
echo.

:: 启动后端HTTP服务
echo [1/3] 启动后端HTTP服务 (端口: 8089)...
start "后端HTTP服务" cmd /k "cd /d %PROJECT_ROOT% && echo 启动后端HTTP服务 && python -m app.main"

:: 等待2秒
timeout /t 2 /nobreak >nul

:: 启动后端HTTPS服务
echo [2/3] 启动后端HTTPS服务 (端口: 8443)...
start "后端HTTPS服务" cmd /k "cd /d %PROJECT_ROOT% && echo 启动后端HTTPS服务 && python -m app.main_https"

:: 等待2秒
timeout /t 2 /nobreak >nul

:: 启动前端服务
echo [3/3] 启动前端服务 (端口: 3003)...
start "前端服务" cmd /k "cd /d %FRONTEND_PATH% && echo 启动前端服务 && npx vite --host 0.0.0.0 --port 3003 --strictPort"

:: 等待前端启动
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   所有服务已启动成功!
echo ========================================
echo.
echo 前端服务:        http://localhost:3003
echo 后端HTTP服务:    http://localhost:8089
echo 后端HTTPS服务:   https://localhost:8443
echo.
echo API文档 (HTTP):  http://localhost:8089/docs
echo API文档 (HTTPS): https://localhost:8443/docs
echo.
echo 手机摄像头页面:  https://[本机IP]:8443/phone-camera
echo.
echo 关闭弹出的命令窗口即可停止对应服务
echo.

pause
