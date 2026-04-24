"""End-to-end API tests for Attribute Grouping feature (iter 113)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://zip-improved.preview.emergentagent.com").rstrip("/")
CREDS = {"email": "admin@demo.com", "password": "demo1234"}


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=CREDS, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def client(token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s


# ─── /levels ────────────────────────────────────────────────────────────────

def test_levels_returns_discovered_list(client):
    r = client.get(f"{BASE_URL}/api/analytics/attribute-grouping/levels", timeout=60)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert "levels" in data and "sku_count" in data
    assert isinstance(data["levels"], list) and len(data["levels"]) >= 1
    keys = {lv["key"] for lv in data["levels"]}
    # Spec says "expect category, style, size, sku_type, sku_color ... at minimum"
    required = {"category", "style", "size"}
    missing = required - keys
    assert not missing, f"missing required levels: {missing}, got={keys}"
    # Each level carries sample values
    for lv in data["levels"]:
        assert "key" in lv and "name" in lv and "values" in lv
        assert "value_count" in lv


def test_levels_sku_count_positive(client):
    r = client.get(f"{BASE_URL}/api/analytics/attribute-grouping/levels", timeout=60)
    assert r.status_code == 200
    assert r.json()["sku_count"] > 0


# ─── /sales/{level_key} ─────────────────────────────────────────────────────

def test_sales_by_category(client):
    r = client.get(f"{BASE_URL}/api/analytics/attribute-grouping/sales/category?days=90", timeout=60)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data["level_key"] == "category"
    assert data["days"] == 90
    assert "data" in data and isinstance(data["data"], list)
    assert len(data["data"]) >= 1
    for row in data["data"]:
        for k in ("attribute_value", "unique_skus", "total_units",
                  "avg_units_per_sku", "total_value"):
            assert k in row, f"missing {k} in row {row}"


def test_sales_unknown_key_returns_400(client):
    r = client.get(f"{BASE_URL}/api/analytics/attribute-grouping/sales/UNKNOWN_KEY?days=30", timeout=60)
    assert r.status_code == 400, f"expected 400 got {r.status_code}: {r.text[:200]}"
    body = r.json()
    assert "Unknown" in (body.get("detail") or "")


def test_sales_invalid_days_clamped(client):
    r = client.get(f"{BASE_URL}/api/analytics/attribute-grouping/sales/category?days=9999", timeout=30)
    # Query validator enforces 1..365 -> FastAPI returns 422
    assert r.status_code == 422


# ─── /trends/{level_key} ────────────────────────────────────────────────────

def test_trends_sku_color(client):
    r = client.get(f"{BASE_URL}/api/analytics/attribute-grouping/trends/sku_color?days=60&limit=5", timeout=60)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert "trending" in data and "declining" in data
    assert isinstance(data["trending"], list) and isinstance(data["declining"], list)
    assert len(data["trending"]) <= 5
    for row in data["trending"]:
        for k in ("attribute_value", "growth_pct", "sku_count", "recent_sales", "old_sales"):
            assert k in row, f"missing {k}"


def test_trends_unknown_key_400(client):
    r = client.get(f"{BASE_URL}/api/analytics/attribute-grouping/trends/foo_bar?days=30", timeout=30)
    assert r.status_code == 400


# ─── POST /compare ──────────────────────────────────────────────────────────

def test_compare_two_categories(client):
    body = {"level_key": "category",
            "attribute_values": ["Apparel", "Footwear"], "days": 90}
    r = client.post(f"{BASE_URL}/api/analytics/attribute-grouping/compare", json=body, timeout=60)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert "comparison" in data and "best_performer" in data and "recommendations" in data
    if data["comparison"]:
        assert data["best_performer"] is not None
        for row in data["comparison"]:
            assert "avg_units_per_sku" in row
            assert row["attribute_value"] in body["attribute_values"]


def test_compare_single_value_fails_422(client):
    body = {"level_key": "category", "attribute_values": ["Apparel"], "days": 90}
    r = client.post(f"{BASE_URL}/api/analytics/attribute-grouping/compare", json=body, timeout=30)
    assert r.status_code == 422, f"expected 422 got {r.status_code}: {r.text[:200]}"


# ─── POST /forecast ─────────────────────────────────────────────────────────

def test_forecast_combination(client):
    body = {"attribute_combination": {"category": "Apparel", "gender": "Men"}, "days": 90}
    r = client.post(f"{BASE_URL}/api/analytics/attribute-grouping/forecast", json=body, timeout=60)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    for k in ("similar_skus_found", "forecast_daily_units",
              "forecast_monthly_units", "forecast_quarterly_units"):
        assert k in data, f"missing {k}"


def test_forecast_empty_fails_422(client):
    body = {"attribute_combination": {}, "days": 90}
    r = client.post(f"{BASE_URL}/api/analytics/attribute-grouping/forecast", json=body, timeout=30)
    assert r.status_code == 422


# ─── Regression: dependent features still up ────────────────────────────────

def test_regression_transfers_list(client):
    r = client.get(f"{BASE_URL}/api/transfers/optimize", timeout=30)
    # Endpoint may be GET or POST; accept 200/404/405 but NOT 500
    assert r.status_code != 500, f"transfers endpoint crashed: {r.text[:200]}"


def test_regression_dashboard_loads(client):
    r = client.get(f"{BASE_URL}/api/dashboard/stats", timeout=30)
    assert r.status_code in (200, 404), f"{r.status_code}: {r.text[:200]}"


def test_regression_buy_planning(client):
    r = client.get(f"{BASE_URL}/api/buy-planning/plans", timeout=30)
    assert r.status_code in (200, 404), f"{r.status_code}: {r.text[:200]}"
