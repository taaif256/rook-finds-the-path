"""Phase 1 smoke tests: API routing, health check and CORS configuration."""

from django.test import override_settings
from django.urls import resolve, reverse
from rest_framework.test import APISimpleTestCase

ANGULAR_ORIGIN = "http://localhost:4200"


class ApiRoutingTests(APISimpleTestCase):
    def test_health_url_is_versioned(self) -> None:
        self.assertEqual(reverse("health"), "/api/v1/health/")

    def test_run_url_is_versioned(self) -> None:
        self.assertEqual(reverse("pathfinding:run"), "/api/v1/pathfinding/run/")
        self.assertEqual(resolve("/api/v1/pathfinding/run/").view_name, "pathfinding:run")


class HealthCheckTests(APISimpleTestCase):
    def test_health_returns_ok(self) -> None:
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["api_version"], "v1")

    def test_health_rejects_post(self) -> None:
        self.assertEqual(self.client.post("/api/v1/health/").status_code, 405)


class CorsTests(APISimpleTestCase):
    def test_angular_origin_is_allowed(self) -> None:
        response = self.client.get("/api/v1/health/", headers={"Origin": ANGULAR_ORIGIN})
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), ANGULAR_ORIGIN)

    def test_preflight_for_run_endpoint_is_allowed(self) -> None:
        response = self.client.options(
            "/api/v1/pathfinding/run/",
            headers={
                "Origin": ANGULAR_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), ANGULAR_ORIGIN)
        self.assertIn("POST", response.headers.get("Access-Control-Allow-Methods", ""))

    def test_unknown_origin_is_not_allowed(self) -> None:
        response = self.client.get("/api/v1/health/", headers={"Origin": "http://evil.example"})
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)

    @override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:9999"])
    def test_allowed_origins_are_configurable(self) -> None:
        response = self.client.get("/api/v1/health/", headers={"Origin": "http://localhost:9999"})
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "http://localhost:9999")
