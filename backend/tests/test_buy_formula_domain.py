"""Unit tests for buy_formula + assortment_matrix domain modules."""

import pytest
from backend.domains.buy_planning.buy_formula import (
    compute_promo_lifts, best_lift_for, compute_demand_buy, compute_display_qty,
    compute_safety_qty_statistical, binding_factor, build_sku_row,
    BuyFormulaService,
)
from backend.domains.buy_planning.assortment_matrix import (
    mixes_eligible_for_wedge, build_matrix, AssortmentMatrixService,
)
from backend.domains.buy_planning.safety_stock import DEFAULT_SAFETY_CONFIG
from backend.domains.buy_planning.sell_through import DEFAULT_SELL_THROUGH


# ═══════════════════════════════════════════════════════════════════
# buy_formula — pure functions.
# ═══════════════════════════════════════════════════════════════════

class TestComputePromoLifts:
    def test_empty(self):
        assert compute_promo_lifts([]) == {}

    def test_category_and_sku_separate(self):
        promos = [{"affected_categories": ["Tops"], "affected_skus": ["SKU1"], "lift_factor": 1.5}]
        lifts = compute_promo_lifts(promos)
        assert lifts == {"cat:Tops": 1.5, "sku:SKU1": 1.5}

    def test_overlapping_promos_take_max(self):
        promos = [
            {"affected_categories": ["Tops"], "affected_skus": [], "lift_factor": 1.3},
            {"affected_categories": ["Tops"], "affected_skus": [], "lift_factor": 2.0},
            {"affected_categories": ["Tops"], "affected_skus": [], "lift_factor": 1.1},
        ]
        assert compute_promo_lifts(promos)["cat:Tops"] == 2.0

    def test_missing_keys_safe(self):
        promos = [{"lift_factor": 2.0}]  # no affected_categories / skus
        assert compute_promo_lifts(promos) == {}


class TestBestLiftFor:
    def test_sku_beats_category_when_higher(self):
        lifts = {"cat:Tops": 1.3, "sku:A": 2.0}
        assert best_lift_for("A", "Tops", lifts) == 2.0

    def test_category_beats_sku_when_higher(self):
        lifts = {"cat:Tops": 2.5, "sku:A": 1.2}
        assert best_lift_for("A", "Tops", lifts) == 2.5

    def test_defaults_to_1(self):
        assert best_lift_for("A", "Tops", {}) == 1.0


class TestComputeDemandBuy:
    def test_no_soh_full_demand(self):
        fc, db = compute_demand_buy(
            daily_ros=10, cover_days=30, lift=1.0,
            sell_through_target=1.0, current_soh=0,
        )
        assert fc == 300
        assert db == 300

    def test_soh_subtracted(self):
        _, db = compute_demand_buy(
            daily_ros=10, cover_days=30, lift=1.0,
            sell_through_target=1.0, current_soh=100,
        )
        assert db == 200

    def test_demand_floored_at_zero(self):
        _, db = compute_demand_buy(
            daily_ros=1, cover_days=30, lift=1.0,
            sell_through_target=1.0, current_soh=500,
        )
        assert db == 0

    def test_lift_scales_forecast(self):
        fc, _ = compute_demand_buy(
            daily_ros=10, cover_days=30, lift=1.5,
            sell_through_target=1.0, current_soh=0,
        )
        assert fc == 450


class TestComputeDisplayQty:
    def test_core_reaches_all_wedges(self):
        disp_mins = {("Tops", "A"): 4, ("Tops", "B"): 3, ("Tops", "C"): 2}
        wedge_counts = {"A": 10, "B": 20, "C": 30}
        # Core → A+B+C: 4*10 + 3*20 + 2*30 = 40+60+60 = 160
        assert compute_display_qty(mix="Core", category="Tops",
                                    disp_mins=disp_mins, wedge_counts=wedge_counts) == 160

    def test_test_only_A(self):
        disp_mins = {("Tops", "A"): 4, ("Tops", "B"): 3, ("Tops", "C"): 2}
        wedge_counts = {"A": 10, "B": 20, "C": 30}
        assert compute_display_qty(mix="Test", category="Tops",
                                    disp_mins=disp_mins, wedge_counts=wedge_counts) == 40

    def test_falls_back_to_ALL_then_4(self):
        # No specific category entry — should use ("ALL", wedge) or default 4
        disp_mins = {("ALL", "A"): 5}
        wedge_counts = {"A": 10, "B": 10, "C": 10}
        # Core: ALL/A=5*10 + missing/B=4*10 + missing/C=4*10 = 50+40+40 = 130
        assert compute_display_qty(mix="Core", category="UnseenCat",
                                    disp_mins=disp_mins, wedge_counts=wedge_counts) == 130


class TestComputeSafetyQtyStatistical:
    def test_cap_at_max_weeks(self):
        # daily_ros huge → mad huge → raw huge → cap kicks in
        cfg = {"service_level": 0.95, "review_period_days": 1, "max_safety_weeks": 4}
        ss = compute_safety_qty_statistical(daily_ros=100, safety_cfg=cfg, lead_time_days=1000)
        mad = 100 * 0.3  # 30
        assert ss == 4 * mad  # 120

    def test_zero_ros_uses_floor_mad(self):
        ss = compute_safety_qty_statistical(daily_ros=0, safety_cfg=DEFAULT_SAFETY_CONFIG)
        # mad = 0.5 (floor); result > 0
        assert ss > 0


class TestBindingFactor:
    def test_demand_wins(self):
        assert binding_factor(demand_buy=100, display_qty=50, safety_qty=30) == "demand"

    def test_display_wins_when_higher(self):
        assert binding_factor(demand_buy=20, display_qty=100, safety_qty=30) == "display_min"

    def test_safety_wins_when_higher(self):
        assert binding_factor(demand_buy=20, display_qty=30, safety_qty=100) == "safety_stock"

    def test_demand_wins_on_tie(self):
        # Tie: demand should win (>= check)
        assert binding_factor(demand_buy=50, display_qty=50, safety_qty=50) == "demand"


class TestBuildSkuRow:
    def test_excluded_returns_none(self):
        inputs = {"excluded_skus": {"A"}, "ros_map": {}, "soh_map": {}, "promo_lifts": {},
                  "disp_mins": {}, "wedge_counts": {}}
        meta = {"style_mix": "Core", "category": "Tops", "sub_category": "T-shirt",
                "style": "S1", "mrp": 100}
        assert build_sku_row(sku="A", meta=meta, inputs=inputs, cover_days=30,
                              sell_targets=DEFAULT_SELL_THROUGH,
                              safety_cfg=DEFAULT_SAFETY_CONFIG) is None

    def test_happy_path_binding_factor_demand(self):
        inputs = {
            "excluded_skus": set(),
            "ros_map": {"SKU1": {"daily_ros": 10, "total_qty": 300, "revenue": 30000}},
            "soh_map": {"SKU1": 0},
            "promo_lifts": {},
            "disp_mins": {},
            "wedge_counts": {"A": 10, "B": 10, "C": 10},
        }
        meta = {"style_mix": "Core", "category": "Tops", "sub_category": "T-shirt",
                "style": "S1", "mrp": 100}
        row = build_sku_row(sku="SKU1", meta=meta, inputs=inputs, cover_days=30,
                             sell_targets={"Core": 1.0, "Fashion": 1.0, "Test": 1.0},
                             safety_cfg=DEFAULT_SAFETY_CONFIG)
        assert row is not None
        assert row["sku"] == "SKU1"
        # demand_buy = 1.0 * 10*30 - 0 = 300; display = 4*30 = 120; safety ~ small
        # → binding should be "demand"
        assert row["binding_factor"] == "demand"
        assert row["binding_constraint"] == "demand"  # legacy alias present
        assert row["buy_qty"] == 300


# ═══════════════════════════════════════════════════════════════════
# buy_formula — service orchestration with fake repo.
# ═══════════════════════════════════════════════════════════════════

class FakeFormulaRepo:
    def __init__(self):
        # Test-db shim: just a namespace with sell_through_config
        class _SellThroughCol:
            async def __aiter__(self): return self._iter()
            def __init__(self):
                self.docs = []
            def find(self, q, proj=None):
                return _AsyncCursor(self.docs)
        class _DB:
            def __init__(self):
                self.sell_through_config = _SellThroughCol()
        self._db = _DB()
        self.wedge_counts = {"A": 10, "B": 10, "C": 10}
        self.disp_mins = {}
        self.soh_map = {}
        self.ros_map = {}
        self.sku_meta = {}
        self.excluded_skus = set()
        self.active_promos = []
        self.safety_cfg = dict(DEFAULT_SAFETY_CONFIG)

    async def aggregate_wedge_counts(self, tenant_id): return dict(self.wedge_counts)
    async def load_display_minimums(self): return dict(self.disp_mins)
    async def aggregate_soh(self, tenant_id): return dict(self.soh_map)
    async def aggregate_ros(self, tenant_id, cover_days): return dict(self.ros_map)
    async def load_sku_meta(self, tenant_id): return dict(self.sku_meta)
    async def load_excluded_skus(self, tenant_id): return set(self.excluded_skus)
    async def load_active_promos(self, tenant_id): return list(self.active_promos)
    async def load_safety_cfg(self, tenant_id): return dict(self.safety_cfg)


class _AsyncCursor:
    def __init__(self, docs): self._docs = docs
    def __aiter__(self): return self
    async def __anext__(self):
        if not self._docs:
            raise StopAsyncIteration
        return self._docs.pop(0)


@pytest.mark.asyncio
async def test_formula_calculate_empty_returns_zero_skus():
    svc = BuyFormulaService(FakeFormulaRepo())
    out = await svc.calculate(tenant_id="t", cover_days=30, safety_days=7)
    assert out["sku_count"] == 0
    assert out["totals"]["total_buy_qty"] == 0


@pytest.mark.asyncio
async def test_formula_calculate_respects_explicit_override():
    repo = FakeFormulaRepo()
    repo.sku_meta = {"SKU1": {"style_mix": "Core", "category": "Tops", "sub_category": "",
                                "style": "S1", "mrp": 100}}
    repo.ros_map = {"SKU1": {"daily_ros": 10, "total_qty": 300, "revenue": 30000}}
    svc = BuyFormulaService(repo)
    out = await svc.calculate(
        tenant_id="t", cover_days=30, safety_days=7,
        sell_through_targets={"Core": 0.5, "Fashion": 0.5, "Test": 0.5},
    )
    assert out["parameters"]["sell_through_targets"]["Core"] == 0.5
    # demand_buy = 0.5 * 300 = 150; display = 4*30=120; max = 150
    assert out["buy_plan"][0]["buy_qty"] == 150


@pytest.mark.asyncio
async def test_formula_aggregates_totals_correctly():
    repo = FakeFormulaRepo()
    repo.sku_meta = {
        "A": {"style_mix": "Core", "category": "Tops", "sub_category": "", "style": "S1", "mrp": 100},
        "B": {"style_mix": "Core", "category": "Tops", "sub_category": "", "style": "S2", "mrp": 200},
    }
    repo.ros_map = {
        "A": {"daily_ros": 10, "total_qty": 300, "revenue": 0},
        "B": {"daily_ros": 5, "total_qty": 150, "revenue": 0},
    }
    svc = BuyFormulaService(repo)
    out = await svc.calculate(
        tenant_id="t", cover_days=30, safety_days=7,
        sell_through_targets={"Core": 1.0, "Fashion": 1.0, "Test": 1.0},
    )
    # Aggregate = sum of per-row qty/value. Exact values depend on display+safety.
    assert out["sku_count"] == 2
    total_qty = sum(r["buy_qty"] for r in out["buy_plan"])
    assert out["totals"]["total_buy_qty"] == total_qty


@pytest.mark.asyncio
async def test_formula_excludes_skus():
    repo = FakeFormulaRepo()
    repo.sku_meta = {
        "KEEP": {"style_mix": "Core", "category": "", "sub_category": "", "style": "", "mrp": 100},
        "DROP": {"style_mix": "Core", "category": "", "sub_category": "", "style": "", "mrp": 100},
    }
    repo.excluded_skus = {"DROP"}
    svc = BuyFormulaService(repo)
    out = await svc.calculate(tenant_id="t", cover_days=30, safety_days=7)
    assert out["sku_count"] == 1
    assert out["totals"]["excluded_skus"] == 1


# ═══════════════════════════════════════════════════════════════════
# assortment_matrix
# ═══════════════════════════════════════════════════════════════════

class TestMixesEligibleForWedge:
    def test_wedge_A_gets_all_mixes(self):
        assert set(mixes_eligible_for_wedge("A")) == {"Core", "Fashion", "Test"}

    def test_wedge_B_gets_core_fashion(self):
        assert set(mixes_eligible_for_wedge("B")) == {"Core", "Fashion"}

    def test_wedge_C_gets_core_only(self):
        assert mixes_eligible_for_wedge("C") == ["Core"]


class TestBuildMatrix:
    def test_structure(self):
        wedge_counts = {"A": {"count": 5}, "B": {"count": 10}, "C": {"count": 15}}
        mix_styles = {"Core": ["s1", "s2"], "Fashion": ["f1"], "Test": ["t1"]}
        m = build_matrix(wedge_counts, mix_styles)
        assert set(m.keys()) == {"A", "B", "C"}
        assert m["A"]["stores"] == 5
        assert m["A"]["styles"] == 4        # 2+1+1
        assert m["B"]["styles"] == 3        # 2+1 (no Test)
        assert m["C"]["styles"] == 2        # 2 (Core only)
        assert m["C"]["style_breakdown"] == {"Core": 2}

    def test_empty_wedge_counts(self):
        m = build_matrix({}, {"Core": []})
        assert m["A"]["stores"] == 0


class FakeMatrixRepo:
    def __init__(self, wedges=None, styles=None):
        self._wedges = wedges or {}
        self._styles = styles or {}

    async def aggregate_wedges_with_stores(self, tenant_id):
        return dict(self._wedges)

    async def aggregate_styles_by_mix(self):
        return dict(self._styles)


@pytest.mark.asyncio
async def test_matrix_service_happy():
    repo = FakeMatrixRepo(
        wedges={"A": {"count": 5, "stores": ["S1"]}, "B": {"count": 10, "stores": []}},
        styles={"Core": ["s1"], "Fashion": ["f1"]},
    )
    svc = AssortmentMatrixService(repo)
    out = await svc.get_matrix("t")
    assert out["core_styles"] == ["s1"]
    assert out["fashion_styles"] == ["f1"]
    assert out["test_styles"] == []
    assert out["matrix"]["A"]["stores"] == 5
