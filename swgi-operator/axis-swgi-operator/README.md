# Axis SWGI Operator

`axis-swgi-operator` is the control-plane component described in the Red Hat handoff. It keeps the SWGI execution path separate by managing only deployment, scaling, configuration, and lifecycle for the published SWGI operand image.

## Scope
- Defines the `SwgiDeployment` custom resource
- Reconciles the SWGI operand `Deployment`, `Service`, `ConfigMap`, and `Secret`
- Keeps execution-path logic in the separately maintained operand repository; the operator only manages runtime plumbing

## Layout
- `controller/main.py`: Kopf-based reconcile loop
- `controller/resources.py`: manifest builders for managed resources
- `config/crd/bases/`: CRD definition
- `config/rbac/`: operator service account and cluster RBAC
- `config/manager/`: operator Deployment manifest
- `config/default/`: aggregate install manifest set
- `config/samples/`: sample custom resource
- `docs/DEPLOYMENT.md`: direct-install and OLM flow
- `tests/`: unit tests for manifest generation

## Local run
```bash
cd /Users/zohaibahmad/Desktop/swgi-operator
python3 -m venv .venv-operator
source .venv-operator/bin/activate
pip install -r axis-swgi-operator/requirements.txt
kopf run axis-swgi-operator/controller/main.py
```

## Sample resource
Apply the CRD, then create the sample resource:

```bash
kubectl apply -f axis-swgi-operator/config/crd/bases/swgi.io_swgideployments.yaml
kubectl apply -f axis-swgi-operator/config/samples/swgi_v1alpha1_swgideployment.yaml
```

The operator will create a same-named `Deployment`, `Service`, `ConfigMap`, and `Secret` for the SWGI operand in the target namespace.

## Install manifests
For a direct cluster install without OLM, apply:

```bash
kubectl apply -k axis-swgi-operator/config/default
kubectl apply -f axis-swgi-operator/config/samples/swgi_v1alpha1_swgideployment.yaml
```

Build and publish note:
- Use the repository root `commands-run.txt` as the current command runbook for image build, Quay push, RHCC bundle publication, and preflight steps.
