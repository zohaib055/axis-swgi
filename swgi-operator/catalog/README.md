# Catalog Image

This directory contains a file-based catalog scaffold for the SWGI Operator.

## Build the catalog image
```bash
podman build -f catalog/index.Dockerfile -t axis-swgi-operator-index:0.1.0 .
```

## Push example
```bash
podman tag axis-swgi-operator-index:0.1.0 registry.connect.redhat.com/axissystems/axis-swgi-operator-index:0.1.0
podman push registry.connect.redhat.com/axissystems/axis-swgi-operator-index:0.1.0
```

The catalog references the bundle image `registry.connect.redhat.com/axissystems/axis-swgi-operator-bundle:0.1.0`. Update `catalog/index.yaml` when the final bundle image tag changes.
