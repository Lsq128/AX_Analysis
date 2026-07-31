# API 参考

> Base URL：`http://localhost:8000`（生产替换为实际域名）。  
> Web 经 Next.js rewrite 代理：`/api/v1/*` → 后端。

**鉴权：** `Authorization: Bearer <JWT>` 或 Dev 模式 `X-User-Id: demo`（`AX_AUTH_ALLOW_HEADER=true`）。

---

## 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | `{"status":"ok"}` |

---

## 鉴权 `/api/v1/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/config` | 鉴权配置（OAuth 提供商、Dev 开关） |
| POST | `/login` | Dev 登录，返回 JWT（需 `AX_AUTH_DEV_LOGIN`） |
| GET | `/oauth/{provider}/start` | 跳转 OAuth（github / oidc） |
| GET | `/oauth/{provider}/callback` | OAuth 回调 → 重定向 Web |
| GET | `/session` | 刷新 token |

---

## 用户 `/api/v1`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/me` | 当前用户、配额、套餐、Admin 标记 |

---

## 分析方案 `/api/v1/presets`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/presets` | Preset 列表；含 `locked`（按用户套餐） |

---

## LLM `/api/v1/llm`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/providers` | v1 国内 Provider + 模型列表 |
| GET | `/quota-estimate?preset=&provider=` | 点数估算 |

---

## 分析任务 `/api/v1/analyses`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/analyses` | 创建任务（202）；body 见下 |
| GET | `/analyses` | 任务列表；`?limit=&status=` |
| GET | `/analyses/{job_id}` | 任务详情 |
| POST | `/analyses/{job_id}/retry` | 失败重试（不重复扣点） |
| GET | `/analyses/{job_id}/events` | **SSE** 进度流 |

### 创建任务 Body

```json
{
  "ticker": "600519.SS",
  "analysis_date": "2026-07-29",
  "preset": "full",
  "llm_provider": "deepseek",
  "shallow_thinker": "deepseek-v4-flash",
  "deep_thinker": "deepseek-v4-pro"
}
```

**错误码：**

- `403` — 套餐不可用该 Preset
- `402` / 配额不足 — 点数不够
- `429` — IP 限流

---

## 报告 `/api/v1/analyses/{job_id}/report`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/report` | 章节 manifest |
| GET | `/report/{section_key}` | 章节 Markdown JSON |
| GET | `/report/signed-urls` | S3 单章 signed URL（local 模式 501） |
| GET | `/report/export` | **Markdown zip** 下载 |

---

## 报告库 `/api/v1/reports`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/reports` | 已完成报告列表；`?limit=` |

---

## 标的 `/api/v1/tickers`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/recent?limit=8` | 用户最近分析标的 |
| GET | `/search?q=&limit=8` | 搜索建议（catalog + 历史） |

---

## 计费 `/api/v1/billing`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/plans` | 套餐 catalog |

---

## 复盘 `/api/v1/memory`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/entries?limit=` | 记忆条目 |
| GET | `/stats` | 复盘统计 |

---

## 管理 `/api/v1/admin`（需 Admin）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/plans` | 套餐列表 |
| GET | `/stats` | 平台统计 |
| GET | `/users?limit=&offset=` | 用户列表 |
| PATCH | `/users/{external_id}/quota` | 调整配额 / 套餐 |

Admin 身份：`AX_ADMIN_USER_IDS` 或请求头 `X-Admin-Key`。

---

## SSE 事件类型（分析室）

连接：`GET /api/v1/analyses/{job_id}/events`，`Accept: text/event-stream`。

常见 event / data 字段（JSON）：

| 类型 | 说明 |
|------|------|
| `agent_status` | Agent 状态变更 |
| `report_section` | 某 Agent 报告片段 |
| `debate_timeline` | 多空辩论条目 |
| `message` | 对话消息 |
| `tool_call` | 工具调用 |
| `job_status` | queued / running / completed / failed |
| `error` | 失败信息 + error_code |

---

## curl 示例

```bash
# Dev 登录
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"demo","display_name":"Demo"}' | jq -r .access_token)

# 用户信息
curl -s http://localhost:8000/api/v1/me -H "Authorization: Bearer $TOKEN" | jq

# 创建分析
curl -s -X POST http://localhost:8000/api/v1/analyses \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"0700.HK","analysis_date":"2026-07-29","preset":"quick"}' | jq

# 标的搜索
curl -s "http://localhost:8000/api/v1/tickers/search?q=茅台" \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

*2026-07-29*
