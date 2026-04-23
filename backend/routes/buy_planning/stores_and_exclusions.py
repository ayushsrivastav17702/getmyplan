"""Store attributes + exclusions endpoints."""

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ._shared import router, _dep_user, get_db


# ─────────────── Store Attributes ───────────────

class StoreAttributeUpdateReq(BaseModel):
    store_format: Optional[str] = None  # hypermarket, supermarket, convenience
    city_tier: Optional[str] = None     # tier1, tier2, tier3
    region: Optional[str] = None        # North, South, East, West, Central
    area_sqft: Optional[int] = None


@router.put("/stores/{store_code}/attributes")
async def update_store_attributes(store_code: str, body: StoreAttributeUpdateReq, user: dict = Depends(_dep_user)):
    """Update store extended attributes (format, tier, region, area)."""
    from domains.buy_planning import (
        StoreAttributesRepository, StoreAttributesService,
        StoreAttrsNotFoundError, StoreAttrsValidationError,
    )
    svc = StoreAttributesService(StoreAttributesRepository(get_db()))
    try:
        return await svc.update(
            store_code=store_code,
            store_format=body.store_format, city_tier=body.city_tier,
            region=body.region, area_sqft=body.area_sqft,
            user_email=user.get("email", ""), tenant_id=user.get("tenant_id", ""),
        )
    except StoreAttrsNotFoundError as e:
        raise HTTPException(404, str(e))
    except StoreAttrsValidationError as e:
        raise HTTPException(400, str(e))


# ─────────────── Exclusions ───────────────

class ExclusionCreateReq(BaseModel):
    store_code: str
    sku: str
    reason: str = ""
    expires_at: Optional[str] = None


@router.post("/exclusions")
async def add_exclusion(body: ExclusionCreateReq, user: dict = Depends(_dep_user)):
    """Add a store-SKU exclusion (excluded from buy plans)."""
    from domains.buy_planning import ExclusionsRepository, ExclusionsService
    svc = ExclusionsService(ExclusionsRepository(get_db()))
    return await svc.add(
        tenant_id=user.get("tenant_id", ""),
        store_code=body.store_code, sku=body.sku,
        reason=body.reason, expires_at=body.expires_at,
        user_email=user.get("email", ""),
    )


@router.delete("/exclusions/{store_code}/{sku}")
async def remove_exclusion(store_code: str, sku: str, user: dict = Depends(_dep_user)):
    """Remove a store-SKU exclusion."""
    from domains.buy_planning import ExclusionsRepository, ExclusionsService, ExclusionsNotFoundError
    svc = ExclusionsService(ExclusionsRepository(get_db()))
    try:
        return await svc.remove(
            tenant_id=user.get("tenant_id", ""), store_code=store_code, sku=sku,
        )
    except ExclusionsNotFoundError as e:
        raise HTTPException(404, str(e))


@router.get("/exclusions")
async def list_exclusions(user: dict = Depends(_dep_user)):
    """List all active exclusions for the tenant."""
    from domains.buy_planning import ExclusionsRepository, ExclusionsService
    svc = ExclusionsService(ExclusionsRepository(get_db()))
    return await svc.list_all(user.get("tenant_id", ""))
