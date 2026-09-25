# tests/test_uv_index.py
import json
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base, get_db
from helper.uvindex import classify_uv_index, get_uv_forecast
from models.uv_index import UVIndexCache
from server import app
from services.uv_index_service import UVIndexService

TEST_DB_FILE = os.path.join(tempfile.gettempdir(), "skinsight_uv_index_test.db")
engine = create_engine(f"sqlite:///{TEST_DB_FILE}", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

MOCK_UV_API_RESPONSE = {
    "ok": True,
    "latitude": 40.71,
    "longitude": -74.01,
    "timezone": {"id": "America/New_York", "name": "America/New_York"},
    "now": {"date": "2026-09-17", "time": "10:00:00", "uv_index": 4.2},
    "today": {"date": "2026-09-17", "max": {"time": "13:00:00", "uv_index": 6.8}},
    "tomorrow": {"date": "2026-09-18", "max": {"time": "13:00:00", "uv_index": 7.1}},
    "daily": [
        {"date": "2026-09-17", "max": {"time": "13:00:00", "uv_index": 6.8}},
        {"date": "2026-09-18", "max": {"time": "13:00:00", "uv_index": 7.1}},
    ],
    "hourly": [
        {"date": "2026-09-17", "time": "12:00:00", "uv_index": 6.0},
        {"date": "2026-09-17", "time": "13:00:00", "uv_index": 6.8},
    ],
    "meta": {
        "source": {"attribution": "Data by uvindexapi.com", "url": "https://uvindexapi.com"},
        "license": {
            "id": "CC-BY-SA-4.0",
            "name": "Creative Commons Attribution-ShareAlike 4.0 International",
            "url": "https://creativecommons.org/licenses/by-sa/4.0/",
        },
    },
}

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_classify_uv_index_who_scale():
    assert classify_uv_index(0)["Level"] == "Low"
    assert classify_uv_index(2)["Level"] == "Low"
    assert classify_uv_index(5)["Level"] == "Moderate"
    assert classify_uv_index(7)["Level"] == "High"
    assert classify_uv_index(10)["Level"] == "Very High"
    assert classify_uv_index(13)["Level"] == "Extreme"
    assert "sunscreen" in classify_uv_index(6)["Advice"].lower()

def test_get_uv_forecast_normalizes_response():
    with patch("helper.uvindex._fetch_api_json", return_value=MOCK_UV_API_RESPONSE):
        result = get_uv_forecast(40.71, -74.01, timezone="Auto")

    assert result["Timezone"]["Id"] == "America/New_York"
    assert result["Now"]["UV_Index"] == 4.2
    assert result["Now"]["Level"] == "Moderate"
    assert result["Today"]["Max"]["Level"] == "High"
    assert result["Tomorrow"]["Max"]["UV_Index"] == 7.1
    assert len(result["Daily"]) == 2
    assert len(result["Hourly"]) == 2
    assert result["Hourly"][0]["Level"] == "High"
    assert result["Source"]["Url"] == "https://uvindexapi.com"

def test_get_uv_forecast_returns_none_when_api_fails():
    with patch("helper.uvindex._fetch_api_json", return_value={"ok": False, "message": "Invalid coordinates."}):
        assert get_uv_forecast(0, 0) is None

    with patch("helper.uvindex._fetch_api_json", return_value=None):
        assert get_uv_forecast(0, 0) is None

def test_service_caches_forecast(db):
    with patch("services.uv_index_service.get_uv_forecast", return_value={"Latitude": 40.71}) as fetch:
        UVIndexService.get_uv_index(db, 40.7128, -74.006)
        assert fetch.call_count == 1
        assert db.query(UVIndexCache).count() == 1
        # Coordinates are rounded to 2 decimals for the cache key
        assert db.query(UVIndexCache).first().latitude == 40.71

    # Second call is served from the fresh cache without hitting the upstream API
    with patch("services.uv_index_service.get_uv_forecast", side_effect=Exception("Should not be called")):
        UVIndexService.get_uv_index(db, 40.7128, -74.006)
        assert db.query(UVIndexCache).count() == 1

def test_service_serves_response_shape(db):
    with patch("helper.uvindex._fetch_api_json", return_value=MOCK_UV_API_RESPONSE):
        response = UVIndexService.get_uv_index(db, 40.71, -74.01, include_daily=True, include_hourly=True)

    assert response["now"]["time"] == "10:00:00"
    assert response["now"]["level"] == "Moderate"
    assert response["today"]["max"]["advice"]
    assert response["timezone"] == {"id": "America/New_York", "name": "America/New_York"}
    assert len(response["daily"]) == 2
    assert len(response["hourly"]) == 2
    assert response["cached"] is False
    assert response["source"]["attribution"] == "Data by uvindexapi.com"

def test_service_omits_daily_and_hourly_when_not_requested(db):
    with patch("helper.uvindex._fetch_api_json", return_value=MOCK_UV_API_RESPONSE):
        response = UVIndexService.get_uv_index(db, 40.71, -74.01, include_daily=False, include_hourly=False)
    assert response["daily"] is None
    assert response["hourly"] is None

def test_service_raises_502_without_cache(db):
    with patch("services.uv_index_service.get_uv_forecast", return_value=None):
        with pytest.raises(HTTPException) as exc:
            UVIndexService.get_uv_index(db, -6.2, 106.8)
    assert exc.value.status_code == 502

def test_service_serves_stale_cache_on_failure(db):
    db.add(UVIndexCache(
        latitude=-6.2,
        longitude=106.8,
        timezone="Asia/Jakarta",
        payload=json.dumps({
            "Latitude": -6.2,
            "Longitude": 106.8,
            "Timezone": {"Id": "Asia/Jakarta", "Name": "Asia/Jakarta"},
            "Now": {"Date": "2026-09-16", "Time": "10:00:00", "UV_Index": 9.5, "Level": "Very High", "Advice": "Avoid direct sun."},
            "Today": {"Date": "2026-09-16", "Max": {"Time": "12:00:00", "UV_Index": 11.0, "Level": "Extreme", "Advice": "Stay indoors."}},
            "Tomorrow": {"Date": "2026-09-17", "Max": {"Time": "12:00:00", "UV_Index": 10.8, "Level": "Very High", "Advice": "Avoid direct sun."}},
            "Daily": [],
            "Hourly": [],
            "Source": {"Attribution": "Data by uvindexapi.com", "Url": "https://uvindexapi.com"},
            "License": {"Id": "CC-BY-SA-4.0", "Name": "CC BY-SA 4.0", "Url": "https://creativecommons.org/licenses/by-sa/4.0/"}
        }),
        fetched_at=datetime.utcnow() - timedelta(hours=48)
    ))
    db.commit()

    with patch("services.uv_index_service.get_uv_forecast", return_value=None):
        response = UVIndexService.get_uv_index(db, -6.2, 106.8, timezone="Asia/Jakarta")

    assert response["now"]["uv_index"] == 9.5
    assert response["now"]["level"] == "Very High"
    assert response["cached"] is True

def test_uv_index_endpoint(client, db):
    with patch("helper.uvindex._fetch_api_json", return_value=MOCK_UV_API_RESPONSE):
        response = client.get("/api/v1/uv-index", params={"latitude": 40.7128, "longitude": -74.006, "hourly": "true"})

    assert response.status_code == 200
    body = response.json()
    assert body["latitude"] == 40.71
    assert body["now"]["level"] == "Moderate"
    assert body["today"]["max"]["uv_index"] == 6.8
    assert len(body["hourly"]) == 2
    assert len(body["daily"]) == 2
    assert body["license"]["id"] == "CC-BY-SA-4.0"

def test_uv_index_endpoint_validates_coordinates(client):
    response = client.get("/api/v1/uv-index", params={"latitude": 120, "longitude": -74.006})
    assert response.status_code == 422

def test_uv_index_endpoint_returns_502_when_source_unavailable(client):
    with patch("helper.uvindex._fetch_api_json", return_value=None):
        response = client.get("/api/v1/uv-index", params={"latitude": 1.5, "longitude": 2.5})
    assert response.status_code == 502
