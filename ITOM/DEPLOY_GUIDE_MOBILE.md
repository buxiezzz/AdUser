# ITOM 平台移动端/H5 部署与访问指南

> [!NOTE]
> 本项目的“移动端”并不是一个独立的 App，而是**嵌入在前端 Vue 3 项目中的 H5 模块**。
> 它的路由前缀是 `/mobile`。部署移动端即部署整个前端项目。

---

## 选项一：本地调试与局域网访问 (最快速)

如果您只是想在本地运行，并用手机（或微信扫码）进行测试，请按照以下步骤操作：

### 1. 启动服务
在项目根目录下，确保已经拉取了依赖并使用一键启动脚本：
```bash
./start.sh
```
这会利用 Vite 的开发服务器启动前端（默认端口 `15173`）和 Uvicorn 启动后端（默认端口 `18000`）。

### 2. 手机访问方式
要在手机上访问，**手机和电脑必须连接同一个 Wi-Fi (处于同一局域网)**。

1.  **获取电脑 IP**：
    在 Mac 终端运行：
    ```bash
    ifconfig | grep "inet " | grep -v 127.0.0.1
    ```
    假设您的电脑 IP 是 `192.168.1.100`。

2.  **手机浏览器访问**：
    在手机浏览器中输入：
    `http://192.168.1.100:15173/mobile`
    *(注意：一定要加 `/mobile` 才能进入移动端界面)*

3.  **扫码功能**：
    如果电脑前端生成了带有特定 URL 的二维码（例如资产详情页 `/mobile/asset/:token`），手机直接扫描该二维码即可。

---

## 选项二：生产环境正式部署 (推荐 Nginx)

如果您需要将项目部署到 Linux 服务器给更多人使用，请使用**打包发布 + Nginx 托管**的方式。

### 1. 打包前端
由于移动端使用 H5 形式，需要对前端 Vue 项目进行静态资源构建：
```bash
cd ITOM/frontend
npm run build
```
构建完成后，会在 `ITOM/frontend` 目录下生成一个 **`dist`** 文件夹。这个文件夹就是您需要部署的静态文件。

### 2. 部署到 Nginx
以下是针对单页应用（SPA）的标准 Nginx 配置文件示例。

> [!IMPORTANT]
> 由于 Vue Router 使用了 `History 模式`，刷新移动端页面（如 `/mobile/index`）时可能会导致 404。必须在 Nginx 中配置 **`try_files`** 将请求重定向到 `index.html`。

#### Nginx 核心配置模板 (`nginx.conf`)：

```nginx
server {
    listen       80;
    server_name  your_domain_or_ip;  # 替换为您的域名或服务器IP

    # 前端静态文件托管 (包含 PC 端和移动端)
    location / {
        root   /path/to/your/ITOM/frontend/dist; # 替换为实际 dist 目录的绝对路径
        index  index.html index.htm;
        
        # 🌟 关键配置：防止刷新页面 404
        try_files $uri $uri/ /index.html;
    }

    # 后端接口反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:18000/; # 替换为您的后端 FastAPI 运行地址
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 3. 配置完成后的访问
*   **管理后台（PC）**：访问 `http://your_domain_or_ip/`
*   **移动端（H5）**：访问 `http://your_domain_or_ip/mobile`

---

## 常见问题 (FAQ)

1.  **手机访问提示“连接超时”？**
    *   检查手机和电脑是否在同一个 Wi-Fi。
    *   检查电脑的防火墙设置，确保开放了对应的端口（如 `15173`）。

2.  **扫码之后页面报错 404？**
    *   如果是开发环境，确认二维码包含的 IP 能够被手机访问。
    *   如果是 Nginx 环境，确认配置了 `try_files` 规则。
