"""
BI Dashboard Endpoints (BI-01 to BI-35)
Covers: KPI Cards, Revenue Trends, Channel/Category/Regional Breakdown, Export
"""
from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import pandas as pd
import numpy as np
import os

router = APIRouter(prefix="/analytics/bi", tags=["bi-dashboard"])
_client: Optional[AsyncIOMotorClient] = None
_get_cached_data_func = None


def init_bi(mongo_client: AsyncIOMotorClient, get_cached_data_func=None):
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


def _catf(df, cats, style_df):
    if not cats or style_df is None:
        return df
    if "style_code" in style_df.columns and "category" in style_df.columns:
        vs = style_df[style_df["category"].isin(cats)]["style_code"].tolist()
        if "style" in df.columns:
            return df[df["style"].isin(vs)]
    return df


def _pl(p):
    return [x.strip() for x in p.split(",") if x.strip()] if p else []


# =========================================================================
# KPI OVERVIEW (BI-01 to BI-08)
# =========================================================================
@router.get("/overview")
async def get_bi_overview(
    start_date: str = None, end_date: str = None,
    categories: str = None, channels: str = None,
    regions: str = None,
):
    """
    BI-01: Total Revenue  BI-02: Total Quantity  BI-03: ASP  BI-04: Discount %
    BI-05: Trend indicators (up/down)  BI-06: WoW comparison  BI-07: YoY comparison
    BI-08: Targets (progress bars — sent as target values, rendered by frontend)
    """
    sales_df = await _cached("daily_sales")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")

    if sales_df is None:
        return {"error": "Sales data not uploaded"}

    try:
        sales = sales_df.copy()
        sales["day"] = pd.to_datetime(sales["day"])

        # Apply filters
        filtered = _filt(sales.copy(), start_date, end_date, "day")
        cl, chl, rgl = _pl(categories), _pl(channels), _pl(regions)
        if chl:
            filtered = _chf(filtered, chl)
        if rgl:
            filtered = _rgf(filtered, rgl, store_df)

        # Merge SKU for category filter and style info
        if sku_df is not None and "ean" in sku_df.columns:
            filtered = filtered.merge(sku_df[["ean", "style"]], left_on="sku", right_on="ean", how="left")
        if cl:
            filtered = _catf(filtered, cl, style_df)

        if len(filtered) == 0:
            return {"error": "No data matches filters"}

        # Current period
        total_rev = float(filtered["revenue"].sum())
        total_qty = int(filtered["quantity"].sum())
        asp = round(total_rev / max(total_qty, 1), 2)

        # Discount: if 'mrp' column exists, discount = (mrp_value - revenue) / mrp_value
        discount_pct = 0.0
        if sku_df is not None and "mrp" in sku_df.columns:
            mrp_map = sku_df.groupby("ean")["mrp"].first().to_dict()
            filtered["mrp_val"] = filtered["sku"].map(mrp_map).fillna(0) * filtered["quantity"]
            total_mrp = float(filtered["mrp_val"].sum())
            if total_mrp > 0:
                discount_pct = round((total_mrp - total_rev) / total_mrp * 100, 1)

        # BI-06: WoW comparison
        cur_min = filtered["day"].min()
        cur_max = filtered["day"].max()
        period_days = (cur_max - cur_min).days + 1
        prev_end = cur_min - pd.Timedelta(days=1)
        prev_start = prev_end - pd.Timedelta(days=period_days - 1)

        prev = _filt(sales.copy(), str(prev_start.date()), str(prev_end.date()), "day")
        if chl:
            prev = _chf(prev, chl)
        if rgl:
            prev = _rgf(prev, rgl, store_df)
        if sku_df is not None and "ean" in sku_df.columns:
            prev = prev.merge(sku_df[["ean", "style"]], left_on="sku", right_on="ean", how="left")
        if cl:
            prev = _catf(prev, cl, style_df)

        prev_rev = float(prev["revenue"].sum()) if len(prev) > 0 else 0
        prev_qty = int(prev["quantity"].sum()) if len(prev) > 0 else 0
        prev_asp = round(prev_rev / max(prev_qty, 1), 2) if prev_qty > 0 else 0

        def pct_change(cur, prv):
            if prv == 0:
                return 100.0 if cur > 0 else 0.0
            return round((cur - prv) / prv * 100, 1)

        wow_rev = pct_change(total_rev, prev_rev)
        wow_qty = pct_change(total_qty, prev_qty)
        wow_asp = pct_change(asp, prev_asp)

        # BI-07: YoY comparison
        yoy_start = cur_min - pd.DateOffset(years=1)
        yoy_end = cur_max - pd.DateOffset(years=1)
        yoy = _filt(sales.copy(), str(yoy_start.date()), str(yoy_end.date()), "day")
        if chl:
            yoy = _chf(yoy, chl)
        if rgl:
            yoy = _rgf(yoy, rgl, store_df)
        if sku_df is not None and "ean" in sku_df.columns:
            yoy = yoy.merge(sku_df[["ean", "style"]], left_on="sku", right_on="ean", how="left")
        if cl:
            yoy = _catf(yoy, cl, style_df)

        yoy_rev = float(yoy["revenue"].sum()) if len(yoy) > 0 else 0
        yoy_qty = int(yoy["quantity"].sum()) if len(yoy) > 0 else 0

        yoy_rev_pct = pct_change(total_rev, yoy_rev)
        yoy_qty_pct = pct_change(total_qty, yoy_qty)

        # BI-08: Targets (use config or defaults)
        cfg = await _db().analysis_config.find_one({"_id": "main"}, {"_id": 0}) or {}
        rev_target = cfg.get("revenue_target", total_rev * 1.1)
        qty_target = cfg.get("quantity_target", total_qty * 1.1)

        return {
            "kpis": {
                "revenue": {"value": round(total_rev, 2), "wow_change": wow_rev, "yoy_change": yoy_rev_pct,
                            "trend": "up" if wow_rev > 0 else "down" if wow_rev < 0 else "flat",
                            "target": round(rev_target, 2), "progress": round(total_rev / max(rev_target, 1) * 100, 1)},
                "quantity": {"value": total_qty, "wow_change": wow_qty, "yoy_change": yoy_qty_pct,
                             "trend": "up" if wow_qty > 0 else "down" if wow_qty < 0 else "flat",
                             "target": round(qty_target), "progress": round(total_qty / max(qty_target, 1) * 100, 1)},
                "asp": {"value": asp, "wow_change": wow_asp, "trend": "up" if wow_asp > 0 else "down" if wow_asp < 0 else "flat"},
                "discount_pct": {"value": discount_pct, "trend": "up" if discount_pct > 0 else "flat"},
            },
            "period": {"start": str(cur_min.date()), "end": str(cur_max.date()), "days": period_days},
            "prev_period": {"start": str(prev_start.date()), "end": str(prev_end.date()),
                            "revenue": round(prev_rev, 2), "quantity": prev_qty},
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# =========================================================================
# REVENUE TREND (BI-09 to BI-14)
# =========================================================================
@router.get("/revenue-trend")
async def get_revenue_trend(
    start_date: str = None, end_date: str = None,
    categories: str = None, channels: str = None,
    regions: str = None, granularity: str = "weekly",
):
    """
    BI-09: Daily trend  BI-10: Weekly trend  BI-11: Monthly trend
    BI-12: Filter by date range  BI-13: Compare periods (prev included)
    BI-14: Drill-down data available at daily level
    """
    sales_df = await _cached("daily_sales")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")

    if sales_df is None:
        return {"error": "Sales data not uploaded"}

    try:
        sales = _filt(sales_df.copy(), start_date, end_date, "day")
        cl, chl, rgl = _pl(categories), _pl(channels), _pl(regions)
        if chl:
            sales = _chf(sales, chl)
        if rgl:
            sales = _rgf(sales, rgl, store_df)
        sales["day"] = pd.to_datetime(sales["day"])
        if sku_df is not None and "ean" in sku_df.columns:
            sales = sales.merge(sku_df[["ean", "style"]], left_on="sku", right_on="ean", how="left")
        if cl:
            sales = _catf(sales, cl, style_df)

        if len(sales) == 0:
            return {"error": "No data matches filters"}

        daily = sales.groupby("day").agg(revenue=("revenue", "sum"), quantity=("quantity", "sum")).reset_index()
        daily = daily.sort_values("day")
        daily["asp"] = (daily["revenue"] / daily["quantity"].clip(lower=1)).round(2)

        # Previous period for comparison (BI-13)
        cur_min, cur_max = daily["day"].min(), daily["day"].max()
        period_days = (cur_max - cur_min).days + 1
        prev_end = cur_min - pd.Timedelta(days=1)
        prev_start = prev_end - pd.Timedelta(days=period_days - 1)

        all_sales = _filt(sales_df.copy(), str(prev_start.date()), str(prev_end.date()), "day")
        all_sales["day"] = pd.to_datetime(all_sales["day"])
        if chl:
            all_sales = _chf(all_sales, chl)
        if rgl:
            all_sales = _rgf(all_sales, rgl, store_df)
        if sku_df is not None and "ean" in sku_df.columns:
            all_sales = all_sales.merge(sku_df[["ean", "style"]], left_on="sku", right_on="ean", how="left")
        if cl:
            all_sales = _catf(all_sales, cl, style_df)
        prev_daily = all_sales.groupby("day").agg(revenue=("revenue", "sum"), quantity=("quantity", "sum")).reset_index().sort_values("day")

        daily_idx = daily.set_index("day")
        prev_idx = prev_daily.set_index("day") if len(prev_daily) > 0 else pd.DataFrame()

        if granularity == "daily":
            cur = daily_idx.reset_index()
            cur["label"] = cur["day"].dt.strftime("%b %d")
            trend = cur[["label", "revenue", "quantity", "asp"]].tail(30).round(2).fillna(0).to_dict("records")
            prev_t = []
            if len(prev_idx) > 0:
                p = prev_idx.reset_index()
                p["label"] = p["day"].dt.strftime("%b %d")
                prev_t = p[["label", "revenue", "quantity"]].tail(30).round(2).fillna(0).to_dict("records")
        elif granularity == "monthly":
            m = daily_idx.resample("ME").agg({"revenue": "sum", "quantity": "sum"}).reset_index()
            m["asp"] = (m["revenue"] / m["quantity"].clip(lower=1)).round(2)
            m["label"] = m["day"].dt.strftime("%b %Y")
            trend = m[["label", "revenue", "quantity", "asp"]].tail(12).round(2).fillna(0).to_dict("records")
            prev_t = []
            if len(prev_idx) > 0:
                pm = prev_idx.resample("M").agg({"revenue": "sum", "quantity": "sum"}).reset_index()
                pm["label"] = pm["day"].dt.strftime("%b %Y")
                prev_t = pm[["label", "revenue", "quantity"]].tail(12).round(2).fillna(0).to_dict("records")
        else:
            w = daily_idx.resample("W").agg({"revenue": "sum", "quantity": "sum"}).reset_index()
            w["asp"] = (w["revenue"] / w["quantity"].clip(lower=1)).round(2)
            w["label"] = w["day"].dt.strftime("%b %d")
            trend = w[["label", "revenue", "quantity", "asp"]].tail(12).round(2).fillna(0).to_dict("records")
            prev_t = []
            if len(prev_idx) > 0:
                pw = prev_idx.resample("W").agg({"revenue": "sum", "quantity": "sum"}).reset_index()
                pw["label"] = pw["day"].dt.strftime("%b %d")
                prev_t = pw[["label", "revenue", "quantity"]].tail(12).round(2).fillna(0).to_dict("records")

        # Daily drill-down always available (BI-14)
        drill_down = daily_idx.reset_index()
        drill_down["label"] = drill_down["day"].dt.strftime("%Y-%m-%d")
        drill = drill_down[["label", "revenue", "quantity", "asp"]].tail(90).round(2).fillna(0).to_dict("records")

        return {
            "granularity": granularity,
            "current": trend,
            "previous": prev_t,
            "drill_down": drill,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# =========================================================================
# CHANNEL BREAKDOWN (BI-15 to BI-20)
# =========================================================================
@router.get("/channels")
async def get_channel_breakdown(
    start_date: str = None, end_date: str = None,
    categories: str = None, channels: str = None,
    regions: str = None,
):
    """
    BI-15: Channel-wise revenue (pie)  BI-16: Channel-wise quantity (bar)
    BI-17: Marketplace performance  BI-18: Channel growth comparison
    BI-19: Filter by channel  BI-20: Export channel data
    """
    sales_df = await _cached("daily_sales")
    store_df = await _cached("store_master")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")

    if sales_df is None:
        return {"error": "Sales data not uploaded"}

    try:
        sales = _filt(sales_df.copy(), start_date, end_date, "day")
        sales["day"] = pd.to_datetime(sales["day"])
        cl, chl, rgl = _pl(categories), _pl(channels), _pl(regions)
        if rgl:
            sales = _rgf(sales, rgl, store_df)
        if sku_df is not None and "ean" in sku_df.columns:
            sales = sales.merge(sku_df[["ean", "style"]], left_on="sku", right_on="ean", how="left")
        if cl:
            sales = _catf(sales, cl, style_df)

        # Merge channel from store_df
        if store_df is not None and "channel" in store_df.columns:
            ch_map = store_df.groupby("store_code")["channel"].first().to_dict()
            sales["channel"] = sales["store_code"].map(ch_map).fillna("Unknown")
        elif "channel" in sales.columns:
            pass
        else:
            sales["channel"] = "Retail"

        if chl:
            sales = sales[sales["channel"].isin(chl)]

        if len(sales) == 0:
            return {"error": "No data matches filters"}

        by_channel = sales.groupby("channel").agg(
            revenue=("revenue", "sum"), quantity=("quantity", "sum"),
            store_count=("store_code", "nunique"),
        ).reset_index()
        by_channel["asp"] = (by_channel["revenue"] / by_channel["quantity"].clip(lower=1)).round(2)
        by_channel["revenue_pct"] = (by_channel["revenue"] / by_channel["revenue"].sum() * 100).round(1)
        by_channel = by_channel.sort_values("revenue", ascending=False)

        # Growth: compare first half vs second half of period
        mid = sales["day"].min() + (sales["day"].max() - sales["day"].min()) / 2
        first_half = sales[sales["day"] <= mid].groupby("channel")["revenue"].sum().rename("first_rev")
        second_half = sales[sales["day"] > mid].groupby("channel")["revenue"].sum().rename("second_rev")
        growth = pd.concat([first_half, second_half], axis=1).fillna(0)
        growth["growth_pct"] = np.where(growth["first_rev"] > 0,
            ((growth["second_rev"] - growth["first_rev"]) / growth["first_rev"] * 100).round(1), 0)
        by_channel = by_channel.merge(growth[["growth_pct"]], left_on="channel", right_index=True, how="left")
        by_channel["growth_pct"] = by_channel["growth_pct"].fillna(0)

        return {
            "channels": by_channel.round(2).fillna(0).to_dict("records"),
            "total_revenue": round(float(by_channel["revenue"].sum()), 2),
            "total_quantity": int(by_channel["quantity"].sum()),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# =========================================================================
# CATEGORY BREAKDOWN (BI-21 to BI-26)
# =========================================================================
@router.get("/categories")
async def get_category_breakdown(
    start_date: str = None, end_date: str = None,
    categories: str = None, channels: str = None,
    regions: str = None,
):
    """
    BI-21: Category-wise revenue  BI-22: Category-wise quantity
    BI-23: Top 5 categories  BI-24: Category growth rates
    BI-25: Filter by category  BI-26: Category hierarchy
    """
    sales_df = await _cached("daily_sales")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")
    store_df = await _cached("store_master")

    if sales_df is None:
        return {"error": "Sales data not uploaded"}

    try:
        sales = _filt(sales_df.copy(), start_date, end_date, "day")
        sales["day"] = pd.to_datetime(sales["day"])
        cl, chl, rgl = _pl(categories), _pl(channels), _pl(regions)
        if chl:
            sales = _chf(sales, chl)
        if rgl:
            sales = _rgf(sales, rgl, store_df)

        # Merge style + category
        if sku_df is not None and "ean" in sku_df.columns:
            sales = sales.merge(sku_df[["ean", "style"]], left_on="sku", right_on="ean", how="left")

        if style_df is not None and "style_code" in style_df.columns and "category" in style_df.columns:
            sc_map = style_df.groupby("style_code")["category"].first().to_dict()
            sales["category"] = sales["style"].map(sc_map).fillna("General") if "style" in sales.columns else "General"
        else:
            sales["category"] = "General"

        if cl:
            sales = sales[sales["category"].isin(cl)]

        if len(sales) == 0:
            return {"error": "No data matches filters"}

        by_cat = sales.groupby("category").agg(
            revenue=("revenue", "sum"), quantity=("quantity", "sum"),
            style_count=("style", "nunique") if "style" in sales.columns else ("sku", "nunique"),
        ).reset_index()
        by_cat["asp"] = (by_cat["revenue"] / by_cat["quantity"].clip(lower=1)).round(2)
        by_cat["revenue_pct"] = (by_cat["revenue"] / by_cat["revenue"].sum() * 100).round(1)
        by_cat = by_cat.sort_values("revenue", ascending=False)

        # Growth: first half vs second half
        mid = sales["day"].min() + (sales["day"].max() - sales["day"].min()) / 2
        f = sales[sales["day"] <= mid].groupby("category")["revenue"].sum().rename("first_rev")
        s = sales[sales["day"] > mid].groupby("category")["revenue"].sum().rename("second_rev")
        g = pd.concat([f, s], axis=1).fillna(0)
        g["growth_pct"] = np.where(g["first_rev"] > 0,
            ((g["second_rev"] - g["first_rev"]) / g["first_rev"] * 100).round(1), 0)
        by_cat = by_cat.merge(g[["growth_pct"]], left_on="category", right_index=True, how="left")
        by_cat["growth_pct"] = by_cat["growth_pct"].fillna(0)

        top5 = by_cat.head(5)["category"].tolist()

        # Sub-category (style-level) drill-down (BI-26)
        style_breakdown = []
        if "style" in sales.columns:
            by_style = sales.groupby(["category", "style"]).agg(
                revenue=("revenue", "sum"), quantity=("quantity", "sum")
            ).reset_index().sort_values("revenue", ascending=False)
            style_breakdown = by_style.head(30).round(2).fillna(0).to_dict("records")

        return {
            "categories": by_cat.round(2).fillna(0).to_dict("records"),
            "top5": top5,
            "style_breakdown": style_breakdown,
            "total_revenue": round(float(by_cat["revenue"].sum()), 2),
            "total_quantity": int(by_cat["quantity"].sum()),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# =========================================================================
# REGIONAL PERFORMANCE (BI-27 to BI-31)
# =========================================================================
@router.get("/regions")
async def get_regional_performance(
    start_date: str = None, end_date: str = None,
    categories: str = None, channels: str = None,
    regions: str = None,
):
    """
    BI-27: Region-wise revenue  BI-28: Region-wise growth
    BI-29: Top performing region  BI-30: Filter by region
    BI-31: City-level drill-down
    """
    sales_df = await _cached("daily_sales")
    store_df = await _cached("store_master")
    sku_df = await _cached("sku_ean_master")
    style_df = await _cached("style_master")

    if sales_df is None or store_df is None:
        return {"error": "Sales and store data required"}

    try:
        sales = _filt(sales_df.copy(), start_date, end_date, "day")
        sales["day"] = pd.to_datetime(sales["day"])
        cl, chl, rgl = _pl(categories), _pl(channels), _pl(regions)
        if chl:
            sales = _chf(sales, chl)
        if sku_df is not None and "ean" in sku_df.columns:
            sales = sales.merge(sku_df[["ean", "style"]], left_on="sku", right_on="ean", how="left")
        if cl:
            sales = _catf(sales, cl, style_df)

        # Merge region
        region_map = store_df.groupby("store_code")["region"].first().to_dict() if "region" in store_df.columns else {}
        sales["region"] = sales["store_code"].map(region_map).fillna("Unknown")

        city_map = store_df.groupby("store_code")["city"].first().to_dict() if "city" in store_df.columns else {}
        sales["city"] = sales["store_code"].map(city_map).fillna("Unknown")

        if rgl:
            sales = sales[sales["region"].isin(rgl)]

        if len(sales) == 0:
            return {"error": "No data matches filters"}

        by_region = sales.groupby("region").agg(
            revenue=("revenue", "sum"), quantity=("quantity", "sum"),
            store_count=("store_code", "nunique"),
        ).reset_index()
        by_region["asp"] = (by_region["revenue"] / by_region["quantity"].clip(lower=1)).round(2)
        by_region["revenue_pct"] = (by_region["revenue"] / by_region["revenue"].sum() * 100).round(1)

        # Growth
        mid = sales["day"].min() + (sales["day"].max() - sales["day"].min()) / 2
        f = sales[sales["day"] <= mid].groupby("region")["revenue"].sum().rename("first_rev")
        s = sales[sales["day"] > mid].groupby("region")["revenue"].sum().rename("second_rev")
        g = pd.concat([f, s], axis=1).fillna(0)
        g["growth_pct"] = np.where(g["first_rev"] > 0,
            ((g["second_rev"] - g["first_rev"]) / g["first_rev"] * 100).round(1), 0)
        by_region = by_region.merge(g[["growth_pct"]], left_on="region", right_index=True, how="left")
        by_region["growth_pct"] = by_region["growth_pct"].fillna(0)
        by_region = by_region.sort_values("revenue", ascending=False)

        top_region = by_region.iloc[0]["region"] if len(by_region) > 0 else "N/A"

        # City-level drill-down (BI-31)
        by_city = sales.groupby(["region", "city"]).agg(
            revenue=("revenue", "sum"), quantity=("quantity", "sum"),
            store_count=("store_code", "nunique"),
        ).reset_index().sort_values("revenue", ascending=False)

        return {
            "regions": by_region.round(2).fillna(0).to_dict("records"),
            "top_region": top_region,
            "city_breakdown": by_city.head(30).round(2).fillna(0).to_dict("records"),
            "total_revenue": round(float(by_region["revenue"].sum()), 2),
            "total_quantity": int(by_region["quantity"].sum()),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
