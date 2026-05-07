from __future__ import annotations

import os
import uuid

import pytest

from app.db import CommandCenterStore
from app.migrations import run_migrations


pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="set TEST_DATABASE_URL to run live Postgres integration tests",
)


def test_live_postgres_org_cluster_key_flow() -> None:
    database_url = os.environ["TEST_DATABASE_URL"]
    os.environ.setdefault("API_KEY_HASH_SECRET", "integration-test-secret")
    run_migrations(database_url)
    store = CommandCenterStore(database_url)

    suffix = uuid.uuid4().hex[:10]
    org_id = f"it-org-{suffix}"
    cluster_id = f"it-cluster-{suffix}"
    token = f"it-token-{suffix}"

    org = store.create_org(
        {
            "org_id": org_id,
            "display_name": "Integration Org",
            "status": "active",
            "plan_code": "starter",
        }
    )
    assert org["org_id"] == org_id

    cluster = store.create_cluster(
        {
            "org_id": org_id,
            "cluster_id": cluster_id,
            "display_name": "Integration Cluster",
            "runtime": "kubernetes",
        },
        token,
    )
    assert cluster["cluster_id"] == cluster_id

    api_key = store.create_api_key(
        api_key_id=f"it-key-{suffix}",
        org_id=org_id,
        cluster_id=cluster_id,
        key_name="integration operator",
        role="operator",
        token=token,
    )
    assert api_key["role"] == "operator"
    assert store.resolve_api_key(token)["cluster_id"] == cluster_id
