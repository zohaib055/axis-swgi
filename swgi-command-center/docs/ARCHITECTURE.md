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
0003_prod_hardening
```

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
