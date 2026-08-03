# Docker one-click (dev/demo) design

**Status:** Approved 2026-08-03  
**Scope:** Development / demo one-click stack start — not production hardening.

## Problem

Today `docker-compose.yml` only runs Postgres / Redis / optional MinIO. API, Worker, and Web must be started on the host in three terminals. There is no Dockerfile and no single command that brings up a usable demo.

## Goals

1. One command starts the full demo stack after `.env` exists with at least one LLM key.
2. Browser entry: `http://localhost:3000`.
3. Keep the existing host-based three-terminal workflow for day-to-day development.
4. Do not bake secrets into image layers; inject via `--env-file` / compose `env_file`.

## Non-goals

- Production HTTPS / Nginx reverse proxy
- Kubernetes / multi-host orchestration
- Forcing MinIO into the default one-click path
- Replacing systemd / host deploy docs as the production path

## Decision

Extend the existing `docker-compose.yml` and add thin wrapper scripts.

### User flow

```bash
cp .env.example .env   # fill at least one LLM API key
./scripts/up.sh        # validate → build → up -d
# → http://localhost:3000
./scripts/down.sh      # compose down (volumes kept)
./scripts/down.sh --volumes  # also remove data volumes
```

### Compose services

| Service | Role | Host ports |
|---------|------|------------|
| postgres | Existing | 5432 |
| redis | Existing | 6379 |
| api | FastAPI (`ax-api`) | 8000 |
| worker | Queue consumer (`ax-worker`) | — |
| web | Next.js (`next start`) | **3000** (primary UX) |

Optional MinIO remains under compose profile `storage` and is **not** started by `up.sh`.

### Networking / env overrides

Inside the compose network, force:

- `DATABASE_URL=postgresql://ax:ax@postgres:5432/ax_analysis`
- `REDIS_URL=redis://redis:6379/0`
- `API_PROXY_URL=http://api:8000`

These overrides must win over host `.env` values that use `localhost`, so containers do not try to reach Postgres/Redis/API on the container loopback.

Demo auth defaults (compose `environment`, aligned with `.env.example` local mode):

- `AX_AUTH_DEV_MODE=true`
- `AX_AUTH_ALLOW_HEADER=true`
- `AX_AUTH_DEV_LOGIN=true`

Report storage for demo:

- `AX_REPORT_STORAGE=local`
- `AX_DATA_ROOT=/data/ax`
- `AX_REPORT_LOCAL_ROOT=/data/ax/report_storage`
- Shared named volume `ax_data` mounted on **both** api and worker at `/data/ax` so completed reports are readable by API.

### Images / files

| Path | Purpose |
|------|---------|
| `Dockerfile.python` | Shared image for api + worker |
| `Dockerfile.web` | Multi-stage Next.js production image |
| `.dockerignore` | Exclude `.venv`, `node_modules`, `.git`, local `data/`, caches |
| `scripts/up.sh` | Preflight + `docker compose up --build -d` + wait/print URLs |
| `scripts/down.sh` | `docker compose down` (+ optional `--volumes`) |
| `docker-compose.yml` | Add api / worker / web services |

**Python image**

- Base: `python:3.12-slim`
- Install: `pip install --no-cache-dir -e ".[api,cn,storage]"`
- Workdir: `/app`
- Compose sets `command`: `ax-api` or `ax-worker`

**Web image**

- Build stage: `node:22-alpine`, `npm ci` / `npm run build` in `apps/web`
- Run stage: `next start --port 3000`
- Runtime `API_PROXY_URL=http://api:8000`
- Use production `next start` for demo stability (not `next dev`)

### `scripts/up.sh` preflight

1. Fail if `.env` missing → print `cp .env.example .env` hint.
2. Fail if none of `DEEPSEEK_API_KEY`, `DASHSCOPE_CN_API_KEY`, `MOONSHOT_API_KEY` is non-empty.
3. Run `docker compose up --build -d` for postgres, redis, api, worker, web.
4. Wait until API `GET /health` succeeds (or timeout with log hint).
5. Print Web and API URLs.

### Health & depends_on

- postgres: existing `pg_isready` healthcheck
- api: healthcheck against `http://127.0.0.1:8000/health` (endpoint already exists)
- worker: `depends_on` postgres (healthy), redis, api (healthy)
- web: `depends_on` api (healthy)

### Docs

- README: add one-click Docker section as the fastest path for demo.
- `docs/getting-started.md` / `docs/deployment.md`: document the flow; label as **dev/demo**; keep host + infra-only compose as the daily-dev and production-oriented paths.

## Compatibility

Host workflow remains valid:

```bash
docker compose up -d postgres redis
# terminals: ax-worker | ax-api | ./scripts/dev_stack.sh web
```

## Acceptance

1. With a valid `.env` containing one LLM key, `./scripts/up.sh` brings up all five core services without manual process starts.
2. `http://localhost:3000` loads the web app; API health is reachable at `http://localhost:8000/health`.
3. Missing `.env` or missing all LLM keys causes a clear non-zero exit before build/up.
4. `./scripts/down.sh` stops containers; data volumes persist unless `--volumes` is passed.
5. Existing `docker compose up -d postgres redis` + host `ax-*` workflow still works.
