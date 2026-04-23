"""
Store Attributes domain module.

Endpoints owned:
  PUT /stores/{store_code}/attributes   update store_format / city_tier / region / area_sqft

Every field change produces an audit-log entry.
"""

from datetime import datetime, timezone
from typing import Optional


VALID_FORMATS = {"hypermarket", "supermarket", "convenience"}
VALID_TIERS = {"tier1", "tier2", "tier3"}
VALID_REGIONS = {"North", "South", "East", "West", "Central"}


class NotFoundError(Exception):
    """Raised when the store does not exist."""


class ValidationError(Exception):
    """Raised on invalid enum values or empty update payload."""


# ═════════════════════════════════════════════════════════════════
# Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

class StoreAttributesRepository:
    def __init__(self, db):
        self._db = db

    async def find_store(self, store_code: str):
        return await self._db.store_master.find_one(
            {"store_code": store_code}, {"_id": 0, "store_code": 1},
        )

    async def apply_updates(self, store_code: str, updates: dict):
        await self._db.store_master.update_one({"store_code": store_code}, {"$set": updates})

    async def append_audit(self, entry: dict):
        await self._db.buy_planning_audit_log.insert_one(entry)


# ═════════════════════════════════════════════════════════════════
# Service — validation + orchestration.
# ═════════════════════════════════════════════════════════════════

def validate_and_build_updates(*, store_format: Optional[str], city_tier: Optional[str],
                                region: Optional[str], area_sqft: Optional[int]) -> dict:
    """Pure validator — builds the update dict or raises ValidationError."""
    updates: dict = {}
    if store_format is not None:
        if store_format not in VALID_FORMATS:
            raise ValidationError(f"store_format must be one of: {', '.join(sorted(VALID_FORMATS))}")
        updates["store_format"] = store_format
    if city_tier is not None:
        if city_tier not in VALID_TIERS:
            raise ValidationError(f"city_tier must be one of: {', '.join(sorted(VALID_TIERS))}")
        updates["city_tier"] = city_tier
    if region is not None:
        if region not in VALID_REGIONS:
            raise ValidationError(f"region must be one of: {', '.join(sorted(VALID_REGIONS))}")
        updates["region"] = region
    if area_sqft is not None:
        updates["area_sqft"] = area_sqft
    if not updates:
        raise ValidationError("No attributes to update")
    return updates


class StoreAttributesService:
    def __init__(self, repo: StoreAttributesRepository):
        self._repo = repo

    async def update(self, *, store_code: str, store_format=None, city_tier=None,
                      region=None, area_sqft=None,
                      user_email: str, tenant_id: str) -> dict:
        existing = await self._repo.find_store(store_code)
        if not existing:
            raise NotFoundError(f"Store '{store_code}' not found")

        updates = validate_and_build_updates(
            store_format=store_format, city_tier=city_tier,
            region=region, area_sqft=area_sqft,
        )

        now_iso = datetime.now(timezone.utc).isoformat()
        updates["attributes_updated_at"] = now_iso
        updates["attributes_updated_by"] = user_email

        await self._repo.apply_updates(store_code, updates)

        for field, new_val in updates.items():
            if field.startswith("attributes_updated"):
                continue
            await self._repo.append_audit({
                "tenant_id": tenant_id, "action": "attribute_update", "entity_type": "store",
                "entity_id": store_code, "field": field,
                "old_value": None, "new_value": str(new_val),
                "reason": "Store attribute updated", "source": "manual",
                "created_by": user_email, "created_at": now_iso,
            })

        return {
            "success": True,
            "store_code": store_code,
            "updated": [k for k in updates.keys() if not k.startswith("attributes_updated")],
        }
