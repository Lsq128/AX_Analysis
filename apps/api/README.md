# apps/api

FastAPI 业务 API。完整接口见 **[docs/api-reference.md](../../docs/api-reference.md)**。

## 启动

```bash
cd AX_Analysis
source .venv/bin/activate
export DATABASE_URL=postgresql://ax:ax@localhost:5432/ax_analysis
export REDIS_URL=redis://localhost:6379/0
ax-api
# http://localhost:8000
```

## 主要路由模块

| 模块 | 前缀 | 能力 |
|------|------|------|
| auth | `/api/v1/auth` | JWT、OAuth |
| users | `/api/v1/me` | 用户与配额 |
| presets | `/api/v1/presets` | 分析方案 + locked |
| llm | `/api/v1/llm` | Provider、点数估算 |
| analyses | `/api/v1/analyses` | 任务 CRUD、SSE、retry |
| reports | `/api/v1/analyses/{id}/report` | 章节、signed URL、zip 导出 |
| report_library | `/api/v1/reports` | 报告库 |
| tickers | `/api/v1/tickers` | recent、search |
| billing | `/api/v1/billing` | 套餐 |
| memory | `/api/v1/memory` | 复盘 |
| admin | `/api/v1/admin` | 管理 |

## 鉴权

- **JWT**：`Authorization: Bearer <token>`
- **OAuth**：GitHub / OIDC
- **Dev**：`X-User-Id`（`AX_AUTH_ALLOW_HEADER=true`）
- **Dev 登录**：`POST /auth/login`

## 示例

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"demo"}' | jq -r .access_token)

curl -s http://localhost:8000/api/v1/me -H "Authorization: Bearer $TOKEN"
```

## 任务存储

- `DATABASE_URL` + `REDIS_URL`：Postgres + Redis（生产）
- `AX_JOB_STORE=memory`：单进程调试
