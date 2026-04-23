"""
Style-Mix domain module.

Second vertical extracted from routes/buy_planning.py.

Scope:
  POST /style-mix/classify       auto-tag every style as Core/Fashion/Test from sales
  GET  /style-mix                list current classifications + summary
  POST /overrides/style-mix      manual override with audit trail
  DELETE /overrides/style-mix/{style}  revert manual override

The classification algorithm is intentionally a pure function (no DB, no clock)
so it can be unit-tested with 3-line fixtures. Everything else is orchestration.
"""

from datetime import datetime, timezone
from typing import List, Literal, Optional

StyleMix = Literal["Core", "Fashion", "Test"]


class NotFoundError(Exception):
    """Raised when a style does not exist."""


class ValidationError(Exception):
    """Raised for bad inputs (invalid mix value, etc.)."""


# ═════════════════════════════════════════════════════════════════
# 1. Pure classification logic — no DB, no network, no clock.
# ═════════════════════════════════════════════════════════════════

def classify_style(
    *,
    avg_weekly_qty: float,
    weeks_active: int,
    peak_to_avg_ratio: float,
    week_presence_pct: float,   # 0.0–1.0
) -> StyleMix:
    """
    Classify one style based on sales stats.

    Rules (ordered — first match wins):
      Core    : avg ≥ 5 units/week AND present in ≥ 80% of weeks
      Fashion : peak-to-avg ≥ 3× AND active < 26 weeks
      Test    : active < 8 weeks OR avg < 2 units/week
      Default : Fashion (middle ground)
    """
    if avg_weekly_qty >= 5 and week_presence_pct >= 0.80:
        return "Core"
    if peak_to_avg_ratio >= 3 and weeks_active < 26:
        return "Fashion"
    if weeks_active < 8 or avg_weekly_qty < 2:
        return "Test"
    return "Fashion"


def compute_style_stats(weekly_qtys: List[int], total_weeks_in_dataset: int) -> dict:
    """Stats the classifier needs, derivable from any weekly-qty series."""
    weeks_active = len(weekly_qtys)
    total_qty = sum(weekly_qtys)
    avg_weekly = total_qty / max(weeks_active, 1)
    max_weekly = max(weekly_qtys) if weekly_qtys else 0
    peak_to_avg = max_weekly / max(avg_weekly, 0.01)
    week_presence = weeks_active / max(total_weeks_in_dataset, 1)
    return {
        "weeks_active": weeks_active,
        "total_qty": total_qty,
        "avg_weekly_qty": round(avg_weekly, 1),
        "peak_to_avg_ratio": round(peak_to_avg, 1),
        "week_presence_pct": round(week_presence * 100, 1),
        "_raw_week_presence": week_presence,
        "_raw_avg_weekly": avg_weekly,
        "_raw_peak_to_avg": peak_to_avg,
    }


# ═════════════════════════════════════════════════════════════════
# 2. Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

def _tenant_match(tenant_id: str) -> dict:
    return {"$or": [{"tenant_id": tenant_id}, {"tenant_id": {"$exists": False}}]}


class StyleMixRepository:
    def __init__(self, db):
        self._db = db

    async def get_sales_date_range(self, tenant_id: str) -> Optional[dict]:
        cursor = self._db.daily_sales.aggregate([
            {"$match": _tenant_match(tenant_id)},
            {"$group": {"_id": None, "min_day": {"$min": "$day"}, "max_day": {"$max": "$day"}}},
        ])
        docs = await cursor.to_list(1)
        if not docs or not docs[0].get("min_day"):
            return None
        return {"min_day": docs[0]["min_day"], "max_day": docs[0]["max_day"]}

    async def aggregate_weekly_sales_by_style(self, tenant_id: str) -> List[dict]:
        pipeline = [
            {"$match": _tenant_match(tenant_id)},
            {"$lookup": {
                "from": "sku_ean_master",
                "let": {"sku": "$sku"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ean", "$$sku"]}}},
                    {"$project": {"style": 1, "_id": 0}},
                ],
                "as": "sku_info",
            }},
            {"$unwind": {"path": "$sku_info", "preserveNullAndEmptyArrays": True}},
            {"$addFields": {
                "style": {"$ifNull": ["$sku_info.style", "$sku"]},
                "week": {"$dateToString": {"format": "%Y-W%V", "date": {"$dateFromString": {"dateString": "$day", "onError": "$day"}}}},
            }},
            {"$group": {
                "_id": {"style": "$style", "week": "$week"},
                "weekly_qty": {"$sum": {"$toInt": {"$ifNull": ["$quantity", 0]}}},
                "weekly_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$revenue", 0]}}},
            }},
            {"$group": {
                "_id": "$_id.style",
                "weeks_active": {"$sum": 1},
                "total_qty": {"$sum": "$weekly_qty"},
                "total_revenue": {"$sum": "$weekly_revenue"},
                "max_weekly_qty": {"$max": "$weekly_qty"},
                "weekly_qtys": {"$push": "$weekly_qty"},
            }},
        ]
        results: list = []
        async for doc in self._db.daily_sales.aggregate(pipeline, allowDiskUse=True):
            results.append(doc)
        return results

    async def get_current_mixes_by_style(self, tenant_id: str) -> dict:
        out: dict = {}
        async for sd in self._db.sku_ean_master.aggregate([
            {"$match": {**_tenant_match(tenant_id), "style_mix": {"$exists": True}}},
            {"$group": {"_id": "$style", "mix": {"$first": "$style_mix"}}},
        ]):
            out[sd["_id"]] = sd.get("mix")
        return out

    async def apply_classification(self, style: str, mix: StyleMix, stats: dict, now_iso: str):
        await self._db.sku_ean_master.update_many(
            {"style": style},
            {"$set": {
                "style_mix": mix,
                "style_mix_stats": {
                    "avg_weekly_qty": stats["avg_weekly_qty"],
                    "weeks_active": stats["weeks_active"],
                    "peak_to_avg": stats["peak_to_avg_ratio"],
                    "week_presence_pct": stats["week_presence_pct"],
                },
                "style_mix_classified_at": now_iso,
            }},
        )

    async def fallback_tag_all_test(self, tenant_id: str) -> int:
        count = 0
        async for sku in self._db.sku_ean_master.find(_tenant_match(tenant_id), {"_id": 0, "style": 1}):
            await self._db.sku_ean_master.update_many(
                {"style": sku.get("style")},
                {"$set": {"style_mix": "Test"}},
            )
            count += 1
        return count

    async def insert_audit_entries(self, entries: List[dict]):
        if entries:
            await self._db.buy_planning_audit_log.insert_many(entries)

    async def list_styles(self) -> List[dict]:
        pipeline = [
            {"$match": {"style_mix": {"$exists": True}}},
            {"$group": {
                "_id": {"style": "$style", "mix": "$style_mix"},
                "sku_count": {"$sum": 1},
                "stats": {"$first": "$style_mix_stats"},
            }},
            {"$project": {
                "_id": 0,
                "style": "$_id.style",
                "style_mix": "$_id.mix",
                "sku_count": 1,
                "stats": 1,
            }},
            {"$sort": {"style_mix": 1, "style": 1}},
        ]
        out: list = []
        async for doc in self._db.sku_ean_master.aggregate(pipeline):
            out.append(doc)
        return out

    async def find_one_style(self, style: str) -> Optional[dict]:
        return await self._db.sku_ean_master.find_one({"style": style}, {"_id": 0, "style_mix": 1})

    async def apply_manual_override(self, style: str, mix: StyleMix, user_email: str, now_iso: str):
        await self._db.sku_ean_master.update_many(
            {"style": style},
            {"$set": {
                "style_mix": mix,
                "style_mix_manual_override": True,
                "style_mix_classified_at": now_iso,
                "style_mix_classified_by": user_email,
            }},
        )

    async def record_override(self, *, style: str, old: Optional[str], new: StyleMix,
                              reason: Optional[str], user_email: str, now_iso: str, tenant_id: str):
        await self._db.buy_planning_overrides.insert_one({
            "entity_type": "sku", "entity_id": style,
            "field": "style_mix", "old_value": old, "new_value": new,
            "reason": reason, "created_by": user_email,
            "created_at": now_iso, "is_active": True,
        })
        await self._db.buy_planning_audit_log.insert_one({
            "tenant_id": tenant_id, "action": "override", "entity_type": "style",
            "entity_id": style, "field": "style_mix",
            "old_value": old, "new_value": new,
            "reason": reason, "source": "manual",
            "created_by": user_email, "created_at": now_iso,
        })

    async def revert_override(self, style: str, user_email: str, now_iso: str):
        await self._db.sku_ean_master.update_many(
            {"style": style},
            {"$set": {"style_mix_manual_override": False}, "$unset": {"style_mix_classified_by": ""}},
        )
        await self._db.buy_planning_overrides.update_many(
            {"entity_type": "sku", "entity_id": style, "is_active": True},
            {"$set": {"is_active": False, "reverted_at": now_iso, "reverted_by": user_email}},
        )


# ═════════════════════════════════════════════════════════════════
# 3. Service — business logic.
# ═════════════════════════════════════════════════════════════════

class StyleMixService:
    VALID_MIXES = ("Core", "Fashion", "Test")

    def __init__(self, repo: StyleMixRepository):
        self._repo = repo

    @staticmethod
    def _compute_total_weeks(min_day, max_day) -> int:
        try:
            d1 = datetime.strptime(min_day, "%Y-%m-%d") if isinstance(min_day, str) else min_day
            d2 = datetime.strptime(max_day, "%Y-%m-%d") if isinstance(max_day, str) else max_day
            return max(1, (d2 - d1).days // 7)
        except Exception:
            return 12

    async def classify(self, *, tenant_id: str, user_email: str) -> dict:
        now_iso = datetime.now(timezone.utc).isoformat()
        date_range = await self._repo.get_sales_date_range(tenant_id)
        if not date_range:
            count = await self._repo.fallback_tag_all_test(tenant_id)
            return {
                "success": True, "method": "no_sales_fallback",
                "message": "No sales data — all styles tagged as Test. Upload daily sales for proper classification.",
                "summary": {"Core": 0, "Fashion": 0, "Test": count},
            }

        total_weeks = self._compute_total_weeks(date_range["min_day"], date_range["max_day"])
        style_stats = await self._repo.aggregate_weekly_sales_by_style(tenant_id)
        if not style_stats:
            return {"success": True, "method": "no_style_data",
                    "summary": {"Core": 0, "Fashion": 0, "Test": 0}, "styles": []}

        old_mixes = await self._repo.get_current_mixes_by_style(tenant_id)
        classifications = {"Core": [], "Fashion": [], "Test": []}
        results = []
        audit_entries: list = []

        for s in style_stats:
            style = s["_id"]
            stats = compute_style_stats(s.get("weekly_qtys", []), total_weeks)
            mix = classify_style(
                avg_weekly_qty=stats["_raw_avg_weekly"],
                weeks_active=stats["weeks_active"],
                peak_to_avg_ratio=stats["_raw_peak_to_avg"],
                week_presence_pct=stats["_raw_week_presence"],
            )
            classifications[mix].append(style)
            await self._repo.apply_classification(style, mix, stats, now_iso)

            old_m = old_mixes.get(style)
            if old_m != mix:
                audit_entries.append({
                    "tenant_id": tenant_id, "action": "classify", "entity_type": "style",
                    "entity_id": style, "field": "style_mix",
                    "old_value": old_m, "new_value": mix,
                    "reason": f"Avg {stats['avg_weekly_qty']}/wk, {stats['weeks_active']}w active, {stats['peak_to_avg_ratio']}x peak",
                    "source": "auto", "created_by": user_email,
                    "created_at": now_iso,
                })

            results.append({
                "style": style,
                "style_mix": mix,
                "total_qty": stats["total_qty"],
                "total_revenue": round(s.get("total_revenue", 0), 2),
                "avg_weekly_qty": stats["avg_weekly_qty"],
                "weeks_active": stats["weeks_active"],
                "peak_to_avg_ratio": stats["peak_to_avg_ratio"],
                "week_presence_pct": stats["week_presence_pct"],
            })

        await self._repo.insert_audit_entries(audit_entries)
        results.sort(key=lambda x: x["total_revenue"], reverse=True)

        return {
            "success": True, "method": "revenue_based",
            "total_weeks_analyzed": total_weeks,
            "date_range": {"from": date_range["min_day"], "to": date_range["max_day"]},
            "summary": {k: len(v) for k, v in classifications.items()},
            "styles": results,
            "audit_changes": len(audit_entries),
        }

    async def list_classifications(self) -> dict:
        styles = await self._repo.list_styles()
        summary = {"Core": 0, "Fashion": 0, "Test": 0}
        for s in styles:
            mix = s.get("style_mix", "Test")
            if mix in summary:
                summary[mix] += 1
        return {
            "styles": styles,
            "summary": summary,
            "classified": len(styles) > 0,
            "total_styles": len(styles),
        }

    async def override(self, *, style: str, mix: str, reason: Optional[str],
                        user_email: str, tenant_id: str) -> dict:
        if mix not in self.VALID_MIXES:
            raise ValidationError(f"style_mix must be one of {self.VALID_MIXES}")
        existing = await self._repo.find_one_style(style)
        if not existing:
            raise NotFoundError(f"Style '{style}' not found")
        old = existing.get("style_mix")
        now_iso = datetime.now(timezone.utc).isoformat()
        await self._repo.apply_manual_override(style, mix, user_email, now_iso)
        await self._repo.record_override(
            style=style, old=old, new=mix, reason=reason,
            user_email=user_email, now_iso=now_iso, tenant_id=tenant_id,
        )
        return {"success": True, "style": style, "old": old, "new": mix}

    async def revert_override(self, style: str, user_email: str) -> dict:
        now_iso = datetime.now(timezone.utc).isoformat()
        await self._repo.revert_override(style, user_email, now_iso)
        return {"success": True, "message": f"Override removed for {style}"}
