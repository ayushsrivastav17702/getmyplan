"""Attribute grouping route adapters — thin wrappers around the domain service."""

from typing import Dict, List, Optional

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field

from routes.analytics import _dep_user, get_db, router


# ─── Request models ─────────────────────────────────────────────────────────

class CompareReq(BaseModel):
    level_key: str
    attribute_values: List[str] = Field(..., min_length=2)
    days: int = 90


class ForecastReq(BaseModel):
    attribute_combination: Dict[str, str] = Field(..., min_length=1)
    days: int = 90


# ─── Handlers ───────────────────────────────────────────────────────────────

@router.get("/attribute-grouping/levels")
async def get_attribute_levels(user: dict = Depends(_dep_user)):
    """List attribute levels available for this tenant + sample values."""
    from domains.analytics.attribute_grouping import (
        AttributeGroupingRepository, AttributeGroupingService,
    )
    svc = AttributeGroupingService(AttributeGroupingRepository(get_db()))
    return await svc.get_levels(tenant_id=user.get("tenant_id", ""))


@router.get("/attribute-grouping/sales/{level_key}")
async def get_attribute_sales(
    level_key: str,
    attribute_value: Optional[str] = Query(None),
    days: int = Query(90, ge=1, le=365),
    user: dict = Depends(_dep_user),
):
    """Roll up sales by the chosen attribute level."""
    from domains.analytics.attribute_grouping import (
        AttributeGroupingRepository, AttributeGroupingService, ValidationError,
    )
    svc = AttributeGroupingService(AttributeGroupingRepository(get_db()))
    try:
        return await svc.get_sales_by_level(
            tenant_id=user.get("tenant_id", ""), level_key=level_key,
            days=days, attribute_value=attribute_value,
        )
    except ValidationError as e:
        raise HTTPException(400, str(e))


@router.get("/attribute-grouping/trends/{level_key}")
async def get_attribute_trends(
    level_key: str,
    days: int = Query(90, ge=2, le=365),
    limit: int = Query(10, ge=1, le=50),
    user: dict = Depends(_dep_user),
):
    """Growth / decline ranking of attribute values, recent vs old window."""
    from domains.analytics.attribute_grouping import (
        AttributeGroupingRepository, AttributeGroupingService, ValidationError,
    )
    svc = AttributeGroupingService(AttributeGroupingRepository(get_db()))
    try:
        return await svc.get_trends(
            tenant_id=user.get("tenant_id", ""),
            level_key=level_key, days=days, limit=limit,
        )
    except ValidationError as e:
        raise HTTPException(400, str(e))


@router.post("/attribute-grouping/compare")
async def compare_attributes(body: CompareReq, user: dict = Depends(_dep_user)):
    """Side-by-side metrics + buy-more recommendation."""
    from domains.analytics.attribute_grouping import (
        AttributeGroupingRepository, AttributeGroupingService, ValidationError,
    )
    svc = AttributeGroupingService(AttributeGroupingRepository(get_db()))
    try:
        return await svc.compare(
            tenant_id=user.get("tenant_id", ""),
            level_key=body.level_key,
            attribute_values=body.attribute_values,
            days=body.days,
        )
    except ValidationError as e:
        raise HTTPException(400, str(e))


@router.post("/attribute-grouping/forecast")
async def forecast_new_combo(body: ForecastReq, user: dict = Depends(_dep_user)):
    """Forecast daily/monthly/quarterly units for a hypothetical new attribute combo."""
    from domains.analytics.attribute_grouping import (
        AttributeGroupingRepository, AttributeGroupingService, ValidationError,
    )
    svc = AttributeGroupingService(AttributeGroupingRepository(get_db()))
    try:
        return await svc.forecast(
            tenant_id=user.get("tenant_id", ""),
            attribute_combination=body.attribute_combination,
            days=body.days,
        )
    except ValidationError as e:
        raise HTTPException(400, str(e))
