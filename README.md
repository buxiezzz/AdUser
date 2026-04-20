# AdUser
Ran command: `./sync_to_server.sh`
Edited manifest.json
Edited manifest.json

这是一个非常好的职业习惯。在准备迁移到新 Debian 服务器前，我为您做了最后的端到端（End-to-End）全量审计。

### 核心审计结果：
您可以非常有信心：该项目目前已经实现了**“开箱即用”**的容器化集成感。您只需拷贝目录，运行 `docker compose up -d` 即可。

以下是针对您 Debian 部署场景的 4 个关键确认点：

#### 1. 依赖库全集成 (Requirements Check)
*   **状态**：**已补齐**。
*   **细节**：我已经手动补足了 `pytz`（时区库）、`pandas` / `openpyxl`（报废审计导出）等所有新增逻辑所需的依赖。
*   **部署表现**：Docker 在编译 `itom-backend` 镜像时会自动从 PyPI 下载并安装这些包，不需要在 Debian 宿主机上安装任何 Python 或库。

#### 2. 时区与物理环境对齐 (Timezone & Environment)
*   **状态**：**已深度纠偏**。
*   **细节**：
    *   `docker-compose.yml` 中加入了 `- /etc/localtime:/etc/localtime:ro`。
    *   模型层移除了会导致时差的 `func.now()`，改为 Python 强制生成的北京时间戳。
*   **部署表现**：在全新 Debian 机器上，只要宿主机时间是准的，系统内的时间记录、审计日志就会精准对齐中国标准时间。

#### 3. 业务规则硬锁定 (Business Rules)
*   **状态**：**已内建校验**。
*   **细节**：关于“在用必须有人员”的拦截逻辑已写死在后端代码中。
*   **部署表现**：即使是在新环境、新数据库里，任何人试图违规操作，系统都会在 API 层面直接拦截，不需要额外的配置。

#### 4. 前端与网络配置 (Network & API)
*   **状态**：**已完成反向代理配置**。
*   **细节**：`frontend` 的 Nginx 配置已经集成了 `/api/` 的反向代理。
*   **部署建议**：
    *   **移动端注意**：在新服务器部署后，请检查 `mobile_app/src/utils/` 下的 API 地址（如果之前写死的是 `10.20.108.159`），需要根据新 Debian 服务器的 IP 进行一次性修改并重新打包 APK/H5。
    *   **宿主机防火墙**：新 Debian 默认可能开启了 `ufw` 或 `iptables`，请务必放行 `8081`（前端）和 `9000`（后端 API）端口。

---

### 给您的部署清单 (Deployment Checklist)：

如果以后要在新服务器部署，只需以下三步：
1.  **拷贝**：将整个 `ITOM` 目录（包含 `backend`, `frontend`, `docker-compose.yml`）拷贝到新服务器。
2.  **权限**：运行一次 `chmod +x sync_to_server.sh`（虽然新环境直接用 docker-compose 更好）。
3.  **启动**：
    ```bash
    docker compose up -d --build
    ```

**总结**：环境已经高度闭环，所有的脏活、累活（如库安装、时区配置、业务校验）都已经封装进 Docker 镜像和代码逻辑中了。您可以放心“乾坤大挪移”！