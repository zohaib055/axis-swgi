# Alignment With swgi_core, swgi-openshift, and swgi-operator

## swgi_core

`swgi_core` remains the deterministic decision and Trust Receipt engine.
Command Center imports it directly for:

- policy evaluation
- payload hashing
- Ed25519 signing
- receipt generation

Command Center does not fork or duplicate core decision logic.

## swgi-openshift

`swgi-openshift` remains the OpenShift-compatible runtime/package path.
It should not become the standalone control plane. Its long-term role is:

- OpenShift deployment compatibility
- Helm/OpenShift packaging
- route/service/security context examples
- optional runtime adapter where needed

The standalone product center of gravity is `swgi-command-center`.

## swgi-operator

`swgi-operator` is the in-cluster enforcement layer. It should integrate with
Command Center through:

- `POST /v1/operator/heartbeat`
- `GET /v1/operator/executions/pending`
- `POST /v1/operator/executions/{execution_id}/status`
- `POST /v1/operator-events`

The Operator must verify:

- signature with `PUBLIC_SIGNING_KEY_PEM`
- payload hash binding
- org, cluster, namespace, workload, action, policy, and expiry binding
- decision is `ALLOW` or valid `MODIFY`

Command Center must never directly apply Kubernetes/OpenShift resources.
