import pytest
from fastapi.testclient import TestClient
from server import app
from helper.ingredients import (
    SKIN_TYPE_EXCEPTIONS,
    SKIN_TYPE_TIPS,
    get_avoided_ingredients_for_skin,
    ingredients_avoid_oily,
    ingredients_avoid_dry,
    ingredients_avoid_normal,
    ingredients_avoid_acne,
    ingredients_avoid_sensitive
)

client = TestClient(app)

def test_skin_type_exceptions_structure():
    expected_skin_types = ["sensitive", "oily", "dry", "combination", "acne-prone", "normal"]
    for skin_type in expected_skin_types:
        assert skin_type in SKIN_TYPE_EXCEPTIONS
        exceptions = SKIN_TYPE_EXCEPTIONS[skin_type]
        assert len(exceptions) > 0
        for item in exceptions:
            assert "name" in item
            assert "category" in item
            assert "reason" in item

def test_backward_compatibility_aliases():
    assert len(ingredients_avoid_oily) > 0
    assert len(ingredients_avoid_dry) > 0
    assert len(ingredients_avoid_normal) > 0
    assert len(ingredients_avoid_acne) > 0
    assert len(ingredients_avoid_sensitive) > 0

def test_get_avoided_ingredients_for_skin():
    sensitive_items = get_avoided_ingredients_for_skin("sensitive")
    assert any("Fragrance" in item["name"] for item in sensitive_items)

def test_ingredients_to_avoid_endpoint():
    response = client.get("/api/v1/skincare/ingredients-to-avoid?skin_type=oily")
    assert response.status_code == 200
    data = response.json()
    assert data["skin_type"] == "oily"
    assert "exceptions" in data
    assert "tips" in data
    assert len(data["exceptions"]) > 0
