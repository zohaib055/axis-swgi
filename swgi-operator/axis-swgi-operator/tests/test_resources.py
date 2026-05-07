import unittest

from controller.resources import (
    configmap_manifest,
    deployment_manifest,
    secret_manifest,
    service_manifest,
)


def _base_spec() -> dict:
    return {
        "image": "registry.connect.redhat.com/axissystems/swgi-core:0.1.0",
        "replicas": 2,
        "port": 8080,
        "orgId": "org-prod",
        "nodeId": "fen-ocp-001",
        "tokens": {"admin": "admin-token", "viewer": "viewer-token"},
        "signingKey": {"pem": "TEST_KEY"},
    }


class ResourceManifestTests(unittest.TestCase):
    def test_configmap_manifest_maps_runtime_settings(self) -> None:
        manifest = configmap_manifest(name="swgi", namespace="swgi-system", spec=_base_spec())
        self.assertEqual(manifest["data"]["SWGI_ORG_ID"], "org-prod")
        self.assertEqual(manifest["data"]["SWGI_NODE_ID"], "fen-ocp-001")
        self.assertEqual(manifest["data"]["PORT"], "8080")

    def test_secret_manifest_contains_tokens_and_signing_key(self) -> None:
        manifest = secret_manifest(name="swgi", namespace="swgi-system", spec=_base_spec())
        self.assertEqual(manifest["stringData"]["ADMIN_API_TOKEN"], "admin-token")
        self.assertEqual(manifest["stringData"]["VIEWER_API_TOKEN"], "viewer-token")
        self.assertEqual(manifest["stringData"]["signing_key_ed25519.pem"], "TEST_KEY")

    def test_service_manifest_selects_operator_labels(self) -> None:
        manifest = service_manifest(name="swgi", namespace="swgi-system", port=8080)
        self.assertEqual(manifest["spec"]["selector"]["app.kubernetes.io/instance"], "swgi")
        self.assertEqual(manifest["spec"]["ports"][0]["targetPort"], 8080)

    def test_deployment_manifest_references_operand_image(self) -> None:
        manifest = deployment_manifest(name="swgi", namespace="swgi-system", spec=_base_spec())
        container = manifest["spec"]["template"]["spec"]["containers"][0]
        self.assertEqual(manifest["spec"]["replicas"], 2)
        self.assertEqual(container["image"], "registry.connect.redhat.com/axissystems/swgi-core:0.1.0")
        self.assertTrue(container["securityContext"]["runAsNonRoot"])


if __name__ == "__main__":
    unittest.main()
