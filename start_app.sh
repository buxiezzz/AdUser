#!/bin/bash

# =================================================================
# ITOM 运维平台一键启动脚本
# =================================================================

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/ITOM"

echo "🚀 正在准备启动 ITOM 运维平台..."

# 1. 检查并运行后端
echo "📂 正在配置后端服务 (FastAPI)..."
cd "$PROJECT_ROOT/backend"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 正在创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
echo "pip 正在检查/安装依赖项..."
pip install -r requirements.txt > /dev/null 2>&1

# 启动后端服务到后台
echo "🟢 正在启动后端服务 (Port: 8000)..."
nohup python3 main.py > backend.log 2>&1 &
BACKEND_PID=$!

# 2. 检查并运行前端
echo "📂 正在配置前端服务 (Vue/Vite)..."
cd "$PROJECT_ROOT/frontend"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 正在安装前端依赖模块 (npm install)..."
    npm install > /dev/null 2>&1
fi

# 启动前端服务
echo "🟢 正在启动前端服务..."
echo "----------------------------------------------------"
echo "✅ 系统启动中！"
echo "🔗 后端 API: http://127.0.0.1:8000"
echo "🔗 默认管理员: admin / 密码: admin123"
echo "----------------------------------------------------"

# 运行前端开发服务器
npm run dev
