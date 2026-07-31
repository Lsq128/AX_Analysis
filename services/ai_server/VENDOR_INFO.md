# AI Server — 内嵌引擎来源说明

本目录为 **AX_Analysis 自有 AI 分析引擎**，代码自开源项目 TradingAgents **完整复制** 而来，复制后 **独立演进**，与仓库上级 `../tradingagents/` **无运行时依赖、无 pip 关联**。

| 项 | 值 |
|----|-----|
| 复制来源 | `TradingAgents/tradingagents/` |
| 源仓库 | https://github.com/TauricResearch/TradingAgents |
| 复制时 commit | `a33fd4c0f134485a43553a2c23a63cb14adbd88f` |
| 复制日期 | 2026-07-29 |
| 许可证 | 见同目录 `LICENSE`（随上游一并复制） |

## 目录

```
services/ai_server/
├── LICENSE
├── VENDOR_INFO.md
└── tradingagents/          ← 多 Agent LangGraph 引擎（原 tradingagents 包）
```

## 未复制（在 AX 其他目录实现）

| 上游路径 | AX 替代 |
|----------|---------|
| `cli/` 交互终端 | `apps/web` + `packages/ax_engine/` |
| 根 `main.py` | `packages/ax_engine/runner.py` |
| 上游 `tests/` | `AX_Analysis/tests/`（待建） |

## 维护原则

1. **禁止** 在 AX 代码中 `import` 上级目录或 `pip install`  sibling 的 TradingAgents。
2. 引擎修改 **只改** `services/ai_server/tradingagents/` 内文件。
3. 若需同步上游安全修复：手动 cherry-pick 到本目录，并更新本文件 commit 记录。
