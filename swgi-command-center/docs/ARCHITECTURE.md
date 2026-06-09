# Command Center Architecture

SWGI Command Center is organized as a modular backend with stable API contracts
for OpenShift packaging and the SWGI Operator.

## Layers

```text
app/main.py
  FastAPI application assembly, middleware, and route registration.

app/modules/*/
  Feature-owned schemas and ORM model re-exports.

app/orm.py
  SQLAlchemy ORM mappings for the Postgres schema managed by Alembic.

app/db.py
  Repository layer. Runtime database access goes through SQLAlchemy ORM
  operations, not hand-written SQL strings.

app/database.py
  Engine/session factory and transaction scope.

app/receipts.py
  Metadata-only receipt shaping.

app/auth.py + app/security.py
  Role enforcement, token generation, token hashing, and scope checks.
```

## Modules

```text
modules/orgs
  organizations and tenant lifecycle

modules/clusters
  cluster registration and status

modules/api_keys
  org and Operator API keys

modules/receipts
  intent intake and Trust Receipt API schemas

modules/executions
  Operator execution handoff

modules/operators
  Operator heartbeat and events

modules/billing
  plans and usage metering

modules/audit
  audit and failed-auth records
```

Each module owns:

- `schemas.py`: Pydantic request/response contracts
- `models.py`: feature-specific ORM model re-exports from `app.orm`

`app/models.py` remains as a compatibility barrel so existing imports keep
working while route files can gradually move into module-specific routers.

## Database

Postgres schema changes are versioned by Alembic. Runtime reads and writes use
SQLAlchemy ORM sessions through `CommandCenterStore`.

Current head:

```text
0006_partner_launch_integrations
```

Current production tables include organizations, clusters, receipts, executions,
operator events, marketplace usage events, audit logs, failed auth events,
users, sessions, onboarding tokens, invite tokens, reset tokens, and API keys.

## API Stability

The public API shape remains aligned with the standalone flow:

```text
Command Center
  -> evaluates intent
  -> signs metadata-only Trust Receipt
  -> stores metadata in Postgres
  -> queues ALLOW/MODIFY execution for Operator

Operator
  -> heartbeats to Command Center
  -> pulls pending executions
  -> verifies signature and payload_hash
  -> applies Kubernetes/OpenShift action
  -> reports status/events
```

## Google Cloud Marketplace Boundary

For Google Cloud Marketplace, SWGI uses a split-tenant architecture:

```text
Axis Systems partner tenant
  -> Google Cloud Marketplace listing and metering boundary
  -> Command Center
  -> Postgres Trust Receipt registry
  -> Cloud Logging / Cloud Monitoring

Customer tenant
  -> Cloud Armor
  -> External HTTPS Load Balancer
  -> GKE / GKE Enterprise / Anthos
  -> SWGI Operator and enforcement pods
  -> customer workloads
  -> optional customer-owned Cloud Storage archive
```

Customer workloads and Kubernetes permissions remain in the customer tenant.
Command Center stores metadata, hashes, decisions, receipts, audit records, and
operator status. Billing and plan enforcement are intentionally isolated behind
the Marketplace metering boundary so the product can run self-serve without
coupling runtime enforcement to commercial plumbing.

Detailed GCP Marketplace architecture and validation notes live in
`../../docs/google-cloud-marketplace`.

## Intel Partner Boundary

For Intel partner positioning, SWGI runs as the governance and evidence layer
for Kubernetes workloads on Intel-based cloud, private cloud, and edge
infrastructure.

```text
Customer Intel infrastructure
  -> Intel Xeon worker nodes
  -> optional Intel TDX capable node pools
  -> Kubernetes / OpenShift / GKE / edge cluster
  -> SWGI Operator and enforcement pods
  -> signed Trust Receipts
```

Intel TDX attestation is treated as validated policy input and receipt metadata
when a customer enables confidential workload controls. SWGI must continue to
keep payloads in the customer environment while storing only metadata, hashes,
decisions, receipts, audit records, and operator state in Command Center.

Detailed Intel partner architecture and validation notes live in
`../../docs/intel-partner`.
