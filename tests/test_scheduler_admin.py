# tests/test_scheduler_admin.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers.admin import router as admin_router
from routers.auth import get_current_user
from models.user import User
from unittest.mock import patch

app = FastAPI()
app.include_router(admin_router, prefix="/api/v1/admin")

def override_admin_user():
    return User(id=1, email="admin@example.com", username="admin", role="admin")

def override_normal_user():
    return User(id=2, email="user@example.com", username="user", role="user")

client = TestClient(app)

def test_admin_sync_endpoints_access_control():
    # 1. Access as non-admin -> 403 Forbidden
    app.dependency_overrides[get_current_user] = override_normal_user
    resp = client.post("/api/v1/admin/sync/news")
    assert resp.status_code == 403

    # 2. Access as admin -> 200 OK
    app.dependency_overrides[get_current_user] = override_admin_user
    with patch("services.news_service.NewsService.sync_news_from_source", return_value=10):
        resp_admin = client.post("/api/v1/admin/sync/news")
        assert resp_admin.status_code == 200
        assert resp_admin.json()["synced_count"] == 10
