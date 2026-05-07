# SWGI Command Center Security Notes

## Metadata-Only Boundary

Command Center must not store raw prompts, raw outputs, customer payloads,
secrets, container logs, environment variable values, or sensitive workload
data.

It stores identifiers, hashes, decisions, timestamps, policy IDs, signatures,
usage counts, operator status, and audit metadata.

## Tenant Isolation

Access is scoped by role:

- `platform_admin`: manage all orgs
- `platform_viewer`: read all orgs
- `org_admin`: manage one org
- `org_viewer`: read one org
- `operator`: report and read only its registered cluster

All receipt, usage, cluster, event, and execution APIs enforce org/cluster
scope in the API layer.

## Token Handling

API and Operator tokens are shown once at creation. Command Center stores only
HMAC-SHA256 token hashes using `API_KEY_HASH_SECRET`.

Production requirements:

- store `API_KEY_HASH_SECRET` in a secrets manager
- rotate `API_KEY_HASH_SECRET` through a planned key-roll procedure
- rotate org and Operator keys regularly
- revoke unused keys
- set `expires_at` on customer API keys

## Signing Key Management

`SIGNING_KEY_PATH` must point to an Ed25519 private key. Store the private key in
a secret manager or mounted secret. The Operator receives only the public key.

Rotating the signing key requires distributing the new public key to Operators
and supporting an overlap window for existing receipts.

## Operator Trust Boundary

Command Center does not apply Kubernetes resources. The Operator enforces inside
the customer cluster only after verifying the signed receipt, payload hash,
cluster binding, namespace binding, workload binding, policy, decision, and
expiry.

## Rate Limiting And Audit

Command Center emits request IDs, records failed auth attempts, stores audit logs
for sensitive operations, and exposes Prometheus metrics. Production ingress
should also apply network-level rate limits and WAF controls.

## Data Retention

Retention should be plan-based. Receipt metadata, audit logs, failed auth events,
and operator events should be expired according to the organization's plan and
contract.
