# AX_Analysis 功能清单

> 本文记录 **已实现** 的产品与工程能力，按用户可见功能 → 后端能力 → 运维能力组织。  
> 未实现项（在线支付、真 PDF、外部标的 API 等）见文末「规划外」。

---

## 1. 用户端功能（Web）

### 1.1 营销与合规

| 功能 | 路由 | 说明 |
|------|------|------|
| 营销首页 | `/` | Hero、能力介绍、方案定价 |
| 登录 | `/login` | Dev JWT 登录 / OAuth 入口 |
| OAuth 回调 | `/login/callback` | GitHub / OIDC 回跳 |
| 免责声明 | `/legal/disclaimer` | 非投资建议声明 |
| 数据说明 | `/legal/data` | 数据来源与局限 |

### 1.2 工作台

| 功能 | 路由 | 说明 |
|------|------|------|
| Dashboard | `/workspace` | 最近任务、快捷入口 |
| 发起分析（向导） | `/workspace/analyses/new` | 四步：方案 → 标的 → 时点 → LLM/确认 |
| 分析室 | `/workspace/analyses/[id]` | SSE 实时进度、Agent 状态、辩论时间线 |
| 决策报告 | `/workspace/analyses/[id]/report` | 评级徽章、结构化摘要卡、章节 Tab |
| 报告库 | `/workspace/reports` | 已完成报告列表、筛选 |
| 复盘中心 | `/workspace/memory` | 历史决策记忆、统计 |
| 我的套餐 | `/workspace/billing` | 当前套餐、点数、方案对比 |
| 管理后台 | `/workspace/admin` | 用户配额、套餐调整（仅 Admin） |

### 1.3 向导与分析室细节

**Step 1 — 分析方案**

- 7 种 Preset：快速诊股、技术趋势、资讯舆情、价值深挖、全面研判、深度推演、数字资产快览
- `free` 套餐锁定「深度推演」，UI 灰显 + 跳转套餐页
- 展示预估耗时、基础点数、分析师图标

**Step 2 — 标的**

- 手动输入 A 股 / 港股 / 美股代码
- **最近分析** chip（`GET /tickers/recent`）
- **搜索建议** 下拉（catalog + 历史，`GET /tickers/search`）

**Step 3 — 分析时点**

- 当前时点（推荐）或指定历史日期

**Step 4 — LLM 与确认**

- 三引擎：DeepSeek / 通义 CN / Kimi，各带快慢模型选择
- 点数 = 方案基础点 × 引擎系数
- 免责声明勾选后提交

**分析室**

- 五幕进度：分析师 → 研究辩论 → 交易 → 风控 → 决策
- Live Tab：当前 Agent 报告 Markdown 预览
- 辩论 Tab：多空时间线
- 日志 Tab：工具调用与消息流
- 完成态：决策预览、**Token/调用统计**（`JobStatsPanel`）、跳转报告库 / 再分析
- 失败态：友好错误文案 + **重试按钮**（不重复扣点，限可重试错误）

**报告页**

- 最终评级徽章（Buy/Hold/Sell 等）
- **交易提案 / 研究经理** 结构化摘要卡
- 章节 Tab 切换 Markdown
- OSS signed URL 单章下载（S3 模式）
- **Markdown 压缩包导出**（全章节 zip）

---

## 2. 后端能力（API + Worker）

### 2.1 鉴权与用户

| 能力 | 说明 |
|------|------|
| JWT 签发 | Dev `POST /auth/login` |
| OAuth | GitHub、通用 OIDC |
| 用户资料 | `GET /me`：配额、套餐、Admin 标记 |
| 生产门禁 | 可关闭 `X-User-Id` 回退与 Dev 登录 |

### 2.2 分析任务

| 能力 | 说明 |
|------|------|
| 创建任务 | `POST /analyses` → 202，Redis 入队 |
| 任务列表 / 详情 | 含 status、stats、error_code |
| SSE 进度 | `GET /analyses/{id}/events`，Redis Pub/Sub |
| 失败重试 | `POST /analyses/{id}/retry` |
| 套餐校验 | 创建时校验 Preset 是否允许 |
| 配额扣减 | Postgres 持久化点数（需 `DATABASE_URL`） |

### 2.3 报告

| 能力 | 说明 |
|------|------|
| 章节 manifest | `GET /analyses/{id}/report` |
| 章节 Markdown | `GET /analyses/{id}/report/{key}` |
| Signed URL | S3 模式单章下载 |
| Zip 导出 | 全章节 Markdown 打包 |
| 报告库 API | `GET /reports` 已完成列表 |

### 2.4 计费与 Admin

| 能力 | 说明 |
|------|------|
| 三档套餐 | free / standard / pro |
| 方案锁定 | free 不可用 deep Preset |
| 套餐列表 | `GET /billing/plans` |
| Admin 统计 | 用户数、任务数 |
| Admin 用户管理 | 列表、调整配额与套餐 |
| Admin API Key | 可选 `X-Admin-Key` |

### 2.5 复盘（Memory）

| 能力 | 说明 |
|------|------|
| 记忆条目 | 按用户读取 trading memory 日志 |
| 统计 | 条目数、标的分布 |

### 2.6 标的与 LLM

| 能力 | 说明 |
|------|------|
| 最近标的 | 用户历史去重 |
| 标的搜索 | 热门 catalog + 历史匹配 |
| LLM 目录 | Provider、模型列表 |
| 点数估算 | preset × provider 系数 |

### 2.7 安全与限流

| 能力 | 说明 |
|------|------|
| 任务归属校验 | 跨用户访问返回 404 |
| IP 限流 | `RateLimitMiddleware`，创建分析更严格 |
| 错误分类 | rate_limited / timeout / llm_error 等，驱动 UI 文案 |

---

## 3. 引擎与数据（Worker 内）

| 能力 | 包 / 模块 | 说明 |
|------|-----------|------|
| 多 Agent 流水线 | `services/ai_server` | 分析师 → 辩论 → 交易 → 风控 → PM |
| Stream 进度 | `ax_engine/progress.py` | 对齐原 CLI chunk 映射 |
| 每用户路径 | `ax_engine/paths.py` | memory / cache / logs 隔离 |
| A 股数据 | `ax_dataflows` | AKShare：OHLCV、指标、基本面、新闻 |
| 报告写入 | ai_server reporting | 本地或上传 S3 |
| 决策记忆 | ai_server Memory | stream 结束后 store_decision |
| 统计采集 | `ax_engine/stats.py` | LLM 调用、Token 写入 job.stats |

---

## 4. 分析与 Preset 对照

| Preset ID | 展示名 | 分析师 | 深度 | 基础点数 |
|-----------|--------|--------|------|----------|
| `quick` | 快速诊股 | market | 1 | 1.0 |
| `technical` | 技术趋势 | market | 1 | 1.0 |
| `news_sentiment` | 资讯舆情 | news, social | 1 | 1.5 |
| `value` | 价值深挖 | market, fundamentals | 3 | 2.0 |
| `full` | 全面研判 | 四维全选 | 3 | 2.5 |
| `deep` | 深度推演 | 四维全选 | 5 | 4.0 |
| `crypto` | 数字资产快览 | market, news, social | 1 | 1.0 |

套餐点数上限见 [architecture.md](./architecture.md) § 计费。

---

## 5. 套餐与功能门控（可选）

> **默认关闭。** `AX_BILLING_ENABLED=false`（或未设置）时不计费、不锁方案；Web 隐藏套餐/管理入口。  
> 设为 `true` 时启用下表行为。

| 套餐 | 月点数 | 深度推演 | 说明 |
|------|--------|----------|------|
| free（体验版） | 10 | ❌ | 新用户试用 |
| standard（标准版） | 50 | ✅ | 默认套餐 |
| pro（专业版） | 200 | ✅ | 高频用户 |

在线支付 **未接入**；升级由 Admin 后台或环境变量 `AX_DEFAULT_PLAN_ID` 控制（仅计费开启时）。

---

## 6. 测试与 CI

| 项 | 说明 |
|------|------|
| pytest | `tests/` 82+ 用例（API、Auth、Billing、P2 等） |
| Web build | `apps/web` Next.js 生产构建 |
| CI | 仓库根 `.github/workflows/ax-analysis-ci.yml` |

---

## 7. 规划外（未实现）

以下能力在审计中标记为 P3 或后续迭代，**当前版本不包含**：

- Stripe / 微信支付宝等在线支付与自助升级
- 真 PDF 报告导出（现为 Markdown zip）
- 外部实时标的搜索 API（如 Wind、同花顺）
- 自选 / 收藏列表
- Playwright E2E
- API/Worker 官方 Docker 镜像（基础设施 Docker 已有，见 [deployment.md](./deployment.md)）

---

*2026-07-29 · 随功能迭代更新*
