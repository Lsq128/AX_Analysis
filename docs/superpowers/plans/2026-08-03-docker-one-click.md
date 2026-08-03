# Docker One-Click (Dev/Demo) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `./scripts/up.sh` path that builds and starts Postgres + Redis + API + Worker + Web so a filled `.env` yields a working demo at `http://localhost:3000`.

**Architecture:** Extend existing `docker-compose.yml` with `api` / `worker` / `web` services. Shared `Dockerfile.python` for API and Worker; multi-stage `Dockerfile.web` for Next.js. Compose overrides host `localhost` URLs with Docker DNS names and shares an `ax_data` volume for local report storage. Thin `up.sh` / `down.sh` wrappers handle LLM-key preflight.

**Tech Stack:** Docker Compose, Python 3.12-slim, Node 22 Alpine / Next.js 15, existing `ax-api` / `ax-worker` entry points.

**Spec:** `docs/superpowers/specs/2026-08-03-docker-one-click-design.md`

## Global Constraints

- Dev/demo only — not production hardening (no Nginx/HTTPS).
- Secrets never baked into image layers; use compose `env_file: .env`.
- Preflight requires `.env` and at least one of `DEEPSEEK_API_KEY`, `DASHSCOPE_CN_API_KEY`, `MOONSHOT_API_KEY` non-empty.
- Compose must override `DATABASE_URL`, `REDIS_URL`, `API_PROXY_URL` to service hostnames.
- Keep host three-terminal workflow (`postgres`+`redis` only + local `ax-*`) working.
- MinIO stays on profile `storage`; `up.sh` does not start it.
- Do not commit unless the user explicitly asks (repo preference overrides plan “Commit” steps — stage changes and skip commit, or ask).

---

## File structure

| Path | Responsibility |
|------|----------------|
| `.dockerignore` | Keep build context small |
| `Dockerfile.python` | Image for `api` and `worker` |
| `Dockerfile.web` | Multi-stage Next.js image |
| `docker-compose.yml` | Add api/worker/web + `ax_data` volume |
| `scripts/check_demo_env.sh` | Preflight: `.env` + LLM key (testable) |
| `scripts/up.sh` | Call preflight → compose up → wait health → print URLs |
| `scripts/down.sh` | compose down; optional `--volumes` |
| `tests/test_check_demo_env.py` | Subprocess tests for preflight script |
| `README.md` | One-click section |
| `docs/getting-started.md` | Document demo path |
| `docs/deployment.md` | Note demo vs production |

---

### Task 1: Preflight script + tests

**Files:**
- Create: `scripts/check_demo_env.sh`
- Create: `tests/test_check_demo_env.py`

**Interfaces:**
- Consumes: path to env file via `AX_ENV_FILE` (default `.env` relative to repo root)
- Produces: exit `0` if OK; exit `1` with stderr message if missing file or no LLM key

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_check_demo_env.py
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_demo_env.sh"


def _run(env_file: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=str(ROOT),
        env={**os.environ, "AX_ENV_FILE": str(env_file)},
        capture_output=True,
        text=True,
    )


def test_missing_env_fails(tmp_path: Path) -> None:
    missing = tmp_path / "nope.env"
    result = _run(missing)
    assert result.returncode == 1
    assert "cp .env.example .env" in result.stderr


def test_empty_keys_fails(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("DEEPSEEK_API_KEY=\nJWT_SECRET=x\n", encoding="utf-8")
    result = _run(env)
    assert result.returncode == 1
    assert "LLM" in result.stderr or "API_KEY" in result.stderr


def test_deepseek_key_ok(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("DEEPSEEK_API_KEY=sk-test\n", encoding="utf-8")
    result = _run(env)
    assert result.returncode == 0, result.stderr


def test_quoted_and_spaced_key_ok(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text('MOONSHOT_API_KEY="sk-moon"\n', encoding="utf-8")
    result = _run(env)
    assert result.returncode == 0, result.stderr
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/eddie/coding/AX_Analysis && .venv/bin/pytest tests/test_check_demo_env.py -v`  
Expected: FAIL (script missing or not executable behavior)

- [ ] **Step 3: Implement `scripts/check_demo_env.sh`**

```bash
#!/usr/bin/env bash
# Preflight for demo docker one-click: require .env + one LLM key.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${AX_ENV_FILE:-$ROOT/.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  echo "Run: cp .env.example .env  # then fill at least one LLM API key" >&2
  exit 1
fi

get_key() {
  local name="$1"
  # last assignment wins; strip export, quotes, CR
  local line
  line="$(grep -E "^[[:space:]]*(export[[:space:]]+)?${name}=" "$ENV_FILE" | tail -n 1 || true)"
  [[ -z "$line" ]] && { echo ""; return; }
  local val="${line#*=}"
  val="${val%$'\r'}"
  val="${val#\"}"
  val="${val%\"}"
  val="${val#\'}"
  val="${val%\'}"
  # trim whitespace
  val="$(printf '%s' "$val" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  printf '%s' "$val"
}

if [[ -z "$(get_key DEEPSEEK_API_KEY)" \
   && -z "$(get_key DASHSCOPE_CN_API_KEY)" \
   && -z "$(get_key MOONSHOT_API_KEY)" ]]; then
  echo "No LLM API key found in $ENV_FILE" >&2
  echo "Set at least one of: DEEPSEEK_API_KEY, DASHSCOPE_CN_API_KEY, MOONSHOT_API_KEY" >&2
  exit 1
fi

exit 0
```

- [ ] **Step 4: Make executable and run tests**

Run:
```bash
chmod +x scripts/check_demo_env.sh
.venv/bin/pytest tests/test_check_demo_env.py -v
```
Expected: all PASS

- [ ] **Step 5: Commit (only if user asked)**

```bash
git add scripts/check_demo_env.sh tests/test_check_demo_env.py
git commit -m "feat: add demo env preflight for docker one-click"
```

---

### Task 2: Docker build context — `.dockerignore` + Dockerfiles

**Files:**
- Create: `.dockerignore`
- Create: `Dockerfile.python`
- Create: `Dockerfile.web`

**Interfaces:**
- Consumes: repo root as build context
- Produces: images runnable as `ax-api` / `ax-worker` / `npm run start` on port 3000

- [ ] **Step 1: Create `.dockerignore`**

```dockerignore
.git
.venv
**/__pycache__
**/*.pyc
.pytest_cache
.ruff_cache
.mypy_cache
node_modules
apps/web/node_modules
apps/web/.next
data
**/data
.env
.env.*
!.env.example
*.md
docs
tests
.cursor
agent-transcripts
**/terminals
```

Note: keep `README.md` out of runtime need; excluding `docs`/`tests` is fine for demo images. Do **not** exclude `pyproject.toml`, `packages/`, `apps/`, `services/`.

- [ ] **Step 2: Create `Dockerfile.python`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# System deps some wheels / akshare paths may need
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY packages ./packages
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker
COPY services/ai_server ./services/ai_server

RUN pip install --no-cache-dir -e ".[api,cn,storage]"

ENV PYTHONUNBUFFERED=1
ENV AX_DATA_ROOT=/data/ax
ENV AX_REPORT_LOCAL_ROOT=/data/ax/report_storage

# Default; compose overrides command
CMD ["ax-api"]
```

- [ ] **Step 3: Create `Dockerfile.web`**

```dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web/ ./
# Rewrites read API_PROXY_URL from next.config at server start; set for build consistency too
ARG API_PROXY_URL=http://api:8000
ENV API_PROXY_URL=$API_PROXY_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV API_PROXY_URL=http://api:8000
ENV PORT=3000

COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json
COPY --from=builder /app/next.config.ts ./next.config.ts
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000
CMD ["npm", "run", "start"]
```

- [ ] **Step 4: Sanity-check file presence (no full image build yet)**

Run:
```bash
test -f .dockerignore && test -f Dockerfile.python && test -f Dockerfile.web && echo OK
```
Expected: `OK`

- [ ] **Step 5: Commit (only if user asked)**

```bash
git add .dockerignore Dockerfile.python Dockerfile.web
git commit -m "feat: add Dockerfiles for api/worker and web demo stack"
```

---

### Task 3: Extend `docker-compose.yml`

**Files:**
- Modify: `docker-compose.yml`

**Interfaces:**
- Consumes: `Dockerfile.python`, `Dockerfile.web`, host `.env`
- Produces: services `api`, `worker`, `web` with health/depends_on; volume `ax_data`

- [ ] **Step 1: Replace `docker-compose.yml` with extended stack**

Keep existing postgres/redis/minio blocks; append api/worker/web and `ax_data`:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - ax_redis_data:/data

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ax
      POSTGRES_PASSWORD: ax
      POSTGRES_DB: ax_analysis
    ports:
      - "5432:5432"
    volumes:
      - ax_pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ax -d ax_analysis"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: axminio
      MINIO_ROOT_PASSWORD: axminio123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - ax_minio_data:/data
    profiles:
      - storage

  api:
    build:
      context: .
      dockerfile: Dockerfile.python
    command: ["ax-api"]
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql://ax:ax@postgres:5432/ax_analysis
      REDIS_URL: redis://redis:6379/0
      AX_JOB_STORE: redis
      AX_DATA_ROOT: /data/ax
      AX_REPORT_STORAGE: local
      AX_REPORT_LOCAL_ROOT: /data/ax/report_storage
      AX_AUTH_DEV_MODE: "true"
      AX_AUTH_ALLOW_HEADER: "true"
      AX_AUTH_DEV_LOGIN: "true"
    ports:
      - "8000:8000"
    volumes:
      - ax_data:/data/ax
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test:
        [
          "CMD",
          "python",
          "-c",
          "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)",
        ]
      interval: 5s
      timeout: 5s
      retries: 12
      start_period: 20s

  worker:
    build:
      context: .
      dockerfile: Dockerfile.python
    command: ["ax-worker"]
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql://ax:ax@postgres:5432/ax_analysis
      REDIS_URL: redis://redis:6379/0
      AX_JOB_STORE: redis
      AX_DATA_ROOT: /data/ax
      AX_REPORT_STORAGE: local
      AX_REPORT_LOCAL_ROOT: /data/ax/report_storage
    volumes:
      - ax_data:/data/ax
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      api:
        condition: service_healthy

  web:
    build:
      context: .
      dockerfile: Dockerfile.web
      args:
        API_PROXY_URL: http://api:8000
    environment:
      API_PROXY_URL: http://api:8000
      NEXT_PUBLIC_AUTH_ALLOW_HEADER: "true"
      NEXT_PUBLIC_DEV_USER_ID: demo
    ports:
      - "3000:3000"
    depends_on:
      api:
        condition: service_healthy

volumes:
  ax_redis_data:
  ax_pg_data:
  ax_minio_data:
  ax_data:
```

- [ ] **Step 2: Validate compose file**

Run: `docker compose -f docker-compose.yml config --quiet`  
Expected: exit 0 (may warn if `.env` missing — ensure a `.env` exists locally for this check, or create a throwaway; do not print secrets)

- [ ] **Step 3: Commit (only if user asked)**

```bash
git add docker-compose.yml
git commit -m "feat: add api/worker/web services to docker compose"
```

---

### Task 4: `up.sh` / `down.sh`

**Files:**
- Create: `scripts/up.sh`
- Create: `scripts/down.sh`

**Interfaces:**
- Consumes: `scripts/check_demo_env.sh`, Docker Compose project at repo root
- Produces: running stack; printed URLs; down stops services

- [ ] **Step 1: Implement `scripts/up.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

bash "$ROOT/scripts/check_demo_env.sh"

echo "Building and starting demo stack (postgres redis api worker web)..."
docker compose up --build -d postgres redis api worker web

echo "Waiting for API health..."
deadline=$((SECONDS + 180))
until curl -fsS "http://127.0.0.1:8000/health" >/dev/null 2>&1; do
  if (( SECONDS >= deadline )); then
    echo "Timed out waiting for API. Check: docker compose logs api worker" >&2
    exit 1
  fi
  sleep 2
done

echo ""
echo "Demo stack is up:"
echo "  Web  http://localhost:3000"
echo "  API  http://localhost:8000/health"
echo ""
echo "Stop with: ./scripts/down.sh"
```

- [ ] **Step 2: Implement `scripts/down.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "${1:-}" == "--volumes" ]]; then
  docker compose down --volumes
  echo "Stopped stack and removed volumes."
else
  docker compose down
  echo "Stopped stack (volumes kept). Use ./scripts/down.sh --volumes to wipe data."
fi
```

- [ ] **Step 3: chmod + smoke syntax**

```bash
chmod +x scripts/up.sh scripts/down.sh
bash -n scripts/up.sh && bash -n scripts/down.sh && echo OK
```
Expected: `OK`

- [ ] **Step 4: Optional live smoke (when Docker available and `.env` has a real key)**

```bash
./scripts/up.sh
curl -fsS http://127.0.0.1:8000/health
curl -fsS -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/
./scripts/down.sh
```
Expected: health JSON `{"status":"ok"}`; web HTTP 200 (or 307); down succeeds.

If build is too heavy for the session, skip live smoke and note it in the handoff.

- [ ] **Step 5: Commit (only if user asked)**

```bash
git add scripts/up.sh scripts/down.sh
git commit -m "feat: add docker demo up/down scripts"
```

---

### Task 5: Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/getting-started.md`
- Modify: `docs/deployment.md` (section 2 intro + pointer to one-click)

- [ ] **Step 1: Update README quick start**

Insert **before** the existing three-terminal block (keep the host workflow below):

```markdown
## 一键启动（Docker 演示）

需已安装 Docker，并准备好 `.env`（至少一个 LLM Key）：

```bash
cd AX_Analysis
cp .env.example .env   # 填写 DEEPSEEK_API_KEY 等
./scripts/up.sh        # → http://localhost:3000
./scripts/down.sh      # 停止（默认保留数据卷）
```

> 演示栈：Postgres + Redis + API + Worker + Web。生产部署见 [docs/deployment.md](./docs/deployment.md)。
```

Also update the structure tree to mention Dockerfiles / `scripts/up.sh`.

- [ ] **Step 2: Update `docs/getting-started.md`**

Add a new section near the top (after 前置条件), e.g. **「2a. Docker 一键演示」**:

```markdown
## 2a. Docker 一键演示（可选）

不装本机 Python/Node 时，可用：

```bash
cp .env.example .env   # 填 LLM Key
./scripts/up.sh
```

浏览器打开 http://localhost:3000 。停止：`./scripts/down.sh`。

这是 **dev/demo** 路径；日常改代码仍建议用下文的 venv + 三终端方式。
```

Renumber subsequent sections only if the doc already uses strict numbering that would collide — prefer inserting as `2a` to minimize churn.

- [ ] **Step 3: Update `docs/deployment.md` §2 intro**

Change the paragraph that says compose only provides infra to:

```markdown
### 2.0 Docker 一键演示（dev/demo）

```bash
cp .env.example .env   # 至少一个 LLM Key
./scripts/up.sh        # postgres + redis + api + worker + web
```

详见设计规格 `docs/superpowers/specs/2026-08-03-docker-one-click-design.md`。  
**生产请勿直接依赖该路径的默认鉴权（dev header / dev login）。**

当前也可只起基础设施容器（§2.1）；API / Worker / Web 可在宿主机运行（§2.3）。
```

- [ ] **Step 4: Commit (only if user asked)**

```bash
git add README.md docs/getting-started.md docs/deployment.md
git commit -m "docs: document docker demo one-click start"
```

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| `./scripts/up.sh` / `down.sh` | Task 4 |
| `.env` + LLM key preflight | Task 1 |
| Dockerfiles python + web | Task 2 |
| Compose api/worker/web + overrides + ax_data | Task 3 |
| Health / depends_on | Task 3 |
| Docs README / getting-started / deployment | Task 5 |
| MinIO not in default up | Task 3–4 (`up.sh` lists services explicitly) |
| Host workflow preserved | Task 3 (postgres/redis unchanged) |

## Plan self-review

- No TBD/placeholder steps; scripts and compose content inlined.
- Preflight key names match `.env.example` and the approved spec.
- Compose service DNS names (`postgres`, `redis`, `api`) match env overrides.
- SSE still works in demo because API is published on host `:8000` and web client defaults SSE to `http://localhost:8000` on localhost.
