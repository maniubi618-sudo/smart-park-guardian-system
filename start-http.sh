#!/bin/bash
# ========================================
#   园区智能安防系统 - HTTP模式启动脚本
#   使用HTTP而非HTTPS，避免浏览器证书问题
# ========================================

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_PATH="$PROJECT_ROOT/park-safety-frontend"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

FRONTEND_PORT="${FRONTEND_PORT:-3003}"
BACKEND_HTTP_PORT="${BACKEND_HTTP_PORT:-8089}"
BACKEND_HTTPS_PORT="${BACKEND_HTTPS_PORT:-8443}"

echo "========================================"
echo "  园区智能安防系统 - HTTP启动脚本"
echo "========================================"
echo ""

# ---- 清理已存在的服务进程 ----
echo -e "${BLUE}[清理]${NC} 检查并停止已存在的服务..."

for pid in $(lsof -i :$BACKEND_HTTP_PORT -t 2>/dev/null); do
    kill -9 $pid 2>/dev/null
    echo -e "${YELLOW}  已停止占用端口 $BACKEND_HTTP_PORT 的进程 (PID: $pid)${NC}"
done

for pid in $(lsof -i :$BACKEND_HTTPS_PORT -t 2>/dev/null); do
    kill -9 $pid 2>/dev/null
    echo -e "${YELLOW}  已停止占用端口 $BACKEND_HTTPS_PORT 的进程 (PID: $pid)${NC}"
done

for pid in $(lsof -i :$FRONTEND_PORT -t 2>/dev/null); do
    kill -9 $pid 2>/dev/null
    echo -e "${YELLOW}  已停止占用端口 $FRONTEND_PORT 的进程 (PID: $pid)${NC}"
done

for pid in $(ps aux | grep "vite" | grep -v grep | awk '{print $2}'); do
    kill -9 $pid 2>/dev/null
    echo -e "${YELLOW}  已停止 vite 进程 (PID: $pid)${NC}"
done

sleep 1
echo -e "${GREEN}  OK${NC} 清理完成"
echo ""

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
echo -e "${BLUE}[1/2]${NC} 启动后端 HTTP 服务 (端口: $BACKEND_HTTP_PORT)..."
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

# ---- 启动前端 HTTP (端口 3003) ----
echo -e "${BLUE}[2/2]${NC} 启动前端服务 (HTTP模式，端口: $FRONTEND_PORT)..."
cd "$FRONTEND_PATH"
nohup npx vite --host 0.0.0.0 --port "$FRONTEND_PORT" --strictPort -c vite.config.http.js > /tmp/smart-park-frontend.log 2>&1 &
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
echo -e "  API 文档:     ${BLUE}http://localhost:$BACKEND_HTTP_PORT/docs${NC}"
echo -e "  前端页面:     ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
echo ""
echo -e "  ${YELLOW}提示: 使用HTTP模式，无需处理HTTPS证书问题${NC}"
echo ""
echo -e "  停止服务:     ${YELLOW}./stop.sh${NC}"
echo ""
