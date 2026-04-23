"""
Orders domain module.

Endpoints owned:
  POST /orders/consolidate     turn an approved buy plan → supplier POs (by category)
  GET  /orders                 list POs (filter by plan_id, status)
  GET  /orders/phased          list phased-shipment POs
  GET  /orders/{po_number}     fetch single PO
  PUT  /orders/{po_number}/status   status lifecycle
  POST /orders/phase           split one PO into phased shipments
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from bson import ObjectId

PO_STATUSES = ["draft", "sent", "confirmed", "shipped", "received", "cancelled"]


class NotFoundError(Exception):
    """Raised when a plan or PO does not exist."""


class ValidationError(Exception):
    """Raised for bad inputs (empty plan, phase %s not summing to 100, etc.)."""


# ═════════════════════════════════════════════════════════════════
# 1. Pure helpers — no I/O.
# ═════════════════════════════════════════════════════════════════

def group_items_by_category(items: List[dict]) -> dict:
    """
    Group buy-plan items by category (proxy for supplier).
    Falls back to sub_category then "General" for missing/blank categories.
    """
    groups: dict = {}
    for item in items:
        cat = item.get("category") or item.get("sub_category") or "General"
        slot = groups.setdefault(cat, {"items": [], "total_units": 0, "total_value": 0})
        qty = item.get("edited_qty") or item.get("buy_qty", 0)
        val = qty * item.get("mrp", 0)
        slot["items"].append({**item, "po_qty": qty, "po_value": round(val, 2)})
        slot["total_units"] += qty
        slot["total_value"] += val
    return groups


def build_po_number(category: str, idx: int, today_str: Optional[str] = None) -> str:
    today_str = today_str or datetime.now(timezone.utc).strftime("%Y%m%d")
    slug = category[:8].upper().replace(" ", "")
    return f"PO-{today_str}-{slug}-{idx + 1:03d}"


def validate_phase_inputs(phase_weeks: List[int], phase_pcts: List[float]):
    if len(phase_weeks) != len(phase_pcts):
        raise ValidationError("phase_weeks and phase_percentages must be same length")
    if abs(sum(phase_pcts) - 100) > 0.5:
        raise ValidationError(f"Percentages must sum to 100 (got {sum(phase_pcts)})")


def build_phase_shipments(items: List[dict], phase_weeks: List[int],
                          phase_pcts: List[float], now: datetime) -> List[dict]:
    """Split a PO's items across phases by percentage."""
    shipments = []
    for idx, (weeks, pct) in enumerate(zip(phase_weeks, phase_pcts)):
        ship_date = (now + timedelta(weeks=weeks)).isoformat()
        phase_items = []
        for item in items:
            qty = round(item.get("po_qty", item.get("buy_qty", 0)) * pct / 100)
            if qty > 0:
                phase_items.append({
                    "sku": item.get("sku", ""),
                    "style": item.get("style", ""),
                    "qty": qty,
                    "value": round(qty * item.get("mrp", 0), 2),
                })
        shipments.append({
            "phase": idx + 1, "weeks_from_now": weeks, "percentage": pct,
            "expected_date": ship_date, "items": phase_items,
            "total_units": sum(i["qty"] for i in phase_items),
            "total_value": round(sum(i["value"] for i in phase_items), 2),
            "status": "ready" if idx == 0 else "pending",
        })
    return shipments


# ═════════════════════════════════════════════════════════════════
# 2. Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

class OrdersRepository:
    def __init__(self, db):
        self._db = db

    async def find_plan(self, tenant_id: str, plan_id: str) -> Optional[dict]:
        try:
            return await self._db.buy_plans.find_one({"_id": ObjectId(plan_id), "tenant_id": tenant_id})
        except Exception:
            return None

    async def insert_po(self, doc: dict):
        await self._db.consolidated_pos.insert_one(doc)

    async def list_pos(self, *, tenant_id: str, plan_id: Optional[str],
                       status: Optional[str]) -> List[dict]:
        query: dict = {"tenant_id": tenant_id}
        if plan_id:
            query["plan_id"] = plan_id
        if status:
            query["status"] = status
        out: list = []
        async for doc in self._db.consolidated_pos.find(query, {"_id": 0}).sort("created_at", -1).limit(100):
            out.append(doc)
        return out

    async def list_phased_pos(self, tenant_id: str) -> List[dict]:
        out: list = []
        async for doc in self._db.phased_pos.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).limit(50):
            out.append(doc)
        return out

    async def find_po(self, tenant_id: str, po_number: str) -> Optional[dict]:
        return await self._db.consolidated_pos.find_one(
            {"tenant_id": tenant_id, "po_number": po_number}, {"_id": 0},
        )

    async def find_po_with_id(self, tenant_id: str, po_number: str) -> Optional[dict]:
        return await self._db.consolidated_pos.find_one(
            {"tenant_id": tenant_id, "po_number": po_number},
        )

    async def update_po_status(self, *, tenant_id: str, po_number: str, status: str,
                                user_email: str, now_iso: str):
        await self._db.consolidated_pos.update_one(
            {"tenant_id": tenant_id, "po_number": po_number},
            {"$set": {
                "status": status,
                f"{status}_at": now_iso,
                f"{status}_by": user_email,
                "updated_at": now_iso,
            }},
        )

    async def insert_phased(self, doc: dict):
        await self._db.phased_pos.insert_one(doc)

    async def mark_po_phased(self, *, tenant_id: str, po_number: str, phased_number: str):
        await self._db.consolidated_pos.update_one(
            {"tenant_id": tenant_id, "po_number": po_number},
            {"$set": {"is_phased": True, "phased_po": phased_number}},
        )


# ═════════════════════════════════════════════════════════════════
# 3. Service — orchestration.
# ═════════════════════════════════════════════════════════════════

class OrdersService:
    def __init__(self, repo: OrdersRepository):
        self._repo = repo

    async def consolidate(self, *, tenant_id: str, plan_id: str, user_email: str) -> dict:
        plan = await self._repo.find_plan(tenant_id, plan_id)
        if not plan:
            raise NotFoundError("Plan not found")
        items = plan.get("items", [])
        if not items:
            raise ValidationError("Plan has no items")

        groups = group_items_by_category(items)
        today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        created_pos = []
        for idx, (cat, data) in enumerate(groups.items()):
            po_number = build_po_number(cat, idx, today_str)
            doc = {
                "tenant_id": tenant_id, "po_number": po_number, "plan_id": plan_id,
                "plan_name": plan.get("plan_name", ""), "supplier_group": cat,
                "items": data["items"], "total_units": data["total_units"],
                "total_value": round(data["total_value"], 2),
                "unique_skus": len(data["items"]), "status": "draft",
                "created_by": user_email,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await self._repo.insert_po(doc)
            created_pos.append({
                "po_number": po_number, "supplier_group": cat,
                "total_units": data["total_units"],
                "total_value": round(data["total_value"], 2),
                "unique_skus": len(data["items"]), "status": "draft",
            })
        return {"success": True, "plan_id": plan_id, "pos_created": len(created_pos), "orders": created_pos}

    async def list_pos(self, *, tenant_id: str, plan_id: Optional[str] = None,
                       status: Optional[str] = None) -> dict:
        orders = await self._repo.list_pos(tenant_id=tenant_id, plan_id=plan_id, status=status)
        return {"orders": orders, "total": len(orders)}

    async def list_phased(self, tenant_id: str) -> dict:
        pos = await self._repo.list_phased_pos(tenant_id)
        return {"phased_pos": pos, "total": len(pos)}

    async def get_po(self, tenant_id: str, po_number: str) -> dict:
        doc = await self._repo.find_po(tenant_id, po_number)
        if not doc:
            raise NotFoundError("PO not found")
        return doc

    async def update_status(self, *, tenant_id: str, po_number: str, status: str,
                             user_email: str) -> dict:
        if status not in PO_STATUSES:
            raise ValidationError(f"Invalid status. Must be one of: {PO_STATUSES}")
        existing = await self._repo.find_po_with_id(tenant_id, po_number)
        if not existing:
            raise NotFoundError("PO not found")
        now_iso = datetime.now(timezone.utc).isoformat()
        await self._repo.update_po_status(
            tenant_id=tenant_id, po_number=po_number, status=status,
            user_email=user_email, now_iso=now_iso,
        )
        return {"success": True, "po_number": po_number, "status": status}

    async def create_phased(self, *, tenant_id: str, po_number: str,
                             phase_weeks: List[int], phase_pcts: List[float],
                             user_email: str) -> dict:
        po = await self._repo.find_po(tenant_id, po_number)
        if not po:
            raise NotFoundError("PO not found")
        validate_phase_inputs(phase_weeks, phase_pcts)

        now = datetime.now(timezone.utc)
        shipments = build_phase_shipments(po.get("items", []), phase_weeks, phase_pcts, now)
        phased_number = f"{po_number}-PHASED"
        phased_doc = {
            "tenant_id": tenant_id, "po_number": phased_number,
            "original_po": po_number, "supplier_group": po.get("supplier_group", ""),
            "shipments": shipments, "total_units": po.get("total_units", 0),
            "total_value": po.get("total_value", 0), "phase_count": len(shipments),
            "created_by": user_email, "created_at": now.isoformat(),
        }
        await self._repo.insert_phased(phased_doc)
        await self._repo.mark_po_phased(
            tenant_id=tenant_id, po_number=po_number, phased_number=phased_number,
        )
        return {"success": True, "po_number": phased_number, "shipments": shipments}
