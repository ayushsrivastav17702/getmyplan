"""Unit tests for sell_through, store_attributes, inventory, safety_stock,
binding_analytics, and buy_plans domain modules (service + pure helpers)."""

import pytest
from backend.domains.buy_planning.sell_through import (
    SellThroughService, DEFAULT_SELL_THROUGH, ValidationError as SellValErr,
)
from backend.domains.buy_planning.store_attributes import (
    StoreAttributesService, validate_and_build_updates,
    NotFoundError as StoreAttrNotFound, ValidationError as StoreAttrValErr,
    VALID_FORMATS, VALID_TIERS, VALID_REGIONS,
)
from backend.domains.buy_planning.inventory import (
    InventoryService, MAX_BULK_RECORDS, ValidationError as InvValErr,
)
from backend.domains.buy_planning.safety_stock import (
    SafetyStockService, compute_safety_stock, z_score_for, validate_config,
    ValidationError as SafetyValErr,
)
from backend.domains.buy_planning.binding_analytics import (
    BindingAnalyticsService, compute_binding_breakdown,
    aggregate_worst_categories, build_trend_series,
    ForbiddenError as BAForbidden,
)
from backend.domains.buy_planning.buy_plans import (
    BuyPlansService, APPROVAL_ACTIONS, APPROVAL_ROLES,
    NotFoundError as BPNotFound, ValidationError as BPValErr, ForbiddenError as BPForbidden,
)


# ═══════════════════════════════════════════════════════════════════
# sell_through
# ═══════════════════════════════════════════════════════════════════

class FakeSellThroughRepo:
    def __init__(self):
        self._stored = {}
        self._audits = []

    async def list_stored(self):
        return dict(self._stored)

    async def get_current(self, style_mix):
        return {"target_multiplier": self._stored[style_mix]["target_multiplier"]} if style_mix in self._stored else None

    async def upsert(self, *, style_mix, multiplier, user_email, now_iso):
        self._stored[style_mix] = {"target_multiplier": multiplier, "updated_by": user_email, "updated_at": now_iso}

    async def delete_all(self):
        self._stored.clear()

    async def append_audit(self, entry):
        self._audits.append(entry)

    async def get_targets(self):
        targets = dict(DEFAULT_SELL_THROUGH)
        targets.update({k: v["target_multiplier"] for k, v in self._stored.items()})
        return targets


@pytest.mark.asyncio
async def test_sell_through_list_returns_defaults_when_empty():
    svc = SellThroughService(FakeSellThroughRepo())
    out = await svc.list_configs()
    assert len(out["configs"]) == 3
    assert all(c["is_default"] for c in out["configs"])


@pytest.mark.asyncio
async def test_sell_through_rejects_invalid_mix():
    svc = SellThroughService(FakeSellThroughRepo())
    with pytest.raises(SellValErr):
        await svc.set_config(style_mix="Premium", multiplier=1.5, user_email="u", tenant_id="t")


@pytest.mark.asyncio
async def test_sell_through_rejects_out_of_range():
    svc = SellThroughService(FakeSellThroughRepo())
    with pytest.raises(SellValErr):
        await svc.set_config(style_mix="Core", multiplier=10, user_email="u", tenant_id="t")


@pytest.mark.asyncio
async def test_sell_through_audit_only_when_changed():
    repo = FakeSellThroughRepo()
    svc = SellThroughService(repo)
    # Set same as default 1.2 → no change, no audit
    await svc.set_config(style_mix="Core", multiplier=1.2, user_email="u", tenant_id="t")
    assert len(repo._audits) == 0
    # Change it → audit entry
    await svc.set_config(style_mix="Core", multiplier=1.5, user_email="u", tenant_id="t")
    assert len(repo._audits) == 1


@pytest.mark.asyncio
async def test_sell_through_reset_clears_stored():
    repo = FakeSellThroughRepo()
    svc = SellThroughService(repo)
    await svc.set_config(style_mix="Core", multiplier=2.0, user_email="u", tenant_id="t")
    out = await svc.reset()
    assert out["defaults"] == DEFAULT_SELL_THROUGH
    assert repo._stored == {}


# ═══════════════════════════════════════════════════════════════════
# store_attributes
# ═══════════════════════════════════════════════════════════════════

class TestValidateAndBuildUpdates:
    def test_empty_raises(self):
        with pytest.raises(StoreAttrValErr, match="No attributes"):
            validate_and_build_updates(store_format=None, city_tier=None, region=None, area_sqft=None)

    def test_bad_format(self):
        with pytest.raises(StoreAttrValErr, match="store_format"):
            validate_and_build_updates(store_format="warehouse", city_tier=None, region=None, area_sqft=None)

    def test_bad_tier(self):
        with pytest.raises(StoreAttrValErr, match="city_tier"):
            validate_and_build_updates(store_format=None, city_tier="tier9", region=None, area_sqft=None)

    def test_bad_region(self):
        with pytest.raises(StoreAttrValErr, match="region"):
            validate_and_build_updates(store_format=None, city_tier=None, region="Atlantis", area_sqft=None)

    def test_valid_all_fields(self):
        out = validate_and_build_updates(
            store_format="hypermarket", city_tier="tier1", region="North", area_sqft=5000,
        )
        assert out == {"store_format": "hypermarket", "city_tier": "tier1", "region": "North", "area_sqft": 5000}

    def test_valid_partial(self):
        out = validate_and_build_updates(store_format="supermarket", city_tier=None, region=None, area_sqft=None)
        assert out == {"store_format": "supermarket"}


class FakeStoreAttrsRepo:
    def __init__(self, exists=True):
        self._exists = exists
        self.applied = {}
        self.audits = []

    async def find_store(self, store_code):
        return {"store_code": store_code} if self._exists else None

    async def apply_updates(self, store_code, updates):
        self.applied = dict(updates)

    async def append_audit(self, entry):
        self.audits.append(entry)


@pytest.mark.asyncio
async def test_store_attrs_not_found():
    svc = StoreAttributesService(FakeStoreAttrsRepo(exists=False))
    with pytest.raises(StoreAttrNotFound):
        await svc.update(store_code="GHOST", store_format="hypermarket",
                         user_email="u", tenant_id="t")


@pytest.mark.asyncio
async def test_store_attrs_audits_per_field():
    repo = FakeStoreAttrsRepo()
    svc = StoreAttributesService(repo)
    out = await svc.update(
        store_code="S1", store_format="hypermarket", city_tier="tier1",
        user_email="u", tenant_id="t",
    )
    # 2 real field changes → 2 audit entries (plus attributes_updated_* skipped)
    assert len(repo.audits) == 2
    assert {"store_format", "city_tier"} <= set(out["updated"])


def test_store_attrs_constants_shape():
    assert "hypermarket" in VALID_FORMATS
    assert "tier1" in VALID_TIERS
    assert "North" in VALID_REGIONS


# ═══════════════════════════════════════════════════════════════════
# inventory
# ═══════════════════════════════════════════════════════════════════

class FakeInventoryRepo:
    def __init__(self):
        self.records = []
        self.sync_logs = []

    async def upsert_record(self, **kw):
        class Result:
            def __init__(self, upserted_id, modified_count):
                self.upserted_id = upserted_id
                self.modified_count = modified_count
        self.records.append(kw)
        return Result(upserted_id=len(self.records), modified_count=0)

    async def insert_sync_log(self, entry):
        self.sync_logs.append(entry)

    async def list_records(self, *, tenant_id, store_code, sku, limit):
        rows = [r for r in self.records if r["tenant_id"] == tenant_id]
        if store_code:
            rows = [r for r in rows if r.get("store_code") == store_code]
        return rows[:limit]

    async def count(self, tenant_id):
        return len([r for r in self.records if r["tenant_id"] == tenant_id])

    async def summary_aggregation(self, tenant_id):
        rows = [r for r in self.records if r["tenant_id"] == tenant_id]
        if not rows:
            return None
        return {
            "total_soh": sum(r.get("soh", 0) for r in rows),
            "total_in_transit": sum(r.get("in_transit", 0) for r in rows),
            "total_open_po": sum(r.get("open_po_qty", 0) for r in rows),
            "unique_stores": list({r.get("store_code") for r in rows}),
            "unique_skus": list({r.get("sku") for r in rows}),
        }

    async def last_sync(self, tenant_id):
        ts = [s for s in self.sync_logs if s["tenant_id"] == tenant_id]
        return ts[-1] if ts else None


@pytest.mark.asyncio
async def test_inventory_bulk_empty_rejected():
    svc = InventoryService(FakeInventoryRepo())
    with pytest.raises(InvValErr):
        await svc.bulk_upload(tenant_id="t", records=[], source="api", user_email="u")


@pytest.mark.asyncio
async def test_inventory_bulk_oversize_rejected():
    svc = InventoryService(FakeInventoryRepo())
    with pytest.raises(InvValErr, match=f"{MAX_BULK_RECORDS:,}"):
        await svc.bulk_upload(
            tenant_id="t", records=[{}] * (MAX_BULK_RECORDS + 1),
            source="api", user_email="u",
        )


@pytest.mark.asyncio
async def test_inventory_bulk_happy_and_syncs_log():
    repo = FakeInventoryRepo()
    svc = InventoryService(repo)
    out = await svc.bulk_upload(
        tenant_id="t",
        records=[{"store_code": "S1", "sku": "A", "soh": 10}],
        source="api", user_email="u",
    )
    assert out["inserted"] == 1
    assert len(repo.sync_logs) == 1


@pytest.mark.asyncio
async def test_inventory_summary_empty_returns_zeros():
    svc = InventoryService(FakeInventoryRepo())
    out = await svc.summary("t")
    assert out["total_soh"] == 0
    assert out["unique_stores"] == 0


# ═══════════════════════════════════════════════════════════════════
# safety_stock
# ═══════════════════════════════════════════════════════════════════

class TestSafetyStockMath:
    def test_z_score_for_known(self):
        assert z_score_for(0.95) == 1.645
        assert z_score_for(0.99) == 2.326

    def test_z_score_for_unknown_defaults(self):
        assert z_score_for(0.123) == 1.645

    def test_compute_safety_stock_capped_at_max_weeks(self):
        # z=3, MAD=10, LT=100, RP=1 → raw = 3*10*sqrt(100) = 300
        # max_weeks=12 * mad=10 = 120 → cap
        ss = compute_safety_stock(mad=10, z=3, lead_time_days=100,
                                   review_period_days=1, max_safety_weeks=12)
        assert ss == 120

    def test_compute_safety_stock_zero_mad_is_zero(self):
        ss = compute_safety_stock(mad=0, z=1.645, lead_time_days=14,
                                   review_period_days=7, max_safety_weeks=12)
        assert ss == 0

    def test_validate_config_bad_service_level(self):
        with pytest.raises(SafetyValErr, match="service_level"):
            validate_config(service_level=0.77, review_period_days=7, max_safety_weeks=12)

    def test_validate_config_bad_review_period(self):
        with pytest.raises(SafetyValErr, match="review_period"):
            validate_config(service_level=0.95, review_period_days=60, max_safety_weeks=12)

    def test_validate_config_bad_max_weeks(self):
        with pytest.raises(SafetyValErr, match="max_safety_weeks"):
            validate_config(service_level=0.95, review_period_days=7, max_safety_weeks=100)


class FakeSafetyRepo:
    def __init__(self):
        self.cfg = None
        self.errors = [2.0, 3.0, 4.0]

    async def get_config(self, tenant_id):
        return self.cfg

    async def upsert_config(self, **kw):
        self.cfg = dict(kw)

    async def delete_config(self, tenant_id):
        self.cfg = None

    async def list_forecast_errors(self, *, tenant_id, sku, limit=52):
        return self.errors


@pytest.mark.asyncio
async def test_safety_get_config_defaults_when_missing():
    svc = SafetyStockService(FakeSafetyRepo())
    out = await svc.get_config("t")
    assert out["is_default"] is True
    assert out["z_score"] == 1.645


@pytest.mark.asyncio
async def test_safety_calculate_with_errors():
    svc = SafetyStockService(FakeSafetyRepo())
    out = await svc.calculate(tenant_id="t", sku="SKU1", lead_time_days=14)
    # MAD = (2+3+4)/3 = 3
    assert out["mad"] == 3.0
    assert out["forecast_errors_used"] == 3
    assert out["z_score"] == 1.645


# ═══════════════════════════════════════════════════════════════════
# binding_analytics
# ═══════════════════════════════════════════════════════════════════

class TestComputeBindingBreakdown:
    def test_empty_items(self):
        bd = compute_binding_breakdown([])
        assert bd["total_skus"] == 0
        assert bd["demand_driven_pct"] == 0
        assert bd["floor_override_pct"] == 0

    def test_mixed_binding(self):
        items = [
            {"binding_factor": "demand", "category": "Tops"},
            {"binding_factor": "demand", "category": "Tops"},
            {"binding_factor": "display_min", "category": "Bottoms"},
            {"binding_factor": "safety_stock", "category": "Bottoms"},
        ]
        bd = compute_binding_breakdown(items)
        assert bd["total_skus"] == 4
        assert bd["counts"]["demand"] == 2
        assert bd["counts"]["display_min"] == 1
        assert bd["counts"]["safety_stock"] == 1
        assert bd["demand_driven_pct"] == 50.0
        assert bd["floor_override_pct"] == 50.0
        # Bottoms 100% override, Tops 0% — Bottoms first
        assert bd["by_category"][0]["category"] == "Bottoms"
        assert bd["by_category"][0]["floor_override_pct"] == 100.0

    def test_legacy_binding_constraint_fallback(self):
        items = [{"binding_constraint": "demand", "category": "X"}]
        bd = compute_binding_breakdown(items)
        assert bd["counts"]["demand"] == 1

    def test_unknown_key_bucketed(self):
        items = [{"binding_factor": "invented", "category": "X"}]
        bd = compute_binding_breakdown(items)
        assert bd["counts"]["unknown"] == 1


class TestAggregateWorstCategories:
    def test_min_threshold_filters_tiny(self):
        plans = [{
            "breakdown": {"by_category": [
                {"category": "Tiny", "total": 2, "counts": {"display_min": 2, "safety_stock": 0}},
                {"category": "Big", "total": 10, "counts": {"display_min": 5, "safety_stock": 0}},
            ]},
        }]
        out = aggregate_worst_categories(plans, min_skus_threshold=5)
        assert [c["category"] for c in out] == ["Big"]

    def test_sorts_desc(self):
        plans = [{
            "breakdown": {"by_category": [
                {"category": "A", "total": 10, "counts": {"display_min": 1, "safety_stock": 0}},
                {"category": "B", "total": 10, "counts": {"display_min": 8, "safety_stock": 0}},
            ]},
        }]
        out = aggregate_worst_categories(plans, min_skus_threshold=5)
        assert out[0]["category"] == "B"


class FakeBindingRepo:
    def __init__(self):
        self._plans_for_iter = []
        self._plans_list = []
        self.breakdown_writes = []

    async def iter_plan_items(self, tenant_id):
        for p in self._plans_for_iter:
            yield p

    async def update_plan_breakdown(self, plan_id, breakdown):
        self.breakdown_writes.append((plan_id, breakdown))

    async def list_recent_plans(self, tenant_id, limit):
        return self._plans_list[:limit]


@pytest.mark.asyncio
async def test_binding_backfill_forbidden_for_non_admin():
    svc = BindingAnalyticsService(FakeBindingRepo())
    with pytest.raises(BAForbidden):
        await svc.backfill(tenant_id="t", role="planner")


@pytest.mark.asyncio
async def test_binding_backfill_admin_happy():
    repo = FakeBindingRepo()
    repo._plans_for_iter = [
        {"_id": "p1", "items": [{"binding_factor": "demand", "category": "X"}]},
        {"_id": "p2", "items": [{"binding_factor": "display_min", "category": "Y"}]},
    ]
    svc = BindingAnalyticsService(repo)
    out = await svc.backfill(tenant_id="t", role="admin")
    assert out["plans_updated"] == 2
    assert len(repo.breakdown_writes) == 2


@pytest.mark.asyncio
async def test_binding_analytics_empty():
    svc = BindingAnalyticsService(FakeBindingRepo())
    out = await svc.get_analytics(tenant_id="t")
    assert out["plan_count"] == 0
    assert out["latest"] is None


# ═══════════════════════════════════════════════════════════════════
# buy_plans
# ═══════════════════════════════════════════════════════════════════

from bson import ObjectId  # noqa: E402


class FakeBuyPlansRepo:
    def __init__(self):
        self._plans: list = []
        self._approvals: list = []
        self._next_id = 1

    async def find(self, tenant_id, plan_id):
        try:
            oid = ObjectId(plan_id)
        except Exception as exc:
            from backend.domains.buy_planning.buy_plans import NotFoundError
            raise NotFoundError("Invalid plan ID") from exc
        for p in self._plans:
            if p["tenant_id"] == tenant_id and p["_id"] == oid:
                return p
        return None

    async def insert(self, doc):
        doc = dict(doc)
        doc["_id"] = ObjectId()
        self._plans.append(doc)
        return str(doc["_id"])

    async def list_metadata(self, tenant_id, status, limit):
        rows = [p for p in self._plans if p["tenant_id"] == tenant_id]
        if status:
            rows = [r for r in rows if r.get("status") == status]
        return rows[:limit]

    async def update(self, plan_id, update):
        oid = ObjectId(plan_id)
        for p in self._plans:
            if p["_id"] == oid:
                # Handle dotted-key updates simplistically
                for k, v in update.items():
                    if "." in k:
                        parts = k.split(".")
                        slot = p
                        for part in parts[:-1]:
                            slot = slot.setdefault(part, {})
                        slot[parts[-1]] = v
                    else:
                        p[k] = v

    async def delete(self, plan_id):
        oid = ObjectId(plan_id)
        self._plans = [p for p in self._plans if p["_id"] != oid]

    async def insert_approval_audit(self, entry):
        self._approvals.append(entry)

    async def list_approval_history(self, tenant_id, plan_id):
        return [a for a in self._approvals if a["tenant_id"] == tenant_id and a["plan_id"] == plan_id]


@pytest.mark.asyncio
async def test_buy_plans_get_invalid_id_404():
    svc = BuyPlansService(FakeBuyPlansRepo())
    with pytest.raises(BPNotFound):
        await svc.get_plan(tenant_id="t", plan_id="not-an-oid")


@pytest.mark.asyncio
async def test_buy_plans_persist_and_list():
    repo = FakeBuyPlansRepo()
    svc = BuyPlansService(repo)
    out = await svc.persist_from_formula(
        tenant_id="t", user_email="u",
        calc_result={"buy_plan": [{"binding_factor": "demand", "category": "X"}],
                     "parameters": {}, "totals": {"total_buy_qty": 10}, "sku_count": 1},
        plan_name=None, cover_days=30, safety_days=7, notes=None,
    )
    assert out["status"] == "draft"
    lst = await svc.list_plans(tenant_id="t")
    assert lst["total"] == 1


@pytest.mark.asyncio
async def test_buy_plans_update_item_cannot_edit_non_draft():
    repo = FakeBuyPlansRepo()
    svc = BuyPlansService(repo)
    out = await svc.persist_from_formula(
        tenant_id="t", user_email="u",
        calc_result={"buy_plan": [{"binding_factor": "demand"}], "parameters": {}, "totals": {}, "sku_count": 1},
        plan_name=None, cover_days=30, safety_days=7, notes=None,
    )
    plan_id = out["plan_id"]
    # Approve it to move out of draft
    await svc.fast_track_approve(tenant_id="t", plan_id=plan_id, user_email="admin")
    # Now try to edit
    with pytest.raises(BPValErr, match="non-draft"):
        await svc.update_item_qty(
            tenant_id="t", plan_id=plan_id, item_index=0, new_qty=99, user_email="u",
        )


@pytest.mark.asyncio
async def test_buy_plans_approval_bad_action():
    repo = FakeBuyPlansRepo()
    svc = BuyPlansService(repo)
    out = await svc.persist_from_formula(
        tenant_id="t", user_email="u",
        calc_result={"buy_plan": [], "parameters": {}, "totals": {}, "sku_count": 0},
        plan_name=None, cover_days=30, safety_days=7, notes=None,
    )
    with pytest.raises(BPValErr, match="Invalid action"):
        await svc.process_approval(
            tenant_id="t", plan_id=out["plan_id"], action="teleport",
            comment=None, user_email="u", role="admin",
        )


@pytest.mark.asyncio
async def test_buy_plans_approval_role_forbidden():
    repo = FakeBuyPlansRepo()
    svc = BuyPlansService(repo)
    out = await svc.persist_from_formula(
        tenant_id="t", user_email="u",
        calc_result={"buy_plan": [], "parameters": {}, "totals": {}, "sku_count": 0},
        plan_name=None, cover_days=30, safety_days=7, notes=None,
    )
    with pytest.raises(BPForbidden):
        await svc.process_approval(
            tenant_id="t", plan_id=out["plan_id"], action="approve_head",
            comment=None, user_email="u", role="viewer",
        )


@pytest.mark.asyncio
async def test_buy_plans_approval_reject_requires_comment():
    repo = FakeBuyPlansRepo()
    svc = BuyPlansService(repo)
    out = await svc.persist_from_formula(
        tenant_id="t", user_email="u",
        calc_result={"buy_plan": [], "parameters": {}, "totals": {}, "sku_count": 0},
        plan_name=None, cover_days=30, safety_days=7, notes=None,
    )
    # Submit first so reject is valid
    await svc.process_approval(
        tenant_id="t", plan_id=out["plan_id"], action="submit",
        comment=None, user_email="u", role="admin",
    )
    with pytest.raises(BPValErr, match="Comment is required"):
        await svc.process_approval(
            tenant_id="t", plan_id=out["plan_id"], action="reject",
            comment=None, user_email="u", role="admin",
        )


@pytest.mark.asyncio
async def test_buy_plans_full_workflow_happy_path():
    repo = FakeBuyPlansRepo()
    svc = BuyPlansService(repo)
    out = await svc.persist_from_formula(
        tenant_id="t", user_email="u",
        calc_result={"buy_plan": [], "parameters": {}, "totals": {}, "sku_count": 0},
        plan_name="Test Plan", cover_days=30, safety_days=7, notes=None,
    )
    pid = out["plan_id"]
    for action in ["submit", "approve_category", "approve_senior", "approve_head", "finance_ack"]:
        result = await svc.process_approval(
            tenant_id="t", plan_id=pid, action=action,
            comment=None, user_email="admin@x.com", role="admin",
        )
        assert result["success"] is True
    # Final state should be ordered
    plan = await svc.get_plan(tenant_id="t", plan_id=pid)
    assert plan["status"] == "ordered"
    # History should have 5 entries
    hist = await svc.approval_history(tenant_id="t", plan_id=pid)
    assert hist["total"] == 5


@pytest.mark.asyncio
async def test_buy_plans_delete_non_draft_rejected():
    repo = FakeBuyPlansRepo()
    svc = BuyPlansService(repo)
    out = await svc.persist_from_formula(
        tenant_id="t", user_email="u",
        calc_result={"buy_plan": [], "parameters": {}, "totals": {}, "sku_count": 0},
        plan_name=None, cover_days=30, safety_days=7, notes=None,
    )
    await svc.fast_track_approve(tenant_id="t", plan_id=out["plan_id"], user_email="admin")
    with pytest.raises(BPValErr, match="non-draft"):
        await svc.delete(tenant_id="t", plan_id=out["plan_id"])


def test_buy_plans_workflow_tables_shape():
    assert set(APPROVAL_ACTIONS.keys()) == set(APPROVAL_ROLES.keys())
    # Every action's roles must be non-empty
    for action, roles in APPROVAL_ROLES.items():
        assert roles, f"No roles configured for {action}"
