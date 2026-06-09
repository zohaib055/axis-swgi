# SWGI on Google Cloud Marketplace Architecture

SWGI is deployed as a split-tenant product:

- Axis Systems manages the control plane in the partner / ISV tenant.
- Customers run enforcement components and protected workloads in their own GCP
  tenant.

This boundary keeps customer workloads, Kubernetes permissions, and network
controls inside the customer's environment while the Command Center provides
policy orchestration, signed Trust Receipts, audit visibility, and operational
metadata.

## Partner / ISV Tenant

Axis Systems managed services:

- Google Cloud Marketplace listing, entitlement, and metering integration.
- SWGI Command Center for tenant onboarding, user/role management, cluster
  registration, API keys, policy orchestration, execution status, and audit.
- Trust Receipt registry backed by Postgres metadata.
- Centralized observability through Cloud Logging and Cloud Monitoring.
- Secrets stored outside container images with Secret Manager or equivalent.

Recommended GCP services:

- Cloud Run or GKE for Command Center API.
- Cloud SQL for PostgreSQL.
- Artifact Registry for partner-owned container images.
- Cloud Load Balancing and Cloud Armor for public ingress.
- Cloud Logging, Cloud Monitoring, and alerting for operations.

## Customer Tenant

Customer managed services:

- Cloud Armor at the public edge when SWGI components are exposed externally.
- External HTTPS Load Balancer for public ingress.
- GKE or GKE Enterprise / Anthos cluster.
- SWGI Operator for policy sync, Trust Receipt verification, attestation, and
  execution status reporting.
- SWGI enforcement pods for intent enforcement, policy evaluation, and Trust
  Receipt generation.
- Customer workloads, applications, and services.
- Optional Cloud Storage bucket for customer-owned receipt and audit archive.
- Cloud Logging and Cloud Monitoring for customer-owned telemetry.

## Request And Metering Flow

```text
1. User / API request reaches the customer edge.
2. Cloud Armor applies DDoS, WAF, and IP filtering controls.
3. External HTTPS Load Balancer routes traffic to GKE / GKE Enterprise.
4. GKE / Anthos runs the SWGI Operator and enforcement pods.
5. SWGI evaluates intent, policy, and workload context.
6. Authorized customer workload executes.
7. SWGI generates a cryptographic Trust Receipt.
8. Receipt metadata and telemetry are written to customer storage/logging and
   reported to Command Center.
9. Marketplace metering receives licensed or usage-based consumption events
   when billing integration is enabled.
```

Billing and plan enforcement remain a separate product integration surface.
The current self-serve product can run without Marketplace billing while still
preserving the metering boundary required for Marketplace submission planning.

## Data Boundary

- Customer payloads stay in the customer tenant.
- Command Center stores metadata, decisions, hashes, receipts, audit records,
  org configuration, users, and cluster state.
- Operator tokens are scoped to one organization and one cluster.
- Trust Receipts are verified before any execution is applied in-cluster.
- Customer-side logs and archives remain customer controlled.

## Security Boundary

- Public traffic should terminate behind Cloud Armor and HTTPS load balancing.
- Command Center sessions use Postgres-backed auth and role checks.
- Org admins manage only their tenant resources.
- Platform admins can remotely inspect customer metadata, integrations, cluster
  status, receipts, audit logs, and operator events.
- In-cluster enforcement must reject unsigned, expired, cross-org, cross-cluster,
  or payload-mismatched executions.
