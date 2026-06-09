# Google Cloud Marketplace Deployment Guide

This guide describes the intended customer deployment path for SWGI on Google
Cloud Marketplace.

## Prerequisites

Customer requirements:

- GKE or GKE Enterprise / Anthos cluster.
- Namespace for SWGI, usually `swgi-system`.
- Network ingress protected by Cloud Armor and HTTPS Load Balancing when exposed
  outside the cluster.
- Access to create Deployments, Services, Secrets, ServiceAccounts, Roles, and
  RoleBindings in the SWGI namespace.
- Optional Cloud Storage bucket for receipt and audit export.
- Optional Cloud Logging and Cloud Monitoring collection for SWGI components.

Axis Systems requirements:

- Command Center running in the partner tenant.
- Customer organization created through self-serve signup or platform admin
  onboarding.
- Customer cluster registered in Command Center.
- Operator install config issued by Command Center:
  - `COMMAND_CENTER_URL`
  - `ORG_ID`
  - `CLUSTER_ID`
  - `OPERATOR_TOKEN`
  - `PUBLIC_SIGNING_KEY_PEM`

## Marketplace Deployment Package

The Marketplace package must collect customer deployment parameters and render
Kubernetes resources into one namespace.

Required parameters for SWGI:

- Application name.
- Namespace.
- Operator image.
- Enforcement image.
- Command Center URL.
- Organization ID.
- Cluster ID.
- Operator token or existing Kubernetes Secret reference.
- Public signing key PEM or existing Kubernetes Secret reference.
- Optional receipt archive bucket.
- Optional Cloud Logging and Cloud Monitoring toggles.

The scaffold in `marketplace/google` provides the package contract. Final
submission must replace image placeholders with Artifact Registry image paths
provided by the Google Cloud Marketplace onboarding flow.

## Customer Deployment Flow

1. Customer subscribes to SWGI on Google Cloud Marketplace.
2. Customer creates or selects a GKE / GKE Enterprise cluster.
3. Customer creates an org through Command Center self-serve signup, or Axis
   creates the org from platform admin.
4. Customer registers the cluster in Command Center.
5. Customer copies the generated Operator install config.
6. Marketplace deployer installs SWGI Operator and enforcement components into
   the customer namespace.
7. Operator heartbeats to Command Center and pulls pending executions.
8. Customer verifies status from Command Center:
   - cluster health
   - operator events
   - receipts
   - executions
   - audit logs

## Production Controls

- Do not store customer payloads in Command Center.
- Store operator tokens in Kubernetes Secrets.
- Store Command Center secrets in Secret Manager or equivalent.
- Enable JSON logs in production.
- Enable `GET /readyz` database readiness checks before serving traffic.
- Run Alembic migrations before production rollout.
- Archive receipts to customer-owned storage when required by customer policy.
- Keep Marketplace billing/metering credentials out of customer clusters unless
  Google Marketplace integration specifically requires customer-side reporting.

## Usage Reporting

Command Center queues Google Marketplace usage events in Postgres when governed
executions are allowed or modified. A partner-tenant reporter sends those events
to Google Service Control and marks each event as reported or failed.

Run the reporter from the partner tenant:

```bash
cd swgi-command-center
COMMAND_CENTER_URL="https://command-center.example" \
ADMIN_API_TOKEN="$ADMIN_API_TOKEN" \
GOOGLE_SERVICE_CONTROL_TOKEN="$GOOGLE_SERVICE_CONTROL_TOKEN" \
GOOGLE_MARKETPLACE_SERVICE_NAME="swgi.endpoints.partner-project.cloud.goog" \
python scripts/google_marketplace_reporter.py
```

`GOOGLE_SERVICE_CONTROL_TOKEN` must be issued for a Google service account that
is authorized to report usage for the Marketplace service. Do not store this
token in customer clusters.

## Rollback And Uninstall

The customer tenant package must support:

- removing SWGI Deployments and Services
- removing SWGI namespace-scoped RBAC
- preserving customer-owned Cloud Storage archives unless the customer deletes
  them
- revoking the cluster operator token from Command Center

Command Center should retain historical receipts and audit logs according to the
customer's retention policy.
