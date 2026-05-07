# Operator Deployment

## Build images
```bash
podman build -f axis-swgi-operator/Dockerfile -t axis-swgi-operator:0.1.0 .
podman tag axis-swgi-operator:0.1.0 registry.connect.redhat.com/axissystems/axis-swgi-operator:0.1.0

podman build -f bundle.Dockerfile -t axis-swgi-operator-bundle:0.1.0 .
podman tag axis-swgi-operator-bundle:0.1.0 registry.connect.redhat.com/axissystems/axis-swgi-operator-bundle:0.1.0

podman build -f catalog/index.Dockerfile -t axis-swgi-operator-index:0.1.0 .
podman tag axis-swgi-operator-index:0.1.0 registry.connect.redhat.com/axissystems/axis-swgi-operator-index:0.1.0
```

Prerequisite:
- The operand image referenced by the custom resource must already exist in the separate operand repository and registry.

## Direct install
```bash
oc create namespace swgi-system
oc apply -k axis-swgi-operator/config/default
oc apply -f axis-swgi-operator/config/samples/swgi_v1alpha1_swgideployment.yaml
```

## OLM install
```bash
oc apply -f catalog/catalogsource.yaml
oc create namespace swgi-system
oc apply -f catalog/operatorgroup.yaml
oc apply -f catalog/subscription.yaml
```

## Validation checkpoints
```bash
oc get csv -n swgi-system
oc get subscription -n swgi-system
oc get swgideployments.swgi.io -n swgi-system
oc get deploy,svc,cm,secret -n swgi-system
oc logs deploy/axis-swgi-operator -n swgi-system
```
