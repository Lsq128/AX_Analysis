# packages/ax_engine

编排 **ai_server**（`services/ai_server/tradingagents`），替代原终端 CLI。

| 模块 | 职责 |
|------|------|
| `env.py` | 显式 `load_dotenv(AX_Analysis/.env)` |
| `build_config.py` | Web selections → `DEFAULT_CONFIG` 字段 |
| `paths.py` | per-user memory/cache/results 路径 |
| `runner.py` | `TradingAgentsGraph` + `stream()` + memory + reports |
| `progress.py` | chunk → 分析室进度 / 事件 |
| `models.py` | `AnalysisRequest`、`AnalystType`、`AssetType` |
| `ticker.py` | normalize / detect_asset_type |
| `stats.py` | LLM/tool 用量回调 |

**import 路径：** `from tradingagents.graph...`（仅 AX 内 ai_server）
