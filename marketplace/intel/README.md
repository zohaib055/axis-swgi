# Intel Partner Packaging Notes

Intel partner readiness does not require a separate Kubernetes marketplace
package in this repository today. SWGI should be presented to Intel and Intel
based customers as a Kubernetes governance and Trust Receipt solution optimized
for Intel infrastructure, with optional confidential computing alignment.

## Partner Assets To Prepare

- Product one-pager: SWGI governance and Trust Receipts on Intel infrastructure.
- Reference architecture: `../../docs/intel-partner/ARCHITECTURE.md`.
- Deployment guide: `../../docs/intel-partner/DEPLOYMENT_GUIDE.md`.
- Validation checklist: `../../docs/intel-partner/VALIDATION_CHECKLIST.md`.
- Demo script: self-serve signup, cluster registration, Operator heartbeat,
  governed execution, Trust Receipt, audit log, and optional TDX policy.

## Customer Evidence

Collect the following evidence for Intel partner and customer reviews:

- Kubernetes distribution and version.
- Intel CPU model and node pool details.
- SWGI Operator version.
- Enforcement pod image digest.
- Receipt signature verification output.
- Audit log export.
- Optional TDX attestation reference for confidential workloads.

## Positioning

SWGI is not an Intel hardware management tool. SWGI is the governance,
authorization, and evidence layer that can record and enforce policy for
workloads running on Intel-based cloud, private cloud, and edge infrastructure.
