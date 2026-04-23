"""
Display-Minimums domain module.

First vertical extracted from routes/buy_planning.py (strangler-fig).

Responsibility: CRUD for per-(category × store_wedge) display minimum configs.
These integer floors are the single knob that — per the binding-factor dashboard
— can cause silent over-buying if misconfigured. Keeping the CRUD clean matters.
"""

from datetime import datetime, timezone
from typing import List


# ── Domain errors ──────────────────────────────────────────────────────────
class NotFoundError(Exception):
    """Raised when a requested config row does not exist."""


# ── Repository (pure Mongo) ────────────────────────────────────────────────
class DisplayMinimumsRepository:
    """
    Mongo access for `display_minimums_config` collection.

    NOTE on tenancy: the current sample-data footprint shares this config
    across all tenants (by design — it's considered a platform default).
    When per-tenant overrides land, add `tenant_id` to the filters here
    and in the compound index — the service layer stays untouched.
    """

    COLLECTION = "display_minimums_config"

    def __init__(self, db):
        self._db = db

    async def list_all(self) -> List[dict]:
        docs: list = []
        async for doc in self._db[self.COLLECTION].find({}, {"_id": 0}):
            docs.append(doc)
        return docs

    async def upsert(
        self,
        *,
        category: str,
        store_wedge: str,
        min_facings: int,
        display_units_per_facing: int,
    ) -> int:
        total = min_facings * display_units_per_facing
        await self._db[self.COLLECTION].update_one(
            {"category": category, "store_wedge": store_wedge},
            {"$set": {
                "category": category,
                "store_wedge": store_wedge,
                "min_facings": min_facings,
                "display_units_per_facing": display_units_per_facing,
                "total_display_min_units": total,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        )
        return total

    async def delete(self, *, category: str, store_wedge: str) -> bool:
        result = await self._db[self.COLLECTION].delete_one(
            {"category": category, "store_wedge": store_wedge}
        )
        return result.deleted_count > 0


# ── Service (business logic) ───────────────────────────────────────────────
class DisplayMinimumsService:
    """Thin service — currently just orchestrates. Add validation/audit here."""

    def __init__(self, repo: DisplayMinimumsRepository):
        self._repo = repo

    async def list_configs(self) -> dict:
        configs = await self._repo.list_all()
        # Backfill derived field for docs that pre-date it
        for c in configs:
            if "total_display_min_units" not in c:
                c["total_display_min_units"] = (
                    c.get("min_facings", 2) * c.get("display_units_per_facing", 2)
                )
        return {"configs": configs, "total": len(configs)}

    async def set_config(
        self,
        *,
        category: str,
        store_wedge: str,
        min_facings: int,
        display_units_per_facing: int,
    ) -> dict:
        if min_facings < 0 or display_units_per_facing < 0:
            raise ValueError("min_facings and display_units_per_facing must be >= 0")
        if store_wedge not in ("A", "B", "C"):
            raise ValueError(f"invalid store_wedge: {store_wedge!r}")

        total = await self._repo.upsert(
            category=category,
            store_wedge=store_wedge,
            min_facings=min_facings,
            display_units_per_facing=display_units_per_facing,
        )
        return {
            "success": True,
            "category": category,
            "store_wedge": store_wedge,
            "total_display_min_units": total,
        }

    async def delete_config(self, *, category: str, store_wedge: str) -> dict:
        if not await self._repo.delete(category=category, store_wedge=store_wedge):
            raise NotFoundError(f"Config not found: {category}/{store_wedge}")
        return {"success": True}
