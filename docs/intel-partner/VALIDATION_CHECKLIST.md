# Intel Partner Validation Checklist

Use this checklist for Intel partner reviews, customer proof-of-value work, and
solution-brief evidence.

## Repo Readiness

| Area | Status | Evidence |
| --- | --- | --- |
| Intel partner architecture | Ready | `docs/intel-partner/ARCHITECTURE.md` |
| Intel deployment guide | Ready | `docs/intel-partner/DEPLOYMENT_GUIDE.md` |
| Command Center auth and roles | Ready | Postgres-backed users and sessions |
| Customer cluster onboarding | Ready | Command Center cluster registration |
| Operator contract | Ready | `swgi-command-center/docs/OPERATOR_CONTRACT.md` |
| Trust Receipt registry | Ready | Command Center Postgres metadata |
| Confidential computing policy hooks | Ready | Intent `attestation` metadata validates Intel TDX evidence references |

## Infrastructure Validation

- Cluster runs on Intel Xeon worker nodes.
- Kubernetes or OpenShift version is supported by the customer's platform.
- SWGI Operator deploys with restricted security context.
- SWGI enforcement pods deploy with restricted security context.
- Operator heartbeat is visible in Command Center.
- Command Center shows cluster health and operator events.
- Customer can revoke Operator token from Command Center.

## Trust Receipt Validation

- Receipt includes organization ID.
- Receipt includes cluster ID.
- Receipt includes workload ID.
- Receipt includes namespace.
- Receipt includes policy decision.
- Receipt includes payload hash.
- Receipt signature verifies with the public signing key.
- Receipt is rejected when expired or tampered with.

## Intel TDX Validation Extension

For confidential workload deployments, validate:

- Intel TDX capable node pool is present.
- Confidential runtime class or equivalent runtime is configured.
- Attestation provider is reachable.
- Attestation evidence is bound to workload identity.
- Policy can require verified confidential runtime.
- Enforcement rejects workload execution when attestation is missing.
- Trust Receipt records TDX verification result or an evidence reference.

## Command Center API Validation

Submit a governed intent with Intel attestation metadata:

```bash
curl -X POST "$COMMAND_CENTER_URL/v1/intents" \
  -H "Authorization: Bearer $ORG_TOKEN" \
  -H "content-type: application/json" \
  -d '{
    "org_id":"customer-org",
    "cluster_id":"intel-cluster-1",
    "namespace":"swgi-system",
    "workload_id":"confidential-workload",
    "action":"kubernetes.apply",
    "intent":"deploy confidential workload",
    "attestation":{
      "provider":"intel-tdx",
      "verification_result":"verified",
      "quote_hash":"sha256:example",
      "runtime_class":"kata-tdx"
    }
  }'
```

The returned Trust Receipt must preserve the attestation metadata without
storing customer payloads.

## Commands

Backend:

```bash
cd swgi-command-center
PYTHONPATH="$PWD:../swgi_core" poetry run pytest
```

Frontend:

```bash
cd command-center-frontend
npm run build
```

Operator deployment evidence:

```bash
kubectl -n swgi-system get pods
kubectl -n swgi-system get deploy
kubectl -n swgi-system logs deploy/swgi-operator
```
