# SWGI Operator Bundle Submission Prep

This directory mirrors the layout expected by the Red Hat `certified-operators`
repository for the SWGI Operator bundle submission.

## Prepared path

```text
swgi-operator-bundle-submission/
  operators/
    axis-swgi-operator/
      ci.yaml
      0.1.0/
        manifests/
        metadata/
```

## Populate the bundle content

Copy the current bundle artifacts into the prepared versioned directory:

```bash
cp -R bundle/manifests/. swgi-operator-bundle-submission/operators/axis-swgi-operator/0.1.0/manifests/
cp -R bundle/metadata/. swgi-operator-bundle-submission/operators/axis-swgi-operator/0.1.0/metadata/
```

## Next step outside this repo

Place `operators/axis-swgi-operator/0.1.0` into a fork of
`redhat-openshift-ecosystem/certified-operators`, then run the hosted operator
pipeline from an environment with `tkn` and operator-pipeline access.

Reference command:

```bash
tkn pipeline start operator-ci-pipeline \
  --param git_repo_url=<fork-url-of-certified-operators> \
  --param git_branch=main \
  --param bundle_path=operators/axis-swgi-operator/0.1.0 \
  --param upstream_repo_name=redhat-openshift-ecosystem/certified-operators \
  --param submit=true \
  --param env=prod \
  --workspace name=pipeline,volumeClaimTemplateFile=templates/workspace-template.yml \
  --showlog
```
