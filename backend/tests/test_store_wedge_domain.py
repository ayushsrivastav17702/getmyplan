"""Unit tests for the store_wedge domain (pure classifier + service orchestration)."""

import pytest
from backend.domains.buy_planning.store_wedge import (
    classify_wedge_by_cumulative_revenue,
    classify_stores_by_revenue,
    tier_to_wedge,
    StoreWedgeService,
    ValidationError,
    NotFoundError,
    NoDataError,
)


# ═══════════════════════════════════════════════════════════════════
# 1. Pure classifier — no I/O, no mocks, no async.
# ═══════════════════════════════════════════════════════════════════

class TestClassifyWedgeByCumulativeRevenue:
    def test_top_stores_are_A(self):
        assert classify_wedge_by_cumulative_revenue(0.50) == "A"
        assert classify_wedge_by_cumulative_revenue(0.80) == "A"

    def test_middle_stores_are_B(self):
        assert classify_wedge_by_cumulative_revenue(0.85) == "B"
        assert classify_wedge_by_cumulative_revenue(0.95) == "B"

    def test_tail_stores_are_C(self):
        assert classify_wedge_by_cumulative_revenue(0.96) == "C"
        assert classify_wedge_by_cumulative_revenue(1.00) == "C"


class TestClassifyStoresByRevenue:
    def test_empty_revenue_returns_empty(self):
        assert classify_stores_by_revenue([]) == []

    def test_all_zero_revenue_returns_empty(self):
        stores = [{"store_code": "S1", "total_revenue": 0}]
        assert classify_stores_by_revenue(stores) == []

    def test_pareto_distribution(self):
        # 4 stores: 80% + 15% + 3% + 2% = 100%
        stores = [
            {"store_code": "S1", "total_revenue": 80},
            {"store_code": "S2", "total_revenue": 15},
            {"store_code": "S3", "total_revenue": 3},
            {"store_code": "S4", "total_revenue": 2},
        ]
        result = classify_stores_by_revenue(stores)
        assert result[0]["store_code"] == "S1"
        assert result[0]["wedge_class"] == "A"
        assert result[0]["revenue_pct"] == 80.0
        assert result[1]["wedge_class"] == "B"   # cumulative 95%
        assert result[2]["wedge_class"] == "C"   # cumulative 98% > 95%
        assert result[3]["wedge_class"] == "C"

    def test_sorts_input_desc_by_revenue(self):
        # Given OUT-of-order input, top earner should still come first
        stores = [
            {"store_code": "small", "total_revenue": 30},
            {"store_code": "big", "total_revenue": 70},
        ]
        result = classify_stores_by_revenue(stores)
        assert result[0]["store_code"] == "big"
        assert result[0]["wedge_class"] == "A"   # 70% ≤ 80% → A

    def test_preserves_extra_fields(self):
        stores = [{"store_code": "S1", "total_revenue": 100, "total_qty": 50, "days_active": 30}]
        result = classify_stores_by_revenue(stores)
        assert result[0]["total_qty"] == 50
        assert result[0]["days_active"] == 30


class TestTierToWedge:
    def test_tier_a_maps_to_A(self):
        assert tier_to_wedge("A") == "A"

    def test_tier_b_maps_to_B(self):
        assert tier_to_wedge("B") == "B"

    def test_tier_c_maps_to_C(self):
        assert tier_to_wedge("C") == "C"

    def test_none_or_unknown_defaults_to_C(self):
        assert tier_to_wedge(None) == "C"
        assert tier_to_wedge("") == "C"
        assert tier_to_wedge("Z") == "C"


# ═══════════════════════════════════════════════════════════════════
# 2. Service layer orchestration — with fake repo.
# ═══════════════════════════════════════════════════════════════════

class FakeStoreWedgeRepo:
    def __init__(self):
        self.stores_revenue: list = []          # aggregated sales
        self.stores_master: list = []           # store_master docs
        self.current_wedges: dict = {}          # store_code → wedge
        self.applied: list = []                 # (store, wedge, rev)
        self.tier_fallbacks: list = []          # (store, wedge)
        self.audit_inserts: list = []
        self.overrides: list = []
        self.reverts: list = []
        self.existing_lookup: dict = {}         # store_code → {wedge_class}

    async def aggregate_revenue_by_store(self, tenant_id):
        return list(self.stores_revenue)

    async def list_stores(self, tenant_id):
        return list(self.stores_master)

    async def get_current_wedges(self, tenant_id):
        return dict(self.current_wedges)

    async def apply_classification(self, store_code, wedge, total_revenue, now_iso):
        self.applied.append((store_code, wedge, total_revenue))

    async def apply_tier_fallback(self, store_code, wedge):
        self.tier_fallbacks.append((store_code, wedge))

    async def insert_audit_entries(self, entries):
        self.audit_inserts.extend(entries)

    async def find_one_store(self, store_code):
        return self.existing_lookup.get(store_code)

    async def apply_manual_override(self, store_code, wedge, user_email, now_iso):
        self.existing_lookup[store_code] = {"wedge_class": wedge}

    async def record_override(self, **kw):
        self.overrides.append(kw)

    async def revert_override(self, store_code, user_email, now_iso):
        self.reverts.append((store_code, user_email))


@pytest.fixture
def svc():
    repo = FakeStoreWedgeRepo()
    return StoreWedgeService(repo), repo


# ─── classify() ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_classify_revenue_based_happy_path(svc):
    service, repo = svc
    repo.stores_revenue = [
        {"store_code": "S1", "total_revenue": 80},
        {"store_code": "S2", "total_revenue": 15},
        {"store_code": "S3", "total_revenue": 5},
    ]
    repo.current_wedges = {"S1": "B", "S2": "B", "S3": "B"}  # stale

    out = await service.classify(tenant_id="t1", user_email="u@x.com")

    assert out["success"] is True
    assert out["method"] == "revenue_based"
    assert out["total_revenue"] == 100
    assert out["summary"] == {"A": 1, "B": 1, "C": 1}
    # S1: B→A (change), S2: B→B (no change), S3: B→C (change) = 2 audits
    assert out["audit_changes"] == 2
    # master updates applied for all 3 stores
    assert {s[0] for s in repo.applied} == {"S1", "S2", "S3"}


@pytest.mark.asyncio
async def test_classify_tier_fallback_when_no_sales(svc):
    service, repo = svc
    repo.stores_revenue = []  # no sales
    repo.stores_master = [
        {"store_code": "S1", "tier": "A"},
        {"store_code": "S2", "tier": "B"},
        {"store_code": "S3", "tier": None},  # → C
    ]

    out = await service.classify(tenant_id="t1", user_email="u@x.com")

    assert out["method"] == "tier_fallback"
    assert out["summary"] == {"A": 1, "B": 1, "C": 1}
    assert len(repo.tier_fallbacks) == 3


@pytest.mark.asyncio
async def test_classify_raises_when_no_data_at_all(svc):
    service, repo = svc
    repo.stores_revenue = []
    repo.stores_master = []
    with pytest.raises(NoDataError):
        await service.classify(tenant_id="t1", user_email="u@x.com")


@pytest.mark.asyncio
async def test_classify_raises_when_all_zero_revenue(svc):
    service, repo = svc
    repo.stores_revenue = [{"store_code": "S1", "total_revenue": 0}]
    # Fallback kicks in because stores_revenue is non-empty but total_rev=0
    # Actually the service checks `if not stores_revenue` first; here it IS populated.
    with pytest.raises(NoDataError):
        await service.classify(tenant_id="t1", user_email="u@x.com")


@pytest.mark.asyncio
async def test_classify_audit_only_logs_changes(svc):
    service, repo = svc
    repo.stores_revenue = [
        {"store_code": "S1", "total_revenue": 80},
        {"store_code": "S2", "total_revenue": 20},
    ]
    # S1 computes A (80% cum), S2 computes C (100% cum).
    # Seed current: S1=A (unchanged), S2=B (changes → B→C).
    repo.current_wedges = {"S1": "A", "S2": "B"}

    await service.classify(tenant_id="t1", user_email="u@x.com")

    assert len(repo.audit_inserts) == 1
    assert repo.audit_inserts[0]["entity_id"] == "S2"
    assert repo.audit_inserts[0]["old_value"] == "B"
    assert repo.audit_inserts[0]["new_value"] == "C"


# ─── list_classifications() ───────────────────────────────────────

@pytest.mark.asyncio
async def test_list_empty(svc):
    service, repo = svc
    out = await service.list_classifications("t1")
    assert out["stores"] == []
    assert out["classified"] is False


@pytest.mark.asyncio
async def test_list_with_classifications(svc):
    service, repo = svc
    repo.stores_master = [
        {"store_code": "S1", "wedge_class": "A"},
        {"store_code": "S2", "wedge_class": "B"},
        {"store_code": "S3"},   # unclassified
    ]
    out = await service.list_classifications("t1")
    assert out["classified"] is True
    assert out["summary"] == {"A": 1, "B": 1, "C": 0}
    assert out["total"] == 3


# ─── override() ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_override_valid(svc):
    service, repo = svc
    repo.existing_lookup["S1"] = {"wedge_class": "C"}

    out = await service.override(
        store_code="S1", wedge="A", reason="Flagship",
        user_email="u@x.com", tenant_id="t1",
    )

    assert out == {"success": True, "store_code": "S1", "old": "C", "new": "A"}
    assert len(repo.overrides) == 1
    assert repo.overrides[0]["old"] == "C"
    assert repo.overrides[0]["new"] == "A"


@pytest.mark.asyncio
async def test_override_rejects_invalid_wedge(svc):
    service, repo = svc
    repo.existing_lookup["S1"] = {"wedge_class": "A"}
    with pytest.raises(ValidationError):
        await service.override(
            store_code="S1", wedge="Z", reason=None,
            user_email="u@x.com", tenant_id="t1",
        )


@pytest.mark.asyncio
async def test_override_rejects_unknown_store(svc):
    service, _ = svc
    with pytest.raises(NotFoundError):
        await service.override(
            store_code="GHOST", wedge="A", reason=None,
            user_email="u@x.com", tenant_id="t1",
        )


# ─── revert_override() ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_revert_override(svc):
    service, repo = svc
    out = await service.revert_override("S1", "u@x.com")
    assert out["success"] is True
    assert repo.reverts == [("S1", "u@x.com")]
