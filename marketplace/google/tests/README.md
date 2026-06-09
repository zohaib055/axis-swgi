# Marketplace Package Validation

Before Marketplace submission, render the templates with real values and run:

```bash
kubectl apply --dry-run=client --validate=false -f rendered/application.yaml
kubectl apply --dry-run=client --validate=false -f rendered/operator.yaml
```

Then validate on a disposable GKE cluster:

```bash
kubectl apply -f rendered/application.yaml
kubectl apply -f rendered/operator.yaml
kubectl -n swgi-system rollout status deploy/swgi-operator
kubectl -n swgi-system rollout status deploy/swgi-enforcement
kubectl -n swgi-system get application swgi
```

Expected results:

- Application custom resource is visible.
- Operator pod starts and reports heartbeat to Command Center.
- Enforcement pod starts with restricted container security context.
- Command Center shows the customer cluster as healthy.
- Operator token can be revoked from Command Center.
- Deleting the namespace removes customer tenant runtime resources.
