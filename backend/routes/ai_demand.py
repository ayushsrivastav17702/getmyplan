"""
AI Demand Planning Endpoints
Covers: ML Forecast (Ensemble), Stockout Prediction, Topseller Prediction,
        Reorder Point Optimisation, Demand Plan Generation.
"""

from fastapi import APIRouter, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai-demand"])

_client: Optional[AsyncIOMotorClient] = None
_get_cached_data = None
_get_db = None

MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def init_ai_demand(mongo_client, get_cached_data_func, get_db_func):
    global _client, _get_cached_data, _get_db
    _client = mongo_client
    _get_cached_data = get_cached_data_func
    _get_db = get_db_func


# ── helpers ──────────────────────────────────────────────────

def _seasonality_factors(values: List[float]) -> dict:
    """MFP seasonality: ratio of each month vs. average."""
    if len(values) < 12:
        return {str(i): 1.0 for i in range(1, 13)}
    last12 = values[-12:]
    avg = sum(last12) / 12 if last12 else 1
    return {str(i + 1): round(last12[i] / avg, 2) if avg > 0 else 1.0 for i in range(12)}


def _growth_trend(values: List[float]) -> dict:
    if len(values) < 2:
        return {'avg_monthly_growth': 0, 'trend': 'stable'}
    rates = []
    for i in range(1, len(values)):
        if values[i - 1] > 0:
            rates.append((values[i] - values[i - 1]) / values[i - 1] * 100)
    avg = float(np.mean(rates)) if rates else 0
    if avg > 5:
        trend = 'accelerating'
    elif avg < -5:
        trend = 'declining'
    else:
        trend = 'stable'
    return {'avg_monthly_growth': round(avg, 1), 'trend': trend}


async def _monthly_revenue(category: str = None, subcategory: str = None) -> List[dict]:
    """Aggregate monthly revenue from uploaded daily_sales data."""
    sales_df = await _get_cached_data('daily_sales')
    sku_df = await _get_cached_data('sku_ean_master')
    style_df = await _get_cached_data('style_master')

    if sales_df is None or sku_df is None:
        return []

    df = sales_df.copy()
    df['day'] = pd.to_datetime(df['day'])

    # join style info
    if 'sku' in df.columns and 'ean' in sku_df.columns:
        merge_cols = ['ean']
        if 'style' in sku_df.columns:
            merge_cols.append('style')
        df = df.merge(sku_df[merge_cols], left_on='sku', right_on='ean', how='left')

    if style_df is not None and 'style' in df.columns:
        style_cols = ['style_code']
        if 'category' in style_df.columns:
            style_cols.append('category')
        if 'subcategory' in style_df.columns:
            style_cols.append('subcategory')
        df = df.merge(style_df[style_cols], left_on='style', right_on='style_code', how='left')

    if category and 'category' in df.columns:
        df = df[df['category'] == category]
    if subcategory and 'subcategory' in df.columns:
        df = df[df['subcategory'] == subcategory]

    if len(df) == 0:
        return []

    df['month'] = df['day'].dt.to_period('M')
    grouped = df.groupby('month').agg(
        revenue=('revenue', 'sum'),
        quantity=('quantity', 'sum'),
    ).reset_index()
    grouped = grouped.sort_values('month')

    result = []
    for _, row in grouped.iterrows():
        result.append({
            'year': row['month'].year,
            'month': row['month'].month,
            'month_name': MONTH_NAMES[row['month'].month - 1],
            'revenue': round(float(row['revenue']), 2),
            'quantity': int(row['quantity']),
        })
    return result


# ── 1. ML Ensemble Forecast ─────────────────────────────────

@router.get("/analytics/ai-demand/forecast")
async def ml_forecast(
    category: str = Query(None),
    subcategory: str = Query(None),
    forecast_horizon: int = Query(12, ge=1, le=24),
):
    """Generate ML ensemble forecast for a category/subcategory."""
    from ml_forecast_engine import MLForecastEngine

    historical = await _monthly_revenue(category, subcategory)

    if len(historical) < 6:
        # Generate demo data if insufficient real data
        historical = _generate_demo_monthly(category or 'All')

    values = [h['revenue'] for h in historical]

    engine = MLForecastEngine()
    result = engine.ensemble_forecast(values, seasonal_periods=12, forecast_horizon=forecast_horizon)

    now = datetime.now(timezone.utc)
    months = []
    for i in range(forecast_horizon):
        m = (now.month + i - 1) % 12 + 1
        y = now.year + ((now.month + i - 1) // 12)
        months.append({
            'month': m,
            'year': y,
            'month_name': MONTH_NAMES[m - 1],
            'label': f"{MONTH_NAMES[m - 1]} {y}",
        })

    seasonality = _seasonality_factors(values)
    growth = _growth_trend(values)

    return {
        'category': category or 'All',
        'subcategory': subcategory or 'All',
        'forecast_horizon': forecast_horizon,
        'months': months,
        'forecast': result['forecast'],
        'confidence_intervals': result.get('confidence_intervals', {}),
        'models_used': result.get('models_used', []),
        'individual_forecasts': result.get('individual_forecasts', {}),
        'confidence_score': result.get('ensemble_accuracy', {}).get('confidence_score', 70),
        'seasonality_factors': seasonality,
        'growth_trend': growth,
        'historical_data': historical[-12:],
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }


# ── 2. Stockout Risk Prediction ─────────────────────────────

@router.get("/analytics/ai-demand/stockout-risk")
async def stockout_risk_prediction(
    category: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """Predict stockout risk across store-SKU combinations using ROS."""
    sales_df = await _get_cached_data('daily_sales')
    inv_df = await _get_cached_data('store_inventory')
    sku_df = await _get_cached_data('sku_ean_master')
    style_df = await _get_cached_data('style_master')

    if sales_df is None or inv_df is None or sku_df is None:
        return _demo_stockout_data()

    try:
        sales_df['day'] = pd.to_datetime(sales_df['day'])
        inv_df['day'] = pd.to_datetime(inv_df['day'])

        # join style info for category filter
        sku_cols = ['ean']
        if 'style' in sku_df.columns:
            sku_cols.append('style')
        if 'mrp' in sku_df.columns:
            sku_cols.append('mrp')
        sales_sku = sales_df.merge(sku_df[sku_cols], left_on='sku', right_on='ean', how='left')

        if category and style_df is not None and 'style' in sales_sku.columns:
            if 'category' in style_df.columns and 'style_code' in style_df.columns:
                valid = style_df[style_df['category'] == category]['style_code'].tolist()
                sales_sku = sales_sku[sales_sku['style'].isin(valid)]

        if len(sales_sku) == 0:
            return _demo_stockout_data()

        # ROS per store-SKU
        ros = sales_sku.groupby(['store_code', 'sku']).agg(
            total_qty=('quantity', 'sum'),
            live_days=('day', 'nunique'),
        ).reset_index()
        ros['ros'] = (ros['total_qty'] / ros['live_days'].clip(lower=1)).round(3)

        # Latest SOH
        latest_date = inv_df['day'].max()
        latest_inv = inv_df[inv_df['day'] == latest_date]
        soh = latest_inv.groupby(['store_code', 'ean'])['quantity'].sum().reset_index()
        soh.columns = ['store_code', 'sku', 'soh']

        merged = ros.merge(soh, on=['store_code', 'sku'], how='left')
        merged['soh'] = merged['soh'].fillna(0)
        merged['days_until_stockout'] = np.where(
            merged['ros'] > 0,
            (merged['soh'] / merged['ros']).round(1),
            999,
        )

        def classify(d):
            if d <= 3:
                return 'critical'
            if d <= 7:
                return 'high'
            if d <= 14:
                return 'medium'
            if d <= 30:
                return 'low'
            return 'healthy'

        merged['risk'] = merged['days_until_stockout'].apply(classify)

        # Add style name
        if 'style' in sku_df.columns:
            style_map = sku_df.groupby('ean')['style'].first()
            merged['style'] = merged['sku'].map(style_map).fillna('Unknown')
        else:
            merged['style'] = 'Unknown'

        # Summary counts
        risk_counts = merged['risk'].value_counts().to_dict()

        # Sort by urgency
        risk_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'healthy': 4}
        merged['risk_order'] = merged['risk'].map(risk_order)
        top = merged.sort_values('risk_order').head(limit)

        items = top[['sku', 'store_code', 'style', 'soh', 'ros', 'days_until_stockout', 'risk']].fillna(0).to_dict('records')

        return {
            'summary': {
                'critical': risk_counts.get('critical', 0),
                'high': risk_counts.get('high', 0),
                'medium': risk_counts.get('medium', 0),
                'low': risk_counts.get('low', 0),
                'healthy': risk_counts.get('healthy', 0),
                'total': len(merged),
                'snapshot_date': str(latest_date.date()) if pd.notna(latest_date) else None,
            },
            'items': items,
        }
    except Exception as e:
        logger.error("Stockout risk prediction error: %s", e)
        return _demo_stockout_data()


# ── 3. Topseller Prediction ─────────────────────────────────

@router.get("/analytics/ai-demand/topseller-prediction")
async def topseller_prediction(
    category: str = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    """Predict top-performing styles based on growth trends."""
    sales_df = await _get_cached_data('daily_sales')
    sku_df = await _get_cached_data('sku_ean_master')
    style_df = await _get_cached_data('style_master')

    if sales_df is None or sku_df is None:
        return _demo_topseller_data()

    try:
        sales_df['day'] = pd.to_datetime(sales_df['day'])
        sku_cols = ['ean']
        if 'style' in sku_df.columns:
            sku_cols.append('style')
        merged = sales_df.merge(sku_df[sku_cols], left_on='sku', right_on='ean', how='left')

        if 'style' not in merged.columns:
            return _demo_topseller_data()

        if category and style_df is not None and 'category' in style_df.columns:
            valid = style_df[style_df['category'] == category]['style_code'].tolist()
            merged = merged[merged['style'].isin(valid)]

        if len(merged) == 0:
            return _demo_topseller_data()

        # monthly revenue per style
        merged['month'] = merged['day'].dt.to_period('M')
        style_monthly = merged.groupby(['style', 'month']).agg(
            revenue=('revenue', 'sum'), quantity=('quantity', 'sum'),
        ).reset_index()

        # get styles with enough data
        style_counts = style_monthly.groupby('style')['month'].nunique().reset_index()
        style_counts.columns = ['style', 'months_active']
        qualified = style_counts[style_counts['months_active'] >= 2]['style'].tolist()

        predictions = []
        for style_code in qualified[:50]:
            sdata = style_monthly[style_monthly['style'] == style_code].sort_values('month')
            revs = sdata['revenue'].tolist()
            if len(revs) < 2:
                continue

            # growth rate (latest vs first)
            first = revs[0] if revs[0] > 0 else 1
            growth = ((revs[-1] - first) / first) * 100

            # simple linear forecast
            x = np.arange(len(revs)).reshape(-1, 1)
            lr = LinearRegression()
            lr.fit(x, revs)
            future = lr.predict([[len(revs)], [len(revs) + 1], [len(revs) + 2]])
            predicted_3m = round(float(sum(future)), 2)

            current_avg = round(float(np.mean(revs[-3:])), 2) if len(revs) >= 3 else round(float(np.mean(revs)), 2)

            # style name from style_df
            name = style_code
            if style_df is not None and 'style_code' in style_df.columns:
                row = style_df[style_df['style_code'] == style_code]
                if len(row) > 0 and 'style_name' in row.columns:
                    name = row.iloc[0]['style_name']
                elif len(row) > 0:
                    name = style_code

            predictions.append({
                'style_code': style_code,
                'style_name': name,
                'current_monthly_avg': current_avg,
                'growth_rate': round(growth, 1),
                'predicted_revenue_3m': max(0, predicted_3m),
                'confidence': min(90, max(40, int(50 + growth / 4))),
                'months_active': int(style_counts[style_counts['style'] == style_code]['months_active'].values[0]),
            })

        predictions.sort(key=lambda x: x['predicted_revenue_3m'], reverse=True)
        return {'predictions': predictions[:limit]}
    except Exception as e:
        logger.error("Topseller prediction error: %s", e)
        return _demo_topseller_data()


# ── 4. Reorder Point Optimisation ────────────────────────────

@router.get("/analytics/ai-demand/reorder-optimisation")
async def reorder_optimisation(
    limit: int = Query(15, ge=1, le=50),
    lead_time_days: int = Query(14, ge=1, le=90),
    service_level: float = Query(95, ge=80, le=99.9),
):
    """Calculate optimal reorder points across SKUs."""
    sales_df = await _get_cached_data('daily_sales')
    inv_df = await _get_cached_data('store_inventory')
    sku_df = await _get_cached_data('sku_ean_master')

    if sales_df is None or inv_df is None or sku_df is None:
        return _demo_reorder_data()

    try:
        sales_df['day'] = pd.to_datetime(sales_df['day'])
        inv_df['day'] = pd.to_datetime(inv_df['day'])

        # daily sales per SKU
        daily = sales_df.groupby(['sku', 'day']).agg(qty=('quantity', 'sum')).reset_index()
        stats = daily.groupby('sku').agg(
            avg_daily=('qty', 'mean'),
            std_daily=('qty', 'std'),
            days_sold=('day', 'nunique'),
        ).reset_index()
        stats['std_daily'] = stats['std_daily'].fillna(0)

        # z-score lookup
        z_map = {80: 0.84, 85: 1.04, 90: 1.28, 95: 1.645, 97.5: 1.96, 99: 2.33, 99.9: 3.09}
        z = z_map.get(service_level, 1.645)

        stats['safety_stock'] = (z * stats['std_daily'] * np.sqrt(lead_time_days)).round(1)
        stats['reorder_point'] = (stats['avg_daily'] * lead_time_days + stats['safety_stock']).round(1)

        # current stock
        latest_date = inv_df['day'].max()
        latest_inv = inv_df[inv_df['day'] == latest_date].groupby('ean')['quantity'].sum().reset_index()
        latest_inv.columns = ['sku', 'current_stock']

        merged = stats.merge(latest_inv, on='sku', how='left')
        merged['current_stock'] = merged['current_stock'].fillna(0)
        merged['days_until_reorder'] = np.where(
            merged['avg_daily'] > 0,
            ((merged['current_stock'] - merged['reorder_point']) / merged['avg_daily']).round(1),
            999,
        )
        merged['status'] = np.where(merged['current_stock'] <= merged['reorder_point'], 'reorder_needed', 'healthy')
        merged['recommended_order'] = np.where(
            merged['status'] == 'reorder_needed',
            (merged['reorder_point'] * 1.5 - merged['current_stock']).clip(lower=0).round(0),
            0,
        )

        # add style
        if 'style' in sku_df.columns:
            style_map = sku_df.groupby('ean')['style'].first()
            merged['style'] = merged['sku'].map(style_map).fillna('Unknown')
        else:
            merged['style'] = 'Unknown'

        # sort: reorder needed first, then by days_until_reorder asc
        merged = merged.sort_values(['status', 'days_until_reorder'], ascending=[False, True])

        items = merged.head(limit)[[
            'sku', 'style', 'avg_daily', 'std_daily', 'safety_stock',
            'reorder_point', 'current_stock', 'days_until_reorder', 'status', 'recommended_order',
        ]].round(2).fillna(0).to_dict('records')

        summary = {
            'total_skus': len(merged),
            'reorder_needed': int((merged['status'] == 'reorder_needed').sum()),
            'healthy': int((merged['status'] == 'healthy').sum()),
            'lead_time_days': lead_time_days,
            'service_level': service_level,
        }

        return {'summary': summary, 'items': items}
    except Exception as e:
        logger.error("Reorder optimisation error: %s", e)
        return _demo_reorder_data()


# ── 5. Generate AI Demand Plan ───────────────────────────────

@router.post("/analytics/ai-demand/generate-plan")
async def generate_demand_plan(
    category: str = Query(None),
    annual_target: float = Query(10000000),
):
    """Generate an AI-powered demand plan blending ML forecast with business target."""
    from ml_forecast_engine import MLForecastEngine

    sales_df = await _get_cached_data('daily_sales')
    sku_df = await _get_cached_data('sku_ean_master')
    style_df = await _get_cached_data('style_master')

    engine = MLForecastEngine()

    # determine subcategories
    subcategories = []
    if style_df is not None and 'subcategory' in style_df.columns:
        if category and 'category' in style_df.columns:
            subcategories = style_df[style_df['category'] == category]['subcategory'].dropna().unique().tolist()
        else:
            subcategories = style_df['subcategory'].dropna().unique().tolist()
    if not subcategories:
        subcategories = ['Default']

    plan_subcats = []
    total_planned = 0
    per_subcat = annual_target / len(subcategories)

    for subcat in subcategories:
        historical = await _monthly_revenue(category, subcat)
        values = [h['revenue'] for h in historical]

        if len(values) >= 6:
            fc = engine.ensemble_forecast(values, forecast_horizon=12)
            forecast_values = fc['forecast']
            confidence = fc.get('ensemble_accuracy', {}).get('confidence_score', 70)
        else:
            forecast_values = [round(per_subcat / 12, 2)] * 12
            confidence = 50

        # seasonality-weighted target distribution
        seasonality = _seasonality_factors(values if len(values) >= 12 else forecast_values)
        total_w = sum(float(v) for v in seasonality.values())
        monthly_targets = [round(per_subcat * float(seasonality[str(m + 1)]) / total_w, 2) for m in range(12)]

        # blend forecast (60%) with target (40%)
        blended = [round(forecast_values[i] * 0.6 + monthly_targets[i] * 0.4, 2) for i in range(12)]

        plan_subcats.append({
            'name': subcat,
            'monthly_plan': blended,
            'forecast_values': forecast_values,
            'total': round(sum(blended), 2),
            'confidence': confidence,
        })
        total_planned += sum(blended)

    variance = annual_target - total_planned
    return {
        'category': category or 'All',
        'annual_target': annual_target,
        'total_planned': round(total_planned, 2),
        'variance': round(variance, 2),
        'variance_pct': round(variance / annual_target * 100, 1) if annual_target > 0 else 0,
        'subcategories': plan_subcats,
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }


# ── Demo / fallback data generators ─────────────────────────

def _generate_demo_monthly(category: str) -> List[dict]:
    """Generate plausible demo monthly data for forecasting."""
    np.random.seed(hash(category) % 2**31)
    base = 500000
    seasonal = [0.8, 0.75, 0.9, 1.0, 1.1, 0.95, 0.85, 0.9, 1.05, 1.2, 1.3, 1.15]
    result = []
    for i in range(24):
        m = i % 12
        noise = np.random.normal(1.0, 0.08)
        trend = 1 + i * 0.01
        rev = round(base * seasonal[m] * noise * trend, 2)
        result.append({
            'year': 2024 + i // 12,
            'month': m + 1,
            'month_name': MONTH_NAMES[m],
            'revenue': rev,
            'quantity': int(rev / 450),
        })
    return result


def _demo_stockout_data():
    items = [
        {'sku': 'SKU-JN-001', 'store_code': 'ST001', 'style': 'Slim Fit Jeans', 'soh': 12, 'ros': 4.2, 'days_until_stockout': 2.9, 'risk': 'critical'},
        {'sku': 'SKU-TS-003', 'store_code': 'ST002', 'style': 'V-Neck T-Shirt', 'soh': 35, 'ros': 6.1, 'days_until_stockout': 5.7, 'risk': 'high'},
        {'sku': 'SKU-JK-007', 'store_code': 'ST001', 'style': 'Denim Jacket', 'soh': 28, 'ros': 2.8, 'days_until_stockout': 10.0, 'risk': 'medium'},
        {'sku': 'SKU-SH-012', 'store_code': 'ST003', 'style': 'Oxford Shirt', 'soh': 55, 'ros': 3.5, 'days_until_stockout': 15.7, 'risk': 'low'},
        {'sku': 'SKU-DR-009', 'store_code': 'ST002', 'style': 'Maxi Dress', 'soh': 90, 'ros': 1.8, 'days_until_stockout': 50.0, 'risk': 'healthy'},
        {'sku': 'SKU-CG-015', 'store_code': 'ST001', 'style': 'Cargo Pants', 'soh': 8, 'ros': 3.0, 'days_until_stockout': 2.7, 'risk': 'critical'},
        {'sku': 'SKU-HD-019', 'store_code': 'ST004', 'style': 'Zip Hoodie', 'soh': 42, 'ros': 5.5, 'days_until_stockout': 7.6, 'risk': 'medium'},
        {'sku': 'SKU-PL-022', 'store_code': 'ST003', 'style': 'Polo Shirt', 'soh': 18, 'ros': 4.0, 'days_until_stockout': 4.5, 'risk': 'high'},
    ]
    return {
        'summary': {'critical': 2, 'high': 2, 'medium': 2, 'low': 1, 'healthy': 1, 'total': 8, 'snapshot_date': datetime.now(timezone.utc).strftime('%Y-%m-%d')},
        'items': items,
    }


def _demo_topseller_data():
    return {'predictions': [
        {'style_code': 'PREM-DNM-JKT', 'style_name': 'Premium Denim Jacket', 'current_monthly_avg': 245000, 'growth_rate': 92.3, 'predicted_revenue_3m': 1410000, 'confidence': 88, 'months_active': 6},
        {'style_code': 'OVERSZ-TEE', 'style_name': 'Oversized T-Shirt', 'current_monthly_avg': 182000, 'growth_rate': 78.1, 'predicted_revenue_3m': 972000, 'confidence': 82, 'months_active': 5},
        {'style_code': 'CARGO-PNT', 'style_name': 'Cargo Pants', 'current_monthly_avg': 125000, 'growth_rate': 65.5, 'predicted_revenue_3m': 620000, 'confidence': 76, 'months_active': 8},
        {'style_code': 'HVY-HOODIE', 'style_name': 'Heavy Weight Hoodie', 'current_monthly_avg': 98000, 'growth_rate': 54.2, 'predicted_revenue_3m': 453000, 'confidence': 72, 'months_active': 4},
        {'style_code': 'STRCH-CHINO', 'style_name': 'Stretch Chino', 'current_monthly_avg': 88000, 'growth_rate': 42.0, 'predicted_revenue_3m': 375000, 'confidence': 68, 'months_active': 7},
    ]}


def _demo_reorder_data():
    return {
        'summary': {'total_skus': 5, 'reorder_needed': 3, 'healthy': 2, 'lead_time_days': 14, 'service_level': 95},
        'items': [
            {'sku': 'SKU-JN-001', 'style': 'Slim Fit Jeans', 'avg_daily': 4.2, 'std_daily': 1.8, 'safety_stock': 11.1, 'reorder_point': 69.9, 'current_stock': 12, 'days_until_reorder': -13.8, 'status': 'reorder_needed', 'recommended_order': 93},
            {'sku': 'SKU-TS-003', 'style': 'V-Neck T-Shirt', 'avg_daily': 6.1, 'std_daily': 2.5, 'safety_stock': 15.4, 'reorder_point': 100.8, 'current_stock': 35, 'days_until_reorder': -10.8, 'status': 'reorder_needed', 'recommended_order': 116},
            {'sku': 'SKU-CG-015', 'style': 'Cargo Pants', 'avg_daily': 3.0, 'std_daily': 1.2, 'safety_stock': 7.4, 'reorder_point': 49.4, 'current_stock': 8, 'days_until_reorder': -13.8, 'status': 'reorder_needed', 'recommended_order': 66},
            {'sku': 'SKU-DR-009', 'style': 'Maxi Dress', 'avg_daily': 1.8, 'std_daily': 0.9, 'safety_stock': 5.5, 'reorder_point': 30.7, 'current_stock': 90, 'days_until_reorder': 32.9, 'status': 'healthy', 'recommended_order': 0},
            {'sku': 'SKU-PL-022', 'style': 'Polo Shirt', 'avg_daily': 4.0, 'std_daily': 1.5, 'safety_stock': 9.2, 'reorder_point': 65.2, 'current_stock': 80, 'days_until_reorder': 3.7, 'status': 'healthy', 'recommended_order': 0},
        ],
    }
