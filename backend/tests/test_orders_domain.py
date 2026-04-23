"""Unit tests for the orders domain (pure helpers + service)."""

import pytest
from datetime import datetime, timezone
from backend.domains.buy_planning.orders import (
    group_items_by_category,
    build_po_number,
    validate_phase_inputs,
    build_phase_shipments,
    OrdersService,
    NotFoundError,
    ValidationError,
    PO_STATUSES,
)


# ═══════════════════════════════════════════════════════════════════
# 1. Pure helpers.
# ═══════════════════════════════════════════════════════════════════

class TestGroupItemsByCategory:
    def test_groups_by_category(self):
        items = [
            {"sku": "A", "category": "Tops", "buy_qty": 10, "mrp": 100},
            {"sku": "B", "category": "Tops", "buy_qty": 5,  "mrp": 200},
            {"sku": "C", "category": "Bottoms", "buy_qty": 3, "mrp": 300},
        ]
        groups = group_items_by_category(items)
        assert set(groups.keys()) == {"Tops", "Bottoms"}
        assert groups["Tops"]["total_units"] == 15
        assert groups["Tops"]["total_value"] == 10 * 100 + 5 * 200
        assert groups["Bottoms"]["total_units"] == 3

    def test_prefers_edited_qty(self):
        items = [{"sku": "A", "category": "Tops", "buy_qty": 10, "edited_qty": 7, "mrp": 100}]
        groups = group_items_by_category(items)
        assert groups["Tops"]["total_units"] == 7

    def test_fallback_to_sub_category_then_general(self):
        items = [
            {"sku": "A", "sub_category": "T-shirt", "buy_qty": 1, "mrp": 100},
            {"sku": "B", "buy_qty": 1, "mrp": 100},  # nothing → General
        ]
        groups = group_items_by_category(items)
        assert "T-shirt" in groups
        assert "General" in groups


class TestBuildPONumber:
    def test_format(self):
        po = build_po_number("Tops", 0, "20260219")
        assert po == "PO-20260219-TOPS-001"

    def test_truncates_long_category(self):
        po = build_po_number("Luxury Accessories", 4, "20260219")
        # slice[:8] = "Luxury A" → .upper().replace(' ','') → "LUXURYA"
        assert po == "PO-20260219-LUXURYA-005"


class TestValidatePhaseInputs:
    def test_valid_sums_to_100(self):
        validate_phase_inputs([0, 2, 4], [50, 30, 20])  # should not raise

    def test_length_mismatch(self):
        with pytest.raises(ValidationError, match="same length"):
            validate_phase_inputs([0, 2], [50, 30, 20])

    def test_does_not_sum_to_100(self):
        with pytest.raises(ValidationError, match="sum to 100"):
            validate_phase_inputs([0, 2, 4], [50, 30, 10])

    def test_small_rounding_tolerated(self):
        # 0.5% tolerance
        validate_phase_inputs([0, 2, 4], [50.25, 30, 19.75])


class TestBuildPhaseShipments:
    def test_splits_qty_by_pct(self):
        items = [{"sku": "A", "style": "S", "po_qty": 100, "mrp": 50}]
        now = datetime(2026, 2, 19, tzinfo=timezone.utc)
        shipments = build_phase_shipments(items, [0, 2, 4], [50, 30, 20], now)
        assert len(shipments) == 3
        assert shipments[0]["total_units"] == 50
        assert shipments[1]["total_units"] == 30
        assert shipments[2]["total_units"] == 20
        assert shipments[0]["status"] == "ready"
        assert shipments[1]["status"] == "pending"

    def test_zero_qty_items_skipped(self):
        items = [{"sku": "A", "po_qty": 10, "mrp": 50}, {"sku": "B", "po_qty": 0, "mrp": 50}]
        now = datetime(2026, 2, 19, tzinfo=timezone.utc)
        shipments = build_phase_shipments(items, [0], [100], now)
        # Only SKU A should be in the shipment (B rounds to 0)
        skus = [i["sku"] for i in shipments[0]["items"]]
        assert skus == ["A"]


# ═══════════════════════════════════════════════════════════════════
# 2. Service layer.
# ═══════════════════════════════════════════════════════════════════

class FakeOrdersRepo:
    def __init__(self):
        self.plans: dict = {}
        self.pos: list = []
        self.phased: list = []
        self.po_status_updates: list = []
        self.marked_phased: list = []

    async def find_plan(self, tenant_id, plan_id):
        return self.plans.get((tenant_id, plan_id))

    async def insert_po(self, doc):
        self.pos.append(doc)

    async def list_pos(self, *, tenant_id, plan_id, status):
        rows = [p for p in self.pos if p["tenant_id"] == tenant_id]
        if plan_id:
            rows = [r for r in rows if r.get("plan_id") == plan_id]
        if status:
            rows = [r for r in rows if r.get("status") == status]
        return rows

    async def list_phased_pos(self, tenant_id):
        return [p for p in self.phased if p["tenant_id"] == tenant_id]

    async def find_po(self, tenant_id, po_number):
        for p in self.pos:
            if p["tenant_id"] == tenant_id and p["po_number"] == po_number:
                return p
        return None

    async def find_po_with_id(self, tenant_id, po_number):
        return await self.find_po(tenant_id, po_number)

    async def update_po_status(self, *, tenant_id, po_number, status, user_email, now_iso):
        self.po_status_updates.append((po_number, status))

    async def insert_phased(self, doc):
        self.phased.append(doc)

    async def mark_po_phased(self, *, tenant_id, po_number, phased_number):
        self.marked_phased.append((po_number, phased_number))


@pytest.mark.asyncio
async def test_consolidate_plan_not_found():
    svc = OrdersService(FakeOrdersRepo())
    with pytest.raises(NotFoundError):
        await svc.consolidate(tenant_id="t1", plan_id="ghost", user_email="u@x.com")


@pytest.mark.asyncio
async def test_consolidate_empty_plan():
    repo = FakeOrdersRepo()
    repo.plans[("t1", "p1")] = {"plan_name": "empty", "items": []}
    svc = OrdersService(repo)
    with pytest.raises(ValidationError):
        await svc.consolidate(tenant_id="t1", plan_id="p1", user_email="u@x.com")


@pytest.mark.asyncio
async def test_consolidate_happy_path():
    repo = FakeOrdersRepo()
    repo.plans[("t1", "p1")] = {
        "plan_name": "Feb Buy",
        "items": [
            {"sku": "A", "category": "Tops", "buy_qty": 10, "mrp": 100},
            {"sku": "B", "category": "Bottoms", "buy_qty": 5, "mrp": 200},
        ],
    }
    svc = OrdersService(repo)
    out = await svc.consolidate(tenant_id="t1", plan_id="p1", user_email="u@x.com")
    assert out["success"] is True
    assert out["pos_created"] == 2
    assert len(repo.pos) == 2


@pytest.mark.asyncio
async def test_update_status_rejects_invalid():
    svc = OrdersService(FakeOrdersRepo())
    with pytest.raises(ValidationError):
        await svc.update_status(
            tenant_id="t1", po_number="PO1", status="invented_status",
            user_email="u@x.com",
        )


@pytest.mark.asyncio
async def test_update_status_not_found():
    svc = OrdersService(FakeOrdersRepo())
    with pytest.raises(NotFoundError):
        await svc.update_status(
            tenant_id="t1", po_number="GHOST", status="sent", user_email="u@x.com",
        )


@pytest.mark.asyncio
async def test_update_status_happy_path():
    repo = FakeOrdersRepo()
    repo.pos.append({"tenant_id": "t1", "po_number": "PO1", "status": "draft"})
    svc = OrdersService(repo)
    out = await svc.update_status(
        tenant_id="t1", po_number="PO1", status="sent", user_email="u@x.com",
    )
    assert out["status"] == "sent"
    assert repo.po_status_updates == [("PO1", "sent")]


@pytest.mark.asyncio
async def test_create_phased_bad_sums():
    repo = FakeOrdersRepo()
    repo.pos.append({
        "tenant_id": "t1", "po_number": "PO1", "status": "draft",
        "items": [{"sku": "A", "po_qty": 100, "mrp": 50}],
        "total_units": 100, "total_value": 5000, "supplier_group": "Tops",
    })
    svc = OrdersService(repo)
    with pytest.raises(ValidationError):
        await svc.create_phased(
            tenant_id="t1", po_number="PO1",
            phase_weeks=[0, 2], phase_pcts=[50, 30],  # sums to 80
            user_email="u@x.com",
        )


@pytest.mark.asyncio
async def test_create_phased_happy_path():
    repo = FakeOrdersRepo()
    repo.pos.append({
        "tenant_id": "t1", "po_number": "PO1", "status": "draft",
        "items": [{"sku": "A", "po_qty": 100, "mrp": 50}],
        "total_units": 100, "total_value": 5000, "supplier_group": "Tops",
    })
    svc = OrdersService(repo)
    out = await svc.create_phased(
        tenant_id="t1", po_number="PO1",
        phase_weeks=[0, 2, 4], phase_pcts=[50, 30, 20],
        user_email="u@x.com",
    )
    assert out["po_number"] == "PO1-PHASED"
    assert len(out["shipments"]) == 3
    assert repo.marked_phased == [("PO1", "PO1-PHASED")]


def test_po_statuses_constant_shape():
    # Sanity: all expected statuses still present
    assert {"draft", "sent", "confirmed", "shipped", "received", "cancelled"} <= set(PO_STATUSES)
