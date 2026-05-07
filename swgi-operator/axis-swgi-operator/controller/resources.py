from __future__ import annotations

from copy import deepcopy
from typing import Any


def labels(name: str) -> dict[str, str]:
    return {
        "app.kubernetes.io/name": "axis-swgi-api",
        "app.kubernetes.io/component": "api",
        "app.kubernetes.io/managed-by": "axis-swgi-operator",
        "app.kubernetes.io/instance": name,
    }


def configmap_manifest(
    *,
    name: str,
    namespace: str,
    spec: dict[str, Any],
) -> dict[str, Any]:
    data = {
        "SWGI_MODE": str(spec.get("swgiMode", "production")),
        "HOST": "0.0.0.0",
        "PORT": str(spec.get("port", 8080)),
        "LOG_LEVEL": str(spec.get("logLevel", "INFO")),
        "LOG_FORMAT": str(spec.get("logFormat", "json")),
        "SWGI_ORG_ID": str(spec.get("orgId", "org-prod")),
        "SWGI_NODE_ID": str(spec.get("nodeId", "fen-ocp-001")),
        "POLICY_PATH": str(spec.get("policyPath", "/opt/app-root/src/axis-swgi-api/data/input/policy.json")),
        "SIGNING_KEY_PATH": "/tmp/secrets/signing_key_ed25519.pem",
        "RECEIPT_STORE_BACKEND": str(spec.get("receiptStoreBackend", "sqlite")),
        "RECEIPT_DB_PATH": str(spec.get("receiptDbPath", "/tmp/swgi/receipts.db")),
        "DATABASE_URL": str(spec.get("databaseUrl", "")),
        "DB_CONNECT_TIMEOUT_SECONDS": str(spec.get("dbConnectTimeoutSeconds", 5)),
        "RUN_DB_MIGRATIONS": str(spec.get("runDbMigrations", True)).lower(),
        "TLS_ENABLED": str(spec.get("tlsEnabled", False)).lower(),
        "METRICS_ENABLED": str(spec.get("metricsEnabled", True)).lower(),
    }
    return {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": labels(name),
        },
        "data": data,
    }


def secret_manifest(
    *,
    name: str,
    namespace: str,
    spec: dict[str, Any],
) -> dict[str, Any]:
    tokens = spec.get("tokens", {})
    signing = spec.get("signingKey", {})
    string_data = {
        "ADMIN_API_TOKEN": str(tokens.get("admin", "change-admin-token")),
        "VIEWER_API_TOKEN": str(tokens.get("viewer", "change-viewer-token")),
        "signing_key_ed25519.pem": str(
            signing.get(
                "pem",
                "-----BEGIN PRIVATE KEY-----\nREPLACE_WITH_REAL_ED25519_PRIVATE_KEY\n-----END PRIVATE KEY-----",
            )
        ),
    }
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": labels(name),
        },
        "type": "Opaque",
        "stringData": string_data,
    }


def service_manifest(*, name: str, namespace: str, port: int) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": labels(name),
        },
        "spec": {
            "ports": [
                {
                    "name": "http",
                    "port": port,
                    "targetPort": port,
                }
            ],
            "selector": labels(name),
        },
    }


def deployment_manifest(
    *,
    name: str,
    namespace: str,
    spec: dict[str, Any],
) -> dict[str, Any]:
    replicas = int(spec.get("replicas", 1))
    image = str(spec.get("image", "registry.connect.redhat.com/axissystems/swgi-core:0.1.0"))
    port = int(spec.get("port", 8080))
    resources = deepcopy(
        spec.get(
            "resources",
            {
                "requests": {"cpu": "100m", "memory": "128Mi"},
                "limits": {"cpu": "500m", "memory": "512Mi"},
            },
        )
    )
    container = {
        "name": "axis-swgi-api",
        "image": image,
        "imagePullPolicy": "IfNotPresent",
        "ports": [{"containerPort": port, "name": "http"}],
        "envFrom": [
            {"configMapRef": {"name": name}},
            {"secretRef": {"name": name}},
        ],
        "volumeMounts": [
            {
                "name": "signing-key",
                "mountPath": "/tmp/secrets",
                "readOnly": True,
            }
        ],
        "livenessProbe": {"httpGet": {"path": "/healthz", "port": port}},
        "readinessProbe": {"httpGet": {"path": "/v1/health", "port": port}},
        "resources": resources,
        "securityContext": {
            "allowPrivilegeEscalation": False,
            "capabilities": {"drop": ["ALL"]},
            "runAsNonRoot": True,
            "runAsUser": 10001,
        },
    }
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": labels(name),
        },
        "spec": {
            "replicas": replicas,
            "selector": {"matchLabels": labels(name)},
            "template": {
                "metadata": {"labels": labels(name)},
                "spec": {
                    "serviceAccountName": spec.get("serviceAccountName", "default"),
                    "securityContext": {
                        "runAsNonRoot": True,
                        "seccompProfile": {"type": "RuntimeDefault"},
                    },
                    "containers": [container],
                    "volumes": [
                        {
                            "name": "signing-key",
                            "secret": {
                                "secretName": name,
                                "items": [
                                    {
                                        "key": "signing_key_ed25519.pem",
                                        "path": "signing_key_ed25519.pem",
                                    }
                                ],
                            },
                        }
                    ],
                },
            },
        },
    }
