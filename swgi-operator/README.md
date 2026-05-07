# SWGI Red Hat Workspace

This workspace contains the SWGI operator packaging assets needed for the current Red Hat / OpenShift path.

## Repositories in this workspace
- `axis-swgi-operator/`: operator/control-plane scaffold for CRDs, reconciliation, scaling, and lifecycle management

## Certification artifacts
- `bundle/`: operator bundle scaffold for hosted pipeline and certification workflows
- `bundle.Dockerfile`: bundle image build file
- `catalog/`: file-based catalog scaffold for the operator index image
- `validation/`: install, reconcile, upgrade, and uninstall evidence placeholders

## Start here
- Operator scaffold: `axis-swgi-operator/README.md`
- Catalog scaffold: `catalog/README.md`

## Current structure
```text
  axis-swgi-operator/
  bundle/
  bundle.Dockerfile
  catalog/
  validation/
```
