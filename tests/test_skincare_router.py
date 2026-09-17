# tests/test_skincare_router.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers.skincare import router as skincare_router
from unittest.mock import patch

app = FastAPI()
app.include_router(skincare_router, prefix="/api/v1/skincare")
client = TestClient(app)

def test_skincare_recommendations_endpoint():
    fake_recs = {
        "recommendations": [{"product_name": "Moisturizer", "price": "50000", "product_image": "", "product_link": "", "match_reason": "Good for oily"}],
        "total_found": 1,
        "recommendation_count": 1,
        "skin_type": "oily"
    }
    with patch("routers.skincare.get_skin_type_recommendations", return_value=fake_recs):
        resp = client.post("/api/v1/skincare/recommendations", json={"skin_type": "oily", "top_k": 5})
        assert resp.status_code == 200
        assert resp.json()["recommendation_count"] == 1
        assert resp.json()["skin_type"] == "oily"
