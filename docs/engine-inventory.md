# 引擎清单 — ai_server 与 AX 分工

> ai_server = `services/ai_server/tradingagents/`（已复制进 AX，**与上级无关**）

---

## 1. ai_server 已包含（复制自原 tradingagents 包）

| 模块 | 路径 | 作用 |
|------|------|------|
| 分析图 | `graph/trading_graph.py` | `TradingAgentsGraph`、stream、checkpoint |
| Agent | `agents/` | 四位 Analyst + 研究/交易/风控/PM |
| 结构化输出 | `agents/schemas.py` | 五档评级、交易提案 |
| 数据流 | `dataflows/` | yfinance、AlphaVantage、FRED、新闻等 |
| LLM | `llm_clients/` | DeepSeek、通义、Kimi、OpenAI… |
| 配置 | `default_config.py` | DEFAULT_CONFIG、TRADINGAGENTS_* |
| 报告 | `reporting.py` | write_report_tree |
| 记忆 | `agents/utils/memory.py` | 决策 log、复盘 |

**共 ~72 个文件**（复制时统计），安装 AX 后 `import tradingagents` 仅指向本目录。

---

## 2. 原 CLI 未复制 — 在 AX 重写

| 原路径 | AX 位置 | 说明 |
|--------|---------|------|
| `cli/main.py` `run_analysis` | `packages/ax_engine/runner.py` | 去 Rich/questionary |
| `cli/main.py` `_build_run_config` | `packages/ax_engine/build_config.py` | 同字段 |
| `cli/utils.py` 深度/分析师 | `packages/ax_presets/` + engine | Preset 展开 |
| `cli/models.py` | `packages/ax_engine/models.py` | 待复制/重写 AnalystType |
| `cli/stats_handler.py` | `packages/ax_engine/stats.py` | 可选，Token 统计 |

终端 UI（Rich Live）→ **`apps/web` 分析室**。

---

## 3. AX 产品层自建（ai_server 没有）

| 功能 | 路径 |
|------|------|
| 注册登录 | `apps/api/auth/` |
| 套餐配额 | `apps/api/billing/` |
| 分析任务表 | `apps/api/analyses/` |
| 队列 | `apps/worker/` |
| 标的搜索（茅台→600519.SS） | `apps/api/symbols/` |
| 营销/工作台 UI | `apps/web/` |
| A 股 AKShare 等 | `packages/ax_dataflows/` → 注入 `config["data_vendors"]` |

---

## 4. ai_server 内后续可改（不影响上级）

- 默认 `data_vendors` 增加 akshare
- 默认 `output_language` Chinese
- 国内 Provider 默认模型
- Sentiment 换国内舆情源

**全部在 `services/ai_server/tradingagents/` 或 ax_dataflows 注入，不动 ../tradingagents。**

---

## 5. 分析 Preset → ai_server 参数

见 [product/analysis-presets.md](./product/analysis-presets.md)。

核心字段：

- `TradingAgentsGraph(selected_analysts, config=config)`
- `config["max_debate_rounds"]` = `config["max_risk_discuss_rounds"]` = 1 | 3 | 5
- `config["llm_provider"]` = `deepseek` | `qwen-cn` | `kimi`

---

## 6. 实施顺序

1. ✅ 复制 `tradingagents` → `services/ai_server/`
2. `pip install -e .` 验证 import
3. `packages/ax_engine/runner.py` 跑通一次分析
4. `apps/worker` 队列
5. `apps/web` 最小 UI
6. `ax_dataflows` A 股

---

*2026-07-29 · standalone AX_Analysis*
