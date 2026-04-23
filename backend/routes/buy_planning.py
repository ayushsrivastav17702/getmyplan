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


def _compute_binding_breakdown(items: list) -> dict:
    """
    Summarize binding_factor across buy plan items.

    This is the signal surface for "are display_minimums misconfigured?"
    If floor_override_pct stays high cycle after cycle, either demand has
    fallen below what floors justify, or the floors are set too aggressively.

    Returned shape:
      {
        "counts":    {demand, display_min, safety_stock, unknown},
        "pcts":      {same keys, percentage of total_skus},
        "total_skus": int,
        "demand_driven_pct": float,
        "floor_override_pct": float,   # display_min + safety_stock
        "by_category": [{category, counts, total}],
      }
    """
    counts = {"demand": 0, "display_min": 0, "safety_stock": 0, "unknown": 0}
    by_cat: dict = {}
    for it in items:
        bf = it.get("binding_factor") or it.get("binding_constraint") or "unknown"
        key = bf if bf in counts else "unknown"
        counts[key] += 1
        cat = it.get("category") or "Uncategorised"
        slot = by_cat.setdefault(cat, {"demand": 0, "display_min": 0, "safety_stock": 0, "unknown": 0, "total": 0})
        slot[key] += 1
        slot["total"] += 1

    total = sum(counts.values())
    pcts = {k: round((v / total * 100), 1) if total > 0 else 0 for k, v in counts.items()}
    by_category = [
        {
            "category": cat,
            "counts": {k: v for k, v in c.items() if k != "total"},
            "total": c["total"],
            "floor_override_pct": round(((c["display_min"] + c["safety_stock"]) / c["total"] * 100), 1) if c["total"] > 0 else 0,
        }
        for cat, c in by_cat.items()
    ]
    by_category.sort(key=lambda x: x["floor_override_pct"], reverse=True)

    return {
        "counts": counts,
        "pcts": pcts,
        "total_skus": total,
        "demand_driven_pct": pcts["demand"],
        "floor_override_pct": round(pcts["display_min"] + pcts["safety_stock"], 1),
        "by_category": by_category,
    }


# ── Store Wedge Classification ──

@router.post("/store-wedge/classify")
async def classify_store_wedge(user: dict = Depends(_dep_user)):
    """
    Classify stores into A/B/C wedge based on revenue contribution.
    A = Top 20% by revenue (≈80% of sales)
    B = Next 30% by revenue (≈15% of sales)
    C = Bottom 50% by revenue (≈5% of sales)
    """
    from domains.buy_planning import (
        StoreWedgeRepository, StoreWedgeService, StoreWedgeNoDataError,
    )
    svc = StoreWedgeService(StoreWedgeRepository(_db_func()))
    try:
        return await svc.classify(
            tenant_id=user.get("tenant_id", ""),
            user_email=user.get("email", "system"),
        )
    except StoreWedgeNoDataError as e:
        raise HTTPException(400, str(e))


@router.get("/store-wedge")
async def get_store_wedge(user: dict = Depends(_dep_user)):
    """Get current store wedge classification."""
    from domains.buy_planning import StoreWedgeRepository, StoreWedgeService
    svc = StoreWedgeService(StoreWedgeRepository(_db_func()))
    return await svc.list_classifications(user.get("tenant_id", ""))


# ── Style Mix Tagging ──

@router.post("/style-mix/classify")
async def classify_style_mix(user: dict = Depends(_dep_user)):
    """
    Classify SKU styles into Core / Fashion / Test.
    Core  = avg >5 units/week, present >80% of weeks
    Fashion = peak-to-avg ratio >3x, lifecycle <26 weeks
    Test  = <8 weeks old OR <2 units/week avg
    """
    from domains.buy_planning import StyleMixRepository, StyleMixService
    svc = StyleMixService(StyleMixRepository(_db_func()))
    return await svc.classify(
        tenant_id=user.get("tenant_id", ""),
        user_email=user.get("email", "system"),
    )


@router.get("/style-mix")
async def get_style_mix(user: dict = Depends(_dep_user)):
    """Get current style mix classification for all SKUs."""
    from domains.buy_planning import StyleMixRepository, StyleMixService
    svc = StyleMixService(StyleMixRepository(_db_func()))
    return await svc.list_classifications()


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
    from domains.buy_planning import DisplayMinimumsRepository, DisplayMinimumsService
    svc = DisplayMinimumsService(DisplayMinimumsRepository(_db_func()))
    return await svc.list_configs()


@router.post("/display-minimums")
async def set_display_minimum(body: DisplayMinimumReq, user: dict = Depends(_dep_user)):
    """Set display minimum for a category × wedge combination."""
    from domains.buy_planning import DisplayMinimumsRepository, DisplayMinimumsService
    svc = DisplayMinimumsService(DisplayMinimumsRepository(_db_func()))
    try:
        return await svc.set_config(
            category=body.category,
            store_wedge=body.store_wedge,
            min_facings=body.min_facings,
            display_units_per_facing=body.display_units_per_facing,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/display-minimums/{category}/{store_wedge}")
async def delete_display_minimum(category: str, store_wedge: str, user: dict = Depends(_dep_user)):
    from domains.buy_planning import (
        DisplayMinimumsRepository, DisplayMinimumsService, NotFoundError,
    )
    svc = DisplayMinimumsService(DisplayMinimumsRepository(_db_func()))
    try:
        return await svc.delete_config(category=category, store_wedge=store_wedge)
    except NotFoundError as e:
        raise HTTPException(404, str(e))


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

    # 6. Load exclusions
    excluded_skus = set()
    async for doc in db.buy_planning_exclusions.find({"tenant_id": tenant_id}, {"_id": 0, "sku": 1}):
        excluded_skus.add(doc.get("sku"))

    # 6b. Load active promotions for lift factors
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    promo_lifts = {}  # category -> max lift, sku -> max lift
    async for promo in db.promotions.find({
        "tenant_id": tenant_id, "status": "active",
        "start_date": {"$lte": today}, "end_date": {"$gte": today},
    }, {"_id": 0, "affected_categories": 1, "affected_skus": 1, "lift_factor": 1}):
        lf = promo.get("lift_factor", 1.0)
        for cat in promo.get("affected_categories", []):
            promo_lifts[f"cat:{cat}"] = max(promo_lifts.get(f"cat:{cat}", 1.0), lf)
        for sku in promo.get("affected_skus", []):
            promo_lifts[f"sku:{sku}"] = max(promo_lifts.get(f"sku:{sku}", 1.0), lf)

    # 7. Calculate buy quantity per SKU
    buy_plan = []
    totals = {"total_buy_qty": 0, "total_buy_value": 0, "total_display_qty": 0, "total_safety_qty": 0, "excluded_skus": 0}

    for sku, meta in sku_meta.items():
        if sku in excluded_skus:
            totals["excluded_skus"] += 1
            continue
        mix = meta["style_mix"]
        category = meta["category"]
        ros_data = ros_map.get(sku, {"total_qty": 0, "daily_ros": 0, "revenue": 0})
        current_soh = soh_map.get(sku, 0)

        # Forecasted demand (with promotion lift)
        daily_ros = ros_data["daily_ros"]
        lift = max(promo_lifts.get(f"sku:{sku}", 1.0), promo_lifts.get(f"cat:{category}", 1.0))
        forecasted_demand = daily_ros * body.cover_days * lift
        sell_through_target = sell_targets.get(mix, 0.8)
        demand_buy = max(0, (sell_through_target * forecasted_demand) - current_soh)

        # Display minimum across eligible stores
        display_qty = 0
        eligible_wedges = {"Core": ["A", "B", "C"], "Fashion": ["A", "B"], "Test": ["A"]}.get(mix, ["A"])
        for w in eligible_wedges:
            dm = disp_mins.get((category, w), disp_mins.get(("ALL", w), 4))
            display_qty += dm * wedge_counts.get(w, 0)

        # Safety stock (statistical: z × MAD × √(LT/RP))
        safety_cfg = await db.safety_stock_config.find_one({"tenant_id": tenant_id}, {"_id": 0})
        if not safety_cfg:
            safety_cfg = {"service_level": 0.95, "review_period_days": 7, "max_safety_weeks": 12}
        z = {0.80: 0.842, 0.85: 1.036, 0.90: 1.282, 0.95: 1.645, 0.98: 2.054, 0.99: 2.326}.get(safety_cfg.get("service_level", 0.95), 1.645)
        rp = safety_cfg.get("review_period_days", 7)
        lead_time = 14  # default lead time days
        import math
        mad = daily_ros * 0.3 if daily_ros > 0 else 0.5  # approximate MAD from ROS volatility
        safety_qty = z * mad * math.sqrt(lead_time / max(rp, 1))
        safety_qty = min(safety_qty, safety_cfg.get("max_safety_weeks", 12) * mad)
        safety_method = "statistical"

        # Full formula: MAX of the three
        buy_qty = max(demand_buy, display_qty, safety_qty)
        buy_qty = round(buy_qty)

        # Binding factor — which component drove the final qty
        if demand_buy >= max(display_qty, safety_qty):
            binding = "demand"
        elif display_qty >= safety_qty:
            binding = "display_min"
        else:
            binding = "safety_stock"

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
            "safety_method": safety_method,
            "promo_lift": lift,
            "current_soh": current_soh,
            "buy_qty": buy_qty,
            "buy_value": round(buy_value, 2),
            "mrp": meta["mrp"],
            "binding_factor": binding,
            "binding_constraint": binding,  # legacy alias — do not remove
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
    from domains.buy_planning import (
        StoreWedgeRepository, StoreWedgeService,
        StoreWedgeValidationError, StoreWedgeNotFoundError,
    )
    svc = StoreWedgeService(StoreWedgeRepository(_db_func()))
    try:
        return await svc.override(
            store_code=body.store_code, wedge=body.wedge_class, reason=body.reason,
            user_email=user.get("email", ""), tenant_id=user.get("tenant_id", ""),
        )
    except StoreWedgeValidationError as e:
        raise HTTPException(400, str(e))
    except StoreWedgeNotFoundError as e:
        raise HTTPException(404, str(e))


@router.delete("/overrides/store-wedge/{store_code}")
async def revert_store_wedge_override(store_code: str, user: dict = Depends(_dep_user)):
    """Remove manual override — store will be reclassified on next auto-run."""
    from domains.buy_planning import StoreWedgeRepository, StoreWedgeService
    svc = StoreWedgeService(StoreWedgeRepository(_db_func()))
    return await svc.revert_override(store_code, user.get("email", ""))


@router.post("/overrides/style-mix")
async def override_style_mix(body: MixOverrideReq, user: dict = Depends(_dep_user)):
    """Manually override a style's mix classification with audit trail."""
    from domains.buy_planning import (
        StyleMixRepository, StyleMixService,
        StyleMixValidationError, StyleMixNotFoundError,
    )
    svc = StyleMixService(StyleMixRepository(_db_func()))
    try:
        return await svc.override(
            style=body.style, mix=body.style_mix, reason=body.reason,
            user_email=user.get("email", ""), tenant_id=user.get("tenant_id", ""),
        )
    except StyleMixValidationError as e:
        raise HTTPException(400, str(e))
    except StyleMixNotFoundError as e:
        raise HTTPException(404, str(e))


@router.delete("/overrides/style-mix/{style}")
async def revert_style_mix_override(style: str, user: dict = Depends(_dep_user)):
    """Remove manual override — style will be reclassified on next auto-run."""
    from domains.buy_planning import StyleMixRepository, StyleMixService
    svc = StyleMixService(StyleMixRepository(_db_func()))
    return await svc.revert_override(style, user.get("email", ""))


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
        if demand_buy >= max(display_qty, safety_qty):
            constraint = "demand"
        elif display_qty >= safety_qty:
            constraint = "display_min"
        else:
            constraint = "safety_stock"
        rows.append({
            "SKU": sku, "Style": meta.get("style", ""), "Category": category,
            "Sub Category": meta.get("sub_category", ""), "Style Mix": mix,
            "MRP": meta.get("mrp", 0), "Daily ROS": round(daily_ros, 2),
            "Current SOH": current_soh, "Forecasted Demand": round(forecasted_demand),
            "Sell-Through Target": sell_through, "Demand Buy": round(demand_buy),
            "Display Minimum": round(display_qty), "Safety Stock": round(safety_qty),
            "Buy Qty": buy_qty, "Buy Value": round(buy_qty * meta.get("mrp", 0), 2),
            "Binding Factor": constraint,
            "Binding Constraint": constraint,  # legacy alias
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
    items = result.get("buy_plan", [])
    binding_breakdown = _compute_binding_breakdown(items)
    plan_doc = {
        "tenant_id": tenant_id,
        "plan_name": plan_name,
        "cover_days": body.cover_days,
        "safety_days": body.safety_days,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": user.get("email", ""),
        "status": "draft",
        "items": items,
        "parameters": result.get("parameters", {}),
        "totals": result.get("totals", {}),
        "sku_count": result.get("sku_count", 0),
        "binding_breakdown": binding_breakdown,
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
        "approvals": doc.get("approvals", {}),
        "submitted_at": doc.get("submitted_at"),
        "submitted_by": doc.get("submitted_by"),
        "category_approved_at": doc.get("category_approved_at"),
        "category_approved_by": doc.get("category_approved_by"),
        "senior_approved_at": doc.get("senior_approved_at"),
        "senior_approved_by": doc.get("senior_approved_by"),
        "head_approved_at": doc.get("head_approved_at"),
        "head_approved_by": doc.get("head_approved_by"),
        "ordered_at": doc.get("ordered_at"),
        "ordered_by": doc.get("ordered_by"),
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
    # Recompute breakdown in case items have been normalized/edited
    binding_breakdown = _compute_binding_breakdown(items)
    await db.buy_plans.update_one(
        {"_id": ObjectId(plan_id)},
        {"$set": {
            "items": items,
            "totals.total_buy_qty": total_qty,
            "totals.total_buy_value": round(total_val, 2),
            "binding_breakdown": binding_breakdown,
        }},
    )
    return {"success": True, "item_index": body.item_index, "new_qty": body.new_qty, "total_buy_qty": total_qty}


# ═══════════════════════════════════════════════════
# MULTI-LEVEL APPROVAL WORKFLOW
# ═══════════════════════════════════════════════════

PLAN_STATUS_CHAIN = ["draft", "submitted", "category_approved", "senior_approved", "head_approved", "ordered"]

APPROVAL_ACTIONS = {
    "submit":            {"from": ["draft"],              "to": "submitted"},
    "approve_category":  {"from": ["submitted"],          "to": "category_approved"},
    "approve_senior":    {"from": ["category_approved"],  "to": "senior_approved"},
    "approve_head":      {"from": ["senior_approved"],    "to": "head_approved"},
    "finance_ack":       {"from": ["head_approved"],      "to": "ordered"},
    "reject":            {"from": ["submitted", "category_approved", "senior_approved", "head_approved"], "to": "rejected"},
    "request_changes":   {"from": ["submitted", "category_approved", "senior_approved"], "to": "draft"},
}

APPROVAL_ROLES = {
    "submit":            ["super_admin", "admin", "junior_planner", "category_planner", "planner"],
    "approve_category":  ["super_admin", "admin", "category_planner"],
    "approve_senior":    ["super_admin", "admin", "senior_planner"],
    "approve_head":      ["super_admin", "admin", "merchandise_head"],
    "finance_ack":       ["super_admin", "admin", "finance"],
    "reject":            ["super_admin", "admin", "category_planner", "senior_planner", "merchandise_head"],
    "request_changes":   ["super_admin", "admin", "category_planner", "senior_planner"],
}


class ApprovalActionReq(BaseModel):
    action: str
    comment: Optional[str] = None


@router.post("/buy-plans/{plan_id}/approval")
async def process_plan_approval(plan_id: str, body: ApprovalActionReq, user: dict = Depends(_dep_user)):
    """Process a multi-level approval action on a buy plan."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    action = body.action
    role = user.get("role", "viewer")

    if action not in APPROVAL_ACTIONS:
        raise HTTPException(400, f"Invalid action: {action}. Valid: {', '.join(APPROVAL_ACTIONS.keys())}")
    if role not in APPROVAL_ROLES.get(action, []):
        raise HTTPException(403, f"Role '{role}' cannot perform '{action}'")

    try:
        doc = await db.buy_plans.find_one({"_id": ObjectId(plan_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(404, "Invalid plan ID")
    if not doc:
        raise HTTPException(404, "Plan not found")

    current = doc.get("status", "draft")
    rule = APPROVAL_ACTIONS[action]
    if current not in rule["from"]:
        raise HTTPException(400, f"Cannot '{action}' from status '{current}'. Requires: {rule['from']}")

    if action in ("reject", "request_changes") and not body.comment:
        raise HTTPException(400, "Comment is required for reject/request_changes")

    new_status = rule["to"]
    now = datetime.now(timezone.utc).isoformat()
    email = user.get("email", "")

    update = {
        "status": new_status,
        f"approvals.{action}": {"by": email, "at": now, "comment": body.comment},
    }
    # Add timestamp fields for each stage
    stage_ts = {
        "submit": ("submitted_at", "submitted_by"),
        "approve_category": ("category_approved_at", "category_approved_by"),
        "approve_senior": ("senior_approved_at", "senior_approved_by"),
        "approve_head": ("head_approved_at", "head_approved_by"),
        "finance_ack": ("ordered_at", "ordered_by"),
    }
    if action in stage_ts:
        ts_field, by_field = stage_ts[action]
        update[ts_field] = now
        update[by_field] = email

    await db.buy_plans.update_one({"_id": ObjectId(plan_id)}, {"$set": update})

    # Audit trail
    await db.buy_planning_approval_audit.insert_one({
        "tenant_id": tenant_id, "plan_id": plan_id,
        "action": action, "from_status": current, "to_status": new_status,
        "comment": body.comment, "performed_by": email, "role": role,
        "performed_at": now,
    })

    return {"success": True, "plan_id": plan_id, "action": action, "old_status": current, "new_status": new_status}


@router.get("/buy-plans/{plan_id}/approval-history")
async def get_approval_history(plan_id: str, user: dict = Depends(_dep_user)):
    """Get the approval audit trail for a plan."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    entries = []
    async for doc in db.buy_planning_approval_audit.find(
        {"tenant_id": tenant_id, "plan_id": plan_id}, {"_id": 0}
    ).sort("performed_at", 1):
        entries.append(doc)
    return {"history": entries, "total": len(entries)}


# Keep old simple approve for backward compat
@router.post("/buy-plans/{plan_id}/approve")
async def approve_buy_plan(plan_id: str, user: dict = Depends(_dep_user)):
    """Simple approve (backward compat) - calls multi-level submit+approve chain."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    try:
        doc = await db.buy_plans.find_one({"_id": ObjectId(plan_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(404, "Invalid plan ID")
    if not doc:
        raise HTTPException(404, "Plan not found")
    status = doc.get("status", "draft")
    if status in ("ordered", "rejected"):
        raise HTTPException(400, f"Plan is already {status}")
    # Auto-advance through all stages
    now = datetime.now(timezone.utc).isoformat()
    email = user.get("email", "")
    await db.buy_plans.update_one(
        {"_id": ObjectId(plan_id)},
        {"$set": {
            "status": "ordered", "approved_at": now, "approved_by": email,
            "submitted_at": now, "submitted_by": email,
            "category_approved_at": now, "category_approved_by": email,
            "senior_approved_at": now, "senior_approved_by": email,
            "head_approved_at": now, "head_approved_by": email,
            "ordered_at": now, "ordered_by": email,
        }},
    )
    return {"success": True, "plan_id": plan_id, "status": "ordered", "approved_at": now}


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



# ═══════════════════════════════════════════════════
# STORE ATTRIBUTES (Format, City Tier, Region)
# ═══════════════════════════════════════════════════

class StoreAttributeUpdateReq(BaseModel):
    store_format: Optional[str] = None  # hypermarket, supermarket, convenience
    city_tier: Optional[str] = None     # tier1, tier2, tier3
    region: Optional[str] = None        # North, South, East, West, Central
    area_sqft: Optional[int] = None


VALID_FORMATS = {"hypermarket", "supermarket", "convenience"}
VALID_TIERS = {"tier1", "tier2", "tier3"}
VALID_REGIONS = {"North", "South", "East", "West", "Central"}


@router.put("/stores/{store_code}/attributes")
async def update_store_attributes(store_code: str, body: StoreAttributeUpdateReq, user: dict = Depends(_dep_user)):
    """Update store extended attributes (format, tier, region, area)."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    store = await db.store_master.find_one({"store_code": store_code}, {"_id": 0, "store_code": 1})
    if not store:
        raise HTTPException(404, f"Store '{store_code}' not found")
    updates = {}
    if body.store_format is not None:
        if body.store_format not in VALID_FORMATS:
            raise HTTPException(400, f"store_format must be one of: {', '.join(VALID_FORMATS)}")
        updates["store_format"] = body.store_format
    if body.city_tier is not None:
        if body.city_tier not in VALID_TIERS:
            raise HTTPException(400, f"city_tier must be one of: {', '.join(VALID_TIERS)}")
        updates["city_tier"] = body.city_tier
    if body.region is not None:
        if body.region not in VALID_REGIONS:
            raise HTTPException(400, f"region must be one of: {', '.join(VALID_REGIONS)}")
        updates["region"] = body.region
    if body.area_sqft is not None:
        updates["area_sqft"] = body.area_sqft
    if not updates:
        raise HTTPException(400, "No attributes to update")
    updates["attributes_updated_at"] = datetime.now(timezone.utc).isoformat()
    updates["attributes_updated_by"] = user.get("email", "")
    await db.store_master.update_one({"store_code": store_code}, {"$set": updates})
    # Audit log
    for field, new_val in updates.items():
        if field.startswith("attributes_updated"):
            continue
        await db.buy_planning_audit_log.insert_one({
            "tenant_id": tenant_id, "action": "attribute_update", "entity_type": "store",
            "entity_id": store_code, "field": field, "old_value": None, "new_value": str(new_val),
            "reason": "Store attribute updated", "source": "manual",
            "created_by": user.get("email", ""), "created_at": datetime.now(timezone.utc).isoformat(),
        })
    return {"success": True, "store_code": store_code, "updated": list(updates.keys())}


# ═══════════════════════════════════════════════════
# EXCLUSION LIST MANAGEMENT
# ═══════════════════════════════════════════════════

class ExclusionCreateReq(BaseModel):
    store_code: str
    sku: str
    reason: str = ""
    expires_at: Optional[str] = None


@router.post("/exclusions")
async def add_exclusion(body: ExclusionCreateReq, user: dict = Depends(_dep_user)):
    """Add a store-SKU exclusion (excluded from buy plans)."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    await db.buy_planning_exclusions.update_one(
        {"tenant_id": tenant_id, "store_code": body.store_code, "sku": body.sku},
        {"$set": {
            "tenant_id": tenant_id, "store_code": body.store_code, "sku": body.sku,
            "reason": body.reason, "expires_at": body.expires_at,
            "created_by": user.get("email", ""), "created_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )
    return {"success": True, "store_code": body.store_code, "sku": body.sku}


@router.delete("/exclusions/{store_code}/{sku}")
async def remove_exclusion(store_code: str, sku: str, user: dict = Depends(_dep_user)):
    """Remove a store-SKU exclusion."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    result = await db.buy_planning_exclusions.delete_one(
        {"tenant_id": tenant_id, "store_code": store_code, "sku": sku}
    )
    if result.deleted_count == 0:
        raise HTTPException(404, "Exclusion not found")
    return {"success": True, "deleted": True}


@router.get("/exclusions")
async def list_exclusions(user: dict = Depends(_dep_user)):
    """List all active exclusions for the tenant."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    exclusions = []
    async for doc in db.buy_planning_exclusions.find({"tenant_id": tenant_id}, {"_id": 0}):
        exclusions.append(doc)
    return {"exclusions": exclusions, "total": len(exclusions)}


# ═══════════════════════════════════════════════════
# INVENTORY INGESTION
# ═══════════════════════════════════════════════════

class InventoryRecordModel(BaseModel):
    store_code: str
    sku: str
    date: str  # ISO date string
    soh: int = 0
    in_transit: int = 0
    open_po_qty: int = 0


class BulkInventoryUploadReq(BaseModel):
    records: list
    source: str = "api"


@router.post("/inventory/bulk")
async def bulk_upload_inventory(body: BulkInventoryUploadReq, user: dict = Depends(_dep_user)):
    """Bulk upload store-level inventory data (SOH, in-transit, open PO)."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    if not body.records:
        raise HTTPException(400, "No records provided")
    if len(body.records) > 100000:
        raise HTTPException(400, "Maximum 100,000 records per request")
    inserted = 0
    updated = 0
    failed = 0
    errors = []
    for rec in body.records:
        try:
            sc = rec.get("store_code", rec.get("store_id", ""))
            sku = rec.get("sku", rec.get("sku_id", ""))
            dt = rec.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            result = await db.store_inventory.update_one(
                {"tenant_id": tenant_id, "store_code": sc, "sku": sku, "date": dt},
                {"$set": {
                    "tenant_id": tenant_id, "store_code": sc, "sku": sku, "date": dt,
                    "soh": rec.get("soh", 0), "in_transit": rec.get("in_transit", 0),
                    "open_po_qty": rec.get("open_po_qty", 0),
                    "source": body.source, "updated_at": datetime.now(timezone.utc).isoformat(),
                    "uploaded_by": user.get("email", ""),
                }},
                upsert=True,
            )
            if result.upserted_id:
                inserted += 1
            elif result.modified_count > 0:
                updated += 1
        except Exception as e:
            failed += 1
            if len(errors) < 10:
                errors.append(f"{rec}: {str(e)}")
    await db.inventory_sync_log.insert_one({
        "tenant_id": tenant_id, "synced_at": datetime.now(timezone.utc).isoformat(),
        "synced_by": user.get("email", ""), "source": body.source,
        "total": len(body.records), "inserted": inserted, "updated": updated, "failed": failed,
    })
    return {"success": failed == 0, "total": len(body.records), "inserted": inserted, "updated": updated, "failed": failed, "errors": errors}


@router.get("/inventory")
async def list_inventory(store_code: Optional[str] = None, sku: Optional[str] = None, limit: int = 200, user: dict = Depends(_dep_user)):
    """List inventory records, optionally filtered by store/sku."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    query = {"tenant_id": tenant_id}
    if store_code:
        query["store_code"] = store_code
    if sku:
        query["sku"] = sku
    records = []
    async for doc in db.store_inventory.find(query, {"_id": 0}).sort("date", -1).limit(limit):
        records.append(doc)
    return {"records": records, "total": len(records)}


@router.get("/inventory/summary")
async def inventory_summary(user: dict = Depends(_dep_user)):
    """Get inventory summary stats."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    total = await db.store_inventory.count_documents({"tenant_id": tenant_id})
    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {
            "_id": None,
            "total_soh": {"$sum": "$soh"},
            "total_in_transit": {"$sum": "$in_transit"},
            "total_open_po": {"$sum": "$open_po_qty"},
            "unique_stores": {"$addToSet": "$store_code"},
            "unique_skus": {"$addToSet": "$sku"},
        }},
    ]
    result = await db.store_inventory.aggregate(pipeline).to_list(1)
    if result:
        r = result[0]
        return {
            "total_records": total,
            "total_soh": r.get("total_soh", 0),
            "total_in_transit": r.get("total_in_transit", 0),
            "total_open_po": r.get("total_open_po", 0),
            "unique_stores": len(r.get("unique_stores", [])),
            "unique_skus": len(r.get("unique_skus", [])),
        }
    return {"total_records": 0, "total_soh": 0, "total_in_transit": 0, "total_open_po": 0, "unique_stores": 0, "unique_skus": 0}


# Last sync info
@router.get("/inventory/sync-status")
async def inventory_sync_status(user: dict = Depends(_dep_user)):
    """Get last inventory sync info."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    last = await db.inventory_sync_log.find_one({"tenant_id": tenant_id}, {"_id": 0}, sort=[("synced_at", -1)])
    return {"last_sync": last}


# ═══════════════════════════════════════════════════
# SAFETY STOCK CONFIGURATION & CALCULATION
# ═══════════════════════════════════════════════════

DEFAULT_SAFETY_CONFIG = {"service_level": 0.95, "review_period_days": 7, "max_safety_weeks": 12}

Z_SCORES = {0.80: 0.842, 0.85: 1.036, 0.90: 1.282, 0.95: 1.645, 0.98: 2.054, 0.99: 2.326, 0.999: 3.09}


class SafetyStockConfigReq(BaseModel):
    service_level: float = 0.95
    review_period_days: int = 7
    max_safety_weeks: int = 12


@router.get("/safety-stock/config")
async def get_safety_stock_config(user: dict = Depends(_dep_user)):
    """Get safety stock config for the tenant."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    doc = await db.safety_stock_config.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not doc:
        return {**DEFAULT_SAFETY_CONFIG, "is_default": True, "z_score": Z_SCORES.get(0.95, 1.645)}
    return {**doc, "is_default": False, "z_score": Z_SCORES.get(doc.get("service_level", 0.95), 1.645)}


@router.put("/safety-stock/config")
async def set_safety_stock_config(body: SafetyStockConfigReq, user: dict = Depends(_dep_user)):
    """Update safety stock config."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    if body.service_level not in Z_SCORES:
        raise HTTPException(400, f"service_level must be one of: {list(Z_SCORES.keys())}")
    if body.review_period_days < 1 or body.review_period_days > 30:
        raise HTTPException(400, "review_period_days must be 1-30")
    if body.max_safety_weeks < 1 or body.max_safety_weeks > 52:
        raise HTTPException(400, "max_safety_weeks must be 1-52")
    await db.safety_stock_config.update_one(
        {"tenant_id": tenant_id},
        {"$set": {
            "tenant_id": tenant_id, "service_level": body.service_level,
            "review_period_days": body.review_period_days, "max_safety_weeks": body.max_safety_weeks,
            "updated_by": user.get("email", ""), "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )
    return {"success": True, "z_score": Z_SCORES[body.service_level], **body.model_dump()}


@router.post("/safety-stock/config/reset")
async def reset_safety_stock_config(user: dict = Depends(_dep_user)):
    """Reset to default safety stock config."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    await db.safety_stock_config.delete_one({"tenant_id": tenant_id})
    return {"success": True, "defaults": DEFAULT_SAFETY_CONFIG}


@router.get("/safety-stock/calculate")
async def calculate_safety_stock(sku: str, lead_time_days: int = 14, user: dict = Depends(_dep_user)):
    """Calculate statistical safety stock for a single SKU."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    cfg = await db.safety_stock_config.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if not cfg:
        cfg = DEFAULT_SAFETY_CONFIG
    z = Z_SCORES.get(cfg.get("service_level", 0.95), 1.645)
    rp = cfg.get("review_period_days", 7)
    max_weeks = cfg.get("max_safety_weeks", 12)
    # Fetch forecast errors (last 90 days)
    errors = []
    async for doc in db.forecast_errors.find({"tenant_id": tenant_id, "sku": sku}, {"_id": 0, "error": 1}).sort("date", -1).limit(52):
        errors.append(doc.get("error", 0))
    mad = sum(errors) / len(errors) if errors else 0.5
    import math
    ss = z * mad * math.sqrt(lead_time_days / rp)
    ss = min(ss, max_weeks * mad)
    return {
        "sku": sku, "safety_stock_units": round(ss, 2), "mad": round(mad, 2),
        "z_score": z, "lead_time_days": lead_time_days, "review_period_days": rp,
        "forecast_errors_used": len(errors), "formula": "z * MAD * sqrt(LT/RP)",
    }



# ═══════════════════════════════════════════════════
# PHASE 1: ORDER CONSOLIDATION & PO MANAGEMENT
# ═══════════════════════════════════════════════════

PO_STATUSES = ["draft", "sent", "confirmed", "shipped", "received", "cancelled"]


class ConsolidateReq(BaseModel):
    plan_id: str


@router.post("/orders/consolidate")
async def consolidate_orders(body: ConsolidateReq, user: dict = Depends(_dep_user)):
    """Consolidate an approved buy plan into supplier-level POs grouped by category."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    try:
        plan = await db.buy_plans.find_one({"_id": ObjectId(body.plan_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(404, "Invalid plan ID")
    if not plan:
        raise HTTPException(404, "Plan not found")
    items = plan.get("items", [])
    if not items:
        raise HTTPException(400, "Plan has no items")

    # Group items by category (proxy for supplier)
    groups = {}
    for item in items:
        cat = item.get("category") or item.get("sub_category") or "General"
        if cat not in groups:
            groups[cat] = {"items": [], "total_units": 0, "total_value": 0}
        qty = item.get("edited_qty") or item.get("buy_qty", 0)
        val = qty * item.get("mrp", 0)
        groups[cat]["items"].append({**item, "po_qty": qty, "po_value": round(val, 2)})
        groups[cat]["total_units"] += qty
        groups[cat]["total_value"] += val

    # Generate POs
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    created_pos = []
    for idx, (cat, data) in enumerate(groups.items()):
        po_number = f"PO-{today}-{cat[:8].upper().replace(' ', '')}-{idx + 1:03d}"
        po_doc = {
            "tenant_id": tenant_id, "po_number": po_number, "plan_id": body.plan_id,
            "plan_name": plan.get("plan_name", ""), "supplier_group": cat,
            "items": data["items"], "total_units": data["total_units"],
            "total_value": round(data["total_value"], 2),
            "unique_skus": len(data["items"]), "status": "draft",
            "created_by": user.get("email", ""), "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.consolidated_pos.insert_one(po_doc)
        created_pos.append({"po_number": po_number, "supplier_group": cat,
                            "total_units": data["total_units"], "total_value": round(data["total_value"], 2),
                            "unique_skus": len(data["items"]), "status": "draft"})
    return {"success": True, "plan_id": body.plan_id, "pos_created": len(created_pos), "orders": created_pos}


@router.get("/orders")
async def list_orders(plan_id: Optional[str] = None, status: Optional[str] = None, user: dict = Depends(_dep_user)):
    """List consolidated POs."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    query = {"tenant_id": tenant_id}
    if plan_id:
        query["plan_id"] = plan_id
    if status:
        query["status"] = status
    orders = []
    async for doc in db.consolidated_pos.find(query, {"_id": 0}).sort("created_at", -1).limit(100):
        orders.append(doc)
    return {"orders": orders, "total": len(orders)}


@router.get("/orders/phased")
async def list_phased_pos(user: dict = Depends(_dep_user)):
    """List all phased POs."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    pos = []
    async for doc in db.phased_pos.find({"tenant_id": tenant_id}, {"_id": 0}).sort("created_at", -1).limit(50):
        pos.append(doc)
    return {"phased_pos": pos, "total": len(pos)}


@router.get("/orders/{po_number}")
async def get_order(po_number: str, user: dict = Depends(_dep_user)):
    """Get a single PO with full item details."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    doc = await db.consolidated_pos.find_one({"tenant_id": tenant_id, "po_number": po_number}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "PO not found")
    return doc


class POStatusReq(BaseModel):
    status: str


@router.put("/orders/{po_number}/status")
async def update_po_status(po_number: str, body: POStatusReq, user: dict = Depends(_dep_user)):
    """Update PO status (draft → sent → confirmed → shipped → received)."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    if body.status not in PO_STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {PO_STATUSES}")
    doc = await db.consolidated_pos.find_one({"tenant_id": tenant_id, "po_number": po_number})
    if not doc:
        raise HTTPException(404, "PO not found")
    now = datetime.now(timezone.utc).isoformat()
    await db.consolidated_pos.update_one(
        {"tenant_id": tenant_id, "po_number": po_number},
        {"$set": {"status": body.status, f"{body.status}_at": now, f"{body.status}_by": user.get("email", ""), "updated_at": now}},
    )
    return {"success": True, "po_number": po_number, "status": body.status}


# ═══════════════════════════════════════════════════
# PHASE 2: PHASED REPLENISHMENT
# ═══════════════════════════════════════════════════

DEFAULT_PHASE_SPLITS = {
    "Core": [50, 30, 20],
    "Fashion": [40, 35, 25],
    "Test": [30, 30, 40],
}


class PhasedReq(BaseModel):
    po_number: str
    phase_weeks: list = [0, 2, 4]
    phase_percentages: list = [50, 30, 20]


@router.post("/orders/phase")
async def create_phased_replenishment(body: PhasedReq, user: dict = Depends(_dep_user)):
    """Split a PO into phased shipments over time."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    po = await db.consolidated_pos.find_one({"tenant_id": tenant_id, "po_number": body.po_number}, {"_id": 0})
    if not po:
        raise HTTPException(404, "PO not found")
    if len(body.phase_weeks) != len(body.phase_percentages):
        raise HTTPException(400, "phase_weeks and phase_percentages must be same length")
    if abs(sum(body.phase_percentages) - 100) > 0.5:
        raise HTTPException(400, f"Percentages must sum to 100 (got {sum(body.phase_percentages)})")

    now = datetime.now(timezone.utc)
    shipments = []
    for idx, (weeks, pct) in enumerate(zip(body.phase_weeks, body.phase_percentages)):
        ship_date = (now + timedelta(weeks=weeks)).isoformat()
        phase_items = []
        for item in po.get("items", []):
            qty = round(item.get("po_qty", item.get("buy_qty", 0)) * pct / 100)
            if qty > 0:
                phase_items.append({"sku": item.get("sku", ""), "style": item.get("style", ""),
                                    "qty": qty, "value": round(qty * item.get("mrp", 0), 2)})
        shipments.append({
            "phase": idx + 1, "weeks_from_now": weeks, "percentage": pct,
            "expected_date": ship_date, "items": phase_items,
            "total_units": sum(i["qty"] for i in phase_items),
            "total_value": round(sum(i["value"] for i in phase_items), 2),
            "status": "ready" if idx == 0 else "pending",
        })

    phased_doc = {
        "tenant_id": tenant_id, "po_number": f"{body.po_number}-PHASED",
        "original_po": body.po_number, "supplier_group": po.get("supplier_group", ""),
        "shipments": shipments, "total_units": po.get("total_units", 0),
        "total_value": po.get("total_value", 0), "phase_count": len(shipments),
        "created_by": user.get("email", ""), "created_at": now.isoformat(),
    }
    await db.phased_pos.insert_one(phased_doc)
    await db.consolidated_pos.update_one(
        {"tenant_id": tenant_id, "po_number": body.po_number},
        {"$set": {"is_phased": True, "phased_po": f"{body.po_number}-PHASED"}},
    )
    return {"success": True, "po_number": f"{body.po_number}-PHASED", "shipments": shipments}


# ═══════════════════════════════════════════════════
# PHASE 3: PROMOTION CALENDAR & LIFT FACTORS
# ═══════════════════════════════════════════════════

class PromotionCreateReq(BaseModel):
    name: str
    promo_type: str = "national"  # national, regional, store
    start_date: str
    end_date: str
    discount_type: str = "percentage"  # percentage, fixed, bogo
    discount_value: float = 0
    affected_categories: list = []
    affected_skus: list = []
    affected_regions: list = []
    lift_factor: float = 1.0
    notes: Optional[str] = None


@router.post("/promotions")
async def create_promotion(body: PromotionCreateReq, user: dict = Depends(_dep_user)):
    """Create a new promotion."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    if body.lift_factor < 0.5 or body.lift_factor > 5:
        raise HTTPException(400, "lift_factor must be between 0.5 and 5")
    now = datetime.now(timezone.utc).isoformat()
    promo_id = f"PROMO-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    doc = {
        "tenant_id": tenant_id, "promo_id": promo_id, **body.model_dump(),
        "status": "active", "created_by": user.get("email", ""), "created_at": now,
    }
    await db.promotions.insert_one(doc)
    return {"success": True, "promo_id": promo_id}


@router.get("/promotions")
async def list_promotions(status: Optional[str] = None, user: dict = Depends(_dep_user)):
    """List promotions."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status
    promos = []
    async for doc in db.promotions.find(query, {"_id": 0}).sort("start_date", -1).limit(100):
        promos.append(doc)
    return {"promotions": promos, "total": len(promos)}


@router.put("/promotions/{promo_id}")
async def update_promotion(promo_id: str, body: PromotionCreateReq, user: dict = Depends(_dep_user)):
    """Update a promotion."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    result = await db.promotions.update_one(
        {"tenant_id": tenant_id, "promo_id": promo_id},
        {"$set": {**body.model_dump(), "updated_by": user.get("email", ""), "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Promotion not found")
    return {"success": True, "promo_id": promo_id}


@router.delete("/promotions/{promo_id}")
async def delete_promotion(promo_id: str, user: dict = Depends(_dep_user)):
    """Delete a promotion."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    result = await db.promotions.delete_one({"tenant_id": tenant_id, "promo_id": promo_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Promotion not found")
    return {"success": True, "deleted": True}


@router.get("/promotions/active-lift")
async def get_active_lift_factors(user: dict = Depends(_dep_user)):
    """Get all active promotion lift factors (for buy formula integration)."""
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    promos = []
    async for doc in db.promotions.find({
        "tenant_id": tenant_id, "status": "active",
        "start_date": {"$lte": today}, "end_date": {"$gte": today},
    }, {"_id": 0, "promo_id": 1, "name": 1, "affected_categories": 1, "affected_skus": 1, "lift_factor": 1}):
        promos.append(doc)
    return {"active_promotions": promos, "total": len(promos)}


# ═══════════════════════════════════════════════════
# BINDING FACTOR ANALYTICS  (display-min misconfiguration detector)
# ═══════════════════════════════════════════════════

@router.post("/analytics/backfill-binding-breakdown")
async def backfill_binding_breakdown(user: dict = Depends(_dep_user)):
    """
    One-shot: backfill `binding_breakdown` onto historical buy_plans that
    pre-date the field. Idempotent — existing breakdowns are recomputed.
    """
    if user.get("role") not in ("super_admin", "admin"):
        raise HTTPException(403, "Admin only")
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    updated = 0
    async for doc in db.buy_plans.find({"tenant_id": tenant_id}, {"items": 1}):
        items = doc.get("items", []) or []
        breakdown = _compute_binding_breakdown(items)
        await db.buy_plans.update_one(
            {"_id": doc["_id"]},
            {"$set": {"binding_breakdown": breakdown}},
        )
        updated += 1
    return {"success": True, "plans_updated": updated}


@router.get("/analytics/binding-factor")
async def binding_factor_analytics(limit: int = 10, user: dict = Depends(_dep_user)):
    """
    Analytics for the "where did the buy qty come from?" question.
    Returns:
      - `latest`: the most recent plan's breakdown (for doughnut chart)
      - `trend`: last N plans ordered oldest→newest (for time-series line)
      - `worst_categories`: categories with highest floor_override_pct across last N plans
      - `plan_count`, `total_skus_analyzed`
    """
    db = _db_func()
    tenant_id = user.get("tenant_id", "")
    limit = max(1, min(limit, 50))

    plans: list = []
    async for doc in db.buy_plans.find(
        {"tenant_id": tenant_id},
        {"_id": 1, "plan_name": 1, "generated_at": 1, "status": 1, "binding_breakdown": 1, "items": 1, "sku_count": 1},
    ).sort("generated_at", -1).limit(limit):
        # Fallback-compute breakdown if missing (rare after backfill)
        bd = doc.get("binding_breakdown")
        if not bd:
            bd = _compute_binding_breakdown(doc.get("items", []) or [])
        plans.append({
            "plan_id": str(doc["_id"]),
            "plan_name": doc.get("plan_name"),
            "generated_at": doc.get("generated_at"),
            "status": doc.get("status"),
            "breakdown": bd,
            "sku_count": doc.get("sku_count", bd.get("total_skus", 0)),
        })

    if not plans:
        return {
            "plan_count": 0,
            "latest": None,
            "trend": [],
            "worst_categories": [],
            "total_skus_analyzed": 0,
        }

    latest = plans[0]
    trend = [
        {
            "plan_id": p["plan_id"],
            "plan_name": p["plan_name"],
            "generated_at": p["generated_at"],
            "total_skus": p["breakdown"]["total_skus"],
            "demand_driven_pct": p["breakdown"]["demand_driven_pct"],
            "floor_override_pct": p["breakdown"]["floor_override_pct"],
            "display_min_pct": p["breakdown"]["pcts"].get("display_min", 0),
            "safety_stock_pct": p["breakdown"]["pcts"].get("safety_stock", 0),
        }
        for p in reversed(plans)  # chronological for chart
    ]

    # Aggregate category floor-override% across ALL plans in window
    cat_totals: dict = {}
    for p in plans:
        for c in p["breakdown"].get("by_category", []):
            slot = cat_totals.setdefault(c["category"], {"skus": 0, "overrides": 0})
            slot["skus"] += c["total"]
            slot["overrides"] += c["counts"].get("display_min", 0) + c["counts"].get("safety_stock", 0)
    worst = sorted(
        [
            {
                "category": cat,
                "total_skus": v["skus"],
                "override_count": v["overrides"],
                "floor_override_pct": round((v["overrides"] / v["skus"] * 100), 1) if v["skus"] else 0,
            }
            for cat, v in cat_totals.items()
            if v["skus"] >= 5  # ignore tiny categories
        ],
        key=lambda x: x["floor_override_pct"],
        reverse=True,
    )[:10]

    return {
        "plan_count": len(plans),
        "latest": {
            "plan_id": latest["plan_id"],
            "plan_name": latest["plan_name"],
            "generated_at": latest["generated_at"],
            "status": latest["status"],
            "breakdown": latest["breakdown"],
        },
        "trend": trend,
        "worst_categories": worst,
        "total_skus_analyzed": sum(p["breakdown"]["total_skus"] for p in plans),
    }
