#!/bin/bash
# ========================================
#   园区智能安防系统 - HTTP 模式启动脚本
#   使用纯 HTTP，无需处理 HTTPS 证书问题
#   跨项目联动端口: 前端 5175 / 后端 8089
# ========================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_PATH="$PROJECT_ROOT/park-safety-frontend"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

FRONTEND_PORT="${FRONTEND_PORT:-5175}"
BACKEND_HTTP_PORT="${BACKEND_HTTP_PORT:-8089}"

PID_BACKEND=/tmp/smart-park-backend.pid
PID_FRONTEND=/tmp/smart-park-frontend.pid
LOG_BACKEND=/tmp/smart-park-backend.log
LOG_FRONTEND=/tmp/smart-park-frontend.log

# ============================================================
# 工具函数
# ============================================================

force_free_port() {
    local port=$1
    local max_wait=10
    lsof -ti:"$port" 2>/dev/null | xargs kill 2>/dev/null || true
    sleep 0.5
    lsof -ti:"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
    sleep 0.5
    local waited=0
    while lsof -ti:"$port" >/dev/null 2>&1; do
        if [ $waited -ge $max_wait ]; then
            echo -e "${RED}  !! 端口 $port 超时未释放，请手动检查${NC}"
            return 1
        fi
        sleep 1
        waited=$((waited + 1))
        lsof -ti:"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
    done
    return 0
}

wait_for_port() {
    local port=$1
    local label="${2:-端口 $port}"
    local max_wait=15
    local waited=0
    while ! lsof -ti:"$port" >/dev/null 2>&1; do
        if [ $waited -ge $max_wait ]; then
            return 1
        fi
        sleep 1
        waited=$((waited + 1))
    done
    echo -e "${GREEN}  OK${NC} $label 已就绪 (${waited}s)"
    return 0
}

is_alive() {
    kill -0 "$1" 2>/dev/null
}

cleanup_on_exit() {
    echo ""
    echo -e "${YELLOW}[中断]${NC} 正在清理..."
    for f in "$PID_BACKEND" "$PID_FRONTEND"; do
        [ -f "$f" ] && kill "$(cat "$f" 2>/dev/null)" 2>/dev/null; rm -f "$f"
    done
    force_free_port "$FRONTEND_PORT" || true
    force_free_port "$BACKEND_HTTP_PORT" || true
    echo -e "${GREEN}已停止${NC}"
    exit 0
}
trap cleanup_on_exit SIGINT SIGTERM

# ============================================================
# 启动流程
# ============================================================

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  园区智能安防系统 - HTTP 启动${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "  前端端口: ${GREEN}$FRONTEND_PORT${NC}"
echo -e "  后端端口: ${GREEN}$BACKEND_HTTP_PORT${NC}"
echo ""

# ---- [1/4] 清理旧进程 ----
echo -e "${BLUE}[1/4]${NC} 清理旧进程..."

for pf in "$PID_BACKEND" "$PID_FRONTEND"; do
    if [ -f "$pf" ]; then
        pid=$(cat "$pf" 2>/dev/null || true)
        [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
        rm -f "$pf"
    fi
done

force_free_port "$BACKEND_HTTP_PORT" "后端 HTTP"
force_free_port "$FRONTEND_PORT"  "前端"

ps aux | grep -E "vite|node.*park-safety" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo -e "${GREEN}  OK${NC} 清理完成"
echo ""

# ---- [2/4] 检查依赖 ----
echo -e "${BLUE}[2/4]${NC} 检查运行环境..."

VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}  !! 虚拟环境不存在: $VENV_PYTHON${NC}"
    echo -e "${RED}     请先运行: python3 -m venv venv && ./venv/bin/pip install -r requirements.txt${NC}"
    exit 1
fi
echo -e "${GREEN}  OK${NC} Python: $("$VENV_PYTHON" --version 2>&1)"

command -v node &>/dev/null || { echo -e "${RED}  !! 未找到 Node.js${NC}"; exit 1; }
echo -e "${GREEN}  OK${NC} Node.js: $(node --version)"

if [ ! -d "$FRONTEND_PATH/node_modules" ]; then
    echo -e "${YELLOW}  .. 前端依赖未安装，正在 npm install...${NC}"
    (cd "$FRONTEND_PATH" && npm install --silent) || { echo -e "${RED}  !! npm install 失败${NC}"; exit 1; }
fi
echo -e "${GREEN}  OK${NC} 前端依赖已就绪"
echo ""

# ---- [3/4] 启动后端 HTTP ----
echo -e "${BLUE}[3/4]${NC} 启动后端 HTTP (0.0.0.0:$BACKEND_HTTP_PORT)..."

cd "$PROJECT_ROOT"
nohup "$VENV_PYTHON" -m app.main > "$LOG_BACKEND" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$PID_BACKEND"

if ! wait_for_port "$BACKEND_HTTP_PORT" "后端 HTTP"; then
    echo -e "${RED}  !! 后端启动超时，查看日志: cat $LOG_BACKEND${NC}"
    exit 1
fi

if ! is_alive "$BACKEND_PID"; then
    echo -e "${RED}  !! 后端进程已退出，查看日志: cat $LOG_BACKEND${NC}"
    exit 1
fi

echo -e "${GREEN}  OK${NC} 后端 HTTP 已启动 (PID: $BACKEND_PID)"

# ---- [4/4] 启动前端 ----
echo -e "${BLUE}[4/4]${NC} 启动前端 (HTTP, 0.0.0.0:$FRONTEND_PORT)..."

cd "$FRONTEND_PATH"
nohup npx vite --host 0.0.0.0 --port "$FRONTEND_PORT" --strictPort -c vite.config.http.js > "$LOG_FRONTEND" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$PID_FRONTEND"

if ! wait_for_port "$FRONTEND_PORT" "前端"; then
    echo -e "${RED}  !! 前端启动超时，查看日志: cat $LOG_FRONTEND${NC}"
    kill "$BACKEND_PID" 2>/dev/null || true
    exit 1
fi

if ! is_alive "$FRONTEND_PID"; then
    echo -e "${RED}  !! 前端进程已退出，查看日志: cat $LOG_FRONTEND${NC}"
    exit 1
fi

echo -e "${GREEN}  OK${NC} 前端已启动 (PID: $FRONTEND_PID)"

# ---- 完成 ----
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}  ✓ 所有服务已启动${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "  前端页面:     ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
echo -e "  后端 API:     ${BLUE}http://localhost:$BACKEND_HTTP_PORT${NC}"
echo -e "  API 文档:     ${BLUE}http://localhost:$BACKEND_HTTP_PORT/docs${NC}"
echo ""
echo -e "  ${YELLOW}日志:${NC}"
echo -e "    后端: tail -f $LOG_BACKEND"
echo -e "    前端: tail -f $LOG_FRONTEND"
echo ""
echo -e "  停止服务:     ${YELLOW}./stop.sh${NC}"
echo ""
