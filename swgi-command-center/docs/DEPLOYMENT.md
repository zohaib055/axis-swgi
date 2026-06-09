# Command Center Deployment

## Local Docker Compose

Generate a local signing key if one does not exist:

```bash
cd swgi-command-center
poetry run python - <<'PY'
from pathlib import Path
from swgi_core import generate_private_key_pem
path = Path("data/input/signing_key_ed25519.pem")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(generate_private_key_pem(), encoding="utf-8")
PY
```

Start local Postgres and Command Center:

```bash
docker compose up --build
```

## Production Runtime

Required environment variables:

```text
DATABASE_URL
ADMIN_API_TOKEN
VIEWER_API_TOKEN
API_KEY_HASH_SECRET
SIGNING_KEY_PATH
COMMAND_CENTER_URL
```

Use a secrets manager for tokens and signing keys. Do not bake secrets into
container images.

## GCP Partner Tenant Runtime

For Google Cloud Marketplace, run Command Center in the Axis Systems managed
partner tenant:

- Cloud Run or GKE for the Command Center API.
- Cloud SQL for PostgreSQL.
- Secret Manager or equivalent for tokens, cookie secrets, hash secrets, and
  signing keys.
- Artifact Registry for production images.
- External HTTPS Load Balancer and Cloud Armor for public ingress.
- Cloud Logging for JSON application logs.
- Cloud Monitoring for health, readiness, latency, failed auth, and heartbeat
  freshness alerts.

Command Center remains the source of truth for customer orgs, users, roles,
cluster registration, API keys, Trust Receipts, audit logs, operator events, and
execution status.

Customer GKE / GKE Enterprise deployment details are documented in
`../../docs/google-cloud-marketplace/DEPLOYMENT_GUIDE.md`.

Google Marketplace usage reporting is intentionally run as a partner-tenant
external worker. See `scripts/google_marketplace_reporter.py` for the reporting
job that drains Command Center usage events and calls Google Service Control.

## Health Checks

- `GET /healthz`: process health
- `GET /readyz`: database readiness
- `GET /metrics`: Prometheus metrics

## Migrations

Run migrations before serving traffic:

```bash
poetry run alembic upgrade head
```

The app can also run migrations on startup with `RUN_DB_MIGRATIONS=true`.
