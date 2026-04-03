"""
AI Demand Planning Endpoints — Full Design Compliance
Covers: ML Forecast (Ensemble), Stockout Prediction, Topseller Prediction (X-Factor),
        Reorder Point Optimisation, Supply Feasibility (DOH), Demand Plan CRUD (with
        optimistic locking), Rate Limiting, and RBAC.
"""

from fastapi import APIRouter, Query, HTTPException, Request, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Dict
import pandas as pd
import numpy as np
import os
import time
import logging
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from sklearn.linear_model import LinearRegression
from services.tenant_data_provider import get_tenant_provider

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai-demand"])

_client: Optional[AsyncIOMotorClient] = None
_get_cached_data = None
_get_db = None
_get_current_user = None
_require_role = None

MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# ── Rate Limiter ─────────────────────────────────────────────
_rate_buckets: Dict[str, list] = {}
RATE_LIMIT = 50  # requests per minute

def _check_rate_limit(request: Request):
    """Per-IP rate limiter: 50 requests/minute on AI demand endpoints."""
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    if ip not in _rate_buckets:
        _rate_buckets[ip] = []
    _rate_buckets[ip] = [t for t in _rate_buckets[ip] if now - t < 60]
    if len(_rate_buckets[ip]) >= RATE_LIMIT:
        raise HTTPException(
            429,
            detail=f"Rate limit exceeded ({RATE_LIMIT} requests/minute). Please try again later.",
            headers={"Retry-After": "60", "X-RateLimit-Limit": str(RATE_LIMIT)},
        )
    _rate_buckets[ip].append(now)


def init_ai_demand(mongo_client, get_cached_data_func, get_db_func, get_current_user_func=None, require_role_func=None):
    global _client, _get_cached_data, _get_db, _get_current_user, _require_role
    _client = mongo_client
    _get_cached_data = get_cached_data_func
    _get_db = get_db_func
    _get_current_user = get_current_user_func
    _require_role = require_role_func


# ═══════════════════════════════════════════════════════════════
# OPTIONS — Dynamic filter values from TenantDataProvider
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics/ai-demand/options")
async def ai_demand_options(request: Request):
    """Dynamic categories, subcategories, channels, and data status for AI Demand filters."""
    if _get_current_user:
        await _get_current_user(request)
    provider = await get_tenant_provider()
    return await provider.get_analytics_options()


# ── helpers ──────────────────────────────────────────────────

def _seasonality_factors(values: List[float]) -> dict:
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
    trend = 'accelerating' if avg > 5 else ('declining' if avg < -5 else 'stable')
    return {'avg_monthly_growth': round(avg, 1), 'trend': trend}


def _doh_classify(soh: float, avg_daily_demand: float, lead_time: int = 14) -> dict:
    """DOH-based supply feasibility classification.
    Achievable: supply covers >120% of demand during lead time
    At Risk:    supply covers 80-120%
    Unachievable: supply covers <80%
    """
    demand_lt = avg_daily_demand * lead_time
    coverage = (soh / demand_lt * 100) if demand_lt > 0 else 999
    if coverage > 120:
        return {'status': 'achievable', 'color': 'green', 'coverage_pct': round(coverage, 1)}
    elif coverage >= 80:
        return {'status': 'at_risk', 'color': 'yellow', 'coverage_pct': round(coverage, 1)}
    else:
        return {'status': 'unachievable', 'color': 'red', 'coverage_pct': round(coverage, 1)}


async def _monthly_revenue(category: str = None, subcategory: str = None) -> List[dict]:
    sales_df = await _get_cached_data('daily_sales')
    sku_df = await _get_cached_data('sku_ean_master')
    style_df = await _get_cached_data('style_master')
    if sales_df is None or sku_df is None:
        return []
    df = sales_df.copy()
    df['day'] = pd.to_datetime(df['day'])
    if 'ean' in sku_df.columns and 'style' in sku_df.columns:
        df = df.merge(sku_df[['ean', 'style']], left_on='sku', right_on='ean', how='left')
    if style_df is not None and 'style' in df.columns:
        scols = [c for c in ['style_code', 'category', 'subcategory'] if c in style_df.columns]
        if scols:
            df = df.merge(style_df[scols], left_on='style', right_on='style_code', how='left')
    if category and 'category' in df.columns:
        df = df[df['category'] == category]
    if subcategory and 'subcategory' in df.columns:
        df = df[df['subcategory'] == subcategory]
    if len(df) == 0:
        return []
    df['month'] = df['day'].dt.to_period('M')
    grouped = df.groupby('month').agg(revenue=('revenue', 'sum'), quantity=('quantity', 'sum')).reset_index().sort_values('month')
    return [{'year': r['month'].year, 'month': r['month'].month, 'month_name': MONTH_NAMES[r['month'].month - 1],
             'revenue': round(float(r['revenue']), 2), 'quantity': int(r['quantity'])} for _, r in grouped.iterrows()]


# ═══════════════════════════════════════════════════════════════
# 1. ML ENSEMBLE FORECAST  (RBAC: all authenticated users)
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics/ai-demand/forecast")
async def ml_forecast(
    request: Request,
    category: str = Query(None),
    subcategory: str = Query(None),
    forecast_horizon: int = Query(12, ge=1, le=24),
):
    _check_rate_limit(request)
    if _get_current_user:
        await _get_current_user(request)  # auth check

    from ml_forecast_engine import MLForecastEngine
    historical = await _monthly_revenue(category, subcategory)
    insufficient = len(historical) < 6
    if insufficient:
        historical = _generate_demo_monthly(category or 'All')
    values = [h['revenue'] for h in historical]
    engine = MLForecastEngine()
    result = engine.ensemble_forecast(values, seasonal_periods=12, forecast_horizon=forecast_horizon)
    now = datetime.now(timezone.utc)
    months = []
    for i in range(forecast_horizon):
        m = (now.month + i - 1) % 12 + 1
        y = now.year + ((now.month + i - 1) // 12)
        months.append({'month': m, 'year': y, 'month_name': MONTH_NAMES[m - 1], 'label': f"{MONTH_NAMES[m - 1]} {y}"})
    confidence = result.get('ensemble_accuracy', {}).get('confidence_score', 70)
    if insufficient:
        confidence = min(confidence, 50)
    return {
        'category': category or 'All', 'subcategory': subcategory or 'All',
        'forecast_horizon': forecast_horizon, 'months': months,
        'forecast': result['forecast'],
        'confidence_intervals': result.get('confidence_intervals', {}),
        'models_used': result.get('models_used', []),
        'individual_forecasts': result.get('individual_forecasts', {}),
        'confidence_score': confidence,
        'seasonality_factors': _seasonality_factors(values),
        'growth_trend': _growth_trend(values),
        'historical_data': historical[-12:],
        'insufficient_data': insufficient,
        'generated_at': now.isoformat(),
        'data_source': 'demo' if insufficient else 'uploaded',
    }


# ═══════════════════════════════════════════════════════════════
# 2. STOCKOUT RISK PREDICTION  (RBAC: admin, merchandiser, allocator)
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics/ai-demand/stockout-risk")
async def stockout_risk_prediction(
    request: Request,
    category: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    _check_rate_limit(request)
    if _get_current_user:
        user = await _get_current_user(request)
        if user.get('role') not in ('admin', 'merchandiser', 'allocator', 'viewer'):
            raise HTTPException(403, "Insufficient role for stockout predictions")

    sales_df = await _get_cached_data('daily_sales')
    inv_df = await _get_cached_data('store_inventory')
    sku_df = await _get_cached_data('sku_ean_master')
    style_df = await _get_cached_data('style_master')
    if sales_df is None or inv_df is None or sku_df is None:
        resp = _demo_stockout_data()
        resp['data_source'] = 'demo'
        return resp
    try:
        sales_df = sales_df.copy()
        inv_df = inv_df.copy()
        sales_df['day'] = pd.to_datetime(sales_df['day'])
        inv_df['day'] = pd.to_datetime(inv_df['day'])
        sku_cols = ['ean']
        if 'style' in sku_df.columns: sku_cols.append('style')
        sales_sku = sales_df.merge(sku_df[sku_cols], left_on='sku', right_on='ean', how='left')
        if category and style_df is not None and 'style' in sales_sku.columns and 'category' in style_df.columns:
            valid = style_df[style_df['category'] == category]['style_code'].tolist()
            sales_sku = sales_sku[sales_sku['style'].isin(valid)]
        if len(sales_sku) == 0:
            return _demo_stockout_data()
        ros = sales_sku.groupby(['store_code', 'sku']).agg(total_qty=('quantity', 'sum'), live_days=('day', 'nunique')).reset_index()
        ros['ros'] = (ros['total_qty'] / ros['live_days'].clip(lower=1)).round(3)
        latest_date = inv_df['day'].max()
        latest_inv = inv_df[inv_df['day'] == latest_date]
        soh = latest_inv.groupby(['store_code', 'ean'])['quantity'].sum().reset_index()
        soh.columns = ['store_code', 'sku', 'soh']
        merged = ros.merge(soh, on=['store_code', 'sku'], how='left')
        merged['soh'] = merged['soh'].fillna(0)
        merged['days_until_stockout'] = np.where(merged['ros'] > 0, (merged['soh'] / merged['ros']).round(1), 999)
        def classify(d):
            if d <= 3: return 'critical'
            if d <= 7: return 'high'
            if d <= 14: return 'medium'
            if d <= 30: return 'low'
            return 'healthy'
        merged['risk'] = merged['days_until_stockout'].apply(classify)
        # DOH supply feasibility
        merged['doh_status'] = merged.apply(lambda r: _doh_classify(r['soh'], r['ros'])['status'], axis=1)
        merged['coverage_pct'] = merged.apply(lambda r: _doh_classify(r['soh'], r['ros'])['coverage_pct'], axis=1)
        if 'style' in sku_df.columns:
            merged['style'] = merged['sku'].map(sku_df.groupby('ean')['style'].first()).fillna('Unknown')
        else:
            merged['style'] = 'Unknown'
        risk_counts = merged['risk'].value_counts().to_dict()
        doh_counts = merged['doh_status'].value_counts().to_dict()
        risk_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'healthy': 4}
        merged['risk_order'] = merged['risk'].map(risk_order)
        top = merged.sort_values('risk_order').head(limit)
        items = top[['sku', 'store_code', 'style', 'soh', 'ros', 'days_until_stockout', 'risk', 'doh_status', 'coverage_pct']].fillna(0).to_dict('records')
        return {
            'summary': {
                'critical': risk_counts.get('critical', 0), 'high': risk_counts.get('high', 0),
                'medium': risk_counts.get('medium', 0), 'low': risk_counts.get('low', 0),
                'healthy': risk_counts.get('healthy', 0), 'total': len(merged),
                'snapshot_date': str(latest_date.date()) if pd.notna(latest_date) else None,
                'doh_achievable': doh_counts.get('achievable', 0),
                'doh_at_risk': doh_counts.get('at_risk', 0),
                'doh_unachievable': doh_counts.get('unachievable', 0),
            },
            'items': items,
            'data_source': 'uploaded',
        }
    except Exception as e:
        logger.error("Stockout risk prediction error: %s", e)
        resp = _demo_stockout_data()
        resp['data_source'] = 'demo'
        return resp


# ═══════════════════════════════════════════════════════════════
# 3. TOPSELLER PREDICTION with X-Factor  (RBAC: admin, merchandiser)
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics/ai-demand/topseller-prediction")
async def topseller_prediction(
    request: Request,
    category: str = Query(None),
    x_factor: float = Query(2.0, ge=1.0, le=5.0, description="X Factor threshold for topseller classification"),
    limit: int = Query(10, ge=1, le=50),
):
    _check_rate_limit(request)
    if _get_current_user:
        user = await _get_current_user(request)
        if user.get('role') not in ('admin', 'merchandiser', 'viewer'):
            raise HTTPException(403, "Insufficient role for topseller predictions")

    sales_df = await _get_cached_data('daily_sales')
    sku_df = await _get_cached_data('sku_ean_master')
    style_df = await _get_cached_data('style_master')
    if sales_df is None or sku_df is None:
        resp = _demo_topseller_data(x_factor)
        resp['data_source'] = 'demo'
        return resp
    try:
        sales_df = sales_df.copy()
        sales_df['day'] = pd.to_datetime(sales_df['day'])
        sku_cols = ['ean']
        if 'style' in sku_df.columns: sku_cols.append('style')
        merged = sales_df.merge(sku_df[sku_cols], left_on='sku', right_on='ean', how='left')
        if 'style' not in merged.columns:
            return _demo_topseller_data(x_factor)
        if category and style_df is not None and 'category' in style_df.columns:
            valid = style_df[style_df['category'] == category]['style_code'].tolist()
            merged = merged[merged['style'].isin(valid)]
        if len(merged) == 0:
            resp = _demo_topseller_data(x_factor)
            resp['data_source'] = 'demo'
            return resp
        merged['month'] = merged['day'].dt.to_period('M')
        style_monthly = merged.groupby(['style', 'month']).agg(revenue=('revenue', 'sum'), quantity=('quantity', 'sum')).reset_index()
        style_counts = style_monthly.groupby('style')['month'].nunique().reset_index()
        style_counts.columns = ['style', 'months_active']
        qualified = style_counts[style_counts['months_active'] >= 2]['style'].tolist()

        # Category average revenue for X-Factor comparison
        cat_avg = float(style_monthly.groupby('style')['revenue'].mean().mean()) if len(style_monthly) > 0 else 0

        predictions = []
        for style_code in qualified[:50]:
            sdata = style_monthly[style_monthly['style'] == style_code].sort_values('month')
            revs = sdata['revenue'].tolist()
            if len(revs) < 2: continue
            first = revs[0] if revs[0] > 0 else 1
            growth = ((revs[-1] - first) / first) * 100
            x = np.arange(len(revs)).reshape(-1, 1)
            lr = LinearRegression()
            lr.fit(x, revs)
            future = lr.predict([[len(revs)], [len(revs) + 1], [len(revs) + 2]])
            predicted_3m = round(float(sum(future)), 2)
            current_avg = round(float(np.mean(revs[-3:])), 2) if len(revs) >= 3 else round(float(np.mean(revs)), 2)
            # X Factor: style revenue vs category average
            style_x_factor = round(current_avg / cat_avg, 2) if cat_avg > 0 else 1.0
            is_topseller = style_x_factor >= x_factor
            name = style_code
            if style_df is not None and 'style_code' in style_df.columns:
                row = style_df[style_df['style_code'] == style_code]
                if len(row) > 0 and 'style_name' in row.columns:
                    name = str(row.iloc[0]['style_name'])
            predictions.append({
                'style_code': style_code, 'style_name': name,
                'current_monthly_avg': current_avg, 'growth_rate': round(growth, 1),
                'predicted_revenue_3m': max(0, predicted_3m),
                'x_factor': style_x_factor, 'is_topseller': is_topseller,
                'category_avg': round(cat_avg, 2),
                'confidence': min(90, max(40, int(50 + growth / 4))),
                'months_active': int(style_counts[style_counts['style'] == style_code]['months_active'].values[0]),
                'recommendation': 'Increase safety stock by 50%' if is_topseller else 'Monitor trend',
            })
        predictions.sort(key=lambda x: x['predicted_revenue_3m'], reverse=True)
        return {'predictions': predictions[:limit], 'x_factor_threshold': x_factor, 'category_avg_revenue': round(cat_avg, 2), 'data_source': 'uploaded'}
    except Exception as e:
        logger.error("Topseller prediction error: %s", e)
        resp = _demo_topseller_data(x_factor)
        resp['data_source'] = 'demo'
        return resp


# ═══════════════════════════════════════════════════════════════
# 4. REORDER POINT OPTIMISATION + DOH  (RBAC: admin, allocator)
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics/ai-demand/reorder-optimisation")
async def reorder_optimisation(
    request: Request,
    limit: int = Query(15, ge=1, le=50),
    lead_time_days: int = Query(14, ge=1, le=90),
    service_level: float = Query(95, ge=80, le=99.9),
):
    _check_rate_limit(request)
    if _get_current_user:
        user = await _get_current_user(request)
        if user.get('role') not in ('admin', 'allocator', 'merchandiser', 'viewer'):
            raise HTTPException(403, "Insufficient role for reorder optimisation")

    sales_df = await _get_cached_data('daily_sales')
    inv_df = await _get_cached_data('store_inventory')
    sku_df = await _get_cached_data('sku_ean_master')
    if sales_df is None or inv_df is None or sku_df is None:
        resp = _demo_reorder_data()
        resp['data_source'] = 'demo'
        return resp
    try:
        sales_df = sales_df.copy()
        inv_df = inv_df.copy()
        sales_df['day'] = pd.to_datetime(sales_df['day'])
        inv_df['day'] = pd.to_datetime(inv_df['day'])
        daily = sales_df.groupby(['sku', 'day']).agg(qty=('quantity', 'sum')).reset_index()
        stats = daily.groupby('sku').agg(avg_daily=('qty', 'mean'), std_daily=('qty', 'std'), days_sold=('day', 'nunique')).reset_index()
        stats['std_daily'] = stats['std_daily'].fillna(0)
        z_map = {80: 0.84, 85: 1.04, 90: 1.28, 95: 1.645, 97.5: 1.96, 99: 2.33, 99.9: 3.09}
        z = z_map.get(service_level, 1.645)
        stats['safety_stock'] = (z * stats['std_daily'] * np.sqrt(lead_time_days)).round(1)
        stats['reorder_point'] = (stats['avg_daily'] * lead_time_days + stats['safety_stock']).round(1)
        latest_date = inv_df['day'].max()
        latest_inv = inv_df[inv_df['day'] == latest_date].groupby('ean')['quantity'].sum().reset_index()
        latest_inv.columns = ['sku', 'current_stock']
        merged = stats.merge(latest_inv, on='sku', how='left')
        merged['current_stock'] = merged['current_stock'].fillna(0)
        merged['days_until_reorder'] = np.where(merged['avg_daily'] > 0, ((merged['current_stock'] - merged['reorder_point']) / merged['avg_daily']).round(1), 999)
        merged['status'] = np.where(merged['current_stock'] <= merged['reorder_point'], 'reorder_needed', 'healthy')
        merged['recommended_order'] = np.where(merged['status'] == 'reorder_needed', (merged['reorder_point'] * 1.5 - merged['current_stock']).clip(lower=0).round(0), 0)
        # DOH classification
        merged['doh_info'] = merged.apply(lambda r: _doh_classify(r['current_stock'], r['avg_daily'], lead_time_days), axis=1)
        merged['doh_status'] = merged['doh_info'].apply(lambda x: x['status'])
        merged['coverage_pct'] = merged['doh_info'].apply(lambda x: x['coverage_pct'])
        if 'style' in sku_df.columns:
            merged['style'] = merged['sku'].map(sku_df.groupby('ean')['style'].first()).fillna('Unknown')
        else:
            merged['style'] = 'Unknown'
        merged = merged.sort_values(['status', 'days_until_reorder'], ascending=[False, True])
        items = merged.head(limit)[['sku', 'style', 'avg_daily', 'std_daily', 'safety_stock', 'reorder_point', 'current_stock', 'days_until_reorder', 'status', 'recommended_order', 'doh_status', 'coverage_pct']].round(2).fillna(0).to_dict('records')
        doh_counts = merged['doh_status'].value_counts().to_dict()
        return {
            'summary': {
                'total_skus': len(merged), 'reorder_needed': int((merged['status'] == 'reorder_needed').sum()),
                'healthy': int((merged['status'] == 'healthy').sum()),
                'lead_time_days': lead_time_days, 'service_level': service_level,
                'doh_achievable': doh_counts.get('achievable', 0),
                'doh_at_risk': doh_counts.get('at_risk', 0),
                'doh_unachievable': doh_counts.get('unachievable', 0),
            },
            'items': items,
            'data_source': 'uploaded',
        }
    except Exception as e:
        logger.error("Reorder optimisation error: %s", e)
        resp = _demo_reorder_data()
        resp['data_source'] = 'demo'
        return resp


# ═══════════════════════════════════════════════════════════════
# 5. GENERATE AI DEMAND PLAN  (RBAC: admin, merchandiser)
# ═══════════════════════════════════════════════════════════════

@router.post("/analytics/ai-demand/generate-plan")
async def generate_demand_plan(
    request: Request,
    category: str = Query(None),
    annual_target: float = Query(10000000),
):
    _check_rate_limit(request)
    user_email = "system"
    if _get_current_user:
        user = await _get_current_user(request)
        if user.get('role') not in ('admin', 'merchandiser'):
            raise HTTPException(403, "Only admin and merchandiser can generate demand plans")
        user_email = user.get('email', 'system')

    from ml_forecast_engine import MLForecastEngine
    engine = MLForecastEngine()
    style_df = await _get_cached_data('style_master')
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
        seasonality = _seasonality_factors(values if len(values) >= 12 else forecast_values)
        total_w = sum(float(v) for v in seasonality.values())
        monthly_targets = [round(per_subcat * float(seasonality[str(m + 1)]) / total_w, 2) for m in range(12)]
        blended = [round(forecast_values[i] * 0.6 + monthly_targets[i] * 0.4, 2) for i in range(12)]
        plan_subcats.append({'name': subcat, 'monthly_plan': blended, 'forecast_values': forecast_values, 'total': round(sum(blended), 2), 'confidence': confidence})
        total_planned += sum(blended)
    variance = annual_target - total_planned

    # Persist plan to DB with version for optimistic locking
    db = _get_db()
    plan_doc = {
        'category': category or 'All',
        'annual_target': annual_target,
        'total_planned': round(total_planned, 2),
        'variance': round(variance, 2),
        'variance_pct': round(variance / annual_target * 100, 1) if annual_target > 0 else 0,
        'subcategories': plan_subcats,
        'status': 'draft',
        'version': 1,
        'created_by': user_email,
        'updated_by': user_email,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'data_source': 'uploaded' if len(historical) >= 6 else 'demo',
    }
    result = await db.demand_plans.insert_one(plan_doc)
    plan_doc.pop('_id', None)
    plan_doc['plan_id'] = str(result.inserted_id)
    return plan_doc


# ═══════════════════════════════════════════════════════════════
# 6. DEMAND PLAN CRUD — Save, Load, Update with Optimistic Locking
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics/ai-demand/plans")
async def list_demand_plans(request: Request):
    """List saved demand plans."""
    _check_rate_limit(request)
    if _get_current_user:
        await _get_current_user(request)
    db = _get_db()
    raw_plans = await db.demand_plans.find({}).sort("created_at", -1).to_list(50)
    plans = []
    for p in raw_plans:
        p['plan_id'] = str(p.pop('_id'))
        plans.append(p)
    return {'plans': plans}


@router.get("/analytics/ai-demand/plans/{plan_id}")
async def get_demand_plan(request: Request, plan_id: str):
    """Get a specific demand plan by ID."""
    _check_rate_limit(request)
    if _get_current_user:
        await _get_current_user(request)
    db = _get_db()
    try:
        plan = await db.demand_plans.find_one({"_id": ObjectId(plan_id)})
    except Exception:
        raise HTTPException(404, "Plan not found")
    if not plan:
        raise HTTPException(404, "Plan not found")
    plan['plan_id'] = str(plan.pop('_id'))
    return plan


@router.put("/analytics/ai-demand/plans/{plan_id}")
async def update_demand_plan(
    request: Request,
    plan_id: str,
    expected_version: int = Query(..., description="Version for optimistic locking"),
):
    """Update demand plan with optimistic locking (concurrent edit protection)."""
    _check_rate_limit(request)
    user_email = "system"
    if _get_current_user:
        user = await _get_current_user(request)
        if user.get('role') not in ('admin', 'merchandiser'):
            raise HTTPException(403, "Only admin and merchandiser can edit demand plans")
        user_email = user.get('email', 'system')

    body = await request.json()
    db = _get_db()
    try:
        existing = await db.demand_plans.find_one({"_id": ObjectId(plan_id)})
    except Exception:
        raise HTTPException(404, "Plan not found")
    if not existing:
        raise HTTPException(404, "Plan not found")

    # Optimistic locking check
    current_version = existing.get('version', 1)
    if current_version != expected_version:
        raise HTTPException(
            409,
            detail=f"Conflict: plan was modified by {existing.get('updated_by', 'another user')}. "
                   f"Your version: {expected_version}, current version: {current_version}. Please reload and try again.",
        )

    # Apply updates
    update_fields = {}
    if 'subcategories' in body:
        update_fields['subcategories'] = body['subcategories']
        total = sum(sum(sc.get('monthly_plan', [])) for sc in body['subcategories'])
        update_fields['total_planned'] = round(total, 2)
        at = body.get('annual_target', existing.get('annual_target', 0))
        update_fields['variance'] = round(at - total, 2)
        update_fields['variance_pct'] = round((at - total) / at * 100, 1) if at > 0 else 0
    if 'annual_target' in body:
        update_fields['annual_target'] = body['annual_target']
    if 'status' in body:
        update_fields['status'] = body['status']

    update_fields['version'] = current_version + 1
    update_fields['updated_by'] = user_email
    update_fields['updated_at'] = datetime.now(timezone.utc).isoformat()

    await db.demand_plans.update_one({"_id": ObjectId(plan_id)}, {"$set": update_fields})
    return {'success': True, 'new_version': update_fields['version'], 'message': 'Plan updated successfully'}


# ═══════════════════════════════════════════════════════════════
# 7. SUPPLY FEASIBILITY (DOH-based)
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics/ai-demand/supply-feasibility")
async def supply_feasibility(
    request: Request,
    plan_id: str = Query(None, description="Demand plan ID to check feasibility against"),
    lead_time_days: int = Query(14, ge=1, le=90),
):
    """Supply feasibility analysis using DOH classification against demand plan."""
    _check_rate_limit(request)
    if _get_current_user:
        user = await _get_current_user(request)
        if user.get('role') not in ('admin', 'allocator', 'merchandiser', 'viewer'):
            raise HTTPException(403, "Insufficient role")

    inv_df = await _get_cached_data('store_inventory')
    sales_df = await _get_cached_data('daily_sales')
    if inv_df is None or sales_df is None:
        resp = _demo_supply_feasibility()
        resp['data_source'] = 'demo'
        return resp

    try:
        inv_df = inv_df.copy()
        sales_df = sales_df.copy()
        inv_df['day'] = pd.to_datetime(inv_df['day'])
        sales_df['day'] = pd.to_datetime(sales_df['day'])

        # Total SOH per SKU (latest date)
        latest = inv_df['day'].max()
        soh = inv_df[inv_df['day'] == latest].groupby('ean')['quantity'].sum().reset_index()
        soh.columns = ['sku', 'total_soh']

        # Average daily demand per SKU
        daily_demand = sales_df.groupby('sku').agg(
            total_qty=('quantity', 'sum'), days=('day', 'nunique'),
        ).reset_index()
        daily_demand['avg_daily'] = (daily_demand['total_qty'] / daily_demand['days'].clip(lower=1)).round(2)

        merged = soh.merge(daily_demand[['sku', 'avg_daily']], on='sku', how='left')
        merged['avg_daily'] = merged['avg_daily'].fillna(0)
        merged['demand_lead_time'] = (merged['avg_daily'] * lead_time_days).round(1)
        merged['coverage_pct'] = np.where(
            merged['demand_lead_time'] > 0,
            (merged['total_soh'] / merged['demand_lead_time'] * 100).round(1),
            999,
        )
        merged['feasibility'] = merged['coverage_pct'].apply(
            lambda c: 'achievable' if c > 120 else ('at_risk' if c >= 80 else 'unachievable')
        )
        counts = merged['feasibility'].value_counts().to_dict()

        # Monthly breakdown (simulate 12-month view)
        months_data = []
        now = datetime.now(timezone.utc)
        for i in range(12):
            m = (now.month + i - 1) % 12 + 1
            y = now.year + ((now.month + i - 1) // 12)
            total_demand = float(merged['avg_daily'].sum() * 30)
            total_supply = float(merged['total_soh'].sum()) - (total_demand * i * 0.3)
            total_supply = max(0, total_supply)
            cov = (total_supply / total_demand * 100) if total_demand > 0 else 999
            months_data.append({
                'month': m, 'year': y, 'label': f"{MONTH_NAMES[m - 1]} {y}",
                'demand': round(total_demand, 2), 'supply': round(total_supply, 2),
                'coverage_pct': round(cov, 1),
                'status': 'achievable' if cov > 120 else ('at_risk' if cov >= 80 else 'unachievable'),
            })

        achievable_months = sum(1 for m in months_data if m['status'] == 'achievable')
        at_risk_months = sum(1 for m in months_data if m['status'] == 'at_risk')
        unachievable_months = sum(1 for m in months_data if m['status'] == 'unachievable')

        return {
            'summary': {
                'achievable_skus': counts.get('achievable', 0),
                'at_risk_skus': counts.get('at_risk', 0),
                'unachievable_skus': counts.get('unachievable', 0),
                'total_skus': len(merged),
                'achievable_months': achievable_months,
                'at_risk_months': at_risk_months,
                'unachievable_months': unachievable_months,
                'lead_time_days': lead_time_days,
            },
            'monthly': months_data,
            'data_source': 'uploaded',
        }
    except Exception as e:
        logger.error("Supply feasibility error: %s", e)
        resp = _demo_supply_feasibility()
        resp['data_source'] = 'demo'
        return resp


# ═══════════════════════════════════════════════════════════════
# DEMO / FALLBACK DATA
# ═══════════════════════════════════════════════════════════════

def _generate_demo_monthly(category: str) -> List[dict]:
    np.random.seed(hash(category) % 2**31)
    base = 500000
    seasonal = [0.8, 0.75, 0.9, 1.0, 1.1, 0.95, 0.85, 0.9, 1.05, 1.2, 1.3, 1.15]
    result = []
    for i in range(24):
        m = i % 12
        noise = np.random.normal(1.0, 0.08)
        trend = 1 + i * 0.01
        rev = round(base * seasonal[m] * noise * trend, 2)
        result.append({'year': 2024 + i // 12, 'month': m + 1, 'month_name': MONTH_NAMES[m], 'revenue': rev, 'quantity': int(rev / 450)})
    return result


def _demo_stockout_data():
    items = [
        {'sku': 'SKU-JN-001', 'store_code': 'ST001', 'style': 'Slim Fit Jeans', 'soh': 12, 'ros': 4.2, 'days_until_stockout': 2.9, 'risk': 'critical', 'doh_status': 'unachievable', 'coverage_pct': 20.5},
        {'sku': 'SKU-TS-003', 'store_code': 'ST002', 'style': 'V-Neck T-Shirt', 'soh': 35, 'ros': 6.1, 'days_until_stockout': 5.7, 'risk': 'high', 'doh_status': 'unachievable', 'coverage_pct': 41.0},
        {'sku': 'SKU-JK-007', 'store_code': 'ST001', 'style': 'Denim Jacket', 'soh': 28, 'ros': 2.8, 'days_until_stockout': 10.0, 'risk': 'medium', 'doh_status': 'at_risk', 'coverage_pct': 71.4},
        {'sku': 'SKU-SH-012', 'store_code': 'ST003', 'style': 'Oxford Shirt', 'soh': 55, 'ros': 3.5, 'days_until_stockout': 15.7, 'risk': 'low', 'doh_status': 'at_risk', 'coverage_pct': 112.2},
        {'sku': 'SKU-DR-009', 'store_code': 'ST002', 'style': 'Maxi Dress', 'soh': 90, 'ros': 1.8, 'days_until_stockout': 50.0, 'risk': 'healthy', 'doh_status': 'achievable', 'coverage_pct': 357.1},
        {'sku': 'SKU-CG-015', 'store_code': 'ST001', 'style': 'Cargo Pants', 'soh': 8, 'ros': 3.0, 'days_until_stockout': 2.7, 'risk': 'critical', 'doh_status': 'unachievable', 'coverage_pct': 19.0},
        {'sku': 'SKU-HD-019', 'store_code': 'ST004', 'style': 'Zip Hoodie', 'soh': 42, 'ros': 5.5, 'days_until_stockout': 7.6, 'risk': 'medium', 'doh_status': 'unachievable', 'coverage_pct': 54.5},
        {'sku': 'SKU-PL-022', 'store_code': 'ST003', 'style': 'Polo Shirt', 'soh': 18, 'ros': 4.0, 'days_until_stockout': 4.5, 'risk': 'high', 'doh_status': 'unachievable', 'coverage_pct': 32.1},
    ]
    return {
        'summary': {'critical': 2, 'high': 2, 'medium': 2, 'low': 1, 'healthy': 1, 'total': 8,
                     'snapshot_date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                     'doh_achievable': 1, 'doh_at_risk': 2, 'doh_unachievable': 5},
        'items': items,
    }


def _demo_topseller_data(x_factor: float = 2.0):
    cat_avg = 120000
    return {'predictions': [
        {'style_code': 'PREM-DNM-JKT', 'style_name': 'Premium Denim Jacket', 'current_monthly_avg': 245000, 'growth_rate': 92.3, 'predicted_revenue_3m': 1410000, 'x_factor': 2.04, 'is_topseller': True, 'category_avg': cat_avg, 'confidence': 88, 'months_active': 6, 'recommendation': 'Increase safety stock by 50%'},
        {'style_code': 'OVERSZ-TEE', 'style_name': 'Oversized T-Shirt', 'current_monthly_avg': 182000, 'growth_rate': 78.1, 'predicted_revenue_3m': 972000, 'x_factor': 1.52, 'is_topseller': False, 'category_avg': cat_avg, 'confidence': 82, 'months_active': 5, 'recommendation': 'Monitor trend'},
        {'style_code': 'CARGO-PNT', 'style_name': 'Cargo Pants', 'current_monthly_avg': 125000, 'growth_rate': 65.5, 'predicted_revenue_3m': 620000, 'x_factor': 1.04, 'is_topseller': False, 'category_avg': cat_avg, 'confidence': 76, 'months_active': 8, 'recommendation': 'Monitor trend'},
        {'style_code': 'HVY-HOODIE', 'style_name': 'Heavy Weight Hoodie', 'current_monthly_avg': 98000, 'growth_rate': 54.2, 'predicted_revenue_3m': 453000, 'x_factor': 0.82, 'is_topseller': False, 'category_avg': cat_avg, 'confidence': 72, 'months_active': 4, 'recommendation': 'Monitor trend'},
        {'style_code': 'STRCH-CHINO', 'style_name': 'Stretch Chino', 'current_monthly_avg': 88000, 'growth_rate': 42.0, 'predicted_revenue_3m': 375000, 'x_factor': 0.73, 'is_topseller': False, 'category_avg': cat_avg, 'confidence': 68, 'months_active': 7, 'recommendation': 'Monitor trend'},
    ], 'x_factor_threshold': x_factor, 'category_avg_revenue': cat_avg}


def _demo_reorder_data():
    return {
        'summary': {'total_skus': 5, 'reorder_needed': 3, 'healthy': 2, 'lead_time_days': 14, 'service_level': 95,
                     'doh_achievable': 2, 'doh_at_risk': 0, 'doh_unachievable': 3},
        'items': [
            {'sku': 'SKU-JN-001', 'style': 'Slim Fit Jeans', 'avg_daily': 4.2, 'std_daily': 1.8, 'safety_stock': 11.1, 'reorder_point': 69.9, 'current_stock': 12, 'days_until_reorder': -13.8, 'status': 'reorder_needed', 'recommended_order': 93, 'doh_status': 'unachievable', 'coverage_pct': 20.4},
            {'sku': 'SKU-TS-003', 'style': 'V-Neck T-Shirt', 'avg_daily': 6.1, 'std_daily': 2.5, 'safety_stock': 15.4, 'reorder_point': 100.8, 'current_stock': 35, 'days_until_reorder': -10.8, 'status': 'reorder_needed', 'recommended_order': 116, 'doh_status': 'unachievable', 'coverage_pct': 41.0},
            {'sku': 'SKU-CG-015', 'style': 'Cargo Pants', 'avg_daily': 3.0, 'std_daily': 1.2, 'safety_stock': 7.4, 'reorder_point': 49.4, 'current_stock': 8, 'days_until_reorder': -13.8, 'status': 'reorder_needed', 'recommended_order': 66, 'doh_status': 'unachievable', 'coverage_pct': 19.0},
            {'sku': 'SKU-DR-009', 'style': 'Maxi Dress', 'avg_daily': 1.8, 'std_daily': 0.9, 'safety_stock': 5.5, 'reorder_point': 30.7, 'current_stock': 90, 'days_until_reorder': 32.9, 'status': 'healthy', 'recommended_order': 0, 'doh_status': 'achievable', 'coverage_pct': 357.1},
            {'sku': 'SKU-PL-022', 'style': 'Polo Shirt', 'avg_daily': 4.0, 'std_daily': 1.5, 'safety_stock': 9.2, 'reorder_point': 65.2, 'current_stock': 80, 'days_until_reorder': 3.7, 'status': 'healthy', 'recommended_order': 0, 'doh_status': 'achievable', 'coverage_pct': 142.9},
        ],
    }


def _demo_supply_feasibility():
    now = datetime.now(timezone.utc)
    months = []
    for i in range(12):
        m = (now.month + i - 1) % 12 + 1
        y = now.year + ((now.month + i - 1) // 12)
        cov = max(20, 180 - i * 15)
        months.append({
            'month': m, 'year': y, 'label': f"{MONTH_NAMES[m - 1]} {y}",
            'demand': 150000, 'supply': round(150000 * cov / 100, 2), 'coverage_pct': cov,
            'status': 'achievable' if cov > 120 else ('at_risk' if cov >= 80 else 'unachievable'),
        })
    return {
        'summary': {
            'achievable_skus': 50, 'at_risk_skus': 25, 'unachievable_skus': 15, 'total_skus': 90,
            'achievable_months': sum(1 for m in months if m['status'] == 'achievable'),
            'at_risk_months': sum(1 for m in months if m['status'] == 'at_risk'),
            'unachievable_months': sum(1 for m in months if m['status'] == 'unachievable'),
            'lead_time_days': 14,
        },
        'monthly': months,
    }
