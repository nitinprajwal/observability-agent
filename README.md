# DevOps AI — Observability Agent

> Observability stack for the **DevOps AI** platform.
> Bundles an OTel Collector, a React SPA dashboard, Grafana, Loki, Tempo, and Prometheus into a single Docker image served over nginx on port **8085**.

---

## Architecture

```
DevopsAI Agent (devopsai-app + devopsai-agent)
    │  OTLP HTTP → :4318
    ▼
observability-agent  (this repo — OTel Collector + React SPA + nginx, port 8085)
    ├── traces  → observability-tempo:4317  (Grafana Tempo)
    ├── metrics → Prometheus pull :8889
    └── logs    → observability-loki:3100/otlp/v1/logs  (Grafana Loki)

Grafana (:3001 / :8085/api/grafana/)
    reads: Prometheus + Loki + Tempo
    SSO:   nginx auth_request → DevopsAI /api/auth/check → X-User-Email → auto-login
```

### Dashboard tabs

| Tab | Data sources |
|-----|-------------|
| Overview | Prometheus request rate, latency, error rate + PostgreSQL user stats |
| Agent Pipeline | Prometheus step counts + Tempo traces (user-scoped) |
| LLM Usage | Prometheus token histogram + Tempo latency |
| A2A Flows | Tempo (all service traces) + Prometheus A2A call rate |
| Sandbox | Jaeger `agent.step.*` spans from `agent_step_span` context manager |
| Logs | Loki `{service_name=~"devopsai.*"}` — level-indexed stream labels |

### Service naming

| Component | `service.name` | `service.namespace` |
|-----------|---------------|-------------------|
| Next.js app | `devopsai-app` | `devopsai` |
| LangGraph agent | `devopsai-agent` | `devopsai` |

---

## Local development

```bash
# From the parent repo root (nitroncore-devops)
make obs   # starts 5 containers — OTel Collector, Prometheus, Loki, Tempo, Grafana
```

| Service | URL | Notes |
|---------|-----|-------|
| Observability dashboard | http://localhost:8085 | React SPA + OTel Collector |
| Grafana (via auth proxy) | http://localhost:8085/api/grafana/ | DevopsAI SSO |
| Grafana (direct) | http://localhost:3001 | admin / nitronode-obs-dev |
| OTel Collector HTTP | http://localhost:4318 | OTLP HTTP ingestion |
| OTel Collector gRPC | localhost:4317 | OTLP gRPC ingestion |

All service configs (OTel Collector, Prometheus, Loki, Tempo, Grafana) are inline `configs:` blocks in `docker-compose.yml` — no external config files are required.

---

## Building & pushing the Docker image

The ECR push is handled by a GitHub Actions workflow on push to `feature/nitin_observability-agent`:

```
ECR: 495660672838.dkr.ecr.us-west-1.amazonaws.com/devops-agents/observability-agent:latest
```

To build locally:

```bash
docker build -t observability-agent .
docker run -p 8085:8085 -p 4317:4317 -p 4318:4318 observability-agent
```

---

## OTel Collector config (`otel-collector-config.yaml`)

Key decisions:

- **No `namespace:` in Prometheus exporter** — prevents double-prefix on metric names (e.g. avoids `nitronode_nitronode_agent_step_count_total`).
- **`transform/logs` processor** — copies `severity_text → attributes["level"]` so Loki indexes it as the `level` stream label.
- **`resource` processor** — upserts `deployment.environment` and `service.namespace = "devopsai"` on every signal.
- **`debug` exporter** — enabled at `basic` verbosity; disable in production.

---

## Prometheus metrics (custom)

| Metric | Emitted by | Description |
|--------|-----------|-------------|
| `agent_step_count_total` | `apps/agent/src/instrumentation.py` | Count per tool step name |
| `agent_step_duration_ms` | `apps/agent/src/instrumentation.py` | Histogram of step duration |
| `gen_ai_client_token_usage_count/sum` | OpenLLMetry / traceloop-sdk | Bedrock input/output tokens |
| `gen_ai_client_operation_duration_seconds` | OpenLLMetry / traceloop-sdk | Bedrock call latency |
| `http_server_duration_milliseconds_count` | OTel HTTP auto-instrumentation | Next.js API route request count |

Host metrics use ratio values (0–1). PromQL examples:

```promql
# CPU utilisation %
(1 - avg(system_cpu_utilization_ratio{state="idle"})) * 100

# Memory utilisation %
(1 - sum(system_memory_utilization_ratio{state=~"free|buffered|cached|slab_reclaimable"})) * 100
```

---

## Loki configuration

Loki 3.x requires `limits_config.otlp_config` to promote OTLP resource attributes to indexed labels. Without this, `{service_name=~"devopsai.*"}` returns nothing.

The config is embedded as an inline block in `docker-compose.yml` under `loki_conf`.

---

## Production (K8s / ArgoCD)

- Accessible at `https://devops-agent.hdcss.com/observability` (auth-gated)
- Grafana auth: nginx-ingress `auth-url` → `/api/auth/check` → `X-User-Email` → Grafana `GF_AUTH_PROXY_HEADER_NAME`
- Helm templates: `charts/templates/observability/` (17 templates)

---

## A2A multi-agent example (`a2a-multi-agent-example/`)

A self-contained demo of the **Agent-to-Agent (A2A) Protocol** with OpenTelemetry cross-agent trace propagation. Five agents collaborate on an AI-powered development workflow:

| Agent | Port | Role |
|-------|------|------|
| Security Scanner | 8001 | Vulnerability scanning |
| Code Reviewer | 8002 | Code quality + MCP tools |
| Documentation Agent | 8003 | Docstring coverage |
| Dev Lead Agent | 8005 | Workflow orchestration |
| Developer Agent | 8006 | GPT-4o-mini code generation |

```bash
cd a2a-multi-agent-example
cp .env.example .env   # add OPENAI_API_KEY + TRACELOOP_API_KEY
uv sync --dev
uv run python test_a2a_complete.py
```

See [`a2a-multi-agent-example/README.md`](a2a-multi-agent-example/README.md) for full details.

---

## observability-app (`observability-app/`)

React + TypeScript SPA (Vite + Tailwind) that powers the dashboard at `:8085`.

```bash
cd observability-app
npm install
npm run dev   # dev server at http://localhost:5173
npm run build # production build → dist/
```

The built `dist/` is served by nginx inside the Docker image.
