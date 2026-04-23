"""Manual override (store-wedge, style-mix) + audit log endpoints."""

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ._shared import router, _dep_user, get_db


class WedgeOverrideReq(BaseModel):
    store_code: str
    wedge_class: str  # A, B, C
    reason: str = ""


class MixOverrideReq(BaseModel):
    style: str
    style_mix: str  # Core, Fashion, Test
    reason: str = ""


@router.post("/overrides/store-wedge")
async def override_store_wedge(body: WedgeOverrideReq, user: dict = Depends(_dep_user)):
    """Manually override a store's wedge class with audit trail."""
    from domains.buy_planning import (
        StoreWedgeRepository, StoreWedgeService,
        StoreWedgeValidationError, StoreWedgeNotFoundError,
    )
    svc = StoreWedgeService(StoreWedgeRepository(get_db()))
    try:
        return await svc.override(
            store_code=body.store_code, wedge=body.wedge_class, reason=body.reason,
            user_email=user.get("email", ""), tenant_id=user.get("tenant_id", ""),
        )
    except StoreWedgeValidationError as e:
        raise HTTPException(400, str(e))
    except StoreWedgeNotFoundError as e:
        raise HTTPException(404, str(e))


@router.delete("/overrides/store-wedge/{store_code}")
async def revert_store_wedge_override(store_code: str, user: dict = Depends(_dep_user)):
    """Remove manual override — store will be reclassified on next auto-run."""
    from domains.buy_planning import StoreWedgeRepository, StoreWedgeService
    svc = StoreWedgeService(StoreWedgeRepository(get_db()))
    return await svc.revert_override(store_code, user.get("email", ""))


@router.post("/overrides/style-mix")
async def override_style_mix(body: MixOverrideReq, user: dict = Depends(_dep_user)):
    """Manually override a style's mix classification with audit trail."""
    from domains.buy_planning import (
        StyleMixRepository, StyleMixService,
        StyleMixValidationError, StyleMixNotFoundError,
    )
    svc = StyleMixService(StyleMixRepository(get_db()))
    try:
        return await svc.override(
            style=body.style, mix=body.style_mix, reason=body.reason,
            user_email=user.get("email", ""), tenant_id=user.get("tenant_id", ""),
        )
    except StyleMixValidationError as e:
        raise HTTPException(400, str(e))
    except StyleMixNotFoundError as e:
        raise HTTPException(404, str(e))


@router.delete("/overrides/style-mix/{style}")
async def revert_style_mix_override(style: str, user: dict = Depends(_dep_user)):
    """Remove manual override — style will be reclassified on next auto-run."""
    from domains.buy_planning import StyleMixRepository, StyleMixService
    svc = StyleMixService(StyleMixRepository(get_db()))
    return await svc.revert_override(style, user.get("email", ""))


@router.get("/overrides/history")
async def get_override_history(entity_type: Optional[str] = None, limit: int = 50, user: dict = Depends(_dep_user)):
    """Get history of manual overrides."""
    from domains.buy_planning import AuditLogRepository, AuditLogService
    svc = AuditLogService(AuditLogRepository(get_db()))
    return await svc.get_override_history(entity_type=entity_type, limit=limit)


@router.get("/audit-log")
async def get_audit_log(
    entity_type: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(_dep_user),
):
    """Get comprehensive audit log for all buy planning changes."""
    from domains.buy_planning import AuditLogRepository, AuditLogService
    svc = AuditLogService(AuditLogRepository(get_db()))
    return await svc.get_audit_log(
        tenant_id=user.get("tenant_id", ""),
        entity_type=entity_type, source=source, limit=limit,
    )
