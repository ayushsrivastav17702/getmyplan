"""
DNA Tags domain module.

Endpoints owned:
  POST /dna-tag          tag one SKU with DNA attrs
  POST /dna-tag/bulk     tag all SKUs of a style
  POST /dna-tag/auto     auto-tag DNA from sales data
  GET  /dna-tags         list current DNA tags grouped by style

Pure classification rules:
  flow_rank:   1=Hero (≤80% cum rev), 2=Core (≤95%), 3=Fill-in (rest)
  lifecycle:   Launch if age ≤ 4 wks; else Exit/Decline/Peak based on age + recency
"""

from datetime import datetime, timezone
from typing import List, Optional


class NotFoundError(Exception):
    """Raised when SKU not found."""


# ═════════════════════════════════════════════════════════════════
# 1. Pure classifiers — no I/O.
# ═════════════════════════════════════════════════════════════════

def classify_flow_rank(cumulative_pct: float) -> int:
    """Top 80% rev → Hero (1), next 15% → Core (2), rest → Fill-in (3)."""
    if cumulative_pct <= 0.80:
        return 1
    if cumulative_pct <= 0.95:
        return 2
    return 3


def classify_lifecycle(age_weeks: int, recency_days: int) -> str:
    """
    Launch    (≤4 weeks old)
    Exit      (no sale for 30+ days)
    Decline   (no sale for 14-30 days OR >12 wks old)
    Peak      (4-12 weeks old, selling)
    """
    if age_weeks <= 4:
        return "Launch"
    if recency_days > 30:
        return "Exit"
    if recency_days > 14:
        return "Decline"
    if age_weeks <= 12:
        return "Peak"
    return "Decline"


def compute_expected_weeks(age_weeks: int, lifecycle: str) -> int:
    """Remaining runway — 52-week cap, 0 if Exit."""
    if lifecycle == "Exit":
        return 0
    return max(4, 52 - age_weeks)


def parse_sale_date_safely(value) -> Optional[datetime]:
    """Accept both date strings and datetime objects; return naive datetime or None."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


# ═════════════════════════════════════════════════════════════════
# 2. Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

def _tenant_match(tenant_id: str) -> dict:
    return {"$or": [{"tenant_id": tenant_id}, {"tenant_id": {"$exists": False}}]}


class DnaTagsRepository:
    def __init__(self, db):
        self._db = db

    async def tag_sku(self, sku: str, update: dict) -> int:
        result = await self._db.sku_ean_master.update_one({"ean": sku}, {"$set": update})
        return result.matched_count

    async def tag_style(self, style: str, update: dict) -> int:
        result = await self._db.sku_ean_master.update_many({"style": style}, {"$set": update})
        return result.modified_count

    async def aggregate_style_sales(self, tenant_id: str) -> List[dict]:
        pipeline = [
            {"$match": _tenant_match(tenant_id)},
            {"$lookup": {
                "from": "sku_ean_master",
                "let": {"sku": "$sku"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$ean", "$$sku"]}}},
                    {"$project": {"style": 1, "_id": 0}},
                ],
                "as": "info",
            }},
            {"$unwind": {"path": "$info", "preserveNullAndEmptyArrays": True}},
            {"$group": {
                "_id": {"$ifNull": ["$info.style", "$sku"]},
                "first_sale": {"$min": "$day"},
                "last_sale": {"$max": "$day"},
                "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$revenue", 0]}}},
                "total_qty": {"$sum": {"$toInt": {"$ifNull": ["$quantity", 0]}}},
            }},
            {"$sort": {"total_revenue": -1}},
        ]
        out: list = []
        async for doc in self._db.daily_sales.aggregate(pipeline, allowDiskUse=True):
            out.append(doc)
        return out

    async def list_dna_tags(self, tenant_id: str) -> List[dict]:
        pipeline = [
            {"$match": {**_tenant_match(tenant_id), "dna_tagged_at": {"$exists": True}}},
            {"$group": {
                "_id": "$style",
                "sku_count": {"$sum": 1},
                "launch_date": {"$first": "$launch_date"},
                "flow_rank": {"$first": "$flow_rank"},
                "lifecycle_stage": {"$first": "$lifecycle_stage"},
                "expected_weeks": {"$first": "$expected_weeks"},
                "style_mix": {"$first": "$style_mix"},
            }},
            {"$project": {
                "_id": 0, "style": "$_id", "sku_count": 1, "launch_date": 1,
                "flow_rank": 1, "lifecycle_stage": 1, "expected_weeks": 1, "style_mix": 1,
            }},
            {"$sort": {"flow_rank": 1, "style": 1}},
        ]
        out: list = []
        async for doc in self._db.sku_ean_master.aggregate(pipeline):
            out.append(doc)
        return out


# ═════════════════════════════════════════════════════════════════
# 3. Service — orchestration.
# ═════════════════════════════════════════════════════════════════

def _build_update(launch_date, flow_rank, lifecycle_stage, expected_weeks) -> dict:
    return {k: v for k, v in {
        "launch_date": launch_date,
        "flow_rank": flow_rank,
        "lifecycle_stage": lifecycle_stage,
        "expected_weeks": expected_weeks,
        "dna_tagged_at": datetime.now(timezone.utc).isoformat(),
    }.items() if v is not None}


class DnaTagsService:
    def __init__(self, repo: DnaTagsRepository):
        self._repo = repo

    async def tag_sku(self, *, sku, launch_date=None, flow_rank=None,
                      lifecycle_stage=None, expected_weeks=None) -> dict:
        update = _build_update(launch_date, flow_rank, lifecycle_stage, expected_weeks)
        matched = await self._repo.tag_sku(sku, update)
        if matched == 0:
            raise NotFoundError(f"SKU '{sku}' not found")
        return {"success": True, "sku": sku}

    async def tag_style_bulk(self, *, style, launch_date=None, flow_rank=None,
                             lifecycle_stage=None, expected_weeks=None) -> dict:
        update = _build_update(launch_date, flow_rank, lifecycle_stage, expected_weeks)
        modified = await self._repo.tag_style(style, update)
        return {"success": True, "style": style, "skus_updated": modified}

    async def auto_tag(self, tenant_id: str) -> dict:
        styles = await self._repo.aggregate_style_sales(tenant_id)
        if not styles:
            return {"success": True, "message": "No sales data for DNA tagging", "tagged": 0}

        total_rev = sum(s.get("total_revenue", 0) for s in styles)
        cumulative = 0.0
        tagged = 0
        now = datetime.now(timezone.utc)

        for s in styles:
            style = s["_id"]
            cumulative += s.get("total_revenue", 0)
            pct = cumulative / max(total_rev, 1)
            flow_rank = classify_flow_rank(pct)

            first_dt = parse_sale_date_safely(s.get("first_sale"))
            last_dt = parse_sale_date_safely(s.get("last_sale"))
            if first_dt and last_dt:
                age_weeks = max(1, (now.replace(tzinfo=None) - first_dt).days // 7)
                recency_days = (now.replace(tzinfo=None) - last_dt).days
            else:
                age_weeks, recency_days = 1, 0

            lifecycle = classify_lifecycle(age_weeks, recency_days)
            update = {
                "launch_date": s.get("first_sale", ""),
                "flow_rank": flow_rank,
                "lifecycle_stage": lifecycle,
                "expected_weeks": compute_expected_weeks(age_weeks, lifecycle),
                "dna_tagged_at": now.isoformat(),
            }
            tagged += await self._repo.tag_style(style, update)

        return {"success": True, "styles_processed": len(styles), "skus_tagged": tagged}

    async def list_tags(self, tenant_id: str) -> dict:
        styles = await self._repo.list_dna_tags(tenant_id)
        return {"styles": styles, "total": len(styles)}
