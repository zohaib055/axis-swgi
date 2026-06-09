# SWGI Intel Partner Architecture

SWGI complements Intel-based infrastructure by adding policy governance,
execution authorization, Trust Receipt generation, and audit evidence across
Kubernetes workloads.

## Deployment Model

```text
Axis Systems managed control plane
  -> SWGI Command Center
  -> orgs, users, roles, API keys
  -> policy orchestration
  -> Trust Receipt registry
  -> audit and operator event visibility

Customer Intel-based infrastructure
  -> Kubernetes / OpenShift / GKE / private cloud / edge cluster
  -> Intel Xeon worker nodes
  -> optional Intel TDX capable node pools
  -> SWGI Operator
  -> SWGI enforcement pods
  -> customer workloads
```

## Intel-Aligned Capabilities

- Runs on Kubernetes clusters backed by Intel Xeon infrastructure.
- Records workload, node, cluster, policy, decision, and execution metadata as
  signed Trust Receipts.
- Supports customer-owned audit retention for regulated environments.
- Provides platform admin visibility into customer integrations and cluster
  health without moving customer payloads into the partner tenant.
- Can be extended to include Intel TDX attestation evidence where customers run
  confidential containers or confidential VMs.

## Confidential Computing Boundary

For customers using Intel Trust Domain Extensions:

```text
Intel TDX capable node pool
  -> confidential VM / confidential container runtime
  -> attestation evidence
  -> SWGI policy decision
  -> signed Trust Receipt
  -> authorized workload execution
```

SWGI should treat TDX attestation as an input to policy and receipt metadata:

- TDX enabled: true / false.
- Attestation provider and verifier.
- Measurement or quote reference.
- Workload identity.
- Node pool or runtime class.
- Verification result.

The enforcement layer must reject confidential-only policies when attestation is
missing, stale, unverifiable, or bound to a different workload identity.

## Data Boundary

- Customer payloads remain in the customer environment.
- Command Center stores metadata, hashes, policy decisions, Trust Receipts,
  operator status, org configuration, and audit logs.
- Intel attestation evidence should be stored as references or compact metadata
  unless the customer contract requires full evidence retention.
- Operator tokens remain cluster scoped and revocable from Command Center.

## Customer Value

- Verifiable governance for workloads on Intel infrastructure.
- Audit-ready evidence for regulated workloads.
- Optional confidential computing policy controls for Intel TDX environments.
- Single operational view for customer clusters, integrations, receipts, users,
  API keys, and operator health.
