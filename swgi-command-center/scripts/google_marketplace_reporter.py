#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def _env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _json_request(url: str, *, method: str = "GET", token: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(
        url,
        data=data,
        method=method,
        headers={
            "authorization": f"Bearer {token}",
            "content-type": "application/json",
            "accept": "application/json",
        },
    )
    with urlopen(request, timeout=30) as response:
        payload = response.read()
    return json.loads(payload.decode("utf-8")) if payload else {}


def _mark(command_center_url: str, admin_token: str, event_id: str, status: str, last_error: str | None = None) -> None:
    _json_request(
        f"{command_center_url}/v1/marketplace/google/usage-events/{event_id}/report",
        method="POST",
        token=admin_token,
        body={"status": status, "last_error": last_error},
    )


def main() -> int:
    command_center_url = _env("COMMAND_CENTER_URL").rstrip("/")
    admin_token = _env("ADMIN_API_TOKEN")
    service_control_token = _env("GOOGLE_SERVICE_CONTROL_TOKEN")
    service_name = _env("GOOGLE_MARKETPLACE_SERVICE_NAME")
    limit = int(os.getenv("GOOGLE_MARKETPLACE_REPORT_LIMIT", "100"))

    operations_payload = _json_request(
        f"{command_center_url}/v1/marketplace/google/service-control-operations?status=pending&limit={limit}",
        token=admin_token,
    )
    operations = operations_payload.get("operations", [])
    if not operations:
        print("No pending Google Marketplace usage operations.")
        return 0

    report_url = f"https://servicecontrol.googleapis.com/v1/services/{service_name}:report"
    for operation in operations:
        event_id = operation["operationId"]
        if not operation.get("consumerId"):
            _mark(command_center_url, admin_token, event_id, "failed", "usage_reporting_id is missing")
            print(f"failed {event_id}: usage_reporting_id is missing")
            continue
        try:
            _json_request(
                report_url,
                method="POST",
                token=service_control_token,
                body={"operations": [operation]},
            )
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            _mark(command_center_url, admin_token, event_id, "failed", error_body[:1000])
            print(f"failed {event_id}: {exc.code} {error_body}", file=sys.stderr)
            continue
        _mark(command_center_url, admin_token, event_id, "reported")
        print(f"reported {event_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
