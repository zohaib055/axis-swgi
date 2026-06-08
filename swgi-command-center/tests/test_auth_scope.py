from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.auth import AuthContext, require_cluster_operator, require_org_access
from app.security import constant_time_equal, generate_api_token, hash_password, hash_token, verify_password


def test_api_token_hash_does_not_expose_plaintext() -> None:
    token = generate_api_token("swgi_test")
    digest = hash_token(token, "test-secret")

    assert token.startswith("swgi_test_")
    assert token not in digest
    assert constant_time_equal(digest, hash_token(token, "test-secret"))


def test_password_hash_verification() -> None:
    encoded = hash_password("correct horse battery staple")

    assert "correct horse battery staple" not in encoded
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong password", encoded)


def test_org_access_rejects_cross_org_user() -> None:
    auth = AuthContext(role="org_viewer", token="token", org_id="org-a")

    with pytest.raises(HTTPException):
        require_org_access(auth, "org-b")


def test_org_write_requires_org_admin() -> None:
    auth = AuthContext(role="org_viewer", token="token", org_id="org-a")

    with pytest.raises(HTTPException):
        require_org_access(auth, "org-a", write=True)


def test_operator_access_requires_matching_cluster() -> None:
    auth = AuthContext(role="operator", token="token", org_id="org-a", cluster_id="cluster-a")

    require_cluster_operator(auth, "org-a", "cluster-a")
    with pytest.raises(HTTPException):
        require_cluster_operator(auth, "org-a", "cluster-b")
