# SWGI Command Center

SWGI Command Center is the standalone control plane for Kubernetes-native
execution governance. It evaluates execution intent, emits signed Trust
Receipts through `swgi_core`, stores metadata in Postgres, exposes dashboard
APIs, and receives metadata-only Operator status.

OpenShift is supported, but the Command Center is not OpenShift-only.

## Responsibilities

- Accept Kubernetes execution intent metadata
- Manage multiple organizations
- Register Kubernetes/OpenShift/GKE/EKS/AKS clusters
- Generate org-scoped API keys and cluster-scoped Operator install tokens
- Evaluate deterministic policy decisions with `swgi_core`
- Generate signed Trust Receipts
- Persist metadata only in Postgres
- Expose receipt, usage, cluster, policy, and operator event APIs
- Provide control-plane data for the future dashboard

## Privacy Boundary

The Command Center must never store raw prompts, raw outputs, customer payloads,
secrets, container logs, environment variable values, or sensitive workload
data. It stores proof and metadata only: identifiers, hashes, decisions,
timestamps, policy IDs, signatures, status, and usage counts.

## Local Run

```bash
cd swgi-command-center
poetry install
cp .env.example .env
poetry run uvicorn app.main:app --reload --port 8081
```

`DATABASE_URL`, `ADMIN_API_TOKEN`, `VIEWER_API_TOKEN`, `API_KEY_HASH_SECRET`,
and `SIGNING_KEY_PATH` are required. Postgres is the only supported Command
Center metadata store.

`DATABASE_URL` may use either `postgresql://`, `postgresql+psycopg://`, or
`postgresql+psycopg2://`; Command Center normalizes these to the `psycopg` v3
driver used by the app and Alembic.

## Database Migrations

Command Center uses Alembic for Postgres migrations.

```bash
cd swgi-command-center
poetry run alembic upgrade head
```

When `RUN_DB_MIGRATIONS=true`, the app applies `alembic upgrade head` during
startup.

## Production Onboarding Flow

Platform admin creates an org:

```bash
curl -X POST http://localhost:8081/v1/orgs \
  -H "Authorization: Bearer $ADMIN_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{"org_id":"axis","display_name":"Axis","plan_code":"business"}'
```

Platform admin or org admin creates an org API key:

```bash
curl -X POST http://localhost:8081/v1/orgs/axis/api-keys \
  -H "Authorization: Bearer $ADMIN_API_TOKEN" \
  -H "content-type: application/json" \
  -d '{"key_name":"axis-admin","role":"org_admin"}'
```

Org admin registers a cluster:

```bash
curl -X POST http://localhost:8081/v1/orgs/axis/clusters \
  -H "Authorization: Bearer $ORG_ADMIN_TOKEN" \
  -H "content-type: application/json" \
  -d '{"cluster_id":"axis-prod-gke-001","display_name":"Axis GKE Prod","runtime":"gke"}'
```

The cluster registration response returns the install configuration for the
in-cluster Operator:

```text
COMMAND_CENTER_URL
ORG_ID
CLUSTER_ID
OPERATOR_TOKEN
PUBLIC_SIGNING_KEY_PEM
```

The Operator uses its cluster-scoped token to send heartbeats and enforcement
events:

```bash
curl -X POST http://localhost:8081/v1/operator/heartbeat \
  -H "Authorization: Bearer $OPERATOR_TOKEN" \
  -H "content-type: application/json" \
  -d '{
    "org_id":"axis",
    "cluster_id":"axis-prod-gke-001",
    "namespace":"swgi-system",
    "operator_version":"0.1.0",
    "health":"healthy"
  }'
```

Tenancy rules:

- `platform_admin` can manage all orgs.
- `platform_viewer` can read all orgs.
- `org_admin` can manage one org.
- `org_viewer` can read one org.
- `operator` can report and read only its registered cluster.

## Tests

```bash
cd swgi-command-center
poetry run pytest
```

## Initial APIs

- `GET /v1/health`
- `GET /readyz`
- `POST /v1/orgs`
- `GET /v1/orgs`
- `GET /v1/orgs/{org_id}`
- `PATCH /v1/orgs/{org_id}`
- `POST /v1/orgs/{org_id}/api-keys`
- `GET /v1/orgs/{org_id}/api-keys`
- `DELETE /v1/orgs/{org_id}/api-keys/{api_key_id}`
- `POST /v1/orgs/{org_id}/api-keys/{api_key_id}/rotate`
- `POST /v1/orgs/{org_id}/clusters`
- `GET /v1/orgs/{org_id}/clusters`
- `GET /v1/orgs/{org_id}/clusters/{cluster_id}`
- `POST /v1/operator/heartbeat`
- `GET /v1/operator/executions/pending`
- `POST /v1/operator/executions/{execution_id}/status`
- `POST /v1/intents`
- `GET /v1/receipts`
- `GET /v1/receipts/{receipt_id}`
- `GET /v1/usage`
- `GET /v1/plans`
- `GET /v1/clusters`
- `GET /v1/policies`
- `GET /v1/operator-events`
- `POST /v1/operator-events`
- `GET /v1/audit-logs`

## Production Docs

- Operator contract: `docs/OPERATOR_CONTRACT.md`
- Deployment: `docs/DEPLOYMENT.md`
- Observability: `docs/OBSERVABILITY.md`
- Security: `docs/SECURITY.md`
- UI build prompt: `LOVABLE_PROMPT.md`
