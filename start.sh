#!/bin/bash

# 获取项目根目录
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# -----------------------------------------
# 自定义启动端口 (可根据需要自行修改)
# -----------------------------------------
BACKEND_PORT=18000
FRONTEND_PORT=15173

echo "========================================="
echo "   ITOM 平台一键启动脚本 (Mac/Linux)"
echo "========================================="

# 定义清理和停止服务函数
cleanup() {
    echo ""
    echo "正在停止所有服务..."
    
    if [ ! -z "$TAIL_BACKEND_PID" ]; then
        kill $TAIL_BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$TAIL_FRONTEND_PID" ]; then
        kill $TAIL_FRONTEND_PID 2>/dev/null
    fi

    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "已停止后端服务 (PID: $BACKEND_PID)"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "已停止前端服务 (PID: $FRONTEND_PID)"
    fi
    
    # 清理临时日志文件
    rm -f "$ROOT_DIR/backend.log" "$ROOT_DIR/frontend.log"
    echo "所有服务已停止。感谢使用！"
    exit 0
}

# 捕获 Ctrl+C 信号 (SIGINT) 和终止信号 (SIGTERM)
trap cleanup SIGINT SIGTERM

# 1. 启动后端
echo "[1/2] 正在启动后端服务..."
cd "$ROOT_DIR/ITOM/backend" || { echo "找不到后端目录"; exit 1; }

# 自动寻找虚拟环境
VENV_PATH=""
if [ -f "$ROOT_DIR/.venv/bin/activate" ]; then
    VENV_PATH="$ROOT_DIR/.venv/bin/activate"
elif [ -f "$ROOT_DIR/ITOM/backend/venv/bin/activate" ]; then
    VENV_PATH="$ROOT_DIR/ITOM/backend/venv/bin/activate"
fi

if [ ! -z "$VENV_PATH" ]; then
    echo "使用虚拟环境: $VENV_PATH"
    source "$VENV_PATH"
else
    echo "⚠️ 未发现独立的虚拟环境，将尝试使用系统默认 Python 运行..."
fi

if [ -f "requirements.txt" ]; then
    echo "正在检查并自动安装缺失的后端依赖..."
    pip install -r requirements.txt > /dev/null 2>&1
fi

# 尝试释放被占用的后端端口
OLD_BACKEND_PID=$(lsof -ti :$BACKEND_PORT 2>/dev/null)
if [ ! -z "$OLD_BACKEND_PID" ]; then
    echo "检测到后端端口 $BACKEND_PORT 被占用，正在释放(PID: $OLD_BACKEND_PID)..."
    kill -9 $OLD_BACKEND_PID 2>/dev/null
fi

# 启动后端 (指定端口) 并在后台运行
uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "$ROOT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "后端已在后台启动 (PID: $BACKEND_PID)"

# 2. 启动前端
echo "[2/2] 正在启动前端服务..."
cd "$ROOT_DIR/ITOM/frontend" || { echo "找不到前端目录"; exit 1; }

if [ ! -d "node_modules" ]; then
    echo "⚠️ 检测到 node_modules 缺失，尝试自动安装依赖..."
    npm install
fi

# 尝试释放被占用的前端端口
OLD_FRONTEND_PID=$(lsof -ti :$FRONTEND_PORT 2>/dev/null)
if [ ! -z "$OLD_FRONTEND_PID" ]; then
    echo "检测到前端端口 $FRONTEND_PORT 被占用，正在释放(PID: $OLD_FRONTEND_PID)..."
    kill -9 $OLD_FRONTEND_PID 2>/dev/null
fi

# 注入端口变量给 vite.config.ts 读取
export VITE_BACKEND_PORT=$BACKEND_PORT
export VITE_FRONTEND_PORT=$FRONTEND_PORT

# 启动前端并把日志保存
npm run dev > "$ROOT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "前端已在后台启动 (PID: $FRONTEND_PID)"

echo "========================================="
echo "🎉 工作流已在后台运行！"
echo "按 [Ctrl + C] 可一键停止所有服务并退出。"
echo "========================================="

# 稍微等待日志生成
sleep 1

# 输出合并日志
if [ -f "$ROOT_DIR/backend.log" ]; then
    tail -f "$ROOT_DIR/backend.log" | sed -e 's/^/[后端] /' &
    TAIL_BACKEND_PID=$!
fi

if [ -f "$ROOT_DIR/frontend.log" ]; then
    tail -f "$ROOT_DIR/frontend.log" | sed -e 's/^/[前端] /' &
    TAIL_FRONTEND_PID=$!
fi

# 让脚本持续运行，响应 Ctrl+C
wait
