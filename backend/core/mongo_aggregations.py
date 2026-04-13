"""
MongoDB Aggregation Pipelines for Analytics.
Replaces in-memory Pandas operations with server-side aggregation for scalability.
Handles both shared DB (with tenant_id) and tenant-specific DBs (no tenant_id).
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


_tid_cache = {}

async def _has_tenant_id(tdb: AsyncIOMotorDatabase, collection: str) -> bool:
    """Check if a collection uses tenant_id field. Cached per db+collection."""
    cache_key = f"{tdb.name}:{collection}"
    if cache_key in _tid_cache:
        return _tid_cache[cache_key]
    doc = await tdb[collection].find_one({"tenant_id": {"$exists": True}}, {"tenant_id": 1})
    result = doc is not None and doc.get("tenant_id") is not None
    _tid_cache[cache_key] = result
    return result


async def _build_match(tdb: AsyncIOMotorDatabase, collection: str, tenant_id: str,
                       start_date: str = None, end_date: str = None,
                       date_field: str = "day", extra: dict = None) -> dict:
    """Build $match with optional tenant_id (skipped if collection doesn't use it)."""
    match = {}
    if await _has_tenant_id(tdb, collection):
        match["tenant_id"] = tenant_id
    if start_date or end_date:
        df = {}
        if start_date:
            df["$gte"] = start_date
        if end_date:
            df["$lte"] = end_date
        if df:
            match[date_field] = df
    if extra:
        match.update(extra)
    return match


def _tenant_match(has_tid: bool, tenant_id: str) -> dict:
    """Quick inline tenant match — use when _build_match is too heavy."""
    return {"tenant_id": tenant_id} if has_tid else {}


async def _resolve_filter_skus(
    tdb: AsyncIOMotorDatabase,
    tenant_id: str,
    categories: List[str] = None,
    channels: List[str] = None,
    regions: List[str] = None,
) -> dict:
    """
    Pre-resolve category/region filters into lists of valid SKUs/store_codes.
    Returns extra $match conditions for daily_sales.
    """
    _has_tid = await _has_tenant_id(tdb, "daily_sales")
    extra = {}

    if categories:
        _sm_tid = await _has_tenant_id(tdb, "style_master")
        style_codes = set()
        async for doc in tdb.style_master.find(
            {**_tenant_match(_sm_tid, tenant_id), "category": {"$in": categories}},
            {"_id": 0, "style_code": 1},
        ):
            if doc.get("style_code"):
                style_codes.add(doc["style_code"])
        if style_codes:
            _sk_tid = await _has_tenant_id(tdb, "sku_master")
            eans = set()
            async for doc in tdb.sku_master.find(
                {**_tenant_match(_sk_tid, tenant_id), "style": {"$in": list(style_codes)}},
                {"_id": 0, "ean": 1},
            ):
                if doc.get("ean"):
                    eans.add(doc["ean"])
            if eans:
                extra["sku"] = {"$in": list(eans)}

    if channels:
        extra["channel"] = {"$in": channels}

    if regions:
        _st_tid = await _has_tenant_id(tdb, "store_master")
        store_codes = set()
        async for doc in tdb.store_master.find(
            {**_tenant_match(_st_tid, tenant_id), "region": {"$in": regions}},
            {"_id": 0, "store_code": 1},
        ):
            if doc.get("store_code"):
                store_codes.add(doc["store_code"])
        if store_codes:
            extra["store_code"] = {"$in": list(store_codes)}

    return extra


# ═══════════════════════════════════════════════════════════
# EXECUTIVE KPIs — MongoDB Aggregation
# ═══════════════════════════════════════════════════════════

async def agg_executive_kpis(
    tdb: AsyncIOMotorDatabase,
    tenant_id: str,
    start_date: str = None,
    end_date: str = None,
    categories: List[str] = None,
    channels: List[str] = None,
    regions: List[str] = None,
) -> dict:
    """Compute revenue, units, margin, WoW, YoY via MongoDB aggregation."""
    _has_tid = await _has_tenant_id(tdb, "daily_sales")

    extra = await _resolve_filter_skus(tdb, tenant_id, categories, channels, regions)

    # ── Total revenue & units ──
    match = _tenant_match(_has_tid, tenant_id)
    if start_date:
        match["day"] = match.get("day", {})
        match["day"]["$gte"] = start_date
    if end_date:
        match.setdefault("day", {})["$lte"] = end_date
    match.update(extra)

    pipeline = [
        {"$match": match},
        {"$addFields": {
            "rev_num": {"$toDouble": {"$ifNull": ["$revenue", 0]}},
            "qty_num": {"$toInt": {"$ifNull": ["$quantity", 0]}},
        }},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$rev_num"},
            "total_units": {"$sum": "$qty_num"},
            "min_day": {"$min": "$day"},
            "max_day": {"$max": "$day"},
        }},
    ]

    result = await tdb.daily_sales.aggregate(pipeline).to_list(1)
    if not result:
        return {
            "revenue": 0, "units_sold": 0, "margin_pct": None,
            "mrp_realisation_pct": None, "total_cogs": 0,
            "wow": {"revenue_change": 0, "units_change": 0,
                    "current_revenue": 0, "previous_revenue": 0,
                    "current_units": 0, "previous_units": 0},
            "yoy": {"revenue_change": 0, "current_revenue": 0, "previous_revenue": 0},
            "has_data": False,
        }

    agg = result[0]
    total_revenue = float(agg["total_revenue"])
    total_units = int(agg["total_units"])
    min_day = agg.get("min_day")
    max_day = agg.get("max_day")

    # ── COGS margin ──
    true_margin_pct = None
    total_cogs = 0
    cogs_match = _tenant_match(_has_tid, tenant_id)
    if start_date:
        cogs_match["transaction_date"] = cogs_match.get("transaction_date", {})
        cogs_match["transaction_date"]["$gte"] = start_date
    if end_date:
        cogs_match.setdefault("transaction_date", {})["$lte"] = end_date

    cogs_pipeline = [
        {"$match": cogs_match},
        {"$addFields": {"cogs_num": {"$toDouble": {"$ifNull": ["$cogs", 0]}}}},
        {"$group": {"_id": None, "total_cogs": {"$sum": "$cogs_num"}}},
    ]
    cogs_result = await tdb.cogs.aggregate(cogs_pipeline).to_list(1)
    if cogs_result:
        total_cogs = float(cogs_result[0]["total_cogs"])
        if total_revenue > 0 and total_cogs > 0:
            true_margin_pct = round((total_revenue - total_cogs) / total_revenue * 100, 1)

    # ── MRP Realisation (fallback) ──
    mrp_realisation = None
    if true_margin_pct is None and total_revenue > 0:
        # Get MRP from sku_master, join with sales
        mrp_pipeline = [
            {"$match": match},
            {"$lookup": {
                "from": "sku_master",
                "localField": "sku",
                "foreignField": "ean",
                "as": "sku_info",
            }},
            {"$unwind": {"path": "$sku_info", "preserveNullAndEmptyArrays": True}},
            {"$addFields": {
                "qty_num": {"$toDouble": {"$ifNull": ["$quantity", 0]}},
                "mrp_num": {"$toDouble": {"$ifNull": ["$sku_info.mrp", 0]}},
            }},
            {"$group": {
                "_id": None,
                "total_mrp_value": {"$sum": {"$multiply": ["$qty_num", "$mrp_num"]}},
            }},
        ]
        mrp_result = await tdb.daily_sales.aggregate(mrp_pipeline).to_list(1)
        if mrp_result and mrp_result[0]["total_mrp_value"] > 0:
            mrp_realisation = round(total_revenue / mrp_result[0]["total_mrp_value"] * 100, 1)

    margin_pct = true_margin_pct if true_margin_pct is not None else mrp_realisation

    # ── WoW ──
    wow = {"revenue_change": 0, "units_change": 0,
           "current_revenue": total_revenue, "previous_revenue": 0,
           "current_units": total_units, "previous_units": 0}

    if min_day and max_day:
        try:
            max_dt = datetime.fromisoformat(max_day) if isinstance(max_day, str) else max_day
            min_dt = datetime.fromisoformat(min_day) if isinstance(min_day, str) else min_day
            date_range_days = (max_dt - min_dt).days

            if date_range_days >= 7:
                cutoff = (max_dt - timedelta(days=7)).isoformat() if isinstance(max_day, str) else (max_dt - timedelta(days=7))
                cutoff_str = cutoff if isinstance(cutoff, str) else cutoff.isoformat()
                prev_cutoff = (max_dt - timedelta(days=14)).isoformat() if isinstance(max_day, str) else (max_dt - timedelta(days=14))
                prev_cutoff_str = prev_cutoff if isinstance(prev_cutoff, str) else prev_cutoff.isoformat()

                cur_match = dict(match)
                cur_match["day"] = {"$gt": cutoff_str}
                cur_pipeline = [
                    {"$match": cur_match},
                    {"$addFields": {"rev": {"$toDouble": {"$ifNull": ["$revenue", 0]}}, "qty": {"$toInt": {"$ifNull": ["$quantity", 0]}}}},
                    {"$group": {"_id": None, "rev": {"$sum": "$rev"}, "qty": {"$sum": "$qty"}}},
                ]
                cur_result = await tdb.daily_sales.aggregate(cur_pipeline).to_list(1)

                prev_match = dict(match)
                prev_match["day"] = {"$gt": prev_cutoff_str, "$lte": cutoff_str}
                prev_pipeline = [
                    {"$match": prev_match},
                    {"$addFields": {"rev": {"$toDouble": {"$ifNull": ["$revenue", 0]}}, "qty": {"$toInt": {"$ifNull": ["$quantity", 0]}}}},
                    {"$group": {"_id": None, "rev": {"$sum": "$rev"}, "qty": {"$sum": "$qty"}}},
                ]
                prev_result = await tdb.daily_sales.aggregate(prev_pipeline).to_list(1)

                cur_rev = float(cur_result[0]["rev"]) if cur_result else 0
                prev_rev = float(prev_result[0]["rev"]) if prev_result else 0
                cur_units = int(cur_result[0]["qty"]) if cur_result else 0
                prev_units = int(prev_result[0]["qty"]) if prev_result else 0

                wow = {
                    "revenue_change": round((cur_rev - prev_rev) / prev_rev * 100, 1) if prev_rev > 0 else 0,
                    "units_change": round((cur_units - prev_units) / prev_units * 100, 1) if prev_units > 0 else 0,
                    "current_revenue": cur_rev,
                    "previous_revenue": prev_rev,
                    "current_units": cur_units,
                    "previous_units": prev_units,
                }
        except Exception as e:
            logger.warning(f"WoW calculation error: {e}")

    # ── YoY ──
    yoy = {"revenue_change": 0, "current_revenue": total_revenue, "previous_revenue": 0}
    if min_day and max_day:
        try:
            max_dt = datetime.fromisoformat(max_day) if isinstance(max_day, str) else max_day
            min_dt = datetime.fromisoformat(min_day) if isinstance(min_day, str) else min_day
            yoy_start = (min_dt.replace(year=min_dt.year - 1)).isoformat()
            yoy_end = (max_dt.replace(year=max_dt.year - 1)).isoformat()

            yoy_match = {**_tenant_match(_has_tid, tenant_id), "day": {"$gte": yoy_start, "$lte": yoy_end}}
            yoy_match.update(extra)
            yoy_pipeline = [
                {"$match": yoy_match},
                {"$addFields": {"rev": {"$toDouble": {"$ifNull": ["$revenue", 0]}}}},
                {"$group": {"_id": None, "rev": {"$sum": "$rev"}}},
            ]
            yoy_result = await tdb.daily_sales.aggregate(yoy_pipeline).to_list(1)
            if yoy_result:
                prev_year_rev = float(yoy_result[0]["rev"])
                if prev_year_rev > 0:
                    yoy = {
                        "revenue_change": round((total_revenue - prev_year_rev) / prev_year_rev * 100, 1),
                        "current_revenue": total_revenue,
                        "previous_revenue": prev_year_rev,
                    }
        except Exception as e:
            logger.warning(f"YoY calculation error: {e}")

    return {
        "revenue": total_revenue,
        "units_sold": total_units,
        "margin_pct": margin_pct,
        "mrp_realisation_pct": mrp_realisation,
        "total_cogs": total_cogs,
        "margin_source": "cogs" if true_margin_pct is not None else "mrp_realisation",
        "wow": wow,
        "yoy": yoy,
        "has_data": True,
    }


# ═══════════════════════════════════════════════════════════
# EXECUTIVE REVENUE TREND — MongoDB Aggregation
# ═══════════════════════════════════════════════════════════

async def agg_revenue_trend(
    tdb: AsyncIOMotorDatabase,
    tenant_id: str,
    start_date: str = None,
    end_date: str = None,
    categories: List[str] = None,
    channels: List[str] = None,
    regions: List[str] = None,
) -> dict:
    """Daily revenue & units timeseries via MongoDB aggregation."""
    _has_tid = await _has_tenant_id(tdb, "daily_sales")

    extra = await _resolve_filter_skus(tdb, tenant_id, categories, channels, regions)

    match = _tenant_match(_has_tid, tenant_id)
    if start_date:
        match["day"] = match.get("day", {})
        match["day"]["$gte"] = start_date
    if end_date:
        match.setdefault("day", {})["$lte"] = end_date
    match.update(extra)

    pipeline = [
        {"$match": match},
        {"$addFields": {
            "rev_num": {"$toDouble": {"$ifNull": ["$revenue", 0]}},
            "qty_num": {"$toInt": {"$ifNull": ["$quantity", 0]}},
            "day_str": {"$substr": ["$day", 0, 10]},
        }},
        {"$group": {
            "_id": "$day_str",
            "revenue": {"$sum": "$rev_num"},
            "units": {"$sum": "$qty_num"},
        }},
        {"$sort": {"_id": 1}},
    ]

    results = await tdb.daily_sales.aggregate(pipeline).to_list(1000)

    if not results:
        return {"labels": [], "revenue": [], "units": []}

    labels = [r["_id"] for r in results]
    revenue = [round(float(r["revenue"]), 2) for r in results]
    units = [int(r["units"]) for r in results]

    return {"labels": labels, "revenue": revenue, "units": units}


# ═══════════════════════════════════════════════════════════
# GAP ANALYSIS (ROS) — MongoDB Aggregation
# ═══════════════════════════════════════════════════════════

async def agg_ros_gap_analysis(
    tdb: AsyncIOMotorDatabase,
    tenant_id: str,
    start_date: str = None,
    end_date: str = None,
    categories: List[str] = None,
    channels: List[str] = None,
    regions: List[str] = None,
) -> dict:
    """
    ROS Gap Analysis via MongoDB aggregation.
    Computes per-style, per-size ROS and identifies broken size sets.
    """
    _has_tid = await _has_tenant_id(tdb, "daily_sales")
    extra = await _resolve_filter_skus(tdb, tenant_id, categories, channels, regions)

    # Step 1: Aggregate sales by SKU
    match = _tenant_match(_has_tid, tenant_id)
    if start_date:
        match["day"] = match.get("day", {})
        match["day"]["$gte"] = start_date
    if end_date:
        match.setdefault("day", {})["$lte"] = end_date
    match.update(extra)

    sales_pipeline = [
        {"$match": match},
        {"$addFields": {
            "qty": {"$toDouble": {"$ifNull": ["$quantity", 0]}},
            "rev": {"$toDouble": {"$ifNull": ["$revenue", 0]}},
        }},
        {"$group": {
            "_id": "$sku",
            "total_qty": {"$sum": "$qty"},
            "total_revenue": {"$sum": "$rev"},
            "days_sold": {"$addToSet": {"$substr": ["$day", 0, 10]}},
        }},
    ]

    sales_by_sku = {}
    async for doc in tdb.daily_sales.aggregate(sales_pipeline):
        sales_by_sku[doc["_id"]] = {
            "total_qty": doc["total_qty"],
            "total_revenue": doc["total_revenue"],
            "days_sold": len(doc["days_sold"]),
        }

    if not sales_by_sku:
        return {"error": None, "data": [], "summary": {
            "total_styles": 0, "healthy_styles": 0, "broken_styles": 0,
            "noos_styles": 0, "avg_ros_gap": 0, "total_sales_loss": 0,
            "healthy_coverage_pct": 0,
        }}

    # Step 2: Get SKU→style/size mapping
    sku_map = {}
    async for doc in tdb.sku_master.find(
        _tenant_match(_has_tid, tenant_id), {"_id": 0, "ean": 1, "style": 1, "size": 1}
    ):
        sku_map[doc.get("ean")] = {"style": doc.get("style"), "size": doc.get("size")}

    # Step 3: Get style→category mapping
    style_cats = {}
    async for doc in tdb.style_master.find(
        _tenant_match(_has_tid, tenant_id), {"_id": 0, "style_code": 1, "category": 1}
    ):
        style_cats[doc.get("style_code")] = doc.get("category", "Unknown")

    # Step 4: Build style-level aggregation
    style_data = {}  # style -> {sizes: {size: {qty, revenue, days}}}

    for sku, sales in sales_by_sku.items():
        info = sku_map.get(sku, {})
        style = info.get("style", sku)
        size = info.get("size", "Unknown")

        if style not in style_data:
            style_data[style] = {"sizes": {}, "category": style_cats.get(style, "Unknown")}

        if size not in style_data[style]["sizes"]:
            style_data[style]["sizes"][size] = {"qty": 0, "revenue": 0, "days": 0}

        style_data[style]["sizes"][size]["qty"] += sales["total_qty"]
        style_data[style]["sizes"][size]["revenue"] += sales["total_revenue"]
        style_data[style]["sizes"][size]["days"] = max(style_data[style]["sizes"][size]["days"], sales["days_sold"])

    # Step 5: Compute ROS per size and gap metrics
    analysis_data = []
    total_healthy = 0
    total_broken = 0
    total_noos = 0
    total_sales_loss = 0

    for style, data in style_data.items():
        sizes = data["sizes"]
        if not sizes:
            continue

        # Compute ROS (rate of sale) per size
        ros_values = {}
        for size, metrics in sizes.items():
            days = max(metrics["days"], 1)
            ros = metrics["qty"] / days
            ros_values[size] = ros

        if not ros_values:
            continue

        avg_ros = sum(ros_values.values()) / len(ros_values)
        max_ros = max(ros_values.values())

        # Classify: healthy if all sizes within 50% of max, broken if any below
        broken_sizes = []
        for size, ros in ros_values.items():
            if max_ros > 0 and ros < max_ros * 0.5:
                broken_sizes.append(size)

        if len(broken_sizes) == len(sizes):
            status = "noos"
            total_noos += 1
        elif broken_sizes:
            status = "broken"
            total_broken += 1
            # Estimate sales loss: (max_ros - actual_ros) * days for each broken size
            for size in broken_sizes:
                loss = (max_ros - ros_values[size]) * max(sizes[size]["days"], 1)
                total_sales_loss += loss
        else:
            status = "healthy"
            total_healthy += 1

        total_revenue_style = sum(m["revenue"] for m in sizes.values())
        total_qty_style = sum(m["qty"] for m in sizes.values())

        analysis_data.append({
            "style": style,
            "category": data["category"],
            "status": status,
            "size_count": len(sizes),
            "broken_sizes": len(broken_sizes),
            "avg_ros": round(avg_ros, 2),
            "max_ros": round(max_ros, 2),
            "total_qty": int(total_qty_style),
            "total_revenue": round(total_revenue_style, 2),
            "sizes": {s: round(r, 2) for s, r in ros_values.items()},
        })

    total_styles = len(analysis_data)
    healthy_pct = round(total_healthy / max(total_styles, 1) * 100, 1)

    return {
        "error": None,
        "data": sorted(analysis_data, key=lambda x: x["total_revenue"], reverse=True)[:200],
        "summary": {
            "total_styles": total_styles,
            "healthy_styles": total_healthy,
            "broken_styles": total_broken,
            "noos_styles": total_noos,
            "avg_ros_gap": round(total_sales_loss / max(total_broken, 1), 1) if total_broken > 0 else 0,
            "total_sales_loss": round(total_sales_loss, 0),
            "healthy_coverage_pct": healthy_pct,
        },
    }



# ═══════════════════════════════════════════════════════════
# DOH (Days on Hand) — MongoDB Aggregation
# ═══════════════════════════════════════════════════════════

async def agg_doh_analysis(
    tdb: AsyncIOMotorDatabase,
    tenant_id: str,
    start_date: str = None,
    end_date: str = None,
    categories: List[str] = None,
    channels: List[str] = None,
    regions: List[str] = None,
    ideal_doh: int = 9,
) -> dict:
    """DOH analysis via MongoDB aggregation."""
    _has_tid = await _has_tenant_id(tdb, "daily_sales")

    extra = await _resolve_filter_skus(tdb, tenant_id, categories, channels, regions)

    # Build match for sales
    sales_match = _tenant_match(_has_tid, tenant_id)
    if start_date:
        sales_match["day"] = sales_match.get("day", {})
        sales_match["day"]["$gte"] = start_date
    if end_date:
        sales_match.setdefault("day", {})["$lte"] = end_date
    sales_match.update(extra)

    # Inventory match — separate (no SKU/channel filters, only tenant + date)
    _inv_has_tid = await _has_tenant_id(tdb, "store_inventory")
    inv_base_match = _tenant_match(_inv_has_tid, tenant_id)

    # 1. ROS per store-SKU
    ros_pipeline = [        {"$match": sales_match},
        {"$addFields": {"qty": {"$toDouble": {"$ifNull": ["$quantity", 0]}},
                        "rev": {"$toDouble": {"$ifNull": ["$revenue", 0]}}}},
        {"$group": {
            "_id": {"store": "$store_code", "sku": "$sku"},
            "total_qty": {"$sum": "$qty"},
            "total_revenue": {"$sum": "$rev"},
            "days": {"$addToSet": {"$substr": ["$day", 0, 10]}},
        }},
        {"$addFields": {"live_days": {"$size": "$days"}}},
        {"$project": {"days": 0}},
    ]
    ros_data = {}
    async for doc in tdb.daily_sales.aggregate(ros_pipeline):
        key = (doc["_id"]["store"], doc["_id"]["sku"])
        live = max(doc["live_days"], 1)
        ros_data[key] = {
            "qty": doc["total_qty"], "rev": doc["total_revenue"],
            "live_days": live, "ros": round(doc["total_qty"] / live, 4),
        }

    # 2. Latest SOH — find max date in inventory then aggregate
    inv_dates_pipeline = [
        {"$match": inv_base_match},
        {"$group": {"_id": None, "max_day": {"$max": "$day"}}},
    ]
    date_result = await tdb.store_inventory.aggregate(inv_dates_pipeline).to_list(1)
    latest_day = date_result[0]["max_day"] if date_result else None

    soh_data = {}
    if latest_day:
        soh_match = {**inv_base_match, "day": latest_day}
        soh_pipeline = [
            {"$match": soh_match},
            {"$addFields": {"qty": {"$toDouble": {"$ifNull": ["$quantity", {"$ifNull": ["$closing_stock", 0]}]}}}},
            {"$group": {"_id": {"store": "$store_code", "sku": {"$ifNull": ["$ean", "$sku"]}}, "soh": {"$sum": "$qty"}}},
        ]
        async for doc in tdb.store_inventory.aggregate(soh_pipeline):
            soh_data[(doc["_id"]["store"], doc["_id"]["sku"])] = doc["soh"]

    if not ros_data and not soh_data:
        return {"error": "No sales or inventory data", "data": {}}

    # 3. Compute DOH per store-SKU
    all_keys = set(ros_data.keys()) | set(soh_data.keys())
    upper = ideal_doh * 1.2
    lower = ideal_doh * 0.8

    status_counts = {"OPTIMAL": 0, "OVERSTOCKED": 0, "UNDERSTOCKED": 0, "STOCKED_OUT": 0, "NO_SALES": 0}
    store_metrics = {}  # store -> {weighted_doh, soh, skus, statuses}
    detail_items = []

    for (store, sku) in all_keys:
        ros_info = ros_data.get((store, sku), {"qty": 0, "rev": 0, "ros": 0, "live_days": 0})
        soh = soh_data.get((store, sku), 0)
        ros = ros_info["ros"]

        if ros > 0:
            doh = round(soh / ros, 1)
        elif soh > 0:
            doh = 9999
        else:
            doh = 0

        # Classify
        if soh == 0 and ros > 0:
            status = "STOCKED_OUT"
        elif ros == 0 and soh > 0:
            status = "NO_SALES"
        elif ros == 0 and soh == 0:
            status = "STOCKED_OUT"
        elif doh > upper:
            status = "OVERSTOCKED"
        elif doh < lower:
            status = "UNDERSTOCKED"
        else:
            status = "OPTIMAL"

        status_counts[status] = status_counts.get(status, 0) + 1

        # Aggregate per store
        if store not in store_metrics:
            store_metrics[store] = {"soh": 0, "weighted_doh": 0, "skus": set(), "statuses": {}}
        if ros > 0 and soh > 0:
            store_metrics[store]["soh"] += soh
            store_metrics[store]["weighted_doh"] += doh * soh
        store_metrics[store]["skus"].add(sku)
        store_metrics[store]["statuses"][status] = store_metrics[store]["statuses"].get(status, 0) + 1

        if ros > 0:
            detail_items.append({
                "store_code": store, "sku": sku, "style": "Unknown",
                "soh": soh, "ros": ros, "doh": doh, "status": status, "ideal_doh": ideal_doh,
            })

    # 4. Store-level aggregation
    store_data = []
    for store, m in store_metrics.items():
        store_doh = round(m["weighted_doh"] / max(m["soh"], 1), 1) if m["soh"] > 0 else 0
        dominant = max(m["statuses"], key=m["statuses"].get) if m["statuses"] else "OPTIMAL"
        store_data.append({
            "store_code": store, "total_inventory": m["soh"],
            "doh": store_doh, "sku_count": len(m["skus"]), "status": dominant,
            "OPTIMAL": m["statuses"].get("OPTIMAL", 0),
            "OVERSTOCKED": m["statuses"].get("OVERSTOCKED", 0),
            "UNDERSTOCKED": m["statuses"].get("UNDERSTOCKED", 0),
            "STOCKED_OUT": m["statuses"].get("STOCKED_OUT", 0),
            "ideal_doh": ideal_doh,
        })
    store_data.sort(key=lambda x: x["doh"])

    # 5. Overall metrics
    total_items = len(all_keys)
    total_soh = sum(soh_data.values())
    total_weighted = sum(m["weighted_doh"] for m in store_metrics.values())
    overall_doh = round(total_weighted / max(total_soh, 1), 1)

    # 6. Recommendations
    recs = []
    so_stores = sum(1 for s in store_data if s["status"] == "STOCKED_OUT")
    us_stores = sum(1 for s in store_data if s["status"] == "UNDERSTOCKED")
    os_stores = sum(1 for s in store_data if s["status"] == "OVERSTOCKED")
    if so_stores > 0:
        recs.append({"priority": "high", "title": "Stock-out detected",
                      "description": f"{so_stores} stores have critical stock-outs."})
    if us_stores > 0:
        recs.append({"priority": "high", "title": f"DOH below {lower:.0f} days",
                      "description": f"{us_stores} stores understocked."})
    if os_stores > 0:
        recs.append({"priority": "medium", "title": f"DOH above {upper:.0f} days",
                      "description": f"{os_stores} stores overstocked."})

    detail_items.sort(key=lambda x: x["doh"])

    return {
        "summary": {
            "overall_doh": overall_doh, "ideal_doh": ideal_doh,
            "total_store_skus": total_items,
            "optimal_count": status_counts.get("OPTIMAL", 0),
            "overstocked_count": status_counts.get("OVERSTOCKED", 0),
            "understocked_count": status_counts.get("UNDERSTOCKED", 0),
            "stockedout_count": status_counts.get("STOCKED_OUT", 0),
            "no_sales_count": status_counts.get("NO_SALES", 0),
            "snapshot_date": str(latest_day)[:10] if latest_day else None,
        },
        "store_data": store_data[:100],
        "category_data": [],
        "trend_data": [],
        "detail": detail_items[:200],
        "recommendations": recs,
        "data_source": "mongodb_aggregation",
    }


# ═══════════════════════════════════════════════════════════
# STOCK-OUT ANALYSIS — MongoDB Aggregation
# ═══════════════════════════════════════════════════════════

async def agg_stock_out(
    tdb: AsyncIOMotorDatabase,
    tenant_id: str,
    start_date: str = None,
    end_date: str = None,
    categories: List[str] = None,
    channels: List[str] = None,
    regions: List[str] = None,
) -> dict:
    """Stock-out analysis via MongoDB aggregation — full response for frontend."""
    _has_tid = await _has_tenant_id(tdb, "daily_sales")

    extra = await _resolve_filter_skus(tdb, tenant_id, categories, channels, regions)
    match = _tenant_match(_has_tid, tenant_id)
    if start_date:
        match["day"] = match.get("day", {})
        match["day"]["$gte"] = start_date
    if end_date:
        match.setdefault("day", {})["$lte"] = end_date
    match.update(extra)

    # 1. ROS per store-SKU
    ros_pipeline = [
        {"$match": match},
        {"$addFields": {"qty": {"$toDouble": {"$ifNull": ["$quantity", 0]}},
                        "rev": {"$toDouble": {"$ifNull": ["$revenue", 0]}}}},
        {"$group": {
            "_id": {"store": "$store_code", "sku": "$sku"},
            "total_qty": {"$sum": "$qty"},
            "total_revenue": {"$sum": "$rev"},
            "days": {"$addToSet": {"$substr": ["$day", 0, 10]}},
        }},
        {"$addFields": {"live_days": {"$size": "$days"}}},
    ]
    ros_map = {}
    async for doc in tdb.daily_sales.aggregate(ros_pipeline):
        key = (doc["_id"]["store"], doc["_id"]["sku"])
        live = max(doc["live_days"], 1)
        ros_map[key] = {
            "ros": round(doc["total_qty"] / live, 3),
            "asp": round(doc["total_revenue"] / max(doc["total_qty"], 1), 2),
            "total_qty": doc["total_qty"],
        }

    # 2. Latest SOH — ALL items (for stockout + high-risk detection)
    _inv_has_tid = await _has_tenant_id(tdb, "store_inventory")
    inv_dates = await tdb.store_inventory.aggregate([
        {"$match": _tenant_match(_inv_has_tid, tenant_id)},
        {"$group": {"_id": None, "max_day": {"$max": "$day"}}},
    ]).to_list(1)
    latest_day = inv_dates[0]["max_day"] if inv_dates else None

    all_soh = {}
    zero_stock = set()
    if latest_day:
        async for doc in tdb.store_inventory.find(
            {**_tenant_match(_inv_has_tid, tenant_id), "day": latest_day},
            {"_id": 0, "store_code": 1, "ean": 1, "sku": 1, "quantity": 1, "closing_stock": 1},
        ):
            qty = doc.get("quantity", doc.get("closing_stock", 0))
            try:
                qty = float(qty)
            except (ValueError, TypeError):
                qty = 0
            sku_val = doc.get("ean", doc.get("sku", ""))
            store_val = doc.get("store_code", "")
            all_soh[(store_val, sku_val)] = qty
            if qty == 0:
                zero_stock.add((store_val, sku_val))

    # 3. SKU -> style mapping
    _sk_tid = await _has_tenant_id(tdb, "sku_master")
    sku_style = {}
    async for doc in tdb.sku_master.find(
        _tenant_match(_sk_tid, tenant_id), {"_id": 0, "ean": 1, "style": 1}
    ):
        if doc.get("ean"):
            sku_style[doc["ean"]] = doc.get("style", "")

    # 4. Style -> category mapping
    _sm_tid = await _has_tenant_id(tdb, "style_master")
    style_cat = {}
    async for doc in tdb.style_master.find(
        _tenant_match(_sm_tid, tenant_id), {"_id": 0, "style_code": 1, "category": 1}
    ):
        if doc.get("style_code"):
            style_cat[doc["style_code"]] = doc.get("category", "Unknown")

    # 5. Stock-outs = zero stock AND positive ROS
    stockout_items = []
    total_daily_loss = 0
    for key in zero_stock:
        if key in ros_map:
            info = ros_map[key]
            daily_loss = round(info["ros"] * info["asp"], 2)
            total_daily_loss += daily_loss
            stockout_items.append({
                "store_code": key[0], "sku": key[1],
                "ros": info["ros"], "asp": info["asp"],
                "daily_sales_loss": daily_loss,
                "severity": "HIGH" if daily_loss > 1000 else "MEDIUM" if daily_loss > 100 else "LOW",
            })
    stockout_items.sort(key=lambda x: x["daily_sales_loss"], reverse=True)

    total_skus_tracked = len(ros_map)
    stockout_rate = round(len(stockout_items) / max(total_skus_tracked, 1) * 100, 1)
    stores_impacted = len(set(item["store_code"] for item in stockout_items))

    # ── Aggregated views ──

    # top_skus: group by sku
    _sku_agg = {}
    for item in stockout_items:
        sk = item["sku"]
        if sk not in _sku_agg:
            _sku_agg[sk] = {"cnt": 0, "ros_s": 0, "asp_s": 0, "loss_s": 0}
        _sku_agg[sk]["cnt"] += 1
        _sku_agg[sk]["ros_s"] += item["ros"]
        _sku_agg[sk]["asp_s"] += item["asp"]
        _sku_agg[sk]["loss_s"] += item["daily_sales_loss"]

    top_skus = []
    for sk, v in _sku_agg.items():
        c = v["cnt"]
        top_skus.append({
            "sku": sk, "style": sku_style.get(sk, ""),
            "stockout_count": c,
            "avg_ros": round(v["ros_s"] / c, 1),
            "avg_asp": round(v["asp_s"] / c, 2),
            "total_daily_loss": round(v["loss_s"], 2),
        })
    top_skus.sort(key=lambda x: x["total_daily_loss"], reverse=True)

    # top_stores: group by store_code
    _store_agg = {}
    for item in stockout_items:
        st = item["store_code"]
        if st not in _store_agg:
            _store_agg[st] = {"cnt": 0, "loss": 0}
        _store_agg[st]["cnt"] += 1
        _store_agg[st]["loss"] += item["daily_sales_loss"]

    top_stores = []
    for st, v in _store_agg.items():
        top_stores.append({
            "store_code": st, "stockout_count": v["cnt"],
            "avg_duration": 1, "total_daily_loss": round(v["loss"], 2),
            "total_severity": round(v["loss"], 2),
        })
    top_stores.sort(key=lambda x: x["total_severity"], reverse=True)

    # category_impact: group by category
    _cat_agg = {}
    for item in stockout_items:
        style = sku_style.get(item["sku"], "")
        cat = style_cat.get(style, "Unknown")
        if cat not in _cat_agg:
            _cat_agg[cat] = {"loss": 0, "cnt": 0}
        _cat_agg[cat]["loss"] += item["daily_sales_loss"]
        _cat_agg[cat]["cnt"] += 1
    category_impact = sorted(
        [{"category": k, "total_daily_loss": round(v["loss"], 2), "count": v["cnt"]} for k, v in _cat_agg.items()],
        key=lambda x: x["total_daily_loss"], reverse=True,
    )

    # store_heatmap: total skus per store vs stockout skus
    _store_total = {}
    for (st, _sk) in ros_map:
        _store_total[st] = _store_total.get(st, 0) + 1
    _store_so = {}
    _store_loss = {}
    for item in stockout_items:
        st = item["store_code"]
        _store_so[st] = _store_so.get(st, 0) + 1
        _store_loss[st] = _store_loss.get(st, 0) + item["daily_sales_loss"]

    store_heatmap = []
    for st in set(list(_store_total.keys()) + list(_store_so.keys())):
        total = _store_total.get(st, 0)
        sos = _store_so.get(st, 0)
        pct = round(sos / max(total, 1) * 100, 1)
        loss = round(_store_loss.get(st, 0), 2)
        sev = "critical" if pct >= 50 else "high" if pct >= 25 else "medium" if pct >= 10 else "low"
        store_heatmap.append({"store_code": st, "total": total, "stockouts": sos,
                              "stockout_pct": pct, "total_loss": loss, "severity": sev})
    store_heatmap.sort(key=lambda x: x["stockout_pct"], reverse=True)

    # category_heatmap
    _cat_total = {}
    _cat_so = {}
    _cat_loss2 = {}
    for (st, sk) in ros_map:
        style = sku_style.get(sk, "")
        cat = style_cat.get(style, "Unknown")
        _cat_total[cat] = _cat_total.get(cat, 0) + 1
    for item in stockout_items:
        style = sku_style.get(item["sku"], "")
        cat = style_cat.get(style, "Unknown")
        _cat_so[cat] = _cat_so.get(cat, 0) + 1
        _cat_loss2[cat] = _cat_loss2.get(cat, 0) + item["daily_sales_loss"]

    category_heatmap = []
    for cat in set(list(_cat_total.keys()) + list(_cat_so.keys())):
        total = _cat_total.get(cat, 0)
        sos = _cat_so.get(cat, 0)
        pct = round(sos / max(total, 1) * 100, 1)
        loss = round(_cat_loss2.get(cat, 0), 2)
        sev = "critical" if pct >= 50 else "high" if pct >= 25 else "medium" if pct >= 10 else "low"
        category_heatmap.append({"category": cat, "total": total, "stockouts": sos,
                                 "stockout_pct": pct, "total_loss": loss, "severity": sev})
    category_heatmap.sort(key=lambda x: x["stockout_pct"], reverse=True)

    # high_risk_skus: SOH > 0 but days_to_stockout <= 7
    high_risk = []
    for key, info in ros_map.items():
        soh = all_soh.get(key, 0)
        if soh > 0 and info["ros"] > 0:
            dts = round(soh / info["ros"], 1)
            if dts <= 7:
                risk = "critical" if dts <= 2 else "high" if dts <= 4 else "medium"
                high_risk.append({
                    "sku": key[1], "style": sku_style.get(key[1], ""),
                    "store_code": key[0], "ros": info["ros"],
                    "soh": soh, "asp": info["asp"],
                    "days_to_stockout": dts, "risk": risk,
                })
    high_risk.sort(key=lambda x: x["days_to_stockout"])

    # reorder_recommendations
    lead_time, safety_days = 14, 7
    reorder_recs = []
    for item in stockout_items[:50]:
        qty = round(item["ros"] * (lead_time + safety_days), 0)
        reorder_recs.append({
            "sku": item["sku"], "style": sku_style.get(item["sku"], ""),
            "store_code": item["store_code"], "ros": item["ros"],
            "soh": 0, "days_to_stockout": 0, "reorder_qty": qty,
        })
    for item in high_risk[:50]:
        qty = max(0, round(item["ros"] * (lead_time + safety_days) - item["soh"], 0))
        if qty > 0:
            reorder_recs.append({
                "sku": item["sku"], "style": item["style"],
                "store_code": item["store_code"], "ros": item["ros"],
                "soh": item["soh"], "days_to_stockout": item["days_to_stockout"],
                "reorder_qty": qty,
            })
    reorder_recs.sort(key=lambda x: x["days_to_stockout"])

    # alternative_suggestions: same-style SKUs with stock at same store
    _store_style_inv = {}
    for (st, sk), soh in all_soh.items():
        if soh > 0:
            style = sku_style.get(sk, "")
            if style:
                _store_style_inv.setdefault((st, style), []).append(
                    {"sku": sk, "soh": soh, "ros": ros_map.get((st, sk), {}).get("ros", 0)})

    alternatives = []
    for item in stockout_items[:20]:
        style = sku_style.get(item["sku"], "")
        if not style:
            continue
        alts = [a for a in _store_style_inv.get((item["store_code"], style), [])
                if a["sku"] != item["sku"]]
        if alts:
            alternatives.append({
                "stockout_sku": item["sku"], "store_code": item["store_code"],
                "alternatives": sorted(alts, key=lambda x: x["soh"], reverse=True)[:5],
            })

    # ── Daily / Weekly / Monthly trends ──
    # Aggregate stockout counts per inventory day
    daily_trend = []
    weekly_trend = []
    monthly_trend = []
    moving_avg = []

    # Get all inventory days (filter out empty/null dates)
    inv_days_pipeline = [
        {"$match": {**_tenant_match(_inv_has_tid, tenant_id), "day": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {"_id": {"$substr": ["$day", 0, 10]}}},
        {"$match": {"_id": {"$ne": "", "$ne": None}}},
        {"$sort": {"_id": 1}},
    ]
    inv_days = [d["_id"] async for d in tdb.store_inventory.aggregate(inv_days_pipeline)]

    if len(inv_days) > 1:
        # For each day, count zero-stock items that have positive ROS
        for day_str in inv_days[-90:]:
            day_zero = set()
            async for doc in tdb.store_inventory.find(
                {**_tenant_match(_inv_has_tid, tenant_id), "day": day_str},
                {"_id": 0, "store_code": 1, "ean": 1, "sku": 1, "quantity": 1, "closing_stock": 1},
            ):
                qty = doc.get("quantity", doc.get("closing_stock", 0))
                try:
                    qty = float(qty)
                except (ValueError, TypeError):
                    qty = 0
                if qty == 0:
                    sku_val = doc.get("ean", doc.get("sku", ""))
                    day_zero.add((doc.get("store_code", ""), sku_val))

            so_count = sum(1 for k in day_zero if k in ros_map)
            so_loss = sum(ros_map[k]["ros"] * ros_map[k]["asp"] for k in day_zero if k in ros_map)
            daily_trend.append({
                "date": day_str, "stockout_count": so_count,
                "lost_sales": round(so_loss, 2),
            })

        # Moving average (7-day)
        for i, d in enumerate(daily_trend):
            window = daily_trend[max(0, i - 6):i + 1]
            ma7 = round(sum(w["stockout_count"] for w in window) / len(window), 1)
            moving_avg.append({"date": d["date"], "ma7": ma7})

        # Weekly rollup
        week_agg = {}
        for d in daily_trend:
            try:
                from datetime import datetime as _dt
                dt = _dt.fromisoformat(d["date"])
                wk = dt.isocalendar()[1]
                yr = dt.year
                key = f"{yr}-W{wk:02d}"
                if key not in week_agg:
                    week_agg[key] = {"cnt": 0, "loss": 0, "days": 0, "rate": 0}
                week_agg[key]["cnt"] += d["stockout_count"]
                week_agg[key]["loss"] += d["lost_sales"]
                week_agg[key]["days"] += 1
            except Exception:
                pass
        for wk in sorted(week_agg.keys()):
            v = week_agg[wk]
            weekly_trend.append({
                "week": wk, "stockout_count": v["cnt"],
                "stockout_rate": round(v["cnt"] / max(total_skus_tracked * v["days"], 1) * 100, 1),
            })

        # Monthly rollup
        month_agg = {}
        for d in daily_trend:
            m = d["date"][:7]
            if m not in month_agg:
                month_agg[m] = {"cnt": 0, "loss": 0, "days": 0}
            month_agg[m]["cnt"] += d["stockout_count"]
            month_agg[m]["loss"] += d["lost_sales"]
            month_agg[m]["days"] += 1
        for m in sorted(month_agg.keys()):
            v = month_agg[m]
            monthly_trend.append({
                "month": m, "stockout_count": v["cnt"],
                "stockout_rate": round(v["cnt"] / max(total_skus_tracked * v["days"], 1) * 100, 1),
            })

    return {
        "summary": {
            "total_stockouts": len(stockout_items),
            "stockout_rate": stockout_rate,
            "total_lost_sales": round(total_daily_loss, 0),
            "total_store_skus": total_skus_tracked,
            "stores_impacted": stores_impacted,
            "snapshot_date": str(latest_day)[:10] if latest_day else None,
            "high_severity": sum(1 for s in stockout_items if s["severity"] == "HIGH"),
            "medium_severity": sum(1 for s in stockout_items if s["severity"] == "MEDIUM"),
            "low_severity": sum(1 for s in stockout_items if s["severity"] == "LOW"),
        },
        "top_skus": top_skus[:20],
        "top_stores": top_stores[:20],
        "category_impact": category_impact,
        "store_heatmap": store_heatmap[:100],
        "category_heatmap": category_heatmap[:50],
        "high_risk_skus": high_risk[:50],
        "reorder_recommendations": reorder_recs[:50],
        "alternative_suggestions": alternatives[:20],
        "daily_trend": daily_trend,
        "weekly_trend": weekly_trend,
        "monthly_trend": monthly_trend,
        "period_trends": {},
        "moving_avg": moving_avg,
        "projected_trend": [],
        "prev_period_trend": [],
        "data": stockout_items[:200],
        "data_source": "mongodb_aggregation",
    }


# ═══════════════════════════════════════════════════════════
# REPLENISHMENT PLAN — MongoDB Aggregation
# ═══════════════════════════════════════════════════════════

async def agg_replenishment(
    tdb: AsyncIOMotorDatabase,
    tenant_id: str,
    start_date: str = None,
    end_date: str = None,
    categories: List[str] = None,
    channels: List[str] = None,
    regions: List[str] = None,
    lead_time_days: int = 14,
    safety_days: int = 7,
    min_ros: float = 0.1,
) -> dict:
    """Replenishment plan via MongoDB aggregation."""
    _has_tid = await _has_tenant_id(tdb, "daily_sales")

    extra = await _resolve_filter_skus(tdb, tenant_id, categories, channels, regions)
    match = _tenant_match(_has_tid, tenant_id)
    if start_date:
        match["day"] = match.get("day", {})
        match["day"]["$gte"] = start_date
    if end_date:
        match.setdefault("day", {})["$lte"] = end_date
    match.update(extra)

    # 1. ROS per store-SKU
    ros_pipeline = [
        {"$match": match},
        {"$addFields": {"qty": {"$toDouble": {"$ifNull": ["$quantity", 0]}},
                        "rev": {"$toDouble": {"$ifNull": ["$revenue", 0]}}}},
        {"$group": {
            "_id": {"store": "$store_code", "sku": "$sku"},
            "total_qty": {"$sum": "$qty"},
            "total_revenue": {"$sum": "$rev"},
            "days": {"$addToSet": {"$substr": ["$day", 0, 10]}},
        }},
        {"$addFields": {"live_days": {"$size": "$days"}}},
    ]
    ros_map = {}
    async for doc in tdb.daily_sales.aggregate(ros_pipeline):
        key = (doc["_id"]["store"], doc["_id"]["sku"])
        live = max(doc["live_days"], 1)
        ros = round(doc["total_qty"] / live, 3)
        if ros >= min_ros:
            ros_map[key] = {
                "ros": ros,
                "asp": round(doc["total_revenue"] / max(doc["total_qty"], 1), 2),
                "total_qty": doc["total_qty"],
            }

    # 2. Current SOH
    _inv_has_tid = await _has_tenant_id(tdb, "store_inventory")
    inv_dates = await tdb.store_inventory.aggregate([
        {"$match": _tenant_match(_inv_has_tid, tenant_id)},
        {"$group": {"_id": None, "max_day": {"$max": "$day"}}},
    ]).to_list(1)
    latest_day = inv_dates[0]["max_day"] if inv_dates else None

    soh_map = {}
    if latest_day:
        async for doc in tdb.store_inventory.find(
            {**_tenant_match(_inv_has_tid, tenant_id), "day": latest_day},
            {"_id": 0, "store_code": 1, "ean": 1, "sku": 1, "quantity": 1, "closing_stock": 1},
        ):
            qty = doc.get("quantity", doc.get("closing_stock", 0))
            try:
                qty = float(qty)
            except (ValueError, TypeError):
                qty = 0
            sku_val = doc.get("ean", doc.get("sku", ""))
            soh_map[(doc.get("store_code", ""), sku_val)] = qty

    # 3. Compute reorder quantities
    items = []
    total_po_value = 0
    critical = 0
    for key, info in ros_map.items():
        ros = info["ros"]
        asp = info["asp"]
        soh = soh_map.get(key, 0)
        safety_stock = round(ros * safety_days, 0)
        reorder_qty = max(0, round((ros * lead_time_days) + safety_stock - soh, 0))

        if reorder_qty <= 0:
            continue

        po_value = round(reorder_qty * asp, 2)
        total_po_value += po_value

        projected_stockout_days = round(soh / ros, 1) if ros > 0 else 0
        urgency = "CRITICAL" if projected_stockout_days <= 3 else "HIGH" if projected_stockout_days <= 7 else "MEDIUM" if projected_stockout_days <= 14 else "LOW"
        if urgency == "CRITICAL":
            critical += 1

        items.append({
            "store_code": key[0], "sku": key[1],
            "ros": ros, "asp": asp, "current_soh": soh,
            "safety_stock": safety_stock, "reorder_qty": reorder_qty,
            "po_value": po_value, "projected_stockout_days": projected_stockout_days,
            "urgency": urgency,
        })

    items.sort(key=lambda x: x["projected_stockout_days"])

    return {
        "summary": {
            "total_items": len(items),
            "total_po_value": round(total_po_value, 0),
            "critical_items": critical,
            "lead_time_days": lead_time_days,
            "safety_days": safety_days,
        },
        "data": items[:200],
        "data_source": "mongodb_aggregation",
    }


# ═══════════════════════════════════════════════════════════
# BI DASHBOARD OVERVIEW — MongoDB Aggregation
# ═══════════════════════════════════════════════════════════

async def agg_bi_overview(
    tdb: AsyncIOMotorDatabase,
    tenant_id: str,
    start_date: str = None,
    end_date: str = None,
) -> dict:
    """BI Dashboard overview stats via MongoDB aggregation."""
    _has_tid = await _has_tenant_id(tdb, "daily_sales")
    match = _tenant_match(_has_tid, tenant_id)
    if start_date:
        match["day"] = match.get("day", {})
        match["day"]["$gte"] = start_date
    if end_date:
        match.setdefault("day", {})["$lte"] = end_date

    # Sales summary
    sales_pipeline = [
        {"$match": match},
        {"$addFields": {"rev": {"$toDouble": {"$ifNull": ["$revenue", 0]}},
                        "qty": {"$toInt": {"$ifNull": ["$quantity", 0]}}}},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$rev"},
            "total_units": {"$sum": "$qty"},
            "unique_skus": {"$addToSet": "$sku"},
            "unique_stores": {"$addToSet": "$store_code"},
            "unique_days": {"$addToSet": {"$substr": ["$day", 0, 10]}},
        }},
    ]
    sales_result = await tdb.daily_sales.aggregate(sales_pipeline).to_list(1)

    if not sales_result:
        return {"total_revenue": 0, "total_units": 0, "unique_skus": 0,
                "unique_stores": 0, "data_days": 0, "aov": 0, "has_data": False}

    s = sales_result[0]
    total_rev = float(s["total_revenue"])
    total_units = int(s["total_units"])
    unique_skus = len(s.get("unique_skus", []))
    unique_stores = len(s.get("unique_stores", []))
    data_days = len(s.get("unique_days", []))
    aov = round(total_rev / max(total_units, 1), 2)

    # Inventory summary
    inv_pipeline = [
        {"$match": _tenant_match(_has_tid, tenant_id)},
        {"$group": {"_id": None, "max_day": {"$max": "$day"}}},
    ]
    inv_date = await tdb.store_inventory.aggregate(inv_pipeline).to_list(1)
    total_inventory = 0
    if inv_date:
        inv_soh = await tdb.store_inventory.aggregate([
            {"$match": {**_tenant_match(_has_tid, tenant_id), "day": inv_date[0]["max_day"]}},
            {"$addFields": {"qty": {"$toDouble": {"$ifNull": ["$quantity", {"$ifNull": ["$closing_stock", 0]}]}}}},
            {"$group": {"_id": None, "total": {"$sum": "$qty"}}},
        ]).to_list(1)
        if inv_soh:
            total_inventory = int(inv_soh[0]["total"])

    return {
        "total_revenue": total_rev,
        "total_units": total_units,
        "unique_skus": unique_skus,
        "unique_stores": unique_stores,
        "data_days": data_days,
        "aov": aov,
        "total_inventory": total_inventory,
        "has_data": True,
    }
