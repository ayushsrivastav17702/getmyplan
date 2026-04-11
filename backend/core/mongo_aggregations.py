"""
MongoDB Aggregation Pipelines for Executive Dashboard and Gap Analysis.
Replaces in-memory Pandas operations with server-side aggregation for scalability.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


def _build_match_stage(
    tenant_id: str,
    start_date: str = None,
    end_date: str = None,
    date_field: str = "day",
    extra_match: dict = None,
) -> dict:
    """Build a $match stage with optional date range and extra filters."""
    match = {"tenant_id": tenant_id}
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            match[date_field] = date_filter
    if extra_match:
        match.update(extra_match)
    return {"$match": match}


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
    extra = {}

    if categories:
        # style_master → get style_codes → sku_master → get eans
        style_codes = set()
        async for doc in tdb.style_master.find(
            {"tenant_id": tenant_id, "category": {"$in": categories}},
            {"_id": 0, "style_code": 1},
        ):
            if doc.get("style_code"):
                style_codes.add(doc["style_code"])
        if style_codes:
            eans = set()
            async for doc in tdb.sku_master.find(
                {"tenant_id": tenant_id, "style": {"$in": list(style_codes)}},
                {"_id": 0, "ean": 1},
            ):
                if doc.get("ean"):
                    eans.add(doc["ean"])
            if eans:
                extra["sku"] = {"$in": list(eans)}

    if channels:
        extra["channel"] = {"$in": channels}

    if regions:
        store_codes = set()
        async for doc in tdb.store_master.find(
            {"tenant_id": tenant_id, "region": {"$in": regions}},
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

    extra = await _resolve_filter_skus(tdb, tenant_id, categories, channels, regions)

    # ── Total revenue & units ──
    match = {"tenant_id": tenant_id}
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
    cogs_match = {"tenant_id": tenant_id}
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

            yoy_match = {"tenant_id": tenant_id, "day": {"$gte": yoy_start, "$lte": yoy_end}}
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

    extra = await _resolve_filter_skus(tdb, tenant_id, categories, channels, regions)

    match = {"tenant_id": tenant_id}
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
    extra = await _resolve_filter_skus(tdb, tenant_id, categories, channels, regions)

    # Step 1: Aggregate sales by SKU
    match = {"tenant_id": tenant_id}
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
        {"tenant_id": tenant_id}, {"_id": 0, "ean": 1, "style": 1, "size": 1}
    ):
        sku_map[doc.get("ean")] = {"style": doc.get("style"), "size": doc.get("size")}

    # Step 3: Get style→category mapping
    style_cats = {}
    async for doc in tdb.style_master.find(
        {"tenant_id": tenant_id}, {"_id": 0, "style_code": 1, "category": 1}
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
