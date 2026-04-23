"""Binding-factor analytics endpoints (display-min misconfiguration detector)."""

from fastapi import Depends, HTTPException

from ._shared import router, _dep_user, get_db


@router.post("/analytics/backfill-binding-breakdown")
async def backfill_binding_breakdown(user: dict = Depends(_dep_user)):
    """
    One-shot: backfill `binding_breakdown` onto historical buy_plans that
    pre-date the field. Idempotent — existing breakdowns are recomputed.
    """
    from domains.buy_planning import (
        BindingAnalyticsRepository, BindingAnalyticsService,
        BindingAnalyticsForbiddenError,
    )
    svc = BindingAnalyticsService(BindingAnalyticsRepository(get_db()))
    try:
        return await svc.backfill(
            tenant_id=user.get("tenant_id", ""),
            role=user.get("role", "viewer"),
        )
    except BindingAnalyticsForbiddenError as e:
        raise HTTPException(403, str(e))


@router.get("/analytics/binding-factor")
async def binding_factor_analytics(limit: int = 10, user: dict = Depends(_dep_user)):
    """
    Analytics for the "where did the buy qty come from?" question.
    Returns:
      - `latest`: the most recent plan's breakdown (for doughnut chart)
      - `trend`: last N plans ordered oldest→newest (for time-series line)
      - `worst_categories`: categories with highest floor_override_pct across last N plans
      - `plan_count`, `total_skus_analyzed`
    """
    from domains.buy_planning import BindingAnalyticsRepository, BindingAnalyticsService
    svc = BindingAnalyticsService(BindingAnalyticsRepository(get_db()))
    return await svc.get_analytics(tenant_id=user.get("tenant_id", ""), limit=limit)
