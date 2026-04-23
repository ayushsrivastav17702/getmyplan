"""Display Minimums + Sell-Through config endpoints."""

from fastapi import Depends, HTTPException
from pydantic import BaseModel

from ._shared import router, _dep_user, get_db


# ─────────────── Display Minimums ───────────────

class DisplayMinimumReq(BaseModel):
    category: str
    store_wedge: str  # A, B, C
    min_facings: int = 2
    display_units_per_facing: int = 2


@router.get("/display-minimums")
async def get_display_minimums(user: dict = Depends(_dep_user)):
    """Get display minimum configuration per category × wedge."""
    from domains.buy_planning import DisplayMinimumsRepository, DisplayMinimumsService
    svc = DisplayMinimumsService(DisplayMinimumsRepository(get_db()))
    return await svc.list_configs()


@router.post("/display-minimums")
async def set_display_minimum(body: DisplayMinimumReq, user: dict = Depends(_dep_user)):
    """Set display minimum for a category × wedge combination."""
    from domains.buy_planning import DisplayMinimumsRepository, DisplayMinimumsService
    svc = DisplayMinimumsService(DisplayMinimumsRepository(get_db()))
    try:
        return await svc.set_config(
            category=body.category,
            store_wedge=body.store_wedge,
            min_facings=body.min_facings,
            display_units_per_facing=body.display_units_per_facing,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/display-minimums/{category}/{store_wedge}")
async def delete_display_minimum(category: str, store_wedge: str, user: dict = Depends(_dep_user)):
    from domains.buy_planning import (
        DisplayMinimumsRepository, DisplayMinimumsService, NotFoundError,
    )
    svc = DisplayMinimumsService(DisplayMinimumsRepository(get_db()))
    try:
        return await svc.delete_config(category=category, store_wedge=store_wedge)
    except NotFoundError as e:
        raise HTTPException(404, str(e))


# ─────────────── Sell-Through Config ───────────────

class SellThroughConfigReq(BaseModel):
    style_mix: str  # Core, Fashion, Test
    target_multiplier: float


@router.get("/sell-through-config")
async def get_sell_through_config(user: dict = Depends(_dep_user)):
    """Get sell-through multiplier config (tenant-specific + defaults)."""
    from domains.buy_planning import SellThroughRepository, SellThroughService
    svc = SellThroughService(SellThroughRepository(get_db()))
    return await svc.list_configs()


@router.put("/sell-through-config")
async def set_sell_through_config(body: SellThroughConfigReq, user: dict = Depends(_dep_user)):
    """Set sell-through multiplier for a style mix."""
    from domains.buy_planning import (
        SellThroughRepository, SellThroughService, SellThroughValidationError,
    )
    svc = SellThroughService(SellThroughRepository(get_db()))
    try:
        return await svc.set_config(
            style_mix=body.style_mix, multiplier=body.target_multiplier,
            user_email=user.get("email", ""), tenant_id=user.get("tenant_id", ""),
        )
    except SellThroughValidationError as e:
        raise HTTPException(400, str(e))


@router.post("/sell-through-config/reset")
async def reset_sell_through_config(user: dict = Depends(_dep_user)):
    """Reset all multipliers to system defaults."""
    from domains.buy_planning import SellThroughRepository, SellThroughService
    svc = SellThroughService(SellThroughRepository(get_db()))
    return await svc.reset()
