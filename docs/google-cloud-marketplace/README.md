# SWGI on Google Cloud Marketplace

This directory maps SWGI to the Google Cloud Marketplace deployment model for a
Kubernetes/GKE listing.

## Documents

- `ARCHITECTURE.md`: partner tenant and customer tenant architecture.
- `DEPLOYMENT_GUIDE.md`: customer-facing deployment flow for GKE/GKE Enterprise.
- `VALIDATION_CHECKLIST.md`: Marketplace technical validation checklist.

## Package Scaffold

The deployer package scaffold lives in `../../marketplace/google`.

The scaffold is intentionally separated from runtime code so Marketplace
submission files can be validated, reviewed, and versioned without changing the
Command Center or customer runtime implementation.
