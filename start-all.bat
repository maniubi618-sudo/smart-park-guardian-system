@echo off
chcp 65001 >nul

:: 园区智能安防系统 - 一键启动脚本
:: 功能：启动前后端服务，包括手机摄像头功能
:: 使用方法: 双击运行 start-all.bat

set "PROJECT_ROOT=%~dp0"
set "FRONTEND_PATH=%PROJECT_ROOT%park-safety-frontend"

echo ========================================
echo   园区智能安防系统 - 一键启动脚本
echo ========================================
echo.
echo 正在启动服务...
echo.

:: 启动HTTP后端
echo [1/3] 启动后端服务 (HTTP)...
start "后端服务 (HTTP)" cmd /k "cd /d %PROJECT_ROOT% && call venv\Scripts\activate.bat && echo 启动 HTTP 后端 (端口: 8089) && python -m app.main"

:: 等待后端启动
echo 等待后端服务启动 (2秒)...
timeout /t 2 /nobreak >nul

:: 启动HTTPS后端（用于手机摄像头）
echo [2/3] 启动后端服务 (HTTPS)...
start "后端服务 (HTTPS)" cmd /k "cd /d %PROJECT_ROOT% && call venv\Scripts\activate.bat && echo 启动 HTTPS 后端 (端口: 8443) && python -m app.main_https"

:: 等待HTTPS后端启动
echo 等待 HTTPS 后端服务启动 (3秒)...
timeout /t 3 /nobreak >nul

:: 启动前端服务
echo [3/3] 启动前端服务...
start "前端服务" cmd /k "cd /d %FRONTEND_PATH% && echo 启动前端服务 (端口: 3000) && npm run dev"

:: 等待前端启动
echo 等待前端服务启动 (5秒)...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   所有服务已启动成功!
echo ========================================
echo.
echo 后端服务 (HTTP): http://localhost:8089
echo 后端服务 (HTTPS): https://localhost:8443
echo 前端服务: https://localhost:3000
echo.
echo API文档 (HTTP): http://localhost:8089/docs
echo API文档 (HTTPS): https://localhost:8443/docs
echo 手机摄像头页面: https://[本机IP]:8443/phone-camera
echo.
echo ⚠️  首次访问HTTPS需信任自签名证书
echo    浏览器提示"不安全" → 点击"继续前往"
echo.
echo 关闭弹出的命令窗口即可停止服务
echo.
echo 使用步骤:
echo 1. 打开前端页面: https://localhost:3000
echo 2. 登录系统
echo 3. 进入"摄像头管理"页面
echo 4. 点击"手机摄像头"按钮
echo 5. 手机访问显示的HTTPS地址
echo 6. 信任证书并允许摄像头权限
echo 7. 切换到"手机推流观看"标签页查看画面
echo.

pause
