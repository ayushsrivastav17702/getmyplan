"""
Store-Wedge domain module.

Third vertical extracted from routes/buy_planning.py.

Scope:
  POST   /store-wedge/classify              auto-classify stores A/B/C by revenue
  GET    /store-wedge                       list current wedge classifications
  POST   /overrides/store-wedge             manual override with audit trail
  DELETE /overrides/store-wedge/{store_code}  revert manual override

Classification rules (Pareto-style revenue bands):
  A = stores contributing cumulative top 80% of revenue
  B = next 15% (cumulative 80-95%)
  C = bottom 5% (cumulative 95-100%)
"""

from datetime import datetime, timezone
from typing import List, Literal, Optional

StoreWedge = Literal["A", "B", "C"]


class NotFoundError(Exception):
    """Raised when a store does not exist."""


class ValidationError(Exception):
    """Raised for bad inputs."""


class NoDataError(Exception):
    """Raised when no store or sales data exists to classify from."""


# ═════════════════════════════════════════════════════════════════
# 1. Pure classifier — no I/O.
# ═════════════════════════════════════════════════════════════════

def classify_wedge_by_cumulative_revenue(cumulative_pct: float) -> StoreWedge:
    """Map cumulative revenue share to wedge band."""
    if cumulative_pct <= 0.80:
        return "A"
    if cumulative_pct <= 0.95:
        return "B"
    return "C"


def classify_stores_by_revenue(stores_revenue: List[dict]) -> List[dict]:
    """
    Pure function: given stores sorted desc by total_revenue, returns the same
    list annotated with wedge_class + revenue_pct.

    Input  : [{"store_code": "S1", "total_revenue": 1000, ...}, ...]
    Output : each dict enriched with wedge_class ('A'|'B'|'C') + revenue_pct.
    Returns [] if total_revenue is 0 across all stores.
    """
    total_rev = sum(s.get("total_revenue", 0) for s in stores_revenue)
    if total_rev == 0:
        return []

    sorted_stores = sorted(stores_revenue, key=lambda s: s.get("total_revenue", 0), reverse=True)
    cumulative = 0.0
    out = []
    for s in sorted_stores:
        cumulative += s.get("total_revenue", 0)
        pct = cumulative / total_rev
        enriched = dict(s)
        enriched["wedge_class"] = classify_wedge_by_cumulative_revenue(pct)
        enriched["revenue_pct"] = round(s.get("total_revenue", 0) / total_rev * 100, 1)
        out.append(enriched)
    return out


def tier_to_wedge(tier: Optional[str]) -> StoreWedge:
    """Fallback when no sales data exists — map existing tier to wedge."""
    if tier == "A":
        return "A"
    if tier == "B":
        return "B"
    return "C"


# ═════════════════════════════════════════════════════════════════
# 2. Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

def _tenant_match(tenant_id: str) -> dict:
    return {"$or": [{"tenant_id": tenant_id}, {"tenant_id": {"$exists": False}}]}


class StoreWedgeRepository:
    def __init__(self, db):
        self._db = db

    async def aggregate_revenue_by_store(self, tenant_id: str) -> List[dict]:
        pipeline = [
            {"$match": _tenant_match(tenant_id)},
            {"$group": {
                "_id": "$store_code",
                "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$revenue", 0]}}},
                "total_qty": {"$sum": {"$toInt": {"$ifNull": ["$quantity", 0]}}},
                "days_active": {"$addToSet": "$day"},
            }},
            {"$project": {
                "store_code": "$_id", "_id": 0,
                "total_revenue": 1, "total_qty": 1,
                "days_active": {"$size": "$days_active"},
            }},
            {"$sort": {"total_revenue": -1}},
        ]
        out: list = []
        async for doc in self._db.daily_sales.aggregate(pipeline):
            out.append(doc)
        return out

    async def list_stores(self, tenant_id: str) -> List[dict]:
        out: list = []
        async for s in self._db.store_master.find(_tenant_match(tenant_id), {"_id": 0}):
            out.append(s)
        return out

    async def get_current_wedges(self, tenant_id: str) -> dict:
        out: dict = {}
        async for s in self._db.store_master.find(
            _tenant_match(tenant_id), {"_id": 0, "store_code": 1, "wedge_class": 1},
        ):
            out[s.get("store_code")] = s.get("wedge_class")
        return out

    async def apply_classification(self, store_code: str, wedge: StoreWedge,
                                    total_revenue: float, now_iso: str):
        await self._db.store_master.update_one(
            {"store_code": store_code},
            {"$set": {
                "wedge_class": wedge,
                "total_revenue": total_revenue,
                "wedge_classified_at": now_iso,
            }},
        )

    async def apply_tier_fallback(self, store_code: str, wedge: StoreWedge):
        await self._db.store_master.update_one(
            {"store_code": store_code},
            {"$set": {"wedge_class": wedge}},
        )

    async def insert_audit_entries(self, entries: List[dict]):
        if entries:
            await self._db.buy_planning_audit_log.insert_many(entries)

    async def find_one_store(self, store_code: str) -> Optional[dict]:
        return await self._db.store_master.find_one(
            {"store_code": store_code}, {"_id": 0, "wedge_class": 1},
        )

    async def apply_manual_override(self, store_code: str, wedge: StoreWedge,
                                     user_email: str, now_iso: str):
        await self._db.store_master.update_one(
            {"store_code": store_code},
            {"$set": {
                "wedge_class": wedge,
                "wedge_manual_override": True,
                "wedge_classified_at": now_iso,
                "wedge_classified_by": user_email,
            }},
        )

    async def record_override(self, *, store_code: str, old: Optional[str], new: StoreWedge,
                              reason: Optional[str], user_email: str, now_iso: str, tenant_id: str):
        await self._db.buy_planning_overrides.insert_one({
            "entity_type": "store", "entity_id": store_code,
            "field": "wedge_class", "old_value": old, "new_value": new,
            "reason": reason, "created_by": user_email,
            "created_at": now_iso, "is_active": True,
        })
        await self._db.buy_planning_audit_log.insert_one({
            "tenant_id": tenant_id, "action": "override", "entity_type": "store",
            "entity_id": store_code, "field": "wedge_class",
            "old_value": old, "new_value": new,
            "reason": reason, "source": "manual",
            "created_by": user_email, "created_at": now_iso,
        })

    async def revert_override(self, store_code: str, user_email: str, now_iso: str):
        await self._db.store_master.update_one(
            {"store_code": store_code},
            {"$set": {"wedge_manual_override": False}, "$unset": {"wedge_classified_by": ""}},
        )
        await self._db.buy_planning_overrides.update_many(
            {"entity_type": "store", "entity_id": store_code, "is_active": True},
            {"$set": {"is_active": False, "reverted_at": now_iso, "reverted_by": user_email}},
        )


# ═════════════════════════════════════════════════════════════════
# 3. Service — orchestration.
# ═════════════════════════════════════════════════════════════════

class StoreWedgeService:
    VALID_WEDGES = ("A", "B", "C")

    def __init__(self, repo: StoreWedgeRepository):
        self._repo = repo

    async def classify(self, *, tenant_id: str, user_email: str) -> dict:
        now_iso = datetime.now(timezone.utc).isoformat()
        stores_revenue = await self._repo.aggregate_revenue_by_store(tenant_id)

        # Fallback: no sales data → use tier from store_master
        if not stores_revenue:
            stores = await self._repo.list_stores(tenant_id)
            if not stores:
                raise NoDataError("No store data found. Upload store master and daily sales first.")
            summary = {"A": 0, "B": 0, "C": 0}
            for s in stores:
                wedge = tier_to_wedge(s.get("tier"))
                summary[wedge] += 1
                await self._repo.apply_tier_fallback(s["store_code"], wedge)
            return {
                "success": True,
                "method": "tier_fallback",
                "message": "Used existing tier data (no sales data). Upload daily sales for revenue-based classification.",
                "summary": summary,
            }

        total_rev = sum(s.get("total_revenue", 0) for s in stores_revenue)
        if total_rev == 0:
            raise NoDataError("All stores have zero revenue.")

        old_wedges = await self._repo.get_current_wedges(tenant_id)
        classified = classify_stores_by_revenue(stores_revenue)
        audit_entries: list = []
        summary = {"A": 0, "B": 0, "C": 0}

        for s in classified:
            wedge = s["wedge_class"]
            summary[wedge] += 1
            await self._repo.apply_classification(
                s["store_code"], wedge, s.get("total_revenue", 0), now_iso,
            )
            old_w = old_wedges.get(s["store_code"])
            if old_w != wedge:
                audit_entries.append({
                    "tenant_id": tenant_id, "action": "classify", "entity_type": "store",
                    "entity_id": s["store_code"], "field": "wedge_class",
                    "old_value": old_w, "new_value": wedge,
                    "reason": f"Revenue-based: {s['revenue_pct']}% of total",
                    "source": "auto", "created_by": user_email,
                    "created_at": now_iso,
                })

        await self._repo.insert_audit_entries(audit_entries)
        return {
            "success": True,
            "method": "revenue_based",
            "total_revenue": round(total_rev, 2),
            "summary": summary,
            "stores": classified,
            "audit_changes": len(audit_entries),
        }

    async def list_classifications(self, tenant_id: str) -> dict:
        stores = await self._repo.list_stores(tenant_id)
        if not stores:
            return {"stores": [], "summary": {"A": 0, "B": 0, "C": 0}, "classified": False}
        summary = {"A": 0, "B": 0, "C": 0}
        classified = False
        for s in stores:
            w = s.get("wedge_class", "")
            if w in summary:
                summary[w] += 1
                classified = True
        return {"stores": stores, "summary": summary, "classified": classified, "total": len(stores)}

    async def override(self, *, store_code: str, wedge: str, reason: Optional[str],
                        user_email: str, tenant_id: str) -> dict:
        if wedge not in self.VALID_WEDGES:
            raise ValidationError(f"wedge_class must be one of {self.VALID_WEDGES}")
        existing = await self._repo.find_one_store(store_code)
        if not existing:
            raise NotFoundError(f"Store '{store_code}' not found")
        old = existing.get("wedge_class")
        now_iso = datetime.now(timezone.utc).isoformat()
        await self._repo.apply_manual_override(store_code, wedge, user_email, now_iso)
        await self._repo.record_override(
            store_code=store_code, old=old, new=wedge, reason=reason,
            user_email=user_email, now_iso=now_iso, tenant_id=tenant_id,
        )
        return {"success": True, "store_code": store_code, "old": old, "new": wedge}

    async def revert_override(self, store_code: str, user_email: str) -> dict:
        now_iso = datetime.now(timezone.utc).isoformat()
        await self._repo.revert_override(store_code, user_email, now_iso)
        return {"success": True, "message": f"Override removed for {store_code}"}
