"""Size Curve Optimization route adapters."""

from typing import Optional

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field

from routes.analytics import _dep_user, get_db, router


class RecommendReq(BaseModel):
    category: str
    days: int = Field(90, ge=1, le=365)
    deviation_threshold_pp: float = Field(10.0, ge=0, le=100)
    min_units: int = Field(50, ge=0)


class AllocateReq(BaseModel):
    category: str
    total_qty: int = Field(..., gt=0)
    store_code: Optional[str] = None
    days: int = Field(90, ge=1, le=365)


@router.get("/size-curve/categories")
async def list_size_curve_categories(user: dict = Depends(_dep_user)):
    """Categories with size data for this tenant."""
    from domains.analytics.size_curve import (
        SizeCurveRepository, SizeCurveService,
    )
    svc = SizeCurveService(SizeCurveRepository(get_db()))
    return await svc.list_categories(tenant_id=user.get("tenant_id", ""))


@router.get("/size-curve/corporate/{category}")
async def get_corporate_curve(
    category: str,
    days: int = Query(90, ge=1, le=365),
    user: dict = Depends(_dep_user),
):
    """Tenant-wide size-mix for the given category."""
    from domains.analytics.size_curve import (
        SizeCurveRepository, SizeCurveService, ValidationError,
    )
    svc = SizeCurveService(SizeCurveRepository(get_db()))
    try:
        return await svc.corporate_curve(
            tenant_id=user.get("tenant_id", ""),
            category=category, days=days,
        )
    except ValidationError as e:
        raise HTTPException(400, str(e))


@router.post("/size-curve/recommend")
async def recommend_size_curves(body: RecommendReq, user: dict = Depends(_dep_user)):
    """Per-store size curves + deviation-flagged outliers."""
    from domains.analytics.size_curve import (
        SizeCurveRepository, SizeCurveService, ValidationError,
    )
    svc = SizeCurveService(SizeCurveRepository(get_db()))
    try:
        return await svc.recommend(
            tenant_id=user.get("tenant_id", ""), **body.model_dump(),
        )
    except ValidationError as e:
        raise HTTPException(400, str(e))


@router.post("/size-curve/allocate")
async def allocate_by_size_curve(body: AllocateReq, user: dict = Depends(_dep_user)):
    """Split a buy-plan total across sizes using the corporate or store curve."""
    from domains.analytics.size_curve import (
        SizeCurveRepository, SizeCurveService, ValidationError,
    )
    svc = SizeCurveService(SizeCurveRepository(get_db()))
    try:
        return await svc.allocate(
            tenant_id=user.get("tenant_id", ""), **body.model_dump(),
        )
    except ValidationError as e:
        raise HTTPException(400, str(e))
