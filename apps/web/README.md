# apps/web

Next.js 工作台（App Router + Tailwind v4）。功能清单见 **[docs/features.md](../../docs/features.md)**。

## 页面路由

| 路由 | 说明 |
|------|------|
| `/` | 营销首页 |
| `/login` | 登录 / OAuth |
| `/legal/disclaimer` · `/legal/data` | 合规页 |
| `/workspace` | Dashboard |
| `/workspace/analyses/new` | 四步分析向导 |
| `/workspace/analyses/[id]` | 分析室（SSE） |
| `/workspace/analyses/[id]/report` | 决策报告 + zip 导出 |
| `/workspace/reports` | 报告库 |
| `/workspace/memory` | 复盘中心 |
| `/workspace/billing` | 我的套餐 |
| `/workspace/admin` | 管理后台 |

## 开发

```bash
cd apps/web
cp .env.local.example .env.local
npm install
npm run dev
# http://localhost:3000
```

需 API 已启动（默认 `http://localhost:8000`）。浏览器请求经 `next.config` rewrite 代理到后端。

## 环境变量

| 变量 | 说明 |
|------|------|
| `API_PROXY_URL` | 后端地址（rewrites） |
| `NEXT_PUBLIC_DEV_USER_ID` | Dev 用户 ID |
| `NEXT_PUBLIC_AUTH_ALLOW_HEADER` | 生产设为 `false` |

## 构建

```bash
npm run build && npm start
```
