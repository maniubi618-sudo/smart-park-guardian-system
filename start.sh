#!/bin/bash
# ========================================
#   园区智能安防系统 - macOS 一键启动脚本
# ========================================

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_PATH="$PROJECT_ROOT/park-safety-frontend"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# 可配置的端口号
FRONTEND_PORT="${FRONTEND_PORT:-3003}"
BACKEND_HTTP_PORT="${BACKEND_HTTP_PORT:-8089}"
BACKEND_HTTPS_PORT="${BACKEND_HTTPS_PORT:-8443}"

echo "========================================"
echo "  园区智能安防系统 - 启动脚本"
echo "========================================"
echo ""

# ---- 清理已存在的服务进程 ----
echo -e "${BLUE}[清理]${NC} 检查并停止已存在的服务..."

# 停止占用后端端口的服务
for pid in $(lsof -i :$BACKEND_HTTP_PORT -t 2>/dev/null); do
    kill -9 $pid 2>/dev/null
    echo -e "${YELLOW}  已停止占用端口 $BACKEND_HTTP_PORT 的进程 (PID: $pid)${NC}"
done

for pid in $(lsof -i :$BACKEND_HTTPS_PORT -t 2>/dev/null); do
    kill -9 $pid 2>/dev/null
    echo -e "${YELLOW}  已停止占用端口 $BACKEND_HTTPS_PORT 的进程 (PID: $pid)${NC}"
done

# 停止前端服务（包括可能的自动切换端口）
for pid in $(lsof -i :$FRONTEND_PORT -t 2>/dev/null); do
    kill -9 $pid 2>/dev/null
    echo -e "${YELLOW}  已停止占用端口 $FRONTEND_PORT 的进程 (PID: $pid)${NC}"
done

# 停止其他可能的前端进程
for pid in $(ps aux | grep "vite" | grep -v grep | awk '{print $2}'); do
    kill -9 $pid 2>/dev/null
    echo -e "${YELLOW}  已停止 vite 进程 (PID: $pid)${NC}"
done

sleep 1

echo -e "${GREEN}  OK${NC} 清理完成"
echo ""

MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-}"

# ---- 检查 MySQL ----
echo -e "${BLUE}[检查]${NC} MySQL 服务..."
if [ -n "$MYSQL_ROOT_PASSWORD" ]; then
    MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqladmin ping -u root 2>/dev/null | grep -q "alive"
else
    mysqladmin ping -u root 2>/dev/null | grep -q "alive"
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  OK${NC} MySQL 已运行"
else
    echo -e "${YELLOW}  !! MySQL 未运行，尝试启动...${NC}"
    if [ -z "$MYSQL_ROOT_PASSWORD" ]; then
        echo -e "${YELLOW}  提示: 如需使用 root 密码检查 MySQL，请先导出环境变量 MYSQL_ROOT_PASSWORD${NC}"
    fi
    /usr/local/mysql/support-files/mysql.server start 2>/dev/null || true
    sleep 2
fi

# ---- 检查虚拟环境 ----
echo -e "${BLUE}[检查]${NC} Python 虚拟环境..."
cd "$PROJECT_ROOT"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
if [ -f "$VENV_PYTHON" ]; then
    echo -e "${GREEN}  OK${NC} 虚拟环境: $VENV_PYTHON"
else
    echo -e "${RED}  !! 虚拟环境不存在，请先运行: python3 -m venv venv && ./venv/bin/python -m pip install -r requirements.txt${NC}"
    exit 1
fi

# ---- 启动后端 HTTP (端口 8089) ----
echo ""
echo -e "${BLUE}[1/3]${NC} 启动后端 HTTP 服务 (端口: $BACKEND_HTTP_PORT)..."
nohup "$VENV_PYTHON" -m app.main > /tmp/smart-park-backend.log 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > /tmp/smart-park-backend.pid
sleep 3
if kill -0 "$BACKEND_PID" 2>/dev/null && lsof -i :$BACKEND_HTTP_PORT -t >/dev/null 2>&1; then
    echo -e "${GREEN}  OK${NC} 后端 HTTP 已启动 (PID: $BACKEND_PID)"
else
    echo -e "${RED}  !! 后端 HTTP 启动失败，查看日志: cat /tmp/smart-park-backend.log${NC}"
    exit 1
fi

# ---- 启动后端 HTTPS (端口 8443)，用于手机摄像头 ----
echo -e "${BLUE}[2/3]${NC} 启动后端 HTTPS 服务 (端口: $BACKEND_HTTPS_PORT)..."
nohup bash -c "cd '$PROJECT_ROOT' && '$VENV_PYTHON' -m app.main_https" > /tmp/smart-park-backend-https.log 2>&1 &
HTTPS_PID=$!
echo "$HTTPS_PID" > /tmp/smart-park-backend-https.pid
sleep 3
if kill -0 "$HTTPS_PID" 2>/dev/null && lsof -i :$BACKEND_HTTPS_PORT -t >/dev/null 2>&1; then
    echo -e "${GREEN}  OK${NC} 后端 HTTPS 已启动 (PID: $HTTPS_PID)"
else
    echo -e "${RED}  !! 后端 HTTPS 启动失败，查看日志: cat /tmp/smart-park-backend-https.log${NC}"
fi

# ---- 启动前端 (端口 3003) ----
echo -e "${BLUE}[3/3]${NC} 启动前端服务 (端口: $FRONTEND_PORT)..."
cd "$FRONTEND_PATH"
nohup npx vite --host 0.0.0.0 --port "$FRONTEND_PORT" --strictPort > /tmp/smart-park-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > /tmp/smart-park-frontend.pid
sleep 3
if kill -0 "$FRONTEND_PID" 2>/dev/null && lsof -i :$FRONTEND_PORT -t >/dev/null 2>&1; then
    echo -e "${GREEN}  OK${NC} 前端已启动 (PID: $FRONTEND_PID)"
else
    echo -e "${RED}  !! 前端启动失败，查看日志: cat /tmp/smart-park-frontend.log${NC}"
fi

# ---- 完成 ----
echo ""
echo "========================================"
echo -e "${GREEN}  所有服务已启动成功!${NC}"
echo "========================================"
echo ""
echo -e "  后端 HTTP:    ${BLUE}http://localhost:$BACKEND_HTTP_PORT${NC}"
echo -e "  后端 HTTPS:   ${BLUE}https://localhost:$BACKEND_HTTPS_PORT${NC}"
echo -e "  API 文档:     ${BLUE}http://localhost:$BACKEND_HTTP_PORT/docs${NC}"
echo -e "  前端页面:     ${BLUE}https://localhost:$FRONTEND_PORT${NC}"
echo ""
echo -e "  手机摄像头:   ${BLUE}https://$(./venv/bin/python -c "
import socket
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.connect(('8.8.8.8',80))
print(s.getsockname()[0])
s.close()
" 2>/dev/null):$BACKEND_HTTPS_PORT/phone-camera${NC}"
echo ""
echo -e "  停止服务:     ${YELLOW}./stop.sh${NC}"
echo ""
