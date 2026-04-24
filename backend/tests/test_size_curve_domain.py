"""Unit tests for the size_curve domain (pure layer — no Mongo)."""

from backend.domains.analytics.size_curve import (
    allocate_by_curve,
    build_store_category_curves,
    classify_stores,
    compute_corporate_curve,
    compute_deviations,
    normalize_distribution,
)


# ── normalize_distribution ──────────────────────────────────────────────────

def test_normalize_empty():
    assert normalize_distribution({}) == {}


def test_normalize_basic():
    out = normalize_distribution({"S": 10, "M": 20, "L": 20})
    assert out == {"S": 20.0, "M": 40.0, "L": 40.0}


def test_normalize_zero_total_returns_all_zero():
    assert normalize_distribution({"S": 0, "M": 0}) == {"S": 0.0, "M": 0.0}


# ── build_store_category_curves ─────────────────────────────────────────────

def test_build_ignores_skus_without_size_or_category():
    skus = [
        {"sku": "a", "category": "Apparel", "size": "M"},
        {"sku": "b", "category": None, "size": "L"},       # no cat → ignored
        {"sku": "c", "category": "Apparel", "size": None}, # no size → ignored
    ]
    sales = {("S1", "a"): 10, ("S1", "b"): 999, ("S1", "c"): 999}
    out = build_store_category_curves(skus, sales)
    assert list(out.keys()) == [("S1", "Apparel")]
    assert out[("S1", "Apparel")]["total_units"] == 10
    assert dict(out[("S1", "Apparel")]["sizes"]) == {"M": 10}


def test_build_aggregates_across_skus_same_size():
    skus = [
        {"sku": "a", "category": "Apparel", "size": "M"},
        {"sku": "b", "category": "Apparel", "size": "M"},
    ]
    sales = {("S1", "a"): 10, ("S1", "b"): 5}
    out = build_store_category_curves(skus, sales)
    assert dict(out[("S1", "Apparel")]["sizes"]) == {"M": 15}
    assert out[("S1", "Apparel")]["total_units"] == 15


# ── compute_corporate_curve ─────────────────────────────────────────────────

def test_corporate_curve_sums_across_stores():
    curves = {
        ("S1", "Apparel"): {"total_units": 100, "sizes": {"S": 50, "M": 50}},
        ("S2", "Apparel"): {"total_units": 100, "sizes": {"S": 25, "M": 75}},
        ("S3", "Footwear"): {"total_units": 999, "sizes": {"XL": 999}},
    }
    corp = compute_corporate_curve(curves, "Apparel")
    assert corp == {"S": 37.5, "M": 62.5}


def test_corporate_curve_empty_when_no_match():
    assert compute_corporate_curve({}, "Apparel") == {}


# ── compute_deviations ──────────────────────────────────────────────────────

def test_deviation_flags_over_and_under_and_sorts_by_abs():
    store = {"S": 30.0, "M": 40.0, "L": 30.0}
    corp = {"S": 25.0, "M": 30.0, "L": 45.0}
    rows = compute_deviations(store, corp)
    # L has biggest delta (|−15|), then M (+10), then S (+5)
    assert [r["size"] for r in rows] == ["L", "M", "S"]
    assert rows[0]["delta_pp"] == -15.0
    assert rows[0]["direction"] == "under"
    assert rows[1]["direction"] == "over"
    assert rows[2]["direction"] == "over"


def test_deviation_handles_size_missing_in_one_side():
    rows = compute_deviations({"S": 100.0}, {"M": 100.0})
    # Each size present once: S is +100 in store, M is −100 in store
    deltas = {r["size"]: r["delta_pp"] for r in rows}
    assert deltas == {"S": 100.0, "M": -100.0}


# ── classify_stores ─────────────────────────────────────────────────────────

def test_classify_separates_outliers_by_threshold():
    curves = {
        ("GOOD", "Apparel"): {"total_units": 1000,
                              "sizes": {"S": 250, "M": 250, "L": 250, "XL": 250}},
        ("OUTLIER", "Apparel"): {"total_units": 1000,
                                 "sizes": {"S": 500, "M": 200, "L": 200, "XL": 100}},
    }
    corp = {"S": 25.0, "M": 25.0, "L": 25.0, "XL": 25.0}
    result = classify_stores(
        curves, "Apparel", corp, deviation_threshold_pp=10.0, min_units=50,
    )
    assert result["aligned_count"] == 1
    assert result["outlier_count"] == 1
    assert result["stores"][0]["store_code"] == "OUTLIER"  # sorted biggest first


def test_classify_skips_stores_below_min_units():
    curves = {
        ("NOISE", "Apparel"): {"total_units": 5,
                               "sizes": {"S": 5}},
    }
    corp = {"S": 25.0, "M": 75.0}
    result = classify_stores(curves, "Apparel", corp, min_units=50)
    assert result["stores"] == []


# ── allocate_by_curve ───────────────────────────────────────────────────────

def test_allocate_sum_always_equals_total_qty():
    # Numbers chosen to exercise the largest-remainder rounding
    curve = {"S": 33.33, "M": 33.34, "L": 33.33}
    alloc = allocate_by_curve(100, curve)
    assert sum(alloc.values()) == 100
    # Each size should be ~33; nobody left out
    for v in alloc.values():
        assert 33 <= v <= 34


def test_allocate_respects_dominant_size():
    curve = {"S": 10.0, "M": 80.0, "L": 10.0}
    alloc = allocate_by_curve(100, curve)
    assert sum(alloc.values()) == 100
    assert alloc["M"] == 80


def test_allocate_handles_zero_total():
    assert allocate_by_curve(0, {"S": 100.0}) == {}


def test_allocate_handles_empty_curve():
    assert allocate_by_curve(100, {}) == {}
