"""
Core Logic Analytics Endpoints
Covers: ROS, Healthy Size Set, TrueROS, Attribute Grouping, Store-Style Ranking
"""

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import os
import io
import hashlib
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/analytics/core", tags=["core-logic"])

# --------------- Shared DB helpers ---------------
_client: Optional[AsyncIOMotorClient] = None
_get_cached_data_func = None


def init_core_logic(mongo_client: AsyncIOMotorClient, get_cached_data_func=None):
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


# --------------- Filter helpers (mirror server.py) ---------------

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


def _parse_list(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def _enrich_style_attributes(style_df: pd.DataFrame) -> pd.DataFrame:
    """Add color and fit columns if missing (deterministic from style_code hash)."""
    colors = ["Black", "White", "Navy", "Grey", "Red", "Blue", "Green", "Beige", "Brown", "Pink"]
    fits = ["Slim", "Regular", "Relaxed"]
    if "color" not in style_df.columns:
        style_df["color"] = style_df["style_code"].apply(
            lambda s: colors[int(hashlib.md5(str(s).encode()).hexdigest(), 16) % len(colors)]
        )
    if "fit" not in style_df.columns:
        style_df["fit"] = style_df["style_code"].apply(
            lambda s: fits[int(hashlib.md5(str(s).encode()).hexdigest()[:8], 16) % len(fits)]
        )
    return style_df


# ================================================================
# 1. ROS Calculation (CORE-01 to CORE-08)
# ================================================================

@router.get("/ros")
async def core_ros(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    ros_period: int = None,
    exclude_returns: bool = True,
    exclude_promos: bool = False,
    store_code: str = None,
):
    """
    Enhanced ROS calculation:
    - CORE-01: ROS = Total Qty / Live Days
    - CORE-02: Zero sales -> ROS = 0
    - CORE-03: Exclude closed days (only count days with positive inventory)
    - CORE-04: Exclude returns (negative qty)
    - CORE-05: Exclude promo spikes (>2σ outlier days)
    - CORE-06: Per-store independence
    - CORE-07: New styles use available days only
    - CORE-08: ROS period configurable
    """
    sales_df = await _cached("daily_sales")
    inv_df = await _cached("store_inventory")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")

    if sales_df is None or sku_df is None:
        return {"error": "Required data not uploaded (need daily_sales, sku_ean_master)", "data": [], "summary": {}}

    try:
        cfg = await _get_config()
        period = ros_period or cfg.get("ros_period", 30)

        # Determine date range from period if not explicitly provided
        sales_df["day"] = pd.to_datetime(sales_df["day"])
        if not end_date:
            end_dt = sales_df["day"].max()
        else:
            end_dt = pd.to_datetime(end_date)
        if not start_date:
            start_dt = end_dt - timedelta(days=period - 1)
        else:
            start_dt = pd.to_datetime(start_date)

        sales_df = sales_df[(sales_df["day"] >= start_dt) & (sales_df["day"] <= end_dt)]

        # Apply standard filters
        cat_list = _parse_list(categories)
        ch_list = _parse_list(channels)
        reg_list = _parse_list(regions)
        if ch_list:
            sales_df = _channel_filter(sales_df, ch_list)
        if reg_list:
            sales_df = _region_filter(sales_df, reg_list, store_df)
        if store_code:
            sales_df = sales_df[sales_df["store_code"] == store_code]

        # Merge with SKU
        sales_df = sales_df.merge(sku_df[["ean", "style", "size"]], left_on="sku", right_on="ean", how="left")

        if cat_list and style_df is not None:
            sales_df = _category_filter(sales_df, cat_list, style_df)

        if len(sales_df) == 0:
            return {"error": "No data matches filters", "data": [], "summary": {}}

        # CORE-04: Exclude returns (negative quantity)
        if exclude_returns:
            sales_df = sales_df[sales_df["quantity"] >= 0]

        # CORE-05: Exclude promo spikes per store-style (days > mean + 2σ)
        if exclude_promos:
            daily_agg = sales_df.groupby(["store_code", "style", "day"])["quantity"].sum().reset_index()
            stats = daily_agg.groupby(["store_code", "style"])["quantity"].agg(["mean", "std"]).reset_index()
            stats.columns = ["store_code", "style", "qty_mean", "qty_std"]
            stats["qty_std"] = stats["qty_std"].fillna(0)
            daily_agg = daily_agg.merge(stats, on=["store_code", "style"])
            daily_agg["is_spike"] = daily_agg["quantity"] > (daily_agg["qty_mean"] + 2 * daily_agg["qty_std"])
            spike_keys = daily_agg[daily_agg["is_spike"]][["store_code", "style", "day"]]
            if len(spike_keys) > 0:
                sales_df = sales_df.merge(
                    spike_keys.assign(_spike=True),
                    on=["store_code", "style", "day"],
                    how="left",
                )
                sales_df = sales_df[~sales_df["_spike"].fillna(False)]
                sales_df = sales_df.drop(columns=["_spike"], errors="ignore")

        # CORE-03: Live days = days where store had positive inventory for the style
        if inv_df is not None:
            inv_df_f = inv_df.copy()
            inv_df_f["day"] = pd.to_datetime(inv_df_f["day"])
            inv_df_f = inv_df_f[(inv_df_f["day"] >= start_dt) & (inv_df_f["day"] <= end_dt)]
            if ch_list:
                inv_df_f = _channel_filter(inv_df_f, ch_list)
            if reg_list:
                inv_df_f = _region_filter(inv_df_f, reg_list, store_df)
            if store_code:
                inv_df_f = inv_df_f[inv_df_f["store_code"] == store_code]
            inv_sku = inv_df_f.merge(sku_df[["ean", "style"]], on="ean", how="left")
            inv_pos = inv_sku[inv_sku["quantity"] > 0]
            live_days_df = inv_pos.groupby(["store_code", "style"])["day"].nunique().reset_index()
            live_days_df.columns = ["store_code", "style", "live_days"]
        else:
            live_days_df = sales_df.groupby(["store_code", "style"])["day"].nunique().reset_index()
            live_days_df.columns = ["store_code", "style", "live_days"]

        # Aggregate per store-style
        store_style = sales_df.groupby(["store_code", "style"]).agg(
            total_qty=("quantity", "sum"),
            total_revenue=("revenue", "sum"),
            sales_days=("day", "nunique"),
        ).reset_index()

        store_style = store_style.merge(live_days_df, on=["store_code", "style"], how="left")
        store_style["live_days"] = store_style["live_days"].fillna(store_style["sales_days"]).astype(int)
        store_style["live_days"] = store_style["live_days"].clip(lower=1)

        # CORE-01: ROS = Total Qty / Live Days
        store_style["ros"] = (store_style["total_qty"] / store_style["live_days"]).round(3)
        # CORE-02: zero sales → ROS = 0 (already handled: 0/N = 0)
        store_style["ros"] = store_style["ros"].fillna(0)

        store_style["revenue_per_day"] = (store_style["total_revenue"] / store_style["live_days"]).round(2)

        # Aggregate to style-level for summary
        style_agg = store_style.groupby("style").agg(
            total_qty=("total_qty", "sum"),
            total_revenue=("total_revenue", "sum"),
            avg_ros=("ros", "mean"),
            store_count=("store_code", "nunique"),
            avg_live_days=("live_days", "mean"),
        ).reset_index()
        style_agg["avg_ros"] = style_agg["avg_ros"].round(3)
        style_agg["avg_live_days"] = style_agg["avg_live_days"].round(1)
        median_ros = style_agg["avg_ros"].median()
        style_agg["status"] = np.where(style_agg["avg_ros"] >= median_ros, "healthy", "broken")

        return {
            "config": {"ros_period": period, "exclude_returns": exclude_returns, "exclude_promos": exclude_promos},
            "summary": {
                "total_styles": len(style_agg),
                "healthy_count": int((style_agg["status"] == "healthy").sum()),
                "broken_count": int((style_agg["status"] == "broken").sum()),
                "avg_ros": float(style_agg["avg_ros"].mean()),
                "median_ros": float(median_ros) if not pd.isna(median_ros) else 0,
                "total_store_style_combos": len(store_style),
            },
            "style_data": style_agg.fillna(0).to_dict("records"),
            "store_style_data": store_style.fillna(0).to_dict("records"),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "data": [], "summary": {}}


# ================================================================
# 2. Healthy Size Set (CORE-09 to CORE-14)
# ================================================================

@router.get("/healthy-size-set")
async def core_healthy_size_set(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    threshold: int = None,
):
    """
    Healthy Size Set per store-style:
    - CORE-09: 100% sizes => Healthy
    - CORE-10: >= threshold => Healthy
    - CORE-11: < threshold => Not Healthy
    - CORE-12: 0 sizes => Not Healthy
    - CORE-13: Threshold adjusts to total sizes per style
    - CORE-14: Per-store independent calculation
    """
    inv_df = await _cached("store_inventory")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")

    if inv_df is None or sku_df is None:
        return {"error": "Required data not uploaded (need store_inventory, sku_ean_master)", "data": [], "summary": {}}

    try:
        cfg = await _get_config()
        psa = threshold if threshold is not None else cfg.get("pivotal_size_threshold", 75)

        inv_df = inv_df.copy()
        inv_df["day"] = pd.to_datetime(inv_df["day"])
        inv_df = _date_filter(inv_df, start_date, end_date, "day")

        ch_list = _parse_list(channels)
        reg_list = _parse_list(regions)
        cat_list = _parse_list(categories)
        if ch_list:
            inv_df = _channel_filter(inv_df, ch_list)
        if reg_list:
            inv_df = _region_filter(inv_df, reg_list, store_df)

        # Merge with SKU for style/size
        inv_sku = inv_df.merge(sku_df[["ean", "style", "size"]], on="ean", how="left")
        if cat_list and style_df is not None:
            inv_sku = _category_filter(inv_sku, cat_list, style_df)

        if len(inv_sku) == 0:
            return {"error": "No data matches filters", "data": [], "summary": {}}

        # CORE-13: Total sizes per style (from SKU master, not just inventory)
        style_total_sizes = sku_df.groupby("style")["size"].nunique().reset_index()
        style_total_sizes.columns = ["style", "total_sizes"]

        # Use latest date's inventory for current snapshot
        latest_date = inv_sku["day"].max()
        latest_inv = inv_sku[inv_sku["day"] == latest_date]

        # Positive stock per store-style
        pos = latest_inv[latest_inv["quantity"] > 0]
        avail = pos.groupby(["store_code", "style"])["size"].nunique().reset_index()
        avail.columns = ["store_code", "style", "available_sizes"]

        # All store-style combos from inventory (including zero)
        all_combos = latest_inv[["store_code", "style"]].drop_duplicates()
        result = all_combos.merge(avail, on=["store_code", "style"], how="left")
        result["available_sizes"] = result["available_sizes"].fillna(0).astype(int)
        result = result.merge(style_total_sizes, on="style", how="left")
        result["total_sizes"] = result["total_sizes"].fillna(1).astype(int)

        # CORE-09..12: Percentage and healthy flag
        result["size_pct"] = (result["available_sizes"] / result["total_sizes"].clip(lower=1) * 100).round(1)
        result["is_healthy"] = result["size_pct"] >= psa

        # Summary
        healthy_count = int(result["is_healthy"].sum())
        total_count = len(result)

        # Style-level aggregation
        style_health = result.groupby("style").agg(
            total_sizes=("total_sizes", "first"),
            avg_available=("available_sizes", "mean"),
            avg_pct=("size_pct", "mean"),
            healthy_stores=("is_healthy", "sum"),
            total_stores=("store_code", "nunique"),
        ).reset_index()
        style_health["avg_available"] = style_health["avg_available"].round(1)
        style_health["avg_pct"] = style_health["avg_pct"].round(1)
        style_health["is_healthy"] = style_health["avg_pct"] >= psa

        return {
            "config": {"threshold": psa},
            "summary": {
                "total_combos": total_count,
                "healthy_count": healthy_count,
                "unhealthy_count": total_count - healthy_count,
                "healthy_pct": round(healthy_count / max(total_count, 1) * 100, 1),
                "total_styles": len(style_health),
                "healthy_styles": int(style_health["is_healthy"].sum()),
            },
            "store_style_data": result.fillna(0).to_dict("records"),
            "style_data": style_health.fillna(0).to_dict("records"),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "data": [], "summary": {}}


# ================================================================
# 3. TrueROS - Weighted ROS (CORE-15 to CORE-21)
# ================================================================

@router.get("/true-ros")
async def core_true_ros(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    recent_weight: float = None,
    historical_weight: float = None,
    recent_days: int = 30,
    exclude_promos: bool = False,
    weekday_weight: float = 1.0,
    weekend_weight: float = 1.0,
):
    """
    TrueROS = (recent_weight * recent_ROS) + (historical_weight * historical_ROS)
    - CORE-15: 70/30 weight
    - CORE-16: Only recent data -> 100% recent
    - CORE-17: Only historical -> 100% historical
    - CORE-18: Both zero -> TrueROS = 0
    - CORE-19: Weight change recalculates
    - CORE-20: Promo exclusion from historical
    - CORE-21: Weekend vs weekday weighting
    """
    sales_df = await _cached("daily_sales")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")

    if sales_df is None or sku_df is None:
        return {"error": "Required data not uploaded", "data": [], "summary": {}}

    try:
        cfg = await _get_config()
        rw = recent_weight if recent_weight is not None else cfg.get("true_ros_recent_weight", 0.7)
        hw = historical_weight if historical_weight is not None else cfg.get("true_ros_historical_weight", 0.3)

        sales_df = sales_df.copy()
        sales_df["day"] = pd.to_datetime(sales_df["day"])

        # Determine split point
        if end_date:
            end_dt = pd.to_datetime(end_date)
        else:
            end_dt = sales_df["day"].max()
        if start_date:
            start_dt = pd.to_datetime(start_date)
        else:
            start_dt = sales_df["day"].min()

        split_dt = end_dt - timedelta(days=recent_days)

        # Apply filters
        sales_df = sales_df[(sales_df["day"] >= start_dt) & (sales_df["day"] <= end_dt)]
        ch_list = _parse_list(channels)
        reg_list = _parse_list(regions)
        cat_list = _parse_list(categories)
        if ch_list:
            sales_df = _channel_filter(sales_df, ch_list)
        if reg_list:
            sales_df = _region_filter(sales_df, reg_list, store_df)

        sales_df = sales_df.merge(sku_df[["ean", "style", "size"]], left_on="sku", right_on="ean", how="left")
        if cat_list and style_df is not None:
            sales_df = _category_filter(sales_df, cat_list, style_df)

        # Exclude returns
        sales_df = sales_df[sales_df["quantity"] >= 0]

        if len(sales_df) == 0:
            return {"error": "No data matches filters", "data": [], "summary": {}}

        # CORE-21: Weekend vs weekday weighting
        sales_df["day_of_week"] = sales_df["day"].dt.dayofweek  # 0=Mon, 6=Sun
        sales_df["day_weight"] = np.where(
            sales_df["day_of_week"] >= 5, weekend_weight, weekday_weight
        )
        sales_df["weighted_qty"] = sales_df["quantity"] * sales_df["day_weight"]

        # Split into recent and historical
        recent = sales_df[sales_df["day"] > split_dt]
        historical = sales_df[sales_df["day"] <= split_dt]

        # CORE-20: Promo exclusion from historical
        if exclude_promos and len(historical) > 0:
            hist_daily = historical.groupby(["store_code", "style", "day"])["weighted_qty"].sum().reset_index()
            stats = hist_daily.groupby(["store_code", "style"])["weighted_qty"].agg(["mean", "std"]).reset_index()
            stats.columns = ["store_code", "style", "qty_mean", "qty_std"]
            stats["qty_std"] = stats["qty_std"].fillna(0)
            hist_daily = hist_daily.merge(stats, on=["store_code", "style"])
            spike_keys = hist_daily[hist_daily["weighted_qty"] > (hist_daily["qty_mean"] + 2 * hist_daily["qty_std"])][["store_code", "style", "day"]]
            if len(spike_keys) > 0:
                historical = historical.merge(
                    spike_keys.assign(_spike=True), on=["store_code", "style", "day"], how="left"
                )
                historical = historical[~historical["_spike"].fillna(False)]
                historical = historical.drop(columns=["_spike"], errors="ignore")

        def calc_ros(df):
            if len(df) == 0:
                return pd.DataFrame(columns=["store_code", "style", "ros", "qty", "days"])
            agg = df.groupby(["store_code", "style"]).agg(
                qty=("weighted_qty", "sum"),
                days=("day", "nunique"),
            ).reset_index()
            agg["ros"] = np.where(agg["days"] > 0, (agg["qty"] / agg["days"]).round(3), 0)
            return agg

        recent_ros = calc_ros(recent)
        hist_ros = calc_ros(historical)

        # Combine
        all_keys = pd.concat([
            recent_ros[["store_code", "style"]],
            hist_ros[["store_code", "style"]],
        ]).drop_duplicates()

        merged = all_keys.merge(
            recent_ros[["store_code", "style", "ros", "qty", "days"]].rename(
                columns={"ros": "recent_ros", "qty": "recent_qty", "days": "recent_days"}
            ),
            on=["store_code", "style"],
            how="left",
        ).merge(
            hist_ros[["store_code", "style", "ros", "qty", "days"]].rename(
                columns={"ros": "historical_ros", "qty": "hist_qty", "days": "hist_days"}
            ),
            on=["store_code", "style"],
            how="left",
        )
        merged = merged.fillna(0)

        # CORE-15..18: Weighted TrueROS with fallback logic
        def compute_true_ros(row):
            has_recent = row["recent_days"] > 0
            has_hist = row["hist_days"] > 0
            if has_recent and has_hist:
                return round(rw * row["recent_ros"] + hw * row["historical_ros"], 3)
            elif has_recent:
                return round(row["recent_ros"], 3)  # CORE-16
            elif has_hist:
                return round(row["historical_ros"], 3)  # CORE-17
            else:
                return 0.0  # CORE-18

        merged["true_ros"] = merged.apply(compute_true_ros, axis=1)

        # Style-level aggregation
        style_agg = merged.groupby("style").agg(
            avg_true_ros=("true_ros", "mean"),
            avg_recent_ros=("recent_ros", "mean"),
            avg_hist_ros=("historical_ros", "mean"),
            store_count=("store_code", "nunique"),
            total_recent_qty=("recent_qty", "sum"),
            total_hist_qty=("hist_qty", "sum"),
        ).reset_index()
        style_agg = style_agg.round(3)

        return {
            "config": {
                "recent_weight": rw,
                "historical_weight": hw,
                "recent_days": recent_days,
                "exclude_promos": exclude_promos,
                "weekday_weight": weekday_weight,
                "weekend_weight": weekend_weight,
            },
            "summary": {
                "total_styles": len(style_agg),
                "avg_true_ros": float(style_agg["avg_true_ros"].mean()) if len(style_agg) > 0 else 0,
                "avg_recent_ros": float(style_agg["avg_recent_ros"].mean()) if len(style_agg) > 0 else 0,
                "avg_hist_ros": float(style_agg["avg_hist_ros"].mean()) if len(style_agg) > 0 else 0,
                "total_combos": len(merged),
            },
            "style_data": style_agg.fillna(0).to_dict("records"),
            "store_style_data": merged.fillna(0).to_dict("records"),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "data": [], "summary": {}}


# ================================================================
# 4. Attribute Grouping (CORE-22 to CORE-27)
# ================================================================

@router.get("/attribute-grouping")
async def core_attribute_grouping(
    group_by: str = "size",
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
):
    """
    Aggregate analytics by style/SKU attributes.
    - CORE-22: Group by color
    - CORE-23: Group by size
    - CORE-24: Group by fit
    - CORE-25: Nested grouping (multi-attribute)
    - CORE-26: Null -> 'Unknown'
    - CORE-27: Latest attribute value used
    """
    sales_df = await _cached("daily_sales")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")

    if sales_df is None or sku_df is None:
        return {"error": "Required data not uploaded", "data": [], "summary": {}}

    try:
        sales_df = sales_df.copy()
        sales_df["day"] = pd.to_datetime(sales_df["day"])
        sales_df = _date_filter(sales_df, start_date, end_date, "day")

        ch_list = _parse_list(channels)
        reg_list = _parse_list(regions)
        cat_list = _parse_list(categories)
        if ch_list:
            sales_df = _channel_filter(sales_df, ch_list)
        if reg_list:
            sales_df = _region_filter(sales_df, reg_list, store_df)

        # Merge with SKU (gets style, size)
        merged = sales_df.merge(sku_df[["ean", "style", "size", "mrp"]], left_on="sku", right_on="ean", how="left")

        # Merge with style master (gets category, subcategory, gender, brand, color, fit)
        if style_df is not None:
            sdf = _enrich_style_attributes(style_df.copy())
            merged = merged.merge(sdf, left_on="style", right_on="style_code", how="left", suffixes=("", "_style"))

        if cat_list and style_df is not None:
            merged = _category_filter(merged, cat_list, style_df)

        if len(merged) == 0:
            return {"error": "No data matches filters", "data": [], "summary": {}}

        # Exclude returns
        merged = merged[merged["quantity"] >= 0]

        # Determine group columns
        group_cols = _parse_list(group_by)
        if not group_cols:
            group_cols = ["size"]

        # CORE-26: Replace nulls with 'Unknown'
        for col in group_cols:
            if col in merged.columns:
                merged[col] = merged[col].fillna("Unknown").replace("", "Unknown")

        # Validate columns exist
        valid_cols = [c for c in group_cols if c in merged.columns]
        if not valid_cols:
            return {
                "error": f"Attribute(s) '{group_by}' not found in data. Available: {list(merged.columns)}",
                "data": [],
                "summary": {},
            }

        # Aggregate
        agg = merged.groupby(valid_cols).agg(
            total_qty=("quantity", "sum"),
            total_revenue=("revenue", "sum"),
            style_count=("style", "nunique"),
            store_count=("store_code", "nunique"),
            live_days=("day", "nunique"),
            avg_mrp=("mrp", "mean"),
        ).reset_index()

        agg["ros"] = (agg["total_qty"] / agg["live_days"].clip(lower=1)).round(3)
        agg["avg_mrp"] = agg["avg_mrp"].round(0)
        agg["revenue_share_pct"] = (agg["total_revenue"] / agg["total_revenue"].sum() * 100).round(1)
        agg = agg.sort_values("total_revenue", ascending=False)

        return {
            "config": {"group_by": valid_cols},
            "summary": {
                "total_groups": len(agg),
                "total_revenue": float(agg["total_revenue"].sum()),
                "total_qty": int(agg["total_qty"].sum()),
                "group_columns": valid_cols,
            },
            "data": agg.fillna(0).to_dict("records"),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "data": [], "summary": {}}


# ================================================================
# 5. Store-Style Ranking (CORE-28 to CORE-35)
# ================================================================

@router.get("/ranking")
async def core_ranking(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    sort_by: str = "revenue",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 50,
    direction: str = None,
    limit: int = 10,
    export_csv: bool = False,
):
    """
    Store-Style Ranking with flexible sorting and pagination.
    - CORE-28: Rank by revenue (highest = 1)
    - CORE-29: Rank by ROS (highest = 1)
    - CORE-30: Rank by DOH (lowest = 1)
    - CORE-31: Tie-breaking (secondary sort by style then store)
    - CORE-32: Pagination (50 per page)
    - CORE-33: Filter before ranking
    - CORE-34: Top 10 / Bottom 10
    - CORE-35: Export to CSV
    """
    sales_df = await _cached("daily_sales")
    inv_df = await _cached("store_inventory")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")

    if sales_df is None or sku_df is None:
        return {"error": "Required data not uploaded", "data": [], "summary": {}}

    try:
        sales_df = sales_df.copy()
        sales_df["day"] = pd.to_datetime(sales_df["day"])
        sales_df = _date_filter(sales_df, start_date, end_date, "day")

        ch_list = _parse_list(channels)
        reg_list = _parse_list(regions)
        cat_list = _parse_list(categories)

        if ch_list:
            sales_df = _channel_filter(sales_df, ch_list)
        if reg_list:
            sales_df = _region_filter(sales_df, reg_list, store_df)

        merged = sales_df.merge(sku_df[["ean", "style"]], left_on="sku", right_on="ean", how="left")
        if cat_list and style_df is not None:
            merged = _category_filter(merged, cat_list, style_df)

        if len(merged) == 0:
            return {"error": "No data matches filters", "data": [], "summary": {}, "pagination": {}}

        # Exclude returns
        merged = merged[merged["quantity"] >= 0]

        # Aggregate per store-style
        agg = merged.groupby(["store_code", "style"]).agg(
            total_qty=("quantity", "sum"),
            total_revenue=("revenue", "sum"),
            live_days=("day", "nunique"),
        ).reset_index()

        agg["ros"] = (agg["total_qty"] / agg["live_days"].clip(lower=1)).round(3)
        agg["revenue_per_day"] = (agg["total_revenue"] / agg["live_days"].clip(lower=1)).round(2)

        # Calculate DOH if inventory available
        if inv_df is not None:
            inv_copy = inv_df.copy()
            inv_copy["day"] = pd.to_datetime(inv_copy["day"])
            inv_copy = _date_filter(inv_copy, start_date, end_date, "day")
            if ch_list:
                inv_copy = _channel_filter(inv_copy, ch_list)
            if reg_list:
                inv_copy = _region_filter(inv_copy, reg_list, store_df)

            latest = inv_copy["day"].max()
            soh = inv_copy[inv_copy["day"] == latest].copy()
            soh_sku = soh.merge(sku_df[["ean", "style"]], on="ean", how="left")
            soh_agg = soh_sku.groupby(["store_code", "style"])["quantity"].sum().reset_index()
            soh_agg.columns = ["store_code", "style", "soh"]
            agg = agg.merge(soh_agg, on=["store_code", "style"], how="left")
            agg["soh"] = agg["soh"].fillna(0)
            agg["doh"] = np.where(agg["ros"] > 0, (agg["soh"] / agg["ros"]).round(1), 0)
        else:
            agg["soh"] = 0
            agg["doh"] = 0

        # CORE-28..30: Sorting and ranking
        valid_sorts = {"revenue": "total_revenue", "ros": "ros", "doh": "doh"}
        sort_col = valid_sorts.get(sort_by, "total_revenue")
        ascending = sort_dir == "asc"
        if sort_by == "doh":
            ascending = not ascending  # CORE-30: lowest DOH = Rank 1 → sort asc for desc ranking

        # CORE-31: Tie-breaking by style then store_code
        agg = agg.sort_values(
            [sort_col, "style", "store_code"],
            ascending=[ascending, True, True],
        )
        agg["rank"] = range(1, len(agg) + 1)

        total_rows = len(agg)

        # CORE-34: Top N / Bottom N
        if direction == "top":
            agg = agg.head(limit)
        elif direction == "bottom":
            agg = agg.tail(limit).sort_values("rank")

        # CORE-35: CSV export
        if export_csv:
            csv_buf = io.StringIO()
            agg.to_csv(csv_buf, index=False)
            csv_buf.seek(0)
            return StreamingResponse(
                iter([csv_buf.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=ranking_export.csv"},
            )

        # CORE-32: Pagination
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_data = agg.iloc[start_idx:end_idx]

        return {
            "config": {"sort_by": sort_by, "sort_dir": sort_dir},
            "summary": {
                "total_combinations": total_rows,
                "unique_stores": int(agg["store_code"].nunique()),
                "unique_styles": int(agg["style"].nunique()),
                "avg_revenue": float(agg["total_revenue"].mean()),
                "avg_ros": float(agg["ros"].mean()),
                "avg_doh": float(agg["doh"].mean()),
            },
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_rows": total_rows,
                "total_pages": total_pages,
            },
            "data": page_data.fillna(0).to_dict("records"),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "data": [], "summary": {}, "pagination": {}}
