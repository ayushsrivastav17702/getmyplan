"""Unit tests for the attribute_grouping domain (pure layer — no Mongo)."""

from backend.domains.analytics.attribute_grouping import (
    compare_attribute_values,
    compute_trend_split,
    discover_levels,
    forecast_new_combination,
    group_sales_by_attribute,
    merge_sku_and_style,
    parse_sku_tokens,
)


# ── parse_sku_tokens ────────────────────────────────────────────────────────

def test_parse_sku_tokens_two_tokens():
    assert parse_sku_tokens("POLO-BLK") == {"sku_type": "POLO", "sku_color": "BLK"}


def test_parse_sku_tokens_three_tokens():
    assert parse_sku_tokens("TSHIRT-BLK-M") == {"sku_type": "TSHIRT", "sku_color": "BLK"}


def test_parse_sku_tokens_five_tokens():
    assert parse_sku_tokens("STYLE-TS-002-PNK-S") == {
        "sku_type": "TS", "sku_color": "PNK",
    }


def test_parse_sku_tokens_single_token():
    assert parse_sku_tokens("POLO") == {"sku_type": "POLO"}


def test_parse_sku_tokens_empty_and_none():
    assert parse_sku_tokens("") == {}
    assert parse_sku_tokens(None) == {}


# ── merge_sku_and_style ─────────────────────────────────────────────────────

def test_merge_pulls_scalars_from_style_master():
    sku = {"sku": "STYLE-TS-001-BLK-S", "style": "STYLE-TS-001", "size": "S", "mrp": 999}
    style = {
        "_id": "ignoreme", "tenant_id": "t1", "style_code": "STYLE-TS-001",
        "category": "Apparel", "sub_category": "T-Shirts", "brand": "Nike",
        "gender": "Unisex", "season": "All Year",
    }
    merged = merge_sku_and_style(sku, style)
    assert merged["category"] == "Apparel"
    assert merged["brand"] == "Nike"
    assert merged["gender"] == "Unisex"
    assert merged["season"] == "All Year"
    # Internal keys must never bubble up
    assert "_id" not in merged
    assert "tenant_id" not in merged
    assert "style_code" not in merged
    # Derived tokens present
    assert merged["sku_type"] == "TS"
    assert merged["sku_color"] == "BLK"


def test_merge_with_no_style_doc():
    sku = {"sku": "POLO-BLU-L", "style": "POLO", "size": "L"}
    merged = merge_sku_and_style(sku, None)
    assert merged["style"] == "POLO"
    assert merged["sku_color"] == "BLU"
    assert "category" not in merged  # no style-master doc to pull from


def test_merge_attributes_subobject_overrides():
    sku = {"sku": "X-BLK-M", "attributes": {"fabric": "Cotton", "fit": "Slim"}}
    merged = merge_sku_and_style(sku, None)
    assert merged["fabric"] == "Cotton"
    assert merged["fit"] == "Slim"


# ── discover_levels ─────────────────────────────────────────────────────────

def test_discover_levels_orders_base_then_extras():
    skus = [
        {"sku": "a", "category": "Apparel", "brand": "Nike", "fabric": "Cotton"},
        {"sku": "b", "category": "Footwear", "brand": "Adidas", "fabric": "Leather"},
    ]
    levels = discover_levels(skus)
    keys = [lv["key"] for lv in levels]
    # category comes before brand (base level) and before fabric (extras at end)
    assert keys.index("category") < keys.index("fabric")


def test_discover_levels_skips_empty():
    skus = [{"sku": "a", "category": "", "brand": None, "season": "Summer"}]
    levels = discover_levels(skus)
    keys = [lv["key"] for lv in levels]
    assert "category" not in keys
    assert "brand" not in keys
    assert "season" in keys


def test_discover_levels_sample_values():
    skus = [{"sku": "a", "category": "Apparel"}, {"sku": "b", "category": "Footwear"}]
    [cat] = [lv for lv in discover_levels(skus) if lv["key"] == "category"]
    assert sorted(cat["values"]) == ["Apparel", "Footwear"]
    assert cat["value_count"] == 2


# ── group_sales_by_attribute ────────────────────────────────────────────────

def test_group_sales_sums_and_averages():
    skus = [
        {"sku": "s1", "color": "BLU"}, {"sku": "s2", "color": "BLU"},
        {"sku": "s3", "color": "RED"},
    ]
    sales = {
        "s1": {"units": 100, "value": 10000.0},
        "s2": {"units": 200, "value": 20000.0},
        "s3": {"units": 50,  "value": 5000.0},
    }
    rows = group_sales_by_attribute(skus, sales, "color")
    blu = next(r for r in rows if r["attribute_value"] == "BLU")
    assert blu["total_units"] == 300
    assert blu["unique_skus"] == 2
    assert blu["avg_units_per_sku"] == 150.0
    # Sorted desc by total_units
    assert rows[0]["attribute_value"] == "BLU"


def test_group_sales_ignores_empty_attribute():
    skus = [{"sku": "s1", "color": "BLU"}, {"sku": "s2", "color": None}]
    sales = {"s1": {"units": 10, "value": 0}, "s2": {"units": 999, "value": 0}}
    rows = group_sales_by_attribute(skus, sales, "color")
    assert len(rows) == 1
    assert rows[0]["total_units"] == 10


# ── compute_trend_split ─────────────────────────────────────────────────────

def test_trend_split_detects_growth_and_decline():
    skus = [{"sku": "s1", "color": "BLU"}, {"sku": "s2", "color": "RED"}]
    old = {"s1": {"units": 100}, "s2": {"units": 100}}
    recent = {"s1": {"units": 200}, "s2": {"units": 50}}
    result = compute_trend_split(skus, recent, old, "color")
    top = result["trending"][0]
    bottom = result["declining"][0]
    assert top["attribute_value"] == "BLU" and top["growth_pct"] == 100.0
    assert bottom["attribute_value"] == "RED" and bottom["growth_pct"] == -50.0


def test_trend_split_new_value_caps_at_100():
    skus = [{"sku": "s1", "color": "BLU"}]
    result = compute_trend_split(
        skus,
        sales_recent={"s1": {"units": 500}},
        sales_old={},
        attribute_key="color",
    )
    assert result["trending"][0]["growth_pct"] == 100.0


# ── compare_attribute_values ────────────────────────────────────────────────

def test_compare_flags_best_performer_and_ratio():
    grouped = [
        {"attribute_value": "A", "avg_units_per_sku": 300, "total_units": 600, "unique_skus": 2},
        {"attribute_value": "B", "avg_units_per_sku": 100, "total_units": 100, "unique_skus": 1},
    ]
    result = compare_attribute_values(grouped, ["A", "B"])
    assert result["best_performer"]["attribute_value"] == "A"
    assert result["recommendations"][0]["ratio"] == 3.0
    assert "A sells 3.0× better" in result["recommendations"][0]["message"]


def test_compare_no_recommendation_when_ratio_under_threshold():
    grouped = [
        {"attribute_value": "A", "avg_units_per_sku": 120, "total_units": 120, "unique_skus": 1},
        {"attribute_value": "B", "avg_units_per_sku": 100, "total_units": 100, "unique_skus": 1},
    ]
    result = compare_attribute_values(grouped, ["A", "B"])
    assert result["best_performer"]["attribute_value"] == "A"
    assert result["recommendations"] == []


def test_compare_missing_value_is_skipped():
    grouped = [{"attribute_value": "A", "avg_units_per_sku": 100, "total_units": 100, "unique_skus": 1}]
    result = compare_attribute_values(grouped, ["A", "GHOST"])
    assert len(result["comparison"]) == 1


# ── forecast_new_combination ────────────────────────────────────────────────

def test_forecast_requires_non_empty_combo():
    assert "error" in forecast_new_combination([], {}, {})


def test_forecast_finds_similar_and_averages():
    skus = [
        {"sku": "a", "category": "Apparel", "color": "BLU"},
        {"sku": "b", "category": "Apparel", "color": "BLU"},  # 100% match
        {"sku": "c", "category": "Apparel", "color": "RED"},  # 50% match
        {"sku": "d", "category": "Footwear", "color": "BLK"},  # 0% match → excluded
    ]
    sales = {
        "a": {"units": 90}, "b": {"units": 90},
        "c": {"units": 30}, "d": {"units": 999},
    }
    result = forecast_new_combination(
        skus, sales,
        {"category": "Apparel", "color": "BLU"}, lookback_days=30,
    )
    assert result["similar_skus_found"] == 3  # a, b, c
    assert result["avg_similarity"] > 0.5
    # (90 + 90 + 30) / 3 / 30 = 2.33 daily
    assert abs(result["forecast_daily_units"] - 2.33) < 0.01


def test_forecast_zero_when_no_matches_meet_threshold():
    skus = [{"sku": "a", "category": "Apparel"}]
    result = forecast_new_combination(
        skus, {"a": {"units": 999}}, {"category": "Footwear"}, min_similarity=0.5,
    )
    assert result["similar_skus_found"] == 0
    assert result["forecast_daily_units"] == 0.0
