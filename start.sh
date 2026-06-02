#!/bin/bash
# ========================================
#   园区智能安防系统 - HTTPS 模式启动脚本
#   前端 HTTPS:5175 / 后端 HTTP:8089 + HTTPS:8443
#   如需纯 HTTP 模式请使用: ./start-http.sh
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
BACKEND_HTTPS_PORT="${BACKEND_HTTPS_PORT:-8443}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-}"

PID_BACKEND=/tmp/smart-park-backend.pid
PID_BACKEND_HTTPS=/tmp/smart-park-backend-https.pid
PID_FRONTEND=/tmp/smart-park-frontend.pid
LOG_BACKEND=/tmp/smart-park-backend.log
LOG_BACKEND_HTTPS=/tmp/smart-park-backend-https.log
LOG_FRONTEND=/tmp/smart-park-frontend.log

force_free_port() {
    local port=$1
    local max_wait=10
    lsof -ti:"$port" 2>/dev/null | xargs kill 2>/dev/null || true
    sleep 0.5
    lsof -ti:"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
    sleep 0.5
    local waited=0
    while lsof -ti:"$port" >/dev/null 2>&1; do
        [ $waited -ge $max_wait ] && { echo -e "${RED}  !! 端口 $port 超时未释放${NC}"; return 1; }
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
        [ $waited -ge $max_wait ] && return 1
        sleep 1
        waited=$((waited + 1))
    done
    echo -e "${GREEN}  OK${NC} $label 已就绪 (${waited}s)"
    return 0
}

is_alive() { kill -0 "$1" 2>/dev/null; }

cleanup_on_exit() {
    echo ""
    echo -e "${YELLOW}[中断]${NC} 正在清理..."
    for f in "$PID_BACKEND" "$PID_BACKEND_HTTPS" "$PID_FRONTEND"; do
        [ -f "$f" ] && kill "$(cat "$f" 2>/dev/null)" 2>/dev/null; rm -f "$f"
    done
    force_free_port "$FRONTEND_PORT" || true
    force_free_port "$BACKEND_HTTP_PORT" || true
    force_free_port "$BACKEND_HTTPS_PORT" || true
    echo -e "${GREEN}已停止${NC}"
    exit 0
}
trap cleanup_on_exit SIGINT SIGTERM

# ============================================================
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  园区智能安防系统 - HTTPS 启动${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "  前端端口: ${GREEN}$FRONTEND_PORT (HTTPS)${NC}"
echo -e "  后端 HTTP: ${GREEN}$BACKEND_HTTP_PORT${NC}"
echo -e "  后端 HTTPS: ${GREEN}$BACKEND_HTTPS_PORT${NC}"
echo ""

# ---- [1/5] 清理 ----
echo -e "${BLUE}[1/5]${NC} 清理旧进程..."
for pf in "$PID_BACKEND" "$PID_BACKEND_HTTPS" "$PID_FRONTEND"; do
    if [ -f "$pf" ]; then
        pid=$(cat "$pf" 2>/dev/null || true)
        [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
        rm -f "$pf"
    fi
done
force_free_port "$BACKEND_HTTP_PORT"  "后端 HTTP"
force_free_port "$BACKEND_HTTPS_PORT" "后端 HTTPS"
force_free_port "$FRONTEND_PORT"     "前端"
ps aux | grep -E "vite|node.*park-safety|app\.main" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
echo -e "${GREEN}  OK${NC} 清理完成"
echo ""

# ---- [2/5] MySQL ----
echo -e "${BLUE}[2/5]${NC} 检查 MySQL..."
if [ -n "$MYSQL_ROOT_PASSWORD" ]; then
    MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqladmin ping -u root --silent 2>/dev/null && mysql_ok=true || mysql_ok=false
else
    mysqladmin ping -u root --silent 2>/dev/null && mysql_ok=true || mysql_ok=false
fi
if $mysql_ok; then
    echo -e "${GREEN}  OK${NC} MySQL 已运行"
else
    echo -e "${YELLOW}  .. MySQL 未运行，尝试启动...${NC}"
    /usr/local/mysql/support-files/mysql.server start 2>/dev/null || true
    sleep 2
fi

# ---- [3/5] 依赖 ----
echo -e "${BLUE}[3/5]${NC} 检查运行环境..."
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
[ -f "$VENV_PYTHON" ] || { echo -e "${RED}  !! 虚拟环境不存在${NC}"; exit 1; }
echo -e "${GREEN}  OK${NC} Python: $("$VENV_PYTHON" --version 2>&1)"
command -v node &>/dev/null || { echo -e "${RED}  !! 未找到 Node.js${NC}"; exit 1; }
echo -e "${GREEN}  OK${NC} Node.js: $(node --version)"

# SSL 证书
CERT_DIR="$PROJECT_ROOT/app"
if [ ! -f "$CERT_DIR/server.crt" ] || [ ! -f "$CERT_DIR/server.key" ]; then
    echo -e "${YELLOW}  .. 生成自签名 SSL 证书...${NC}"
    mkdir -p "$CERT_DIR"
    openssl req -x509 -newkey rsa:2048 -keyout "$CERT_DIR/server.key" \
        -out "$CERT_DIR/server.crt" -days 365 -nodes \
        -subj "/CN=localhost" 2>/dev/null
    echo -e "${GREEN}  OK${NC} 证书已生成"
fi

[ -d "$FRONTEND_PATH/node_modules" ] || {
    echo -e "${YELLOW}  .. 安装前端依赖...${NC}"
    (cd "$FRONTEND_PATH" && npm install --silent) || { echo -e "${RED}  !! npm install 失败${NC}"; exit 1; }
}
echo -e "${GREEN}  OK${NC} 前端依赖已就绪"
echo ""

# ---- [4/5] 后端 ----
echo -e "${BLUE}[4/5]${NC} 启动后端..."
cd "$PROJECT_ROOT"
nohup "$VENV_PYTHON" -m app.main > "$LOG_BACKEND" 2>&1 &
echo "$!" > "$PID_BACKEND"
wait_for_port "$BACKEND_HTTP_PORT" "后端 HTTP" || { echo -e "${RED}  !! 后端 HTTP 启动超时${NC}"; exit 1; }

nohup bash -c "cd '$PROJECT_ROOT' && '$VENV_PYTHON' -m app.main_https" > "$LOG_BACKEND_HTTPS" 2>&1 &
echo "$!" > "$PID_BACKEND_HTTPS"
wait_for_port "$BACKEND_HTTPS_PORT" "后端 HTTPS" || echo -e "${RED}  !! 后端 HTTPS 启动超时 (非致命)${NC}"

# ---- [5/5] 前端 ----
echo -e "${BLUE}[5/5]${NC} 启动前端 (HTTPS, 0.0.0.0:$FRONTEND_PORT)..."
cd "$FRONTEND_PATH"
nohup npx vite --host 0.0.0.0 --port "$FRONTEND_PORT" --strictPort > "$LOG_FRONTEND" 2>&1 &
echo "$!" > "$PID_FRONTEND"
if ! wait_for_port "$FRONTEND_PORT" "前端"; then
    echo -e "${RED}  !! 前端启动超时${NC}"
    kill "$(cat "$PID_BACKEND")" 2>/dev/null
    exit 1
fi

# ---- 本机 IP ----
LOCAL_IP=$(python3 -c "import socket;s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.settimeout(1);s.connect(('8.8.8.8',80));print(s.getsockname()[0]);s.close()" 2>/dev/null || echo "")

# ---- 完成 ----
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}  ✓ 所有服务已启动${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "  前端页面:     ${BLUE}https://localhost:$FRONTEND_PORT${NC}"
echo -e "  后端 HTTP:    ${BLUE}http://localhost:$BACKEND_HTTP_PORT${NC}"
echo -e "  后端 HTTPS:   ${BLUE}https://localhost:$BACKEND_HTTPS_PORT${NC}"
echo -e "  API 文档:     ${BLUE}http://localhost:$BACKEND_HTTP_PORT/docs${NC}"
echo ""
[ -n "$LOCAL_IP" ] && echo -e "  手机摄像头:   ${BLUE}https://$LOCAL_IP:$BACKEND_HTTPS_PORT/phone-camera${NC}" && echo ""
echo -e "  ${YELLOW}注意: 自签名证书浏览器会提示不安全，需手动信任${NC}"
echo -e "  ${YELLOW}提示: 纯 HTTP 模式请用 ./start-http.sh${NC}"
echo ""
echo -e "  ${YELLOW}日志:${NC}"
echo -e "    后端 HTTP:  tail -f $LOG_BACKEND"
echo -e "    后端 HTTPS: tail -f $LOG_BACKEND_HTTPS"
echo -e "    前端:       tail -f $LOG_FRONTEND"
echo ""
echo -e "  停止服务:     ${YELLOW}./stop.sh${NC}"
echo ""
