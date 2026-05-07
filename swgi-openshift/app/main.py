from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from prometheus_client import Counter, Histogram, generate_latest

load_dotenv()

from swgi_core.config import SWGIConfig
from swgi_core.evaluator import SWGIEnforcementNode
from swgi_core.policy_engine import PolicyEngine

from .auth import AuthContext, require_admin, require_auth
from .config import settings
from .db import get_receipt_store
from .logging_config import configure_logging
from .models import AuthorizeRequest, ReceiptListResponse

configure_logging(settings.log_level, settings.log_format)
logger = logging.getLogger("swgi_openshift")
settings.validate_runtime()


class Metrics:
    def __init__(self) -> None:
        self.auth_total = Counter("swgi_authorize_total", "Total authorize calls", ["result"])
        self.auth_latency = Histogram(
            "swgi_authorize_latency_ms",
            "Authorize latency (ms)",
            buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 25, 50, 100, 250, 500, 1000),
        )

    def observe_authorize(self, latency_ms: float, result: str) -> None:
        self.auth_total.labels(result=result).inc()
        self.auth_latency.observe(latency_ms)


def _load_private_key_pem(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _load_policy_id(policy_path: str) -> str:
    return PolicyEngine.from_file(policy_path).policy_id


app = FastAPI(title="SWGI OpenShift API", version=settings.app_version)
store, receipt_store_name = get_receipt_store()
if settings.run_db_migrations:
    store.initialize()

policy_engine = PolicyEngine.from_file(settings.policy_path)
config = SWGIConfig(org_id=settings.org_id, node_id=settings.node_id, policy_id=_load_policy_id(settings.policy_path))
node = SWGIEnforcementNode(
    config=config,
    signing_private_key_pem=_load_private_key_pem(settings.signing_key_path),
    policy_engine=policy_engine,
)
metrics = Metrics()

logger.info(
    "swgi_openshift.started mode=%s node_id=%s org_id=%s tls_enabled=%s receipt_store=%s",
    settings.swgi_mode,
    settings.node_id,
    settings.org_id,
    settings.tls_enabled,
    receipt_store_name,
)


@app.get("/v1/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "mode": settings.swgi_mode,
        "node_id": settings.node_id,
        "policy_id": config.policy_id,
        "receipt_store": receipt_store_name,
        "tls_enabled": settings.tls_enabled,
    }


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return health()


@app.get("/metrics")
def prometheus_metrics() -> PlainTextResponse:
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type="text/plain; version=0.0.4")


@app.post("/v1/authorize")
def authorize(req: AuthorizeRequest, auth: AuthContext = Depends(require_admin)) -> JSONResponse:
    t0 = time.perf_counter()
    authority = dict(req.authority)
    authority.setdefault("token", auth.token)
    authority.setdefault("role", auth.role)

    decision, receipt = node.evaluate(
        intent=req.intent,
        context=req.context,
        action=req.action,
        authority=authority,
        workload_id=req.workload_id,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    receipt["latency_ms"] = round(elapsed_ms, 4)
    receipt["request_payload"] = req.model_dump(mode="json")
    store.persist(receipt)
    metrics.observe_authorize(elapsed_ms, decision)

    logger.info(
        "receipt.generated receipt_id=%s org_id=%s node_id=%s decision=%s policy_id=%s",
        receipt.get("receipt_id"),
        receipt.get("org_id"),
        receipt.get("node_id"),
        decision,
        receipt.get("policy_id"),
    )
    return JSONResponse(
        {
            "result": decision,
            "reason": receipt.get("reason", "authorized" if decision == "ALLOW" else "denied"),
            "integrity_classification": receipt.get("integrity_classification", "HIGH"),
            "receipt_id": receipt.get("receipt_id"),
            "latency_ms": round(elapsed_ms, 4),
        }
    )


@app.get("/v1/receipts/{receipt_id}")
def get_receipt(receipt_id: str, _: AuthContext = Depends(require_auth)) -> JSONResponse:
    receipt = store.load(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return JSONResponse(receipt)


@app.get("/v1/receipts", response_model=ReceiptListResponse)
def list_receipts(
    org_id: str | None = None,
    node_id: str | None = None,
    result: str | None = None,
    policy_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = 50,
    offset: int = 0,
    _: AuthContext = Depends(require_auth),
) -> ReceiptListResponse:
    items = store.list_receipts(
        org_id=org_id,
        node_id=node_id,
        result=result,
        policy_id=policy_id,
        start_ts=start,
        end_ts=end,
        limit=limit,
        offset=offset,
    )
    return ReceiptListResponse(count=len(items), items=items)


@app.get("/v1/receipts/export.csv")
def export_receipts_csv(
    org_id: str | None = None,
    node_id: str | None = None,
    result: str | None = None,
    policy_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
    _: AuthContext = Depends(require_auth),
) -> Response:
    csv_body = store.export_csv(
        org_id=org_id,
        node_id=node_id,
        result=result,
        policy_id=policy_id,
        start_ts=start,
        end_ts=end,
    )
    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="receipts.csv"'},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port, reload=False)
