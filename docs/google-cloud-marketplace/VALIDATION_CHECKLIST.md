# Google Cloud Marketplace Validation Checklist

This checklist keeps SWGI aligned with Google Cloud Marketplace technical
validation for Kubernetes/GKE offerings.

## Current Repo Status

| Area | Status | Evidence |
| --- | --- | --- |
| Split-tenant architecture | Ready | `docs/google-cloud-marketplace/ARCHITECTURE.md` |
| Self-serve signup | Ready | Command Center auth/signup routes and frontend flow |
| Postgres auth and roles | Ready | Command Center migrations through `0005_sales_readiness` |
| Customer cluster registration | Ready | Command Center onboarding and operator install config |
| Operator contract | Ready | `swgi-command-center/docs/OPERATOR_CONTRACT.md` |
| Customer GKE deployment guide | Ready | `docs/google-cloud-marketplace/DEPLOYMENT_GUIDE.md` |
| Marketplace package scaffold | Ready | `marketplace/google` |
| Application CR scaffold | Ready | `marketplace/google/templates/application.yaml` |
| Deployer schema scaffold | Ready | `marketplace/google/schema.yaml` |
| Usage metering event queue | Ready | `marketplace_usage_events` and `/v1/marketplace/google/*` APIs |
| Google usage reporter | Ready | `swgi-command-center/scripts/google_marketplace_reporter.py` |
| Billing / plan enforcement | Excluded by product scope | Usage reporting is integration-ready; plan enforcement remains separate |

## Marketplace Package Requirements

- Repository includes public package documentation and a clear deployment guide.
- Package can be represented as Kubernetes YAML or Helm.
- Package deploys an Application custom resource.
- Deploy-time parameters include namespace, app name, and image references.
- Resources are scoped to one namespace unless elevated privileges are explicitly
  required and documented.
- Runtime images are placeholders until Google Marketplace Artifact Registry
  image names are issued.
- Final deployer image must include `/data/schema.yaml`.
- Final deployer image must render the Kubernetes manifests and apply them to
  the selected GKE / GKE Enterprise cluster.
- Partner tenant must export pending usage events and report them through the
  Google Service Control API with production Marketplace credentials.
- Final image manifests must include the Google Marketplace service-name
  annotation required for new or updated GKE listings.

## GCP Partner Tenant Checklist

- Command Center deployed behind HTTPS.
- Cloud Armor configured for public ingress.
- Cloud SQL PostgreSQL configured with backups.
- Alembic migrations run to current head.
- Secrets stored in Secret Manager or equivalent.
- Cloud Logging enabled for JSON application logs.
- Cloud Monitoring configured for API health, readiness, latency, failed auth,
  and operator heartbeat freshness.
- Artifact Registry contains production images.

## Customer Tenant Checklist

- Customer GKE / GKE Enterprise cluster exists.
- `swgi-system` namespace created by deployer or selected by customer.
- Operator token stored as a Kubernetes Secret.
- Public signing key stored as ConfigMap or Secret according to customer policy.
- SWGI Operator heartbeats to Command Center.
- Enforcement pods reject invalid, expired, cross-org, cross-cluster, or
  payload-mismatched executions.
- Cloud Logging / Monitoring collection configured when customer requires it.
- Cloud Storage archive configured when customer requires customer-owned receipt
  retention.

## Validation Commands

Backend:

```bash
cd swgi-command-center
poetry run alembic upgrade head
PYTHONPATH="$PWD:../swgi_core" poetry run pytest
```

Frontend:

```bash
cd command-center-frontend
npm run build
```

Marketplace scaffold:

```bash
kubectl apply --dry-run=client --validate=false -f marketplace/google/templates/application.yaml
kubectl apply --dry-run=client --validate=false -f marketplace/google/templates/operator.yaml
```

The Marketplace scaffold uses placeholder substitution values. Replace all
`${...}` values before running real cluster validation.
