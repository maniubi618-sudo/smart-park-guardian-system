#!/bin/bash
# ========================================
#   园区智能安防系统 - 停止脚本
# ========================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}正在停止所有服务...${NC}"
echo ""

stopped_any=false

stop_by_pidfile() {
    local pidfile=$1
    local name=$2
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile" 2>/dev/null || true)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            sleep 0.3
            kill -9 "$PID" 2>/dev/null || true
            echo -e "${GREEN}  OK${NC} $name 已停止 (PID: $PID)"
            stopped_any=true
        fi
        rm -f "$pidfile"
    fi
}

stop_by_pidfile /tmp/smart-park-backend.pid        "后端 HTTP"
stop_by_pidfile /tmp/smart-park-backend-https.pid  "后端 HTTPS"
stop_by_pidfile /tmp/smart-park-frontend.pid       "前端"

# 兜底：按端口强制释放
for port in 5175 8089 8443 3003; do
    if lsof -ti:"$port" >/dev/null 2>&1; then
        lsof -ti:"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
        echo -e "${GREEN}  OK${NC} 端口 $port 已释放"
        stopped_any=true
    fi
done

# 清理残留进程
ps aux | grep -E "vite|app\.main" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

echo ""
if $stopped_any; then
    echo -e "${GREEN}所有服务已停止${NC}"
else
    echo -e "${YELLOW}没有运行中的服务${NC}"
fi
