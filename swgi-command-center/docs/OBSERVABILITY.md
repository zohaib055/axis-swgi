# Command Center Observability

## Request IDs

Every response includes `x-request-id`. Incoming `x-request-id` is preserved;
otherwise Command Center generates a UUID.

## Metrics

Prometheus endpoint:

```text
GET /metrics
```

Initial metrics include:

```text
swgi_command_center_intents_total
swgi_command_center_scoped_intents_total
swgi_command_center_intent_latency_ms
```

## Audit Logs

Sensitive operations write to `audit_logs`, including org creation, org update,
API key creation/revocation/rotation, cluster registration, heartbeats, intent
submission, and execution status updates.

Read audit logs:

```text
GET /v1/audit-logs
GET /v1/audit-logs?org_id=axis
```

## Failed Auth

Failed auth attempts are recorded in `failed_auth_events` with reason, request
ID, and token hash when available.
