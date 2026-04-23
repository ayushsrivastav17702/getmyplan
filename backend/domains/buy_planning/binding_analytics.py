"""
Binding-Factor Analytics domain module.

Endpoints owned:
  POST /analytics/backfill-binding-breakdown   recompute binding_breakdown on historical plans
  GET  /analytics/binding-factor               latest + trend + worst categories

Also hosts the **canonical** `compute_binding_breakdown()` — previously this
helper lived inside `routes/buy_planning.py` as `_compute_binding_breakdown`
and was re-used by 5 different call sites (calculate, generate, edit-item,
backfill, read-analytics). Now the ONLY source of truth for
"how do we summarise binding_factor across a plan's items?".
"""

from typing import List, Optional
from bson import ObjectId


class ForbiddenError(Exception):
    """Raised when a non-admin tries to run the backfill."""


# ═════════════════════════════════════════════════════════════════
# 1. Pure summary — no I/O.
# ═════════════════════════════════════════════════════════════════

def compute_binding_breakdown(items: list) -> dict:
    """
    Summarize binding_factor across buy-plan items.

    Returns:
      {
        "counts":    {demand, display_min, safety_stock, unknown},
        "pcts":      {same keys, percentage of total_skus},
        "total_skus": int,
        "demand_driven_pct": float,
        "floor_override_pct": float,   # display_min + safety_stock
        "by_category": [{category, counts, total, floor_override_pct}]
      }
    """
    counts = {"demand": 0, "display_min": 0, "safety_stock": 0, "unknown": 0}
    by_cat: dict = {}
    for it in items:
        bf = it.get("binding_factor") or it.get("binding_constraint") or "unknown"
        key = bf if bf in counts else "unknown"
        counts[key] += 1
        cat = it.get("category") or "Uncategorised"
        slot = by_cat.setdefault(cat, {"demand": 0, "display_min": 0, "safety_stock": 0, "unknown": 0, "total": 0})
        slot[key] += 1
        slot["total"] += 1

    total = sum(counts.values())
    pcts = {k: round((v / total * 100), 1) if total > 0 else 0 for k, v in counts.items()}
    by_category = [
        {
            "category": cat,
            "counts": {k: v for k, v in c.items() if k != "total"},
            "total": c["total"],
            "floor_override_pct": round(((c["display_min"] + c["safety_stock"]) / c["total"] * 100), 1) if c["total"] > 0 else 0,
        }
        for cat, c in by_cat.items()
    ]
    by_category.sort(key=lambda x: x["floor_override_pct"], reverse=True)

    return {
        "counts": counts,
        "pcts": pcts,
        "total_skus": total,
        "demand_driven_pct": pcts["demand"],
        "floor_override_pct": round(pcts["display_min"] + pcts["safety_stock"], 1),
        "by_category": by_category,
    }


def aggregate_worst_categories(plans: List[dict], min_skus_threshold: int = 5,
                                top_n: int = 10) -> list:
    """Roll up category floor_override_pct across multiple plans."""
    cat_totals: dict = {}
    for p in plans:
        for c in p["breakdown"].get("by_category", []):
            slot = cat_totals.setdefault(c["category"], {"skus": 0, "overrides": 0})
            slot["skus"] += c["total"]
            slot["overrides"] += c["counts"].get("display_min", 0) + c["counts"].get("safety_stock", 0)
    return sorted(
        [
            {
                "category": cat,
                "total_skus": v["skus"],
                "override_count": v["overrides"],
                "floor_override_pct": round((v["overrides"] / v["skus"] * 100), 1) if v["skus"] else 0,
            }
            for cat, v in cat_totals.items()
            if v["skus"] >= min_skus_threshold
        ],
        key=lambda x: x["floor_override_pct"],
        reverse=True,
    )[:top_n]


def build_trend_series(plans_newest_first: List[dict]) -> list:
    """Chronological (oldest→newest) plot points for the trend chart."""
    return [
        {
            "plan_id": p["plan_id"],
            "plan_name": p["plan_name"],
            "generated_at": p["generated_at"],
            "total_skus": p["breakdown"]["total_skus"],
            "demand_driven_pct": p["breakdown"]["demand_driven_pct"],
            "floor_override_pct": p["breakdown"]["floor_override_pct"],
            "display_min_pct": p["breakdown"]["pcts"].get("display_min", 0),
            "safety_stock_pct": p["breakdown"]["pcts"].get("safety_stock", 0),
        }
        for p in reversed(plans_newest_first)
    ]


# ═════════════════════════════════════════════════════════════════
# 2. Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

class BindingAnalyticsRepository:
    def __init__(self, db):
        self._db = db

    async def iter_plan_items(self, tenant_id: str):
        async for doc in self._db.buy_plans.find({"tenant_id": tenant_id}, {"items": 1}):
            yield doc

    async def update_plan_breakdown(self, plan_id, breakdown: dict):
        await self._db.buy_plans.update_one(
            {"_id": plan_id},
            {"$set": {"binding_breakdown": breakdown}},
        )

    async def list_recent_plans(self, tenant_id: str, limit: int) -> List[dict]:
        out: list = []
        async for doc in self._db.buy_plans.find(
            {"tenant_id": tenant_id},
            {"_id": 1, "plan_name": 1, "generated_at": 1, "status": 1,
             "binding_breakdown": 1, "items": 1, "sku_count": 1},
        ).sort("generated_at", -1).limit(limit):
            out.append(doc)
        return out


# ═════════════════════════════════════════════════════════════════
# 3. Service — orchestration.
# ═════════════════════════════════════════════════════════════════

class BindingAnalyticsService:
    def __init__(self, repo: BindingAnalyticsRepository):
        self._repo = repo

    async def backfill(self, *, tenant_id: str, role: str) -> dict:
        if role not in ("super_admin", "admin"):
            raise ForbiddenError("Admin only")
        updated = 0
        async for doc in self._repo.iter_plan_items(tenant_id):
            breakdown = compute_binding_breakdown(doc.get("items", []) or [])
            await self._repo.update_plan_breakdown(doc["_id"], breakdown)
            updated += 1
        return {"success": True, "plans_updated": updated}

    async def get_analytics(self, *, tenant_id: str, limit: int = 10) -> dict:
        limit = max(1, min(limit, 50))
        raw_plans = await self._repo.list_recent_plans(tenant_id, limit)

        plans = []
        for doc in raw_plans:
            bd = doc.get("binding_breakdown")
            if not bd:
                bd = compute_binding_breakdown(doc.get("items", []) or [])
            plans.append({
                "plan_id": str(doc["_id"]),
                "plan_name": doc.get("plan_name"),
                "generated_at": doc.get("generated_at"),
                "status": doc.get("status"),
                "breakdown": bd,
                "sku_count": doc.get("sku_count", bd.get("total_skus", 0)),
            })

        if not plans:
            return {
                "plan_count": 0, "latest": None, "trend": [],
                "worst_categories": [], "total_skus_analyzed": 0,
            }

        latest = plans[0]
        return {
            "plan_count": len(plans),
            "latest": {
                "plan_id": latest["plan_id"],
                "plan_name": latest["plan_name"],
                "generated_at": latest["generated_at"],
                "status": latest["status"],
                "breakdown": latest["breakdown"],
            },
            "trend": build_trend_series(plans),
            "worst_categories": aggregate_worst_categories(plans),
            "total_skus_analyzed": sum(p["breakdown"]["total_skus"] for p in plans),
        }
