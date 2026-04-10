"""
DOH (Days on Hand) Analysis Endpoints
Covers: DOH Calculation, Classification, Heatmaps, Correlation, Recommendations
Test Cases: DOH-01 to DOH-35
"""

from fastapi import APIRouter, Query
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import os
from datetime import datetime, timezone

from services.cache_service import cache_get, cache_set, cache_extra, get_tenant_id as _cache_tid

router = APIRouter(prefix="/analytics/doh", tags=["doh-analysis"])

_client: Optional[AsyncIOMotorClient] = None
_get_cached_data_func = None


def init_doh(mongo_client: AsyncIOMotorClient, get_cached_data_func=None):
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


def _date_filter(df, start=None, end=None, col="day"):
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


def _parse_list(param: str) -> List[str]:
    if not param:
        return []
    return [x.strip() for x in param.split(",") if x.strip()]


# =========================================================================
# MAIN DOH ANALYSIS (DOH-01 to DOH-15)
# =========================================================================
@router.get("/analysis")
async def get_doh_analysis(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    store_classes: str = None,
    ideal_doh: int = None,
    include_wh: bool = False,
    topseller_multiplier: float = None,
):
    """
    Enhanced DOH Analysis covering DOH-01 to DOH-15.
    DOH-01: DOH(store,sku) = Inventory / Daily ROS
    DOH-02: Zero inventory -> DOH=0, Status=STOCKED_OUT
    DOH-03: Zero ROS -> DOH=Infinity(9999), Status=NO_SALES
    DOH-04: Weighted average DOH = Sum(DOH x Inv) / Sum(Inv)
    DOH-05: Channel level DOH aggregated from stores
    DOH-06: Category level DOH aggregated from styles
    DOH-07: DOH with WH stock included (include_wh=true)
    DOH-08: DOH without WH stock (default)
    DOH-09-13: Classification (Optimal ±20%, Overstocked >120%, Understocked <80%, Stocked Out)
    DOH-14: Different ideal per category (from config)
    DOH-15: Topseller additional cover (ideal_doh x multiplier)
    """
    _tid = _cache_tid()
    _ex = cache_extra(sd=start_date, ed=end_date, cat=categories, ch=channels, rg=regions, sc=store_classes, idoh=ideal_doh, wh=include_wh, tm=topseller_multiplier)
    _hit, _data = cache_get("doh_heatmap", _tid, _ex)
    if _hit:
        return _data
    cfg = await _get_config()
    if ideal_doh is None:
        ideal_doh = cfg.get("ideal_doh", 9)
    if topseller_multiplier is None:
        topseller_multiplier = cfg.get("topseller_x_factor", 2.0)

    sales_df = await _cached("daily_sales")
    inv_df = await _cached("store_inventory")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")
    wh_df = await _cached("warehouse_inventory")

    if sales_df is None or inv_df is None or sku_df is None:
        return {"error": "Required data not uploaded (need daily_sales, store_inventory, sku_ean_master)"}

    try:
        sales = _date_filter(sales_df.copy(), start_date, end_date, "day")
        inv = _date_filter(inv_df.copy(), start_date, end_date, "day")
        cat_list = _parse_list(categories)
        ch_list = _parse_list(channels)
        rg_list = _parse_list(regions)
        sc_list = _parse_list(store_classes)

        if ch_list:
            sales = _channel_filter(sales, ch_list)
            inv = _channel_filter(inv, ch_list)
        if rg_list:
            sales = _region_filter(sales, rg_list, store_df)
            inv = _region_filter(inv, rg_list, store_df)

        # DOH-20: Filter by store class
        if sc_list and store_df is not None:
            assignments = await _get_db().store_class_assignments.find({}, {"_id": 0}).to_list(5000)
            class_stores = [a["store_code"] for a in assignments if a.get("class_code") in sc_list]
            if class_stores:
                sales = sales[sales["store_code"].isin(class_stores)]
                inv = inv[inv["store_code"].isin(class_stores)]

        sales["day"] = pd.to_datetime(sales["day"])
        inv["day"] = pd.to_datetime(inv["day"])

        # Merge sales with SKU master
        sku_cols = ["ean"]
        if "style" in sku_df.columns:
            sku_cols.append("style")
        sales_sku = sales.merge(sku_df[sku_cols], left_on="sku", right_on="ean", how="left")

        if cat_list and style_df is not None:
            if "style_code" in style_df.columns:
                filtered_styles = style_df[style_df["category"].isin(cat_list)]["style_code"].tolist()
                if "style" in sales_sku.columns:
                    sales_sku = sales_sku[sales_sku["style"].isin(filtered_styles)]

        if len(sales_sku) == 0:
            return {"error": "No data matches the selected filters"}

        # ================================================
        # DOH-01: ROS per store-SKU
        # ================================================
        ros_calc = sales_sku.groupby(["store_code", "sku"]).agg(
            total_qty=("quantity", "sum"),
            total_revenue=("revenue", "sum"),
            live_days=("day", "nunique"),
        ).reset_index()
        ros_calc["ros"] = (ros_calc["total_qty"] / ros_calc["live_days"].clip(lower=1)).round(4)

        # ================================================
        # DOH-01/08: Latest SOH per store-SKU (store only by default)
        # ================================================
        latest_date = inv["day"].max()
        latest_inv = inv[inv["day"] == latest_date].copy()
        soh = latest_inv.groupby(["store_code", "ean"])["quantity"].sum().reset_index()
        soh.columns = ["store_code", "sku", "soh"]

        # ================================================
        # DOH-07: Add warehouse stock if include_wh=true
        # ================================================
        wh_stock_by_sku = {}
        if include_wh and wh_df is not None and len(wh_df) > 0:
            wh = wh_df.copy()
            wh["day"] = pd.to_datetime(wh["day"])
            wh_latest = wh[wh["day"] == wh["day"].max()]
            wh_agg = wh_latest.groupby("sku")["quantity"].sum()
            wh_stock_by_sku = wh_agg.to_dict()

        # ================================================
        # Merge: DOH = SOH / ROS
        # ================================================
        doh_df = ros_calc.merge(soh, on=["store_code", "sku"], how="outer")
        doh_df["soh"] = doh_df["soh"].fillna(0)
        doh_df["ros"] = doh_df["ros"].fillna(0)
        doh_df["total_qty"] = doh_df["total_qty"].fillna(0)
        doh_df["total_revenue"] = doh_df["total_revenue"].fillna(0)

        # Add WH stock if applicable (DOH-07)
        if include_wh and wh_stock_by_sku:
            doh_df["wh_stock"] = doh_df["sku"].astype(str).map(wh_stock_by_sku).fillna(0)
            doh_df["total_stock"] = doh_df["soh"] + doh_df["wh_stock"]
        else:
            doh_df["wh_stock"] = 0
            doh_df["total_stock"] = doh_df["soh"]

        # DOH calculation
        stock_col = "total_stock" if include_wh else "soh"
        doh_df["doh"] = np.where(
            doh_df["ros"] > 0,
            (doh_df[stock_col] / doh_df["ros"]).round(1),
            np.where(doh_df[stock_col] > 0, 9999, 0),
        )

        # Map style info
        if "style" in sku_df.columns:
            doh_df["style"] = doh_df["sku"].map(sku_df.groupby("ean")["style"].first()).fillna("Unknown")
        else:
            doh_df["style"] = "Unknown"

        # Map category
        style_category = {}
        if style_df is not None and "style_code" in style_df.columns and "category" in style_df.columns:
            style_category = style_df.groupby("style_code")["category"].first().to_dict()
        doh_df["category"] = doh_df["style"].map(style_category).fillna("General")

        # Map channel from store_df
        store_channel = {}
        if store_df is not None and "store_code" in store_df.columns and "channel" in store_df.columns:
            store_channel = store_df.groupby("store_code")["channel"].first().to_dict()
        doh_df["channel"] = doh_df["store_code"].map(store_channel).fillna("Unknown")

        # Map region from store_df
        store_region = {}
        if store_df is not None and "store_code" in store_df.columns and "region" in store_df.columns:
            store_region = store_df.groupby("store_code")["region"].first().to_dict()
        doh_df["region"] = doh_df["store_code"].map(store_region).fillna("Unknown")

        # ================================================
        # DOH-14: Category-specific ideal DOH
        # ================================================
        cat_ideal_doc = await _get_db().category_ideal_doh.find({}, {"_id": 0}).to_list(200)
        cat_ideal_map = {d["category"]: d["ideal_doh"] for d in cat_ideal_doc}
        doh_df["cat_ideal_doh"] = doh_df["category"].map(cat_ideal_map).fillna(ideal_doh)

        # ================================================
        # DOH-15: Topseller additional cover
        # ================================================
        # Identify topsellers: revenue in top 20% per category
        if len(ros_calc) > 0:
            rev_threshold = ros_calc.groupby("sku")["total_revenue"].sum().quantile(0.8)
            sku_total_rev = ros_calc.groupby("sku")["total_revenue"].sum()
            topseller_skus = set(sku_total_rev[sku_total_rev >= rev_threshold].index)
        else:
            topseller_skus = set()
        doh_df["is_topseller"] = doh_df["sku"].isin(topseller_skus)
        doh_df["effective_ideal_doh"] = np.where(
            doh_df["is_topseller"],
            (doh_df["cat_ideal_doh"] * topseller_multiplier).round(1),
            doh_df["cat_ideal_doh"],
        )

        # ================================================
        # Classification using effective ideal DOH (DOH-09 to DOH-13)
        # ================================================
        def classify(row):
            eff_ideal = row["effective_ideal_doh"]
            upper = eff_ideal * 1.2
            lower = eff_ideal * 0.8
            s = row[stock_col]
            r = row["ros"]
            if s == 0 and r > 0:
                return "STOCKED_OUT"
            if r == 0 and s > 0:
                return "NO_SALES"
            if r == 0 and s == 0:
                return "STOCKED_OUT"
            if row["doh"] > upper:
                return "OVERSTOCKED"
            if row["doh"] < lower:
                return "UNDERSTOCKED"
            return "OPTIMAL"

        doh_df["status"] = doh_df.apply(classify, axis=1)

        # ================================================
        # DOH-04: Weighted average DOH (overall)
        # ================================================
        valid = doh_df[(doh_df["ros"] > 0) & (doh_df[stock_col] > 0)].copy()
        valid["weighted_doh"] = valid["doh"] * valid[stock_col]
        overall_doh = 0.0
        if len(valid) > 0:
            overall_doh = round(float(valid["weighted_doh"].sum() / valid[stock_col].sum()), 1)

        # ================================================
        # Store-wise aggregation
        # ================================================
        store_agg = valid.groupby("store_code").agg(
            total_inventory=(stock_col, "sum"),
            weighted_doh_sum=("weighted_doh", "sum"),
            sku_count=("sku", "nunique"),
            total_revenue=("total_revenue", "sum"),
        ).reset_index()
        store_agg["doh"] = (store_agg["weighted_doh_sum"] / store_agg["total_inventory"].clip(lower=1)).round(1)

        store_status = doh_df.groupby(["store_code", "status"]).size().unstack(fill_value=0).reset_index()
        for col in ["OPTIMAL", "OVERSTOCKED", "UNDERSTOCKED", "STOCKED_OUT", "NO_SALES"]:
            if col not in store_status.columns:
                store_status[col] = 0
        store_agg = store_agg.merge(store_status, on="store_code", how="left")

        # Add region, channel
        store_agg["region"] = store_agg["store_code"].map(store_region).fillna("Unknown")
        store_agg["channel"] = store_agg["store_code"].map(store_channel).fillna("Unknown")

        # Store class
        assignments = await _get_db().store_class_assignments.find({}, {"_id": 0}).to_list(5000)
        sc_map = {a["store_code"]: a["class_code"] for a in assignments}
        store_agg["store_class"] = store_agg["store_code"].map(sc_map).fillna("-")

        def store_overall(row):
            if row.get("STOCKED_OUT", 0) > row.get("OPTIMAL", 0):
                return "STOCKED_OUT"
            if row.get("UNDERSTOCKED", 0) > row.get("OPTIMAL", 0):
                return "UNDERSTOCKED"
            if row.get("OVERSTOCKED", 0) > row.get("OPTIMAL", 0):
                return "OVERSTOCKED"
            return "OPTIMAL"

        store_agg["status"] = store_agg.apply(store_overall, axis=1)
        store_agg["ideal_doh"] = ideal_doh
        store_data = store_agg.sort_values("doh")[[
            "store_code", "channel", "region", "store_class", "total_inventory",
            "doh", "sku_count", "status", "ideal_doh",
            "OPTIMAL", "OVERSTOCKED", "UNDERSTOCKED", "STOCKED_OUT",
        ]].fillna(0).to_dict("records")

        # ================================================
        # DOH-06: Category-wise aggregation
        # ================================================
        category_data = []
        if "category" in doh_df.columns:
            valid_cat = doh_df[(doh_df["ros"] > 0) & (doh_df[stock_col] > 0)].copy()
            valid_cat["weighted_doh"] = valid_cat["doh"] * valid_cat[stock_col]
            cat_agg = valid_cat.groupby("category").agg(
                total_inventory=(stock_col, "sum"),
                weighted_doh_sum=("weighted_doh", "sum"),
                sku_count=("sku", "nunique"),
            ).reset_index()
            cat_agg["doh"] = (cat_agg["weighted_doh_sum"] / cat_agg["total_inventory"].clip(lower=1)).round(1)
            cat_agg["ideal_doh"] = cat_agg["category"].map(cat_ideal_map).fillna(ideal_doh)

            def cat_classify(row):
                upper = row["ideal_doh"] * 1.2
                lower = row["ideal_doh"] * 0.8
                if row["doh"] > upper:
                    return "OVERSTOCKED"
                if row["doh"] < lower:
                    return "UNDERSTOCKED"
                return "OPTIMAL"

            cat_agg["status"] = cat_agg.apply(cat_classify, axis=1)
            # Count statuses per category
            cat_status = doh_df.groupby(["category", "status"]).size().unstack(fill_value=0).reset_index()
            for col in ["OPTIMAL", "OVERSTOCKED", "UNDERSTOCKED", "STOCKED_OUT"]:
                if col not in cat_status.columns:
                    cat_status[col] = 0
            cat_agg = cat_agg.merge(cat_status, on="category", how="left")
            category_data = cat_agg[[
                "category", "total_inventory", "doh", "sku_count", "status", "ideal_doh",
                "OPTIMAL", "OVERSTOCKED", "UNDERSTOCKED", "STOCKED_OUT",
            ]].fillna(0).to_dict("records")

        # ================================================
        # DOH-05: Channel-level DOH
        # ================================================
        channel_data = []
        if "channel" in doh_df.columns:
            valid_ch = doh_df[(doh_df["ros"] > 0) & (doh_df[stock_col] > 0)].copy()
            valid_ch["weighted_doh"] = valid_ch["doh"] * valid_ch[stock_col]
            ch_agg = valid_ch.groupby("channel").agg(
                total_inventory=(stock_col, "sum"),
                weighted_doh_sum=("weighted_doh", "sum"),
                store_count=("store_code", "nunique"),
                sku_count=("sku", "nunique"),
            ).reset_index()
            ch_agg["doh"] = (ch_agg["weighted_doh_sum"] / ch_agg["total_inventory"].clip(lower=1)).round(1)
            ch_agg["ideal_doh"] = ideal_doh

            def ch_classify(row):
                upper = ideal_doh * 1.2
                lower = ideal_doh * 0.8
                if row["doh"] > upper:
                    return "OVERSTOCKED"
                if row["doh"] < lower:
                    return "UNDERSTOCKED"
                return "OPTIMAL"

            ch_agg["status"] = ch_agg.apply(ch_classify, axis=1)
            channel_data = ch_agg[[
                "channel", "total_inventory", "doh", "store_count", "sku_count", "status", "ideal_doh",
            ]].fillna(0).to_dict("records")

        # ================================================
        # DOH Trend (weekly) with stock-out correlation
        # ================================================
        inv_daily = inv.groupby("day")["quantity"].sum().reset_index()
        inv_daily.columns = ["day", "total_inv"]
        sales_daily = sales.groupby("day")["quantity"].sum().reset_index()
        sales_daily.columns = ["day", "total_sales"]
        daily = inv_daily.merge(sales_daily, on="day", how="outer").sort_values("day").fillna(0)
        daily["ros_7d"] = daily["total_sales"].rolling(7, min_periods=1).mean()
        daily["doh"] = np.where(daily["ros_7d"] > 0, (daily["total_inv"] / daily["ros_7d"]).round(1), 0)
        # Stockout count per day
        daily_so = inv[inv["quantity"] == 0].groupby("day").size().reset_index()
        daily_so.columns = ["day", "stockout_count"]
        daily = daily.merge(daily_so, on="day", how="left")
        daily["stockout_count"] = daily["stockout_count"].fillna(0).astype(int)
        daily = daily.set_index("day")
        weekly = daily.resample("W").agg({"doh": "mean", "stockout_count": "sum", "total_inv": "last"}).reset_index()
        weekly["doh"] = weekly["doh"].round(1)
        weekly["week_label"] = weekly["day"].dt.strftime("%b %d")
        trend_data = weekly[["week_label", "doh", "stockout_count"]].tail(12).fillna(0).to_dict("records")

        # ================================================
        # Summary & detail
        # ================================================
        status_counts = doh_df["status"].value_counts().to_dict()
        total_items = len(doh_df)

        detail_df = doh_df[doh_df["ros"] > 0][[
            "store_code", "sku", "style", "category", "soh", "wh_stock",
            "ros", "doh", "status", "effective_ideal_doh", "is_topseller",
        ]].sort_values("doh").head(200)
        for c in ["is_topseller"]:
            detail_df[c] = detail_df[c].astype(bool)
        detail_data = detail_df.round(2).fillna(0).to_dict("records")

        _result = {
            "summary": {
                "overall_doh": overall_doh,
                "ideal_doh": ideal_doh,
                "total_store_skus": total_items,
                "optimal_count": int(status_counts.get("OPTIMAL", 0)),
                "overstocked_count": int(status_counts.get("OVERSTOCKED", 0)),
                "understocked_count": int(status_counts.get("UNDERSTOCKED", 0)),
                "stockedout_count": int(status_counts.get("STOCKED_OUT", 0)),
                "no_sales_count": int(status_counts.get("NO_SALES", 0)),
                "topseller_count": int(doh_df["is_topseller"].sum()),
                "include_wh": include_wh,
                "topseller_multiplier": topseller_multiplier,
                "snapshot_date": str(latest_date.date()) if pd.notna(latest_date) else None,
            },
            "store_data": store_data,
            "category_data": category_data,
            "channel_data": channel_data,
            "trend_data": trend_data,
            "detail": detail_data,
        }
        cache_set("doh_heatmap", _tid, _result, _ex)
        return _result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# =========================================================================
# DOH-14: Category-specific ideal DOH management
# =========================================================================
@router.get("/category-ideal")
async def get_category_ideal_doh():
    """Get category-specific ideal DOH settings."""
    docs = await _get_db().category_ideal_doh.find({}, {"_id": 0}).to_list(200)
    return {"categories": docs}


@router.post("/category-ideal")
async def set_category_ideal_doh(body: Dict[str, Any]):
    """Set ideal DOH for a specific category."""
    category = body.get("category", "").strip()
    ideal = body.get("ideal_doh")
    if not category or ideal is None:
        return {"error": "category and ideal_doh required"}
    await _get_db().category_ideal_doh.update_one(
        {"category": category},
        {"$set": {"category": category, "ideal_doh": int(ideal), "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"status": "ok", "category": category, "ideal_doh": int(ideal)}


# =========================================================================
# HEATMAP ENDPOINTS (DOH-16 to DOH-21)
# =========================================================================
@router.get("/heatmap")
async def get_doh_heatmap(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    store_classes: str = None,
    ideal_doh: int = None,
    view: str = "store",
):
    """
    DOH-16: Store grid heatmap (view=store)
    DOH-17: Category grid heatmap (view=category)
    DOH-18: Click store shows details (detail per store included)
    DOH-19: Filter by region
    DOH-20: Filter by store class
    DOH-21: Export data (returned as structured JSON for CSV export on frontend)
    """
    # Get the full analysis data
    result = await get_doh_analysis(
        start_date=start_date, end_date=end_date,
        categories=categories, channels=channels, regions=regions,
        store_classes=store_classes, ideal_doh=ideal_doh,
    )
    if "error" in result:
        return result

    cfg = await _get_config()
    if ideal_doh is None:
        ideal_doh = cfg.get("ideal_doh", 9)

    if view == "category":
        # DOH-17: Category heatmap
        grid = []
        for cat in result.get("category_data", []):
            total = cat.get("OPTIMAL", 0) + cat.get("OVERSTOCKED", 0) + cat.get("UNDERSTOCKED", 0) + cat.get("STOCKED_OUT", 0)
            grid.append({
                "id": cat["category"],
                "label": cat["category"],
                "doh": cat["doh"],
                "status": cat["status"],
                "inventory": cat["total_inventory"],
                "sku_count": cat["sku_count"],
                "ideal_doh": cat.get("ideal_doh", ideal_doh),
                "optimal_pct": round(cat.get("OPTIMAL", 0) / max(total, 1) * 100, 1),
                "overstocked_pct": round(cat.get("OVERSTOCKED", 0) / max(total, 1) * 100, 1),
                "understocked_pct": round(cat.get("UNDERSTOCKED", 0) / max(total, 1) * 100, 1),
                "stockedout_pct": round(cat.get("STOCKED_OUT", 0) / max(total, 1) * 100, 1),
            })
        return {"view": "category", "grid": grid, "ideal_doh": ideal_doh}
    else:
        # DOH-16: Store heatmap
        grid = []
        for s in result.get("store_data", []):
            total = s.get("OPTIMAL", 0) + s.get("OVERSTOCKED", 0) + s.get("UNDERSTOCKED", 0) + s.get("STOCKED_OUT", 0)
            grid.append({
                "id": s["store_code"],
                "label": s["store_code"],
                "doh": s["doh"],
                "status": s["status"],
                "channel": s.get("channel", "Unknown"),
                "region": s.get("region", "Unknown"),
                "store_class": s.get("store_class", "-"),
                "inventory": s["total_inventory"],
                "sku_count": s["sku_count"],
                "ideal_doh": s.get("ideal_doh", ideal_doh),
                "optimal_pct": round(s.get("OPTIMAL", 0) / max(total, 1) * 100, 1),
                "overstocked_pct": round(s.get("OVERSTOCKED", 0) / max(total, 1) * 100, 1),
                "understocked_pct": round(s.get("UNDERSTOCKED", 0) / max(total, 1) * 100, 1),
                "stockedout_pct": round(s.get("STOCKED_OUT", 0) / max(total, 1) * 100, 1),
            })
        return {"view": "store", "grid": grid, "ideal_doh": ideal_doh}


# DOH-18: Store drill-down detail
@router.get("/heatmap/detail")
async def get_heatmap_detail(
    store_code: str = None,
    category: str = None,
    start_date: str = None,
    end_date: str = None,
    ideal_doh: int = None,
):
    """Click on store/category in heatmap to see SKU-level detail."""
    cfg = await _get_config()
    if ideal_doh is None:
        ideal_doh = cfg.get("ideal_doh", 9)

    sales_df = await _cached("daily_sales")
    inv_df = await _cached("store_inventory")
    sku_df = await _cached("sku_ean_master")

    if sales_df is None or inv_df is None or sku_df is None:
        return {"error": "Required data not uploaded"}

    try:
        sales = _date_filter(sales_df.copy(), start_date, end_date, "day")
        inv = _date_filter(inv_df.copy(), start_date, end_date, "day")
        sales["day"] = pd.to_datetime(sales["day"])
        inv["day"] = pd.to_datetime(inv["day"])

        if store_code:
            sales = sales[sales["store_code"] == store_code]
            inv = inv[inv["store_code"] == store_code]

        ros_calc = sales.groupby(["store_code", "sku"]).agg(
            total_qty=("quantity", "sum"),
            live_days=("day", "nunique"),
        ).reset_index()
        ros_calc["ros"] = (ros_calc["total_qty"] / ros_calc["live_days"].clip(lower=1)).round(4)

        latest_date = inv["day"].max()
        latest_inv = inv[inv["day"] == latest_date]
        soh_agg = latest_inv.groupby(["store_code", "ean"])["quantity"].sum().reset_index()
        soh_agg.columns = ["store_code", "sku", "soh"]

        detail = ros_calc.merge(soh_agg, on=["store_code", "sku"], how="outer")
        detail["soh"] = detail["soh"].fillna(0)
        detail["ros"] = detail["ros"].fillna(0)
        detail["doh"] = np.where(detail["ros"] > 0, (detail["soh"] / detail["ros"]).round(1), np.where(detail["soh"] > 0, 9999, 0))

        if "style" in sku_df.columns:
            detail["style"] = detail["sku"].map(sku_df.groupby("ean")["style"].first()).fillna("Unknown")
        else:
            detail["style"] = "Unknown"
        if "size" in sku_df.columns:
            detail["size"] = detail["sku"].map(sku_df.groupby("ean")["size"].first()).fillna("-")
        else:
            detail["size"] = "-"

        upper = ideal_doh * 1.2
        lower = ideal_doh * 0.8

        def cls(row):
            if row["soh"] == 0 and row["ros"] > 0:
                return "STOCKED_OUT"
            if row["ros"] == 0 and row["soh"] > 0:
                return "NO_SALES"
            if row["ros"] == 0 and row["soh"] == 0:
                return "STOCKED_OUT"
            if row["doh"] > upper:
                return "OVERSTOCKED"
            if row["doh"] < lower:
                return "UNDERSTOCKED"
            return "OPTIMAL"

        detail["status"] = detail.apply(cls, axis=1)

        if category and "style" in detail.columns:
            style_df = await _cached("style_master")
            if style_df is not None and "style_code" in style_df.columns:
                cat_styles = style_df[style_df["category"] == category]["style_code"].tolist()
                detail = detail[detail["style"].isin(cat_styles)]

        detail = detail[detail["ros"] > 0].sort_values("doh").head(100)

        status_counts = detail["status"].value_counts().to_dict()
        total = len(detail)

        return {
            "store_code": store_code,
            "category": category,
            "total_skus": total,
            "status_counts": {
                "optimal": int(status_counts.get("OPTIMAL", 0)),
                "overstocked": int(status_counts.get("OVERSTOCKED", 0)),
                "understocked": int(status_counts.get("UNDERSTOCKED", 0)),
                "stocked_out": int(status_counts.get("STOCKED_OUT", 0)),
            },
            "detail": detail[["store_code", "sku", "style", "size", "soh", "ros", "doh", "status"]].round(2).fillna(0).to_dict("records"),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# =========================================================================
# CORRELATION ENDPOINTS (DOH-22 to DOH-27)
# =========================================================================
@router.get("/correlation")
async def get_doh_stockout_correlation(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    ideal_doh: int = None,
):
    """
    DOH-22: High DOH -> Low stock-outs (negative correlation)
    DOH-23: Low DOH -> High stock-outs (positive correlation)
    DOH-24: Trendline with both metrics
    DOH-25: Correlation coefficient
    DOH-26: Optimal DOH range identification
    DOH-27: Store-level correlation
    """
    cfg = await _get_config()
    if ideal_doh is None:
        ideal_doh = cfg.get("ideal_doh", 9)

    sales_df = await _cached("daily_sales")
    inv_df = await _cached("store_inventory")
    sku_df = await _cached("sku_ean_master")
    store_df = await _cached("store_master")

    if sales_df is None or inv_df is None or sku_df is None:
        return {"error": "Required data not uploaded"}

    try:
        sales = _date_filter(sales_df.copy(), start_date, end_date, "day")
        inv = _date_filter(inv_df.copy(), start_date, end_date, "day")
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

        # Weekly DOH and stock-out counts
        inv_daily = inv.groupby("day")["quantity"].sum().reset_index()
        inv_daily.columns = ["day", "total_inv"]
        sales_daily = sales.groupby("day")["quantity"].sum().reset_index()
        sales_daily.columns = ["day", "total_sales"]
        daily = inv_daily.merge(sales_daily, on="day", how="outer").sort_values("day").fillna(0)
        daily["ros_7d"] = daily["total_sales"].rolling(7, min_periods=1).mean()
        daily["doh"] = np.where(daily["ros_7d"] > 0, (daily["total_inv"] / daily["ros_7d"]).round(1), 0)
        daily_so = inv[inv["quantity"] == 0].groupby("day").size().reset_index()
        daily_so.columns = ["day", "stockout_count"]
        daily = daily.merge(daily_so, on="day", how="left")
        daily["stockout_count"] = daily["stockout_count"].fillna(0).astype(int)

        daily = daily.set_index("day")
        weekly = daily.resample("W").agg({"doh": "mean", "stockout_count": "sum"}).reset_index()
        weekly["doh"] = weekly["doh"].round(1)
        weekly["week_label"] = weekly["day"].dt.strftime("%b %d")

        # DOH-24: Trendline data
        trend_data = weekly[["week_label", "doh", "stockout_count"]].tail(12).fillna(0).to_dict("records")

        # DOH-25: Correlation coefficient
        doh_vals = weekly["doh"].values
        so_vals = weekly["stockout_count"].values
        correlation = 0.0
        if len(doh_vals) >= 3:
            # Use numpy corrcoef
            valid_mask = (doh_vals > 0) & (so_vals >= 0)
            if valid_mask.sum() >= 3:
                corr_matrix = np.corrcoef(doh_vals[valid_mask], so_vals[valid_mask])
                correlation = round(float(corr_matrix[0, 1]), 3) if not np.isnan(corr_matrix[0, 1]) else 0.0

        # DOH-22/23: Interpretation
        if correlation < -0.3:
            correlation_interpretation = "Negative correlation: Higher DOH is associated with fewer stock-outs"
        elif correlation > 0.3:
            correlation_interpretation = "Positive correlation: DOH and stock-outs move together (unusual — investigate data quality)"
        else:
            correlation_interpretation = "Weak or no linear correlation between DOH and stock-outs"

        # DOH-26: Optimal DOH range — find the DOH range with lowest stock-out rate
        # Bucket store-level DOH and compute stockout rate per bucket
        ros_calc = sales.groupby(["store_code", "sku"]).agg(
            total_qty=("quantity", "sum"),
            live_days=("day", "nunique"),
        ).reset_index()
        ros_calc["ros"] = (ros_calc["total_qty"] / ros_calc["live_days"].clip(lower=1)).round(4)

        latest_date = inv["day"].max()
        latest_inv = inv[inv["day"] == latest_date]
        soh_agg = latest_inv.groupby(["store_code", "ean"])["quantity"].sum().reset_index()
        soh_agg.columns = ["store_code", "sku", "soh"]
        store_level = ros_calc.merge(soh_agg, on=["store_code", "sku"], how="outer")
        store_level["soh"] = store_level["soh"].fillna(0)
        store_level["ros"] = store_level["ros"].fillna(0)
        store_level["doh"] = np.where(store_level["ros"] > 0, (store_level["soh"] / store_level["ros"]).round(1), 0)
        store_level["is_stockout"] = (store_level["soh"] == 0) & (store_level["ros"] > 0)

        # Aggregate per store
        store_metrics = store_level[store_level["ros"] > 0].groupby("store_code").agg(
            avg_doh=("doh", "mean"),
            total_skus=("sku", "count"),
            stockout_skus=("is_stockout", "sum"),
        ).reset_index()
        store_metrics["stockout_rate"] = (store_metrics["stockout_skus"] / store_metrics["total_skus"].clip(lower=1) * 100).round(1)
        store_metrics["avg_doh"] = store_metrics["avg_doh"].round(1)

        # DOH-26: Bucket into ranges and find the sweet spot
        bins = [0, 3, 5, 7, 9, 12, 15, 20, 30, float("inf")]
        labels = ["0-3", "3-5", "5-7", "7-9", "9-12", "12-15", "15-20", "20-30", "30+"]
        store_metrics["doh_bucket"] = pd.cut(store_metrics["avg_doh"], bins=bins, labels=labels)
        bucket_agg = store_metrics.groupby("doh_bucket", observed=True).agg(
            store_count=("store_code", "count"),
            avg_stockout_rate=("stockout_rate", "mean"),
        ).reset_index()
        bucket_agg["avg_stockout_rate"] = bucket_agg["avg_stockout_rate"].round(1)
        bucket_data = bucket_agg.to_dict("records")

        # Find optimal range (lowest stockout rate)
        optimal_range = "N/A"
        if len(bucket_agg) > 0:
            best = bucket_agg.loc[bucket_agg["avg_stockout_rate"].idxmin()]
            optimal_range = str(best["doh_bucket"])

        # DOH-27: Store-level correlation data
        store_correlation = store_metrics[[
            "store_code", "avg_doh", "total_skus", "stockout_skus", "stockout_rate",
        ]].sort_values("stockout_rate", ascending=False).head(50).round(1).to_dict("records")

        return {
            "trend_data": trend_data,
            "correlation_coefficient": correlation,
            "correlation_interpretation": correlation_interpretation,
            "optimal_doh_range": optimal_range,
            "doh_bucket_analysis": bucket_data,
            "store_correlation": store_correlation,
            "ideal_doh": ideal_doh,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# =========================================================================
# RECOMMENDATIONS (DOH-28 to DOH-35)
# =========================================================================
@router.get("/recommendations")
async def get_doh_recommendations(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    ideal_doh: int = None,
):
    """
    DOH-28: Low DOH -> Increase replenishment
    DOH-29: High DOH -> Reduce order quantity
    DOH-30: Stocked out -> Expedite replenishment
    DOH-31: Multiple styles low DOH -> Bulk recommendation
    DOH-32: Category-wide issue -> Category recommendation
    DOH-33: Store-wide issue -> Store recommendation
    DOH-34: Seasonal adjustment -> Plan for peak
    DOH-35: DOH target setting -> Ideal DOH suggestion
    """
    # Get the analysis data
    result = await get_doh_analysis(
        start_date=start_date, end_date=end_date,
        categories=categories, channels=channels, regions=regions,
        ideal_doh=ideal_doh,
    )
    if "error" in result:
        return result

    cfg = await _get_config()
    if ideal_doh is None:
        ideal_doh = cfg.get("ideal_doh", 9)
    upper = ideal_doh * 1.2
    lower = ideal_doh * 0.8

    summary = result.get("summary", {})
    store_data = result.get("store_data", [])
    category_data = result.get("category_data", [])
    detail = result.get("detail", [])

    recommendations = []

    # DOH-30: Stocked out stores
    stockedout_stores = [s for s in store_data if s["status"] == "STOCKED_OUT"]
    if stockedout_stores:
        recommendations.append({
            "id": "DOH-30",
            "priority": "critical",
            "type": "stockout",
            "title": f"Expedite replenishment for {len(stockedout_stores)} stocked-out stores",
            "description": f"Stores {', '.join(s['store_code'] for s in stockedout_stores[:5])} have critical stock-outs. Prioritize emergency replenishment for items with active demand.",
            "affected_stores": [s["store_code"] for s in stockedout_stores],
            "action": "expedite_replenishment",
        })

    # DOH-28: Low DOH stores
    understocked_stores = [s for s in store_data if s["status"] == "UNDERSTOCKED"]
    if understocked_stores:
        recommendations.append({
            "id": "DOH-28",
            "priority": "high",
            "type": "low_doh",
            "title": f"Increase replenishment frequency for {len(understocked_stores)} understocked stores",
            "description": f"These stores have DOH below {lower:.0f} days (80% of ideal {ideal_doh}d). Increase order frequency or quantities.",
            "affected_stores": [s["store_code"] for s in understocked_stores],
            "action": "increase_replenishment",
        })

    # DOH-29: High DOH stores
    overstocked_stores = [s for s in store_data if s["status"] == "OVERSTOCKED"]
    if overstocked_stores:
        recommendations.append({
            "id": "DOH-29",
            "priority": "medium",
            "type": "high_doh",
            "title": f"Reduce order quantity for {len(overstocked_stores)} overstocked stores",
            "description": f"These stores have DOH above {upper:.0f} days (120% of ideal). Reduce order quantities or consider inter-store transfers.",
            "affected_stores": [s["store_code"] for s in overstocked_stores],
            "action": "reduce_orders",
        })

    # DOH-31: Multiple styles with low DOH (bulk)
    low_doh_styles = [d for d in detail if d.get("doh", 0) > 0 and d["doh"] < lower and d.get("status") == "UNDERSTOCKED"]
    if len(low_doh_styles) >= 5:
        style_set = list(set(d.get("style", "Unknown") for d in low_doh_styles))[:10]
        recommendations.append({
            "id": "DOH-31",
            "priority": "high",
            "type": "bulk_low_doh",
            "title": f"Bulk replenishment needed for {len(low_doh_styles)} style-store combinations",
            "description": f"Styles affected include: {', '.join(style_set[:5])}. Create a bulk purchase order covering all understocked styles.",
            "affected_styles": style_set,
            "action": "bulk_replenishment",
        })

    # DOH-32: Category-wide issues
    for cat in category_data:
        if cat.get("status") == "UNDERSTOCKED":
            recommendations.append({
                "id": "DOH-32",
                "priority": "high",
                "type": "category_wide",
                "title": f"Category '{cat['category']}' has low DOH ({cat['doh']}d vs ideal {cat.get('ideal_doh', ideal_doh)}d)",
                "description": f"Entire category is understocked with {cat['sku_count']} SKUs affected. Review category-level replenishment strategy.",
                "category": cat["category"],
                "action": "category_replenishment",
            })
        elif cat.get("status") == "OVERSTOCKED":
            recommendations.append({
                "id": "DOH-32",
                "priority": "medium",
                "type": "category_wide",
                "title": f"Category '{cat['category']}' is overstocked ({cat['doh']}d vs ideal {cat.get('ideal_doh', ideal_doh)}d)",
                "description": f"Consider markdown, promotions, or inter-store transfers for {cat['sku_count']} SKUs in this category.",
                "category": cat["category"],
                "action": "reduce_category_stock",
            })

    # DOH-33: Store-wide issues
    for store in store_data:
        total_skus = int(store.get("OPTIMAL", 0) + store.get("OVERSTOCKED", 0) + store.get("UNDERSTOCKED", 0) + store.get("STOCKED_OUT", 0))
        if total_skus > 10:
            stk_pct = store.get("STOCKED_OUT", 0) / max(total_skus, 1) * 100
            under_pct = store.get("UNDERSTOCKED", 0) / max(total_skus, 1) * 100
            over_pct = store.get("OVERSTOCKED", 0) / max(total_skus, 1) * 100
            if stk_pct > 30:
                recommendations.append({
                    "id": "DOH-33",
                    "priority": "critical",
                    "type": "store_wide",
                    "title": f"Store {store['store_code']} has {stk_pct:.0f}% SKUs stocked out",
                    "description": f"Investigate supply chain issues for this store. {int(store.get('STOCKED_OUT', 0))} of {total_skus} SKUs are stocked out.",
                    "store_code": store["store_code"],
                    "action": "store_investigation",
                })
            elif under_pct > 50:
                recommendations.append({
                    "id": "DOH-33",
                    "priority": "high",
                    "type": "store_wide",
                    "title": f"Store {store['store_code']} has {under_pct:.0f}% SKUs understocked",
                    "description": "Systemic understocking at this location. Review replenishment schedule and allocation priority.",
                    "store_code": store["store_code"],
                    "action": "store_replenishment_review",
                })
            elif over_pct > 50:
                recommendations.append({
                    "id": "DOH-33",
                    "priority": "medium",
                    "type": "store_wide",
                    "title": f"Store {store['store_code']} has {over_pct:.0f}% SKUs overstocked",
                    "description": "Consider reducing allocation or running targeted promotions for this store.",
                    "store_code": store["store_code"],
                    "action": "store_overstock_action",
                })

    # DOH-34: Seasonal adjustment
    sales_df = await _cached("daily_sales")
    if sales_df is not None:
        s = sales_df.copy()
        s["day"] = pd.to_datetime(s["day"])
        s["month"] = s["day"].dt.month
        monthly_sales = s.groupby("month")["quantity"].sum()
        if len(monthly_sales) >= 2:
            avg_monthly = monthly_sales.mean()
            peak_months = monthly_sales[monthly_sales > avg_monthly * 1.3].index.tolist()
            if peak_months:
                month_names = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                               7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
                peak_labels = [month_names.get(m, str(m)) for m in peak_months]
                recommendations.append({
                    "id": "DOH-34",
                    "priority": "medium",
                    "type": "seasonal",
                    "title": f"Plan higher inventory for peak months: {', '.join(peak_labels)}",
                    "description": f"Sales data shows {len(peak_months)} peak months with >30% above average sales. Increase DOH target by 30-50% during these periods.",
                    "peak_months": peak_months,
                    "action": "seasonal_planning",
                })

    # DOH-35: DOH target setting
    # Suggest ideal DOH based on the current data distribution
    overall = summary.get("overall_doh", 0)
    stockout_pct = summary.get("stockedout_count", 0) / max(summary.get("total_store_skus", 1), 1) * 100
    if overall > 0:
        if stockout_pct > 20:
            suggested = max(ideal_doh, round(overall * 1.5))
            recommendations.append({
                "id": "DOH-35",
                "priority": "high",
                "type": "target_setting",
                "title": f"Increase ideal DOH target from {ideal_doh}d to {suggested}d",
                "description": f"With {stockout_pct:.0f}% stock-outs, current ideal DOH of {ideal_doh} days is too aggressive. Suggest increasing to {suggested} days.",
                "current_ideal": ideal_doh,
                "suggested_ideal": suggested,
                "action": "adjust_target",
            })
        elif stockout_pct < 5 and summary.get("overstocked_count", 0) > summary.get("understocked_count", 0):
            suggested = max(3, round(ideal_doh * 0.8))
            recommendations.append({
                "id": "DOH-35",
                "priority": "low",
                "type": "target_setting",
                "title": f"Consider reducing ideal DOH from {ideal_doh}d to {suggested}d",
                "description": f"Low stock-out rate ({stockout_pct:.1f}%) with more overstocked than understocked items. Reducing target could free up working capital.",
                "current_ideal": ideal_doh,
                "suggested_ideal": suggested,
                "action": "adjust_target",
            })

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recommendations.sort(key=lambda r: priority_order.get(r.get("priority", "low"), 3))

    return {
        "recommendations": recommendations,
        "summary": {
            "total_recommendations": len(recommendations),
            "critical_count": len([r for r in recommendations if r["priority"] == "critical"]),
            "high_count": len([r for r in recommendations if r["priority"] == "high"]),
            "medium_count": len([r for r in recommendations if r["priority"] == "medium"]),
            "low_count": len([r for r in recommendations if r["priority"] == "low"]),
            "overall_doh": summary.get("overall_doh", 0),
            "ideal_doh": ideal_doh,
        },
    }
