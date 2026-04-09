"""
Replenishment Planner Endpoints
Covers: Reorder Point, Order Quantity, IST (Inter-Store Transfer),
        Replenishment Run, and Orders Dashboard
"""

from fastapi import APIRouter, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import pandas as pd
import numpy as np
import os
import io
import uuid
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/analytics/replenishment", tags=["replenishment"])

# --------------- Shared DB helpers ---------------
_client: Optional[AsyncIOMotorClient] = None
_get_cached_data_func = None


def init_replenishment(mongo_client: AsyncIOMotorClient, get_cached_data_func=None):
    global _client, _get_cached_data_func
    _client = mongo_client
    _get_cached_data_func = get_cached_data_func


def _get_db():
    from multi_tenant import tenant_context
    ctx = tenant_context.get()
    if ctx:
        return _client[ctx.db_name]
    return _client[os.environ["DB_NAME"]]


async def _cached(file_type: str) -> Optional[pd.DataFrame]:
    if _get_cached_data_func:
        return await _get_cached_data_func(file_type)
    doc = await _get_db().uploaded_files.find_one({"file_type": file_type})
    if doc and "data" in doc:
        return pd.DataFrame(doc["data"])
    return None


async def _get_config() -> dict:
    cfg = await _get_db().analysis_config.find_one({"_id": "main"}, {"_id": 0})
    return cfg or {}


# --------------- Filter helpers ---------------

def _date_filter(df: pd.DataFrame, start: str = None, end: str = None, col="day"):
    if col not in df.columns:
        return df
    df[col] = pd.to_datetime(df[col])
    if start:
        df = df[df[col] >= pd.to_datetime(start)]
    if end:
        df = df[df[col] <= pd.to_datetime(end)]
    return df


def _channel_filter(df, channels):
    if not channels or "channel" not in df.columns:
        return df
    return df[df["channel"].isin(channels)]


def _region_filter(df, regions, store_df=None):
    if not regions:
        return df
    if "region" in df.columns:
        return df[df["region"].isin(regions)]
    if store_df is not None and "store_code" in df.columns and "region" in store_df.columns:
        valid = store_df[store_df["region"].isin(regions)]["store_code"].tolist()
        return df[df["store_code"].isin(valid)]
    return df


def _category_filter(df, categories, style_df=None):
    if not categories or style_df is None:
        return df
    if "category" in df.columns:
        return df[df["category"].isin(categories)]
    if "style" in df.columns and "style_code" in style_df.columns:
        valid = style_df[style_df["category"].isin(categories)]["style_code"].tolist()
        return df[df["style"].isin(valid)]
    return df


def _parse_list(param: str) -> List[str]:
    if not param:
        return []
    return [x.strip() for x in param.split(",") if x.strip()]


# --------------- Pydantic models ---------------

class ManualOverride(BaseModel):
    store_code: str
    sku: str
    reorder_point: Optional[float] = None
    reorder_qty: Optional[float] = None


class OrderAction(BaseModel):
    order_id: str
    action: str  # "approve" or "reject"
    notes: Optional[str] = ""


class BulkOrderAction(BaseModel):
    order_ids: List[str]
    action: str  # "approve" or "reject"
    notes: Optional[str] = ""


class ScheduleConfig(BaseModel):
    enabled: bool = False
    frequency: str = "weekly"  # "daily" or "weekly"
    day_of_week: Optional[int] = 1  # 0=Mon, 6=Sun
    lead_time_days: int = 14
    safety_days: int = 7


class ISTTransferAction(BaseModel):
    transfer_id: str
    action: str  # "approve" or "reject"
    notes: Optional[str] = ""


# =========================================================================
# ENDPOINT 1: Reorder Point Calculation (REP-01 to REP-08)
# =========================================================================
@router.get("/reorder-points")
async def get_reorder_points(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    lead_time_days: int = None,
    safety_days: int = None,
):
    """
    REP-01: Reorder Point = (Avg Daily Sales x Lead Time) + Safety Stock
    REP-02: Zero lead time -> RP = Safety Stock
    REP-03: Zero safety stock -> RP = Avg Sales x Lead Time
    REP-04: High variability -> higher safety stock (uses std dev)
    REP-05: Seasonal -> dynamic safety stock
    REP-06: New style (no history) -> use category average
    REP-07: Manual override -> user value takes precedence
    REP-08: Reorder point exceeded -> trigger replenishment flag
    """
    cfg = await _get_config()
    if lead_time_days is None:
        lead_time_days = cfg.get("lead_time_days", 14)
    if safety_days is None:
        safety_days = cfg.get("safety_days", cfg.get("cover_days", 7))

    sales_df = await _cached("daily_sales")
    inv_df = await _cached("store_inventory")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")

    if sales_df is None or inv_df is None or sku_df is None:
        return {"error": "Required data not uploaded (need daily_sales, store_inventory, sku_ean_master)"}

    try:
        sales = _date_filter(sales_df.copy(), start_date, end_date, "day")
        inv = _date_filter(inv_df.copy(), start_date, end_date, "day")
        cat_list = _parse_list(categories)
        ch_list = _parse_list(channels)
        rg_list = _parse_list(regions)

        if ch_list:
            sales = _channel_filter(sales, ch_list)
            inv = _channel_filter(inv, ch_list)
        if rg_list:
            sales = _region_filter(sales, rg_list, store_df)
            inv = _region_filter(inv, rg_list, store_df)

        sales["day"] = pd.to_datetime(sales["day"])
        inv["day"] = pd.to_datetime(inv["day"])

        # Compute ROS per store-SKU, plus std dev for variability (REP-04)
        ros_calc = sales.groupby(["store_code", "sku"]).agg(
            total_qty=("quantity", "sum"),
            total_revenue=("revenue", "sum"),
            live_days=("day", "nunique"),
            daily_std=("quantity", "std"),
        ).reset_index()
        ros_calc["daily_std"] = ros_calc["daily_std"].fillna(0)
        ros_calc["avg_daily_sales"] = (ros_calc["total_qty"] / ros_calc["live_days"].clip(lower=1)).round(4)

        # Map style and category
        if "style" in sku_df.columns:
            ros_calc["style"] = ros_calc["sku"].map(sku_df.groupby("ean")["style"].first()).fillna("Unknown")
        else:
            ros_calc["style"] = "Unknown"

        if "size" in sku_df.columns:
            ros_calc["size"] = ros_calc["sku"].map(sku_df.groupby("ean")["size"].first()).fillna("-")
        else:
            ros_calc["size"] = "-"

        # Add category from style_df
        style_category = {}
        if style_df is not None and "style_code" in style_df.columns and "category" in style_df.columns:
            style_category = style_df.groupby("style_code")["category"].first().to_dict()
        ros_calc["category"] = ros_calc["style"].map(style_category).fillna("General")

        if cat_list:
            ros_calc = _category_filter(ros_calc, cat_list, style_df)

        # Detect seasonal styles (REP-05) — based on whether the style has > 50% sales in a single quarter
        sales_with_qtr = sales.copy()
        sales_with_qtr["quarter"] = pd.to_datetime(sales_with_qtr["day"]).dt.quarter
        qtr_sales = sales_with_qtr.groupby(["sku", "quarter"])["quantity"].sum().reset_index()
        total_by_sku = qtr_sales.groupby("sku")["quantity"].sum().rename("total_qty_all")
        qtr_pct = qtr_sales.merge(total_by_sku, on="sku")
        qtr_pct["pct"] = qtr_pct["quantity"] / qtr_pct["total_qty_all"].clip(lower=1)
        seasonal_skus = set(qtr_pct[qtr_pct["pct"] > 0.5]["sku"].unique())

        # Category average ROS for new styles fallback (REP-06)
        cat_avg_ros = ros_calc.groupby("category")["avg_daily_sales"].mean().to_dict()

        # Determine date range for "new style" detection — first sale date per sku
        first_sale = sales.groupby("sku")["day"].min().rename("first_sale_date")
        ros_calc = ros_calc.merge(first_sale, left_on="sku", right_index=True, how="left")
        latest_date = sales["day"].max()
        days_since_first = (latest_date - ros_calc["first_sale_date"]).dt.days.fillna(0)
        ros_calc["is_new_style"] = days_since_first < 30

        # Compute safety stock with variability multiplier (REP-04)
        # z-score 1.65 for ~95% service level
        z_score = 1.65
        ros_calc["base_safety_stock"] = (ros_calc["avg_daily_sales"] * safety_days).round(1)
        ros_calc["variability_safety"] = (z_score * ros_calc["daily_std"] * np.sqrt(float(lead_time_days))).round(1)
        ros_calc["is_high_variability"] = ros_calc["daily_std"] > (ros_calc["avg_daily_sales"] * 0.5)

        # Seasonal dynamic safety — bump 50% for seasonal styles (REP-05)
        ros_calc["is_seasonal"] = ros_calc["sku"].isin(seasonal_skus)
        seasonal_mult = np.where(ros_calc["is_seasonal"], 1.5, 1.0)

        # Final safety stock
        ros_calc["safety_stock"] = (
            np.where(
                ros_calc["is_high_variability"],
                ros_calc["base_safety_stock"] + ros_calc["variability_safety"],
                ros_calc["base_safety_stock"],
            ) * seasonal_mult
        ).round(0)

        # For new styles (REP-06), use category average if own ROS is very low
        for idx in ros_calc[ros_calc["is_new_style"]].index:
            cat = ros_calc.at[idx, "category"]
            cat_ros = cat_avg_ros.get(cat, ros_calc["avg_daily_sales"].mean())
            if ros_calc.at[idx, "avg_daily_sales"] < cat_ros * 0.3:
                ros_calc.at[idx, "avg_daily_sales"] = round(cat_ros, 4)
                ros_calc.at[idx, "safety_stock"] = round(cat_ros * safety_days, 0)

        # Reorder point = (Avg Daily Sales x Lead Time) + Safety Stock (REP-01, REP-02, REP-03)
        ros_calc["demand_during_lead"] = (ros_calc["avg_daily_sales"] * lead_time_days).round(1)
        ros_calc["reorder_point"] = (ros_calc["demand_during_lead"] + ros_calc["safety_stock"]).round(0)

        # Get current SOH
        latest_inv_date = inv["day"].max()
        latest_inv = inv[inv["day"] == latest_inv_date]
        soh = latest_inv.groupby(["store_code", "ean"])["quantity"].sum().reset_index()
        soh.columns = ["store_code", "sku", "current_soh"]
        ros_calc = ros_calc.merge(soh, on=["store_code", "sku"], how="left")
        ros_calc["current_soh"] = ros_calc["current_soh"].fillna(0).clip(lower=0)

        # Trigger flag (REP-08) — stock below reorder point
        ros_calc["trigger_replenishment"] = ros_calc["current_soh"] < ros_calc["reorder_point"]

        # Manual overrides (REP-07) from DB
        overrides = await _get_db().reorder_overrides.find({}, {"_id": 0}).to_list(5000)
        override_map = {(o["store_code"], o["sku"]): o for o in overrides}
        ros_calc["has_manual_override"] = False
        for idx, row in ros_calc.iterrows():
            key = (row["store_code"], str(row["sku"]))
            if key in override_map:
                ovr = override_map[key]
                if ovr.get("reorder_point") is not None:
                    ros_calc.at[idx, "reorder_point"] = ovr["reorder_point"]
                    ros_calc.at[idx, "has_manual_override"] = True
                    ros_calc.at[idx, "trigger_replenishment"] = row["current_soh"] < ovr["reorder_point"]

        # Summary
        total_items = len(ros_calc)
        triggered_count = int(ros_calc["trigger_replenishment"].sum())
        high_var_count = int(ros_calc["is_high_variability"].sum())
        seasonal_count = int(ros_calc["is_seasonal"].sum())
        new_style_count = int(ros_calc["is_new_style"].sum())
        override_count = int(ros_calc["has_manual_override"].sum())

        out_cols = [
            "store_code", "sku", "style", "size", "category",
            "avg_daily_sales", "demand_during_lead", "safety_stock",
            "reorder_point", "current_soh", "trigger_replenishment",
            "is_high_variability", "is_seasonal", "is_new_style",
            "has_manual_override",
        ]
        detail = ros_calc[out_cols].sort_values("trigger_replenishment", ascending=False).head(300)
        # Convert booleans to Python bool for JSON serialization
        for c in ["trigger_replenishment", "is_high_variability", "is_seasonal", "is_new_style", "has_manual_override"]:
            detail[c] = detail[c].astype(bool)

        return {
            "summary": {
                "total_store_sku_pairs": total_items,
                "triggered_count": triggered_count,
                "high_variability_count": high_var_count,
                "seasonal_count": seasonal_count,
                "new_style_count": new_style_count,
                "override_count": override_count,
                "lead_time_days": lead_time_days,
                "safety_days": safety_days,
            },
            "detail": detail.round(2).fillna(0).to_dict("records"),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# REP-07: Manual override endpoint
@router.post("/reorder-points/override")
async def set_reorder_override(body: ManualOverride):
    """Set a manual override for reorder point or quantity for a store-SKU."""
    db = _get_db()
    doc = {
        "store_code": body.store_code,
        "sku": body.sku,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if body.reorder_point is not None:
        doc["reorder_point"] = body.reorder_point
    if body.reorder_qty is not None:
        doc["reorder_qty"] = body.reorder_qty

    await db.reorder_overrides.update_one(
        {"store_code": body.store_code, "sku": body.sku},
        {"$set": doc},
        upsert=True,
    )
    return {"status": "ok", "message": f"Override set for {body.store_code}/{body.sku}"}


@router.get("/reorder-points/overrides")
async def list_reorder_overrides():
    """List all manual reorder point overrides."""
    overrides = await _get_db().reorder_overrides.find({}, {"_id": 0}).to_list(5000)
    return {"overrides": overrides, "count": len(overrides)}


@router.delete("/reorder-points/override")
async def delete_reorder_override(store_code: str, sku: str):
    result = await _get_db().reorder_overrides.delete_one({"store_code": store_code, "sku": sku})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Override not found")
    return {"status": "ok", "message": "Override removed"}


# =========================================================================
# ENDPOINT 2: Order Quantity Calculation (REP-09 to REP-15)
# =========================================================================
@router.get("/order-quantity")
async def get_order_quantities(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    lead_time_days: int = None,
    safety_days: int = None,
    cover_days: int = None,
    moq: int = 1,
    pack_size: int = 1,
):
    """
    REP-09: Order Qty = (Cover Days x Avg Sales) - Current Stock, min 0
    REP-10: If current stock > requirement -> qty = 0
    REP-11: MOQ -> round up to minimum order quantity
    REP-12: Pack size -> round up to pack multiple
    REP-13: Warehouse stock availability check
    REP-14: Multiple store allocation based on ROS
    REP-15: Priority store allocation (A-class stores get more)
    """
    cfg = await _get_config()
    if lead_time_days is None:
        lead_time_days = cfg.get("lead_time_days", 14)
    if safety_days is None:
        safety_days = cfg.get("safety_days", cfg.get("cover_days", 7))
    if cover_days is None:
        cover_days = lead_time_days + safety_days

    sales_df = await _cached("daily_sales")
    inv_df = await _cached("store_inventory")
    wh_df = await _cached("warehouse_inventory")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")
    open_orders_df = await _cached("open_orders")

    if sales_df is None or inv_df is None or sku_df is None:
        return {"error": "Required data not uploaded (need daily_sales, store_inventory, sku_ean_master)"}

    try:
        sales = _date_filter(sales_df.copy(), start_date, end_date, "day")
        inv = _date_filter(inv_df.copy(), start_date, end_date, "day")
        cat_list = _parse_list(categories)
        ch_list = _parse_list(channels)
        rg_list = _parse_list(regions)

        if ch_list:
            sales = _channel_filter(sales, ch_list)
            inv = _channel_filter(inv, ch_list)
        if rg_list:
            sales = _region_filter(sales, rg_list, store_df)
            inv = _region_filter(inv, rg_list, store_df)

        sales["day"] = pd.to_datetime(sales["day"])
        inv["day"] = pd.to_datetime(inv["day"])

        # ROS per store-SKU
        ros_calc = sales.groupby(["store_code", "sku"]).agg(
            total_qty=("quantity", "sum"),
            total_revenue=("revenue", "sum"),
            live_days=("day", "nunique"),
        ).reset_index()
        ros_calc["avg_daily_sales"] = (ros_calc["total_qty"] / ros_calc["live_days"].clip(lower=1)).round(4)

        # ASP per SKU
        if "mrp" in sku_df.columns:
            ros_calc["asp"] = ros_calc["sku"].map(sku_df.groupby("ean")["mrp"].first()).fillna(0)
        else:
            ros_calc["asp"] = np.where(
                ros_calc["total_qty"] > 0,
                (ros_calc["total_revenue"] / ros_calc["total_qty"]).round(2),
                0,
            )

        # Map style/size
        if "style" in sku_df.columns:
            ros_calc["style"] = ros_calc["sku"].map(sku_df.groupby("ean")["style"].first()).fillna("Unknown")
        else:
            ros_calc["style"] = "Unknown"
        if "size" in sku_df.columns:
            ros_calc["size"] = ros_calc["sku"].map(sku_df.groupby("ean")["size"].first()).fillna("-")
        else:
            ros_calc["size"] = "-"

        if cat_list:
            ros_calc = _category_filter(ros_calc, cat_list, style_df)

        # Current SOH
        latest_date = inv["day"].max()
        latest_inv = inv[inv["day"] == latest_date]
        soh = latest_inv.groupby(["store_code", "ean"])["quantity"].sum().reset_index()
        soh.columns = ["store_code", "sku", "current_soh"]
        ros_calc = ros_calc.merge(soh, on=["store_code", "sku"], how="left")
        ros_calc["current_soh"] = ros_calc["current_soh"].fillna(0).clip(lower=0)

        # Deduct in-transit / open orders from requirement
        ros_calc["in_transit_qty"] = 0
        if open_orders_df is not None and len(open_orders_df) > 0:
            oo = open_orders_df.copy()
            oo["order_quantity"] = pd.to_numeric(oo.get("order_quantity", pd.Series(dtype=float)), errors="coerce").fillna(0)
            # Only count non-delivered orders (open, confirmed, in_transit)
            if "status" in oo.columns:
                active_statuses = ["open", "confirmed", "in_transit", "shipped", "in-transit"]
                oo = oo[oo["status"].str.lower().isin(active_statuses)]
            in_transit = oo.groupby(["store_code", "sku_code"])["order_quantity"].sum().reset_index()
            in_transit.columns = ["store_code", "sku", "in_transit_qty"]
            ros_calc = ros_calc.merge(in_transit, on=["store_code", "sku"], how="left", suffixes=("", "_oo"))
            if "in_transit_qty_oo" in ros_calc.columns:
                ros_calc["in_transit_qty"] = ros_calc["in_transit_qty_oo"].fillna(0)
                ros_calc.drop(columns=["in_transit_qty_oo"], inplace=True)
            else:
                ros_calc["in_transit_qty"] = ros_calc["in_transit_qty"].fillna(0)

        # REP-09: Order Qty = (Cover Days x Avg Sales) - Current Stock - In Transit
        ros_calc["requirement"] = (ros_calc["avg_daily_sales"] * cover_days).round(0)
        ros_calc["raw_order_qty"] = (ros_calc["requirement"] - ros_calc["current_soh"] - ros_calc["in_transit_qty"]).clip(lower=0).round(0)

        # REP-10: Current stock > requirement -> 0
        # Already handled by clip(lower=0)

        # REP-11: MOQ rounding
        ros_calc["order_qty_moq"] = np.where(
            (ros_calc["raw_order_qty"] > 0) & (ros_calc["raw_order_qty"] < moq),
            moq,
            ros_calc["raw_order_qty"],
        )

        # REP-12: Pack size rounding
        if pack_size > 1:
            ros_calc["order_qty"] = np.where(
                ros_calc["order_qty_moq"] > 0,
                np.ceil(ros_calc["order_qty_moq"] / pack_size) * pack_size,
                0,
            )
        else:
            ros_calc["order_qty"] = ros_calc["order_qty_moq"]

        ros_calc["order_qty"] = ros_calc["order_qty"].astype(int)

        # REP-13: Warehouse stock availability
        wh_stock = {}
        warehouse_alert = []
        if wh_df is not None and len(wh_df) > 0:
            wh_inv = wh_df.copy()
            wh_inv["day"] = pd.to_datetime(wh_inv["day"])
            wh_latest = wh_inv[wh_inv["day"] == wh_inv["day"].max()]
            wh_stock_df = wh_latest.groupby("sku")["quantity"].sum().reset_index()
            wh_stock = dict(zip(wh_stock_df["sku"].astype(str), wh_stock_df["quantity"]))

            # Check per-SKU total demand vs warehouse stock
            sku_demand = ros_calc.groupby("sku")["order_qty"].sum().reset_index()
            for _, row in sku_demand.iterrows():
                sku_str = str(row["sku"])
                available = wh_stock.get(sku_str, 0)
                if row["order_qty"] > available:
                    warehouse_alert.append({
                        "sku": sku_str,
                        "total_demand": int(row["order_qty"]),
                        "warehouse_available": int(available),
                        "shortfall": int(row["order_qty"] - available),
                    })

            # Reduce order qty if warehouse insufficient
            ros_calc["wh_available"] = ros_calc["sku"].astype(str).map(wh_stock).fillna(0)
            # Pro-rata reduction per store based on ROS weight within each SKU
            for sku_val in ros_calc["sku"].unique():
                mask = ros_calc["sku"] == sku_val
                total_demand = ros_calc.loc[mask, "order_qty"].sum()
                avail = wh_stock.get(str(sku_val), 0)
                if total_demand > avail and total_demand > 0:
                    ratio = avail / total_demand
                    ros_calc.loc[mask, "order_qty"] = (ros_calc.loc[mask, "order_qty"] * ratio).round(0).astype(int)
        else:
            ros_calc["wh_available"] = 0

        # REP-14 & REP-15: Store allocation based on ROS and class
        # Get store classes
        store_classes = await _get_db().store_classes.find({}, {"_id": 0}).to_list(100)
        class_priorities = {c["code"]: c.get("priority", 99) for c in store_classes}
        assignments = await _get_db().store_class_assignments.find({}, {"_id": 0}).to_list(5000)
        store_class_map = {a["store_code"]: a["class_code"] for a in assignments}

        ros_calc["store_class"] = ros_calc["store_code"].map(store_class_map).fillna("C")
        ros_calc["class_priority"] = ros_calc["store_class"].map(class_priorities).fillna(99)

        # Allocation weight = ROS * class_weight (lower priority number = higher weight)
        max_pri = max(class_priorities.values()) if class_priorities else 3
        ros_calc["class_weight"] = (max_pri + 1 - ros_calc["class_priority"]).clip(lower=1)
        ros_calc["allocation_score"] = (ros_calc["avg_daily_sales"] * ros_calc["class_weight"]).round(2)

        ros_calc["po_value"] = (ros_calc["order_qty"] * ros_calc["asp"]).round(2)

        # Priority
        ros_calc["days_to_stockout"] = np.where(
            ros_calc["avg_daily_sales"] > 0,
            (ros_calc["current_soh"] / ros_calc["avg_daily_sales"]).round(1),
            999,
        )
        ros_calc["priority"] = pd.cut(
            ros_calc["days_to_stockout"].astype(float),
            bins=[-1, 0, 3, 7, 14, float("inf")],
            labels=["Stock-Out", "Critical", "High", "Medium", "Low"],
        ).astype(str)

        needs_order = ros_calc[ros_calc["order_qty"] > 0].copy()
        needs_order = needs_order.sort_values("days_to_stockout")

        # Summaries
        total_po = float(needs_order["po_value"].sum())
        total_units = int(needs_order["order_qty"].sum())

        by_store = needs_order.groupby("store_code").agg(
            sku_count=("sku", "nunique"),
            total_units=("order_qty", "sum"),
            total_value=("po_value", "sum"),
            store_class=("store_class", "first"),
        ).reset_index().sort_values("total_value", ascending=False)

        by_priority = needs_order.groupby("priority").agg(
            count=("sku", "count"),
            total_units=("order_qty", "sum"),
            total_value=("po_value", "sum"),
        ).reset_index()
        priority_order = {"Stock-Out": 0, "Critical": 1, "High": 2, "Medium": 3, "Low": 4}
        by_priority["sort_key"] = by_priority["priority"].map(priority_order)
        by_priority = by_priority.sort_values("sort_key").drop(columns=["sort_key"])

        detail_cols = [
            "sku", "style", "size", "store_code", "store_class",
            "avg_daily_sales", "current_soh", "in_transit_qty", "requirement",
            "raw_order_qty", "order_qty", "asp", "po_value",
            "allocation_score", "days_to_stockout", "priority",
        ]
        detail = needs_order[detail_cols].head(300)

        return {
            "summary": {
                "total_po_value": round(total_po, 2),
                "total_order_units": total_units,
                "skus_needing_order": int(needs_order["sku"].nunique()),
                "stores_needing_order": int(needs_order["store_code"].nunique()),
                "cover_days": cover_days,
                "moq": moq,
                "pack_size": pack_size,
                "total_in_transit": int(ros_calc["in_transit_qty"].sum()),
                "open_orders_source": "uploaded" if (open_orders_df is not None and len(open_orders_df) > 0) else "none",
            },
            "warehouse_alerts": warehouse_alert[:50],
            "by_priority": by_priority.round(2).fillna(0).to_dict("records"),
            "by_store": by_store.round(2).fillna(0).to_dict("records"),
            "detail": detail.round(2).fillna(0).to_dict("records"),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# =========================================================================
# ENDPOINT 3: IST — Inter-Store Transfer (REP-16 to REP-21)
# =========================================================================
@router.get("/ist")
async def get_ist_suggestions(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    overstock_doh_threshold: int = 30,
    understock_doh_threshold: int = 7,
):
    """
    REP-16: Overstocked store = DOH > 30 days
    REP-17: Understocked store = DOH < 7 days
    REP-18: Transfer qty = Min(overstock surplus, understock need)
    REP-19: Transfer cost — prioritize nearby stores (same region)
    REP-20: Multiple source stores — best fit selection
    REP-21: Transfer approval workflow (admin)
    """
    sales_df = await _cached("daily_sales")
    inv_df = await _cached("store_inventory")
    sku_df = await _cached("sku_ean_master")
    store_df = await _cached("store_master")
    style_df = await _cached("style_master")

    if sales_df is None or inv_df is None or sku_df is None:
        return {"error": "Required data not uploaded"}

    try:
        sales = _date_filter(sales_df.copy(), start_date, end_date, "day")
        inv = _date_filter(inv_df.copy(), start_date, end_date, "day")
        cat_list = _parse_list(categories)
        ch_list = _parse_list(channels)
        rg_list = _parse_list(regions)

        if ch_list:
            sales = _channel_filter(sales, ch_list)
            inv = _channel_filter(inv, ch_list)
        if rg_list:
            sales = _region_filter(sales, rg_list, store_df)
            inv = _region_filter(inv, rg_list, store_df)

        sales["day"] = pd.to_datetime(sales["day"])
        inv["day"] = pd.to_datetime(inv["day"])

        # ROS per store-SKU
        ros_calc = sales.groupby(["store_code", "sku"]).agg(
            total_qty=("quantity", "sum"),
            live_days=("day", "nunique"),
        ).reset_index()
        ros_calc["ros"] = (ros_calc["total_qty"] / ros_calc["live_days"].clip(lower=1)).round(4)

        # SOH
        latest_date = inv["day"].max()
        latest_inv = inv[inv["day"] == latest_date]
        soh = latest_inv.groupby(["store_code", "ean"])["quantity"].sum().reset_index()
        soh.columns = ["store_code", "sku", "soh"]

        doh = ros_calc.merge(soh, on=["store_code", "sku"], how="outer")
        doh["soh"] = doh["soh"].fillna(0)
        doh["ros"] = doh["ros"].fillna(0)
        doh["doh"] = np.where(doh["ros"] > 0, (doh["soh"] / doh["ros"]).round(1), np.where(doh["soh"] > 0, 9999, 0))

        # Style mapping
        if "style" in sku_df.columns:
            doh["style"] = doh["sku"].map(sku_df.groupby("ean")["style"].first()).fillna("Unknown")
        else:
            doh["style"] = "Unknown"
        if "size" in sku_df.columns:
            doh["size"] = doh["sku"].map(sku_df.groupby("ean")["size"].first()).fillna("-")
        else:
            doh["size"] = "-"

        if cat_list:
            doh = _category_filter(doh, cat_list, style_df)

        # Region mapping for transfer cost heuristic (REP-19)
        store_region = {}
        if store_df is not None and "store_code" in store_df.columns and "region" in store_df.columns:
            store_region = store_df.groupby("store_code")["region"].first().to_dict()
        doh["region"] = doh["store_code"].map(store_region).fillna("Unknown")

        # REP-16: Overstocked stores
        overstocked = doh[doh["doh"] > overstock_doh_threshold].copy()
        overstocked["surplus"] = (overstocked["soh"] - overstocked["ros"] * overstock_doh_threshold).clip(lower=0).round(0)

        # REP-17: Understocked stores
        understocked = doh[(doh["doh"] < understock_doh_threshold) & (doh["ros"] > 0)].copy()
        understocked["need"] = (understocked["ros"] * understock_doh_threshold - understocked["soh"]).clip(lower=0).round(0)

        # Generate IST suggestions
        transfers = []
        for _, under_row in understocked.iterrows():
            sku_val = under_row["sku"]
            need = under_row["need"]
            dest_store = under_row["store_code"]
            dest_region = under_row["region"]

            if need <= 0:
                continue

            # Find overstocked sources for this SKU (REP-20)
            sources = overstocked[overstocked["sku"] == sku_val].copy()
            if len(sources) == 0:
                continue

            # REP-19: Prioritize same region (lower cost)
            sources["same_region"] = (sources["region"] == dest_region).astype(int)
            sources = sources.sort_values(["same_region", "surplus"], ascending=[False, False])

            remaining_need = need
            for _, src_row in sources.iterrows():
                if remaining_need <= 0:
                    break
                transfer_qty = min(float(src_row["surplus"]), float(remaining_need))
                if transfer_qty <= 0:
                    continue
                transfers.append({
                    "transfer_id": str(uuid.uuid4())[:8],
                    "sku": str(sku_val),
                    "style": str(under_row.get("style", "Unknown")),
                    "size": str(under_row.get("size", "-")),
                    "source_store": str(src_row["store_code"]),
                    "source_region": str(src_row["region"]),
                    "source_doh": float(src_row["doh"]),
                    "source_surplus": int(src_row["surplus"]),
                    "dest_store": str(dest_store),
                    "dest_region": str(dest_region),
                    "dest_doh": float(under_row["doh"]),
                    "dest_need": int(need),
                    "transfer_qty": int(transfer_qty),
                    "same_region": bool(src_row["same_region"]),
                    "status": "pending",
                })
                remaining_need -= transfer_qty

        # Summary
        total_transfers = len(transfers)
        total_units_transfer = sum(t["transfer_qty"] for t in transfers)
        same_region_pct = (
            sum(1 for t in transfers if t["same_region"]) / max(total_transfers, 1) * 100
        )

        overstocked_stores = int(overstocked["store_code"].nunique())
        understocked_stores = int(understocked["store_code"].nunique())

        # Existing pending transfers from DB (REP-21)
        pending_transfers = await _get_db().ist_transfers.find(
            {"status": "pending"}, {"_id": 0}
        ).to_list(500)

        return {
            "summary": {
                "overstocked_stores": overstocked_stores,
                "understocked_stores": understocked_stores,
                "total_suggested_transfers": total_transfers,
                "total_transfer_units": total_units_transfer,
                "same_region_pct": round(same_region_pct, 1),
                "overstock_threshold_doh": overstock_doh_threshold,
                "understock_threshold_doh": understock_doh_threshold,
            },
            "transfers": transfers[:200],
            "pending_approvals": pending_transfers,
            "overstocked_detail": overstocked[["store_code", "sku", "style", "soh", "ros", "doh", "surplus", "region"]].head(100).round(2).fillna(0).to_dict("records"),
            "understocked_detail": understocked[["store_code", "sku", "style", "soh", "ros", "doh", "need", "region"]].head(100).round(2).fillna(0).to_dict("records"),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# REP-21: IST Transfer approval/rejection
@router.post("/ist/action")
async def ist_transfer_action(body: ISTTransferAction):
    """Approve or reject an IST transfer."""
    db = _get_db()
    now = datetime.now(timezone.utc).isoformat()
    result = await db.ist_transfers.update_one(
        {"transfer_id": body.transfer_id},
        {"$set": {
            "status": "approved" if body.action == "approve" else "rejected",
            "action_notes": body.notes,
            "actioned_at": now,
        }},
    )
    if result.matched_count == 0:
        # Save as new if not found
        await db.ist_transfers.insert_one({
            "transfer_id": body.transfer_id,
            "status": "approved" if body.action == "approve" else "rejected",
            "action_notes": body.notes,
            "actioned_at": now,
        })
    return {"status": "ok", "transfer_id": body.transfer_id, "action": body.action}


@router.post("/ist/bulk-action")
async def ist_bulk_action(body: BulkOrderAction):
    """Bulk approve/reject IST transfers."""
    db = _get_db()
    now = datetime.now(timezone.utc).isoformat()
    status = "approved" if body.action == "approve" else "rejected"
    updated = 0
    for tid in body.order_ids:
        await db.ist_transfers.update_one(
            {"transfer_id": tid},
            {"$set": {"status": status, "action_notes": body.notes, "actioned_at": now}},
            upsert=True,
        )
        updated += 1
    return {"status": "ok", "updated": updated, "action": body.action}


# =========================================================================
# ENDPOINT 4: Replenishment Run (REP-22 to REP-27)
# =========================================================================
@router.post("/run")
async def run_replenishment(
    lead_time_days: int = None,
    safety_days: int = None,
    cover_days: int = None,
    moq: int = 1,
    pack_size: int = 1,
):
    """
    REP-22: Run replenishment algorithm -> generate orders
    REP-23: Pre vs Post comparison
    REP-24: Stock-out reduction %
    REP-25: Fill rate improvement
    REP-26: DOH improvement
    REP-27: Warehouse stock exhaustion alert
    """
    cfg = await _get_config()
    if lead_time_days is None:
        lead_time_days = cfg.get("lead_time_days", 14)
    if safety_days is None:
        safety_days = cfg.get("safety_days", cfg.get("cover_days", 7))
    if cover_days is None:
        cover_days = lead_time_days + safety_days

    sales_df = await _cached("daily_sales")
    inv_df = await _cached("store_inventory")
    wh_df = await _cached("warehouse_inventory")
    sku_df = await _cached("sku_ean_master")

    if sales_df is None or inv_df is None or sku_df is None:
        return {"error": "Required data not uploaded"}

    try:
        sales = sales_df.copy()
        inv = inv_df.copy()
        sales["day"] = pd.to_datetime(sales["day"])
        inv["day"] = pd.to_datetime(inv["day"])

        # ROS per store-SKU
        ros_calc = sales.groupby(["store_code", "sku"]).agg(
            total_qty=("quantity", "sum"),
            live_days=("day", "nunique"),
        ).reset_index()
        ros_calc["ros"] = (ros_calc["total_qty"] / ros_calc["live_days"].clip(lower=1)).round(4)

        # ASP
        if "mrp" in sku_df.columns:
            ros_calc["asp"] = ros_calc["sku"].map(sku_df.groupby("ean")["mrp"].first()).fillna(0)
        else:
            ros_calc["asp"] = 0

        # SOH
        latest_date = inv["day"].max()
        latest_inv = inv[inv["day"] == latest_date]
        soh = latest_inv.groupby(["store_code", "ean"])["quantity"].sum().reset_index()
        soh.columns = ["store_code", "sku", "current_soh"]
        plan = ros_calc.merge(soh, on=["store_code", "sku"], how="left")
        plan["current_soh"] = plan["current_soh"].fillna(0).clip(lower=0)

        # ===== PRE-METRICS =====
        plan["pre_doh"] = np.where(plan["ros"] > 0, (plan["current_soh"] / plan["ros"]).round(1), 0)
        plan["pre_stockout"] = (plan["current_soh"] == 0) & (plan["ros"] > 0)
        total_store_skus = len(plan)
        pre_stockout_count = int(plan["pre_stockout"].sum())
        pre_fill_rate = round((1 - pre_stockout_count / max(total_store_skus, 1)) * 100, 2)
        pre_avg_doh = round(float(plan[plan["ros"] > 0]["pre_doh"].mean()), 1) if len(plan[plan["ros"] > 0]) > 0 else 0

        # ===== GENERATE ORDERS =====
        plan["safety_stock"] = (plan["ros"] * safety_days).round(0)
        plan["requirement"] = (plan["ros"] * cover_days).round(0)
        plan["order_qty"] = (plan["requirement"] - plan["current_soh"]).clip(lower=0).round(0)

        # MOQ & pack size
        plan["order_qty"] = np.where(
            (plan["order_qty"] > 0) & (plan["order_qty"] < moq),
            moq,
            plan["order_qty"],
        )
        if pack_size > 1:
            plan["order_qty"] = np.where(
                plan["order_qty"] > 0,
                np.ceil(plan["order_qty"] / pack_size) * pack_size,
                0,
            )
        plan["order_qty"] = plan["order_qty"].astype(int)

        # REP-27: Warehouse stock check
        wh_stock = {}
        wh_alerts = []
        if wh_df is not None and len(wh_df) > 0:
            wh = wh_df.copy()
            wh["day"] = pd.to_datetime(wh["day"])
            wh_latest = wh[wh["day"] == wh["day"].max()]
            wh_agg = wh_latest.groupby("sku")["quantity"].sum()
            wh_stock = wh_agg.to_dict()

            sku_demand = plan.groupby("sku")["order_qty"].sum()
            for sku_val, demand in sku_demand.items():
                avail = wh_stock.get(str(sku_val), wh_stock.get(sku_val, 0))
                remaining = avail - demand
                if remaining < 0:
                    wh_alerts.append({
                        "sku": str(sku_val),
                        "demand": int(demand),
                        "warehouse_stock": int(avail),
                        "shortfall": int(abs(remaining)),
                        "exhausted": avail <= 0,
                    })

            # Reduce orders proportionally where warehouse can't fulfill
            for sku_val in plan["sku"].unique():
                mask = plan["sku"] == sku_val
                total_demand = plan.loc[mask, "order_qty"].sum()
                avail = wh_stock.get(str(sku_val), wh_stock.get(sku_val, 0))
                if total_demand > avail and total_demand > 0:
                    ratio = avail / total_demand
                    plan.loc[mask, "order_qty"] = (plan.loc[mask, "order_qty"] * ratio).round(0).astype(int)

        plan["po_value"] = (plan["order_qty"] * plan["asp"]).round(2)

        # ===== POST-METRICS =====
        plan["post_soh"] = plan["current_soh"] + plan["order_qty"]
        plan["post_doh"] = np.where(plan["ros"] > 0, (plan["post_soh"] / plan["ros"]).round(1), 0)
        plan["post_stockout"] = (plan["post_soh"] == 0) & (plan["ros"] > 0)
        post_stockout_count = int(plan["post_stockout"].sum())
        post_fill_rate = round((1 - post_stockout_count / max(total_store_skus, 1)) * 100, 2)
        post_avg_doh = round(float(plan[plan["ros"] > 0]["post_doh"].mean()), 1) if len(plan[plan["ros"] > 0]) > 0 else 0

        # REP-24: Stock-out reduction %
        stockout_reduction = round(
            (pre_stockout_count - post_stockout_count) / max(pre_stockout_count, 1) * 100, 2
        )
        # REP-25: Fill rate improvement
        fill_rate_improvement = round(post_fill_rate - pre_fill_rate, 2)
        # REP-26: DOH improvement
        doh_improvement = round(post_avg_doh - pre_avg_doh, 1)

        orders_generated = plan[plan["order_qty"] > 0].copy()
        total_po = float(orders_generated["po_value"].sum())
        total_units = int(orders_generated["order_qty"].sum())

        # Save run to DB
        run_id = str(uuid.uuid4())[:12]
        run_doc = {
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "config": {
                "lead_time_days": lead_time_days,
                "safety_days": safety_days,
                "cover_days": cover_days,
                "moq": moq,
                "pack_size": pack_size,
            },
            "pre_metrics": {
                "stockout_count": pre_stockout_count,
                "fill_rate": pre_fill_rate,
                "avg_doh": pre_avg_doh,
            },
            "post_metrics": {
                "stockout_count": post_stockout_count,
                "fill_rate": post_fill_rate,
                "avg_doh": post_avg_doh,
            },
            "improvements": {
                "stockout_reduction_pct": stockout_reduction,
                "fill_rate_improvement": fill_rate_improvement,
                "doh_improvement": doh_improvement,
            },
            "total_orders": len(orders_generated),
            "total_units": total_units,
            "total_po_value": round(total_po, 2),
            "warehouse_alerts": wh_alerts[:50],
            "status": "pending_approval",
        }
        await _get_db().replenishment_runs.insert_one(run_doc)

        # Save individual orders
        order_docs = []
        for _, row in orders_generated.head(500).iterrows():
            order_docs.append({
                "order_id": str(uuid.uuid4())[:8],
                "run_id": run_id,
                "sku": str(row["sku"]),
                "store_code": str(row["store_code"]),
                "order_qty": int(row["order_qty"]),
                "asp": float(row["asp"]),
                "po_value": float(row["po_value"]),
                "pre_soh": int(row["current_soh"]),
                "post_soh": int(row["post_soh"]),
                "ros": float(row["ros"]),
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        if order_docs:
            await _get_db().replenishment_orders.insert_many(order_docs)

        return {
            "run_id": run_id,
            "pre_metrics": run_doc["pre_metrics"],
            "post_metrics": run_doc["post_metrics"],
            "improvements": run_doc["improvements"],
            "total_orders": len(orders_generated),
            "total_units": total_units,
            "total_po_value": round(total_po, 2),
            "warehouse_alerts": wh_alerts[:50],
            "config": run_doc["config"],
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@router.get("/runs")
async def list_replenishment_runs():
    """List all replenishment runs."""
    runs = await _get_db().replenishment_runs.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"runs": runs}


# =========================================================================
# ENDPOINT 5: Orders Dashboard (REP-28 to REP-32)
# =========================================================================
@router.get("/orders")
async def list_orders(
    status: str = None,
    run_id: str = None,
    limit: int = 200,
):
    """REP-28: View pending orders."""
    query = {}
    if status:
        query["status"] = status
    if run_id:
        query["run_id"] = run_id
    orders = await _get_db().replenishment_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    # Summary counts
    all_orders = await _get_db().replenishment_orders.find({}, {"_id": 0, "status": 1}).to_list(10000)
    counts = {"pending": 0, "approved": 0, "rejected": 0}
    for o in all_orders:
        s = o.get("status", "pending")
        if s in counts:
            counts[s] += 1

    return {"orders": orders, "counts": counts, "total": len(orders)}


# REP-29: Approve/Reject individual order
@router.post("/orders/action")
async def order_action(body: OrderAction):
    """Approve or reject a single replenishment order."""
    db = _get_db()
    now = datetime.now(timezone.utc).isoformat()
    new_status = "approved" if body.action == "approve" else "rejected"
    result = await db.replenishment_orders.update_one(
        {"order_id": body.order_id},
        {"$set": {"status": new_status, "action_notes": body.notes, "actioned_at": now}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"status": "ok", "order_id": body.order_id, "new_status": new_status}


# REP-30: Bulk approve/reject
@router.post("/orders/bulk-action")
async def bulk_order_action(body: BulkOrderAction):
    """Bulk approve or reject replenishment orders."""
    db = _get_db()
    now = datetime.now(timezone.utc).isoformat()
    new_status = "approved" if body.action == "approve" else "rejected"
    updated = 0
    for oid in body.order_ids:
        result = await db.replenishment_orders.update_one(
            {"order_id": oid},
            {"$set": {"status": new_status, "action_notes": body.notes, "actioned_at": now}},
        )
        if result.modified_count > 0:
            updated += 1
    return {"status": "ok", "updated": updated, "total_requested": len(body.order_ids), "action": body.action}


# REP-31: Export is handled on the frontend (CSV download from data)

# REP-32: Schedule auto-replenishment
@router.get("/schedule")
async def get_schedule():
    """Get auto-replenishment schedule config."""
    doc = await _get_db().replenishment_schedule.find_one({"_id": "main"}, {"_id": 0})
    if not doc:
        return {
            "enabled": False,
            "frequency": "weekly",
            "day_of_week": 1,
            "lead_time_days": 14,
            "safety_days": 7,
        }
    return doc


@router.post("/schedule")
async def set_schedule(body: ScheduleConfig):
    """Save auto-replenishment schedule config."""
    db = _get_db()
    doc = body.model_dump()
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.replenishment_schedule.update_one(
        {"_id": "main"},
        {"$set": doc},
        upsert=True,
    )
    return {"status": "ok", "schedule": doc}
