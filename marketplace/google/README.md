# SWGI Google Cloud Marketplace Package Scaffold

This directory contains the Google Cloud Marketplace packaging scaffold for the
customer-tenant SWGI deployment.

It is not a finished Marketplace submission by itself. The final submission must
be built with the Google-provided deployer base image, the final Artifact
Registry image paths, product service name, and partner portal metadata.

## Files

- `schema.yaml`: deploy-time parameter schema expected inside the deployer image
  at `/data/schema.yaml`.
- `templates/application.yaml`: Marketplace Application custom resource.
- `templates/operator.yaml`: customer-tenant Operator and enforcement scaffold.
- `tests/README.md`: validation notes for the package.

## Rendering

The templates use `${PARAMETER}` placeholders so the Marketplace deployer can
substitute customer values before applying resources.

Minimum required values:

```text
APP_NAME
NAMESPACE
COMMAND_CENTER_URL
ORG_ID
CLUSTER_ID
OPERATOR_TOKEN
PUBLIC_SIGNING_KEY_PEM
OPERATOR_IMAGE
ENFORCEMENT_IMAGE
```

Optional values:

```text
RECEIPT_ARCHIVE_BUCKET
ENABLE_CLOUD_LOGGING
ENABLE_CLOUD_MONITORING
```

## Submission Notes

- Replace image placeholders with Marketplace Artifact Registry image paths.
- Build a deployer image that copies this directory and exposes
  `/data/schema.yaml`.
- Ensure the submitted image manifest includes the product service-name
  annotation required by Google Cloud Marketplace for GKE listings.
- Keep billing and usage reporting credentials in the partner tenant unless the
  final commercial integration requires another approved pattern.
