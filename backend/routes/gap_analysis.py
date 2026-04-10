"""
Gap Analysis Endpoints — Extracted from server.py
Covers: ROS Analysis, ROS Gap (Healthy Size Set), Size Gap, NOOS.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, List, Any
import pandas as pd
import numpy as np
import os
import io
import logging

from services.cache_service import cache_get, cache_set, cache_extra, get_tenant_id as _cache_tid

logger = logging.getLogger(__name__)

router = APIRouter(tags=["gap-analysis"])

_client: Optional[AsyncIOMotorClient] = None
_get_cached_data = None
_get_db = None
_apply_date_filter = None
_apply_channel_filter = None
_apply_region_filter = None
_apply_category_filter = None


def init_gap_analysis(mongo_client, get_cached_data_func, get_db_func,
                      apply_date_filter_func, apply_channel_filter_func,
                      apply_region_filter_func, apply_category_filter_func):
    global _client, _get_cached_data, _get_db
    global _apply_date_filter, _apply_channel_filter, _apply_region_filter, _apply_category_filter
    _client = mongo_client
    _get_cached_data = get_cached_data_func
    _get_db = get_db_func
    _apply_date_filter = apply_date_filter_func
    _apply_channel_filter = apply_channel_filter_func
    _apply_region_filter = apply_region_filter_func
    _apply_category_filter = apply_category_filter_func


# ─────────── ROS Analysis ───────────

@router.get("/analytics/ros")
async def get_ros_analysis(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    min_size: int = None,
    min_size_percent: int = None
):
    """Calculate Rate of Sale analysis with filters"""
    _tid = _cache_tid()
    _ex = cache_extra(sd=start_date, ed=end_date, cat=categories, ch=channels, rg=regions, ms=min_size, msp=min_size_percent)
    _hit, _data = cache_get("gap_analysis", _tid, _ex)
    if _hit:
        return _data
    sales_df = await _get_cached_data('daily_sales')
    sku_df = await _get_cached_data('sku_ean_master')
    style_df = await _get_cached_data('style_master')
    store_df = await _get_cached_data('store_master')

    if sales_df is None or sku_df is None:
        return {"error": "Required data not uploaded", "data": []}

    try:
        sales_df = _apply_date_filter(sales_df, start_date, end_date, 'day')
        if channels:
            sales_df = _apply_channel_filter(sales_df, channels.split(','))
        if regions and store_df is not None:
            sales_df = _apply_region_filter(sales_df, regions.split(','), store_df)

        sales_df['day'] = pd.to_datetime(sales_df['day'])
        sales_with_sku = sales_df.merge(sku_df[['ean', 'style', 'size']], left_on='sku', right_on='ean', how='left')

        if categories and style_df is not None:
            sales_with_sku = _apply_category_filter(sales_with_sku, categories.split(','), style_df)

        if len(sales_with_sku) == 0:
            return {"error": "No data matches the selected filters", "data": [], "summary": {}}

        ros_by_style = sales_with_sku.groupby('style').agg({
            'quantity': 'sum', 'revenue': 'sum', 'day': 'nunique', 'store_code': 'nunique'
        }).reset_index()
        ros_by_style.columns = ['style', 'total_quantity', 'total_revenue', 'live_days', 'store_count']
        ros_by_style['ros'] = (ros_by_style['total_quantity'] / ros_by_style['live_days']).round(2)
        ros_by_style['revenue_per_day'] = (ros_by_style['total_revenue'] / ros_by_style['live_days']).round(2)

        median_ros = ros_by_style['ros'].median()
        ros_by_style['status'] = ros_by_style['ros'].apply(lambda x: 'healthy' if x >= median_ros else 'broken')

        if min_size_percent and min_size_percent > 0:
            threshold = ros_by_style['ros'].quantile(min_size_percent / 100)
            ros_by_style['status'] = ros_by_style['ros'].apply(lambda x: 'healthy' if x >= threshold else 'broken')

        ros_by_style['potential_sales'] = ros_by_style.apply(
            lambda row: (median_ros * row['live_days']) if row['status'] == 'broken' else row['total_quantity'], axis=1
        )
        ros_by_style['sales_loss'] = (ros_by_style['potential_sales'] - ros_by_style['total_quantity']).clip(lower=0).round(0)

        _result = {
            "summary": {
                "total_styles": len(ros_by_style),
                "healthy_count": len(ros_by_style[ros_by_style['status'] == 'healthy']),
                "broken_count": len(ros_by_style[ros_by_style['status'] == 'broken']),
                "avg_healthy_ros": float(ros_by_style[ros_by_style['status'] == 'healthy']['ros'].mean()),
                "avg_broken_ros": float(ros_by_style[ros_by_style['status'] == 'broken']['ros'].mean()),
                "total_sales_loss": float(ros_by_style['sales_loss'].sum())
            },
            "data": ros_by_style.fillna(0).to_dict('records'),
            "data_source": "uploaded"
        }
        cache_set("gap_analysis", _tid, _result, _ex)
        return _result
    except Exception as e:
        logger.error(f"ROS analysis error: {str(e)}")
        return {"error": str(e), "data": [], "data_source": "error"}


# ─────────── ROS Gap Analysis ───────────

@router.get("/analytics/ros-gap")
async def get_ros_gap_analysis(
    start_date: str = None, end_date: str = None, categories: str = None,
    channels: str = None, regions: str = None, brands: str = None,
    store: str = None, sort_by: str = "sales_loss",
):
    """PRD-based ROS Gap Analysis with Healthy Size Set, Sales Loss, and NOOS."""
    sales_df = await _get_cached_data('daily_sales')
    inventory_df = await _get_cached_data('store_inventory')
    sku_df = await _get_cached_data('sku_ean_master')
    style_df = await _get_cached_data('style_master')
    store_df = await _get_cached_data('store_master')

    if sales_df is None or inventory_df is None or sku_df is None:
        return {"error": "Required data not uploaded (need daily_sales, store_inventory, sku_ean_master)", "data": {}}

    try:
        sales_df = _apply_date_filter(sales_df, start_date, end_date, 'day')
        inventory_df = _apply_date_filter(inventory_df, start_date, end_date, 'day')

        if channels:
            channel_list = channels.split(',')
            sales_df = _apply_channel_filter(sales_df, channel_list)
            inventory_df = _apply_channel_filter(inventory_df, channel_list)
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_df = _apply_region_filter(sales_df, region_list, store_df)
            inventory_df = _apply_region_filter(inventory_df, region_list, store_df)

        sales_df['day'] = pd.to_datetime(sales_df['day'])
        inventory_df['day'] = pd.to_datetime(inventory_df['day'])

        sales_sku = sales_df.merge(sku_df[['ean', 'style', 'size']], left_on='sku', right_on='ean', how='left')
        inv_sku = inventory_df.merge(sku_df[['ean', 'style', 'size']], on='ean', how='left')

        if categories and style_df is not None:
            category_list = categories.split(',')
            sales_sku = _apply_category_filter(sales_sku, category_list, style_df)
            inv_sku = _apply_category_filter(inv_sku, category_list, style_df)

        if brands and style_df is not None and 'brand' in style_df.columns:
            brand_list = [b.strip() for b in brands.split(',')]
            filtered_styles = style_df[style_df['brand'].isin(brand_list)]['style_code'].tolist()
            sales_sku = sales_sku[sales_sku['style'].isin(filtered_styles)]
            inv_sku = inv_sku[inv_sku['style'].isin(filtered_styles)]

        if store:
            sales_sku = sales_sku[sales_sku['store_code'] == store]
            inv_sku = inv_sku[inv_sku['store_code'] == store]

        if len(sales_sku) == 0:
            return {"error": "No data matches the selected filters", "data": {}}

        # 1. Healthy Size Set classification
        style_total_sizes = sku_df.groupby('style')['size'].nunique().reset_index()
        style_total_sizes.columns = ['style', 'total_sizes']

        inv_pos = inv_sku[inv_sku['quantity'] > 0]
        daily_size_avail = inv_pos.groupby(['store_code', 'style', 'day'])['size'].nunique().reset_index()
        daily_size_avail.columns = ['store_code', 'style', 'day', 'available_sizes']
        daily_size_avail = daily_size_avail.merge(style_total_sizes, on='style', how='left')
        daily_size_avail['size_pct'] = (daily_size_avail['available_sizes'] / daily_size_avail['total_sizes'].clip(lower=1) * 100)

        _cfg = await _get_db().analysis_config.find_one({"_id": "main"}, {"_id": 0})
        _psa_threshold = (_cfg or {}).get("pivotal_size_threshold", 75)
        daily_size_avail['is_healthy'] = daily_size_avail['size_pct'] >= _psa_threshold

        # 2. True Live Days & Raw ROS
        true_live = inv_sku[inv_sku['quantity'] > 0].groupby(['store_code', 'style'])['day'].nunique().reset_index()
        true_live.columns = ['store_code', 'style', 'true_live_days']

        net_sales = sales_sku.groupby(['store_code', 'style']).agg(
            net_sales_qty=('quantity', 'sum'), revenue=('revenue', 'sum')
        ).reset_index()

        ros_df = net_sales.merge(true_live, on=['store_code', 'style'], how='outer').fillna(0)
        ros_df['raw_ros'] = np.where(ros_df['true_live_days'] > 0, (ros_df['net_sales_qty'] / ros_df['true_live_days']).round(3), 0)

        # 3. Healthy/Broken days
        healthy_days = daily_size_avail[daily_size_avail['is_healthy']].groupby(['store_code', 'style'])['day'].nunique().reset_index()
        healthy_days.columns = ['store_code', 'style', 'healthy_days']
        broken_days = daily_size_avail[~daily_size_avail['is_healthy']].groupby(['store_code', 'style'])['day'].nunique().reset_index()
        broken_days.columns = ['store_code', 'style', 'broken_days']

        ros_df = ros_df.merge(healthy_days, on=['store_code', 'style'], how='left')
        ros_df = ros_df.merge(broken_days, on=['store_code', 'style'], how='left')
        ros_df['healthy_days'] = ros_df['healthy_days'].fillna(0).astype(int)
        ros_df['broken_days'] = ros_df['broken_days'].fillna(0).astype(int)

        # Sales split by health
        sales_daily = sales_sku.groupby(['store_code', 'style', 'day'])['quantity'].sum().reset_index()
        sales_daily.columns = ['store_code', 'style', 'day', 'day_qty']
        day_health = daily_size_avail[['store_code', 'style', 'day', 'is_healthy']].drop_duplicates()
        sales_tagged = sales_daily.merge(day_health, on=['store_code', 'style', 'day'], how='left')
        sales_tagged['is_healthy'] = sales_tagged['is_healthy'].fillna(False).astype(bool)

        healthy_sales = sales_tagged[sales_tagged['is_healthy']].groupby(['store_code', 'style'])['day_qty'].sum().reset_index()
        healthy_sales.columns = ['store_code', 'style', 'healthy_sales']
        broken_sales = sales_tagged[~sales_tagged['is_healthy']].groupby(['store_code', 'style'])['day_qty'].sum().reset_index()
        broken_sales.columns = ['store_code', 'style', 'broken_sales']

        ros_df = ros_df.merge(healthy_sales, on=['store_code', 'style'], how='left')
        ros_df = ros_df.merge(broken_sales, on=['store_code', 'style'], how='left')
        ros_df['healthy_sales'] = ros_df['healthy_sales'].fillna(0)
        ros_df['broken_sales'] = ros_df['broken_sales'].fillna(0)
        ros_df['healthy_ros'] = np.where(ros_df['healthy_days'] > 0, (ros_df['healthy_sales'] / ros_df['healthy_days']).round(3), 0)

        # 4. Sales Loss
        ros_df['sales_loss'] = ((ros_df['healthy_ros'] * ros_df['broken_days']) - ros_df['broken_sales']).clip(lower=0).round(1)
        ros_df['ros_gap'] = (ros_df['healthy_ros'] - ros_df['raw_ros']).round(3)
        ros_df['status'] = np.where(ros_df['healthy_days'] > ros_df['broken_days'], 'Healthy', 'Broken')

        # 5. NOOS
        total_period_days = max(inventory_df['day'].nunique(), 1)
        sales_day_count = sales_sku.groupby(['store_code', 'style'])['day'].nunique().reset_index()
        sales_day_count.columns = ['store_code', 'style', 'sales_days']
        inv_day_count = inv_sku[inv_sku['quantity'] > 0].groupby(['store_code', 'style'])['day'].nunique().reset_index()
        inv_day_count.columns = ['store_code', 'style', 'inv_days']
        noos_df = sales_day_count.merge(inv_day_count, on=['store_code', 'style'], how='outer').fillna(0)
        noos_df['sales_consistency'] = (noos_df['sales_days'] / total_period_days * 100).round(1)
        noos_df['inv_consistency'] = (noos_df['inv_days'] / total_period_days * 100).round(1)
        noos_df['is_noos'] = (noos_df['sales_consistency'] >= 80) & (noos_df['inv_consistency'] >= 80)

        noos_styles = noos_df.groupby('style').agg(
            store_count=('store_code', 'nunique'), noos_store_count=('is_noos', 'sum'),
            avg_sales_consistency=('sales_consistency', 'mean'), avg_inv_consistency=('inv_consistency', 'mean')
        ).reset_index()
        noos_styles['noos_pct'] = (noos_styles['noos_store_count'] / noos_styles['store_count'].clip(lower=1) * 100).round(1)
        noos_styles['is_noos'] = noos_styles['noos_pct'] >= 50

        # 6. Aggregated views
        style_ros = ros_df.groupby('style').agg(
            healthy_ros=('healthy_ros', 'mean'), raw_ros=('raw_ros', 'mean'),
            total_sales_loss=('sales_loss', 'sum'), healthy_days=('healthy_days', 'sum'),
            broken_days=('broken_days', 'sum'), store_count=('store_code', 'nunique'),
            total_qty=('net_sales_qty', 'sum'), total_revenue=('revenue', 'sum')
        ).reset_index()
        style_ros['ros_gap'] = (style_ros['healthy_ros'] - style_ros['raw_ros']).round(3)
        style_ros['status'] = np.where(style_ros['healthy_days'] > style_ros['broken_days'], 'Healthy', 'Broken')

        sort_map = {'sales_loss': ('total_sales_loss', False), 'gap_size': ('ros_gap', False), 'ros': ('raw_ros', False), 'revenue': ('total_revenue', False)}
        sort_col, sort_asc = sort_map.get(sort_by, ('total_sales_loss', False))
        style_ros = style_ros.sort_values(sort_col, ascending=sort_asc)

        store_health = ros_df.groupby('store_code').agg(
            total_healthy=('healthy_days', 'sum'), total_broken=('broken_days', 'sum'),
            total_sales_loss=('sales_loss', 'sum'), style_count=('style', 'nunique')
        ).reset_index()
        store_health['total_days'] = store_health['total_healthy'] + store_health['total_broken']
        store_health['healthy_pct'] = np.where(store_health['total_days'] > 0, (store_health['total_healthy'] / store_health['total_days'] * 100).round(1), 0)
        store_health['broken_pct'] = (100 - store_health['healthy_pct']).round(1)
        store_health = store_health.sort_values('total_sales_loss', ascending=False)

        avg_ros_gap = float(style_ros['ros_gap'].mean()) if len(style_ros) > 0 else 0
        total_sales_loss = float(ros_df['sales_loss'].sum())
        total_days_all = int(ros_df['healthy_days'].sum() + ros_df['broken_days'].sum())
        healthy_coverage = round((ros_df['healthy_days'].sum() / max(total_days_all, 1)) * 100, 1)
        noos_count = int(noos_styles['is_noos'].sum())

        # Weekly trend
        weekly_trend = []
        try:
            sales_sku_copy = sales_sku.copy()
            sales_sku_copy['week'] = sales_sku_copy['day'].dt.isocalendar().week.astype(int)
            inv_sku_copy = inv_sku.copy()
            if 'day' in inv_sku_copy.columns:
                inv_sku_copy['day'] = pd.to_datetime(inv_sku_copy['day'])
                inv_sku_copy['week'] = inv_sku_copy['day'].dt.isocalendar().week.astype(int)
                weekly_health = inv_sku_copy[inv_sku_copy['quantity'] > 0].groupby(['store_code', 'style', 'week'])['size'].nunique().reset_index()
                weekly_health.columns = ['store_code', 'style', 'week', 'avail']
                weekly_health = weekly_health.merge(style_total_sizes, on='style', how='left')
                weekly_health['healthy'] = (weekly_health['avail'] / weekly_health['total_sizes'].clip(lower=1) * 100) >= _psa_threshold
                wk_agg = weekly_health.groupby('week').agg(total_combos=('store_code', 'count'), healthy_combos=('healthy', 'sum')).reset_index()
                wk_agg['healthy_pct'] = (wk_agg['healthy_combos'] / wk_agg['total_combos'].clip(lower=1) * 100).round(1)
                wk_sales = sales_sku_copy.groupby('week')['quantity'].sum().reset_index()
                wk_sales.columns = ['week', 'total_qty']
                wk_agg = wk_agg.merge(wk_sales, on='week', how='left').fillna(0)
                weekly_trend = wk_agg.sort_values('week').to_dict('records')
        except Exception:
            pass

        return {
            "summary": {
                "avg_ros_gap": round(avg_ros_gap, 3), "total_sales_loss": round(total_sales_loss, 0),
                "healthy_coverage_pct": healthy_coverage, "total_styles": len(style_ros),
                "healthy_styles": int((style_ros['status'] == 'Healthy').sum()),
                "broken_styles": int((style_ros['status'] == 'Broken').sum()),
                "noos_styles": noos_count, "total_noos_candidates": len(noos_styles)
            },
            "style_ros_gap": style_ros.round(3).fillna(0).to_dict('records'),
            "store_health": store_health.round(1).fillna(0).to_dict('records'),
            "noos_styles": noos_styles.round(1).fillna(0).to_dict('records'),
            "weekly_trend": weekly_trend,
            "data_source": "uploaded"
        }
    except Exception as e:
        logger.error(f"ROS Gap analysis error: {str(e)}")
        return {"error": str(e), "data": {}, "data_source": "error"}


# ─────────── Size Gap Analysis ───────────

@router.get("/analytics/size-gap")
async def get_size_gap_analysis(
    start_date: str = None, end_date: str = None, categories: str = None,
    channels: str = None, regions: str = None,
    understock_threshold: int = -5, overstock_threshold: int = 5
):
    """Enhanced size set gap analysis."""
    sales_df = await _get_cached_data('daily_sales')
    inventory_df = await _get_cached_data('store_inventory')
    sku_df = await _get_cached_data('sku_ean_master')
    style_df = await _get_cached_data('style_master')
    store_df = await _get_cached_data('store_master')

    if sales_df is None or sku_df is None or inventory_df is None:
        return {"error": "Required data not uploaded", "data": []}

    try:
        sales_df = _apply_date_filter(sales_df, start_date, end_date, 'day')
        inventory_df_f = inventory_df.copy()
        inventory_df_f['day'] = pd.to_datetime(inventory_df_f['day'])
        inventory_df_f = _apply_date_filter(inventory_df_f, start_date, end_date, 'day')

        if channels:
            channel_list = channels.split(',')
            sales_df = _apply_channel_filter(sales_df, channel_list)
            inventory_df_f = _apply_channel_filter(inventory_df_f, channel_list)
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_df = _apply_region_filter(sales_df, region_list, store_df)
            inventory_df_f = _apply_region_filter(inventory_df_f, region_list, store_df)

        sales_with_sku = sales_df.merge(sku_df[['ean', 'style', 'size']], left_on='sku', right_on='ean', how='left')
        inv_sku = inventory_df_f.merge(sku_df[['ean', 'style', 'size']], on='ean', how='left')

        if categories and style_df is not None:
            category_list = categories.split(',')
            sales_with_sku = _apply_category_filter(sales_with_sku, category_list, style_df)
            inv_sku = _apply_category_filter(inv_sku, category_list, style_df)

        if len(sales_with_sku) == 0:
            return {"error": "No data matches the selected filters", "data": [], "summary": {}}

        # Size gap calc
        size_dist = sales_with_sku.groupby(['style', 'size'])['quantity'].sum().reset_index()
        total_by_style = size_dist.groupby('style')['quantity'].sum().reset_index()
        total_by_style.columns = ['style', 'total_sales']
        size_dist = size_dist.merge(total_by_style, on='style')
        size_dist['sales_ratio'] = (size_dist['quantity'] / size_dist['total_sales']).round(4)

        latest_date = inventory_df_f['day'].max()
        current_inv = inventory_df_f[inventory_df_f['day'] == latest_date].copy()
        inv_with_sku_latest = current_inv.merge(sku_df[['ean', 'style', 'size']], on='ean', how='left')
        inv_by_size = inv_with_sku_latest.groupby(['style', 'size'])['quantity'].sum().reset_index()
        inv_by_size.columns = ['style', 'size', 'current_qty']
        total_inv = inv_by_size.groupby('style')['current_qty'].sum().reset_index()
        total_inv.columns = ['style', 'total_inv']

        gap_df = inv_by_size.merge(size_dist[['style', 'size', 'sales_ratio']], on=['style', 'size'], how='outer')
        gap_df = gap_df.merge(total_inv, on='style', how='left')
        gap_df['sales_ratio'] = gap_df['sales_ratio'].fillna(0.1)
        gap_df['current_qty'] = gap_df['current_qty'].fillna(0)
        gap_df['total_inv'] = gap_df['total_inv'].fillna(0)
        gap_df['ideal_qty'] = (gap_df['total_inv'] * gap_df['sales_ratio']).round(0)
        gap_df['gap'] = (gap_df['current_qty'] - gap_df['ideal_qty']).round(0)
        gap_df['status'] = gap_df['gap'].apply(lambda x: 'Overstock' if x >= overstock_threshold else 'Understock' if x <= understock_threshold else 'Optimal')
        status_counts = gap_df['status'].value_counts().to_dict()

        # Healthy size set per store
        _cfg = await _get_db().analysis_config.find_one({"_id": "main"}, {"_id": 0})
        _psa = (_cfg or {}).get("pivotal_size_threshold", 75)
        style_total_sizes = sku_df.groupby('style')['size'].nunique().reset_index()
        style_total_sizes.columns = ['style', 'total_sizes']

        pos = inv_sku[inv_sku['quantity'] > 0]
        store_style_avail = pos[pos['day'] == latest_date].groupby(['store_code', 'style'])['size'].nunique().reset_index()
        store_style_avail.columns = ['store_code', 'style', 'available_sizes']
        all_combos = inv_sku[inv_sku['day'] == latest_date][['store_code', 'style']].drop_duplicates()
        health_df = all_combos.merge(store_style_avail, on=['store_code', 'style'], how='left')
        health_df['available_sizes'] = health_df['available_sizes'].fillna(0).astype(int)
        health_df = health_df.merge(style_total_sizes, on='style', how='left')
        health_df['total_sizes'] = health_df['total_sizes'].fillna(1).astype(int)
        health_df['size_pct'] = (health_df['available_sizes'] / health_df['total_sizes'].clip(lower=1) * 100).round(1)
        health_df['is_healthy'] = health_df['size_pct'] >= _psa

        healthy_count = int(health_df['is_healthy'].sum())
        unhealthy_count = len(health_df) - healthy_count

        # Sales loss
        sales_agg = sales_with_sku.groupby(['store_code', 'style']).agg(total_qty=('quantity', 'sum'), total_rev=('revenue', 'sum')).reset_index()
        days_in_period = max(sales_with_sku['day'].nunique() if 'day' in sales_with_sku.columns else 1, 1)
        sales_agg['ros'] = (sales_agg['total_qty'] / days_in_period).round(3)
        health_loss = health_df.merge(sales_agg[['store_code', 'style', 'ros', 'total_rev']], on=['store_code', 'style'], how='left').fillna(0)
        health_loss['estimated_loss'] = np.where(~health_loss['is_healthy'], (health_loss['ros'] * (1 - health_loss['size_pct'] / 100) * days_in_period).round(1), 0)
        total_estimated_loss = float(health_loss['estimated_loss'].sum())

        # Store comparison
        store_comparison = health_df.groupby('store_code').agg(
            total_combos=('style', 'count'), healthy_count=('is_healthy', 'sum'), avg_size_pct=('size_pct', 'mean')
        ).reset_index()
        store_comparison['healthy_pct'] = (store_comparison['healthy_count'] / store_comparison['total_combos'].clip(lower=1) * 100).round(1)
        store_comparison = store_comparison.sort_values('healthy_pct', ascending=True)

        # Category breakdown
        category_breakdown = []
        if style_df is not None and 'category' in style_df.columns:
            health_cat = health_df.merge(style_df[['style_code', 'category']].rename(columns={'style_code': 'style'}), on='style', how='left')
            cat_agg = health_cat.groupby('category').agg(total=('style', 'count'), healthy=('is_healthy', 'sum'), avg_pct=('size_pct', 'mean')).reset_index()
            cat_agg['healthy_pct'] = (cat_agg['healthy'] / cat_agg['total'].clip(lower=1) * 100).round(1)
            category_breakdown = cat_agg.fillna(0).to_dict('records')

        # Gender breakdown
        gender_breakdown = []
        if style_df is not None and 'gender' in style_df.columns:
            health_gen = health_df.merge(style_df[['style_code', 'gender']].rename(columns={'style_code': 'style'}), on='style', how='left')
            gen_agg = health_gen.groupby('gender').agg(total=('style', 'count'), healthy=('is_healthy', 'sum'), avg_pct=('size_pct', 'mean')).reset_index()
            gen_agg['healthy_pct'] = (gen_agg['healthy'] / gen_agg['total'].clip(lower=1) * 100).round(1)
            gender_breakdown = gen_agg.fillna(0).to_dict('records')

        # Weekly trend
        weekly_trend = []
        try:
            inv_sku_copy = inv_sku.copy()
            inv_sku_copy['week'] = inv_sku_copy['day'].dt.isocalendar().week.astype(int)
            wk_avail = inv_sku_copy[inv_sku_copy['quantity'] > 0].groupby(['store_code', 'style', 'week'])['size'].nunique().reset_index()
            wk_avail.columns = ['store_code', 'style', 'week', 'avail']
            wk_avail = wk_avail.merge(style_total_sizes, on='style', how='left')
            wk_avail['healthy'] = (wk_avail['avail'] / wk_avail['total_sizes'].clip(lower=1) * 100) >= _psa
            wk_trend = wk_avail.groupby('week').agg(total=('store_code', 'count'), healthy=('healthy', 'sum')).reset_index()
            wk_trend['healthy_pct'] = (wk_trend['healthy'] / wk_trend['total'].clip(lower=1) * 100).round(1)
            weekly_trend = wk_trend.sort_values('week').to_dict('records')
        except Exception:
            pass

        return {
            "summary": {
                "overstock": status_counts.get('Overstock', 0), "understock": status_counts.get('Understock', 0),
                "optimal": status_counts.get('Optimal', 0), "total_gap": abs(gap_df['gap']).sum(),
                "healthy_store_styles": healthy_count, "unhealthy_store_styles": unhealthy_count,
                "healthy_pct": round(healthy_count / max(healthy_count + unhealthy_count, 1) * 100, 1),
                "total_estimated_loss": total_estimated_loss, "psa_threshold": _psa,
            },
            "data": gap_df.dropna(subset=['style']).fillna(0).to_dict('records'),
            "store_health": health_df.fillna(0).to_dict('records'),
            "store_comparison": store_comparison.fillna(0).to_dict('records'),
            "category_breakdown": category_breakdown,
            "gender_breakdown": gender_breakdown,
            "weekly_trend": weekly_trend,
            "data_source": "uploaded",
        }
    except Exception as e:
        logger.error(f"Size gap analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "data": [], "data_source": "error"}


# ─────────── NOOS Analysis ───────────

@router.get("/analytics/noos")
async def get_noos_analysis(
    start_date: str = None, end_date: str = None, categories: str = None,
    channels: str = None, regions: str = None, export_all: bool = False,
):
    """Enhanced NOOS analysis."""
    sales_df = await _get_cached_data('daily_sales')
    inventory_df = await _get_cached_data('store_inventory')
    sku_df = await _get_cached_data('sku_ean_master')
    style_df = await _get_cached_data('style_master')
    store_df = await _get_cached_data('store_master')

    if sales_df is None or inventory_df is None or sku_df is None:
        return {"error": "Required data not uploaded", "data": []}

    try:
        sales_df = _apply_date_filter(sales_df, start_date, end_date, 'day')
        inventory_df = _apply_date_filter(inventory_df, start_date, end_date, 'day')

        if channels:
            channel_list = channels.split(',')
            sales_df = _apply_channel_filter(sales_df, channel_list)
            inventory_df = _apply_channel_filter(inventory_df, channel_list)
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_df = _apply_region_filter(sales_df, region_list, store_df)
            inventory_df = _apply_region_filter(inventory_df, region_list, store_df)

        sales_df['day'] = pd.to_datetime(sales_df['day'])
        inventory_df['day'] = pd.to_datetime(inventory_df['day'])

        inv_with_sku = inventory_df.merge(sku_df[['ean', 'style']], on='ean', how='left')
        if categories and style_df is not None:
            category_list = categories.split(',')
            inv_with_sku = _apply_category_filter(inv_with_sku, category_list, style_df)

        if len(inv_with_sku) == 0:
            return {"error": "No data matches the selected filters", "data": [], "summary": {}}

        exposure = inv_with_sku[inv_with_sku['quantity'] > 0].groupby(['store_code', 'style'])['day'].nunique().reset_index()
        exposure.columns = ['store_code', 'style', 'exposure_days']
        total_days = max(inventory_df['day'].nunique(), sales_df['day'].nunique(), 1)
        exposure['availability_pct'] = (exposure['exposure_days'] / total_days * 100).round(1)

        sales_with_sku = sales_df.merge(sku_df[['ean', 'style']], left_on='sku', right_on='ean', how='left')
        if categories and style_df is not None:
            sales_with_sku = _apply_category_filter(sales_with_sku, category_list, style_df)
        style_sales = sales_with_sku.groupby(['store_code', 'style']).agg(
            quantity=('quantity', 'sum'), revenue=('revenue', 'sum'), sales_days=('day', 'nunique')
        ).reset_index()
        style_sales['sales_pct'] = (style_sales['sales_days'] / max(total_days, 1) * 100).round(1)

        noos_df = exposure.merge(style_sales, on=['store_code', 'style'], how='outer').fillna(0)

        # Exclude new styles
        first_sale = sales_with_sku.groupby('style')['day'].min().reset_index()
        first_sale.columns = ['style', 'first_sale_date']
        period_end = sales_df['day'].max() if len(sales_df) > 0 else pd.Timestamp.now()
        first_sale['style_age_days'] = (period_end - first_sale['first_sale_date']).dt.days
        noos_df = noos_df.merge(first_sale[['style', 'style_age_days']], on='style', how='left')
        noos_df['style_age_days'] = noos_df['style_age_days'].fillna(0).astype(int)
        noos_df['is_new_style'] = noos_df['style_age_days'] < 30

        # Seasonal exclusion
        noos_df['is_seasonal_excluded'] = False
        if style_df is not None and 'season' in style_df.columns:
            current_month = period_end.month if hasattr(period_end, 'month') else 1
            season_prefix = 'SS' if 3 <= current_month <= 8 else 'AW'
            season_map = style_df[['style_code', 'season']].rename(columns={'style_code': 'style'})
            noos_df = noos_df.merge(season_map, on='style', how='left')
            noos_df['season'] = noos_df['season'].fillna('Unknown')
            generic_seasons = ['All-Season', 'Unknown', 'Perennial', '']
            noos_df['is_seasonal_excluded'] = ~(noos_df['season'].str.startswith(season_prefix) | noos_df['season'].isin(generic_seasons))

        _cfg = await _get_db().analysis_config.find_one({"_id": "main"}, {"_id": 0})
        min_shelf_life = (_cfg or {}).get("min_shelf_life_days", 30)
        noos_df['meets_shelf_life'] = noos_df['exposure_days'] >= min_shelf_life
        noos_df['noos_candidate'] = (
            noos_df['meets_shelf_life'] & (noos_df['quantity'] > 0) & (noos_df['availability_pct'] >= 80)
            & (noos_df['sales_pct'] >= 80) & (~noos_df['is_new_style']) & (~noos_df['is_seasonal_excluded'])
        )

        # Low stock alert
        latest_date = inventory_df['day'].max()
        latest_inv = inv_with_sku[inv_with_sku['day'] == latest_date]
        current_stock = latest_inv.groupby(['store_code', 'style'])['quantity'].sum().reset_index()
        current_stock.columns = ['store_code', 'style', 'current_stock']
        noos_df = noos_df.merge(current_stock, on=['store_code', 'style'], how='left')
        noos_df['current_stock'] = noos_df['current_stock'].fillna(0)
        noos_df['daily_avg_sales'] = np.where(noos_df['sales_days'] > 0, noos_df['quantity'] / noos_df['sales_days'], 0)
        noos_df['stock_threshold'] = (noos_df['daily_avg_sales'] * 30 * 0.8).round(0)
        noos_df['low_stock_alert'] = noos_df['noos_candidate'] & (noos_df['current_stock'] < noos_df['stock_threshold']) & (noos_df['current_stock'] > 0)

        # Recovery plan
        def recovery_plan(row):
            if not row.get('noos_candidate', False):
                return "Not NOOS - no action needed"
            if row.get('low_stock_alert', False):
                return f"URGENT: Replenish {int(row['stock_threshold'] - row['current_stock'])} units. Current stock covers ~{int(row['current_stock'] / max(row['daily_avg_sales'], 0.1))} days."
            if row.get('availability_pct', 0) < 90:
                return "Monitor: Availability below 90%. Ensure consistent replenishment."
            return "Healthy NOOS - maintain current stock levels."
        noos_df['recovery_plan'] = noos_df.apply(recovery_plan, axis=1)

        noos_candidates = int(noos_df['noos_candidate'].sum())
        low_stock_count = int(noos_df['low_stock_alert'].sum())

        export_cols = ['store_code', 'style', 'exposure_days', 'availability_pct', 'sales_days', 'sales_pct', 'quantity', 'revenue', 'current_stock', 'noos_candidate', 'low_stock_alert', 'recovery_plan']
        export_data = noos_df[[c for c in export_cols if c in noos_df.columns]]

        if export_all:
            csv_buf = io.StringIO()
            export_data.to_csv(csv_buf, index=False)
            csv_buf.seek(0)
            return StreamingResponse(
                iter([csv_buf.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=noos_export.csv"},
            )

        return {
            "summary": {
                "total_combinations": len(noos_df), "noos_candidates": noos_candidates,
                "avg_availability": float(noos_df['availability_pct'].mean()) if len(noos_df) > 0 else 0,
                "total_revenue": float(noos_df['revenue'].sum()), "low_stock_alerts": low_stock_count,
                "new_styles_excluded": int(noos_df['is_new_style'].sum()),
                "seasonal_excluded": int(noos_df['is_seasonal_excluded'].sum()), "total_days": total_days,
            },
            "data": noos_df.fillna(0).to_dict('records'),
            "data_source": "uploaded",
        }
    except Exception as e:
        logger.error(f"NOOS analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "data": [], "data_source": "error"}



# ─────────── Data Status for Gap Analysis UX ───────────

@router.get("/analytics/data-status")
async def get_data_status():
    """Return upload status for all required file types used by Gap Analysis."""
    db = _get_db()

    REQUIRED_FILES = [
        ("style_master", "Style Master"),
        ("sku_master", "SKU Master"),
        ("store_master", "Store Master"),
        ("daily_sales", "Daily Sales"),
        ("store_inventory", "Store Inventory"),
        ("planogram", "Planogram"),
        ("warehouse_inventory", "Warehouse Inventory"),
    ]

    files = {}
    total_uploaded = 0

    for coll_name, display_name in REQUIRED_FILES:
        count = await db[coll_name].estimated_document_count()
        # V1 fallback
        if count == 0:
            v1 = await db.uploaded_files.find_one({"file_type": coll_name}, {"_id": 0, "data": 0})
            if v1:
                count = v1.get("row_count", 1)
        uploaded = count > 0
        if uploaded:
            total_uploaded += 1
        files[coll_name] = {"display_name": display_name, "uploaded": uploaded, "count": count}

    # Compute summary stats
    days_history = 0
    if files["daily_sales"]["uploaded"]:
        sales_df = await _get_cached_data("daily_sales")
        if sales_df is not None and len(sales_df) > 0:
            sales_df["day"] = pd.to_datetime(sales_df["day"], errors="coerce")
            valid = sales_df.dropna(subset=["day"])
            if len(valid):
                days_history = (valid["day"].max() - valid["day"].min()).days + 1

    return {
        "files": files,
        "summary": {
            "uploaded_count": total_uploaded,
            "total_count": len(REQUIRED_FILES),
            "styles": files["style_master"]["count"],
            "stores": files["store_master"]["count"],
            "sales_records": files["daily_sales"]["count"],
            "days_history": days_history,
        },
    }
