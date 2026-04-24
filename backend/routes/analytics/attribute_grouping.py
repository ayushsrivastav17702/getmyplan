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


class SaveRecReq(BaseModel):
    level_key: str
    best_value: str
    vs_value: str
    ratio: float
    message: str
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


@router.post("/attribute-grouping/save-recommendation")
async def save_attribute_recommendation(
    body: SaveRecReq, user: dict = Depends(_dep_user),
):
    """Persist a buy-more recommendation so merchants can action it on the Buy Planning page.

    Stores the rec in the `buy_plan_recommendations` collection (scoped by
    tenant_id) with source='attribute-grouping-compare' so the Buy Planning
    UI can later surface it as a pending action.
    """
    from datetime import datetime, timezone
    from uuid import uuid4
    db = get_db()
    rec_id = str(uuid4())
    doc = {
        "rec_id": rec_id,
        "tenant_id": user.get("tenant_id", ""),
        "source": "attribute-grouping-compare",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("email", ""),
        **body.model_dump(),
    }
    await db.buy_plan_recommendations.insert_one(doc)
    return {"success": True, "rec_id": rec_id, "status": "pending"}


@router.get("/attribute-grouping/recommendations")
async def list_attribute_recommendations(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(_dep_user),
):
    """List saved buy-more recommendations (excludes Mongo _id)."""
    db = get_db()
    q: Dict[str, object] = {"tenant_id": user.get("tenant_id", "")}
    if status:
        q["status"] = status
    recs = []
    async for doc in db.buy_plan_recommendations.find(
        q, {"_id": 0},
    ).sort("created_at", -1).limit(limit):
        recs.append(doc)
    return {"recommendations": recs, "total": len(recs)}
