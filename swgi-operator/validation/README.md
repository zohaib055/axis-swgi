# Validation Evidence

This directory is the handoff location for the validation evidence requested in `packaging.txt`.

## Required evidence
- `install.log`: fresh install via OLM or direct manifests
- `reconcile.log`: operator creates and maintains operand resources cleanly
- `upgrade.log`: `N -> N+1` operator and/or operand upgrade evidence
- `uninstall.log`: uninstall removes operator-managed resources without orphaning them
- `artifacts.md`: command summary, image references, and test environment notes

## Suggested commands
```bash
oc apply -k axis-swgi-operator/config/default
oc apply -f axis-swgi-operator/config/samples/swgi_v1alpha1_swgideployment.yaml
oc get swgideployment -n swgi-system
oc get deploy,svc,cm,secret -n swgi-system
oc logs deploy/axis-swgi-operator -n swgi-system
```

For OLM validation, capture Subscription, InstallPlan, CSV, and operand rollout logs here as well.
