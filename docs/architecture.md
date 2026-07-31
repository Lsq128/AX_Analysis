# AX_Analysis 架构与技术方案

> AX 是 **独立 SaaS 产品**：引擎自 TradingAgents **复制** 至 `services/ai_server/`，与上级仓库无 import 关系。

---

## 1. 设计原则

1. **薄产品层、厚引擎层** — Web/API 只做账户、队列、计费；分析逻辑在 ai_server
2. **对齐原 CLI** — `ax_engine` 复用 stream 循环、Agent 映射、报告结构，不发明新分析范式
3. **多租户隔离** — 每用户独立 memory / cache / results 路径，DB 校验任务归属
4. **Key 不下发** — LLM / 数据 API Key 仅在 Worker 进程

---

## 2. 分层架构

```
┌──────────────────────────────────────────────────────────────────┐
│  apps/web              Next.js 15 · App Router · Tailwind v4      │
│    营销 · 工作台 · 分析室 SSE · 报告 · Admin                       │
├──────────────────────────────────────────────────────────────────┤
│  apps/api              FastAPI · JWT/OAuth · SSE proxy           │
│    任务 CRUD · 计费 · 报告读 · 限流 middleware                    │
├──────────────────────────────────────────────────────────────────┤
│  apps/worker           Redis BLPOP · ax_engine.run_analysis_job  │
├──────────────────────────────────────────────────────────────────┤
│  packages/                                                         │
│    ax_presets    UI Preset → analysts + research_depth           │
│    ax_llm        v1 国内 Provider 目录 + 点数系数                 │
│    ax_billing    套餐 · 配额扣减 · plan_gates                     │
│    ax_auth       JWT · OAuth GitHub/OIDC                         │
│    ax_jobs       任务模型 · memory/redis/postgres store           │
│    ax_db         SQLAlchemy · User · Quota                       │
│    ax_engine     build_config · runner · progress · paths        │
│    ax_dataflows  A 股 AKShare vendor 注入                         │
│    ax_reports    报告章节解析                                       │
│    ax_storage    local / S3 报告读写 + signed URL                 │
│    ax_memory     用户 memory 日志读取（复盘）                        │
├──────────────────────────────────────────────────────────────────┤
│  services/ai_server/tradingagents                                 │
│    TradingAgentsGraph · agents · dataflows · llm · reporting     │
└──────────────────────────────────────────────────────────────────┘
         PostgreSQL          Redis              OSS / local disk
         用户/配额/任务       队列 + Pub/Sub       报告 + 用户数据
```

---

## 3. 分析请求全链路

```
1. Web 向导提交
      ↓ POST /api/v1/analyses
2. API 校验 ticker、preset 套餐、配额
      ↓ 扣点（Postgres）· 写 job · LPUSH Redis
3. Worker BLPOP
      ↓ ax_presets.expand_preset
      ↓ ax_engine.build_config（LLM、路径、data_vendors）
      ↓ TradingAgentsGraph.stream()
4. 每个 chunk → Redis Pub/Sub → API SSE → 浏览器分析室
5. 结束 → write_report_tree → ax_storage 上传（可选）
      ↓ 更新 job：completed、report_path、stats、decision_preview
6. Web 报告页 / 报告库读取章节
```

**失败路径：** Worker 捕获异常 → `ax_jobs/errors` 分类 → job.failed + error_code → UI 友好文案 + retry API。

---

## 4. 核心包职责

| 包 | 职责 |
|----|------|
| `ax_engine` | SaaS 侧「无 CLI 终端」运行器；`run_analysis_job` 入口 |
| `ax_presets` | 7 种 Preset，映射 analysts + research_depth + 基础点数 |
| `ax_dataflows` | 注册 A 股 vendor，Worker 按 ticker 注入 `config["data_vendors"]` |
| `ax_billing` | `plans.py` 三档套餐；`quota.py` 扣点；`plan_gates.py` Preset 锁定 |
| `ax_jobs` | `AnalysisJobRecord`；store 实现 memory / redis / postgres |
| `ax_auth` | JWT 签发校验；OAuth state + callback |
| `ax_storage` | 报告 local 根目录或 S3 put/get + signed URL |
| `ax_reports` | 扫描报告目录、按 key 读 Markdown |
| `ax_memory` | 解析 per-user `trading_memory.md` 供复盘 UI |
| `ax_llm` | DeepSeek / 通义 CN / Kimi 模型表与 quota_factor |
| `ax_db` | User、UserQuota ORM；`UserRepository` |

---

## 5. 任务存储模式

| 模式 | 环境 | 行为 |
|------|------|------|
| memory | `AX_JOB_STORE=memory` | 单进程调试，重启丢失 |
| redis | `REDIS_URL` | 队列 + SSE，job 元数据在 Redis |
| postgres | `DATABASE_URL` + Redis | 持久化用户、配额、job；**生产推荐** |

---

## 6. 报告存储

| `AX_REPORT_STORAGE` | Worker 写 | API 读 |
|---------------------|-----------|--------|
| `local`（默认） | 磁盘 `report_path` | 同机直读 |
| `s3` | 上传后 DB 存 key | signed URL 或 API 代理读 |

生产多 Worker / 多 API 实例 **必须** S3 或共享 NFS。

---

## 7. 计费模型

```
consumption_points = preset.quota_points × llm_provider.quota_factor
```

- 创建任务时预扣；失败且不可重试时可退（按实现）
- `retry` 不重复扣点（同一 job_id）
- `free` 套餐：`deep` Preset API 403 + UI locked

套餐定义：`packages/ax_billing/plans.py`

---

## 8. 鉴权模型

| 层级 | 机制 |
|------|------|
| 用户 | JWT Bearer；sub = external_id |
| Dev | `X-User-Id` + `POST /auth/login` |
| Admin | `AX_ADMIN_USER_IDS` 或 `X-Admin-Key` |
| 资源 | `assert_job_owner(job.user_id, current_user_id)` |

生产：`AX_AUTH_ALLOW_HEADER=false`、`AX_AUTH_DEV_LOGIN=false` + OAuth。

---

## 9. 限流

`RateLimitMiddleware`：按客户端 IP 滑动窗口（60s）。

- 默认：`AX_API_RATE_LIMIT_RPM=120`
- `POST /api/v1/analyses` 更严：`max(5, RPM/6)`

---

## 10. 部署单元

| 进程 | 入口 | 端口 |
|------|------|------|
| ax-api | `ax_api.main:app` | 8000 |
| ax-worker | `ax_worker.main` | — |
| ax-web | `next start` | 3000 |

基础设施（Docker）：Postgres 5432、Redis 6379、MinIO 9000（可选）。

详见 [deployment.md](./deployment.md)。

---

## 11. 与 TradingAgents 的关系

| | TradingAgents（上级） | AX_Analysis |
|--|----------------------|-------------|
| 定位 | 开源研究框架 / CLI | 商业 SaaS |
| 代码 | `../tradingagents/` | `services/ai_server/tradingagents/` 复制体 |
| 运行时依赖 | — | **无** |
| 演进 | 社区 upstream | AX 团队独立维护 ai_server |

Preset 与 CLI 参数对齐说明见上级仓库 `docs/ax-analysis/analysis-plan-config.md`。

---

## 12. 实现阶段（已完成）

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0 | 引擎 runner、per-user 路径、失败重试、部署文档 | ✅ |
| P1 | LLM 选择、报告 OSS、A 股 dataflows、分析室 SSE | ✅ |
| P2 | Auth/OAuth、套餐 Admin、Memory 复盘、报告库 | ✅ |
| P2+ | 标的搜索、套餐锁定、限流、zip 导出、CI | ✅ |
| P3 | 在线支付、PDF、E2E、容器镜像 | 未做 |

功能明细见 [features.md](./features.md)。

---

*2026-07-29*
