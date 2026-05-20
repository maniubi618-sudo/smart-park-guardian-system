@echo off
chcp 65001 >nul

:: Park Safety System - Simple Startup Script
:: Function: Start all services

set "ROOT=%~dp0"
set "FRONTEND=%ROOT%park-safety-frontend"

echo ===========================
echo Park Safety System
echo ===========================
echo.

:: Start HTTP Backend
echo [1/3] Starting Backend (HTTP)
start "Backend HTTP" cmd /k "cd /d %ROOT% && python -m app.main"

:: Wait
echo Waiting 2 seconds...
timeout /t 2 /nobreak >nul

:: Start HTTPS Backend
echo [2/3] Starting Backend (HTTPS)
start "Backend HTTPS" cmd /k "cd /d %ROOT% && python -m app.main_https"

:: Wait
echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

:: Start Frontend
echo [3/3] Starting Frontend
start "Frontend" cmd /k "cd /d %FRONTEND% && npm run dev"

:: Wait
echo Waiting 5 seconds...
timeout /t 5 /nobreak >nul

echo.
echo ===========================
echo Services started successfully!
echo ===========================
echo.
echo Backend HTTP: http://localhost:8089
echo Backend HTTPS: https://localhost:8443
echo Frontend: http://localhost:3000
echo.
echo Phone Camera: https://[YourIP]:8443/phone-camera
echo.
echo Close windows to stop services
echo.

pause
