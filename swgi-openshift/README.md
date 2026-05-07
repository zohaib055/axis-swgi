# SWGI OpenShift

`swgi-openshift` is the OpenShift-compatible runtime package for SWGI. The
standalone product control plane now lives in `../swgi-command-center`; this
package remains focused on OpenShift deployment, Helm configuration, Routes,
service accounts, and compatibility validation.

For new standalone product work, start with `swgi-command-center`. Use
`swgi-openshift` when the target runtime is OpenShift.

## Included
- FastAPI service using `swgi_core`
- legacy SQLite receipt store for local compatibility
- Postgres backend path for production-like OpenShift deployments
- Versioned endpoints:
  - `POST /v1/authorize`
  - `GET /v1/receipts/{receipt_id}`
  - `GET /v1/receipts`
  - `GET /v1/receipts/export.csv`
  - `GET /v1/health`
  - `GET /healthz`
  - `GET /metrics`
- UBI minimal Dockerfile with OpenShift-compatible metadata labels
- Helm chart with Deployment, Service, Route, ConfigMap, Secret, ServiceAccount, Role, and RoleBinding

## Local run

### 1. Prepare environment
```bash
cd /Users/zohaibahmad/Desktop/swgi-redhat/swgi-openshift
cp .env.example .env
openssl genpkey -algorithm Ed25519 -out data/input/signing_key_ed25519.pem
```

Update `.env`:
- replace `ADMIN_API_TOKEN` and `VIEWER_API_TOKEN`
- keep `SWGI_MODE=production`
- keep `RECEIPT_STORE_BACKEND=sqlite`
- change `RECEIPT_DB_PATH` only if you want the SQLite file elsewhere

Local signing key:
- generate `data/input/signing_key_ed25519.pem` locally before starting the app
- container and Helm deployments can still override `SIGNING_KEY_PATH` to `/tmp/secrets/signing_key_ed25519.pem`

### 2. Install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Start the API
```bash
python -m app.main
```

The service listens on `http://localhost:8080`.

## Auth model
- `admin` token can call `POST /v1/authorize`
- `viewer` token can read receipts
- send tokens as `Authorization: Bearer <token>`

## Example requests
Health:
```bash
curl http://localhost:8080/v1/health
```

Authorize:
```bash
curl -X POST http://localhost:8080/v1/authorize \
  -H "Authorization: Bearer change-admin-token" \
  -H "content-type: application/json" \
  -d '{
    "intent":"TEST",
    "context":{"env":"prod"},
    "action":"ai.infer",
    "authority":{"role":"admin"},
    "state":{"s":0},
    "workload_id":"workload-prod"
  }'
```

List receipts:
```bash
curl http://localhost:8080/v1/receipts \
  -H "Authorization: Bearer change-viewer-token"
```

Current storage note:
- Command Center uses Postgres only
- this OpenShift package still has SQLite for legacy local runs
- production-like OpenShift deployments should use `RECEIPT_STORE_BACKEND=postgres`

## Container build
```bash
cd /Users/zohaibahmad/Desktop/swgi-redhat
docker build -f swgi-openshift/Dockerfile -t swgi-openshift:0.1.0 .
podman tag swgi-openshift:0.1.0 registry.connect.redhat.com/axissystems/swgi-core:0.1.0
podman push registry.connect.redhat.com/axissystems/swgi-core:0.1.0
```

Registry note:
- The target repository is `registry.connect.redhat.com/axissystems/swgi-core:0.1.0`
- For standalone distribution, publish equivalent images to an SWGI-controlled registry
- Keep this image path only for OpenShift compatibility and certification workflows

## Helm deployment
```bash
helm upgrade --install swgi-openshift ./swgi-openshift/helm/swgi-openshift \
  --namespace swgi-system \
  --create-namespace \
  --set image.repository=registry.connect.redhat.com/axissystems/swgi-core \
  --set image.tag=0.1.0
```

See `docs/DEPLOYMENT.md` for deployment details.
