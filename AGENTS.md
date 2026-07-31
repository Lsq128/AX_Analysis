# AGENTS.md — AX_Analysis

> **独立项目。** 与仓库内 `../tradingagents/` **无关联**：不 import 上级、不 pip 依赖上级、不改上级文件。

---

## 1. 架构一句话

```
apps (web/api/worker)  →  packages (ax_*)  →  services/ai_server (tradingagents)
```

- **ai_server**：内嵌 AI 分析引擎（自 TradingAgents 复制，见 `VENDOR_INFO.md`）
- **ax_engine**：无终端 UI 的分析运行器（逻辑参考原 CLI，代码在 AX 内重写）
- **apps**：SaaS 产品层

---

## 2. 禁止事项

1. ❌ 修改 `../tradingagents/`、`../cli/`、`../geo_engine/`
2. ❌ `pip install -e ..` 或从上级 import
3. ❌ 在文档中把 AX 描述为 TradingAgents 的「插件 / 上游下游」—— **复制完成后两者无关**

---

## 3. 允许事项

1. ✅ 只改 `AX_Analysis/` 内文件
2. ✅ 改 `services/ai_server/tradingagents/`（A 股 vendor、prompt 等）
3. ✅ 将 AX_Analysis 整目录移到 **独立 git 仓库** 发布

---

## 4. v1 范围

- 用户：国内个人投资者
- LLM：DeepSeek、通义 CN、Kimi（Key 在 Worker / ai_server 环境）
- 产品页：向导、分析室、决策摘要、报告库、Admin
- 数据：A 股扩展在 `packages/ax_dataflows`，注入 ai_server config

---

## 5. 文档索引

- [docs/completeness-audit.md](./docs/completeness-audit.md) — **TradingAgents 全能力对照 + 遗漏 + 安全**
- [docs/engine-inventory.md](./docs/engine-inventory.md)
- [docs/product/wireframes.md](./docs/product/wireframes.md)

---

*AX_Analysis standalone · 2026-07-29*
