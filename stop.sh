#!/bin/bash
# ========================================
#   园区智能安防系统 - macOS 停止脚本
# ========================================

GREEN='\033[0;32m'
NC='\033[0m'

echo "正在停止所有服务..."

stop_by_pidfile() {
    local pidfile=$1
    local name=$2
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            echo -e "${GREEN}  OK${NC} $name 已停止 (PID: $PID)"
        fi
        rm -f "$pidfile"
    fi
}

stop_by_pidfile /tmp/smart-park-backend.pid        "后端 HTTP"
stop_by_pidfile /tmp/smart-park-backend-https.pid  "后端 HTTPS"
stop_by_pidfile /tmp/smart-park-frontend.pid       "前端"

# 兜底：按端口杀
for port in 8089 8443 3000; do
    lsof -ti:$port 2>/dev/null | xargs kill 2>/dev/null && echo -e "${GREEN}  OK${NC} 端口 $port 已释放" || true
done

echo ""
echo -e "${GREEN}所有服务已停止${NC}"
