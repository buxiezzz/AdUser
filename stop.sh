#!/bin/bash

# 获取项目根目录
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

BACKEND_PORT=18000
FRONTEND_PORT=15173

echo "========================================="
echo "   ITOM 平台一键停止脚本"
echo "========================================="

# 查找并杀掉端口占用
stop_port() {
    local port=$1
    local name=$2
    # 使用 lsof 查找端口对应的 PID
    local pid=$(lsof -ti :$port 2>/dev/null)
    
    if [ ! -z "$pid" ]; then
        echo "正在停止 $name (端口: $port, PID: $pid)..."
        kill -9 $pid 2>/dev/null
        echo "✅ $name 已停止。"
    else
        echo "ℹ️ $name 暂未运行或已关闭 (端口: $port)"
    fi
}

# 1. 停止后端
stop_port $BACKEND_PORT "后端服务"

# 2. 停止前端
stop_port $FRONTEND_PORT "前端服务"

# 3. 清理可能残留的日志文件
if [ -f "$ROOT_DIR/backend.log" ]; then
    rm -f "$ROOT_DIR/backend.log"
fi
if [ -f "$ROOT_DIR/frontend.log" ]; then
    rm -f "$ROOT_DIR/frontend.log"
fi

echo "========================================="
echo "🎉 所有服务已清理完毕！"
echo "========================================="
