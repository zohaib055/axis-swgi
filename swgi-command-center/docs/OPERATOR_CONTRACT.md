# SWGI Operator Contract

The Operator is the only component that applies Kubernetes/OpenShift actions.
Command Center issues signed authorization artifacts and records metadata only.

## Install Configuration

Cluster registration returns:

```text
COMMAND_CENTER_URL
ORG_ID
CLUSTER_ID
OPERATOR_TOKEN
PUBLIC_SIGNING_KEY_PEM
```

The Operator stores `OPERATOR_TOKEN` as a cluster secret and uses
`PUBLIC_SIGNING_KEY_PEM` to verify Trust Receipts.

## Heartbeat

```http
POST /v1/operator/heartbeat
Authorization: Bearer <OPERATOR_TOKEN>
```

```json
{
  "org_id": "axis",
  "cluster_id": "axis-prod-gke-001",
  "namespace": "swgi-system",
  "operator_version": "0.1.0",
  "health": "healthy"
}
```

## Pull Pending Executions

```http
GET /v1/operator/executions/pending?limit=25
Authorization: Bearer <OPERATOR_TOKEN>
```

The response is scoped to the Operator token's `org_id` and `cluster_id`.

Each item includes:

```text
execution_id
receipt_id
org_id
cluster_id
namespace
workload_id
action
decision
payload_hash
receipt_metadata
status
```

## Enforcement Rules

Before applying any object, the Operator must verify:

- receipt signature is valid using `PUBLIC_SIGNING_KEY_PEM`
- `decision` is `ALLOW` or `MODIFY`
- receipt is not expired
- `org_id` matches install config
- `cluster_id` matches install config
- namespace and workload match the target object
- recomputed payload hash matches `payload_hash`

If any check fails, the Operator must reject the execution.

## Submit Execution Status

```http
POST /v1/operator/executions/{execution_id}/status
Authorization: Bearer <OPERATOR_TOKEN>
```

```json
{
  "status": "succeeded",
  "error_code": null,
  "error_summary": null
}
```

Allowed statuses:

```text
claimed
running
succeeded
failed
rejected
```

## Operator Events

```http
POST /v1/operator-events
Authorization: Bearer <OPERATOR_TOKEN>
```

```json
{
  "org_id": "axis",
  "receipt_id": "receipt-id",
  "cluster_id": "axis-prod-gke-001",
  "namespace": "default",
  "workload_id": "workload-1",
  "enforcement_status": "succeeded",
  "operator_version": "0.1.0",
  "error_code": null,
  "error_summary": null
}
```
