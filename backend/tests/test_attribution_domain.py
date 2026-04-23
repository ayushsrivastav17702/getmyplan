"""Unit tests for the attribution domain (pure rules + service orchestration)."""

import pytest
from backend.domains.buy_planning.attribution import (
    WEDGE_RULES,
    eligible_wedges_for_mix,
    compute_wedge_allocation,
    build_attribution_row,
    AttributionService,
)


# ═══════════════════════════════════════════════════════════════════
# 1. Pure rules — no I/O, no mocks, no async.
# ═══════════════════════════════════════════════════════════════════

class TestEligibleWedgesForMix:
    def test_core_reaches_all(self):
        assert eligible_wedges_for_mix("Core") == ["A", "B", "C"]

    def test_fashion_reaches_A_and_B(self):
        assert eligible_wedges_for_mix("Fashion") == ["A", "B"]

    def test_test_reaches_A_only(self):
        assert eligible_wedges_for_mix("Test") == ["A"]

    def test_unknown_mix_defaults_to_test_rules(self):
        assert eligible_wedges_for_mix("Premium") == ["A"]
        assert eligible_wedges_for_mix("") == ["A"]
        assert eligible_wedges_for_mix(None) == ["A"]   # type: ignore[arg-type]


class TestComputeWedgeAllocation:
    def test_core_allocates_proportionally(self):
        alloc = compute_wedge_allocation("Core", {"A": 10, "B": 20, "C": 70})
        assert alloc["A"]["eligible"] is True
        assert alloc["A"]["allocation_pct"] == 10.0
        assert alloc["B"]["allocation_pct"] == 20.0
        assert alloc["C"]["allocation_pct"] == 70.0

    def test_fashion_excludes_C(self):
        alloc = compute_wedge_allocation("Fashion", {"A": 10, "B": 30, "C": 60})
        assert alloc["C"]["eligible"] is False
        assert alloc["C"]["stores"] == 0
        # Only A+B = 40 eligible stores → A=25%, B=75%
        assert alloc["A"]["allocation_pct"] == 25.0
        assert alloc["B"]["allocation_pct"] == 75.0

    def test_test_only_A(self):
        alloc = compute_wedge_allocation("Test", {"A": 5, "B": 15, "C": 80})
        assert alloc["A"]["eligible"] is True
        assert alloc["A"]["allocation_pct"] == 100.0
        assert alloc["B"]["eligible"] is False
        assert alloc["C"]["eligible"] is False

    def test_zero_eligible_stores_safe(self):
        alloc = compute_wedge_allocation("Test", {"A": 0, "B": 5, "C": 5})
        # A is eligible but has 0 stores → not eligible path
        assert alloc["A"]["eligible"] is False   # 0 eligible_stores → falls to else
        assert alloc["A"]["allocation_pct"] == 0


class TestBuildAttributionRow:
    def test_core_style_full_coverage(self):
        row = build_attribution_row(
            style="TEE-001", mix="Core", sku_count=12,
            wedge_counts={"A": 5, "B": 5, "C": 10},
        )
        assert row["style"] == "TEE-001"
        assert row["sku_count"] == 12
        assert row["eligible_stores"] == 20
        assert row["total_stores"] == 20
        assert row["coverage_pct"] == 100.0

    def test_test_style_flagship_only(self):
        row = build_attribution_row(
            style="LUX-99", mix="Test", sku_count=3,
            wedge_counts={"A": 2, "B": 8, "C": 10},
        )
        assert row["eligible_stores"] == 2
        assert row["total_stores"] == 20
        assert row["coverage_pct"] == 10.0

    def test_no_stores_gives_zero_coverage(self):
        row = build_attribution_row(
            style="X", mix="Core", sku_count=1,
            wedge_counts={"A": 0, "B": 0, "C": 0},
        )
        # max(0,1) guard avoids divide-by-zero
        assert row["coverage_pct"] == 0.0


class TestWedgeRules:
    def test_three_mixes_present(self):
        assert set(WEDGE_RULES.keys()) == {"Core", "Fashion", "Test"}

    def test_rules_shape(self):
        for mix, rules in WEDGE_RULES.items():
            assert set(rules.keys()) == {"A", "B", "C"}


# ═══════════════════════════════════════════════════════════════════
# 2. Service layer — with fake repo.
# ═══════════════════════════════════════════════════════════════════

class FakeAttributionRepo:
    def __init__(self, wedge_counts=None, styles=None):
        self._wedge_counts = wedge_counts or {"A": 0, "B": 0, "C": 0}
        self._styles = styles or []

    async def aggregate_wedge_counts(self, tenant_id):
        return dict(self._wedge_counts)

    async def aggregate_styles_with_mix(self, tenant_id):
        return list(self._styles)


@pytest.mark.asyncio
async def test_get_matrix_empty():
    svc = AttributionService(FakeAttributionRepo())
    out = await svc.get_matrix("t1")
    assert out["total_styles"] == 0
    assert out["attributions"] == []
    assert out["store_counts"] == {"A": 0, "B": 0, "C": 0}
    assert out["rules"] == WEDGE_RULES


@pytest.mark.asyncio
async def test_get_matrix_sorted_by_coverage_desc():
    svc = AttributionService(FakeAttributionRepo(
        wedge_counts={"A": 5, "B": 10, "C": 35},
        styles=[
            {"style": "TEST-A", "style_mix": "Test", "sku_count": 2},      # coverage 10%
            {"style": "CORE-B", "style_mix": "Core", "sku_count": 5},      # coverage 100%
            {"style": "FASH-C", "style_mix": "Fashion", "sku_count": 8},   # coverage 30%
        ],
    ))
    out = await svc.get_matrix("t1")
    assert out["total_styles"] == 3
    coverages = [row["coverage_pct"] for row in out["attributions"]]
    assert coverages == sorted(coverages, reverse=True)
    assert out["attributions"][0]["style"] == "CORE-B"  # highest coverage first
    assert out["attributions"][-1]["style"] == "TEST-A"  # lowest coverage last
