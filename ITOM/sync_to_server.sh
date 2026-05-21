#!/bin/bash

# =========================================================
# 一键同步代码并部署到 10.10.102.160 服务器的脚本
# 使用方法：在开发完毕后，在终端执行 ./sync_to_server.sh 即可
# =========================================================

echo "[1/3] 正在本地清理并打包项目核心源码..."
# 将核心代码压成包，自动排除 node_modules 等多余或超大文件
tar --exclude="node_modules" \
    --exclude="dist" \
    --exclude="__pycache__" \
    --exclude=".venv" \
    --exclude="venv" \
    --exclude=".git" \
    --exclude="*.exp" \
    --exclude="backend/core/config.json" \
    --exclude="backend/data" \
    --exclude="*.db" \
    --exclude="*.sqlite3" \
    -czvf itom_pack.tar.gz backend frontend docker-compose.yml > /dev/null

echo "[2/3] 正在推送至 10.10.102.160 服务器..."

# 使用 expect 自动输入服务器密码完成文件传输与应用重启
expect -c '
set password "Zmkhjjg@123"
set timeout -1

# 1. 传输压缩文件
spawn scp -o StrictHostKeyChecking=no itom_pack.tar.gz root@10.10.102.160:/opt/itom/
expect {
    "*assword:*" { send "$password\r"; exp_continue }
    eof
}

# 2. 登录目标服务器、解压代码并指示 docker 强制重建变更的镜像
spawn ssh -o StrictHostKeyChecking=no root@10.10.102.160 "cd /opt/itom && tar -xzvf itom_pack.tar.gz > /dev/null && echo '解压完毕，准备编译容器...' && docker compose up -d --build"
expect {
    "*assword:*" { send "$password\r"; exp_continue }
    eof
}
'

echo ""
echo "[3/3] 部署并同步完成！"
echo "本地残余安装包清理..."
rm itom_pack.tar.gz
echo "您可以直接访问 http://10.10.102.160/ 查看最新修改的效果了。"
