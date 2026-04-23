"""
Promotions domain module.

Endpoints owned:
  POST   /promotions              create promo
  GET    /promotions              list (filter by status)
  PUT    /promotions/{promo_id}   update
  DELETE /promotions/{promo_id}   delete
  GET    /promotions/active-lift  currently-active lift factors (buy-formula input)
"""

from datetime import datetime, timezone
from typing import List, Optional


class NotFoundError(Exception):
    """Raised when a promotion does not exist."""


class ValidationError(Exception):
    """Raised on invalid promo input (bad lift factor, etc.)."""


# ═════════════════════════════════════════════════════════════════
# Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

class PromotionsRepository:
    def __init__(self, db):
        self._db = db

    async def insert(self, doc: dict):
        await self._db.promotions.insert_one(doc)

    async def list_all(self, tenant_id: str, status: Optional[str]) -> List[dict]:
        query: dict = {"tenant_id": tenant_id}
        if status:
            query["status"] = status
        out: list = []
        async for doc in self._db.promotions.find(query, {"_id": 0}).sort("start_date", -1).limit(100):
            out.append(doc)
        return out

    async def update(self, *, tenant_id: str, promo_id: str, payload: dict,
                     user_email: str, now_iso: str) -> int:
        result = await self._db.promotions.update_one(
            {"tenant_id": tenant_id, "promo_id": promo_id},
            {"$set": {**payload, "updated_by": user_email, "updated_at": now_iso}},
        )
        return result.matched_count

    async def delete(self, *, tenant_id: str, promo_id: str) -> int:
        result = await self._db.promotions.delete_one({"tenant_id": tenant_id, "promo_id": promo_id})
        return result.deleted_count

    async def list_active_on(self, tenant_id: str, today_iso: str) -> List[dict]:
        out: list = []
        async for doc in self._db.promotions.find({
            "tenant_id": tenant_id, "status": "active",
            "start_date": {"$lte": today_iso}, "end_date": {"$gte": today_iso},
        }, {
            "_id": 0, "promo_id": 1, "name": 1, "affected_categories": 1,
            "affected_skus": 1, "lift_factor": 1,
        }):
            out.append(doc)
        return out


# ═════════════════════════════════════════════════════════════════
# Service — orchestration + validation.
# ═════════════════════════════════════════════════════════════════

def _validate_lift(lift_factor: float):
    if lift_factor < 0.5 or lift_factor > 5:
        raise ValidationError("lift_factor must be between 0.5 and 5")


class PromotionsService:
    def __init__(self, repo: PromotionsRepository):
        self._repo = repo

    async def create(self, *, tenant_id: str, payload: dict, user_email: str) -> dict:
        _validate_lift(payload.get("lift_factor", 1.0))
        now = datetime.now(timezone.utc)
        promo_id = f"PROMO-{now.strftime('%Y%m%d%H%M%S')}"
        doc = {
            "tenant_id": tenant_id, "promo_id": promo_id, **payload,
            "status": "active", "created_by": user_email, "created_at": now.isoformat(),
        }
        await self._repo.insert(doc)
        return {"success": True, "promo_id": promo_id}

    async def list_all(self, tenant_id: str, status: Optional[str] = None) -> dict:
        promos = await self._repo.list_all(tenant_id, status)
        return {"promotions": promos, "total": len(promos)}

    async def update(self, *, tenant_id: str, promo_id: str, payload: dict, user_email: str) -> dict:
        _validate_lift(payload.get("lift_factor", 1.0))
        now_iso = datetime.now(timezone.utc).isoformat()
        matched = await self._repo.update(
            tenant_id=tenant_id, promo_id=promo_id, payload=payload,
            user_email=user_email, now_iso=now_iso,
        )
        if matched == 0:
            raise NotFoundError("Promotion not found")
        return {"success": True, "promo_id": promo_id}

    async def delete(self, *, tenant_id: str, promo_id: str) -> dict:
        deleted = await self._repo.delete(tenant_id=tenant_id, promo_id=promo_id)
        if deleted == 0:
            raise NotFoundError("Promotion not found")
        return {"success": True, "deleted": True}

    async def get_active_lifts(self, tenant_id: str) -> dict:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        promos = await self._repo.list_active_on(tenant_id, today)
        return {"active_promotions": promos, "total": len(promos)}
