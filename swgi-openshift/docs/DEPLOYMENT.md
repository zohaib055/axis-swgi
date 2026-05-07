# OpenShift Deployment

This guide is for the OpenShift-compatible runtime path. The standalone SWGI
control plane is `../../swgi-command-center` and uses Postgres only.

## Prerequisites
- OpenShift cluster access
- Helm 3.x
- A real Ed25519 private key stored as a Kubernetes Secret value
- A provisioned Red Hat Connect repository at `registry.connect.redhat.com/axissystems/swgi-core`

If the Connect UI still shows an empty `Repository path`, save or submit the container entry first and wait for Red Hat to provision the backend repository before pushing.

## Deploy
```bash
helm upgrade --install swgi-openshift ./helm/swgi-openshift \
  --namespace swgi-system \
  --create-namespace \
  --set image.repository=registry.connect.redhat.com/axissystems/swgi-core \
  --set image.tag=0.1.0 \
  --set config.receiptStoreBackend="postgres" \
  --set config.databaseUrl="postgresql://swgi:swgi@postgres:5432/swgi" \
  --set secrets.adminApiToken="replace-admin-token" \
  --set secrets.viewerApiToken="replace-viewer-token" \
  --set-file secrets.signingKey=./data/input/real_signing_key_ed25519.pem
```

## Push Image
```bash
cd /Users/zohaibahmad/Desktop/swgi-redhat
docker build -f swgi-openshift/Dockerfile -t swgi-openshift:0.1.0 .
podman tag swgi-openshift:0.1.0 registry.connect.redhat.com/axissystems/swgi-core:0.1.0
podman push registry.connect.redhat.com/axissystems/swgi-core:0.1.0
```

## Verify
```bash
oc get all -n swgi-system
oc get route -n swgi-system
oc logs deploy/swgi-openshift -n swgi-system
```

## Upgrade
```bash
helm upgrade swgi-openshift ./helm/swgi-openshift -n swgi-system
```

## Uninstall
```bash
helm uninstall swgi-openshift -n swgi-system
```

The chart keeps configuration externalized through ConfigMap and Secret.
Postgres is the production storage target for standalone SWGI and production-like
OpenShift deployments.
