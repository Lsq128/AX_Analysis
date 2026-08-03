# AX_Analysis

**个人自用 / 自托管投研工具**（可选开启 SaaS 套餐计费）— 国内个人投资者 AI 多 Agent 投研（A 股 / 港股 / 美股）。

默认 `AX_BILLING_ENABLED=false`：不计费、不限套餐、Web 不展示套餐页；设为 `true` 可恢复点数与套餐门控。

与同级目录 `../tradingagents/`、**TradingAgents 开源项目无任何运行时关系**：引擎代码已 **复制** 到本仓库内 `services/ai_server/`，后续只在 AX 内维护。

---

## 文档（从这里开始）

| 文档 | 说明 |
|------|------|
| **[docs/README.md](./docs/README.md)** | **文档中心** — 全部文档索引 |
| [docs/getting-started.md](./docs/getting-started.md) | **本地启动**（venv、Docker、三终端联调） |
| [docs/features.md](./docs/features.md) | **已实现功能清单**（含可选套餐说明） |
| [docs/architecture.md](./docs/architecture.md) | **技术方案**与分层 |
| [docs/deployment.md](./docs/deployment.md) | **生产 / Docker 部署** |
| [docs/api-reference.md](./docs/api-reference.md) | REST / SSE 接口 |
| [docs/completeness-audit.md](./docs/completeness-audit.md) | 引擎能力对照与安全审计 |

工程约束：[AGENTS.md](./AGENTS.md)

---

## 仓库结构

```
AX_Analysis/
├── services/ai_server/tradingagents/   ← 多 Agent 引擎（vendored）
├── packages/                           ← ax_engine · ax_billing（可选）· ax_dataflows …
├── apps/web · api · worker
├── Dockerfile.python · Dockerfile.web  ← 演示栈镜像
├── docker-compose.yml                  ← Postgres + Redis + API + Worker + Web (+ MinIO 可选)
├── scripts/up.sh · down.sh             ← Docker 一键演示
├── scripts/dev_stack.sh
└── docs/
```

---

## 一键启动（Docker 演示）

需已安装 Docker，并准备好 `.env`（至少一个 LLM Key）：

```bash
cd AX_Analysis
cp .env.example .env   # 填写 DEEPSEEK_API_KEY 等；默认已 AX_BILLING_ENABLED=false
./scripts/up.sh        # → http://localhost:3000
./scripts/down.sh      # 停止（默认保留数据卷）
```

> 演示栈：Postgres + Redis + API + Worker + Web。生产部署见 [docs/deployment.md](./docs/deployment.md)。

---

## 快速启动

```bash
cd AX_Analysis
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[cn,dev]"
cp .env.example .env          # 填写 LLM Key（默认不计费）

docker compose up -d postgres redis

# 终端 1          终端 2          终端 3
ax-worker         ax-api          ./scripts/dev_stack.sh web
                                  → http://localhost:3000
```

环境变量（本地）：

```bash
export DATABASE_URL=postgresql://ax:ax@localhost:5432/ax_analysis
export REDIS_URL=redis://localhost:6379/0
# 可选：export AX_BILLING_ENABLED=true   # 恢复套餐 / 点数
```

无 Docker 调试：`./scripts/dev_stack.sh --memory`（任务不持久化）。

**详细步骤 → [docs/getting-started.md](./docs/getting-started.md)**

---

## 测试

```bash
pytest -q
cd apps/web && npm run build
```

---

## 原则

1. **不修改** 上级 `../tradingagents/`、`../cli/`。
2. **不依赖** 上级 pip 包；`import tradingagents` 只解析到 `services/ai_server/tradingagents/`。
3. 产品、账户、Web **只在 AX_Analysis 实现**；套餐计费默认关闭，代码保留便于再开。

---

*2026-08-03*
