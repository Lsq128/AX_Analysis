# AX_Analysis 完整性审计 — 基于 TradingAgents 全能力

> **前提：** AX 的核心是 **TradingAgents 这套多 Agent 投研引擎**（已复制到 `services/ai_server/`）。  
> 本文逐项对照引擎 + 原 CLI **已有能力**，标记：✅ 已覆盖 / ⚠️ 待移植 / ❌ AX 需额外设计 / 🔒 安全风险。

---

## 1. 引擎能力总览（ai_server 已复制）

### 1.1 分析流水线

| 阶段 | 组件 | state 字段 | AX 产品映射 |
|------|------|------------|-------------|
| 分析师 | Market | `market_report` | 技术面 Tab / 分析室 |
| 分析师 | Sentiment | `sentiment_report` | 舆情 Tab |
| 分析师 | News | `news_report` | 资讯 Tab（含宏观工具） |
| 分析师 | Fundamentals | `fundamentals_report` | 基本面 Tab |
| 研究 | Bull / Bear / Manager | `investment_debate_state` | 多空时间线 + 研究结论卡 |
| 交易 | Trader | `trader_investment_plan` | 交易提案卡 |
| 风控 | Aggressive / Neutral / Conservative | `risk_debate_state` | 风控 Tab |
| 决策 | Portfolio Manager | `risk_debate_state.judge_decision` | 最终评级徽章 |
| 输出 | Signal | `final_trade_decision` | 列表摘要 |

### 1.2 数据工具（dataflows → Agent 调用）

| 类别 | 工具 | 默认 vendor | 需要 Key |
|------|------|-------------|----------|
| 行情 | `get_stock_data` | yfinance | 无 |
| 技术指标 | `get_indicators` | yfinance | 无 |
| 基本面 | `get_fundamentals` 等 | yfinance | 无 |
| 新闻 | `get_news`, `get_global_news` | yfinance | 无 |
| 内幕 | `get_insider_transactions` | yfinance | 无 |
| **宏观** | `get_macro_indicators` | **fred** | **FRED_API_KEY** |
| 预测市场 | `get_prediction_markets` | polymarket | 无（需出网） |
| 备用 | 上述多项 | alpha_vantage | **ALPHA_VANTAGE_API_KEY** |

Sentiment Analyst **额外**（非 dataflows vendor 表）：
- `stocktwits.py` — 公开 API，无 Key
- `reddit.py` — RSS/JSON，无 Key  
→ **A 股几乎无效**，AX 需在 `ax_dataflows` 或 ai_server 内扩展国内舆情。

### 1.3 LLM Provider（api_key_env.py）

| Provider | 环境变量 | v1 AX 是否启用 |
|----------|----------|----------------|
| deepseek | DEEPSEEK_API_KEY | ✅ |
| qwen-cn | DASHSCOPE_CN_API_KEY | ✅ |
| kimi | MOONSHOT_API_KEY | ✅ |
| qwen | DASHSCOPE_API_KEY | 可选 |
| openai / anthropic / google / … | 各 *_API_KEY | Phase 2+ |

### 1.4 Config / 环境变量（default_config.py）

**TRADINGAGENTS_*（导入时自动 overlay）：**

| 变量 | 作用 | AX 建议 |
|------|------|---------|
| TRADINGAGENTS_LLM_PROVIDER | Provider | Worker 按用户选择写入 env 或 config |
| TRADINGAGENTS_DEEP/QUICK_THINK_LLM | 模型 | 同上 |
| TRADINGAGENTS_LLM_BACKEND_URL | 自定义端点 | 一般不设 |
| TRADINGAGENTS_OUTPUT_LANGUAGE | 报告语言 | 默认 Chinese |
| TRADINGAGENTS_MAX_DEBATE_ROUNDS | 研究轮数 | = research_depth |
| TRADINGAGENTS_MAX_RISK_ROUNDS | 风控轮数 | = research_depth |
| TRADINGAGENTS_CHECKPOINT_ENABLED | 断点续跑 | 可选 true |
| TRADINGAGENTS_BENCHMARK_TICKER | Alpha 基准 | 一般自动 |
| TRADINGAGENTS_TEMPERATURE | 采样温度 | 可选 |
| TRADINGAGENTS_LLM_MAX_RETRIES | 429 重试 | 建议 6 |
| TRADINGAGENTS_*_EFFORT / THINKING | 推理深度 | 用 Claude/GPT 时再设 |

**路径类（SaaS 必须 per-user / per-job，不能共用 `~/.tradingagents`）：**

| 变量 | 默认 | 🔒 AX 必须 |
|------|------|-----------|
| TRADINGAGENTS_RESULTS_DIR | ~/.tradingagents/logs | `/data/users/{id}/logs` |
| TRADINGAGENTS_CACHE_DIR | ~/.tradingagents/cache | `/data/users/{id}/cache` |
| TRADINGAGENTS_MEMORY_LOG_PATH | ~/.tradingagents/memory/... | **每用户独立文件** |

### 1.5 记忆与复盘（Memory + Reflection）

| 能力 | 入口 | 说明 |
|------|------|------|
| 写入决策 | `memory_log.store_decision` | 每次完成后 |
| 注入 PM | `get_past_context(ticker)` | 同标的历史 |
| 解析 pending | `_resolve_pending_entries` | 下次跑同 ticker 时算收益 |
| 反思 | `Reflector.reflect_on_final_decision` | 需持有期价格 |

⚠️ **原 CLI `run_analysis` 走 `stream` 路径时，未调用 `store_decision` / 未注入 `past_context`**（与 `propagate()` 不一致）。  
**AX ax_engine 必须补齐**，否则复盘中心无数据。

### 1.6 Checkpoint

| 项 | 说明 |
|----|------|
| SQLite | `{data_cache_dir}/checkpoints/{TICKER}.db` |
| thread_id | ticker + date + analysts + debate + risk + asset_type |

🔒 **多用户同 ticker 会共用 checkpoint 文件名** — AX 必须在 path 加 `user_id` 前缀。

### 1.7 报告

| 项 | 函数 |
|----|------|
| 分章 Markdown | `reporting.write_report_tree` |
| 完整路径 | `TradingAgentsGraph.save_reports` |

---

## 2. 原 CLI 未复制 — ax_engine 必须移植

| 原文件 | 函数/逻辑 | 优先级 | 说明 |
|--------|-----------|--------|------|
| `cli/main.py` | `_build_run_config` | P0 | config 组装 |
| `cli/main.py` | stream 循环 1132–1238 | P0 | 分析室事件源 |
| `cli/main.py` | `update_analyst_statuses` | P0 | 五幕进度 |
| `cli/main.py` | debate/risk chunk 处理 | P0 | 研究/风控 Live |
| `cli/main.py` | `trace` merge → final_state | P0 | 报告生成 |
| `cli/main.py` | `resolve_instrument_context` | P0 | 防公司名幻觉 |
| `cli/utils.py` | `detect_asset_type` | P0 | stock/crypto |
| `cli/utils.py` | `filter_analysts_for_asset_type` | P0 | crypto 无基本面 |
| `cli/utils.py` | `select_research_depth` 1/3/5 | P0 | Preset |
| `cli/utils.py` | `is_valid_ticker_input` | P0 | 输入校验 |
| `cli/models.py` | AnalystType, AssetType | P0 | |
| `cli/stats_handler.py` | Token/工具统计 | P1 | 成本面板 |
| `cli/main.py` | `propagate()` 侧 memory | P0 | **CLI 遗漏，AX 要补** |
| `graph/trading_graph.py` | `propagate()` 或 `_run_graph` 收尾 | P0 | store_decision |

**可选复制参考（不必 import cli 包）：** 将上述逻辑抄到 `packages/ax_engine/` 单文件模块。

---

## 3. 原 .env.example 应对齐的变量（AX .env）

### 3.1 建议 v1 必填/推荐

```bash
# LLM（平台 Worker）
DEEPSEEK_API_KEY=
DASHSCOPE_CN_API_KEY=
MOONSHOT_API_KEY=

# 宏观（News Analyst）
FRED_API_KEY=

# 引擎行为
TRADINGAGENTS_LLM_PROVIDER=deepseek
TRADINGAGENTS_DEEP_THINK_LLM=deepseek-v4-pro
TRADINGAGENTS_QUICK_THINK_LLM=deepseek-v4-flash
TRADINGAGENTS_OUTPUT_LANGUAGE=Chinese
TRADINGAGENTS_LLM_MAX_RETRIES=6
```

### 3.2 可选增强

```bash
ALPHA_VANTAGE_API_KEY=          # yfinance 失败时 fallback
TRADINGAGENTS_CHECKPOINT_ENABLED=false
TRADINGAGENTS_TEMPERATURE=
```

### 3.3 与 geo_engine/.env 无关

`geo_engine` 是 **GEO 评分** 独立产品（Perplexity/Kimi 监控引用），**不包含** FRED、不包含 TradingAgents 分析链。**不要混用一份 .env。**

---

## 4. 国内市场 — 引擎默认的缺口（AX 必须规划）

| 缺口 | 现状 | AX 动作 |
|------|------|---------|
| A 股行情/财报 | yfinance 弱 | `ax_dataflows` + config 注入 |
| 中文新闻 | yfinance 少 | ax_dataflows |
| 舆情 | StockTwits/Reddit | 国内源 Phase 2 |
| 宏观 | FRED 偏美国 | FRED 仍有用；中国宏观 Phase 2 |
| global_news_queries | 英文美联储/SPY | **ai_server 内改中文/亚太 query** |
| benchmark_map | 含 .SS/.SZ | ✅ 已有 |

---

## 5. 🔒 安全与多租户（当前规划遗漏项）

| 风险 | 说明 | 缓解 |
|------|------|------|
| **Key 泄露** | LLM/FRED Key 在 Worker env | 禁止下发前端；日志脱敏 |
| **用户数据串线** | 默认 memory/cache 全局 | 每用户独立路径 + DB 鉴权 |
| **Checkpoint 串线** | 按 ticker 文件名 | path 含 user_id |
| **报告越权** | 猜 analysis_id | API 校验 user_id |
| **配额滥用** | 无限提交分析 | 点数 + 速率限制 |
| **LLM 成本攻击** | 深度推演 × 大模型 | 套餐上限 + 模型系数 |
| **Ticker 注入** | 路径/特殊字符 | `safe_ticker_component` + 校验 |
| **dotenv CWD** | ai_server 从 CWD 读 .env | Worker 启动时显式 `load_dotenv(AX/.env)` |
| **合规** | 金融建议 | 免责声明 + 非投资建议 |
| **密钥进 Git** | .env 误提交 | .gitignore；只用 .env.example |
| **多 .env 密钥不一致** | 根 vs geo vs AX | 文档约定：**AX 只用 AX_Analysis/.env** |

---

## 6. 当前 AX 仓库状态自检

| 项 | 状态 |
|----|------|
| ai_server/tradingagents 复制 | ✅ ~72 文件 |
| ax_engine 可运行 runner | ✅ `run_analysis_job` |
| CLI stream 逻辑移植 | ✅ `progress.py` + `runner.py` |
| memory store_decision 补齐 | ✅ stream 结束后写入 |
| per-user 路径策略 | ✅ `paths.py` |
| .env.example 完整 | ⚠️ 已补 FRED，见下 |
| Web/API/Worker | ✅ API/Worker 骨架 + Next.js 工作台 + Postgres 配额 |
| 向导 Step4 LLM + 点数系数 | ✅ PR2：`ax_llm` / `ax_billing` + `/api/v1/llm/*` + Step4 UI |
| 报告 OSS + signed URL | ✅ PR3：`ax_storage` + Worker 上传 + `/report/signed-urls` |
| A 股 ax_dataflows | ✅ PR1+PR4：OHLCV/指标/基本面/新闻（AKShare） |
| 分析室辩论时间线 + Markdown | ✅ PR5：`debate_timeline` SSE + `MarkdownView` |
| 生产 Auth（关 header + OAuth） | ✅ PR6：OAuth GitHub/OIDC + `AuthGuard` + dev login 门禁 |
| 套餐计费 + Admin | ✅ PR7：`ax_billing/plans` + `/billing/plans` + `/admin/*` + 管理页 |
| Memory 复盘 UI | ✅ PR8：`ax_memory` + `/memory/*` + 复盘中心页 |
| 报告库独立页 | ✅ `/reports` API + `/workspace/reports` 报告库 |
| 失败重试 + 友好错误 | ✅ `POST /analyses/{id}/retry` + error_code 分类 |
| 最近标的 API | ✅ `GET /tickers/recent` + 向导 Step2 |
| 报告结构化摘要卡片 | ✅ 交易提案 / 研究经理卡片 |
| 生产部署文档 | ✅ `docs/deployment.md` |
| 套餐方案锁定（free 禁 deep） | ✅ `plan_gates` + presets `locked` + 创建 403 |
| API 按 IP 限流 | ✅ `RateLimitMiddleware` + `AX_API_RATE_LIMIT_RPM` |
| 标的搜索建议 | ✅ `GET /tickers/search` + 向导下拉 |
| 报告 Markdown 压缩包导出 | ✅ `GET /analyses/{id}/report/export` |
| 套餐页 + 法律页 | ✅ `/workspace/billing` + `/legal/*` |
| Token/调用统计面板 | ✅ `JobStatsPanel` 分析室完成态 |
| CI（pytest + web build） | ✅ `.github/workflows/ax-analysis-ci.yml` |

---

## 7. ax_engine 推荐实现路径（对齐引擎，不遗漏）

```
run_analysis_job(job):
  1. load_dotenv(AX_Analysis/.env)
  2. build_config(job) + per-user paths
  3. graph = TradingAgentsGraph(analysts, config)
  4. graph._resolve_pending_entries(ticker)   # propagate 同款
  5. past_context = graph.memory_log.get_past_context(ticker)
  6. instrument_context = graph.resolve_instrument_context(...)
  7. init_state = create_initial_state(..., past_context, instrument_context)
  8. for chunk in graph.graph.stream(init_state, **args):
         emit_sse(map_chunk(chunk))           # CLI 1132–1238 同款
  9. merge trace → final_state
 10. memory_log.store_decision(...)
 11. write_report_tree → OSS
 12. stats → DB（成本）
```

**不要** 仅调用 `invoke()` 而无 stream，否则分析室无 Live 体验。

---

## 8. 实施优先级（修订）

| 优先级 | 任务 |
|--------|------|
| P0 | 完整 `.env.example` + Worker 显式 load |
| P0 | `ax_engine/runner.py` 按 §7 实现 |
| P0 | per-user memory/cache/results 路径 |
| P1 | Preset + 国内三 Provider Web 选择 |
| P1 | SSE + 报告 OSS |
| P1 | FRED + 可选 ALPHA_VANTAGE |
| P2 | ax_dataflows A 股 |
| P2 | 复盘 UI + pending 解析 |
| P2 | checkpoint 带 user_id |
| P3 | Auth、配额、Admin |

---

## 9. 自审结论（曾忽略的点）

1. **FRED** — 宏观默认 vendor，AX 应显式配置（你已指出）。  
2. **ALPHA_VANTAGE** — fallback 未写入 AX .env.example。  
3. **Memory 链路** — CLI stream 路径不完整，AX 不能照抄 CLI 而不补 `store_decision` / `past_context`。  
4. **多租户路径** — 引擎默认 `~/.tradingagents` 在 SaaS **不可用**。  
5. **Checkpoint 文件名** — 仅 ticker，多用户冲突。  
6. **global_news_queries** — 美国中心，国内产品需改 ai_server 配置。  
7. **Sentiment 数据源** — 非 vendor 表，A 股空白。  
8. **geo_engine** — 与 TradingAgents 分析无关，env 不应合并。  
9. **propagate vs stream** — 需合并两者优点。  
10. **TRADINGAGENTS_LLM_MAX_RETRIES** — 国内 API 429 时重要。

---

*2026-07-29 · 随 ax_engine 实现更新勾选状态*
