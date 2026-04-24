"""Unit tests for Inter-Store Transfer (IST) optimization domain."""

import pytest
from backend.domains.buy_planning.transfers import (
    compute_dos, build_store_sku_metrics, identify_donors, identify_recipients,
    match_transfers_greedily, rank_by_uplift,
    TransfersService, NotFoundError, ValidationError, INF,
)


# ═══════════════════════════════════════════════════════════════════
# 1. Pure helpers
# ═══════════════════════════════════════════════════════════════════

class TestComputeDos:
    def test_normal(self):
        assert compute_dos(100, 5) == 20

    def test_zero_ros_is_infinite(self):
        assert compute_dos(100, 0) == INF

    def test_zero_soh_is_zero(self):
        assert compute_dos(0, 5) == 0

    def test_both_zero_is_infinite(self):
        assert compute_dos(0, 0) == INF


class TestBuildStoreSkuMetrics:
    def test_merges_both_sources(self):
        inv = {("A", "S1"): 100, ("B", "S1"): 50}
        sales = {("A", "S1"): {"total_qty": 30, "days": 30}, ("C", "S2"): {"total_qty": 10, "days": 10}}
        rows = build_store_sku_metrics(inv, sales)
        assert len(rows) == 3  # A/S1 merged, B/S1 inventory-only, C/S2 sales-only
        a = next(r for r in rows if (r["sku"], r["store_code"]) == ("A", "S1"))
        assert a["soh"] == 100
        assert a["daily_ros"] == 1.0
        assert a["dos"] == 100

    def test_zero_sales_row_has_inf_dos(self):
        rows = build_store_sku_metrics({("X", "S1"): 10}, {})
        assert rows[0]["dos"] == INF


class TestIdentifyDonors:
    def test_picks_high_dos(self):
        rows = [
            {"sku": "A", "store_code": "S1", "soh": 100, "daily_ros": 1, "dos": 100},
            {"sku": "A", "store_code": "S2", "soh": 50, "daily_ros": 5, "dos": 10},
        ]
        assert [d["store_code"] for d in identify_donors(rows, threshold_dos=45)] == ["S1"]

    def test_ignores_zero_soh(self):
        rows = [{"sku": "A", "store_code": "S1", "soh": 0, "daily_ros": 0, "dos": INF}]
        assert identify_donors(rows, threshold_dos=45) == []


class TestIdentifyRecipients:
    def test_picks_low_dos_with_sales(self):
        rows = [
            {"sku": "A", "store_code": "S1", "soh": 5, "daily_ros": 2, "dos": 2.5},
            {"sku": "A", "store_code": "S2", "soh": 100, "daily_ros": 1, "dos": 100},
        ]
        assert [r["store_code"] for r in identify_recipients(rows, threshold_dos=7)] == ["S1"]

    def test_rejects_zero_sales_even_if_low_stock(self):
        rows = [{"sku": "A", "store_code": "S1", "soh": 2, "daily_ros": 0, "dos": INF}]
        assert identify_recipients(rows, threshold_dos=7) == []


class TestMatchTransfersGreedily:
    def test_empty_when_no_donors(self):
        recipients = [{"sku": "A", "store_code": "S1", "soh": 2, "daily_ros": 1, "dos": 2}]
        assert match_transfers_greedily([], recipients) == []

    def test_empty_when_no_recipients(self):
        donors = [{"sku": "A", "store_code": "S1", "soh": 100, "daily_ros": 1, "dos": 100}]
        assert match_transfers_greedily(donors, []) == []

    def test_happy_path_single_match(self):
        donors = [{"sku": "A", "store_code": "D1", "soh": 100, "daily_ros": 1, "dos": 100}]
        recipients = [{"sku": "A", "store_code": "R1", "soh": 5, "daily_ros": 2, "dos": 2.5}]
        # Recipient wants 21 days × 2 = 42 units, has 5 → shortfall 37
        # Donor has 100, min_residual = 30 × 1 = 30, excess = 70
        # qty = min(37, 70) = 37
        suggestions = match_transfers_greedily(donors, recipients)
        assert len(suggestions) == 1
        s = suggestions[0]
        assert s["from_store"] == "D1"
        assert s["to_store"] == "R1"
        assert s["qty"] == 37
        assert s["recipient_daily_ros"] == 2
        assert s["donor_dos_after"] == 63.0  # (100-37)/1
        assert s["recipient_dos_after"] == 21.0  # (5+37)/2

    def test_donor_residual_respected(self):
        # Donor has 40 units @ 1 ros/day → min_residual 30 → excess 10
        # Recipient wants a lot → but donor only gives 10
        donors = [{"sku": "A", "store_code": "D1", "soh": 40, "daily_ros": 1, "dos": 40}]
        recipients = [{"sku": "A", "store_code": "R1", "soh": 2, "daily_ros": 5, "dos": 0.4}]
        suggestions = match_transfers_greedily(donors, recipients)
        assert suggestions[0]["qty"] == 10

    def test_min_transfer_qty_respected(self):
        # Donor has only 2 units excess — below min_transfer_qty=3 → skip
        donors = [{"sku": "A", "store_code": "D1", "soh": 32, "daily_ros": 1, "dos": 32}]
        recipients = [{"sku": "A", "store_code": "R1", "soh": 1, "daily_ros": 10, "dos": 0.1}]
        assert match_transfers_greedily(donors, recipients, min_transfer_qty=3) == []

    def test_scoped_per_sku(self):
        donors = [
            {"sku": "A", "store_code": "D1", "soh": 100, "daily_ros": 1, "dos": 100},
            {"sku": "B", "store_code": "D2", "soh": 100, "daily_ros": 1, "dos": 100},
        ]
        recipients = [
            {"sku": "A", "store_code": "R1", "soh": 5, "daily_ros": 2, "dos": 2.5},
        ]
        # Only SKU A has both donor and recipient → one suggestion
        suggestions = match_transfers_greedily(donors, recipients)
        assert len(suggestions) == 1
        assert suggestions[0]["sku"] == "A"

    def test_multiple_recipients_drain_donor(self):
        donors = [{"sku": "A", "store_code": "D1", "soh": 200, "daily_ros": 1, "dos": 200}]
        recipients = [
            {"sku": "A", "store_code": "R1", "soh": 0, "daily_ros": 2, "dos": 0},
            {"sku": "A", "store_code": "R2", "soh": 0, "daily_ros": 3, "dos": 0},
        ]
        suggestions = match_transfers_greedily(donors, recipients)
        # Both recipients served; total qty ≤ donor excess (170)
        assert len(suggestions) == 2
        assert sum(s["qty"] for s in suggestions) <= 170


class TestRankByUplift:
    def test_sorts_desc_by_value(self):
        suggestions = [
            {"sku": "CHEAP", "qty": 100, "recipient_daily_ros": 1, "from_store": "D", "to_store": "R"},
            {"sku": "LUX",   "qty": 10,  "recipient_daily_ros": 1, "from_store": "D", "to_store": "R"},
        ]
        mrp = {"CHEAP": 100, "LUX": 5000}
        ranked = rank_by_uplift(suggestions, mrp)
        # LUX: 10 × 1 × 5000 = 50,000
        # CHEAP: 100 × 1 × 100 = 10,000
        assert ranked[0]["sku"] == "LUX"
        assert ranked[0]["expected_uplift_value"] == 50_000
        assert ranked[1]["sku"] == "CHEAP"

    def test_missing_mrp_is_zero(self):
        suggestions = [{"sku": "X", "qty": 10, "recipient_daily_ros": 1, "from_store": "D", "to_store": "R"}]
        ranked = rank_by_uplift(suggestions, {})
        assert ranked[0]["expected_uplift_value"] == 0
        assert ranked[0]["mrp"] == 0


# ═══════════════════════════════════════════════════════════════════
# 2. Service orchestration — with fake repo
# ═══════════════════════════════════════════════════════════════════

class FakeTransfersRepo:
    def __init__(self):
        self.soh = {}
        self.sales = {}
        self.mrp = {}
        self.style_meta = {}
        self.saved = []
        self.batches = []

    async def load_latest_soh(self, tenant_id):
        return dict(self.soh)

    async def aggregate_ros(self, tenant_id, lookback_days):
        return dict(self.sales)

    async def load_mrp_map(self, tenant_id):
        return dict(self.mrp)

    async def load_sku_style_map(self, tenant_id):
        return dict(self.style_meta)

    async def save_batch(self, doc):
        self.saved.append(doc)
        self.batches.append(doc)
        return doc["batch_id"]

    async def list_batches(self, tenant_id, status, limit):
        rows = [b for b in self.batches if b["tenant_id"] == tenant_id]
        if status:
            rows = [r for r in rows if r.get("status") == status]
        return rows[:limit]

    async def get_batch(self, tenant_id, batch_id):
        for b in self.batches:
            if b["tenant_id"] == tenant_id and b["batch_id"] == batch_id:
                return b
        return None

    async def update_status(self, *, tenant_id, batch_id, status, user_email, now_iso):
        for b in self.batches:
            if b["tenant_id"] == tenant_id and b["batch_id"] == batch_id:
                b["status"] = status
                return 1
        return 0


@pytest.mark.asyncio
async def test_optimize_empty_inputs():
    svc = TransfersService(FakeTransfersRepo())
    out = await svc.optimize(tenant_id="t")
    assert out["recommendations"] == []
    assert out["summary"]["suggestion_count"] == 0


@pytest.mark.asyncio
async def test_optimize_end_to_end():
    repo = FakeTransfersRepo()
    # Store D1 over-stocked on SKU A, R1 running low and selling fast
    repo.soh = {("A", "D1"): 100, ("A", "R1"): 5}
    repo.sales = {
        ("A", "D1"): {"total_qty": 30, "days": 30},  # 1/day
        ("A", "R1"): {"total_qty": 60, "days": 30},  # 2/day
    }
    repo.mrp = {"A": 500}
    repo.style_meta = {"A": {"style": "STY-1", "category": "Tops", "style_mix": "Core"}}
    svc = TransfersService(repo)
    out = await svc.optimize(tenant_id="t")
    assert out["summary"]["suggestion_count"] == 1
    rec = out["recommendations"][0]
    assert rec["sku"] == "A"
    assert rec["from_store"] == "D1"
    assert rec["to_store"] == "R1"
    assert rec["qty"] > 0
    assert rec["style"] == "STY-1"
    assert rec["expected_uplift_value"] > 0


@pytest.mark.asyncio
async def test_generate_batch_persists():
    repo = FakeTransfersRepo()
    repo.soh = {("A", "D"): 100, ("A", "R"): 0}
    repo.sales = {("A", "D"): {"total_qty": 30, "days": 30}, ("A", "R"): {"total_qty": 60, "days": 30}}
    repo.mrp = {"A": 100}
    svc = TransfersService(repo)
    out = await svc.generate_batch(tenant_id="t", user_email="u@x.com")
    assert out["success"]
    assert out["batch_id"].startswith("IST-")
    assert len(repo.saved) == 1
    assert repo.saved[0]["status"] == "draft"


@pytest.mark.asyncio
async def test_transition_happy_path():
    repo = FakeTransfersRepo()
    repo.batches.append({"tenant_id": "t", "batch_id": "B1", "status": "draft"})
    svc = TransfersService(repo)
    out = await svc.transition(tenant_id="t", batch_id="B1", new_status="approved", user_email="u")
    assert out["status"] == "approved"


@pytest.mark.asyncio
async def test_transition_illegal():
    repo = FakeTransfersRepo()
    repo.batches.append({"tenant_id": "t", "batch_id": "B1", "status": "draft"})
    svc = TransfersService(repo)
    # Cannot jump draft → executed
    with pytest.raises(ValidationError):
        await svc.transition(tenant_id="t", batch_id="B1", new_status="executed", user_email="u")


@pytest.mark.asyncio
async def test_transition_unknown_status():
    svc = TransfersService(FakeTransfersRepo())
    with pytest.raises(ValidationError):
        await svc.transition(tenant_id="t", batch_id="B1", new_status="teleported", user_email="u")


@pytest.mark.asyncio
async def test_transition_not_found():
    svc = TransfersService(FakeTransfersRepo())
    with pytest.raises(NotFoundError):
        await svc.transition(tenant_id="t", batch_id="GHOST", new_status="approved", user_email="u")


@pytest.mark.asyncio
async def test_get_batch_not_found():
    svc = TransfersService(FakeTransfersRepo())
    with pytest.raises(NotFoundError):
        await svc.get_batch(tenant_id="t", batch_id="GHOST")
