from __future__ import annotations

from app.database import Base
from app.modules.api_keys.schemas import ApiKeyCreateRequest
from app.modules.audit.schemas import AuditLogResponse
from app.modules.billing.schemas import PlanResponse, UsageResponse
from app.modules.clusters.schemas import ClusterCreateRequest
from app.modules.executions.schemas import ExecutionStatusRequest
from app.modules.operators.schemas import OperatorHeartbeatRequest
from app.modules.orgs.schemas import OrgCreateRequest
from app.modules.receipts.schemas import ExecutionIntentRequest
from app.orm import ApiKey, Cluster, ExecutionRequest, Organization, TrustReceipt


def test_modules_own_public_schemas() -> None:
    assert OrgCreateRequest.__name__ == "OrgCreateRequest"
    assert ClusterCreateRequest.__name__ == "ClusterCreateRequest"
    assert ApiKeyCreateRequest.__name__ == "ApiKeyCreateRequest"
    assert ExecutionIntentRequest.__name__ == "ExecutionIntentRequest"
    assert ExecutionStatusRequest.__name__ == "ExecutionStatusRequest"
    assert OperatorHeartbeatRequest.__name__ == "OperatorHeartbeatRequest"
    assert UsageResponse.__name__ == "UsageResponse"
    assert PlanResponse.__name__ == "PlanResponse"
    assert AuditLogResponse.__name__ == "AuditLogResponse"


def test_orm_models_are_registered_with_sqlalchemy_base() -> None:
    tables = Base.metadata.tables

    assert Organization.__tablename__ in tables
    assert Cluster.__tablename__ in tables
    assert ApiKey.__tablename__ in tables
    assert TrustReceipt.__tablename__ in tables
    assert ExecutionRequest.__tablename__ in tables
