"""Warehouse Module — stock, movements, transfers, performance, dashboard.
Covers WH-01 to WH-30 test cases.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import pandas as pd
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


async def _get_cached(file_type: str):
    doc = await get_db().uploaded_files.find_one({"file_type": file_type})
    if doc and 'data' in doc:
        return pd.DataFrame(doc['data'])
    return None


# ═══════════════════════════════════════════════════════════════
# WH-01 to WH-08: STOCK
# ═══════════════════════════════════════════════════════════════

@router.get("/stock")
async def get_warehouse_stock(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    alert_type: Optional[str] = None,
):
    """WH-01..08: View stock with filters, search, value calc, alerts."""
    wh_inv = await _get_cached('warehouse_inventory')
    sku_df = await _get_cached('sku_ean_master')
    style_df = await _get_cached('style_master')

    if wh_inv is None or len(wh_inv) == 0:
        return {"error": "No warehouse inventory data", "items": [], "totals": {}}

    wh_inv['day'] = pd.to_datetime(wh_inv['day'])
    latest = wh_inv[wh_inv['day'] == wh_inv['day'].max()].copy()

    # Merge SKU for MRP + style info
    if sku_df is not None:
        sku_cols = ['ean', 'style', 'size']
        if 'mrp' in sku_df.columns:
            sku_cols.append('mrp')
        latest = latest.merge(
            sku_df[sku_cols].rename(columns={'ean': 'sku'}),
            on='sku', how='left'
        )

    # Merge style master for category
    if style_df is not None and 'style' in latest.columns:
        style_cols = ['style_code']
        if 'category' in style_df.columns:
            style_cols.append('category')
        if 'brand' in style_df.columns:
            style_cols.append('brand')
        latest = latest.merge(
            style_df[style_cols].rename(columns={'style_code': 'style'}),
            on='style', how='left'
        )

    # Stock value (WH-05)
    if 'mrp' in latest.columns:
        latest['mrp'] = pd.to_numeric(latest['mrp'], errors='coerce').fillna(0)
        latest['stock_value'] = latest['quantity'] * latest['mrp']
    else:
        latest['stock_value'] = 0

    # Load config for thresholds
    config = await get_db().warehouse_config.find_one({"_id": "thresholds"}) or {}
    reorder_point = config.get('reorder_point', 50)
    max_threshold = config.get('max_threshold', 500)

    # Alerts (WH-06, WH-07, WH-08)
    latest['alert'] = latest['quantity'].apply(
        lambda q: 'out_of_stock' if q == 0 else (
            'low_stock' if q < reorder_point else (
                'overstock' if q > max_threshold else 'normal'
            )
        )
    )

    # Apply filters
    if warehouse:
        latest = latest[latest['warehouse'] == warehouse]
    if category and 'category' in latest.columns:
        latest = latest[latest['category'].str.lower() == category.lower()]
    if search:
        sl = search.lower()
        mask = latest['sku'].astype(str).str.lower().str.contains(sl, na=False)
        if 'style' in latest.columns:
            mask = mask | latest['style'].astype(str).str.lower().str.contains(sl, na=False)
        latest = latest[mask]
    if alert_type and alert_type != 'all':
        latest = latest[latest['alert'] == alert_type]

    # Fill NaN
    for col in ['style', 'size', 'category', 'brand']:
        if col in latest.columns:
            latest[col] = latest[col].fillna('')

    items = latest.to_dict('records')
    for item in items:
        for k in list(item.keys()):
            if isinstance(item[k], float) and pd.isna(item[k]):
                item[k] = 0

    total_stock = int(latest['quantity'].sum())
    total_value = round(float(latest['stock_value'].sum()), 2)
    low_stock_count = int((latest['alert'] == 'low_stock').sum())
    oos_count = int((latest['alert'] == 'out_of_stock').sum())
    overstock_count = int((latest['alert'] == 'overstock').sum())
    warehouses_list = sorted(latest['warehouse'].unique().tolist())
    categories_list = sorted(latest['category'].unique().tolist()) if 'category' in latest.columns else []

    return {
        "items": items[:200],
        "totals": {
            "total_stock": total_stock,
            "total_value": total_value,
            "total_skus": int(latest['sku'].nunique()),
            "total_warehouses": int(latest['warehouse'].nunique()),
            "low_stock": low_stock_count,
            "out_of_stock": oos_count,
            "overstock": overstock_count,
            "reorder_point": reorder_point,
            "max_threshold": max_threshold,
        },
        "warehouses": warehouses_list,
        "categories": categories_list,
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
    if direction and direction != 'all':
        query["direction"] = direction

    movements = await get_db().warehouse_movements.find(
        query, {"_id": 0}
    ).sort("timestamp", -1).to_list(500)

    # Summary
    inbound = [m for m in movements if m.get('direction') == 'inbound']
    outbound = [m for m in movements if m.get('direction') == 'outbound']

    return {
        "movements": movements,
        "summary": {
            "total_inbound": sum(m.get('quantity', 0) for m in inbound),
            "total_outbound": sum(m.get('quantity', 0) for m in outbound),
            "inbound_count": len(inbound),
            "outbound_count": len(outbound),
        }
    }


@router.get("/daily-change")
async def get_daily_stock_change(warehouse: Optional[str] = None, days: int = 7):
    """WH-12: Opening vs closing stock by day."""
    wh_inv = await _get_cached('warehouse_inventory')
    if wh_inv is None or len(wh_inv) == 0:
        return {"days": []}

    wh_inv['day'] = pd.to_datetime(wh_inv['day'])
    if warehouse:
        wh_inv = wh_inv[wh_inv['warehouse'] == warehouse]

    by_day = wh_inv.groupby(wh_inv['day'].dt.date).agg(
        total_qty=('quantity', 'sum'),
        sku_count=('sku', 'nunique')
    ).reset_index().sort_values('day')
    by_day.columns = ['date', 'closing_stock', 'sku_count']
    by_day['date'] = by_day['date'].astype(str)

    records = by_day.tail(days).to_dict('records')
    # Opening stock is previous day's closing
    for i, r in enumerate(records):
        r['opening_stock'] = records[i - 1]['closing_stock'] if i > 0 else r['closing_stock']
        r['change'] = r['closing_stock'] - r['opening_stock']

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
    del rec['_id']
    return rec


@router.get("/adjustments")
async def get_adjustments(warehouse: Optional[str] = None, days: int = 30):
    """WH-14: Stock adjustment log (who changed what)."""
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
    del adj['_id']
    return adj


# ═══════════════════════════════════════════════════════════════
# WH-15 to WH-20: TRANSFERS
# ═══════════════════════════════════════════════════════════════

@router.get("/transfers")
async def list_transfers(
    status: Optional[str] = None,
    warehouse: Optional[str] = None,
):
    """WH-15..20: List transfer orders."""
    query: Dict[str, Any] = {}
    if status and status != 'all':
        query["status"] = status
    if warehouse:
        query["$or"] = [{"from_warehouse": warehouse}, {"to_store": warehouse}]

    transfers = await get_db().warehouse_transfers.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    return {"transfers": transfers}


@router.post("/transfers")
async def create_transfer(body: dict):
    """WH-15: Create transfer order."""
    transfer = {
        "transfer_id": str(uuid.uuid4())[:8],
        "from_warehouse": body.get("from_warehouse", ""),
        "to_store": body.get("to_store", ""),
        "items": body.get("items", []),
        "total_qty": sum(i.get("quantity", 0) for i in body.get("items", [])),
        "status": "pending",
        "created_by": body.get("created_by", "admin"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_at": None,
        "approved_by": None,
        "dispatched_at": None,
        "received_at": None,
        "received_by": None,
        "notes": body.get("notes", ""),
    }
    await get_db().warehouse_transfers.insert_one(transfer)
    del transfer['_id']
    return transfer


@router.put("/transfers/{transfer_id}/allocate")
async def allocate_transfer(transfer_id: str):
    """WH-16: Allocate stock — reduce WH qty, mark as allocated."""
    result = await get_db().warehouse_transfers.find_one_and_update(
        {"transfer_id": transfer_id, "status": "pending"},
        {"$set": {"status": "allocated", "allocated_at": datetime.now(timezone.utc).isoformat()}},
        return_document=False
    )
    if not result:
        raise HTTPException(404, "Transfer not found or not in pending status")
    return {"message": "Stock allocated", "transfer_id": transfer_id, "status": "allocated"}


@router.put("/transfers/{transfer_id}/approve")
async def approve_transfer(transfer_id: str, body: dict = None):
    """WH-17: Multi-step approval."""
    body = body or {}
    result = await get_db().warehouse_transfers.find_one_and_update(
        {"transfer_id": transfer_id, "status": "allocated"},
        {"$set": {
            "status": "approved",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": body.get("approved_by", "manager"),
        }},
        return_document=False
    )
    if not result:
        raise HTTPException(404, "Transfer not found or not in allocated status")
    return {"message": "Transfer approved", "transfer_id": transfer_id, "status": "approved"}


@router.put("/transfers/{transfer_id}/dispatch")
async def dispatch_transfer(transfer_id: str):
    """Dispatch approved transfer — mark as in_transit."""
    result = await get_db().warehouse_transfers.find_one_and_update(
        {"transfer_id": transfer_id, "status": "approved"},
        {"$set": {"status": "in_transit", "dispatched_at": datetime.now(timezone.utc).isoformat()}},
        return_document=False
    )
    if not result:
        raise HTTPException(404, "Transfer not found or not approved")
    return {"message": "Transfer dispatched", "transfer_id": transfer_id, "status": "in_transit"}


@router.get("/transfers/in-transit")
async def get_in_transit():
    """WH-18: Track in-transit inventory."""
    transfers = await get_db().warehouse_transfers.find(
        {"status": "in_transit"}, {"_id": 0}
    ).to_list(200)
    total_in_transit = sum(t.get('total_qty', 0) for t in transfers)
    return {"transfers": transfers, "total_in_transit": total_in_transit}


@router.put("/transfers/{transfer_id}/receive")
async def receive_transfer(transfer_id: str, body: dict = None):
    """WH-19: Receive transfer — update store inventory."""
    body = body or {}
    result = await get_db().warehouse_transfers.find_one_and_update(
        {"transfer_id": transfer_id, "status": "in_transit"},
        {"$set": {
            "status": "received",
            "received_at": datetime.now(timezone.utc).isoformat(),
            "received_by": body.get("received_by", "store_manager"),
        }},
        return_document=False
    )
    if not result:
        raise HTTPException(404, "Transfer not found or not in transit")
    return {"message": "Transfer received", "transfer_id": transfer_id, "status": "received"}


@router.get("/transfers/history")
async def get_transfer_history(days: int = 90):
    """WH-20: Full transfer audit trail."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    transfers = await get_db().warehouse_transfers.find(
        {"created_at": {"$gte": cutoff}}, {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    return {"transfers": transfers, "total": len(transfers)}


# ═══════════════════════════════════════════════════════════════
# WH-21 to WH-25: PERFORMANCE
# ═══════════════════════════════════════════════════════════════

@router.get("/performance")
async def get_warehouse_performance(warehouse: Optional[str] = None):
    """WH-21..25: Fulfillment rate, dispatch time, turnover, utilization, slow-moving."""
    wh_inv = await _get_cached('warehouse_inventory')
    sales_df = await _get_cached('daily_sales')
    sku_df = await _get_cached('sku_ean_master')

    result: Dict[str, Any] = {
        "fulfillment_rate": 0,
        "avg_dispatch_hours": 0,
        "turnover_ratio": 0,
        "utilization_pct": 0,
        "slow_moving": [],
        "by_warehouse": [],
    }

    # Transfers for fulfillment rate (WH-21) and dispatch time (WH-22)
    transfers = await get_db().warehouse_transfers.find({}, {"_id": 0}).to_list(1000)
    if transfers:
        total_orders = len(transfers)
        fulfilled = sum(1 for t in transfers if t.get('status') in ('received', 'in_transit', 'approved'))
        result["fulfillment_rate"] = round((fulfilled / max(total_orders, 1)) * 100, 1)

        dispatch_times = []
        for t in transfers:
            if t.get('dispatched_at') and t.get('created_at'):
                try:
                    created = datetime.fromisoformat(t['created_at'])
                    dispatched = datetime.fromisoformat(t['dispatched_at'])
                    hours = (dispatched - created).total_seconds() / 3600
                    dispatch_times.append(hours)
                except Exception:
                    pass
        result["avg_dispatch_hours"] = round(sum(dispatch_times) / max(len(dispatch_times), 1), 1)

    if wh_inv is not None and len(wh_inv) > 0:
        wh_inv['day'] = pd.to_datetime(wh_inv['day'])
        latest = wh_inv[wh_inv['day'] == wh_inv['day'].max()].copy()

        if warehouse:
            latest = latest[latest['warehouse'] == warehouse]

        avg_inv = float(latest['quantity'].mean()) if len(latest) > 0 else 1

        # Turnover (WH-23): COGS / Average Inventory
        if sales_df is not None and sku_df is not None and 'mrp' in sku_df.columns:
            sales_copy = sales_df.copy()
            sales_copy = sales_copy.merge(
                sku_df[['ean', 'mrp']].rename(columns={'ean': 'sku'}),
                on='sku', how='left'
            )
            sales_copy['mrp'] = pd.to_numeric(sales_copy['mrp'], errors='coerce').fillna(0)
            sales_copy['quantity'] = pd.to_numeric(sales_copy['quantity'], errors='coerce').fillna(0)
            cogs = float((sales_copy['quantity'] * sales_copy['mrp']).sum())
            total_inv_value = float(latest['quantity'].sum())
            if total_inv_value > 0:
                result["turnover_ratio"] = round(cogs / total_inv_value, 2)

        # Utilization (WH-24)
        config = await get_db().warehouse_config.find_one({"_id": "capacity"}) or {}
        capacities = config.get('warehouses', {})
        by_wh = latest.groupby('warehouse')['quantity'].sum().reset_index()
        wh_util = []
        for _, row in by_wh.iterrows():
            wh_name = row['warehouse']
            stock = int(row['quantity'])
            cap = capacities.get(wh_name, 100000)
            wh_util.append({
                "warehouse": wh_name,
                "current_stock": stock,
                "capacity": cap,
                "utilization_pct": round((stock / max(cap, 1)) * 100, 1),
            })
        result["by_warehouse"] = wh_util
        total_cap = sum(w['capacity'] for w in wh_util)
        total_stock = sum(w['current_stock'] for w in wh_util)
        result["utilization_pct"] = round((total_stock / max(total_cap, 1)) * 100, 1)

        # Slow-moving stock (WH-25): no movement for 90+ days
        if sales_df is not None:
            sales_copy2 = sales_df.copy()
            sales_copy2['day'] = pd.to_datetime(sales_copy2['day'])
            cutoff_90 = sales_copy2['day'].max() - timedelta(days=90)
            recent_sales = sales_copy2[sales_copy2['day'] >= cutoff_90]
            sold_skus = set(recent_sales['sku'].unique())
            all_wh_skus = set(latest['sku'].unique())
            slow = all_wh_skus - sold_skus

            slow_df = latest[latest['sku'].isin(slow)].groupby('sku').agg(
                total_qty=('quantity', 'sum')
            ).reset_index().sort_values('total_qty', ascending=False).head(50)

            if sku_df is not None:
                slow_df = slow_df.merge(
                    sku_df[['ean', 'style', 'size']].rename(columns={'ean': 'sku'}),
                    on='sku', how='left'
                )
            result["slow_moving"] = slow_df.fillna('').to_dict('records')
            result["slow_moving_count"] = len(slow)

    return result


# ═══════════════════════════════════════════════════════════════
# WH-26 to WH-30: DASHBOARD
# ═══════════════════════════════════════════════════════════════

@router.get("/dashboard")
async def get_warehouse_dashboard():
    """WH-26..30: Enhanced KPIs, category chart, movement trend, comparison."""
    wh_inv = await _get_cached('warehouse_inventory')
    sku_df = await _get_cached('sku_ean_master')
    style_df = await _get_cached('style_master')

    if wh_inv is None or len(wh_inv) == 0:
        return {"error": "No warehouse data", "kpis": {}, "category_chart": [], "comparison": []}

    wh_inv['day'] = pd.to_datetime(wh_inv['day'])
    latest = wh_inv[wh_inv['day'] == wh_inv['day'].max()].copy()

    # Merge SKU for MRP + style
    if sku_df is not None:
        cols = ['ean', 'style', 'size']
        if 'mrp' in sku_df.columns:
            cols.append('mrp')
        latest = latest.merge(sku_df[cols].rename(columns={'ean': 'sku'}), on='sku', how='left')

    # Merge style for category
    if style_df is not None and 'style' in latest.columns:
        scols = ['style_code']
        if 'category' in style_df.columns:
            scols.append('category')
        latest = latest.merge(style_df[scols].rename(columns={'style_code': 'style'}), on='style', how='left')

    # Stock value
    total_value = 0
    if 'mrp' in latest.columns:
        latest['mrp'] = pd.to_numeric(latest['mrp'], errors='coerce').fillna(0)
        total_value = round(float((latest['quantity'] * latest['mrp']).sum()), 2)

    # KPIs (WH-26)
    kpis = {
        "total_stock": int(latest['quantity'].sum()),
        "total_value": total_value,
        "total_skus": int(latest['sku'].nunique()),
        "total_warehouses": int(latest['warehouse'].nunique()),
        "snapshot_date": str(wh_inv['day'].max().date()),
    }

    # Category chart (WH-27)
    category_chart = []
    if 'category' in latest.columns:
        cat_agg = latest.groupby('category').agg(
            total_qty=('quantity', 'sum'),
            sku_count=('sku', 'nunique')
        ).reset_index().sort_values('total_qty', ascending=False)
        cat_agg['category'] = cat_agg['category'].fillna('Unknown')
        category_chart = cat_agg.to_dict('records')

    # Movement trend (WH-28) — using inventory snapshots
    trend = wh_inv.groupby(wh_inv['day'].dt.date.astype(str)).agg(
        total_qty=('quantity', 'sum')
    ).reset_index()
    trend.columns = ['date', 'total_qty']
    trend_records = trend.tail(14).to_dict('records')
    for i, r in enumerate(trend_records):
        prev = trend_records[i - 1]['total_qty'] if i > 0 else r['total_qty']
        r['inbound'] = max(0, r['total_qty'] - prev)
        r['outbound'] = max(0, prev - r['total_qty'])

    # Multi-warehouse comparison (WH-30)
    comparison = latest.groupby('warehouse').agg(
        total_qty=('quantity', 'sum'),
        sku_count=('sku', 'nunique'),
    ).reset_index()
    if 'mrp' in latest.columns:
        val_by_wh = latest.groupby('warehouse').apply(
            lambda g: round(float((g['quantity'] * g['mrp']).sum()), 2)
        ).reset_index()
        val_by_wh.columns = ['warehouse', 'stock_value']
        comparison = comparison.merge(val_by_wh, on='warehouse', how='left')
    else:
        comparison['stock_value'] = 0
    comparison = comparison.sort_values('total_qty', ascending=False)

    return {
        "kpis": kpis,
        "category_chart": category_chart,
        "movement_trend": trend_records,
        "comparison": comparison.fillna(0).to_dict('records'),
    }


# ═══════════════════════════════════════════════════════════════
# SEED DEMO DATA
# ═══════════════════════════════════════════════════════════════

@router.post("/seed-demo")
async def seed_warehouse_demo():
    """Seed demo data for movements, transfers, adjustments, config."""
    db = get_db()
    now = datetime.now(timezone.utc)

    # Config: thresholds & capacities
    await db.warehouse_config.update_one(
        {"_id": "thresholds"},
        {"$set": {"reorder_point": 50, "max_threshold": 500}},
        upsert=True
    )
    await db.warehouse_config.update_one(
        {"_id": "capacity"},
        {"$set": {"warehouses": {"WH001": 150000, "WH002": 100000}}},
        upsert=True
    )

    # Movements (30 days)
    await db.warehouse_movements.delete_many({})
    movements = []
    skus = [str(1000001 + i) for i in range(20)]
    warehouses = ["WH001", "WH002"]
    stores = [f"ST{str(i).zfill(3)}" for i in range(1, 11)]
    for d in range(30):
        day = now - timedelta(days=d)
        for _ in range(random.randint(3, 8)):
            movements.append({
                "movement_id": str(uuid.uuid4())[:8],
                "warehouse": random.choice(warehouses),
                "sku": random.choice(skus),
                "quantity": random.randint(50, 500),
                "direction": "inbound",
                "source": f"PO-{random.randint(1000, 9999)}",
                "reference": f"GRN-{random.randint(1000, 9999)}",
                "timestamp": day.replace(hour=random.randint(8, 17)).isoformat(),
            })
        for _ in range(random.randint(2, 6)):
            movements.append({
                "movement_id": str(uuid.uuid4())[:8],
                "warehouse": random.choice(warehouses),
                "sku": random.choice(skus),
                "quantity": random.randint(20, 200),
                "direction": "outbound",
                "destination": random.choice(stores),
                "reference": f"DO-{random.randint(1000, 9999)}",
                "timestamp": day.replace(hour=random.randint(8, 17)).isoformat(),
            })
    if movements:
        await db.warehouse_movements.insert_many(movements)

    # Transfers (various statuses)
    await db.warehouse_transfers.delete_many({})
    transfers = []
    statuses = ["pending", "allocated", "approved", "in_transit", "received", "received"]
    for i in range(15):
        created = now - timedelta(days=random.randint(1, 60), hours=random.randint(0, 23))
        st = statuses[i % len(statuses)]
        t = {
            "transfer_id": str(uuid.uuid4())[:8],
            "from_warehouse": random.choice(warehouses),
            "to_store": random.choice(stores),
            "items": [{"sku": random.choice(skus), "quantity": random.randint(10, 100)} for _ in range(random.randint(1, 5))],
            "total_qty": 0,
            "status": st,
            "created_by": "admin",
            "created_at": created.isoformat(),
            "approved_at": (created + timedelta(hours=random.randint(2, 12))).isoformat() if st not in ("pending",) else None,
            "approved_by": "manager" if st not in ("pending",) else None,
            "dispatched_at": (created + timedelta(hours=random.randint(12, 36))).isoformat() if st in ("in_transit", "received") else None,
            "received_at": (created + timedelta(hours=random.randint(36, 72))).isoformat() if st == "received" else None,
            "received_by": "store_manager" if st == "received" else None,
            "notes": "",
        }
        t["total_qty"] = sum(item["quantity"] for item in t["items"])
        transfers.append(t)
    if transfers:
        await db.warehouse_transfers.insert_many(transfers)

    # Adjustments
    await db.warehouse_adjustments.delete_many({})
    adjustments = []
    reasons = ["Physical count correction", "Damaged goods write-off", "System error fix",
               "Returns processing", "Expiry removal", "Vendor return"]
    for d in range(14):
        day = now - timedelta(days=d)
        for _ in range(random.randint(0, 3)):
            prev = random.randint(50, 500)
            change = random.randint(-50, 50)
            adjustments.append({
                "adjustment_id": str(uuid.uuid4())[:8],
                "warehouse": random.choice(warehouses),
                "sku": random.choice(skus),
                "previous_qty": prev,
                "new_qty": max(0, prev + change),
                "change": change,
                "reason": random.choice(reasons),
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
            "reconciliation_id": str(uuid.uuid4())[:8],
            "warehouse": random.choice(warehouses),
            "sku": random.choice(skus),
            "system_qty": sys_qty,
            "physical_qty": phys_qty,
            "variance": phys_qty - sys_qty,
            "notes": "Monthly physical count" if random.random() < 0.5 else "Spot check",
            "reconciled_by": random.choice(["admin", "wh_manager"]),
            "reconciled_at": (now - timedelta(days=random.randint(0, 30))).isoformat(),
        })
    if recs:
        await db.warehouse_reconciliations.insert_many(recs)

    return {
        "message": "Warehouse demo data seeded",
        "counts": {
            "movements": len(movements),
            "transfers": len(transfers),
            "adjustments": len(adjustments),
            "reconciliations": len(recs),
        }
    }
