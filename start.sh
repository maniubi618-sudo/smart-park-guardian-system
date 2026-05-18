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

echo "========================================"
echo "  园区智能安防系统 - 启动脚本"
echo "========================================"
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
echo -e "${BLUE}[1/3]${NC} 启动后端 HTTP 服务 (端口: 8089)..."
nohup "$VENV_PYTHON" -m app.main > /tmp/smart-park-backend.log 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > /tmp/smart-park-backend.pid
sleep 2
if kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo -e "${GREEN}  OK${NC} 后端 HTTP 已启动 (PID: $BACKEND_PID)"
else
    echo -e "${RED}  !! 后端 HTTP 启动失败，查看日志: cat /tmp/smart-park-backend.log${NC}"
    exit 1
fi

# ---- 启动后端 HTTPS (端口 8443)，用于手机摄像头 ----
echo -e "${BLUE}[2/3]${NC} 启动后端 HTTPS 服务 (端口: 8443)..."
nohup bash -c "cd '$PROJECT_ROOT' && '$VENV_PYTHON' -m app.main_https" > /tmp/smart-park-backend-https.log 2>&1 &
HTTPS_PID=$!
echo "$HTTPS_PID" > /tmp/smart-park-backend-https.pid
sleep 2
if kill -0 "$HTTPS_PID" 2>/dev/null; then
    echo -e "${GREEN}  OK${NC} 后端 HTTPS 已启动 (PID: $HTTPS_PID)"
else
    echo -e "${RED}  !! 后端 HTTPS 启动失败，查看日志: cat /tmp/smart-park-backend-https.log${NC}"
fi

# ---- 启动前端 (端口 5173) ----
echo -e "${BLUE}[3/3]${NC} 启动前端服务 (端口: 5173)..."
cd "$FRONTEND_PATH"
nohup npm run dev > /tmp/smart-park-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > /tmp/smart-park-frontend.pid
sleep 3
if kill -0 "$FRONTEND_PID" 2>/dev/null; then
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
echo -e "  后端 HTTP:    ${BLUE}http://localhost:8089${NC}"
echo -e "  后端 HTTPS:   ${BLUE}https://localhost:8443${NC}"
echo -e "  API 文档:     ${BLUE}http://localhost:8089/docs${NC}"
echo -e "  前端页面:     ${BLUE}https://localhost:5173${NC}"
echo ""
echo -e "  手机摄像头:   ${BLUE}https://$(./venv/bin/python -c "
import socket
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.connect(('8.8.8.8',80))
print(s.getsockname()[0])
s.close()
" 2>/dev/null):8443/phone-camera${NC}"
echo ""
echo -e "  停止服务:     ${YELLOW}./stop.sh${NC}"
echo ""
