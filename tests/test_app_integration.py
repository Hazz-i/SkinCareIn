# tests/test_app_integration.py
import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_api_v1_health_and_root():
    # Root check
    resp_root = client.get("/")
    assert resp_root.status_code == 200
    assert "version" in resp_root.json()

    # API v1 Health check
    resp_health = client.get("/api/v1/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "ok"
    assert resp_health.json()["version"] == "2.0.0"
