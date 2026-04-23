"""Promotion calendar + lift-factor endpoints."""

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ._shared import router, _dep_user, get_db


class PromotionCreateReq(BaseModel):
    name: str
    promo_type: str = "national"  # national, regional, store
    start_date: str
    end_date: str
    discount_type: str = "percentage"  # percentage, fixed, bogo
    discount_value: float = 0
    affected_categories: list = []
    affected_skus: list = []
    affected_regions: list = []
    lift_factor: float = 1.0
    notes: Optional[str] = None


@router.post("/promotions")
async def create_promotion(body: PromotionCreateReq, user: dict = Depends(_dep_user)):
    """Create a new promotion."""
    from domains.buy_planning import (
        PromotionsRepository, PromotionsService, PromotionsValidationError,
    )
    svc = PromotionsService(PromotionsRepository(get_db()))
    try:
        return await svc.create(
            tenant_id=user.get("tenant_id", ""),
            payload=body.model_dump(),
            user_email=user.get("email", ""),
        )
    except PromotionsValidationError as e:
        raise HTTPException(400, str(e))


@router.get("/promotions")
async def list_promotions(status: Optional[str] = None, user: dict = Depends(_dep_user)):
    """List promotions."""
    from domains.buy_planning import PromotionsRepository, PromotionsService
    svc = PromotionsService(PromotionsRepository(get_db()))
    return await svc.list_all(user.get("tenant_id", ""), status)


@router.put("/promotions/{promo_id}")
async def update_promotion(promo_id: str, body: PromotionCreateReq, user: dict = Depends(_dep_user)):
    """Update a promotion."""
    from domains.buy_planning import (
        PromotionsRepository, PromotionsService,
        PromotionsNotFoundError, PromotionsValidationError,
    )
    svc = PromotionsService(PromotionsRepository(get_db()))
    try:
        return await svc.update(
            tenant_id=user.get("tenant_id", ""), promo_id=promo_id,
            payload=body.model_dump(), user_email=user.get("email", ""),
        )
    except PromotionsValidationError as e:
        raise HTTPException(400, str(e))
    except PromotionsNotFoundError as e:
        raise HTTPException(404, str(e))


@router.delete("/promotions/{promo_id}")
async def delete_promotion(promo_id: str, user: dict = Depends(_dep_user)):
    """Delete a promotion."""
    from domains.buy_planning import (
        PromotionsRepository, PromotionsService, PromotionsNotFoundError,
    )
    svc = PromotionsService(PromotionsRepository(get_db()))
    try:
        return await svc.delete(
            tenant_id=user.get("tenant_id", ""), promo_id=promo_id,
        )
    except PromotionsNotFoundError as e:
        raise HTTPException(404, str(e))


@router.get("/promotions/active-lift")
async def get_active_lift_factors(user: dict = Depends(_dep_user)):
    """Get all active promotion lift factors (for buy formula integration)."""
    from domains.buy_planning import PromotionsRepository, PromotionsService
    svc = PromotionsService(PromotionsRepository(get_db()))
    return await svc.get_active_lifts(user.get("tenant_id", ""))
