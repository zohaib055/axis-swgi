from swgi_core import SWGIConfig, SWGIEnforcementNode, generate_private_key_pem


def _build_node() -> SWGIEnforcementNode:
    key = generate_private_key_pem()
    cfg = SWGIConfig(org_id="tm-org", node_id="tm-node", policy_id="policy.v1.tm")
    return SWGIEnforcementNode(config=cfg, signing_private_key_pem=key)


def test_evaluate_allow_generates_receipt() -> None:
    node = _build_node()

    result, receipt = node.evaluate(
        intent="LIVE_MARKET_SNAPSHOT",
        context={"blocked_actions": []},
        action="live_market.snapshot.read",
        authority={"token": "demo-token"},
        workload_id="live-market-snapshot-ws",
    )

    assert result == "ALLOW"
    assert receipt["org_id"] == "tm-org"
    assert receipt["node_id"] == "tm-node"
    assert receipt["result"] == "ALLOW"
    assert receipt["signature"]


def test_evaluate_deny_when_missing_token() -> None:
    node = _build_node()

    result, receipt = node.evaluate(
        intent="LIVE_MARKET_SNAPSHOT",
        context={},
        action="live_market.snapshot.read",
        authority={},
        workload_id="live-market-snapshot-ws",
    )

    assert result == "DENY"
    assert receipt["result"] == "DENY"
