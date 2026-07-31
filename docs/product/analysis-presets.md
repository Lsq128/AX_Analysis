# AX_Analysis — 分析 Preset & 引擎参数（对齐 TradingAgents CLI）

> **原则：** 不新增引擎概念。Web 表单的每个字段，必须能一一对应 CLI / `DEFAULT_CONFIG` 已有项。  
> 参考代码：`cli/main.py`（`get_user_selections` → `_build_run_config` → `run_analysis`）、`cli/utils.py`、`cli/models.py`。

---

## 1. Worker 与 CLI 同构的 selections

CLI 在 `run_analysis` 里组装 `selections` dict，再 `_build_run_config(selections)`。  
AX Worker **应复用同一结构**，仅把 questionary 换成 HTTP/Web 传入的值：

```python
selections = {
    "ticker": "600519.SS",
    "analysis_date": "2026-07-29",
    "asset_type": "stock",           # detect_asset_type(ticker)
    "analysts": [AnalystType.MARKET, ...],  # 或 analyst key 字符串列表
    "research_depth": 3,             # 1 | 3 | 5，同 select_research_depth()
    "llm_provider": "deepseek",      # v1: deepseek | qwen-cn | kimi
    "shallow_thinker": "deepseek-v4-flash",
    "deep_thinker": "deepseek-v4-pro",
    "backend_url": None,
    "output_language": "Chinese",
}
# config = _build_run_config(selections, checkpoint=None)
# graph = TradingAgentsGraph(selected_analyst_keys, config=config, ...)
```

**实现位置：** `packages/ax_engine/build_config.py`（逻辑参考原 CLI，代码只在 AX 内）。

---

## 2. UI Preset → CLI 参数（非引擎 plan_id）

| AX 展示名 | `analysts`（key） | `research_depth` |
|-----------|-------------------|------------------|
| 快速诊股 | `market` | 1 |
| 技术趋势 | `market` | 1 |
| 资讯舆情 | `news`, `social` | 1 |
| 价值深挖 | `market`, `fundamentals` | 3 |
| 全面研判 | `market`, `social`, `news`, `fundamentals` | 3 |
| 深度推演 | 四位全选 | 5 |
| 数字资产快览 | `market`, `news`, `social` | 1 |

Preset 展开后仍走 `ANALYST_ORDER` 排序（`cli/main.py`）。  
Crypto：`filter_analysts_for_asset_type` 自动去掉 `fundamentals`（`cli/utils.py`）。

**research_depth** 同时写入（与 CLI 一致）：

- `config["max_debate_rounds"] = research_depth`
- `config["max_risk_discuss_rounds"] = research_depth`

---

## 3. v1 国内 LLM（对齐 `model_catalog.py`）

| 用户选择 | `llm_provider` | API Key  env |
|----------|----------------|--------------|
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` |
| 通义千问 | `qwen-cn` | `DASHSCOPE_CN_API_KEY` |
| Kimi | `kimi` | `MOONSHOT_API_KEY` |

快慢模型列表 **直接读** `get_model_options(provider)`，与 CLI Step 7 相同。  
v1 **不提供** OpenAI / Claude 选项（Phase 2+ 再加）。

---

## 4. 配额（SaaS 独有，引擎无此概念）

仅 SaaS 计费层需要，与引擎 config 无关：

```
consumption_points = preset_quota_factor[research_depth/analysts组合] × optional_model_factor
```

可简化为：**按 research_depth 分档**（1→1点，3→2.5点，5→4点），与国内模型成本差异 Phase 2 再细调。

---

## 5. 进度与报告（引擎已有）

| 需求 | 直接用 |
|------|--------|
| Live 进度 | `for chunk in graph.graph.stream(...)`（`cli/main.py` 同循环） |
| Agent 名 / 报告 key | `ANALYST_AGENT_NAMES`, `ANALYST_REPORT_MAP`（`cli/main.py`） |
| 保存报告 | `write_report_tree(final_state, ticker, path)` |
| 结构化结论 | 解析 state 中 PM / Trader 输出，或 `schemas.py` 渲染结果 |

**不需要** 单独设计 OpenAPI 或新 event schema 才能开工；Worker 可把 chunk 序列化 JSON 推 Redis/SSE，字段与 CLI `message_buffer` 一致即可。

---

## 6. A 股数据（仅引擎 dataflows 扩展）

SaaS 不改分析流程；Worker 在 `config["data_vendors"]` 按 ticker 后缀注入（与 `default_config.py` 相同机制）。  
见 AGENTS.md §3。

---

*2026-07-29 · 对齐「薄封装、复用 CLI」取向*
