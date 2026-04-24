"""Integration tests for Size Curve Optimization + Save-Recommendation (iter114)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://zip-improved.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def auth():
    r = requests.post(f"{API}/auth/login", json={"email": "admin@demo.com", "password": "demo1234"}, timeout=30)
    assert r.status_code == 200, r.text
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok
    return {"Authorization": f"Bearer {tok}"}


# ── Size Curve: categories ───────────────────────────────────────────────
def test_categories(auth):
    r = requests.get(f"{API}/analytics/size-curve/categories", headers=auth, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    # Accept either list or dict wrapper
    cats = data.get("categories") if isinstance(data, dict) else data
    assert isinstance(cats, list) and len(cats) >= 3
    # category key may be "name" or "category"
    key = "name" if "name" in cats[0] else "category"
    names = {c[key] for c in cats}
    assert {"Apparel", "Footwear", "Accessories"}.issubset(names)
    apparel = next(c for c in cats if c[key] == "Apparel")
    assert apparel.get("sku_count") == 112


# ── Corporate curve ──────────────────────────────────────────────────────
def test_corporate_curve_apparel(auth):
    r = requests.get(f"{API}/analytics/size-curve/corporate/Apparel", params={"days": 90}, headers=auth, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "curve" in d and "sizes" in d
    assert isinstance(d["curve"], dict) and len(d["curve"]) > 0
    total = sum(d["curve"].values())
    assert 99.0 <= total <= 101.0, f"curve sums to {total}"
    # sizes sorted desc by share
    shares = [d["curve"][s] for s in d["sizes"]]
    assert shares == sorted(shares, reverse=True)


def test_corporate_curve_bogus_400(auth):
    r = requests.get(f"{API}/analytics/size-curve/corporate/Bogus", params={"days": 90}, headers=auth, timeout=30)
    assert r.status_code == 400, r.text
    assert "No sales data" in r.text or "no sales" in r.text.lower()


# ── Recommend ────────────────────────────────────────────────────────────
def test_recommend(auth):
    body = {"category": "Apparel", "days": 90, "deviation_threshold_pp": 10, "min_units": 50}
    r = requests.post(f"{API}/analytics/size-curve/recommend", json=body, headers=auth, timeout=60)
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("corporate_curve", "stores", "outlier_count", "aligned_count"):
        assert k in d
    assert isinstance(d["stores"], list)
    if d["stores"]:
        s0 = d["stores"][0]
        for k in ("store_code", "total_units", "curve", "deviations", "max_abs_delta_pp", "is_outlier"):
            assert k in s0, f"missing {k} in store row"
        if s0["deviations"]:
            assert "delta_pp" in s0["deviations"][0]


# ── Allocate ─────────────────────────────────────────────────────────────
def test_allocate_corporate(auth):
    body = {"category": "Apparel", "total_qty": 1000, "days": 90}
    r = requests.post(f"{API}/analytics/size-curve/allocate", json=body, headers=auth, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("curve_source") == "corporate"
    alloc = d.get("allocation") or {}
    assert isinstance(alloc, dict) and alloc
    total = sum(alloc.values())
    assert total == 1000, f"expected 1000, got {total}"


def test_allocate_store(auth):
    body = {"category": "Apparel", "total_qty": 1000, "days": 90, "store_code": "DEL-01"}
    r = requests.post(f"{API}/analytics/size-curve/allocate", json=body, headers=auth, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("curve_source") == "store:DEL-01"
    alloc = d.get("allocation") or {}
    assert isinstance(alloc, dict) and alloc
    total = sum(alloc.values())
    assert total == 1000


def test_allocate_zero_422(auth):
    body = {"category": "Apparel", "total_qty": 0, "days": 90}
    r = requests.post(f"{API}/analytics/size-curve/allocate", json=body, headers=auth, timeout=30)
    assert r.status_code == 422, r.text


# ── Save-recommendation + list ───────────────────────────────────────────
def test_save_and_list_recommendation(auth):
    body = {
        "level_key": "category",
        "best_value": "Apparel",
        "vs_value": "Accessories",
        "ratio": 1.62,
        "message": "TEST_iter114 Apparel outsells Accessories 1.62x",
        "days": 90,
    }
    r = requests.post(f"{API}/analytics/attribute-grouping/save-recommendation",
                      json=body, headers=auth, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("success") is True
    assert d.get("status") == "pending"
    rec_id = d.get("rec_id")
    assert rec_id and len(rec_id) >= 16

    r2 = requests.get(f"{API}/analytics/attribute-grouping/recommendations",
                      headers=auth, timeout=30)
    assert r2.status_code == 200
    d2 = r2.json()
    recs = d2.get("recommendations", [])
    assert any(rec.get("rec_id") == rec_id for rec in recs), "saved rec not found in list"
    for rec in recs:
        assert "_id" not in rec, "Mongo _id must be excluded"
