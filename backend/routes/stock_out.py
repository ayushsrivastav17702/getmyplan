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

from services.cache_service import cache_get, cache_set, cache_extra, get_tenant_id as _cache_tid

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
    """Stock-Out Analysis using MongoDB aggregation (memory-safe)."""
    _tid = _cache_tid()
    _ex = cache_extra(sd=start_date, ed=end_date, cat=categories, ch=channels, rg=regions)
    _hit, _data = cache_get("stockout_list", _tid, _ex)
    if _hit:
        return _data

    from core.mongo_aggregations import agg_stock_out
    tdb = _get_db()
    cat_list = [c.strip() for c in categories.split(',')] if categories else None
    ch_list = [c.strip() for c in channels.split(',')] if channels else None
    rg_list = [r.strip() for r in regions.split(',')] if regions else None

    try:
        _result = await agg_stock_out(tdb, _tid, start_date, end_date, cat_list, ch_list, rg_list)
        cache_set("stockout_list", _tid, _result, _ex)
        return _result
    except Exception as e:
        logger.error(f"Stock-out analysis error: {str(e)}")
        return {"error": str(e), "data": {}}


