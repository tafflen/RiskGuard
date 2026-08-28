"""Liveness endpoint tests for the application bootstrap."""

from app.core.config import Settings
from app.main import create_application
from fastapi.testclient import TestClient


def test_health_returns_liveness_status() -> None:
    client = TestClient(create_application(Settings(environment="test")))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
