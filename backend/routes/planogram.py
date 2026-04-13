"""
Planogram Fill Rate Endpoints (PLAN-01 to PLAN-32)
Migrated from Pandas to native MongoDB aggregation for memory efficiency.
"""
from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
import os
from datetime import datetime, timezone

router = APIRouter(prefix="/analytics/planogram", tags=["planogram"])
_client: Optional[AsyncIOMotorClient] = None
_get_cached_data_func = None


def init_planogram(mongo_client: AsyncIOMotorClient, get_cached_data_func=None):
    global _client, _get_cached_data_func
    _client = mongo_client
    _get_cached_data_func = get_cached_data_func


def _db():
    from multi_tenant import tenant_context
    ctx = tenant_context.get()
    return _client[ctx.db_name] if ctx else _client[os.environ["DB_NAME"]]


def _pl(p):
    return [x.strip() for x in p.split(",") if x.strip()] if p else []


def _classify(rate):
    if rate >= 90:
        return "GOOD"
    if rate >= 80:
        return "MODERATE"
    return "CRITICAL"


async def _build_fill_data(db, start_date=None, end_date=None, categories=None, channels=None, regions=None):
    """Build fill rate data using MongoDB queries instead of Pandas DataFrames."""

    # 1. Get inventory date range and find latest day
    inv_match = {}
    if start_date:
        inv_match["day"] = inv_match.get("day", {})
        inv_match["day"]["$gte"] = start_date
    if end_date:
        inv_match.setdefault("day", {})["$lte"] = end_date
    if channels:
        inv_match["channel"] = {"$in": channels}

    # Find latest day in inventory
    date_pipeline = [{"$match": inv_match} if inv_match else {"$match": {}},
                     {"$group": {"_id": None, "max_day": {"$max": "$day"}}}]
    date_result = await db.store_inventory.aggregate(date_pipeline).to_list(1)
    if not date_result:
        return None, None, None
    latest_day = date_result[0]["max_day"]

    # Detect field name: ean or sku (check documents WITH day field)
    sample = await db.store_inventory.find_one({"day": {"$exists": True}}, {"_id": 0})
    if not sample:
        sample = await db.store_inventory.find_one({}, {"_id": 0})
    ean_field = "ean" if sample and "ean" in sample else "sku"

    # 2. Build lookup maps
    sku_map = {}
    async for doc in db.sku_master.find({}, {"_id": 0, "ean": 1, "style": 1, "mrp": 1, "size": 1}):
        if doc.get("ean"):
            sku_map[doc["ean"]] = doc

    style_cat = {}
    async for doc in db.style_master.find({}, {"_id": 0, "style_code": 1, "category": 1}):
        if doc.get("style_code"):
            style_cat[doc["style_code"]] = doc.get("category", "General")

    # Region filter -> store codes
    valid_stores = None
    if regions:
        valid_stores = set()
        async for doc in db.store_master.find({"region": {"$in": regions}}, {"_id": 0, "store_code": 1}):
            valid_stores.add(doc.get("store_code"))

    # Category filter -> valid styles -> valid EANs
    valid_eans = None
    if categories:
        valid_styles = set()
        for style, cat in style_cat.items():
            if cat in categories:
                valid_styles.add(style)
        valid_eans = set()
        for ean, info in sku_map.items():
            if info.get("style") in valid_styles:
                valid_eans.add(ean)

    # 3. Norm allocated: max observed inventory per store-EAN
    norm_match = {}
    if start_date:
        norm_match["day"] = norm_match.get("day", {})
        norm_match["day"]["$gte"] = start_date
    if end_date:
        norm_match.setdefault("day", {})["$lte"] = end_date
    if valid_stores is not None:
        norm_match["store_code"] = {"$in": list(valid_stores)}
    if valid_eans is not None:
        norm_match[ean_field] = {"$in": list(valid_eans)}

    norm_pipeline = [
        {"$match": norm_match} if norm_match else {"$match": {}},
        {"$addFields": {
            "qty": {"$toDouble": {"$ifNull": ["$quantity", {"$ifNull": ["$closing_stock", 0]}]}},
            "_ean": {"$ifNull": ["$ean", "$sku"]},
        }},
        {"$group": {
            "_id": {"store": "$store_code", "ean": "$_ean"},
            "max_qty": {"$max": "$qty"},
        }},
    ]
    norm_map = {}
    async for doc in db.store_inventory.aggregate(norm_pipeline):
        store_val = doc["_id"].get("store")
        ean_val = doc["_id"].get("ean")
        if store_val and ean_val:
            norm_map[(store_val, ean_val)] = max(doc["max_qty"], 1)

    if not norm_map:
        return None, None, None

    # 4. Current stock (latest day SOH)
    soh_match = {"day": latest_day}
    if valid_stores is not None:
        soh_match["store_code"] = {"$in": list(valid_stores)}
    if valid_eans is not None:
        soh_match[ean_field] = {"$in": list(valid_eans)}

    soh_map = {}
    async for doc in db.store_inventory.find(soh_match, {"_id": 0, "store_code": 1, "ean": 1, "sku": 1, "quantity": 1, "closing_stock": 1}):
        key = (doc.get("store_code"), doc.get("ean", doc.get("sku")))
        soh_map[key] = max(float(doc.get("quantity", doc.get("closing_stock", 0)) or 0), 0)

    # 5. ROS from daily_sales
    sales_match = {}
    if start_date:
        sales_match["day"] = sales_match.get("day", {})
        sales_match["day"]["$gte"] = start_date
    if end_date:
        sales_match.setdefault("day", {})["$lte"] = end_date
    if channels:
        sales_match["channel"] = {"$in": channels}
    if valid_stores is not None:
        sales_match["store_code"] = {"$in": list(valid_stores)}
    if valid_eans is not None:
        sales_match["sku"] = {"$in": list(valid_eans)}
    ros_pipeline = [
        {"$match": sales_match} if sales_match else {"$match": {}},
        {"$addFields": {
            "qty": {"$toDouble": {"$ifNull": ["$quantity", 0]}},
            "rev": {"$toDouble": {"$ifNull": ["$revenue", 0]}},
        }},
        {"$group": {
            "_id": {"store": "$store_code", "sku": "$sku"},
            "total_qty": {"$sum": "$qty"},
            "total_rev": {"$sum": "$rev"},
            "days": {"$addToSet": {"$substr": ["$day", 0, 10]}},
        }},
    ]
    ros_map = {}
    async for doc in db.daily_sales.aggregate(ros_pipeline):
        key = (doc["_id"]["store"], doc["_id"]["sku"])
        live = max(len(doc["days"]), 1)
        ros_map[key] = round(doc["total_qty"] / live, 3)

    # 6. Build fill rate items
    fill_items = []
    for (store, ean), norm_val in norm_map.items():
        current_stock = soh_map.get((store, ean), 0)
        fill_rate = round(current_stock / norm_val * 100, 1)
        missing = max(norm_val - current_stock, 0)
        status = _classify(fill_rate)
        sku_info = sku_map.get(ean, {})
        style = sku_info.get("style", "Unknown")
        asp = float(sku_info.get("mrp", 0) or 0)
        category = style_cat.get(style, "General")
        ros = ros_map.get((store, ean), 0)
        lost_sales = round(missing * ros * asp, 2)

        fill_items.append({
            "store_code": store, "ean": ean, "style": style, "category": category,
            "current_stock": current_stock, "norm_allocated": norm_val,
            "fill_rate": fill_rate, "missing_facings": missing,
            "ros": ros, "asp": asp, "lost_sales": lost_sales, "status": status,
        })

    return fill_items, latest_day, norm_map


# =========================================================================
# MAIN ANALYSIS (PLAN-01 to PLAN-14, PLAN-21 to PLAN-25)
# =========================================================================
@router.get("/analysis")
async def get_fill_rate_analysis(
    start_date: str = None, end_date: str = None,
    categories: str = None, channels: str = None,
    regions: str = None, target_fill_rate: int = 85,
):
    db = _db()
    cl, chl, rgl = _pl(categories), _pl(channels), _pl(regions)

    try:
        fill_items, latest_day, norm_map = await _build_fill_data(db, start_date, end_date, cl, chl, rgl)
        if not fill_items:
            return {"error": "Required data not uploaded or no data matches filters"}

        # Overall metrics
        total_current = sum(f["current_stock"] for f in fill_items)
        total_norm = sum(f["norm_allocated"] for f in fill_items)
        overall_fill = round(total_current / max(total_norm, 1) * 100, 1)
        overall_lost = sum(f["lost_sales"] for f in fill_items)

        status_counts = {}
        for f in fill_items:
            status_counts[f["status"]] = status_counts.get(f["status"], 0) + 1

        # Store aggregation
        store_data = {}
        for f in fill_items:
            s = f["store_code"]
            if s not in store_data:
                store_data[s] = {"current_stock": 0, "norm_allocated": 0, "lost_sales": 0,
                                 "skus": set(), "GOOD": 0, "MODERATE": 0, "CRITICAL": 0}
            store_data[s]["current_stock"] += f["current_stock"]
            store_data[s]["norm_allocated"] += f["norm_allocated"]
            store_data[s]["lost_sales"] += f["lost_sales"]
            store_data[s]["skus"].add(f["ean"])
            store_data[s][f["status"]] += 1

        store_agg = []
        for s, v in store_data.items():
            fr = round(v["current_stock"] / max(v["norm_allocated"], 1) * 100, 1)
            store_agg.append({
                "store_code": s, "current_stock": v["current_stock"], "norm_allocated": v["norm_allocated"],
                "lost_sales": round(v["lost_sales"], 2), "sku_count": len(v["skus"]),
                "good_count": v["GOOD"], "moderate_count": v["MODERATE"], "critical_count": v["CRITICAL"],
                "fill_rate": fr, "status": _classify(fr), "region": "Unknown",
            })
        store_agg.sort(key=lambda x: x["fill_rate"])

        # Category aggregation
        cat_data = {}
        for f in fill_items:
            c = f["category"]
            if c not in cat_data:
                cat_data[c] = {"current_stock": 0, "norm_allocated": 0, "lost_sales": 0, "skus": set()}
            cat_data[c]["current_stock"] += f["current_stock"]
            cat_data[c]["norm_allocated"] += f["norm_allocated"]
            cat_data[c]["lost_sales"] += f["lost_sales"]
            cat_data[c]["skus"].add(f["ean"])

        cat_agg = []
        for c, v in cat_data.items():
            fr = round(v["current_stock"] / max(v["norm_allocated"], 1) * 100, 1)
            cat_agg.append({
                "category": c, "current_stock": v["current_stock"], "norm_allocated": v["norm_allocated"],
                "lost_sales": round(v["lost_sales"], 2), "sku_count": len(v["skus"]),
                "fill_rate": fr, "status": _classify(fr),
            })
        cat_agg.sort(key=lambda x: x["fill_rate"])

        # Compliance trend (weekly) — aggregate inventory by day
        inv_daily_pipeline = [
            {"$addFields": {"qty": {"$toDouble": {"$ifNull": ["$quantity", 0]}}, "day_str": {"$substr": ["$day", 0, 10]}}},
            {"$group": {"_id": "$day_str", "total_stock": {"$sum": "$qty"}}},
            {"$sort": {"_id": 1}},
        ]
        daily_results = await db.store_inventory.aggregate(inv_daily_pipeline).to_list(1000)
        # Build weekly from daily
        compliance_trend = []
        if daily_results:
            week_data = {}
            for d in daily_results:
                try:
                    dt = datetime.fromisoformat(d["_id"])
                    week_key = dt.strftime("%b %d")
                    week_num = dt.isocalendar()[1]
                    if week_num not in week_data:
                        week_data[week_num] = {"label": week_key, "rates": [], "stock": 0}
                    fr = round(d["total_stock"] / max(total_norm, 1) * 100, 1)
                    week_data[week_num]["rates"].append(fr)
                    week_data[week_num]["stock"] = d["total_stock"]
                except Exception:
                    pass
            for wn in sorted(week_data.keys())[-12:]:
                w = week_data[wn]
                avg_fr = round(sum(w["rates"]) / max(len(w["rates"]), 1), 1)
                compliance_trend.append({
                    "week_label": w["label"], "fill_rate": avg_fr,
                    "status": _classify(avg_fr), "target": target_fill_rate,
                })

        # Lost sales breakdowns
        lost_by_cat = sorted(
            [{"category": c, "lost_sales": round(v["lost_sales"], 2)} for c, v in cat_data.items()],
            key=lambda x: x["lost_sales"], reverse=True,
        )
        lost_by_store = sorted(
            [{"store_code": s, "lost_sales": round(v["lost_sales"], 2)} for s, v in store_data.items()],
            key=lambda x: x["lost_sales"], reverse=True,
        )[:20]

        # Detail (sorted by fill_rate, first 200)
        detail = sorted(fill_items, key=lambda x: x["fill_rate"])[:200]

        return {
            "summary": {
                "overall_fill_rate": overall_fill,
                "overall_status": _classify(overall_fill),
                "target_fill_rate": target_fill_rate,
                "total_current_stock": round(total_current, 0),
                "total_norm_allocated": round(total_norm, 0),
                "total_lost_sales": round(overall_lost, 2),
                "total_store_skus": len(fill_items),
                "good_count": status_counts.get("GOOD", 0),
                "moderate_count": status_counts.get("MODERATE", 0),
                "critical_count": status_counts.get("CRITICAL", 0),
                "total_stores": len(store_data),
                "snapshot_date": str(latest_day)[:10] if latest_day else None,
                "norm_source": "auto_derived",
            },
            "store_data": store_agg,
            "category_data": cat_agg,
            "compliance_trend": compliance_trend,
            "lost_sales_by_category": lost_by_cat,
            "lost_sales_by_store": lost_by_store,
            "detail": detail,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# =========================================================================
# PRE vs POST REPLENISHMENT (PLAN-15 to PLAN-20)
# =========================================================================
@router.get("/pre-post")
async def get_pre_post_comparison(
    start_date: str = None, end_date: str = None,
    categories: str = None, channels: str = None,
    regions: str = None, target_fill_rate: int = 85,
):
    db = _db()
    cl, chl, rgl = _pl(categories), _pl(channels), _pl(regions)

    # Get pre fill rate
    pre_result = await get_fill_rate_analysis(start_date, end_date, categories, channels, regions, target_fill_rate)
    if "error" in pre_result:
        return pre_result

    # Get replenishment orders
    orders = await db.replenishment_orders.find({"status": {"$in": ["pending", "approved"]}}, {"_id": 0}).to_list(5000)
    runs = await db.replenishment_runs.find({}, {"_id": 0}).sort("created_at", -1).to_list(1)

    order_map = {}
    for o in orders:
        key = (o.get("store_code", ""), str(o.get("sku", "")))
        order_map[key] = order_map.get(key, 0) + o.get("order_qty", 0)

    try:
        fill_items, latest_day, norm_map = await _build_fill_data(db, start_date, end_date, cl, chl, rgl)
        if not fill_items:
            return {"error": "Required data not uploaded"}

        # Apply replenishment orders
        pre_sc = {"GOOD": 0, "MODERATE": 0, "CRITICAL": 0}
        post_sc = {"GOOD": 0, "MODERATE": 0, "CRITICAL": 0}
        pre_store = {}
        post_store = {}
        total_pre_stock = 0
        total_post_stock = 0
        total_norm = 0

        for f in fill_items:
            key = (f["store_code"], f["ean"])
            order_qty = order_map.get(key, 0)
            post_stock = f["current_stock"] + order_qty
            post_fr = round(post_stock / max(f["norm_allocated"], 1) * 100, 1)
            post_status = _classify(post_fr)

            pre_sc[f["status"]] = pre_sc.get(f["status"], 0) + 1
            post_sc[post_status] = post_sc.get(post_status, 0) + 1
            total_pre_stock += f["current_stock"]
            total_post_stock += post_stock
            total_norm += f["norm_allocated"]

            s = f["store_code"]
            if s not in pre_store:
                pre_store[s] = {"stock": 0, "norm": 0}
                post_store[s] = {"stock": 0, "norm": 0}
            pre_store[s]["stock"] += f["current_stock"]
            pre_store[s]["norm"] += f["norm_allocated"]
            post_store[s]["stock"] += post_stock
            post_store[s]["norm"] += f["norm_allocated"]

        pre_overall = round(total_pre_stock / max(total_norm, 1) * 100, 1)
        post_overall = round(total_post_stock / max(total_norm, 1) * 100, 1)
        improvement = round(post_overall - pre_overall, 1)
        improvement_pct = round(improvement / max(pre_overall, 0.1) * 100, 1) if pre_overall > 0 else 0

        # Count improved stores
        improved_stores = 0
        moved_to_good = 0
        rank = {"CRITICAL": 0, "MODERATE": 1, "GOOD": 2}
        for s in pre_store:
            pre_fr = round(pre_store[s]["stock"] / max(pre_store[s]["norm"], 1) * 100, 1)
            post_fr = round(post_store[s]["stock"] / max(post_store[s]["norm"], 1) * 100, 1)
            pre_st = _classify(pre_fr)
            post_st = _classify(post_fr)
            if rank.get(post_st, 0) > rank.get(pre_st, 0):
                improved_stores += 1
            if post_st == "GOOD" and pre_st != "GOOD":
                moved_to_good += 1

        return {
            "pre": {"fill_rate": pre_overall, "status": _classify(pre_overall),
                    "good_count": pre_sc.get("GOOD", 0), "moderate_count": pre_sc.get("MODERATE", 0),
                    "critical_count": pre_sc.get("CRITICAL", 0)},
            "post": {"fill_rate": post_overall, "status": _classify(post_overall),
                     "good_count": post_sc.get("GOOD", 0), "moderate_count": post_sc.get("MODERATE", 0),
                     "critical_count": post_sc.get("CRITICAL", 0)},
            "improvement": improvement, "improvement_pct": improvement_pct,
            "stores_improved": improved_stores, "stores_moved_to_good": moved_to_good,
            "total_stores": len(pre_store),
            "has_replenishment_data": len(orders) > 0,
            "run_id": runs[0]["run_id"] if runs else None,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# =========================================================================
# TREND (PLAN-26 to PLAN-32)
# =========================================================================
@router.get("/trend")
async def get_fill_rate_trend(
    start_date: str = None, end_date: str = None,
    categories: str = None, channels: str = None,
    regions: str = None, target_fill_rate: int = 85,
    granularity: str = "weekly",
):
    db = _db()

    try:
        # Get norm (max observed per store-ean)
        norm_match = {}
        if start_date:
            norm_match["day"] = norm_match.get("day", {})
            norm_match["day"]["$gte"] = start_date
        if end_date:
            norm_match.setdefault("day", {})["$lte"] = end_date

        norm_pipeline = [
            {"$match": norm_match} if norm_match else {"$match": {}},
            {"$addFields": {"qty": {"$toDouble": {"$ifNull": ["$quantity", {"$ifNull": ["$closing_stock", 0]}]}}}},
            {"$group": {"_id": {"store": "$store_code", "ean": {"$ifNull": ["$ean", "$sku"]}}, "max_qty": {"$max": "$qty"}}},
        ]
        total_norm = 0
        async for doc in db.store_inventory.aggregate(norm_pipeline):
            total_norm += max(doc["max_qty"], 1)

        if total_norm == 0:
            return {"error": "Required data not uploaded"}

        # Daily stock totals
        daily_pipeline = [
            {"$match": norm_match} if norm_match else {"$match": {}},
            {"$addFields": {"qty": {"$toDouble": {"$ifNull": ["$quantity", {"$ifNull": ["$closing_stock", 0]}]}}, "day_str": {"$substr": ["$day", 0, 10]}}},
            {"$group": {"_id": "$day_str", "total_stock": {"$sum": "$qty"}}},
            {"$sort": {"_id": 1}},
        ]
        daily_results = await db.store_inventory.aggregate(daily_pipeline).to_list(1000)

        if not daily_results:
            return {"error": "No inventory data"}

        # Build daily fill rates
        daily_data = []
        for d in daily_results:
            fr = round(d["total_stock"] / max(total_norm, 1) * 100, 1)
            daily_data.append({"date": d["_id"], "total_stock": d["total_stock"], "fill_rate": fr,
                               "target": target_fill_rate, "below_threshold": fr < 80})

        # Moving average
        for i, d in enumerate(daily_data):
            window = daily_data[max(0, i - 6):i + 1]
            d["moving_avg_7d"] = round(sum(w["fill_rate"] for w in window) / len(window), 1)

        # Alerts
        alerts = [{"date": d["date"], "fill_rate": d["fill_rate"],
                   "message": f"Fill rate dropped to {d['fill_rate']}% on {d['date']}"}
                  for d in daily_data if d["below_threshold"]][-5:]

        # Resample by granularity
        if granularity == "daily":
            trend = [{"label": d["date"][5:], "fill_rate": d["fill_rate"],
                      "target": target_fill_rate, "moving_avg_7d": d["moving_avg_7d"]}
                     for d in daily_data[-30:]]
        elif granularity == "monthly":
            monthly = {}
            for d in daily_data:
                m = d["date"][:7]
                if m not in monthly:
                    monthly[m] = {"rates": [], "stock": 0}
                monthly[m]["rates"].append(d["fill_rate"])
                monthly[m]["stock"] = d["total_stock"]
            trend = []
            for m in sorted(monthly.keys())[-12:]:
                avg = round(sum(monthly[m]["rates"]) / len(monthly[m]["rates"]), 1)
                trend.append({"label": m, "fill_rate": avg, "target": target_fill_rate, "moving_avg_7d": avg})
        else:
            # Weekly
            weekly = {}
            for d in daily_data:
                try:
                    dt = datetime.fromisoformat(d["date"])
                    wk = dt.isocalendar()[1]
                    yr = dt.year
                    key = (yr, wk)
                    if key not in weekly:
                        weekly[key] = {"label": d["date"][5:], "rates": []}
                    weekly[key]["rates"].append(d["fill_rate"])
                except Exception:
                    pass
            trend = []
            for key in sorted(weekly.keys())[-12:]:
                w = weekly[key]
                avg = round(sum(w["rates"]) / len(w["rates"]), 1)
                trend.append({"label": w["label"], "fill_rate": avg, "target": target_fill_rate, "moving_avg_7d": avg})

        below_count = sum(1 for d in daily_data if d["below_threshold"])

        return {
            "granularity": granularity,
            "target_fill_rate": target_fill_rate,
            "trend": trend,
            "alerts": alerts,
            "total_norm": round(total_norm, 0),
            "below_threshold_days": below_count,
            "total_days": len(daily_data),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
