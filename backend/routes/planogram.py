"""
Planogram Fill Rate Endpoints (PLAN-01 to PLAN-32)
Covers: Fill Rate Calc, Classification, Pre/Post Replenishment, Lost Sales, Trends
"""
from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
import pandas as pd
import numpy as np
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


async def _cached(ft):
    if _get_cached_data_func:
        return await _get_cached_data_func(ft)
    doc = await _db().uploaded_files.find_one({"file_type": ft})
    return pd.DataFrame(doc["data"]) if doc and "data" in doc else None


async def _cfg():
    c = await _db().analysis_config.find_one({"_id": "main"}, {"_id": 0})
    return c or {}


def _filt(df, s=None, e=None, col="day"):
    if col not in df.columns:
        return df
    df[col] = pd.to_datetime(df[col])
    if s:
        df = df[df[col] >= pd.to_datetime(s)]
    if e:
        df = df[df[col] <= pd.to_datetime(e)]
    return df


def _chf(df, ch):
    if not ch or "channel" not in df.columns:
        return df
    return df[df["channel"].isin(ch)]


def _rgf(df, rg, sdf=None):
    if not rg:
        return df
    if "region" in df.columns:
        return df[df["region"].isin(rg)]
    if sdf is not None and "store_code" in df.columns and "region" in sdf.columns:
        v = sdf[sdf["region"].isin(rg)]["store_code"].tolist()
        return df[df["store_code"].isin(v)]
    return df


def _pl(p):
    return [x.strip() for x in p.split(",") if x.strip()] if p else []


def _classify(rate):
    if rate >= 90:
        return "GOOD"
    if rate >= 80:
        return "MODERATE"
    return "CRITICAL"


def _build_fill_df(inv_filtered, sales_filtered, sku_df, style_df, categories_list, planogram_df=None):
    """Build the core fill rate dataframe used across multiple endpoints."""
    sku_cols = ["ean"]
    if "style" in sku_df.columns:
        sku_cols.append("style")
    if "mrp" in sku_df.columns:
        sku_cols.append("mrp")

    inv_sku = inv_filtered.merge(sku_df[sku_cols], on="ean", how="left")
    sales_sku = sales_filtered.merge(sku_df[sku_cols], left_on="sku", right_on="ean", how="left")

    if categories_list and style_df is not None:
        if "style_code" in style_df.columns and "category" in style_df.columns:
            valid_styles = style_df[style_df["category"].isin(categories_list)]["style_code"].tolist()
            if "style" in inv_sku.columns:
                inv_sku = inv_sku[inv_sku["style"].isin(valid_styles)]
            if "style" in sales_sku.columns:
                sales_sku = sales_sku[sales_sku["style"].isin(valid_styles)]

    # Norm Allocated: prefer uploaded planogram, fall back to max observed inventory
    if planogram_df is not None and len(planogram_df) > 0:
        plano = planogram_df.copy()
        plano["norm_allocated"] = pd.to_numeric(plano.get("norm_allocated", pd.Series(dtype=float)), errors="coerce").fillna(0).clip(lower=1)
        # Map planogram style_code → sku via sku_df
        if "style" in sku_df.columns:
            sku_style = sku_df[["ean", "style"]].drop_duplicates("ean")
            plano_sku = plano.merge(sku_style, left_on="style_code", right_on="style", how="inner")
            if len(plano_sku) > 0:
                norm = plano_sku.groupby(["store_code", "ean"]).agg(norm_allocated=("norm_allocated", "first")).reset_index()
            else:
                norm = inv_sku.groupby(["store_code", "ean"]).agg(max_qty=("quantity", "max")).reset_index()
                norm["norm_allocated"] = norm["max_qty"].clip(lower=1)
        else:
            norm = inv_sku.groupby(["store_code", "ean"]).agg(max_qty=("quantity", "max")).reset_index()
            norm["norm_allocated"] = norm["max_qty"].clip(lower=1)
    else:
        # Fallback: auto-derive from max observed inventory per store-EAN
        norm = inv_sku.groupby(["store_code", "ean"]).agg(max_qty=("quantity", "max")).reset_index()
        norm["norm_allocated"] = norm["max_qty"].clip(lower=1)

    # Current Stock = latest day SOH
    latest_date = inv_filtered["day"].max()
    soh = inv_filtered[inv_filtered["day"] == latest_date].groupby(["store_code", "ean"])["quantity"].sum().reset_index()
    soh.columns = ["store_code", "ean", "current_stock"]

    fill = norm.merge(soh, on=["store_code", "ean"], how="left")
    fill["current_stock"] = fill["current_stock"].fillna(0).clip(lower=0)
    fill["fill_rate"] = (fill["current_stock"] / fill["norm_allocated"].clip(lower=1) * 100).round(1)
    fill["missing_facings"] = (fill["norm_allocated"] - fill["current_stock"]).clip(lower=0)
    fill["status"] = fill["fill_rate"].apply(_classify)

    # Style / ASP
    if "style" in sku_df.columns:
        fill["style"] = fill["ean"].map(sku_df.groupby("ean")["style"].first()).fillna("Unknown")
    else:
        fill["style"] = "Unknown"
    if "mrp" in sku_df.columns:
        fill["asp"] = fill["ean"].map(sku_df.groupby("ean")["mrp"].first()).fillna(0)
    else:
        fill["asp"] = 0

    # Category
    if style_df is not None and "style_code" in style_df.columns and "category" in style_df.columns:
        sc = style_df.groupby("style_code")["category"].first().to_dict()
        fill["category"] = fill["style"].map(sc).fillna("General")
    else:
        fill["category"] = "General"

    # ROS + lost sales
    ros = sales_sku.groupby(["store_code", "sku"]).agg(
        total_qty=("quantity", "sum"), live_days=("day", "nunique"),
        total_rev=("revenue", "sum")
    ).reset_index()
    ros["ros"] = (ros["total_qty"] / ros["live_days"].clip(lower=1)).round(3)
    fill = fill.merge(ros[["store_code", "sku", "ros"]], left_on=["store_code", "ean"], right_on=["store_code", "sku"], how="left")
    fill["ros"] = fill["ros"].fillna(0)
    fill["lost_sales"] = (fill["missing_facings"] * fill["ros"] * fill["asp"]).round(2)

    return fill, latest_date


# =========================================================================
# MAIN ANALYSIS (PLAN-01 to PLAN-14, PLAN-21 to PLAN-25)
# =========================================================================
@router.get("/analysis")
async def get_fill_rate_analysis(
    start_date: str = None, end_date: str = None,
    categories: str = None, channels: str = None,
    regions: str = None, target_fill_rate: int = 85,
):
    """
    PLAN-01: fill_rate = (current_stock / norm_allocated) * 100
    PLAN-02: 100% when current = norm
    PLAN-03: 0% when current = 0
    PLAN-04: Overall = weighted avg
    PLAN-05/06: Category and store aggregations
    PLAN-07: >100% fill rate when current > norm
    PLAN-08: Missing facings when current < norm
    PLAN-09-14: Classification (Good >=90, Moderate 80-90, Critical <80)
    PLAN-21-25: Lost sales = missing_facings * ros * asp
    """
    sales_df = await _cached("daily_sales")
    inv_df = await _cached("store_inventory")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")
    planogram_df = await _cached("planogram")

    if sales_df is None or inv_df is None or sku_df is None:
        return {"error": "Required data not uploaded"}

    try:
        sales = _filt(sales_df.copy(), start_date, end_date, "day")
        inv = _filt(inv_df.copy(), start_date, end_date, "day")
        cl, chl, rgl = _pl(categories), _pl(channels), _pl(regions)
        if chl:
            sales, inv = _chf(sales, chl), _chf(inv, chl)
        if rgl:
            sales, inv = _rgf(sales, rgl, store_df), _rgf(inv, rgl, store_df)
        sales["day"] = pd.to_datetime(sales["day"])
        inv["day"] = pd.to_datetime(inv["day"])

        fill, latest_date = _build_fill_df(inv, sales, sku_df, style_df, cl, planogram_df)
        if len(fill) == 0:
            return {"error": "No data matches filters"}

        # PLAN-04: Overall weighted fill rate
        oc = float(fill["current_stock"].sum())
        on = float(fill["norm_allocated"].sum())
        overall_fill = round(oc / max(on, 1) * 100, 1)
        overall_lost = float(fill["lost_sales"].sum())
        sc = fill["status"].value_counts().to_dict()

        # PLAN-06: Store aggregation
        store_agg = fill.groupby("store_code").agg(
            current_stock=("current_stock", "sum"), norm_allocated=("norm_allocated", "sum"),
            lost_sales=("lost_sales", "sum"), sku_count=("ean", "nunique"),
            good_count=("status", lambda x: int((x == "GOOD").sum())),
            moderate_count=("status", lambda x: int((x == "MODERATE").sum())),
            critical_count=("status", lambda x: int((x == "CRITICAL").sum())),
        ).reset_index()
        store_agg["fill_rate"] = (store_agg["current_stock"] / store_agg["norm_allocated"].clip(lower=1) * 100).round(1)
        store_agg["status"] = store_agg["fill_rate"].apply(_classify)
        # Add region
        if store_df is not None and "region" in store_df.columns:
            srm = store_df.groupby("store_code")["region"].first().to_dict()
            store_agg["region"] = store_agg["store_code"].map(srm).fillna("Unknown")
        else:
            store_agg["region"] = "Unknown"
        store_agg = store_agg.sort_values("fill_rate")

        # PLAN-05: Category aggregation
        cat_agg = fill.groupby("category").agg(
            current_stock=("current_stock", "sum"), norm_allocated=("norm_allocated", "sum"),
            lost_sales=("lost_sales", "sum"), sku_count=("ean", "nunique"),
        ).reset_index()
        cat_agg["fill_rate"] = (cat_agg["current_stock"] / cat_agg["norm_allocated"].clip(lower=1) * 100).round(1)
        cat_agg["status"] = cat_agg["fill_rate"].apply(_classify)
        cat_agg = cat_agg.sort_values("fill_rate")

        # PLAN-13: Weekly compliance trend
        inv_daily = inv.groupby("day")["quantity"].sum().reset_index()
        inv_daily.columns = ["day", "total_stock"]
        total_norm = float(fill["norm_allocated"].sum())
        inv_daily["fill_rate"] = (inv_daily["total_stock"] / max(total_norm, 1) * 100).round(1)
        inv_daily["status"] = inv_daily["fill_rate"].apply(_classify)
        inv_daily = inv_daily.set_index("day")
        weekly = inv_daily.resample("W").agg({"fill_rate": "mean", "total_stock": "last"}).reset_index()
        weekly["fill_rate"] = weekly["fill_rate"].round(1)
        weekly["status"] = weekly["fill_rate"].apply(_classify)
        weekly["week_label"] = weekly["day"].dt.strftime("%b %d")
        weekly["target"] = target_fill_rate
        compliance_trend = weekly[["week_label", "fill_rate", "status", "target"]].tail(12).fillna(0).to_dict("records")

        # PLAN-25: Lost sales breakdown
        lost_by_cat = fill.groupby("category")["lost_sales"].sum().reset_index().sort_values("lost_sales", ascending=False)
        lost_by_store = fill.groupby("store_code")["lost_sales"].sum().reset_index().sort_values("lost_sales", ascending=False)

        detail_cols = ["store_code", "ean", "style", "category", "current_stock", "norm_allocated",
                       "fill_rate", "missing_facings", "ros", "asp", "lost_sales", "status"]
        detail = fill[detail_cols].sort_values("fill_rate").head(200).round(2).fillna(0).to_dict("records")

        return {
            "summary": {
                "overall_fill_rate": overall_fill,
                "overall_status": _classify(overall_fill),
                "target_fill_rate": target_fill_rate,
                "total_current_stock": round(oc, 0),
                "total_norm_allocated": round(on, 0),
                "total_lost_sales": round(overall_lost, 2),
                "total_store_skus": len(fill),
                "good_count": int(sc.get("GOOD", 0)),
                "moderate_count": int(sc.get("MODERATE", 0)),
                "critical_count": int(sc.get("CRITICAL", 0)),
                "total_stores": int(store_agg["store_code"].nunique()),
                "snapshot_date": str(latest_date.date()) if pd.notna(latest_date) else None,
                "norm_source": "uploaded_planogram" if (planogram_df is not None and len(planogram_df) > 0) else "auto_derived",
            },
            "store_data": store_agg.fillna(0).round(2).to_dict("records"),
            "category_data": cat_agg.fillna(0).round(2).to_dict("records"),
            "compliance_trend": compliance_trend,
            "lost_sales_by_category": lost_by_cat.round(2).to_dict("records"),
            "lost_sales_by_store": lost_by_store.head(20).round(2).to_dict("records"),
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
    # Get current (pre) fill rate
    pre_result = await get_fill_rate_analysis(start_date, end_date, categories, channels, regions, target_fill_rate)
    if "error" in pre_result:
        return pre_result

    # Get latest replenishment run for post-simulation
    runs = await _db().replenishment_runs.find({}, {"_id": 0}).sort("created_at", -1).to_list(1)
    orders = await _db().replenishment_orders.find({"status": {"$in": ["pending", "approved"]}}, {"_id": 0}).to_list(5000)

    # Simulate post by adding order quantities to current stock
    order_map = {}
    for o in orders:
        key = (o.get("store_code", ""), str(o.get("sku", "")))
        order_map[key] = order_map.get(key, 0) + o.get("order_qty", 0)

    sales_df = await _cached("daily_sales")  # needed by analysis endpoint  # noqa: F841
    inv_df = await _cached("store_inventory")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")

    if inv_df is None or sku_df is None:
        return {"error": "Required data not uploaded"}

    try:
        inv = _filt(inv_df.copy(), start_date, end_date, "day")
        cl, chl, rgl = _pl(categories), _pl(channels), _pl(regions)
        if chl:
            inv = _chf(inv, chl)
        if rgl:
            inv = _rgf(inv, rgl, store_df)
        inv["day"] = pd.to_datetime(inv["day"])

        # Norm
        norm = inv.groupby(["store_code", "ean"]).agg(max_qty=("quantity", "max")).reset_index()
        norm["norm_allocated"] = norm["max_qty"].clip(lower=1)

        latest_date = inv["day"].max()
        soh = inv[inv["day"] == latest_date].groupby(["store_code", "ean"])["quantity"].sum().reset_index()
        soh.columns = ["store_code", "ean", "current_stock"]

        fill = norm.merge(soh, on=["store_code", "ean"], how="left")
        fill["current_stock"] = fill["current_stock"].fillna(0).clip(lower=0)

        # Pre fill rate
        fill["pre_fill_rate"] = (fill["current_stock"] / fill["norm_allocated"].clip(lower=1) * 100).round(1)
        fill["pre_status"] = fill["pre_fill_rate"].apply(_classify)

        # Post: add replenishment orders
        fill["order_qty"] = fill.apply(
            lambda r: order_map.get((r["store_code"], str(int(r["ean"])) if isinstance(r["ean"], float) else str(r["ean"])), 0), axis=1
        )
        fill["post_stock"] = fill["current_stock"] + fill["order_qty"]
        fill["post_fill_rate"] = (fill["post_stock"] / fill["norm_allocated"].clip(lower=1) * 100).round(1)
        fill["post_status"] = fill["post_fill_rate"].apply(_classify)

        # Category filter
        if cl and style_df is not None and "style" in sku_df.columns:
            fill["style"] = fill["ean"].map(sku_df.groupby("ean")["style"].first()).fillna("Unknown")
            sc_map = style_df.groupby("style_code")["category"].first().to_dict() if "style_code" in style_df.columns else {}
            fill["category"] = fill["style"].map(sc_map).fillna("General")
            fill = fill[fill["category"].isin(cl)]

        pre_oc = float(fill["current_stock"].sum())
        pre_on = float(fill["norm_allocated"].sum())
        pre_overall = round(pre_oc / max(pre_on, 1) * 100, 1)
        post_oc = float(fill["post_stock"].sum())
        post_overall = round(post_oc / max(pre_on, 1) * 100, 1)

        improvement = round(post_overall - pre_overall, 1)
        improvement_pct = round(improvement / max(pre_overall, 0.1) * 100, 1) if pre_overall > 0 else 0

        pre_sc = fill["pre_status"].value_counts().to_dict()
        post_sc = fill["post_status"].value_counts().to_dict()

        # PLAN-20: Count stores that improved status
        pre_store_status = fill.groupby("store_code")["pre_status"].agg(
            lambda x: _classify(fill.loc[x.index, "current_stock"].sum() / max(fill.loc[x.index, "norm_allocated"].sum(), 1) * 100)
        ).to_dict()
        post_store_status = fill.groupby("store_code")["post_status"].agg(
            lambda x: _classify(fill.loc[x.index, "post_stock"].sum() / max(fill.loc[x.index, "norm_allocated"].sum(), 1) * 100)
        ).to_dict()
        status_rank = {"CRITICAL": 0, "MODERATE": 1, "GOOD": 2}
        improved_stores = sum(
            1 for s in pre_store_status
            if status_rank.get(post_store_status.get(s, "CRITICAL"), 0) > status_rank.get(pre_store_status.get(s, "CRITICAL"), 0)
        )
        moved_to_good = sum(1 for s in post_store_status if post_store_status[s] == "GOOD" and pre_store_status.get(s) != "GOOD")

        return {
            "pre": {
                "fill_rate": pre_overall,
                "status": _classify(pre_overall),
                "good_count": int(pre_sc.get("GOOD", 0)),
                "moderate_count": int(pre_sc.get("MODERATE", 0)),
                "critical_count": int(pre_sc.get("CRITICAL", 0)),
            },
            "post": {
                "fill_rate": post_overall,
                "status": _classify(post_overall),
                "good_count": int(post_sc.get("GOOD", 0)),
                "moderate_count": int(post_sc.get("MODERATE", 0)),
                "critical_count": int(post_sc.get("CRITICAL", 0)),
            },
            "improvement": improvement,
            "improvement_pct": improvement_pct,
            "stores_improved": improved_stores,
            "stores_moved_to_good": moved_to_good,
            "total_stores": int(fill["store_code"].nunique()),
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
    """
    PLAN-26: Daily trend
    PLAN-27: Weekly trend
    PLAN-28: Monthly trend
    PLAN-29: Target line (85%)
    PLAN-30: 7-day moving average
    PLAN-31: Threshold alerts (<80%)
    PLAN-32: Export (CSV export from returned data on frontend)
    """
    inv_df = await _cached("store_inventory")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")

    if inv_df is None or sku_df is None:
        return {"error": "Required data not uploaded"}

    try:
        inv = _filt(inv_df.copy(), start_date, end_date, "day")
        cl, chl, rgl = _pl(categories), _pl(channels), _pl(regions)
        if chl:
            inv = _chf(inv, chl)
        if rgl:
            inv = _rgf(inv, rgl, store_df)
        inv["day"] = pd.to_datetime(inv["day"])

        if cl and style_df is not None and "style" in sku_df.columns:
            inv = inv.merge(sku_df[["ean", "style"]], on="ean", how="left")
            sc_map = style_df.groupby("style_code")["category"].first().to_dict() if "style_code" in style_df.columns else {}
            inv["category"] = inv["style"].map(sc_map).fillna("General")
            inv = inv[inv["category"].isin(cl)]

        # Norm = max observed per store-ean across all time
        norm = inv.groupby(["store_code", "ean"]).agg(max_qty=("quantity", "max")).reset_index()
        total_norm = float(norm["max_qty"].clip(lower=1).sum())

        daily = inv.groupby("day")["quantity"].sum().reset_index()
        daily.columns = ["day", "total_stock"]
        daily = daily.sort_values("day")
        daily["fill_rate"] = (daily["total_stock"] / max(total_norm, 1) * 100).round(1)
        daily["target"] = target_fill_rate
        daily["moving_avg_7d"] = daily["fill_rate"].rolling(7, min_periods=1).mean().round(1)
        daily["below_threshold"] = daily["fill_rate"] < 80

        # Alerts (PLAN-31)
        alerts = []
        alert_dates = daily[daily["below_threshold"]]
        if len(alert_dates) > 0:
            for _, row in alert_dates.tail(5).iterrows():
                alerts.append({
                    "date": str(row["day"].date()),
                    "fill_rate": float(row["fill_rate"]),
                    "message": f"Fill rate dropped to {row['fill_rate']}% on {row['day'].strftime('%b %d')}",
                })

        # Resample based on granularity
        daily_idx = daily.set_index("day")
        if granularity == "daily":
            out = daily_idx.reset_index()
            out["label"] = out["day"].dt.strftime("%b %d")
            trend = out[["label", "fill_rate", "target", "moving_avg_7d"]].tail(30).fillna(0).to_dict("records")
        elif granularity == "monthly":
            monthly = daily_idx.resample("ME").agg({"fill_rate": "mean", "total_stock": "last"}).reset_index()
            monthly["fill_rate"] = monthly["fill_rate"].round(1)
            monthly["target"] = target_fill_rate
            monthly["label"] = monthly["day"].dt.strftime("%b %Y")
            monthly["moving_avg_7d"] = monthly["fill_rate"]
            trend = monthly[["label", "fill_rate", "target", "moving_avg_7d"]].tail(12).fillna(0).to_dict("records")
        else:
            weekly = daily_idx.resample("W").agg({"fill_rate": "mean", "total_stock": "last"}).reset_index()
            weekly["fill_rate"] = weekly["fill_rate"].round(1)
            weekly["target"] = target_fill_rate
            weekly["moving_avg_7d"] = weekly["fill_rate"].rolling(4, min_periods=1).mean().round(1)
            weekly["label"] = weekly["day"].dt.strftime("%b %d")
            trend = weekly[["label", "fill_rate", "target", "moving_avg_7d"]].tail(12).fillna(0).to_dict("records")

        return {
            "granularity": granularity,
            "target_fill_rate": target_fill_rate,
            "trend": trend,
            "alerts": alerts,
            "total_norm": round(total_norm, 0),
            "below_threshold_days": int(daily["below_threshold"].sum()),
            "total_days": len(daily),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
