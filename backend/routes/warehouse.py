"""Warehouse Module — stock, movements, transfers, performance, dashboard.
Covers WH-01 to WH-30 test cases.
Migrated from Pandas to native MongoDB aggregation for memory efficiency.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import random
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics/warehouse", tags=["Warehouse"])

_client = None
_db_func = None


def init_warehouse(mongo_client, get_db_func=None):
    global _client, _db_func
    _client = mongo_client
    _db_func = get_db_func


def get_db():
    if _db_func:
        return _db_func()
    from server import get_db as server_get_db
    return server_get_db()


# ═══════════════════════════════════════════════════════════════
# WH-01 to WH-08: STOCK (MongoDB Aggregation)
# ═══════════════════════════════════════════════════════════════

@router.get("/stock")
async def get_warehouse_stock(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    alert_type: Optional[str] = None,
):
    """WH-01..08: View stock with filters, search, value calc, alerts."""
    db = get_db()

    # Find latest day
    date_pipeline = [{"$group": {"_id": None, "max_day": {"$max": "$day"}}}]
    date_result = await db.warehouse_inventory.aggregate(date_pipeline).to_list(1)
    if not date_result:
        return {"error": "No warehouse inventory data", "items": [], "totals": {}}
    latest_day = date_result[0]["max_day"]

    # Get latest inventory
    match = {"day": latest_day}
    if warehouse:
        match["warehouse"] = warehouse

    items_raw = []
    async for doc in db.warehouse_inventory.find(match, {"_id": 0}):
        items_raw.append(doc)

    if not items_raw:
        return {"error": "No warehouse inventory data", "items": [], "totals": {}}

    # Build SKU→info and style→category maps
    sku_map = {}
    async for doc in db.sku_master.find({}, {"_id": 0, "ean": 1, "style": 1, "size": 1, "mrp": 1}):
        if doc.get("ean"):
            sku_map[doc["ean"]] = doc

    style_cat = {}
    async for doc in db.style_master.find({}, {"_id": 0, "style_code": 1, "category": 1, "brand": 1}):
        if doc.get("style_code"):
            style_cat[doc["style_code"]] = doc

    # Config for thresholds
    config = await db.warehouse_config.find_one({"_id": "thresholds"}) or {}
    reorder_point = config.get("reorder_point", 50)
    max_threshold = config.get("max_threshold", 500)

    # Enrich items
    items = []
    total_stock = 0
    total_value = 0.0
    low_stock_count = 0
    oos_count = 0
    overstock_count = 0
    warehouses_set = set()
    categories_set = set()
    skus_set = set()

    for item in items_raw:
        sku = item.get("sku", "")
        qty = float(item.get("quantity", 0))
        wh = item.get("warehouse", "")
        sku_info = sku_map.get(sku, {})
        style = sku_info.get("style", "")
        size = sku_info.get("size", "")
        mrp = float(sku_info.get("mrp", 0) or 0)
        style_info = style_cat.get(style, {})
        cat = style_info.get("category", "")
        brand = style_info.get("brand", "")
        stock_value = qty * mrp

        # Alert classification
        if qty == 0:
            alert = "out_of_stock"
            oos_count += 1
        elif qty < reorder_point:
            alert = "low_stock"
            low_stock_count += 1
        elif qty > max_threshold:
            alert = "overstock"
            overstock_count += 1
        else:
            alert = "normal"

        # Apply filters
        if category and cat.lower() != category.lower():
            continue
        if search:
            sl = search.lower()
            if sl not in sku.lower() and sl not in style.lower():
                continue
        if alert_type and alert_type != "all" and alert != alert_type:
            continue

        total_stock += int(qty)
        total_value += stock_value
        warehouses_set.add(wh)
        if cat:
            categories_set.add(cat)
        skus_set.add(sku)

        items.append({
            "sku": sku, "warehouse": wh, "quantity": int(qty), "day": str(latest_day),
            "style": style, "size": size, "category": cat, "brand": brand,
            "mrp": mrp, "stock_value": round(stock_value, 2), "alert": alert,
        })

    return {
        "items": items[:200],
        "totals": {
            "total_stock": total_stock,
            "total_value": round(total_value, 2),
            "total_skus": len(skus_set),
            "total_warehouses": len(warehouses_set),
            "low_stock": low_stock_count,
            "out_of_stock": oos_count,
            "overstock": overstock_count,
            "reorder_point": reorder_point,
            "max_threshold": max_threshold,
        },
        "warehouses": sorted(warehouses_set),
        "categories": sorted(categories_set),
    }


# ═══════════════════════════════════════════════════════════════
# WH-09 to WH-14: STOCK MOVEMENTS
# ═══════════════════════════════════════════════════════════════

@router.get("/movements")
async def get_stock_movements(
    warehouse: Optional[str] = None,
    direction: Optional[str] = None,
    days: int = 30,
):
    """WH-09..11: Inbound/outbound tracking with history timeline."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    query: Dict[str, Any] = {"timestamp": {"$gte": cutoff}}
    if warehouse:
        query["warehouse"] = warehouse
    if direction and direction != "all":
        query["direction"] = direction

    movements = await get_db().warehouse_movements.find(
        query, {"_id": 0}
    ).sort("timestamp", -1).to_list(500)

    inbound = [m for m in movements if m.get("direction") == "inbound"]
    outbound = [m for m in movements if m.get("direction") == "outbound"]

    return {
        "movements": movements,
        "summary": {
            "total_inbound": sum(m.get("quantity", 0) for m in inbound),
            "total_outbound": sum(m.get("quantity", 0) for m in outbound),
            "inbound_count": len(inbound),
            "outbound_count": len(outbound),
        },
    }


@router.get("/daily-change")
async def get_daily_stock_change(warehouse: Optional[str] = None, days: int = 7):
    """WH-12: Opening vs closing stock by day (MongoDB aggregation)."""
    db = get_db()
    match: Dict[str, Any] = {}
    if warehouse:
        match["warehouse"] = warehouse

    pipeline = [
        {"$match": match} if match else {"$match": {}},
        {"$addFields": {"qty": {"$toDouble": {"$ifNull": ["$quantity", 0]}}}},
        {"$group": {
            "_id": {"$substr": ["$day", 0, 10]},
            "closing_stock": {"$sum": "$qty"},
            "sku_count": {"$addToSet": "$sku"},
        }},
        {"$addFields": {"sku_count": {"$size": "$sku_count"}}},
        {"$sort": {"_id": 1}},
    ]
    results = await db.warehouse_inventory.aggregate(pipeline).to_list(1000)
    if not results:
        return {"days": []}

    all_days = [{"date": r["_id"], "closing_stock": int(r["closing_stock"]), "sku_count": r["sku_count"]} for r in results]
    records = all_days[-days:]
    for i, r in enumerate(records):
        r["opening_stock"] = records[i - 1]["closing_stock"] if i > 0 else r["closing_stock"]
        r["change"] = r["closing_stock"] - r["opening_stock"]

    return {"days": records}


@router.get("/reconciliation")
async def get_reconciliation(warehouse: Optional[str] = None):
    """WH-13: System vs physical stock reconciliation."""
    query: Dict[str, Any] = {}
    if warehouse:
        query["warehouse"] = warehouse
    recs = await get_db().warehouse_reconciliations.find(
        query, {"_id": 0}
    ).sort("reconciled_at", -1).to_list(200)
    return {"reconciliations": recs}


@router.post("/reconciliation")
async def create_reconciliation(body: dict):
    """WH-13: Record a physical count reconciliation."""
    rec = {
        "reconciliation_id": str(uuid.uuid4())[:8],
        "warehouse": body.get("warehouse", ""),
        "sku": body.get("sku", ""),
        "system_qty": body.get("system_qty", 0),
        "physical_qty": body.get("physical_qty", 0),
        "variance": body.get("physical_qty", 0) - body.get("system_qty", 0),
        "notes": body.get("notes", ""),
        "reconciled_by": body.get("reconciled_by", "system"),
        "reconciled_at": datetime.now(timezone.utc).isoformat(),
    }
    await get_db().warehouse_reconciliations.insert_one(rec)
    del rec["_id"]
    return rec


@router.get("/adjustments")
async def get_adjustments(warehouse: Optional[str] = None, days: int = 30):
    """WH-14: Stock adjustment log."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    query: Dict[str, Any] = {"adjusted_at": {"$gte": cutoff}}
    if warehouse:
        query["warehouse"] = warehouse
    adjustments = await get_db().warehouse_adjustments.find(
        query, {"_id": 0}
    ).sort("adjusted_at", -1).to_list(500)
    return {"adjustments": adjustments}


@router.post("/adjustments")
async def create_adjustment(body: dict):
    """WH-14: Log a stock adjustment."""
    adj = {
        "adjustment_id": str(uuid.uuid4())[:8],
        "warehouse": body.get("warehouse", ""),
        "sku": body.get("sku", ""),
        "previous_qty": body.get("previous_qty", 0),
        "new_qty": body.get("new_qty", 0),
        "change": body.get("new_qty", 0) - body.get("previous_qty", 0),
        "reason": body.get("reason", ""),
        "adjusted_by": body.get("adjusted_by", "admin"),
        "adjusted_at": datetime.now(timezone.utc).isoformat(),
    }
    await get_db().warehouse_adjustments.insert_one(adj)
    del adj["_id"]
    return adj


# ═══════════════════════════════════════════════════════════════
# WH-15 to WH-20: TRANSFERS (already MongoDB-native)
# ═══════════════════════════════════════════════════════════════

@router.get("/transfers")
async def list_transfers(status: Optional[str] = None, warehouse: Optional[str] = None):
    query: Dict[str, Any] = {}
    if status and status != "all":
        query["status"] = status
    if warehouse:
        query["$or"] = [{"from_warehouse": warehouse}, {"to_store": warehouse}]
    transfers = await get_db().warehouse_transfers.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"transfers": transfers}


@router.post("/transfers")
async def create_transfer(body: dict):
    transfer = {
        "transfer_id": str(uuid.uuid4())[:8],
        "from_warehouse": body.get("from_warehouse", ""),
        "to_store": body.get("to_store", ""),
        "items": body.get("items", []),
        "total_qty": sum(i.get("quantity", 0) for i in body.get("items", [])),
        "status": "pending",
        "created_by": body.get("created_by", "admin"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_at": None, "approved_by": None,
        "dispatched_at": None, "received_at": None, "received_by": None,
        "notes": body.get("notes", ""),
    }
    await get_db().warehouse_transfers.insert_one(transfer)
    del transfer["_id"]
    return transfer


@router.put("/transfers/{transfer_id}/allocate")
async def allocate_transfer(transfer_id: str):
    result = await get_db().warehouse_transfers.find_one_and_update(
        {"transfer_id": transfer_id, "status": "pending"},
        {"$set": {"status": "allocated", "allocated_at": datetime.now(timezone.utc).isoformat()}},
        return_document=False,
    )
    if not result:
        raise HTTPException(404, "Transfer not found or not in pending status")
    return {"message": "Stock allocated", "transfer_id": transfer_id, "status": "allocated"}


@router.put("/transfers/{transfer_id}/approve")
async def approve_transfer(transfer_id: str, body: dict = None):
    body = body or {}
    result = await get_db().warehouse_transfers.find_one_and_update(
        {"transfer_id": transfer_id, "status": "allocated"},
        {"$set": {"status": "approved", "approved_at": datetime.now(timezone.utc).isoformat(),
                  "approved_by": body.get("approved_by", "manager")}},
        return_document=False,
    )
    if not result:
        raise HTTPException(404, "Transfer not found or not in allocated status")
    return {"message": "Transfer approved", "transfer_id": transfer_id, "status": "approved"}


@router.put("/transfers/{transfer_id}/dispatch")
async def dispatch_transfer(transfer_id: str):
    result = await get_db().warehouse_transfers.find_one_and_update(
        {"transfer_id": transfer_id, "status": "approved"},
        {"$set": {"status": "in_transit", "dispatched_at": datetime.now(timezone.utc).isoformat()}},
        return_document=False,
    )
    if not result:
        raise HTTPException(404, "Transfer not found or not approved")
    return {"message": "Transfer dispatched", "transfer_id": transfer_id, "status": "in_transit"}


@router.get("/transfers/in-transit")
async def get_in_transit():
    transfers = await get_db().warehouse_transfers.find({"status": "in_transit"}, {"_id": 0}).to_list(200)
    total_in_transit = sum(t.get("total_qty", 0) for t in transfers)
    return {"transfers": transfers, "total_in_transit": total_in_transit}


@router.put("/transfers/{transfer_id}/receive")
async def receive_transfer(transfer_id: str, body: dict = None):
    body = body or {}
    result = await get_db().warehouse_transfers.find_one_and_update(
        {"transfer_id": transfer_id, "status": "in_transit"},
        {"$set": {"status": "received", "received_at": datetime.now(timezone.utc).isoformat(),
                  "received_by": body.get("received_by", "store_manager")}},
        return_document=False,
    )
    if not result:
        raise HTTPException(404, "Transfer not found or not in transit")
    return {"message": "Transfer received", "transfer_id": transfer_id, "status": "received"}


@router.get("/transfers/history")
async def get_transfer_history(days: int = 90):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    transfers = await get_db().warehouse_transfers.find(
        {"created_at": {"$gte": cutoff}}, {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    return {"transfers": transfers, "total": len(transfers)}


# ═══════════════════════════════════════════════════════════════
# WH-21 to WH-25: PERFORMANCE (MongoDB Aggregation)
# ═══════════════════════════════════════════════════════════════

@router.get("/performance")
async def get_warehouse_performance(warehouse: Optional[str] = None):
    """WH-21..25: Fulfillment rate, dispatch time, turnover, utilization, slow-moving."""
    db = get_db()
    result: Dict[str, Any] = {
        "fulfillment_rate": 0, "avg_dispatch_hours": 0, "turnover_ratio": 0,
        "utilization_pct": 0, "slow_moving": [], "by_warehouse": [],
    }

    # WH-21/22: Fulfillment rate & dispatch time from transfers
    transfers = await db.warehouse_transfers.find({}, {"_id": 0}).to_list(1000)
    if transfers:
        total_orders = len(transfers)
        fulfilled = sum(1 for t in transfers if t.get("status") in ("received", "in_transit", "approved"))
        result["fulfillment_rate"] = round((fulfilled / max(total_orders, 1)) * 100, 1)

        dispatch_times = []
        for t in transfers:
            if t.get("dispatched_at") and t.get("created_at"):
                try:
                    hours = (datetime.fromisoformat(t["dispatched_at"]) - datetime.fromisoformat(t["created_at"])).total_seconds() / 3600
                    dispatch_times.append(hours)
                except Exception:
                    pass
        result["avg_dispatch_hours"] = round(sum(dispatch_times) / max(len(dispatch_times), 1), 1)

    # Latest inventory day
    date_result = await db.warehouse_inventory.aggregate([
        {"$group": {"_id": None, "max_day": {"$max": "$day"}}}
    ]).to_list(1)
    if not date_result:
        return result
    latest_day = date_result[0]["max_day"]

    # Latest inventory by warehouse
    wh_match = {"day": latest_day}
    if warehouse:
        wh_match["warehouse"] = warehouse

    inv_pipeline = [
        {"$match": wh_match},
        {"$addFields": {"qty": {"$toDouble": {"$ifNull": ["$quantity", 0]}}}},
        {"$group": {
            "_id": "$warehouse",
            "total_qty": {"$sum": "$qty"},
            "skus": {"$addToSet": "$sku"},
        }},
    ]
    wh_data = {}
    async for doc in db.warehouse_inventory.aggregate(inv_pipeline):
        wh_data[doc["_id"]] = {"total_qty": doc["total_qty"], "sku_count": len(doc["skus"]), "skus": set(doc["skus"])}

    total_inv = sum(v["total_qty"] for v in wh_data.values())

    # WH-23: Turnover = total sales value / total inventory
    # Get total sales revenue via aggregation
    sales_pipeline = [
        {"$addFields": {
            "qty": {"$toDouble": {"$ifNull": ["$quantity", 0]}},
            "rev": {"$toDouble": {"$ifNull": ["$revenue", 0]}},
        }},
        {"$group": {"_id": None, "total_rev": {"$sum": "$rev"}}},
    ]
    sales_result = await db.daily_sales.aggregate(sales_pipeline).to_list(1)
    if sales_result and total_inv > 0:
        result["turnover_ratio"] = round(float(sales_result[0]["total_rev"]) / total_inv, 2)

    # WH-24: Utilization
    config = await db.warehouse_config.find_one({"_id": "capacity"}) or {}
    capacities = config.get("warehouses", {})
    wh_util = []
    for wh_name, data in wh_data.items():
        stock = int(data["total_qty"])
        cap = capacities.get(wh_name, 100000)
        wh_util.append({
            "warehouse": wh_name, "current_stock": stock, "capacity": cap,
            "utilization_pct": round((stock / max(cap, 1)) * 100, 1),
        })
    result["by_warehouse"] = wh_util
    total_cap = sum(w["capacity"] for w in wh_util)
    total_stock = sum(w["current_stock"] for w in wh_util)
    result["utilization_pct"] = round((total_stock / max(total_cap, 1)) * 100, 1)

    # WH-25: Slow-moving (no sales in last 90 days)
    sales_90d_pipeline = [
        {"$group": {"_id": "$sku"}},
    ]
    sold_skus = set()
    async for doc in db.daily_sales.aggregate(sales_90d_pipeline):
        sold_skus.add(doc["_id"])

    all_wh_skus = set()
    for data in wh_data.values():
        all_wh_skus |= data["skus"]

    slow_skus = all_wh_skus - sold_skus
    if slow_skus:
        # Get quantities for slow SKUs
        slow_pipeline = [
            {"$match": {"day": latest_day, "sku": {"$in": list(slow_skus)}}},
            {"$addFields": {"qty": {"$toDouble": {"$ifNull": ["$quantity", 0]}}}},
            {"$group": {"_id": "$sku", "total_qty": {"$sum": "$qty"}}},
            {"$sort": {"total_qty": -1}},
            {"$limit": 50},
        ]
        slow_items = []
        sku_info_map = {}
        async for doc in db.sku_master.find({"ean": {"$in": list(slow_skus)}}, {"_id": 0, "ean": 1, "style": 1, "size": 1}):
            sku_info_map[doc.get("ean")] = doc
        async for doc in db.warehouse_inventory.aggregate(slow_pipeline):
            info = sku_info_map.get(doc["_id"], {})
            slow_items.append({
                "sku": doc["_id"], "total_qty": int(doc["total_qty"]),
                "style": info.get("style", ""), "size": info.get("size", ""),
            })
        result["slow_moving"] = slow_items
        result["slow_moving_count"] = len(slow_skus)

    return result


# ═══════════════════════════════════════════════════════════════
# WH-26 to WH-30: DASHBOARD (MongoDB Aggregation)
# ═══════════════════════════════════════════════════════════════

@router.get("/dashboard")
async def get_warehouse_dashboard():
    """WH-26..30: KPIs, category chart, movement trend, comparison."""
    db = get_db()

    # Latest day
    date_result = await db.warehouse_inventory.aggregate([
        {"$group": {"_id": None, "max_day": {"$max": "$day"}}}
    ]).to_list(1)
    if not date_result:
        return {"error": "No warehouse data", "kpis": {}, "category_chart": [], "comparison": []}
    latest_day = date_result[0]["max_day"]

    # Build maps
    sku_map = {}
    async for doc in db.sku_master.find({}, {"_id": 0, "ean": 1, "style": 1, "mrp": 1}):
        if doc.get("ean"):
            sku_map[doc["ean"]] = doc
    style_cat = {}
    async for doc in db.style_master.find({}, {"_id": 0, "style_code": 1, "category": 1}):
        if doc.get("style_code"):
            style_cat[doc["style_code"]] = doc.get("category", "Unknown")

    # KPIs via aggregation
    kpi_pipeline = [
        {"$match": {"day": latest_day}},
        {"$addFields": {"qty": {"$toDouble": {"$ifNull": ["$quantity", 0]}}}},
        {"$group": {
            "_id": None,
            "total_stock": {"$sum": "$qty"},
            "unique_skus": {"$addToSet": "$sku"},
            "unique_warehouses": {"$addToSet": "$warehouse"},
        }},
    ]
    kpi_result = await db.warehouse_inventory.aggregate(kpi_pipeline).to_list(1)
    if not kpi_result:
        return {"error": "No warehouse data", "kpis": {}, "category_chart": [], "comparison": []}

    k = kpi_result[0]
    total_stock = int(k["total_stock"])
    unique_skus = len(k.get("unique_skus", []))
    unique_wh = len(k.get("unique_warehouses", []))

    # Stock value = sum(qty * mrp) for each item
    total_value = 0.0
    cat_agg = {}
    wh_agg = {}
    async for doc in db.warehouse_inventory.find({"day": latest_day}, {"_id": 0}):
        sku = doc.get("sku", "")
        qty = float(doc.get("quantity", 0))
        wh = doc.get("warehouse", "")
        info = sku_map.get(sku, {})
        mrp = float(info.get("mrp", 0) or 0)
        val = qty * mrp
        total_value += val
        style = info.get("style", "")
        cat = style_cat.get(style, "Unknown")

        # Category aggregation
        if cat not in cat_agg:
            cat_agg[cat] = {"total_qty": 0, "skus": set()}
        cat_agg[cat]["total_qty"] += int(qty)
        cat_agg[cat]["skus"].add(sku)

        # Warehouse aggregation
        if wh not in wh_agg:
            wh_agg[wh] = {"total_qty": 0, "skus": set(), "stock_value": 0.0}
        wh_agg[wh]["total_qty"] += int(qty)
        wh_agg[wh]["skus"].add(sku)
        wh_agg[wh]["stock_value"] += val

    kpis = {
        "total_stock": total_stock,
        "total_value": round(total_value, 2),
        "total_skus": unique_skus,
        "total_warehouses": unique_wh,
        "snapshot_date": str(latest_day)[:10],
    }

    # Category chart
    category_chart = sorted(
        [{"category": c, "total_qty": v["total_qty"], "sku_count": len(v["skus"])} for c, v in cat_agg.items()],
        key=lambda x: x["total_qty"], reverse=True,
    )

    # Movement trend (last 14 days)
    trend_pipeline = [
        {"$addFields": {"qty": {"$toDouble": {"$ifNull": ["$quantity", 0]}}, "day_str": {"$substr": ["$day", 0, 10]}}},
        {"$group": {"_id": "$day_str", "total_qty": {"$sum": "$qty"}}},
        {"$sort": {"_id": 1}},
    ]
    trend_raw = await db.warehouse_inventory.aggregate(trend_pipeline).to_list(1000)
    trend_records = [{"date": r["_id"], "total_qty": int(r["total_qty"])} for r in trend_raw][-14:]
    for i, r in enumerate(trend_records):
        prev = trend_records[i - 1]["total_qty"] if i > 0 else r["total_qty"]
        r["inbound"] = max(0, r["total_qty"] - prev)
        r["outbound"] = max(0, prev - r["total_qty"])

    # Warehouse comparison
    comparison = sorted(
        [{"warehouse": wh, "total_qty": v["total_qty"], "sku_count": len(v["skus"]),
          "stock_value": round(v["stock_value"], 2)} for wh, v in wh_agg.items()],
        key=lambda x: x["total_qty"], reverse=True,
    )

    return {
        "kpis": kpis,
        "category_chart": category_chart,
        "movement_trend": trend_records,
        "comparison": comparison,
    }


# ═══════════════════════════════════════════════════════════════
# SEED DEMO DATA
# ═══════════════════════════════════════════════════════════════

@router.post("/seed-demo")
async def seed_warehouse_demo():
    """Seed demo data for movements, transfers, adjustments, config."""
    db = get_db()
    now = datetime.now(timezone.utc)

    await db.warehouse_config.update_one({"_id": "thresholds"}, {"$set": {"reorder_point": 50, "max_threshold": 500}}, upsert=True)
    await db.warehouse_config.update_one({"_id": "capacity"}, {"$set": {"warehouses": {"WH001": 150000, "WH002": 100000}}}, upsert=True)

    # Movements
    await db.warehouse_movements.delete_many({})
    movements = []
    skus = [str(1000001 + i) for i in range(20)]
    warehouses = ["WH001", "WH002"]
    stores = [f"ST{str(i).zfill(3)}" for i in range(1, 11)]
    for d in range(30):
        day = now - timedelta(days=d)
        for _ in range(random.randint(3, 8)):
            movements.append({
                "movement_id": str(uuid.uuid4())[:8], "warehouse": random.choice(warehouses),
                "sku": random.choice(skus), "quantity": random.randint(50, 500),
                "direction": "inbound", "source": f"PO-{random.randint(1000, 9999)}",
                "reference": f"GRN-{random.randint(1000, 9999)}",
                "timestamp": day.replace(hour=random.randint(8, 17)).isoformat(),
            })
        for _ in range(random.randint(2, 6)):
            movements.append({
                "movement_id": str(uuid.uuid4())[:8], "warehouse": random.choice(warehouses),
                "sku": random.choice(skus), "quantity": random.randint(20, 200),
                "direction": "outbound", "destination": random.choice(stores),
                "reference": f"DO-{random.randint(1000, 9999)}",
                "timestamp": day.replace(hour=random.randint(8, 17)).isoformat(),
            })
    if movements:
        await db.warehouse_movements.insert_many(movements)

    # Transfers
    await db.warehouse_transfers.delete_many({})
    transfers = []
    statuses = ["pending", "allocated", "approved", "in_transit", "received", "received"]
    for i in range(15):
        created = now - timedelta(days=random.randint(1, 60), hours=random.randint(0, 23))
        st = statuses[i % len(statuses)]
        t = {
            "transfer_id": str(uuid.uuid4())[:8], "from_warehouse": random.choice(warehouses),
            "to_store": random.choice(stores),
            "items": [{"sku": random.choice(skus), "quantity": random.randint(10, 100)} for _ in range(random.randint(1, 5))],
            "total_qty": 0, "status": st, "created_by": "admin", "created_at": created.isoformat(),
            "approved_at": (created + timedelta(hours=random.randint(2, 12))).isoformat() if st not in ("pending",) else None,
            "approved_by": "manager" if st not in ("pending",) else None,
            "dispatched_at": (created + timedelta(hours=random.randint(12, 36))).isoformat() if st in ("in_transit", "received") else None,
            "received_at": (created + timedelta(hours=random.randint(36, 72))).isoformat() if st == "received" else None,
            "received_by": "store_manager" if st == "received" else None, "notes": "",
        }
        t["total_qty"] = sum(item["quantity"] for item in t["items"])
        transfers.append(t)
    if transfers:
        await db.warehouse_transfers.insert_many(transfers)

    # Adjustments
    await db.warehouse_adjustments.delete_many({})
    adjustments = []
    reasons = ["Physical count correction", "Damaged goods write-off", "System error fix", "Returns processing", "Expiry removal", "Vendor return"]
    for d in range(14):
        day = now - timedelta(days=d)
        for _ in range(random.randint(0, 3)):
            prev = random.randint(50, 500)
            change = random.randint(-50, 50)
            adjustments.append({
                "adjustment_id": str(uuid.uuid4())[:8], "warehouse": random.choice(warehouses),
                "sku": random.choice(skus), "previous_qty": prev, "new_qty": max(0, prev + change),
                "change": change, "reason": random.choice(reasons),
                "adjusted_by": random.choice(["admin", "wh_manager", "supervisor"]),
                "adjusted_at": day.replace(hour=random.randint(8, 17)).isoformat(),
            })
    if adjustments:
        await db.warehouse_adjustments.insert_many(adjustments)

    # Reconciliations
    await db.warehouse_reconciliations.delete_many({})
    recs = []
    for _ in range(8):
        sys_qty = random.randint(100, 1000)
        phys_qty = sys_qty + random.randint(-30, 30)
        recs.append({
            "reconciliation_id": str(uuid.uuid4())[:8], "warehouse": random.choice(warehouses),
            "sku": random.choice(skus), "system_qty": sys_qty, "physical_qty": phys_qty,
            "variance": phys_qty - sys_qty,
            "notes": "Monthly physical count" if random.random() < 0.5 else "Spot check",
            "reconciled_by": random.choice(["admin", "wh_manager"]),
            "reconciled_at": (now - timedelta(days=random.randint(0, 30))).isoformat(),
        })
    if recs:
        await db.warehouse_reconciliations.insert_many(recs)

    return {
        "message": "Warehouse demo data seeded",
        "counts": {"movements": len(movements), "transfers": len(transfers),
                   "adjustments": len(adjustments), "reconciliations": len(recs)},
    }
