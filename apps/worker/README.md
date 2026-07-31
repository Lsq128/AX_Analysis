# apps/worker

Redis 队列消费者：调用 `ax_engine.run_analysis_job` 执行多 Agent 分析。

部署说明见 **[docs/deployment.md](../../docs/deployment.md)**。

## 启动

```bash
cd AX_Analysis
source .venv/bin/activate
pip install -e ".[cn,dev]"

export REDIS_URL=redis://localhost:6379/0
export DATABASE_URL=postgresql://ax:ax@localhost:5432/ax_analysis
ax-worker
```

内存模式：`export AX_JOB_STORE=memory`（无需 Postgres，调试用）。

## 与 API 联调

```bash
docker compose up -d redis postgres
# 终端 1: ax-worker
# 终端 2: ax-api
```

或：`./scripts/dev_stack.sh --memory`

## 流程

1. `BLPOP ax:queue:analysis`
2. job → `running`
3. `run_analysis_job` → stream 事件发布到 `ax:events:{job_id}`
4. 完成 → `report_path`、stats、memory；失败 → error_code

Per-user 路径：`AnalysisRequest.user_id` → `ax_engine.paths`。

## 环境要求

- Worker 进程需 LLM Key（`.env` 中 `DEEPSEEK_API_KEY` 等）
- A 股：`pip install -e ".[cn]"`（AKShare）
- 启动目录应为 `AX_Analysis/`（load_dotenv）
