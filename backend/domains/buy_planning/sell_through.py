"""
Sell-Through Config domain module.

Endpoints owned:
  GET  /sell-through-config          current config (stored + defaults)
  PUT  /sell-through-config          set multiplier for a style_mix
  POST /sell-through-config/reset    wipe overrides back to defaults
"""

from datetime import datetime, timezone
from typing import Optional


DEFAULT_SELL_THROUGH = {"Core": 1.2, "Fashion": 0.8, "Test": 0.4}

VALID_MIXES = ("Core", "Fashion", "Test")


class ValidationError(Exception):
    """Raised on invalid input (unknown mix or out-of-range multiplier)."""


# ═════════════════════════════════════════════════════════════════
# Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

class SellThroughRepository:
    def __init__(self, db):
        self._db = db

    async def list_stored(self) -> dict:
        stored: dict = {}
        async for doc in self._db.sell_through_config.find({}, {"_id": 0}):
            stored[doc["style_mix"]] = doc
        return stored

    async def get_current(self, style_mix: str) -> Optional[dict]:
        return await self._db.sell_through_config.find_one(
            {"style_mix": style_mix}, {"_id": 0, "target_multiplier": 1},
        )

    async def upsert(self, *, style_mix: str, multiplier: float,
                     user_email: str, now_iso: str):
        await self._db.sell_through_config.update_one(
            {"style_mix": style_mix},
            {"$set": {
                "style_mix": style_mix,
                "target_multiplier": multiplier,
                "updated_at": now_iso,
                "updated_by": user_email,
            }},
            upsert=True,
        )

    async def delete_all(self):
        await self._db.sell_through_config.delete_many({})

    async def append_audit(self, entry: dict):
        await self._db.buy_planning_audit_log.insert_one(entry)

    async def get_targets(self) -> dict:
        """Load sell-through targets from DB, falling back to defaults."""
        targets = dict(DEFAULT_SELL_THROUGH)
        async for doc in self._db.sell_through_config.find({}, {"_id": 0}):
            targets[doc["style_mix"]] = doc["target_multiplier"]
        return targets


# ═════════════════════════════════════════════════════════════════
# Service — orchestration + validation.
# ═════════════════════════════════════════════════════════════════

class SellThroughService:
    def __init__(self, repo: SellThroughRepository):
        self._repo = repo

    async def list_configs(self) -> dict:
        stored = await self._repo.list_stored()
        configs = []
        for mix in VALID_MIXES:
            if mix in stored:
                configs.append({
                    "style_mix": mix,
                    "target_multiplier": stored[mix]["target_multiplier"],
                    "is_default": False,
                    "updated_at": stored[mix].get("updated_at"),
                    "updated_by": stored[mix].get("updated_by"),
                })
            else:
                configs.append({
                    "style_mix": mix,
                    "target_multiplier": DEFAULT_SELL_THROUGH[mix],
                    "is_default": True,
                })
        return {"configs": configs}

    async def set_config(self, *, style_mix: str, multiplier: float,
                          user_email: str, tenant_id: str) -> dict:
        if style_mix not in VALID_MIXES:
            raise ValidationError("style_mix must be Core, Fashion, or Test")
        if multiplier < 0 or multiplier > 5:
            raise ValidationError("target_multiplier must be between 0 and 5")

        old_doc = await self._repo.get_current(style_mix)
        old_val = old_doc.get("target_multiplier") if old_doc else DEFAULT_SELL_THROUGH.get(style_mix)
        now_iso = datetime.now(timezone.utc).isoformat()
        await self._repo.upsert(
            style_mix=style_mix, multiplier=multiplier,
            user_email=user_email, now_iso=now_iso,
        )
        if old_val != multiplier:
            await self._repo.append_audit({
                "tenant_id": tenant_id, "action": "config_update", "entity_type": "config",
                "entity_id": style_mix, "field": "target_multiplier",
                "old_value": str(old_val), "new_value": str(multiplier),
                "reason": f"Sell-through target changed for {style_mix}",
                "source": "manual", "created_by": user_email, "created_at": now_iso,
            })
        return {"success": True, "style_mix": style_mix, "target_multiplier": multiplier}

    async def reset(self) -> dict:
        await self._repo.delete_all()
        return {"success": True, "defaults": DEFAULT_SELL_THROUGH}
