# SWGI Standalone Kubernetes Governance Workspace

This workspace contains the SWGI components for the standalone Kubernetes-native
execution governance product. OpenShift remains a supported runtime, but SWGI is
not OpenShift-only.

## Repositories in this workspace
- `swgi_core/`: reusable SWGI core package for deterministic policy evaluation and trust receipt generation
- `swgi-command-center/`: standalone control plane for intent intake, signed Trust Receipts, Postgres metadata, dashboard APIs, usage, and Operator status
- `swgi-openshift/`: OpenShift-compatible deployment/runtime package backed by PostgreSQL and Helm
- `swgi-operator/`: in-cluster Operator/enforcement layer, kept local and ignored from this repository

## Certification artifacts
- `bundle/`: operator bundle scaffold for hosted pipeline and certification workflows
- `bundle.Dockerfile`: bundle image build file
- `docs/google-cloud-marketplace/`: GCP Marketplace architecture, deployment, and validation readiness
- `docs/intel-partner/`: Intel partner architecture, deployment, and validation readiness
- `marketplace/google/`: Google Cloud Marketplace Kubernetes package scaffold
- `marketplace/intel/`: Intel partner packaging and evidence notes

## Start here
- Command Center: `swgi-command-center/README.md`
- OpenShift service: `swgi-openshift/README.md`
- Core package: `swgi_core/README.md`
- Google Cloud Marketplace: `docs/google-cloud-marketplace/README.md`
- Intel partner readiness: `docs/intel-partner/README.md`

## Current structure
```text
  bundle/
  bundle.Dockerfile
  docs/google-cloud-marketplace/
  docs/intel-partner/
  marketplace/google/
  marketplace/intel/
  swgi-command-center/
  swgi_core/
  swgi-openshift/
```
