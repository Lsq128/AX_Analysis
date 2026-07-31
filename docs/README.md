# AX_Analysis 文档中心

> **AX_Analysis** 是面向国内个人投资者的 AI 多 Agent 投研 SaaS，引擎代码 vendored 于 `services/ai_server/`，与上级 `tradingagents/` **无运行时依赖**。

---

## 快速导航

| 文档 | 适合谁 | 内容 |
|------|--------|------|
| [getting-started.md](./getting-started.md) | 开发者 | **本地启动**、环境变量、联调、测试 |
| [features.md](./features.md) | 产品 / 研发 | **已实现功能清单**（Web、API、Worker、计费） |
| [architecture.md](./architecture.md) | 架构师 | **技术方案**、分层、数据流、包职责 |
| [deployment.md](./deployment.md) | 运维 | **Docker 基础设施**、生产部署、安全清单 |
| [api-reference.md](./api-reference.md) | 前后端 | REST / SSE **接口一览** |
| [completeness-audit.md](./completeness-audit.md) | 全员 | 引擎能力对照、遗漏项、安全审计 |
| [engine-inventory.md](./engine-inventory.md) | 引擎维护 | ai_server 模块清单 |

### 产品与引擎配置

| 文档 | 内容 |
|------|------|
| [product/analysis-presets.md](./product/analysis-presets.md) | 分析方案 Preset 说明 |
| [product/wireframes.md](./product/wireframes.md) | 线框与页面结构 |
| [../.env.example](../.env.example) | 环境变量完整模板 |

### 工程约束

| 文档 | 内容 |
|------|------|
| [../AGENTS.md](../AGENTS.md) | 开发禁止/允许事项 |
| [../services/ai_server/VENDOR_INFO.md](../services/ai_server/VENDOR_INFO.md) | 引擎复制来源 |

---

## 一分钟概览

```
用户浏览器
    ↓
apps/web (Next.js :3000)  ──rewrite──→  apps/api (FastAPI :8000)
                                              ↓
                                    Redis 队列 + Postgres 配额
                                              ↓
                                    apps/worker → ax_engine → ai_server
                                              ↓
                                    报告 local / S3 · 每用户 memory/cache
```

**本地最简路径：**

```bash
cd AX_Analysis
python -m venv .venv && source .venv/bin/activate
pip install -e ".[cn,dev]"
cp .env.example .env          # 填写 LLM Key
docker compose up -d postgres redis
# 终端 1: ax-worker  |  终端 2: ax-api  |  终端 3: ./scripts/dev_stack.sh web
```

详见 [getting-started.md](./getting-started.md)。

---

## 仓库结构

```
AX_Analysis/
├── apps/
│   ├── web/          Next.js 前端
│   ├── api/          FastAPI 业务 API
│   └── worker/       Redis 队列消费者
├── packages/
│   ├── ax_engine/    分析运行编排（替代 CLI）
│   ├── ax_presets/   分析方案
│   ├── ax_dataflows/ A 股等数据源
│   ├── ax_billing/   套餐与配额
│   ├── ax_auth/      JWT / OAuth
│   ├── ax_jobs/      任务模型与存储
│   ├── ax_db/        Postgres ORM
│   ├── ax_memory/    复盘读取
│   ├── ax_reports/   报告章节解析
│   ├── ax_storage/   local / S3 报告存储
│   └── ax_llm/       v1 国内 LLM 目录
├── services/ai_server/tradingagents/   多 Agent 引擎（vendored）
├── docker-compose.yml                  Postgres + Redis + MinIO(可选)
├── scripts/dev_stack.sh                本地开发辅助
└── tests/                              pytest（82+ 用例）
```

---

*最后更新：2026-07-29*
