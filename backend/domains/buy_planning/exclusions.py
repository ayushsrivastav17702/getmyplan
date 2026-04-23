"""
Exclusions domain module.

Endpoints owned:
  POST   /exclusions                   add a store × SKU exclusion
  DELETE /exclusions/{store}/{sku}     remove exclusion
  GET    /exclusions                   list all for tenant

Exclusions mean "this SKU should never appear in buy plans for this store"
— used in the buy-formula calc path to filter SKUs before running the formula.
"""

from datetime import datetime, timezone
from typing import List, Optional


class NotFoundError(Exception):
    """Raised when an exclusion does not exist."""


class ExclusionsRepository:
    def __init__(self, db):
        self._db = db

    async def upsert(self, *, tenant_id: str, store_code: str, sku: str,
                     reason: Optional[str], expires_at: Optional[str],
                     user_email: str, now_iso: str):
        await self._db.buy_planning_exclusions.update_one(
            {"tenant_id": tenant_id, "store_code": store_code, "sku": sku},
            {"$set": {
                "tenant_id": tenant_id, "store_code": store_code, "sku": sku,
                "reason": reason, "expires_at": expires_at,
                "created_by": user_email, "created_at": now_iso,
            }},
            upsert=True,
        )

    async def delete(self, *, tenant_id: str, store_code: str, sku: str) -> int:
        result = await self._db.buy_planning_exclusions.delete_one(
            {"tenant_id": tenant_id, "store_code": store_code, "sku": sku},
        )
        return result.deleted_count

    async def list_all(self, tenant_id: str) -> List[dict]:
        out: list = []
        async for doc in self._db.buy_planning_exclusions.find({"tenant_id": tenant_id}, {"_id": 0}):
            out.append(doc)
        return out


class ExclusionsService:
    def __init__(self, repo: ExclusionsRepository):
        self._repo = repo

    async def add(self, *, tenant_id: str, store_code: str, sku: str,
                  reason: Optional[str], expires_at: Optional[str], user_email: str) -> dict:
        now_iso = datetime.now(timezone.utc).isoformat()
        await self._repo.upsert(
            tenant_id=tenant_id, store_code=store_code, sku=sku,
            reason=reason, expires_at=expires_at,
            user_email=user_email, now_iso=now_iso,
        )
        return {"success": True, "store_code": store_code, "sku": sku}

    async def remove(self, *, tenant_id: str, store_code: str, sku: str) -> dict:
        deleted = await self._repo.delete(tenant_id=tenant_id, store_code=store_code, sku=sku)
        if deleted == 0:
            raise NotFoundError("Exclusion not found")
        return {"success": True, "deleted": True}

    async def list_all(self, tenant_id: str) -> dict:
        items = await self._repo.list_all(tenant_id)
        return {"exclusions": items, "total": len(items)}
