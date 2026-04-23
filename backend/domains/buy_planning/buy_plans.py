"""
Buy-Plans domain module.

Endpoints owned:
  POST   /buy-plans/generate                 generate + save a plan via buy-formula
  GET    /buy-plans                          list saved plans (metadata only)
  GET    /buy-plans/{plan_id}                full plan detail incl. items + approvals
  PUT    /buy-plans/{plan_id}/items          edit one item's qty in a draft plan
  POST   /buy-plans/{plan_id}/approval       multi-level workflow action
  GET    /buy-plans/{plan_id}/approval-history  audit trail per plan
  POST   /buy-plans/{plan_id}/approve        legacy fast-track (submit→ordered)
  DELETE /buy-plans/{plan_id}                delete a draft plan

Uses `compute_binding_breakdown` from the binding_analytics domain module so
"binding_factor" roll-ups have ONE definition across the codebase.
"""

from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId

from .binding_analytics import compute_binding_breakdown


# ═════════════════════════════════════════════════════════════════
# Workflow tables — pure data.
# ═════════════════════════════════════════════════════════════════

PLAN_STATUS_CHAIN = [
    "draft", "submitted", "category_approved", "senior_approved",
    "head_approved", "ordered",
]

APPROVAL_ACTIONS = {
    "submit":            {"from": ["draft"],              "to": "submitted"},
    "approve_category":  {"from": ["submitted"],          "to": "category_approved"},
    "approve_senior":    {"from": ["category_approved"],  "to": "senior_approved"},
    "approve_head":      {"from": ["senior_approved"],    "to": "head_approved"},
    "finance_ack":       {"from": ["head_approved"],      "to": "ordered"},
    "reject":            {"from": ["submitted", "category_approved", "senior_approved", "head_approved"], "to": "rejected"},
    "request_changes":   {"from": ["submitted", "category_approved", "senior_approved"],                   "to": "draft"},
}

APPROVAL_ROLES = {
    "submit":            ["super_admin", "admin", "junior_planner", "category_planner", "planner"],
    "approve_category":  ["super_admin", "admin", "category_planner"],
    "approve_senior":    ["super_admin", "admin", "senior_planner"],
    "approve_head":      ["super_admin", "admin", "merchandise_head"],
    "finance_ack":       ["super_admin", "admin", "finance"],
    "reject":            ["super_admin", "admin", "category_planner", "senior_planner", "merchandise_head"],
    "request_changes":   ["super_admin", "admin", "category_planner", "senior_planner"],
}

_STAGE_TS_FIELDS = {
    "submit":           ("submitted_at", "submitted_by"),
    "approve_category": ("category_approved_at", "category_approved_by"),
    "approve_senior":   ("senior_approved_at", "senior_approved_by"),
    "approve_head":     ("head_approved_at", "head_approved_by"),
    "finance_ack":      ("ordered_at", "ordered_by"),
}


class NotFoundError(Exception):
    """Plan does not exist / bad ObjectId / wrong tenant."""


class ValidationError(Exception):
    """Bad action / wrong status / missing required comment."""


class ForbiddenError(Exception):
    """Role not allowed to perform this action."""


# ═════════════════════════════════════════════════════════════════
# Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

def _to_object_id(plan_id: str) -> ObjectId:
    try:
        return ObjectId(plan_id)
    except Exception as exc:
        raise NotFoundError("Invalid plan ID") from exc


class BuyPlansRepository:
    def __init__(self, db):
        self._db = db

    async def find(self, tenant_id: str, plan_id: str):
        return await self._db.buy_plans.find_one(
            {"_id": _to_object_id(plan_id), "tenant_id": tenant_id},
        )

    async def insert(self, doc: dict) -> str:
        result = await self._db.buy_plans.insert_one(doc)
        return str(result.inserted_id)

    async def list_metadata(self, tenant_id: str, status: Optional[str], limit: int):
        query: dict = {"tenant_id": tenant_id}
        if status:
            query["status"] = status
        out: list = []
        async for doc in self._db.buy_plans.find(query, {"items": 0}).sort("generated_at", -1).limit(limit):
            out.append(doc)
        return out

    async def update(self, plan_id: str, update: dict):
        await self._db.buy_plans.update_one({"_id": _to_object_id(plan_id)}, {"$set": update})

    async def delete(self, plan_id: str):
        await self._db.buy_plans.delete_one({"_id": _to_object_id(plan_id)})

    async def insert_approval_audit(self, entry: dict):
        await self._db.buy_planning_approval_audit.insert_one(entry)

    async def list_approval_history(self, tenant_id: str, plan_id: str):
        out: list = []
        async for doc in self._db.buy_planning_approval_audit.find(
            {"tenant_id": tenant_id, "plan_id": plan_id}, {"_id": 0},
        ).sort("performed_at", 1):
            out.append(doc)
        return out


# ═════════════════════════════════════════════════════════════════
# Service — orchestration.
# ═════════════════════════════════════════════════════════════════

def _plan_metadata(doc: dict) -> dict:
    return {
        "plan_id": str(doc["_id"]),
        "plan_name": doc.get("plan_name", ""),
        "status": doc.get("status", "draft"),
        "generated_at": doc.get("generated_at", ""),
        "generated_by": doc.get("generated_by", ""),
        "sku_count": doc.get("sku_count", 0),
        "totals": doc.get("totals", {}),
        "cover_days": doc.get("cover_days", 30),
        "notes": doc.get("notes"),
        "approved_at": doc.get("approved_at"),
        "approved_by": doc.get("approved_by"),
    }


def _plan_full(doc: dict) -> dict:
    return {
        **_plan_metadata(doc),
        "parameters": doc.get("parameters", {}),
        "items": doc.get("items", []),
        "approvals": doc.get("approvals", {}),
        "submitted_at": doc.get("submitted_at"),
        "submitted_by": doc.get("submitted_by"),
        "category_approved_at": doc.get("category_approved_at"),
        "category_approved_by": doc.get("category_approved_by"),
        "senior_approved_at": doc.get("senior_approved_at"),
        "senior_approved_by": doc.get("senior_approved_by"),
        "head_approved_at": doc.get("head_approved_at"),
        "head_approved_by": doc.get("head_approved_by"),
        "ordered_at": doc.get("ordered_at"),
        "ordered_by": doc.get("ordered_by"),
    }


class BuyPlansService:
    def __init__(self, repo: BuyPlansRepository):
        self._repo = repo

    async def persist_from_formula(self, *, tenant_id: str, user_email: str,
                                    calc_result: dict, plan_name: Optional[str],
                                    cover_days: int, safety_days: int,
                                    notes: Optional[str]) -> dict:
        name = plan_name or f"Buy Plan {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
        items = calc_result.get("buy_plan", [])
        breakdown = compute_binding_breakdown(items)
        doc = {
            "tenant_id": tenant_id, "plan_name": name,
            "cover_days": cover_days, "safety_days": safety_days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": user_email, "status": "draft", "items": items,
            "parameters": calc_result.get("parameters", {}),
            "totals": calc_result.get("totals", {}),
            "sku_count": calc_result.get("sku_count", 0),
            "binding_breakdown": breakdown, "notes": notes,
        }
        plan_id = await self._repo.insert(doc)
        return {
            "success": True, "plan_id": plan_id, "plan_name": name,
            "status": "draft", "sku_count": calc_result.get("sku_count", 0),
            "totals": calc_result.get("totals", {}),
        }

    async def list_plans(self, *, tenant_id: str, status: Optional[str] = None, limit: int = 20) -> dict:
        docs = await self._repo.list_metadata(tenant_id, status, limit)
        return {"plans": [_plan_metadata(d) for d in docs], "total": len(docs)}

    async def get_plan(self, *, tenant_id: str, plan_id: str) -> dict:
        doc = await self._repo.find(tenant_id, plan_id)
        if not doc:
            raise NotFoundError("Plan not found")
        return _plan_full(doc)

    async def update_item_qty(self, *, tenant_id: str, plan_id: str,
                               item_index: int, new_qty: int, user_email: str) -> dict:
        doc = await self._repo.find(tenant_id, plan_id)
        if not doc:
            raise NotFoundError("Plan not found")
        if doc.get("status") != "draft":
            raise ValidationError("Cannot edit non-draft plan")
        items = doc.get("items", [])
        if item_index < 0 or item_index >= len(items):
            raise ValidationError("Item index out of range")

        items[item_index]["edited_qty"] = new_qty
        items[item_index]["edited_by"] = user_email
        items[item_index]["edited_at"] = datetime.now(timezone.utc).isoformat()
        total_qty = sum(i.get("edited_qty", i.get("buy_qty", 0)) for i in items)
        total_val = sum(i.get("edited_qty", i.get("buy_qty", 0)) * i.get("mrp", 0) for i in items)
        breakdown = compute_binding_breakdown(items)

        await self._repo.update(plan_id, {
            "items": items,
            "totals.total_buy_qty": total_qty,
            "totals.total_buy_value": round(total_val, 2),
            "binding_breakdown": breakdown,
        })
        return {
            "success": True, "item_index": item_index,
            "new_qty": new_qty, "total_buy_qty": total_qty,
        }

    async def process_approval(self, *, tenant_id: str, plan_id: str,
                                action: str, comment: Optional[str],
                                user_email: str, role: str) -> dict:
        if action not in APPROVAL_ACTIONS:
            raise ValidationError(
                f"Invalid action: {action}. Valid: {', '.join(APPROVAL_ACTIONS.keys())}"
            )
        if role not in APPROVAL_ROLES.get(action, []):
            raise ForbiddenError(f"Role '{role}' cannot perform '{action}'")
        if action in ("reject", "request_changes") and not comment:
            raise ValidationError("Comment is required for reject/request_changes")

        doc = await self._repo.find(tenant_id, plan_id)
        if not doc:
            raise NotFoundError("Plan not found")
        current = doc.get("status", "draft")
        rule = APPROVAL_ACTIONS[action]
        if current not in rule["from"]:
            raise ValidationError(
                f"Cannot '{action}' from status '{current}'. Requires: {rule['from']}"
            )

        new_status = rule["to"]
        now_iso = datetime.now(timezone.utc).isoformat()
        update = {
            "status": new_status,
            f"approvals.{action}": {"by": user_email, "at": now_iso, "comment": comment},
        }
        if action in _STAGE_TS_FIELDS:
            ts_field, by_field = _STAGE_TS_FIELDS[action]
            update[ts_field] = now_iso
            update[by_field] = user_email

        await self._repo.update(plan_id, update)
        await self._repo.insert_approval_audit({
            "tenant_id": tenant_id, "plan_id": plan_id,
            "action": action, "from_status": current, "to_status": new_status,
            "comment": comment, "performed_by": user_email, "role": role,
            "performed_at": now_iso,
        })
        return {
            "success": True, "plan_id": plan_id, "action": action,
            "old_status": current, "new_status": new_status,
        }

    async def approval_history(self, *, tenant_id: str, plan_id: str) -> dict:
        entries = await self._repo.list_approval_history(tenant_id, plan_id)
        return {"history": entries, "total": len(entries)}

    async def fast_track_approve(self, *, tenant_id: str, plan_id: str,
                                   user_email: str) -> dict:
        """Legacy single-step approval — auto-fills every stage timestamp."""
        doc = await self._repo.find(tenant_id, plan_id)
        if not doc:
            raise NotFoundError("Plan not found")
        status = doc.get("status", "draft")
        if status in ("ordered", "rejected"):
            raise ValidationError(f"Plan is already {status}")

        now_iso = datetime.now(timezone.utc).isoformat()
        await self._repo.update(plan_id, {
            "status": "ordered",
            "approved_at": now_iso, "approved_by": user_email,
            "submitted_at": now_iso, "submitted_by": user_email,
            "category_approved_at": now_iso, "category_approved_by": user_email,
            "senior_approved_at": now_iso, "senior_approved_by": user_email,
            "head_approved_at": now_iso, "head_approved_by": user_email,
            "ordered_at": now_iso, "ordered_by": user_email,
        })
        return {
            "success": True, "plan_id": plan_id,
            "status": "ordered", "approved_at": now_iso,
        }

    async def delete(self, *, tenant_id: str, plan_id: str) -> dict:
        doc = await self._repo.find(tenant_id, plan_id)
        if not doc:
            raise NotFoundError("Plan not found")
        if doc.get("status") != "draft":
            raise ValidationError("Cannot delete non-draft plan")
        await self._repo.delete(plan_id)
        return {"success": True, "deleted": True}
