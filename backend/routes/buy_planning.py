"""Buy Planning module: Store Wedge Classification + Style Mix Tagging."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/buy-planning", tags=["buy-planning"])

_db_func = None
_get_current_user = None


def init_buy_planning(get_db_func, get_current_user_func):
    global _db_func, _get_current_user
    _db_func = get_db_func
    _get_current_user = get_current_user_func


async def _dep_user(request: Request) -> dict:
    return await _get_current_user(request)


def _tenant_match(tenant_id: str) -> dict:
    """Match documents with or without tenant_id (handles sample data)."""
    return {"$or": [{"tenant_id": tenant_id}, {"tenant_id": {"$exists": False}}]}


# ── Store Wedge Classification ──

@router.post("/store-wedge/classify")
async def classify_store_wedge(user: dict = Depends(_dep_user)):
    """
    Classify stores into A/B/C wedge based on revenue contribution.
    A = Top 20% by revenue (≈80% of sales)
    B = Next 30% by revenue (≈15% of sales)
    C = Bottom 50% by revenue (≈5% of sales)
    """
    db = _db_func()
    tenant_id = user.get("tenant_id", "")

    # Aggregate total revenue per store from daily_sales
    pipeline = [
        {"$match": _tenant_match(tenant_id)},
        {"$group": {
            "_id": "$store_code",
            "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$revenue", 0]}}},
            "total_qty": {"$sum": {"$toInt": {"$ifNull": ["$quantity", 0]}}},
            "days_active": {"$addToSet": "$day"},
        }},
        {"$project": {
            "store_code": "$_id",
            "_id": 0,
            "total_revenue": 1,
            "total_qty": 1,
            "days_active": {"$size": "$days_active"},
        }},
        {"$sort": {"total_revenue": -1}},
    ]

    stores_revenue = []
    async for doc in db.daily_sales.aggregate(pipeline):
        stores_revenue.append(doc)

    if not stores_revenue:
        # Fallback: use store_master tier if no sales data
        stores = []
        async for s in db.store_master.find(_tenant_match(tenant_id), {"_id": 0}):
            stores.append(s)
        if not stores:
            raise HTTPException(400, "No store data found. Upload store master and daily sales first.")
        # Use existing tier or area_sqft as proxy
        for s in stores:
            tier = s.get("tier", "C")
            wedge = "A" if tier == "A" else "B" if tier == "B" else "C"
            await db.store_master.update_one(
                {"store_code": s["store_code"]},
                {"$set": {"wedge_class": wedge}},
            )
        return {
            "success": True,
            "method": "tier_fallback",
            "message": "Used existing tier data (no sales data). Upload daily sales for revenue-based classification.",
            "summary": {"A": sum(1 for s in stores if s.get("tier") == "A"),
                        "B": sum(1 for s in stores if s.get("tier") == "B"),
                        "C": sum(1 for s in stores if s.get("tier") not in ("A", "B"))},
        }

    # Calculate cumulative revenue share
    total_rev = sum(s["total_revenue"] for s in stores_revenue)
    if total_rev == 0:
        raise HTTPException(400, "All stores have zero revenue.")

    cumulative = 0
    classifications = {"A": [], "B": [], "C": []}

    for s in stores_revenue:
        cumulative += s["total_revenue"]
        pct = cumulative / total_rev
        if pct <= 0.80:
            wedge = "A"
        elif pct <= 0.95:
            wedge = "B"
        else:
            wedge = "C"
        s["wedge_class"] = wedge
        s["revenue_pct"] = round(s["total_revenue"] / total_rev * 100, 1)
        classifications[wedge].append(s["store_code"])

        # Update store_master
        await db.store_master.update_one(
            {"store_code": s["store_code"]},
            {"$set": {"wedge_class": wedge, "total_revenue": s["total_revenue"],
                      "wedge_classified_at": datetime.now(timezone.utc).isoformat()}},
        )

    return {
        "success": True,
        "method": "revenue_based",
        "total_revenue": round(total_rev, 2),
        "summary": {k: len(v) for k, v in classifications.items()},
        "stores": stores_revenue,
    }


@router.get("/store-wedge")
async def get_store_wedge(user: dict = Depends(_dep_user)):
    """Get current store wedge classification."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")

    stores = []
    async for s in db.store_master.find(_tenant_match(tenant_id), {"_id": 0}):
        stores.append(s)

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


# ── Style Mix Tagging ──

@router.post("/style-mix/classify")
async def classify_style_mix(user: dict = Depends(_dep_user)):
    """
    Classify SKU styles into Core / Fashion / Test.
    Core  = avg >5 units/week, present >80% of weeks
    Fashion = peak-to-avg ratio >3x, lifecycle <26 weeks
    Test  = <8 weeks old OR <2 units/week avg
    """
    db = _db_func()
    tenant_id = user.get("tenant_id", "")

    # Get the date range from daily_sales
    date_pipeline = [
        {"$match": _tenant_match(tenant_id)},
        {"$group": {"_id": None, "min_day": {"$min": "$day"}, "max_day": {"$max": "$day"}}},
    ]
    date_range = await db.daily_sales.aggregate(date_pipeline).to_list(1)
    if not date_range or not date_range[0].get("min_day"):
        # Fallback: tag all as Test
        sku_count = 0
        async for sku in db.sku_ean_master.find(_tenant_match(tenant_id), {"_id": 0, "style": 1}):
            await db.sku_ean_master.update_many(
                {"style": sku.get("style")},
                {"$set": {"style_mix": "Test"}},
            )
            sku_count += 1
        return {
            "success": True,
            "method": "no_sales_fallback",
            "message": "No sales data — all styles tagged as Test. Upload daily sales for proper classification.",
            "summary": {"Core": 0, "Fashion": 0, "Test": sku_count},
        }

    min_day = date_range[0]["min_day"]
    max_day = date_range[0]["max_day"]

    # Calculate total weeks in dataset
    try:
        from datetime import datetime as _dt
        d1 = _dt.strptime(min_day, "%Y-%m-%d") if isinstance(min_day, str) else min_day
        d2 = _dt.strptime(max_day, "%Y-%m-%d") if isinstance(max_day, str) else max_day
        total_weeks = max(1, (d2 - d1).days // 7)
    except Exception:
        total_weeks = 12

    # Aggregate: weekly sales per style
    weekly_pipeline = [
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

    style_stats = []
    async for doc in db.daily_sales.aggregate(weekly_pipeline, allowDiskUse=True):
        style_stats.append(doc)

    if not style_stats:
        return {"success": True, "method": "no_style_data", "summary": {"Core": 0, "Fashion": 0, "Test": 0}, "styles": []}

    # Classify each style
    classifications = {"Core": [], "Fashion": [], "Test": []}
    results = []

    for s in style_stats:
        style = s["_id"]
        weeks_active = s.get("weeks_active", 0)
        total_qty = s.get("total_qty", 0)
        avg_weekly = total_qty / max(weeks_active, 1)
        max_weekly = s.get("max_weekly_qty", 0)
        peak_to_avg = max_weekly / max(avg_weekly, 0.01)
        week_presence = weeks_active / max(total_weeks, 1)

        # Classification logic
        if avg_weekly >= 5 and week_presence >= 0.80:
            mix = "Core"
        elif peak_to_avg >= 3 and weeks_active < 26:
            mix = "Fashion"
        elif weeks_active < 8 or avg_weekly < 2:
            mix = "Test"
        else:
            mix = "Fashion"  # Default middle ground

        classifications[mix].append(style)

        # Update sku_ean_master for all SKUs of this style
        await db.sku_ean_master.update_many(
            {"style": style},
            {"$set": {
                "style_mix": mix,
                "style_mix_stats": {
                    "avg_weekly_qty": round(avg_weekly, 1),
                    "weeks_active": weeks_active,
                    "peak_to_avg": round(peak_to_avg, 1),
                    "week_presence_pct": round(week_presence * 100, 1),
                },
                "style_mix_classified_at": datetime.now(timezone.utc).isoformat(),
            }},
        )

        results.append({
            "style": style,
            "style_mix": mix,
            "total_qty": total_qty,
            "total_revenue": round(s.get("total_revenue", 0), 2),
            "avg_weekly_qty": round(avg_weekly, 1),
            "weeks_active": weeks_active,
            "peak_to_avg_ratio": round(peak_to_avg, 1),
            "week_presence_pct": round(week_presence * 100, 1),
        })

    results.sort(key=lambda x: x["total_revenue"], reverse=True)

    return {
        "success": True,
        "method": "revenue_based",
        "total_weeks_analyzed": total_weeks,
        "date_range": {"from": min_day, "to": max_day},
        "summary": {k: len(v) for k, v in classifications.items()},
        "styles": results,
    }


@router.get("/style-mix")
async def get_style_mix(user: dict = Depends(_dep_user)):
    """Get current style mix classification for all SKUs."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")

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

    styles = []
    async for doc in db.sku_ean_master.aggregate(pipeline):
        styles.append(doc)

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


# ── Assortment Matrix (Wedge × Mix) ──

@router.get("/assortment-matrix")
async def get_assortment_matrix(user: dict = Depends(_dep_user)):
    """
    Return the Wedge × Style Mix assortment matrix:
    A-Stores: Core + Fashion + Test (Full assortment)
    B-Stores: Core + Fashion (Standard assortment)
    C-Stores: Core only (Efficiency assortment)
    """
    db = _db_func()
    tenant_id = user.get("tenant_id", "")

    # Get store wedge counts
    store_pipeline = [
        {"$match": _tenant_match(tenant_id)},
        {"$group": {"_id": "$wedge_class", "count": {"$sum": 1}, "stores": {"$push": "$store_code"}}},
    ]
    wedge_counts = {}
    async for doc in db.store_master.aggregate(store_pipeline):
        wedge_counts[doc["_id"]] = {"count": doc["count"], "stores": doc["stores"]}

    # Get style mix counts
    mix_pipeline = [
        {"$match": {"style_mix": {"$exists": True}}},
        {"$group": {"_id": "$style_mix", "styles": {"$addToSet": "$style"}}},
    ]
    mix_data = {}
    async for doc in db.sku_ean_master.aggregate(mix_pipeline):
        mix_data[doc["_id"]] = list(set(doc["styles"]))

    core_styles = mix_data.get("Core", [])
    fashion_styles = mix_data.get("Fashion", [])
    test_styles = mix_data.get("Test", [])

    matrix = {
        "A": {
            "stores": wedge_counts.get("A", {}).get("count", 0),
            "assortment": "Full (Core + Fashion + Test)",
            "styles": len(core_styles) + len(fashion_styles) + len(test_styles),
            "style_breakdown": {"Core": len(core_styles), "Fashion": len(fashion_styles), "Test": len(test_styles)},
        },
        "B": {
            "stores": wedge_counts.get("B", {}).get("count", 0),
            "assortment": "Standard (Core + Fashion)",
            "styles": len(core_styles) + len(fashion_styles),
            "style_breakdown": {"Core": len(core_styles), "Fashion": len(fashion_styles)},
        },
        "C": {
            "stores": wedge_counts.get("C", {}).get("count", 0),
            "assortment": "Efficiency (Core NOS only)",
            "styles": len(core_styles),
            "style_breakdown": {"Core": len(core_styles)},
        },
    }

    return {"matrix": matrix, "core_styles": core_styles, "fashion_styles": fashion_styles, "test_styles": test_styles}
