"""
Stock-Out Analysis Endpoints — Extracted from server.py
Covers: SOH=0 detection, Sales Loss, Severity, Duration, Trends,
  Heatmaps, Risk Assessment, Reorder Recommendations, Alternatives.
"""

from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, List, Any
import pandas as pd
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stock-out"])

_client: Optional[AsyncIOMotorClient] = None
_get_cached_data = None
_get_db = None
_apply_date_filter = None
_apply_channel_filter = None
_apply_region_filter = None
_apply_category_filter = None


def init_stock_out(mongo_client, get_cached_data_func, get_db_func,
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


@router.get("/analytics/stock-out")
async def get_stock_out_analysis(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None
):
    """
    PRD Stock-Out Analysis.
    Stock-out: SOH = 0 AND Last 30 Days ROS > 0
    Daily Sales Loss: ((ROS x 1) - SOH) x ASP
    Severity: LostSales x Duration x Importance
    """
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

        sku_cols = ['ean']
        if 'style' in sku_df.columns:
            sku_cols.append('style')
        if 'size' in sku_df.columns:
            sku_cols.append('size')
        if 'mrp' in sku_df.columns:
            sku_cols.append('mrp')

        sales_sku = sales_df.merge(sku_df[sku_cols], left_on='sku', right_on='ean', how='left')

        if categories and style_df is not None:
            category_list = categories.split(',')
            sales_sku = _apply_category_filter(sales_sku, category_list, style_df)

        if len(sales_sku) == 0:
            return {"error": "No data matches the selected filters", "data": {}}

        # 1. ROS per store-SKU
        ros_df = sales_sku.groupby(['store_code', 'sku']).agg(
            total_qty=('quantity', 'sum'),
            total_revenue=('revenue', 'sum'),
            live_days=('day', 'nunique')
        ).reset_index()
        ros_df['ros'] = (ros_df['total_qty'] / ros_df['live_days'].clip(lower=1)).round(3)

        if 'mrp' in sku_df.columns:
            asp_map = sku_df.groupby('ean')['mrp'].first()
            ros_df['asp'] = ros_df['sku'].map(asp_map).fillna(0)
        else:
            ros_df['asp'] = np.where(
                ros_df['total_qty'] > 0,
                (ros_df['total_revenue'] / ros_df['total_qty']).round(2),
                0
            )

        # 2. Latest SOH
        latest_date = inventory_df['day'].max()
        latest_inv = inventory_df[inventory_df['day'] == latest_date].copy()
        soh_df = latest_inv.groupby(['store_code', 'ean'])['quantity'].sum().reset_index()
        soh_df.columns = ['store_code', 'sku', 'soh']

        # 3. Identify stock-outs
        merged = ros_df.merge(soh_df, on=['store_code', 'sku'], how='left')
        merged['soh'] = merged['soh'].fillna(0)
        merged['is_stockout'] = (merged['soh'] == 0) & (merged['ros'] > 0)

        total_store_skus = len(merged)
        stockouts = merged[merged['is_stockout']]
        total_stockouts = len(stockouts)
        stockout_rate = round((total_stockouts / max(total_store_skus, 1)) * 100, 1)

        # 4. Sales Loss
        stockouts = stockouts.copy()
        stockouts['daily_sales_loss'] = ((stockouts['ros'] * 1 - stockouts['soh']) * stockouts['asp']).clip(lower=0).round(2)
        total_lost_sales = float(stockouts['daily_sales_loss'].sum())

        # 5. Duration
        inv_with_sku = inventory_df.merge(sku_df[['ean']].drop_duplicates(), on='ean', how='inner')
        zero_days = inv_with_sku[inv_with_sku['quantity'] == 0].groupby(['store_code', 'ean'])['day'].nunique().reset_index()
        zero_days.columns = ['store_code', 'sku', 'stockout_days']
        stockouts = stockouts.merge(zero_days, on=['store_code', 'sku'], how='left')
        stockouts['stockout_days'] = stockouts['stockout_days'].fillna(1).astype(int)
        stockouts['severity'] = (stockouts['daily_sales_loss'] * stockouts['stockout_days']).round(2)

        # 6. Top SKUs
        if 'style' in sku_df.columns:
            sku_style_map = sku_df.groupby('ean')['style'].first()
            stockouts['style'] = stockouts['sku'].map(sku_style_map).fillna('Unknown')
        else:
            stockouts['style'] = 'Unknown'

        top_skus = stockouts.groupby('sku').agg(
            stockout_count=('store_code', 'nunique'),
            total_daily_loss=('daily_sales_loss', 'sum'),
            avg_ros=('ros', 'mean'),
            avg_asp=('asp', 'mean'),
            style=('style', 'first')
        ).reset_index().sort_values('total_daily_loss', ascending=False).head(15)

        # 7. Top stores
        top_stores = stockouts.groupby('store_code').agg(
            stockout_count=('sku', 'nunique'),
            total_daily_loss=('daily_sales_loss', 'sum'),
            avg_duration=('stockout_days', 'mean'),
            total_severity=('severity', 'sum')
        ).reset_index().sort_values('total_severity', ascending=False).head(15)
        top_stores['avg_duration'] = top_stores['avg_duration'].round(1)

        # 8. Category impact
        category_impact = []
        if style_df is not None and 'category' in style_df.columns and 'style' in stockouts.columns:
            if 'style_code' in style_df.columns:
                style_cat = style_df[['style_code', 'category']].drop_duplicates()
                so_cat = stockouts.merge(style_cat, left_on='style', right_on='style_code', how='left')
            else:
                so_cat = stockouts.copy()
                so_cat['category'] = 'Unknown'
            cat_agg = so_cat.groupby('category').agg(
                stockout_count=('sku', 'nunique'),
                total_daily_loss=('daily_sales_loss', 'sum')
            ).reset_index().sort_values('total_daily_loss', ascending=False)
            category_impact = cat_agg.fillna(0).to_dict('records')

        # 9. Daily trend
        inv_with_ros = inventory_df.merge(
            ros_df[['store_code', 'sku', 'ros']].drop_duplicates(),
            left_on=['store_code', 'ean'], right_on=['store_code', 'sku'], how='left'
        )
        inv_with_ros['ros'] = inv_with_ros['ros'].fillna(0)
        inv_with_ros['is_stockout'] = (inv_with_ros['quantity'] == 0) & (inv_with_ros['ros'] > 0)

        daily_trend = inv_with_ros.groupby('day')['is_stockout'].sum().reset_index()
        daily_trend.columns = ['date', 'stockout_count']
        daily_trend['date'] = daily_trend['date'].dt.strftime('%Y-%m-%d')
        daily_trend = daily_trend.sort_values('date')

        # 10. High-risk SKUs
        non_stockout = merged[(~merged['is_stockout']) & (merged['ros'] > 0) & (merged['soh'] > 0)].copy()
        non_stockout['days_to_stockout'] = (non_stockout['soh'] / non_stockout['ros']).round(1)
        non_stockout['risk'] = pd.cut(
            non_stockout['days_to_stockout'],
            bins=[-1, 3, 5, 7, float('inf')],
            labels=['critical', 'high', 'medium', 'low']
        )
        if 'style' in sku_df.columns:
            sku_style_map2 = sku_df.groupby('ean')['style'].first()
            non_stockout['style'] = non_stockout['sku'].map(sku_style_map2).fillna('Unknown')
        else:
            non_stockout['style'] = 'Unknown'
        high_risk = non_stockout[non_stockout['days_to_stockout'] <= 7].sort_values('days_to_stockout').head(15)
        high_risk_list = high_risk[['sku', 'store_code', 'ros', 'soh', 'asp', 'days_to_stockout', 'risk', 'style']].fillna(0).to_dict('records')
        for item in high_risk_list:
            item['risk'] = str(item['risk'])

        # 11. Stores impacted
        stores_impacted = int(stockouts['store_code'].nunique())

        # 12. Weekly & Monthly aggregation
        weekly_trend = []
        monthly_trend = []
        try:
            inv_with_ros_copy = inv_with_ros.copy()
            inv_with_ros_copy['week'] = inv_with_ros_copy['day'].dt.isocalendar().week.astype(int)
            inv_with_ros_copy['month'] = inv_with_ros_copy['day'].dt.month
            inv_with_ros_copy['is_stockout_bool'] = inv_with_ros_copy['is_stockout'].astype(bool)

            wk = inv_with_ros_copy.groupby('week').agg(
                stockout_count=('is_stockout_bool', 'sum'),
                total_skus=('ean', 'count'),
            ).reset_index()
            wk['stockout_rate'] = (wk['stockout_count'] / wk['total_skus'].clip(lower=1) * 100).round(1)
            weekly_trend = wk.sort_values('week').to_dict('records')

            mo = inv_with_ros_copy.groupby('month').agg(
                stockout_count=('is_stockout_bool', 'sum'),
                total_skus=('ean', 'count'),
            ).reset_index()
            mo['stockout_rate'] = (mo['stockout_count'] / mo['total_skus'].clip(lower=1) * 100).round(1)
            monthly_trend = mo.sort_values('month').to_dict('records')
        except Exception:
            pass

        # 13. Period trends
        period_trends = {}
        try:
            ref_date = latest_date
            day_col = inv_with_ros['day']
            for label, start in [
                ('wtd', ref_date - pd.Timedelta(days=ref_date.weekday())),
                ('mtd', ref_date.replace(day=1)),
                ('qtd', ref_date - pd.offsets.QuarterBegin(startingMonth=1)),
                ('ytd', ref_date.replace(month=1, day=1)),
            ]:
                mask = (day_col >= pd.Timestamp(start)) & (day_col <= ref_date)
                subset = inv_with_ros[mask]
                if len(subset) > 0:
                    grp = subset.groupby('day')['is_stockout'].sum().reset_index()
                    grp.columns = ['date', 'stockout_count']
                    grp['date'] = grp['date'].dt.strftime('%Y-%m-%d')
                    period_trends[label] = grp.sort_values('date').to_dict('records')
                else:
                    period_trends[label] = []
        except Exception:
            pass

        # 14. Previous period comparison
        prev_period_trend = []
        try:
            period_days = (sales_df['day'].max() - sales_df['day'].min()).days + 1
            prev_start = sales_df['day'].min() - pd.Timedelta(days=period_days)
            prev_end = sales_df['day'].min() - pd.Timedelta(days=1)
            prev_inv = inventory_df[(inventory_df['day'] >= prev_start) & (inventory_df['day'] <= prev_end)]
            if len(prev_inv) > 0:
                prev_merged = prev_inv.merge(
                    ros_df[['store_code', 'sku', 'ros']].drop_duplicates(),
                    left_on=['store_code', 'ean'], right_on=['store_code', 'sku'], how='left'
                )
                prev_merged['ros'] = prev_merged['ros'].fillna(0)
                prev_merged['is_stockout'] = (prev_merged['quantity'] == 0) & (prev_merged['ros'] > 0)
                pt = prev_merged.groupby('day')['is_stockout'].sum().reset_index()
                pt.columns = ['date', 'stockout_count']
                pt['date'] = pt['date'].dt.strftime('%Y-%m-%d')
                prev_period_trend = pt.sort_values('date').to_dict('records')
        except Exception:
            pass

        # 15. Moving average
        moving_avg = []
        try:
            dt = daily_trend.copy()
            if isinstance(dt, pd.DataFrame) and len(dt) > 0:
                dt_sorted = dt.sort_values('date')
                dt_sorted['ma7'] = dt_sorted['stockout_count'].rolling(7, min_periods=1).mean().round(1)
                moving_avg = dt_sorted[['date', 'ma7']].to_dict('records')
        except Exception:
            pass

        # 16. Projected trend
        projected_trend = []
        try:
            if len(daily_trend) >= 7:
                recent_avg = daily_trend.tail(7)['stockout_count'].mean()
                last_date_val = pd.to_datetime(daily_trend['date'].iloc[-1])
                for i in range(1, 8):
                    future = last_date_val + pd.Timedelta(days=i)
                    projected_trend.append({
                        'date': future.strftime('%Y-%m-%d'),
                        'projected_count': round(recent_avg * (1 - 0.05 * i), 1),
                    })
        except Exception:
            pass

        # 17. Store heatmap
        store_heatmap = []
        try:
            store_so = merged.groupby('store_code').agg(
                total=('sku', 'count'),
                stockouts=('is_stockout', 'sum'),
                total_loss=('asp', lambda x: 0),
            ).reset_index()
            so_loss = stockouts.groupby('store_code')['daily_sales_loss'].sum().reset_index()
            so_loss.columns = ['store_code', 'total_loss']
            store_so = store_so.drop(columns=['total_loss']).merge(so_loss, on='store_code', how='left')
            store_so['total_loss'] = store_so['total_loss'].fillna(0)
            store_so['stockout_pct'] = (store_so['stockouts'] / store_so['total'].clip(lower=1) * 100).round(1)
            store_so['severity'] = pd.cut(
                store_so['stockout_pct'],
                bins=[-1, 5, 15, 30, float('inf')],
                labels=['low', 'medium', 'high', 'critical']
            ).astype(str)
            store_heatmap = store_so.sort_values('stockout_pct', ascending=False).fillna(0).to_dict('records')
        except Exception:
            pass

        # 18. Category heatmap
        category_heatmap = []
        try:
            if style_df is not None and 'category' in style_df.columns and 'style' in sku_df.columns:
                sku_cat = sku_df.merge(
                    style_df[['style_code', 'category']].rename(columns={'style_code': 'style'}),
                    on='style', how='left'
                )
                merged_cat = merged.merge(sku_cat[['ean', 'category']], left_on='sku', right_on='ean', how='left', suffixes=('', '_cat'))
                cat_so = merged_cat.groupby('category').agg(
                    total=('sku', 'count'),
                    stockouts=('is_stockout', 'sum'),
                ).reset_index()
                cat_loss = merged_cat[merged_cat['is_stockout']].groupby('category').apply(
                    lambda g: ((g['ros'] - g['soh']) * g['asp']).clip(lower=0).sum()
                ).reset_index()
                cat_loss.columns = ['category', 'total_loss']
                cat_so = cat_so.merge(cat_loss, on='category', how='left')
                cat_so['total_loss'] = cat_so['total_loss'].fillna(0).round(2)
                cat_so['stockout_pct'] = (cat_so['stockouts'] / cat_so['total'].clip(lower=1) * 100).round(1)
                cat_so['severity'] = pd.cut(
                    cat_so['stockout_pct'],
                    bins=[-1, 5, 15, 30, float('inf')],
                    labels=['low', 'medium', 'high', 'critical']
                ).astype(str)
                category_heatmap = cat_so.sort_values('stockout_pct', ascending=False).fillna(0).to_dict('records')
        except Exception:
            pass

        # 19. Reorder recommendations
        reorder_recs = []
        try:
            cfg_doc = await _get_db().analysis_config.find_one({"_id": "main"}, {"_id": 0})
            safety_days = (cfg_doc or {}).get("safety_days", 7)
            lead_time = 14
            candidates = merged[(merged['ros'] > 0)].copy()
            candidates['days_to_stockout'] = np.where(
                candidates['ros'] > 0,
                (candidates['soh'] / candidates['ros']).round(1),
                999
            )
            candidates['reorder_qty'] = np.where(
                candidates['days_to_stockout'] < (lead_time + safety_days),
                ((candidates['ros'] * (lead_time + safety_days)) - candidates['soh']).clip(lower=0).round(0),
                0
            )
            needs_reorder = candidates[candidates['reorder_qty'] > 0].sort_values('days_to_stockout')
            if 'style' in sku_df.columns:
                sku_style_map3 = sku_df.groupby('ean')['style'].first()
                needs_reorder['style'] = needs_reorder['sku'].map(sku_style_map3).fillna('Unknown')
            else:
                needs_reorder['style'] = 'Unknown'
            reorder_recs = needs_reorder[['sku', 'store_code', 'style', 'ros', 'soh', 'asp',
                'days_to_stockout', 'reorder_qty']].head(20).fillna(0).to_dict('records')
        except Exception:
            pass

        # 20. Alternative suggestions
        alt_suggestions = []
        try:
            if 'style' in sku_df.columns and 'size' in sku_df.columns:
                so_skus = stockouts[['sku', 'store_code', 'style']].head(10)
                for _, row in so_skus.iterrows():
                    style = row.get('style', '')
                    if style and style != 'Unknown':
                        same_style_skus = sku_df[sku_df['style'] == style]['ean'].tolist()
                        store_inv = merged[(merged['store_code'] == row['store_code']) &
                                          (merged['sku'].isin(same_style_skus)) &
                                          (merged['soh'] > 0)]
                        alts = store_inv[['sku', 'soh', 'ros']].head(3).to_dict('records')
                        if alts:
                            alt_suggestions.append({
                                'stockout_sku': row['sku'],
                                'store_code': row['store_code'],
                                'alternatives': alts,
                            })
        except Exception:
            pass

        return {
            "summary": {
                "total_stockouts": total_stockouts,
                "stockout_rate": stockout_rate,
                "total_lost_sales": round(total_lost_sales, 2),
                "stores_impacted": stores_impacted,
                "total_store_skus": total_store_skus,
                "snapshot_date": str(latest_date.date()) if pd.notna(latest_date) else None,
            },
            "top_skus": top_skus.round(2).fillna(0).to_dict('records'),
            "top_stores": top_stores.round(2).fillna(0).to_dict('records'),
            "category_impact": category_impact,
            "daily_trend": daily_trend.to_dict('records'),
            "weekly_trend": weekly_trend,
            "monthly_trend": monthly_trend,
            "period_trends": period_trends,
            "prev_period_trend": prev_period_trend,
            "moving_avg": moving_avg,
            "projected_trend": projected_trend,
            "high_risk_skus": high_risk_list,
            "store_heatmap": store_heatmap,
            "category_heatmap": category_heatmap,
            "reorder_recommendations": reorder_recs,
            "alternative_suggestions": alt_suggestions,
        }
    except Exception as e:
        logger.error(f"Stock-out analysis error: {str(e)}")
        return {"error": str(e), "data": {}}
