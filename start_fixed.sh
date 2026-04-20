#!/bin/bash
export PATH="/Users/long/miniconda_itom/envs/itom/bin:$PATH"

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_PORT=18000
FRONTEND_PORT=15173

# 注入环境变量供 Vite 读取
export VITE_BACKEND_PORT=$BACKEND_PORT
export VITE_FRONTEND_PORT=$FRONTEND_PORT

echo "=== 正在启动后端服务 ==="
cd "$ROOT_DIR/ITOM/backend"
pip install -r requirements.txt
# 忽略 alembic 版本冲突，手动安装最新版以支持 3.10
pip install alembic fastapi uvicorn sqlalchemy pydantic python-multipart "python-jose[cryptography]" "passlib[bcrypt]" redis pydantic-settings openpyxl pandas pytz psycopg2-binary ldap3 dnspython

uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "$ROOT_DIR/backend_new.log" 2>&1 &
BACKEND_PID=$!
echo "后端已启动 (PID: $BACKEND_PID)"

echo "=== 正在启动前端服务 ==="
cd "$ROOT_DIR/ITOM/frontend"
npm install
npm run dev -- --port $FRONTEND_PORT > "$ROOT_DIR/frontend_new.log" 2>&1 &
FRONTEND_PID=$!
echo "前端已启动 (PID: $FRONTEND_PID)"

echo "========================================="
echo "🎉 项目已启动！"
echo "后端地址: http://localhost:$BACKEND_PORT"
echo "前端地址: http://localhost:$FRONTEND_PORT"
echo "可通过 tail -f backend_new.log 或 frontend_new.log 查看日志。"
echo "========================================="

# 保持运行
wait
