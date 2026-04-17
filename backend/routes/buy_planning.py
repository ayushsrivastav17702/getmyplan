"""Buy Planning module: Store Wedge Classification + Style Mix Tagging."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import io
import csv
from bson import ObjectId

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

    # Fetch current wedge classes for audit logging
    old_wedges = {}
    async for sd in db.store_master.find(_tenant_match(tenant_id), {"_id": 0, "store_code": 1, "wedge_class": 1}):
        old_wedges[sd.get("store_code")] = sd.get("wedge_class")
    audit_entries = []

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

        # Track change for audit
        old_w = old_wedges.get(s["store_code"])
        if old_w != wedge:
            audit_entries.append({
                "tenant_id": tenant_id, "action": "classify", "entity_type": "store",
                "entity_id": s["store_code"], "field": "wedge_class",
                "old_value": old_w, "new_value": wedge,
                "reason": f"Revenue-based: {s['revenue_pct']}% of total",
                "source": "auto", "created_by": user.get("email", "system"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    if audit_entries:
        await db.buy_planning_audit_log.insert_many(audit_entries)

    return {
        "success": True,
        "method": "revenue_based",
        "total_revenue": round(total_rev, 2),
        "summary": {k: len(v) for k, v in classifications.items()},
        "stores": stores_revenue,
        "audit_changes": len(audit_entries),
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

    # Fetch current style mixes for audit logging
    old_mixes = {}
    async for sd in db.sku_ean_master.aggregate([
        {"$match": {**_tenant_match(tenant_id), "style_mix": {"$exists": True}}},
        {"$group": {"_id": "$style", "mix": {"$first": "$style_mix"}}},
    ]):
        old_mixes[sd["_id"]] = sd.get("mix")
    audit_entries = []

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

        # Track change for audit
        old_m = old_mixes.get(style)
        if old_m != mix:
            audit_entries.append({
                "tenant_id": tenant_id, "action": "classify", "entity_type": "style",
                "entity_id": style, "field": "style_mix",
                "old_value": old_m, "new_value": mix,
                "reason": f"Avg {round(avg_weekly, 1)}/wk, {weeks_active}w active, {round(peak_to_avg, 1)}x peak",
                "source": "auto", "created_by": user.get("email", "system"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

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

    if audit_entries:
        await db.buy_planning_audit_log.insert_many(audit_entries)

    results.sort(key=lambda x: x["total_revenue"], reverse=True)

    return {
        "success": True,
        "method": "revenue_based",
        "total_weeks_analyzed": total_weeks,
        "date_range": {"from": min_day, "to": max_day},
        "summary": {k: len(v) for k, v in classifications.items()},
        "styles": results,
        "audit_changes": len(audit_entries),
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


# ═══════════════════════════════════════════════════
# PHASE 2: Display Minimums + Full Buy Formula
# ═══════════════════════════════════════════════════

class DisplayMinimumReq(BaseModel):
    category: str
    store_wedge: str  # A, B, C
    min_facings: int = 2
    display_units_per_facing: int = 2


@router.get("/display-minimums")
async def get_display_minimums(user: dict = Depends(_dep_user)):
    """Get display minimum configuration per category × wedge."""
    db = _db_func()
    configs = []
    async for doc in db.display_minimums_config.find({}, {"_id": 0}):
        doc["total_display_min_units"] = doc.get("min_facings", 2) * doc.get("display_units_per_facing", 2)
        configs.append(doc)
    return {"configs": configs, "total": len(configs)}


@router.post("/display-minimums")
async def set_display_minimum(body: DisplayMinimumReq, user: dict = Depends(_dep_user)):
    """Set display minimum for a category × wedge combination."""
    db = _db_func()
    total = body.min_facings * body.display_units_per_facing
    await db.display_minimums_config.update_one(
        {"category": body.category, "store_wedge": body.store_wedge},
        {"$set": {
            "category": body.category,
            "store_wedge": body.store_wedge,
            "min_facings": body.min_facings,
            "display_units_per_facing": body.display_units_per_facing,
            "total_display_min_units": total,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )
    return {"success": True, "category": body.category, "store_wedge": body.store_wedge, "total_display_min_units": total}


@router.delete("/display-minimums/{category}/{store_wedge}")
async def delete_display_minimum(category: str, store_wedge: str, user: dict = Depends(_dep_user)):
    result = await _db_func().display_minimums_config.delete_one({"category": category, "store_wedge": store_wedge})
    if result.deleted_count == 0:
        raise HTTPException(404, "Config not found")
    return {"success": True}


# Sell-through targets by style mix (configurable)
DEFAULT_SELL_THROUGH = {"Core": 1.2, "Fashion": 0.8, "Test": 0.4}


class SellThroughConfigReq(BaseModel):
    style_mix: str  # Core, Fashion, Test
    target_multiplier: float


@router.get("/sell-through-config")
async def get_sell_through_config(user: dict = Depends(_dep_user)):
    """Get sell-through multiplier config (tenant-specific + defaults)."""
    db = _db_func()
    stored = {}
    async for doc in db.sell_through_config.find({}, {"_id": 0}):
        stored[doc["style_mix"]] = doc

    configs = []
    for mix in ["Core", "Fashion", "Test"]:
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


@router.put("/sell-through-config")
async def set_sell_through_config(body: SellThroughConfigReq, user: dict = Depends(_dep_user)):
    """Set sell-through multiplier for a style mix."""
    if body.style_mix not in ("Core", "Fashion", "Test"):
        raise HTTPException(400, "style_mix must be Core, Fashion, or Test")
    if body.target_multiplier < 0 or body.target_multiplier > 5:
        raise HTTPException(400, "target_multiplier must be between 0 and 5")
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    # Get old value for audit
    old_doc = await db.sell_through_config.find_one({"style_mix": body.style_mix}, {"_id": 0, "target_multiplier": 1})
    old_val = old_doc.get("target_multiplier") if old_doc else DEFAULT_SELL_THROUGH.get(body.style_mix)
    await db.sell_through_config.update_one(
        {"style_mix": body.style_mix},
        {"$set": {
            "style_mix": body.style_mix,
            "target_multiplier": body.target_multiplier,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.get("email", ""),
        }},
        upsert=True,
    )
    if old_val != body.target_multiplier:
        await db.buy_planning_audit_log.insert_one({
            "tenant_id": tenant_id, "action": "config_update", "entity_type": "config",
            "entity_id": body.style_mix, "field": "target_multiplier",
            "old_value": str(old_val), "new_value": str(body.target_multiplier),
            "reason": f"Sell-through target changed for {body.style_mix}",
            "source": "manual", "created_by": user.get("email", ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    return {"success": True, "style_mix": body.style_mix, "target_multiplier": body.target_multiplier}


@router.post("/sell-through-config/reset")
async def reset_sell_through_config(user: dict = Depends(_dep_user)):
    """Reset all multipliers to system defaults."""
    db = _db_func()
    await db.sell_through_config.delete_many({})
    return {"success": True, "defaults": DEFAULT_SELL_THROUGH}


async def _get_sell_through_targets(db) -> dict:
    """Load sell-through targets from DB, falling back to defaults."""
    targets = dict(DEFAULT_SELL_THROUGH)
    async for doc in db.sell_through_config.find({}, {"_id": 0}):
        targets[doc["style_mix"]] = doc["target_multiplier"]
    return targets


class BuyFormulaReq(BaseModel):
    cover_days: int = 30
    safety_days: int = 7
    sell_through_targets: Optional[dict] = None  # override defaults


@router.post("/buy-formula/calculate")
async def calculate_buy_formula(body: BuyFormulaReq, user: dict = Depends(_dep_user)):
    """
    Full Buy Formula:
    buy_qty = MAX(
        (target_sell_through × forecasted_demand) - current_SOH,
        display_minimum_units × store_count,
        safety_stock_units
    )
    """
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    sell_targets = body.sell_through_targets or DEFAULT_SELL_THROUGH

    # 1. Get store wedge counts
    wedge_counts = {"A": 0, "B": 0, "C": 0}
    async for doc in db.store_master.aggregate([
        {"$match": _tenant_match(tenant_id)},
        {"$group": {"_id": "$wedge_class", "count": {"$sum": 1}}},
    ]):
        if doc["_id"] in wedge_counts:
            wedge_counts[doc["_id"]] = doc["count"]
    total_stores = sum(wedge_counts.values())

    # 2. Get display minimums
    disp_mins = {}
    async for doc in db.display_minimums_config.find({}, {"_id": 0}):
        key = (doc["category"], doc["store_wedge"])
        disp_mins[key] = doc.get("total_display_min_units", 4)

    # 3. Get current SOH (stock on hand) from store_inventory
    soh_pipeline = [
        {"$match": _tenant_match(tenant_id)},
        {"$group": {"_id": "$sku", "total_soh": {"$sum": {"$toInt": {"$ifNull": ["$closing_stock", 0]}}}}},
    ]
    soh_map = {}
    async for doc in db.store_inventory.aggregate(soh_pipeline):
        soh_map[doc["_id"]] = doc["total_soh"]

    # 4. Get ROS per SKU (from daily_sales, last N days)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=body.cover_days)).strftime("%Y-%m-%d")
    ros_pipeline = [
        {"$match": {**_tenant_match(tenant_id), "day": {"$gte": cutoff}}},
        {"$group": {
            "_id": "$sku",
            "total_qty": {"$sum": {"$toInt": {"$ifNull": ["$quantity", 0]}}},
            "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$revenue", 0]}}},
            "days": {"$addToSet": "$day"},
        }},
    ]
    ros_map = {}
    async for doc in db.daily_sales.aggregate(ros_pipeline):
        days = len(doc.get("days", []))
        ros_map[doc["_id"]] = {
            "total_qty": doc["total_qty"],
            "daily_ros": doc["total_qty"] / max(days, 1),
            "revenue": doc["total_revenue"],
        }

    # 5. Get SKU metadata (style_mix, category)
    sku_meta = {}
    async for doc in db.sku_ean_master.find(_tenant_match(tenant_id), {"_id": 0}):
        sku_meta[doc.get("ean", "")] = {
            "style": doc.get("style", ""),
            "category": doc.get("category", ""),
            "sub_category": doc.get("sub_category", ""),
            "style_mix": doc.get("style_mix", "Test"),
            "mrp": doc.get("mrp", 0),
        }

    # 6. Calculate buy quantity per SKU
    buy_plan = []
    totals = {"total_buy_qty": 0, "total_buy_value": 0, "total_display_qty": 0, "total_safety_qty": 0}

    for sku, meta in sku_meta.items():
        mix = meta["style_mix"]
        category = meta["category"]
        ros_data = ros_map.get(sku, {"total_qty": 0, "daily_ros": 0, "revenue": 0})
        current_soh = soh_map.get(sku, 0)

        # Forecasted demand
        daily_ros = ros_data["daily_ros"]
        forecasted_demand = daily_ros * body.cover_days
        sell_through_target = sell_targets.get(mix, 0.8)
        demand_buy = max(0, (sell_through_target * forecasted_demand) - current_soh)

        # Display minimum across eligible stores
        display_qty = 0
        eligible_wedges = {"Core": ["A", "B", "C"], "Fashion": ["A", "B"], "Test": ["A"]}.get(mix, ["A"])
        for w in eligible_wedges:
            dm = disp_mins.get((category, w), disp_mins.get(("ALL", w), 4))
            display_qty += dm * wedge_counts.get(w, 0)

        # Safety stock
        safety_qty = daily_ros * body.safety_days

        # Full formula: MAX of the three
        buy_qty = max(demand_buy, display_qty, safety_qty)
        buy_qty = round(buy_qty)

        buy_value = buy_qty * meta.get("mrp", 0)
        totals["total_buy_qty"] += buy_qty
        totals["total_buy_value"] += buy_value
        totals["total_display_qty"] += round(display_qty)
        totals["total_safety_qty"] += round(safety_qty)

        buy_plan.append({
            "sku": sku,
            "style": meta["style"],
            "category": category,
            "sub_category": meta["sub_category"],
            "style_mix": mix,
            "daily_ros": round(daily_ros, 2),
            "forecasted_demand": round(forecasted_demand),
            "sell_through_target": sell_through_target,
            "demand_buy": round(demand_buy),
            "display_minimum": round(display_qty),
            "safety_stock": round(safety_qty),
            "current_soh": current_soh,
            "buy_qty": buy_qty,
            "buy_value": round(buy_value, 2),
            "mrp": meta["mrp"],
            "binding_constraint": "demand" if demand_buy >= max(display_qty, safety_qty) else "display_min" if display_qty >= safety_qty else "safety_stock",
        })

    buy_plan.sort(key=lambda x: x["buy_value"], reverse=True)

    return {
        "success": True,
        "parameters": {
            "cover_days": body.cover_days,
            "safety_days": body.safety_days,
            "sell_through_targets": sell_targets,
            "store_counts": wedge_counts,
        },
        "totals": {k: round(v, 2) for k, v in totals.items()},
        "sku_count": len(buy_plan),
        "buy_plan": buy_plan,
    }


# ═══════════════════════════════════════════════════
# PHASE 3: DNA Tagging + Piece-Level Attribution
# ═══════════════════════════════════════════════════

class DNATagReq(BaseModel):
    sku: str
    launch_date: Optional[str] = None
    flow_rank: Optional[int] = None  # 1=Hero, 2=Core, 3=Fill-in
    lifecycle_stage: Optional[str] = None  # Pre-launch, Launch, Peak, Decline, Exit
    expected_weeks: Optional[int] = None


class DNABulkTagReq(BaseModel):
    style: str
    launch_date: Optional[str] = None
    flow_rank: Optional[int] = None
    lifecycle_stage: Optional[str] = None
    expected_weeks: Optional[int] = None


@router.post("/dna-tag")
async def tag_sku_dna(body: DNATagReq, user: dict = Depends(_dep_user)):
    """Tag a single SKU with DNA attributes."""
    db = _db_func()
    update = {k: v for k, v in {
        "launch_date": body.launch_date,
        "flow_rank": body.flow_rank,
        "lifecycle_stage": body.lifecycle_stage,
        "expected_weeks": body.expected_weeks,
        "dna_tagged_at": datetime.now(timezone.utc).isoformat(),
    }.items() if v is not None}
    result = await db.sku_ean_master.update_one({"ean": body.sku}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(404, f"SKU '{body.sku}' not found")
    return {"success": True, "sku": body.sku}


@router.post("/dna-tag/bulk")
async def tag_style_dna_bulk(body: DNABulkTagReq, user: dict = Depends(_dep_user)):
    """Tag all SKUs of a style with DNA attributes."""
    db = _db_func()
    update = {k: v for k, v in {
        "launch_date": body.launch_date,
        "flow_rank": body.flow_rank,
        "lifecycle_stage": body.lifecycle_stage,
        "expected_weeks": body.expected_weeks,
        "dna_tagged_at": datetime.now(timezone.utc).isoformat(),
    }.items() if v is not None}
    result = await db.sku_ean_master.update_many({"style": body.style}, {"$set": update})
    return {"success": True, "style": body.style, "skus_updated": result.modified_count}


@router.post("/dna-tag/auto")
async def auto_tag_dna(user: dict = Depends(_dep_user)):
    """
    Auto-tag DNA based on sales data:
    - launch_date: first sale date
    - lifecycle_stage: based on recent vs peak sales trend
    - flow_rank: 1=Hero (top 20% revenue), 2=Core (next 30%), 3=Fill-in (bottom 50%)
    """
    db = _db_func()
    tenant_id = user.get("tenant_id", "")

    # Get first/last sale date + total revenue per style
    pipeline = [
        {"$match": _tenant_match(tenant_id)},
        {"$lookup": {
            "from": "sku_ean_master",
            "let": {"sku": "$sku"},
            "pipeline": [{"$match": {"$expr": {"$eq": ["$ean", "$$sku"]}}}, {"$project": {"style": 1, "_id": 0}}],
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

    styles = []
    async for doc in db.daily_sales.aggregate(pipeline, allowDiskUse=True):
        styles.append(doc)

    if not styles:
        return {"success": True, "message": "No sales data for DNA tagging", "tagged": 0}

    total_rev = sum(s["total_revenue"] for s in styles)
    cumulative = 0
    tagged = 0
    now = datetime.now(timezone.utc)

    for s in styles:
        style = s["_id"]
        cumulative += s["total_revenue"]
        pct = cumulative / max(total_rev, 1)

        # Flow rank
        if pct <= 0.80:
            flow_rank = 1  # Hero
        elif pct <= 0.95:
            flow_rank = 2  # Core
        else:
            flow_rank = 3  # Fill-in

        # Lifecycle stage based on age
        first_sale = s.get("first_sale", "")
        last_sale = s.get("last_sale", "")
        try:
            first_dt = datetime.strptime(first_sale, "%Y-%m-%d") if isinstance(first_sale, str) else first_sale
            last_dt = datetime.strptime(last_sale, "%Y-%m-%d") if isinstance(last_sale, str) else last_sale
            age_weeks = max(1, (now.replace(tzinfo=None) - first_dt).days // 7)
            recency_days = (now.replace(tzinfo=None) - last_dt).days
        except Exception:
            age_weeks = 1
            recency_days = 0

        if age_weeks <= 4:
            lifecycle = "Launch"
        elif recency_days > 30:
            lifecycle = "Exit"
        elif recency_days > 14:
            lifecycle = "Decline"
        elif age_weeks <= 12:
            lifecycle = "Peak"
        else:
            lifecycle = "Decline"

        update = {
            "launch_date": first_sale,
            "flow_rank": flow_rank,
            "lifecycle_stage": lifecycle,
            "expected_weeks": max(4, 52 - age_weeks) if lifecycle != "Exit" else 0,
            "dna_tagged_at": now.isoformat(),
        }
        result = await db.sku_ean_master.update_many({"style": style}, {"$set": update})
        tagged += result.modified_count

    return {"success": True, "styles_processed": len(styles), "skus_tagged": tagged}


@router.get("/dna-tags")
async def get_dna_tags(user: dict = Depends(_dep_user)):
    """Get DNA tags grouped by style."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")

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
        {"$project": {"_id": 0, "style": "$_id", "sku_count": 1, "launch_date": 1, "flow_rank": 1, "lifecycle_stage": 1, "expected_weeks": 1, "style_mix": 1}},
        {"$sort": {"flow_rank": 1, "style": 1}},
    ]

    styles = []
    async for doc in db.sku_ean_master.aggregate(pipeline):
        styles.append(doc)
    return {"styles": styles, "total": len(styles)}


# ── Piece-Level Attribution Matrix ──

@router.get("/attribution/matrix")
async def get_attribution_matrix(user: dict = Depends(_dep_user)):
    """
    Return SKU → Store cluster attribution.
    Core → ALL stores (proportional to store count)
    Fashion → A + B only
    Test → A only
    """
    db = _db_func()
    tenant_id = user.get("tenant_id", "")

    # Get store wedge counts
    wedge_counts = {"A": 0, "B": 0, "C": 0}
    async for doc in db.store_master.aggregate([
        {"$match": _tenant_match(tenant_id)},
        {"$group": {"_id": "$wedge_class", "count": {"$sum": 1}}},
    ]):
        if doc["_id"] in wedge_counts:
            wedge_counts[doc["_id"]] = doc["count"]
    total_stores = sum(wedge_counts.values())

    # Get styles with mix
    pipeline = [
        {"$match": {**_tenant_match(tenant_id), "style_mix": {"$exists": True}}},
        {"$group": {"_id": {"style": "$style", "mix": "$style_mix"}, "sku_count": {"$sum": 1}}},
    ]
    style_data = []
    async for doc in db.sku_ean_master.aggregate(pipeline):
        style_data.append({"style": doc["_id"]["style"], "style_mix": doc["_id"]["mix"], "sku_count": doc["sku_count"]})

    # Attribution rules
    WEDGE_RULES = {
        "Core": {"A": True, "B": True, "C": True},
        "Fashion": {"A": True, "B": True, "C": False},
        "Test": {"A": True, "B": False, "C": False},
    }

    attributions = []
    for s in style_data:
        mix = s["style_mix"]
        rules = WEDGE_RULES.get(mix, WEDGE_RULES["Test"])
        eligible_stores = sum(wedge_counts[w] for w in ["A", "B", "C"] if rules.get(w))
        wedge_alloc = {}
        for w in ["A", "B", "C"]:
            if rules.get(w) and eligible_stores > 0:
                wedge_alloc[w] = {
                    "eligible": True,
                    "stores": wedge_counts[w],
                    "allocation_pct": round(wedge_counts[w] / eligible_stores * 100, 1),
                }
            else:
                wedge_alloc[w] = {"eligible": False, "stores": 0, "allocation_pct": 0}

        attributions.append({
            "style": s["style"],
            "style_mix": mix,
            "sku_count": s["sku_count"],
            "eligible_stores": eligible_stores,
            "total_stores": total_stores,
            "coverage_pct": round(eligible_stores / max(total_stores, 1) * 100, 1),
            "wedge_allocation": wedge_alloc,
        })

    attributions.sort(key=lambda x: x["coverage_pct"], reverse=True)

    return {
        "attributions": attributions,
        "total_styles": len(attributions),
        "store_counts": wedge_counts,
        "rules": WEDGE_RULES,
    }

# ═══════════════════════════════════════════════════
# FEATURE B: Manual Overrides with Audit
# ═══════════════════════════════════════════════════

class WedgeOverrideReq(BaseModel):
    store_code: str
    wedge_class: str  # A, B, C
    reason: str = ""


class MixOverrideReq(BaseModel):
    style: str
    style_mix: str  # Core, Fashion, Test
    reason: str = ""


@router.post("/overrides/store-wedge")
async def override_store_wedge(body: WedgeOverrideReq, user: dict = Depends(_dep_user)):
    """Manually override a store's wedge class with audit trail."""
    if body.wedge_class not in ("A", "B", "C"):
        raise HTTPException(400, "wedge_class must be A, B, or C")
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    store = await db.store_master.find_one({"store_code": body.store_code}, {"_id": 0, "wedge_class": 1})
    if not store:
        raise HTTPException(404, f"Store '{body.store_code}' not found")
    old = store.get("wedge_class")
    now = datetime.now(timezone.utc).isoformat()
    await db.store_master.update_one(
        {"store_code": body.store_code},
        {"$set": {
            "wedge_class": body.wedge_class,
            "wedge_manual_override": True,
            "wedge_classified_at": now,
            "wedge_classified_by": user.get("email", "manual"),
        }},
    )
    await db.buy_planning_overrides.insert_one({
        "entity_type": "store", "entity_id": body.store_code,
        "field": "wedge_class", "old_value": old, "new_value": body.wedge_class,
        "reason": body.reason, "created_by": user.get("email", ""),
        "created_at": now, "is_active": True,
    })
    await db.buy_planning_audit_log.insert_one({
        "tenant_id": tenant_id, "action": "override", "entity_type": "store",
        "entity_id": body.store_code, "field": "wedge_class",
        "old_value": old, "new_value": body.wedge_class,
        "reason": body.reason, "source": "manual",
        "created_by": user.get("email", ""), "created_at": now,
    })
    return {"success": True, "store_code": body.store_code, "old": old, "new": body.wedge_class}


@router.delete("/overrides/store-wedge/{store_code}")
async def revert_store_wedge_override(store_code: str, user: dict = Depends(_dep_user)):
    """Remove manual override — store will be reclassified on next auto-run."""
    db = _db_func()
    await db.store_master.update_one(
        {"store_code": store_code},
        {"$set": {"wedge_manual_override": False}, "$unset": {"wedge_classified_by": ""}},
    )
    await db.buy_planning_overrides.update_many(
        {"entity_type": "store", "entity_id": store_code, "is_active": True},
        {"$set": {"is_active": False, "reverted_at": datetime.now(timezone.utc).isoformat(), "reverted_by": user.get("email", "")}},
    )
    return {"success": True, "message": f"Override removed for {store_code}"}


@router.post("/overrides/style-mix")
async def override_style_mix(body: MixOverrideReq, user: dict = Depends(_dep_user)):
    """Manually override a style's mix classification with audit trail."""
    if body.style_mix not in ("Core", "Fashion", "Test"):
        raise HTTPException(400, "style_mix must be Core, Fashion, or Test")
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    sku = await db.sku_ean_master.find_one({"style": body.style}, {"_id": 0, "style_mix": 1})
    if not sku:
        raise HTTPException(404, f"Style '{body.style}' not found")
    old = sku.get("style_mix")
    now = datetime.now(timezone.utc).isoformat()
    await db.sku_ean_master.update_many(
        {"style": body.style},
        {"$set": {
            "style_mix": body.style_mix,
            "style_mix_manual_override": True,
            "style_mix_classified_at": now,
            "style_mix_classified_by": user.get("email", "manual"),
        }},
    )
    await db.buy_planning_overrides.insert_one({
        "entity_type": "sku", "entity_id": body.style,
        "field": "style_mix", "old_value": old, "new_value": body.style_mix,
        "reason": body.reason, "created_by": user.get("email", ""),
        "created_at": now, "is_active": True,
    })
    await db.buy_planning_audit_log.insert_one({
        "tenant_id": tenant_id, "action": "override", "entity_type": "style",
        "entity_id": body.style, "field": "style_mix",
        "old_value": old, "new_value": body.style_mix,
        "reason": body.reason, "source": "manual",
        "created_by": user.get("email", ""), "created_at": now,
    })
    return {"success": True, "style": body.style, "old": old, "new": body.style_mix}


@router.delete("/overrides/style-mix/{style}")
async def revert_style_mix_override(style: str, user: dict = Depends(_dep_user)):
    """Remove manual override — style will be reclassified on next auto-run."""
    db = _db_func()
    await db.sku_ean_master.update_many(
        {"style": style},
        {"$set": {"style_mix_manual_override": False}, "$unset": {"style_mix_classified_by": ""}},
    )
    await db.buy_planning_overrides.update_many(
        {"entity_type": "sku", "entity_id": style, "is_active": True},
        {"$set": {"is_active": False, "reverted_at": datetime.now(timezone.utc).isoformat(), "reverted_by": user.get("email", "")}},
    )
    return {"success": True, "message": f"Override removed for {style}"}


@router.get("/overrides/history")
async def get_override_history(entity_type: Optional[str] = None, limit: int = 50, user: dict = Depends(_dep_user)):
    """Get history of manual overrides."""
    db = _db_func()
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    overrides = []
    async for doc in db.buy_planning_overrides.find(query, {"_id": 0}).sort("created_at", -1).limit(limit):
        overrides.append(doc)
    return {"overrides": overrides, "total": len(overrides)}


@router.get("/audit-log")
async def get_audit_log(
    entity_type: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(_dep_user),
):
    """Get comprehensive audit log for all buy planning changes."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    query = {"tenant_id": tenant_id}
    if entity_type:
        query["entity_type"] = entity_type
    if source:
        query["source"] = source
    entries = []
    async for doc in db.buy_planning_audit_log.find(query, {"_id": 0}).sort("created_at", -1).limit(limit):
        entries.append(doc)
    return {"entries": entries, "total": len(entries)}


# ═══════════════════════════════════════════════════
# FEATURE C: Export Buy Plan to CSV
# ═══════════════════════════════════════════════════

@router.get("/buy-formula/export/csv")
async def export_buy_plan_csv(cover_days: int = 30, safety_days: int = 7, user: dict = Depends(_dep_user)):
    """Export the full buy plan to CSV."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")

    # Reuse the calculate logic inline for export
    from fastapi.testclient import TestClient
    # Build buy plan data directly
    sell_targets = DEFAULT_SELL_THROUGH

    wedge_counts = {"A": 0, "B": 0, "C": 0}
    async for doc in db.store_master.aggregate([
        {"$match": _tenant_match(tenant_id)},
        {"$group": {"_id": "$wedge_class", "count": {"$sum": 1}}},
    ]):
        if doc["_id"] in wedge_counts:
            wedge_counts[doc["_id"]] = doc["count"]

    disp_mins = {}
    async for doc in db.display_minimums_config.find({}, {"_id": 0}):
        disp_mins[(doc["category"], doc["store_wedge"])] = doc.get("total_display_min_units", 4)

    soh_map = {}
    async for doc in db.store_inventory.aggregate([
        {"$match": _tenant_match(tenant_id)},
        {"$group": {"_id": "$sku", "total_soh": {"$sum": {"$toInt": {"$ifNull": ["$closing_stock", 0]}}}}},
    ]):
        soh_map[doc["_id"]] = doc["total_soh"]

    cutoff = (datetime.now(timezone.utc) - timedelta(days=cover_days)).strftime("%Y-%m-%d")
    ros_map = {}
    async for doc in db.daily_sales.aggregate([
        {"$match": {**_tenant_match(tenant_id), "day": {"$gte": cutoff}}},
        {"$group": {"_id": "$sku", "total_qty": {"$sum": {"$toInt": {"$ifNull": ["$quantity", 0]}}},
                    "total_revenue": {"$sum": {"$toDouble": {"$ifNull": ["$revenue", 0]}}}, "days": {"$addToSet": "$day"}}},
    ]):
        days = len(doc.get("days", []))
        ros_map[doc["_id"]] = {"daily_ros": doc["total_qty"] / max(days, 1), "revenue": doc["total_revenue"]}

    sku_meta = {}
    async for doc in db.sku_ean_master.find(_tenant_match(tenant_id), {"_id": 0}):
        sku_meta[doc.get("ean", "")] = doc

    rows = []
    for sku, meta in sku_meta.items():
        mix = meta.get("style_mix", "Test")
        category = meta.get("category", "")
        ros_data = ros_map.get(sku, {"daily_ros": 0, "revenue": 0})
        current_soh = soh_map.get(sku, 0)
        daily_ros = ros_data["daily_ros"]
        forecasted_demand = daily_ros * cover_days
        sell_through = sell_targets.get(mix, 0.8)
        demand_buy = max(0, (sell_through * forecasted_demand) - current_soh)
        display_qty = 0
        eligible = {"Core": ["A", "B", "C"], "Fashion": ["A", "B"], "Test": ["A"]}.get(mix, ["A"])
        for w in eligible:
            display_qty += disp_mins.get((category, w), disp_mins.get(("ALL", w), 4)) * wedge_counts.get(w, 0)
        safety_qty = daily_ros * safety_days
        buy_qty = round(max(demand_buy, display_qty, safety_qty))
        constraint = "demand" if demand_buy >= max(display_qty, safety_qty) else "display_min" if display_qty >= safety_qty else "safety_stock"
        rows.append({
            "SKU": sku, "Style": meta.get("style", ""), "Category": category,
            "Sub Category": meta.get("sub_category", ""), "Style Mix": mix,
            "MRP": meta.get("mrp", 0), "Daily ROS": round(daily_ros, 2),
            "Current SOH": current_soh, "Forecasted Demand": round(forecasted_demand),
            "Sell-Through Target": sell_through, "Demand Buy": round(demand_buy),
            "Display Minimum": round(display_qty), "Safety Stock": round(safety_qty),
            "Buy Qty": buy_qty, "Buy Value": round(buy_qty * meta.get("mrp", 0), 2),
            "Binding Constraint": constraint,
            "Flow Rank": meta.get("flow_rank"), "Lifecycle": meta.get("lifecycle_stage", ""),
            "Launch Date": meta.get("launch_date", ""),
        })

    rows.sort(key=lambda x: x["Buy Value"], reverse=True)

    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        buf.write("No data available\n")
    buf.seek(0)

    filename = f"buy_plan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ═══════════════════════════════════════════════════
# BUY PLAN PERSISTENCE & APPROVAL WORKFLOW
# ═══════════════════════════════════════════════════

class GeneratePlanReq(BaseModel):
    plan_name: Optional[str] = None
    cover_days: int = 30
    safety_days: int = 7
    notes: Optional[str] = None


class UpdateItemQtyReq(BaseModel):
    item_index: int
    new_qty: int


@router.post("/buy-plans/generate")
async def generate_and_save_plan(body: GeneratePlanReq, user: dict = Depends(_dep_user)):
    """Generate a buy plan using the full formula and save to database."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")

    # Reuse the existing calculate logic
    calc_body = BuyFormulaReq(cover_days=body.cover_days, safety_days=body.safety_days)
    result = await calculate_buy_formula(calc_body, user)

    plan_name = body.plan_name or f"Buy Plan {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
    plan_doc = {
        "tenant_id": tenant_id,
        "plan_name": plan_name,
        "cover_days": body.cover_days,
        "safety_days": body.safety_days,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": user.get("email", ""),
        "status": "draft",
        "items": result.get("buy_plan", []),
        "parameters": result.get("parameters", {}),
        "totals": result.get("totals", {}),
        "sku_count": result.get("sku_count", 0),
        "notes": body.notes,
    }
    insert_result = await db.buy_plans.insert_one(plan_doc)
    plan_id = str(insert_result.inserted_id)

    return {
        "success": True,
        "plan_id": plan_id,
        "plan_name": plan_name,
        "status": "draft",
        "sku_count": result.get("sku_count", 0),
        "totals": result.get("totals", {}),
    }


@router.get("/buy-plans")
async def list_buy_plans(status: Optional[str] = None, limit: int = 20, user: dict = Depends(_dep_user)):
    """List saved buy plans (without items for performance)."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status
    plans = []
    async for doc in db.buy_plans.find(query, {"items": 0}).sort("generated_at", -1).limit(limit):
        plans.append({
            "plan_id": str(doc["_id"]),
            "plan_name": doc.get("plan_name", ""),
            "status": doc.get("status", "draft"),
            "generated_at": doc.get("generated_at", ""),
            "generated_by": doc.get("generated_by", ""),
            "sku_count": doc.get("sku_count", 0),
            "totals": doc.get("totals", {}),
            "cover_days": doc.get("cover_days", 30),
            "notes": doc.get("notes"),
            "approved_at": doc.get("approved_at"),
            "approved_by": doc.get("approved_by"),
        })
    return {"plans": plans, "total": len(plans)}


@router.get("/buy-plans/{plan_id}")
async def get_buy_plan(plan_id: str, user: dict = Depends(_dep_user)):
    """Get a single buy plan with full item details."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    try:
        doc = await db.buy_plans.find_one({"_id": ObjectId(plan_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(404, "Invalid plan ID")
    if not doc:
        raise HTTPException(404, "Plan not found")
    return {
        "plan_id": str(doc["_id"]),
        "plan_name": doc.get("plan_name", ""),
        "status": doc.get("status", "draft"),
        "generated_at": doc.get("generated_at", ""),
        "generated_by": doc.get("generated_by", ""),
        "sku_count": doc.get("sku_count", 0),
        "totals": doc.get("totals", {}),
        "parameters": doc.get("parameters", {}),
        "items": doc.get("items", []),
        "cover_days": doc.get("cover_days", 30),
        "notes": doc.get("notes"),
        "approved_at": doc.get("approved_at"),
        "approved_by": doc.get("approved_by"),
    }


@router.put("/buy-plans/{plan_id}/items")
async def update_plan_item(plan_id: str, body: UpdateItemQtyReq, user: dict = Depends(_dep_user)):
    """Update quantity for a specific item in a draft plan."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    try:
        doc = await db.buy_plans.find_one({"_id": ObjectId(plan_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(404, "Invalid plan ID")
    if not doc:
        raise HTTPException(404, "Plan not found")
    if doc.get("status") != "draft":
        raise HTTPException(400, "Cannot edit non-draft plan")
    items = doc.get("items", [])
    if body.item_index < 0 or body.item_index >= len(items):
        raise HTTPException(400, "Item index out of range")
    items[body.item_index]["edited_qty"] = body.new_qty
    items[body.item_index]["edited_by"] = user.get("email", "")
    items[body.item_index]["edited_at"] = datetime.now(timezone.utc).isoformat()
    total_qty = sum(i.get("edited_qty", i.get("buy_qty", 0)) for i in items)
    total_val = sum(i.get("edited_qty", i.get("buy_qty", 0)) * i.get("mrp", 0) for i in items)
    await db.buy_plans.update_one(
        {"_id": ObjectId(plan_id)},
        {"$set": {"items": items, "totals.total_buy_qty": total_qty, "totals.total_buy_value": round(total_val, 2)}},
    )
    return {"success": True, "item_index": body.item_index, "new_qty": body.new_qty, "total_buy_qty": total_qty}


@router.post("/buy-plans/{plan_id}/approve")
async def approve_buy_plan(plan_id: str, user: dict = Depends(_dep_user)):
    """Approve a draft buy plan."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    try:
        doc = await db.buy_plans.find_one({"_id": ObjectId(plan_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(404, "Invalid plan ID")
    if not doc:
        raise HTTPException(404, "Plan not found")
    if doc.get("status") != "draft":
        raise HTTPException(400, f"Plan is already {doc.get('status')}")
    now = datetime.now(timezone.utc).isoformat()
    await db.buy_plans.update_one(
        {"_id": ObjectId(plan_id)},
        {"$set": {"status": "approved", "approved_at": now, "approved_by": user.get("email", "")}},
    )
    return {"success": True, "plan_id": plan_id, "status": "approved", "approved_at": now}


@router.delete("/buy-plans/{plan_id}")
async def delete_buy_plan(plan_id: str, user: dict = Depends(_dep_user)):
    """Delete a draft buy plan."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    try:
        doc = await db.buy_plans.find_one({"_id": ObjectId(plan_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(404, "Invalid plan ID")
    if not doc:
        raise HTTPException(404, "Plan not found")
    if doc.get("status") != "draft":
        raise HTTPException(400, "Cannot delete non-draft plan")
    await db.buy_plans.delete_one({"_id": ObjectId(plan_id)})
    return {"success": True, "deleted": True}

