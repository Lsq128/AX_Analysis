# AX_Analysis 生产部署指南

> 目标：Web、API、Worker、Redis、Postgres、报告存储在同一拓扑下协同工作，避免「分析完成但报告 404」。

**相关文档：** [getting-started.md](./getting-started.md)（本地） · [architecture.md](./architecture.md)（拓扑） · [api-reference.md](./api-reference.md)

---

## 1. 架构拓扑

```
                         ┌─────────────┐
    用户 ───────────────►│  Nginx/Caddy │  HTTPS
                         └──────┬──────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
       ┌──────▼──────┐   ┌──────▼──────┐         │
       │  apps/web   │   │  ax-api     │         │
       │  Next.js    │   │  FastAPI    │         │
       │  :3000      │   │  :8000      │         │
       └─────────────┘   └──────┬──────┘         │
                                  │                │
                    ┌─────────────┼────────────┐   │
                    │             │            │   │
             ┌──────▼──────┐ ┌────▼────┐ ┌─────▼─────┐
             │  Postgres   │ │ Redis   │ │ ax-worker │ ×N
             │  用户/配额   │ │ 队列/SSE│ │ 调引擎     │
             └─────────────┘ └─────────┘ └─────┬─────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │ S3 / OSS / local+NFS │
                                    │ AX_DATA_ROOT 用户数据 │
                                    └─────────────────────┘
```

**必须同时运行：** API + Worker + Redis。  
**生产推荐：** Postgres + S3 兼容 OSS。

---

## 2. Docker 部署

### 2.0 Docker 一键演示（dev/demo）

```bash
cp .env.example .env   # 至少一个 LLM Key
./scripts/up.sh        # postgres + redis + api + worker + web
```

详见设计规格 `docs/superpowers/specs/2026-08-03-docker-one-click-design.md`。  
**生产请勿直接依赖该路径的默认鉴权（dev header / dev login）。**

当前也可只起基础设施容器（§2.1）；API / Worker / Web 可在宿主机运行（§2.3）。

### 2.1 仅基础设施（推荐起步）

```bash
cd AX_Analysis
docker compose up -d postgres redis
```

| 服务 | 镜像 | 端口 | 默认账号 |
|------|------|------|----------|
| postgres | postgres:16-alpine | 5432 | `ax` / `ax` / DB `ax_analysis` |
| redis | redis:7-alpine | 6379 | 无密码 |

`.env`：

```env
DATABASE_URL=postgresql://ax:ax@localhost:5432/ax_analysis
REDIS_URL=redis://localhost:6379/0
```

数据卷：`ax_pg_data`、`ax_redis_data`（持久化）。

### 2.2 含 MinIO（S3 本地模拟）

```bash
docker compose --profile storage up -d minio
```

| 服务 | 端口 | 账号 |
|------|------|------|
| MinIO API | 9000 | `axminio` / `axminio123` |
| MinIO Console | 9001 | 同上 |

创建 bucket `ax-reports` 后配置：

```env
AX_REPORT_STORAGE=s3
AX_S3_BUCKET=ax-reports
AX_S3_REGION=us-east-1
AX_S3_ENDPOINT=http://localhost:9000
AX_S3_ACCESS_KEY=axminio
AX_S3_SECRET_KEY=axminio123
AX_REPORT_SIGNED_URL_TTL=3600
```

生产替换为阿里云 OSS / AWS S3 等，**Bucket 私有**，仅 signed URL 对外。

### 2.3 应用进程（宿主机）

```bash
cd AX_Analysis
python -m venv .venv && source .venv/bin/activate
pip install -e ".[cn,dev,storage]"
cp .env.example .env   # 编辑生产值

# systemd / supervisor / tmux
ax-worker          # 可 N 实例
ax-api             # uvicorn 0.0.0.0:8000

cd apps/web
npm ci && npm run build
API_PROXY_URL=http://127.0.0.1:8000 npm start
```

Worker 启动前 **工作目录须在 `AX_Analysis/`**，以便 `load_ax_env()` 加载 `.env`。

### 2.4 容器化 API / Worker（可选参考）

演示栈已内置 Dockerfile，由 `docker-compose.yml` 引用：

| 文件 | 用途 |
|------|------|
| `Dockerfile.python` | API、Worker（`api` / `worker` 服务） |
| `Dockerfile.web` | Next.js Web（`web` 服务） |

**一键启动**见 **§2.0**（`./scripts/up.sh` → Postgres + Redis + API + Worker + Web）。

以下为 **生产环境自定义镜像** 时的可选参考（演示栈无需自建）：

```dockerfile
# 示例 Dockerfile.api（生产定制）
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e ".[cn,storage]"
ENV AX_JOB_STORE=redis
CMD ["ax-api"]
```

注意：

- 同一 `.env` 通过 `--env-file` 或 K8s Secret 注入
- Worker 需 LLM Key、可选 AKShare；**不要** 把 Key 打进镜像层
- Web 可用 Node 镜像单独构建 `apps/web`

---

## 3. 环境变量清单

复制 `AX_Analysis/.env.example` → `.env`。

### 3.1 必填（生产）

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | Postgres |
| `REDIS_URL` | 任务队列 + SSE |
| `JWT_SECRET` | **≥32 字节随机串** |
| `DEEPSEEK_API_KEY` 等 | 至少一个 LLM Key（Worker） |

### 3.2 鉴权（生产）

```env
AX_AUTH_DEV_MODE=false
AX_AUTH_ALLOW_HEADER=false
AX_AUTH_DEV_LOGIN=false
AX_WEB_URL=https://app.example.com
AX_OAUTH_PROVIDERS=github
OAUTH_GITHUB_CLIENT_ID=...
OAUTH_GITHUB_CLIENT_SECRET=...
AX_OAUTH_REDIRECT_URI=https://app.example.com/api/v1/auth/oauth/github/callback
```

Web：

```env
# apps/web/.env.production
API_PROXY_URL=http://127.0.0.1:8000
NEXT_PUBLIC_AUTH_ALLOW_HEADER=false
```

### 3.3 数据与路径

| 变量 | 说明 |
|------|------|
| `FRED_API_KEY` | News 宏观（推荐） |
| `AX_DATA_ROOT` | 用户 memory/cache/logs 根目录，如 `/data/ax` |
| `AX_DEFAULT_PLAN_ID` | 新用户套餐：free / standard / pro |

### 3.4 报告与 Admin

| 变量 | 说明 |
|------|------|
| `AX_REPORT_STORAGE` | `local` 或 `s3` |
| `AX_S3_*` | S3/OSS 连接 |
| `AX_ADMIN_USER_IDS` | 管理员 external_id，逗号分隔 |
| `AX_ADMIN_API_KEY` | 可选服务端 Admin Key |
| `AX_API_RATE_LIMIT_RPM` | 默认 120 |

---

## 4. 反向代理

示例 Nginx（Web + API 同域）：

```nginx
server {
    listen 443 ssl;
    server_name app.example.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # 若 Web rewrite 已代理 /api，可不单独暴露 8000
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_buffering off;   # SSE
    }
}
```

OAuth callback URL 必须与 GitHub/OIDC 应用配置及 `AX_OAUTH_REDIRECT_URI` **完全一致**。

---

## 5. systemd 示例

`/etc/systemd/system/ax-worker.service`：

```ini
[Unit]
Description=AX Analysis Worker
After=network.target docker.service

[Service]
Type=simple
User=ax
WorkingDirectory=/opt/AX_Analysis
EnvironmentFile=/opt/AX_Analysis/.env
ExecStart=/opt/AX_Analysis/.venv/bin/ax-worker
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

`ax-api.service` 同理，`ExecStart=.../ax-api`。

---

## 6. 报告存储策略

| 模式 | 适用 | 注意 |
|------|------|------|
| `local` | 单机 dev | API 与 Worker **同机** 或 NFS |
| `s3` | 生产 | Worker 上传 → DB 存 key → API signed URL / 直读 |

流程：Worker 完成 → `upload_report_tree` → `report_path=reports/{user}/{job}`。

---

## 7. 多 Worker 与队列

- Redis `BLPOP`：多 Worker 竞争任务，无 sticky session
- SSE：`ax:events:{job_id}` Pub/Sub
- 勿对同一 job 重复入队（retry API 已校验状态）

---

## 8. 数据库迁移

API 启动时 `init_db()` 自动建表。  
**已有库**若缺列（如 `user_quotas.plan_id`）需手动：

```sql
ALTER TABLE user_quotas ADD COLUMN IF NOT EXISTS plan_id VARCHAR(32) DEFAULT 'standard';
```

---

## 9. 安全检查清单

- [ ] `JWT_SECRET` 已更换（≥32 字节）
- [ ] `AX_AUTH_ALLOW_HEADER=false`
- [ ] `AX_AUTH_DEV_LOGIN=false`
- [ ] LLM / 数据 Key 仅在 Worker
- [ ] Admin 已配置 `AX_ADMIN_USER_IDS` 或 API Key
- [ ] Postgres / Redis 不对公网暴露
- [ ] S3 Bucket 私有 + signed URL TTL 合理
- [ ] HTTPS 全站
- [ ] `AX_API_RATE_LIMIT_RPM` 按流量调整

---

## 10. 健康检查与验收

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

**端到端验收：**

1. OAuth / 登录成功
2. 发起分析 → Worker 日志 `Processing job`
3. 分析室 SSE 有进度 → completed
4. 报告库可见 → 章节可读 → zip 导出成功
5. 配额点数减少（Postgres 模式）
6. Admin 可查看用户列表

---

## 11. 常见问题

| 现象 | 原因 | 处理 |
|------|------|------|
| 永远 queued | Worker 未跑 / Redis 不通 | 启动 worker，查 `REDIS_URL` |
| 报告 404 | local 存储跨机 | 改 S3 或 NFS |
| 配额不扣 | 无 `DATABASE_URL` | 配置 Postgres |
| 重启后任务消失 | memory store | Redis + Postgres |
| OAuth 失败 | redirect URI 不匹配 | 对齐三方应用与 env |
| 429 频繁 | 限流过严 | 调 `AX_API_RATE_LIMIT_RPM` |
| A 股无数据 | 未装 cn  extra | `pip install -e ".[cn]"` |

---

## 12. CI

仓库根目录 `.github/workflows/ax-analysis-ci.yml`：

- `pytest`（`AX_Analysis/tests`）
- `apps/web` `npm run build`

---

*2026-07-29 · 含 Docker 基础设施与生产清单*
