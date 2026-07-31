# 本地开发指南

> 从零在 macOS / Linux 上跑通 AX_Analysis 全栈：**Postgres + Redis + API + Worker + Web**。

---

## 1. 前置条件

| 工具 | 版本建议 | 用途 |
|------|----------|------|
| Python | 3.10+（推荐 3.11–3.14） | API、Worker、引擎 |
| Node.js | 20+ | Web 前端 |
| Docker | 最新 | Postgres、Redis（可选 MinIO） |
| Git | — | 克隆仓库 |

至少配置 **一个 LLM API Key**（三选一）：

- `DEEPSEEK_API_KEY`
- `DASHSCOPE_CN_API_KEY`
- `MOONSHOT_API_KEY`

A 股数据推荐额外安装 CN 扩展：`pip install -e ".[cn,dev]"`

---

## 2. 安装

```bash
cd AX_Analysis

# Python 虚拟环境
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 安装（含 API、Worker、测试、A 股 AKShare）
pip install -e ".[cn,dev]"

# 环境变量模板
cp .env.example .env
# 编辑 .env：至少填一个 LLM Key；DATABASE_URL / REDIS_URL 见下节
```

验证 CLI 入口：

```bash
ax-api --help    # 或 .venv/bin/ax-api
ax-worker --help
```

---

## 3. 启动基础设施（Docker）

```bash
cd AX_Analysis
docker compose up -d postgres redis
```

默认连接串（与 `docker-compose.yml` 一致）：

```bash
export DATABASE_URL=postgresql://ax:ax@localhost:5432/ax_analysis
export REDIS_URL=redis://localhost:6379/0
```

检查：

```bash
docker compose ps
# postgres 应 healthy
redis-cli ping   # PONG
```

### 可选：MinIO（S3 兼容，测报告 OSS）

```bash
docker compose --profile storage up -d minio
# Console: http://localhost:9001  用户 axminio / axminio123
```

`.env` 中配置：

```env
AX_REPORT_STORAGE=s3
AX_S3_BUCKET=ax-reports
AX_S3_ENDPOINT=http://localhost:9000
AX_S3_ACCESS_KEY=axminio
AX_S3_SECRET_KEY=axminio123
```

---

## 4. 启动应用（三个终端）

**终端 1 — Worker**

```bash
cd AX_Analysis
source .venv/bin/activate
export DATABASE_URL=postgresql://ax:ax@localhost:5432/ax_analysis
export REDIS_URL=redis://localhost:6379/0
ax-worker
```

**终端 2 — API**

```bash
cd AX_Analysis
source .venv/bin/activate
export DATABASE_URL=postgresql://ax:ax@localhost:5432/ax_analysis
export REDIS_URL=redis://localhost:6379/0
ax-api
# 默认 http://0.0.0.0:8000
```

**终端 3 — Web**

```bash
cd AX_Analysis/apps/web
cp .env.local.example .env.local
npm install
npm run dev
# 默认 http://localhost:3000
```

或使用辅助脚本（仅 Web 或打印提示）：

```bash
./scripts/dev_stack.sh        # 打印启动说明并拉起 docker
./scripts/dev_stack.sh web    # 仅启动 Next dev
```

---

## 5. 内存模式（无 Docker / 无 Postgres）

适合快速调试 API 逻辑，**重启后任务与配额不持久**：

```bash
export AX_JOB_STORE=memory
unset DATABASE_URL
# 仍需 Redis，或配合 memory 单进程调试
./scripts/dev_stack.sh --memory
```

---

## 6. 首次使用

1. 打开 http://localhost:3000
2. 进入 **登录** → Dev 模式输入任意 `user_id`（如 `demo`）
3. **发起分析** → 选方案、输入标的（如 `600519.SS` 或 `NVDA`）
4. 提交后进入 **分析室**，观察 SSE 进度
5. 完成后查看 **报告** 或 **报告库**

健康检查：

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## 7. 开发鉴权说明

默认 `.env` / `.env.example` 开启开发友好选项：

| 变量 | 默认 | 说明 |
|------|------|------|
| `AX_AUTH_ALLOW_HEADER` | `true` | 允许 `X-User-Id` 头（Web dev 用） |
| `AX_AUTH_DEV_LOGIN` | `true` | 允许 `POST /auth/login` 签发 JWT |
| `AX_AUTH_DEV_MODE` | `true` | 综合 Dev 行为 |

Web 侧 `NEXT_PUBLIC_DEV_USER_ID=demo`（`.env.local`）。

**生产必须关闭**，见 [deployment.md](./deployment.md) § 安全。

---

## 8. 运行测试

```bash
cd AX_Analysis
source .venv/bin/activate
pytest -q                    # 全量
pytest tests/test_p2_features.py -q   # 单文件

cd apps/web && npm run build  # 前端类型检查 + 生产构建
```

---

## 9. 常见问题

| 现象 | 处理 |
|------|------|
| `ax-api` 找不到 | 确认 venv 已 activate 且 `pip install -e ".[dev]"` |
| 任务一直 queued | Worker 未启动或 `REDIS_URL` 不一致 |
| 登录 401 | 检查 JWT / Dev 登录是否开启 |
| A 股无数据 | `pip install -e ".[cn]"` 安装 AKShare |
| 端口占用 | 改 `AX_API_PORT` 或 Web `API_PROXY_URL` |
| Postgres 连接失败 | `docker compose up -d postgres`，核对 `DATABASE_URL` |

---

## 10. 环境变量速查

完整列表见 [`.env.example`](../.env.example)。本地最少：

```env
DEEPSEEK_API_KEY=sk-...
DATABASE_URL=postgresql://ax:ax@localhost:5432/ax_analysis
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=dev-secret-change-in-prod
AX_AUTH_ALLOW_HEADER=true
AX_AUTH_DEV_LOGIN=true
```

可选：

```env
FRED_API_KEY=...              # News 宏观指标
AX_DEFAULT_PLAN_ID=standard   # 新用户套餐
AX_API_RATE_LIMIT_RPM=120     # API 限流
```

---

*下一步：生产部署见 [deployment.md](./deployment.md)；接口详情见 [api-reference.md](./api-reference.md)*
