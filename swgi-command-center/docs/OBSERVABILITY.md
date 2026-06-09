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

## Google Cloud Observability Mapping

For the Google Cloud Marketplace architecture:

- Command Center emits JSON logs into Cloud Logging from the partner tenant.
- Customer tenant SWGI Operator and enforcement pods emit logs into the
  customer's Cloud Logging pipeline when enabled.
- Command Center metrics should be scraped or exported into Cloud Monitoring.
- Customer clusters should alert on stale Operator heartbeat, failed execution
  status, rejected receipt verification, and enforcement pod availability.
- Receipt and audit exports can be copied to customer-owned Cloud Storage when a
  customer requires tenant-local retention.
