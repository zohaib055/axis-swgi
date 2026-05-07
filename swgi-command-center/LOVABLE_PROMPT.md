# Loveable Prompt: SWGI Command Center UI

Build a production-grade SaaS dashboard for **SWGI Command Center for Kubernetes
Execution Governance**.

SWGI Command Center is a multi-tenant control plane. It manages organizations,
registered Kubernetes/OpenShift/GKE/EKS/AKS clusters, signed Trust Receipts,
execution handoff to in-cluster Operators, usage metering, audit logs, API keys,
and operator health.

Design style:

- Quiet enterprise SaaS, security/compliance focused
- Dense but clean operational dashboard
- No marketing landing page
- First screen is the actual Command Center dashboard
- Use a left sidebar navigation
- Use compact tables, filters, status badges, and detail drawers
- Avoid oversized hero sections and decorative gradients

Navigation:

- Dashboard
- Organizations
- Clusters
- Receipts
- Executions
- Usage & Billing
- Policies
- Operator Events
- API Keys
- Audit Logs
- Settings

Core screens:

1. Dashboard
   - total executions
   - ALLOW / DENY / MODIFY counts
   - active clusters
   - degraded/disconnected operators
   - monthly usage against plan
   - recent receipts
   - recent operator events

2. Organizations
   - table of orgs with status, plan, cluster count, monthly executions
   - create org modal
   - org detail page with tabs for clusters, users/API keys, usage, receipts

3. Clusters
   - runtime filter: Kubernetes, OpenShift, GKE, EKS, AKS, on-prem
   - health/status badges
   - last heartbeat
   - operator version
   - registration detail view showing install config fields:
     COMMAND_CENTER_URL, ORG_ID, CLUSTER_ID, OPERATOR_TOKEN, PUBLIC_SIGNING_KEY_PEM
   - hide token by default and show copy buttons

4. Receipts
   - metadata-only receipt table
   - filters by org, cluster, namespace, workload, decision, policy, date
   - receipt detail drawer showing signature status, payload hash, expiry,
     decision, policy, operator enforcement status
   - never show raw customer payloads

5. Executions
   - pending/running/succeeded/failed/rejected status tabs
   - show execution_id, receipt_id, cluster, namespace, workload, action,
     payload_hash, created_at, updated_at
   - detail drawer with receipt metadata and operator status history

6. Usage & Billing
   - executions by org, cluster, namespace
   - allowed executions, denied attempts, modified executions
   - plan limits and over-limit state
   - billing period selector

7. API Keys
   - org-scoped API keys
   - role badges: org_admin, org_viewer, operator
   - created, last used, expires, status
   - create, revoke, rotate actions
   - show generated token once in a secure modal

8. Operator Events
   - table of enforcement status reports
   - filters by org, cluster, namespace, workload, receipt
   - highlight failed/rejected events

9. Audit Logs
   - immutable audit timeline
   - filters by org, actor role, action, resource type, outcome, request id

10. Settings
   - signing key public fingerprint
   - data retention policy
   - rate limit settings
   - metadata-only security statement

API assumptions:

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
- `POST /v1/intents`
- `GET /v1/receipts`
- `GET /v1/receipts/{receipt_id}`
- `GET /v1/operator/executions/pending`
- `POST /v1/operator/executions/{execution_id}/status`
- `GET /v1/usage`
- `GET /v1/plans`
- `GET /v1/clusters`
- `GET /v1/policies`
- `GET /v1/operator-events`
- `POST /v1/operator-events`
- `GET /v1/audit-logs`

Use mock data first, but structure the app so API integration can be wired later.
All UI copy must reinforce: metadata-only, signed Trust Receipts, tenant
isolation, and Operator-enforced Kubernetes execution governance.
