# swgi_core

Standalone SWGI Federated Enforcement Node core package for:
- deterministic policy evaluation (`ALLOW` / `DENY`)
- trust receipt generation
- Ed25519 signing
- minimal in-memory metrics counters

This package has no dependency on any specific host app and can be integrated into any Python application.

## Package Layout

```text
swgi_core/
  pyproject.toml
  README.md
  swgi_core/
    __init__.py
    config.py
    evaluator.py
    models.py
    policy_engine.py
    receipt_emitter.py
    signature.py
    metrics.py
```

## Install

If `swgi_core` is in your local filesystem:

```bash
pip install /path/to/swgi_core
```

Editable mode for development:

```bash
pip install -e ./swgi_core
```

Poetry example:

```bash
poetry add /path/to/swgi_core
```

## Environment Variables

Required:
- `SWGI_SIGNING_PRIVATE_KEY_PEM`: Ed25519 private key in PEM format

Optional:
- `SWGI_ORG_ID` (default: `default-org`)
- `SWGI_NODE_ID` (default: `default-node`)
- `SWGI_POLICY_ID` (default: `policy.v1.default`)
- `SWGI_SCHEMA_VERSION` (default: `v1.0`)
- `SWGI_STRICT_MODE` (default: `true`)

## Generate Key (One Time)

```python
from swgi_core import generate_private_key_pem

print(generate_private_key_pem())
```

Put the generated PEM into `SWGI_SIGNING_PRIVATE_KEY_PEM`.

## Integration Steps (Any Python App)

1. Install the package in your app environment.
2. Set `SWGI_SIGNING_PRIVATE_KEY_PEM` in your app secrets/environment.
3. Initialize one `SWGIEnforcementNode` instance at app startup.
4. Call `evaluate(...)` from your business flow.
5. Persist or forward returned receipts as needed.

## API Surface

```python
from swgi_core import SWGIEnforcementNode

node = SWGIEnforcementNode()
result, receipt = node.evaluate(
    intent="OPERATION_NAME",
    context={"env": "prod", "blocked_actions": [], "blocked_workloads": []},
    action="resource.operation",
    authority={"role": "service", "token": "internal-token"},
    workload_id="service-identifier",
)
```

Return values:
- `result`: `ALLOW` or `DENY`
- `receipt`: signed trust receipt dictionary

Functional shortcut API:

```python
from swgi_core import evaluate

result, receipt = evaluate(
    intent="OPERATION_NAME",
    context={"env": "prod"},
    action="resource.operation",
    authority={"token": "internal-token"},
    workload_id="service-identifier",
)
```

## Receipt Fields (v1)

`receipt_id`, `schema_version`, `org_id`, `node_id`, `timestamp`, `action`, `workload_id`, `policy_id`, `result`, `payload_hash`, `authority_token_hash`, `integrity_classification`, `signature`

## Notes

- Receipts are signed with Ed25519.
- `receipt_id` is UUID4.
- `payload_hash` is SHA-256 over canonical JSON.
- Current policy engine is deterministic and conservative by default.
- For production, keep signing keys in a secret manager and rotate regularly.
