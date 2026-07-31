# AI Server（内嵌分析引擎）

AX_Analysis 的 **核心 AI 服务**：多 Agent 投研图（LangGraph）、数据流、LLM 客户端、报告生成。

- Python 包名：`tradingagents`（保留原名以减少复制后 diff；**仅存在于 AX_Analysis 内**）
- 调用方：`packages/ax_engine`、`apps/worker`
- 与仓库外 TradingAgents 项目：**无任何关系**

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
```

详见 [VENDOR_INFO.md](./VENDOR_INFO.md)。
