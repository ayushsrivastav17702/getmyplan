"""
Safety-Stock domain module.

Endpoints owned:
  GET    /safety-stock/config       current tenant config (+ z_score)
  PUT    /safety-stock/config       set service_level / review_period / max_weeks
  POST   /safety-stock/config/reset wipe tenant config
  GET    /safety-stock/calculate    compute z × MAD × √(LT/RP) for a SKU

Pure formula: safety_stock = min(z × MAD × √(LT/RP), max_weeks × MAD)
"""

import math
from datetime import datetime, timezone
from typing import Optional


DEFAULT_SAFETY_CONFIG = {
    "service_level": 0.95,
    "review_period_days": 7,
    "max_safety_weeks": 12,
}

Z_SCORES = {
    0.80: 0.842, 0.85: 1.036, 0.90: 1.282, 0.95: 1.645,
    0.98: 2.054, 0.99: 2.326, 0.999: 3.09,
}


class ValidationError(Exception):
    """Raised on invalid service_level / review_period / max_weeks."""


# ═════════════════════════════════════════════════════════════════
# 1. Pure math — no I/O.
# ═════════════════════════════════════════════════════════════════

def z_score_for(service_level: float) -> float:
    return Z_SCORES.get(service_level, 1.645)


def compute_safety_stock(*, mad: float, z: float, lead_time_days: int,
                          review_period_days: int, max_safety_weeks: int) -> float:
    """
    Classical safety-stock formula, capped so no SKU's safety can exceed
    max_weeks × MAD (protects against pathological inputs).
    """
    raw = z * mad * math.sqrt(lead_time_days / max(review_period_days, 1))
    return min(raw, max_safety_weeks * mad)


def validate_config(*, service_level: float, review_period_days: int, max_safety_weeks: int):
    if service_level not in Z_SCORES:
        raise ValidationError(f"service_level must be one of: {list(Z_SCORES.keys())}")
    if review_period_days < 1 or review_period_days > 30:
        raise ValidationError("review_period_days must be 1-30")
    if max_safety_weeks < 1 or max_safety_weeks > 52:
        raise ValidationError("max_safety_weeks must be 1-52")


# ═════════════════════════════════════════════════════════════════
# 2. Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

class SafetyStockRepository:
    def __init__(self, db):
        self._db = db

    async def get_config(self, tenant_id: str) -> Optional[dict]:
        return await self._db.safety_stock_config.find_one({"tenant_id": tenant_id}, {"_id": 0})

    async def upsert_config(self, *, tenant_id: str, service_level: float,
                             review_period_days: int, max_safety_weeks: int,
                             user_email: str, now_iso: str):
        await self._db.safety_stock_config.update_one(
            {"tenant_id": tenant_id},
            {"$set": {
                "tenant_id": tenant_id, "service_level": service_level,
                "review_period_days": review_period_days, "max_safety_weeks": max_safety_weeks,
                "updated_by": user_email, "updated_at": now_iso,
            }},
            upsert=True,
        )

    async def delete_config(self, tenant_id: str):
        await self._db.safety_stock_config.delete_one({"tenant_id": tenant_id})

    async def list_forecast_errors(self, *, tenant_id: str, sku: str, limit: int = 52):
        errors = []
        async for doc in self._db.forecast_errors.find(
            {"tenant_id": tenant_id, "sku": sku}, {"_id": 0, "error": 1},
        ).sort("date", -1).limit(limit):
            errors.append(doc.get("error", 0))
        return errors


# ═════════════════════════════════════════════════════════════════
# 3. Service — orchestration.
# ═════════════════════════════════════════════════════════════════

class SafetyStockService:
    def __init__(self, repo: SafetyStockRepository):
        self._repo = repo

    async def get_config(self, tenant_id: str) -> dict:
        doc = await self._repo.get_config(tenant_id)
        if not doc:
            return {
                **DEFAULT_SAFETY_CONFIG,
                "is_default": True,
                "z_score": z_score_for(0.95),
            }
        return {
            **doc,
            "is_default": False,
            "z_score": z_score_for(doc.get("service_level", 0.95)),
        }

    async def set_config(self, *, tenant_id: str, service_level: float,
                          review_period_days: int, max_safety_weeks: int,
                          user_email: str) -> dict:
        validate_config(
            service_level=service_level,
            review_period_days=review_period_days,
            max_safety_weeks=max_safety_weeks,
        )
        now_iso = datetime.now(timezone.utc).isoformat()
        await self._repo.upsert_config(
            tenant_id=tenant_id, service_level=service_level,
            review_period_days=review_period_days, max_safety_weeks=max_safety_weeks,
            user_email=user_email, now_iso=now_iso,
        )
        return {
            "success": True, "z_score": z_score_for(service_level),
            "service_level": service_level,
            "review_period_days": review_period_days,
            "max_safety_weeks": max_safety_weeks,
        }

    async def reset(self, tenant_id: str) -> dict:
        await self._repo.delete_config(tenant_id)
        return {"success": True, "defaults": DEFAULT_SAFETY_CONFIG}

    async def calculate(self, *, tenant_id: str, sku: str, lead_time_days: int = 14) -> dict:
        cfg = await self._repo.get_config(tenant_id) or DEFAULT_SAFETY_CONFIG
        z = z_score_for(cfg.get("service_level", 0.95))
        rp = cfg.get("review_period_days", 7)
        max_weeks = cfg.get("max_safety_weeks", 12)

        errors = await self._repo.list_forecast_errors(tenant_id=tenant_id, sku=sku)
        mad = sum(errors) / len(errors) if errors else 0.5
        ss = compute_safety_stock(
            mad=mad, z=z, lead_time_days=lead_time_days,
            review_period_days=rp, max_safety_weeks=max_weeks,
        )
        return {
            "sku": sku, "safety_stock_units": round(ss, 2), "mad": round(mad, 2),
            "z_score": z, "lead_time_days": lead_time_days, "review_period_days": rp,
            "forecast_errors_used": len(errors), "formula": "z * MAD * sqrt(LT/RP)",
        }
