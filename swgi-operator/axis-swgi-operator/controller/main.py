from __future__ import annotations

import kopf
import kubernetes

from .resources import (
    configmap_manifest,
    deployment_manifest,
    secret_manifest,
    service_manifest,
)


GROUP = "swgi.io"
VERSION = "v1alpha1"
PLURAL = "swgideployments"


def _api_clients() -> tuple[kubernetes.client.CoreV1Api, kubernetes.client.AppsV1Api, kubernetes.client.CustomObjectsApi]:
    try:
        kubernetes.config.load_incluster_config()
    except kubernetes.config.ConfigException:
        kubernetes.config.load_kube_config()
    return (
        kubernetes.client.CoreV1Api(),
        kubernetes.client.AppsV1Api(),
        kubernetes.client.CustomObjectsApi(),
    )


def _apply_resource(kind: str, namespace: str, body: dict) -> None:
    core_api, apps_api, _ = _api_clients()
    name = body["metadata"]["name"]

    if kind == "ConfigMap":
        try:
            core_api.read_namespaced_config_map(name, namespace)
            core_api.patch_namespaced_config_map(name, namespace, body)
        except kubernetes.client.ApiException as exc:
            if exc.status != 404:
                raise
            core_api.create_namespaced_config_map(namespace, body)
        return

    if kind == "Secret":
        try:
            core_api.read_namespaced_secret(name, namespace)
            core_api.patch_namespaced_secret(name, namespace, body)
        except kubernetes.client.ApiException as exc:
            if exc.status != 404:
                raise
            core_api.create_namespaced_secret(namespace, body)
        return

    if kind == "Service":
        try:
            core_api.read_namespaced_service(name, namespace)
            core_api.patch_namespaced_service(name, namespace, body)
        except kubernetes.client.ApiException as exc:
            if exc.status != 404:
                raise
            core_api.create_namespaced_service(namespace, body)
        return

    if kind == "Deployment":
        try:
            apps_api.read_namespaced_deployment(name, namespace)
            apps_api.patch_namespaced_deployment(name, namespace, body)
        except kubernetes.client.ApiException as exc:
            if exc.status != 404:
                raise
            apps_api.create_namespaced_deployment(namespace, body)
        return

    raise ValueError(f"Unsupported kind: {kind}")


def reconcile_instance(name: str, namespace: str, spec: dict) -> None:
    port = int(spec.get("port", 8080))
    resources = [
        configmap_manifest(name=name, namespace=namespace, spec=spec),
        secret_manifest(name=name, namespace=namespace, spec=spec),
        service_manifest(name=name, namespace=namespace, port=port),
        deployment_manifest(name=name, namespace=namespace, spec=spec),
    ]
    for body in resources:
        _apply_resource(body["kind"], namespace, body)


def patch_status(
    *,
    name: str,
    namespace: str,
    status: dict,
) -> None:
    _, _, custom_api = _api_clients()
    custom_api.patch_namespaced_custom_object_status(
        group=GROUP,
        version=VERSION,
        namespace=namespace,
        plural=PLURAL,
        name=name,
        body={"status": status},
    )


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_: object) -> None:
    settings.persistence.finalizer = f"{GROUP}/finalizer"


@kopf.on.create(GROUP, VERSION, PLURAL)
@kopf.on.update(GROUP, VERSION, PLURAL)
def reconcile(
    spec: dict,
    name: str,
    namespace: str,
    meta: dict,
    **_: object,
) -> dict[str, object]:
    reconcile_instance(name=name, namespace=namespace, spec=spec)
    status = {
        "observedGeneration": meta.get("generation", 1),
        "phase": "Ready",
        "message": "SWGI operand reconciled",
        "readyReplicas": int(spec.get("replicas", 1)),
    }
    patch_status(name=name, namespace=namespace, status=status)
    return status


@kopf.on.delete(GROUP, VERSION, PLURAL)
def delete(name: str, namespace: str, **_: object) -> None:
    core_api, apps_api, _ = _api_clients()
    delete_opts = kubernetes.client.V1DeleteOptions()
    for deleter in (
        lambda: apps_api.delete_namespaced_deployment(name, namespace, body=delete_opts),
        lambda: core_api.delete_namespaced_service(name, namespace, body=delete_opts),
        lambda: core_api.delete_namespaced_secret(name, namespace, body=delete_opts),
        lambda: core_api.delete_namespaced_config_map(name, namespace, body=delete_opts),
    ):
        try:
            deleter()
        except kubernetes.client.ApiException as exc:
            if exc.status != 404:
                raise
