"""Buy-plan persistence + multi-level approval workflow endpoints."""

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ._shared import router, _dep_user, get_db
from .buy_formula import calculate_buy_formula, BuyFormulaReq


class GeneratePlanReq(BaseModel):
    plan_name: Optional[str] = None
    cover_days: int = 30
    safety_days: int = 7
    notes: Optional[str] = None


class UpdateItemQtyReq(BaseModel):
    item_index: int
    new_qty: int


class ApprovalActionReq(BaseModel):
    action: str
    comment: Optional[str] = None


@router.post("/buy-plans/generate")
async def generate_and_save_plan(body: GeneratePlanReq, user: dict = Depends(_dep_user)):
    """Generate a buy plan using the full formula and save to database."""
    from domains.buy_planning import BuyPlansRepository, BuyPlansService
    # Reuse existing buy-formula calculation
    calc_body = BuyFormulaReq(cover_days=body.cover_days, safety_days=body.safety_days)
    calc_result = await calculate_buy_formula(calc_body, user)
    svc = BuyPlansService(BuyPlansRepository(get_db()))
    return await svc.persist_from_formula(
        tenant_id=user.get("tenant_id", ""),
        user_email=user.get("email", ""),
        calc_result=calc_result,
        plan_name=body.plan_name,
        cover_days=body.cover_days, safety_days=body.safety_days,
        notes=body.notes,
    )


@router.get("/buy-plans")
async def list_buy_plans(status: Optional[str] = None, limit: int = 20, user: dict = Depends(_dep_user)):
    """List saved buy plans (without items for performance)."""
    from domains.buy_planning import BuyPlansRepository, BuyPlansService
    svc = BuyPlansService(BuyPlansRepository(get_db()))
    return await svc.list_plans(
        tenant_id=user.get("tenant_id", ""), status=status, limit=limit,
    )


@router.get("/buy-plans/{plan_id}")
async def get_buy_plan(plan_id: str, user: dict = Depends(_dep_user)):
    """Get a single buy plan with full item details."""
    from domains.buy_planning import (
        BuyPlansRepository, BuyPlansService, BuyPlansNotFoundError,
    )
    svc = BuyPlansService(BuyPlansRepository(get_db()))
    try:
        return await svc.get_plan(tenant_id=user.get("tenant_id", ""), plan_id=plan_id)
    except BuyPlansNotFoundError as e:
        raise HTTPException(404, str(e))


@router.put("/buy-plans/{plan_id}/items")
async def update_plan_item(plan_id: str, body: UpdateItemQtyReq, user: dict = Depends(_dep_user)):
    """Update quantity for a specific item in a draft plan."""
    from domains.buy_planning import (
        BuyPlansRepository, BuyPlansService,
        BuyPlansNotFoundError, BuyPlansValidationError,
    )
    svc = BuyPlansService(BuyPlansRepository(get_db()))
    try:
        return await svc.update_item_qty(
            tenant_id=user.get("tenant_id", ""), plan_id=plan_id,
            item_index=body.item_index, new_qty=body.new_qty,
            user_email=user.get("email", ""),
        )
    except BuyPlansNotFoundError as e:
        raise HTTPException(404, str(e))
    except BuyPlansValidationError as e:
        raise HTTPException(400, str(e))


@router.post("/buy-plans/{plan_id}/approval")
async def process_plan_approval(plan_id: str, body: ApprovalActionReq, user: dict = Depends(_dep_user)):
    """Process a multi-level approval action on a buy plan."""
    from domains.buy_planning import (
        BuyPlansRepository, BuyPlansService,
        BuyPlansNotFoundError, BuyPlansValidationError, BuyPlansForbiddenError,
    )
    svc = BuyPlansService(BuyPlansRepository(get_db()))
    try:
        return await svc.process_approval(
            tenant_id=user.get("tenant_id", ""), plan_id=plan_id,
            action=body.action, comment=body.comment,
            user_email=user.get("email", ""), role=user.get("role", "viewer"),
        )
    except BuyPlansNotFoundError as e:
        raise HTTPException(404, str(e))
    except BuyPlansValidationError as e:
        raise HTTPException(400, str(e))
    except BuyPlansForbiddenError as e:
        raise HTTPException(403, str(e))


@router.get("/buy-plans/{plan_id}/approval-history")
async def get_approval_history(plan_id: str, user: dict = Depends(_dep_user)):
    """Get the approval audit trail for a plan."""
    from domains.buy_planning import BuyPlansRepository, BuyPlansService
    svc = BuyPlansService(BuyPlansRepository(get_db()))
    return await svc.approval_history(
        tenant_id=user.get("tenant_id", ""), plan_id=plan_id,
    )


@router.post("/buy-plans/{plan_id}/approve")
async def approve_buy_plan(plan_id: str, user: dict = Depends(_dep_user)):
    """Simple approve (backward compat) — calls the multi-level submit+approve chain."""
    from domains.buy_planning import (
        BuyPlansRepository, BuyPlansService,
        BuyPlansNotFoundError, BuyPlansValidationError,
    )
    svc = BuyPlansService(BuyPlansRepository(get_db()))
    try:
        return await svc.fast_track_approve(
            tenant_id=user.get("tenant_id", ""), plan_id=plan_id,
            user_email=user.get("email", ""),
        )
    except BuyPlansNotFoundError as e:
        raise HTTPException(404, str(e))
    except BuyPlansValidationError as e:
        raise HTTPException(400, str(e))


@router.delete("/buy-plans/{plan_id}")
async def delete_buy_plan(plan_id: str, user: dict = Depends(_dep_user)):
    """Delete a draft buy plan."""
    from domains.buy_planning import (
        BuyPlansRepository, BuyPlansService,
        BuyPlansNotFoundError, BuyPlansValidationError,
    )
    svc = BuyPlansService(BuyPlansRepository(get_db()))
    try:
        return await svc.delete(
            tenant_id=user.get("tenant_id", ""), plan_id=plan_id,
        )
    except BuyPlansNotFoundError as e:
        raise HTTPException(404, str(e))
    except BuyPlansValidationError as e:
        raise HTTPException(400, str(e))
