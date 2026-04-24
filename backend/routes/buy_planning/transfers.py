"""Inter-Store Transfer (IST) Optimization route adapters."""

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ._shared import router, _dep_user, get_db


class OptimizeReq(BaseModel):
    donor_dos_threshold: float = 45
    recipient_dos_threshold: float = 7
    target_post_transfer_dos: float = 21
    min_donor_residual_dos: float = 30
    min_transfer_qty: int = 3
    lookback_days: int = 30
    max_suggestions: int = 500


@router.post("/transfers/optimize")
async def optimize_transfers(body: OptimizeReq, user: dict = Depends(_dep_user)):
    """Run the IST optimizer live — returns recommendations without saving."""
    from domains.buy_planning.transfers import TransfersRepository, TransfersService
    svc = TransfersService(TransfersRepository(get_db()))
    return await svc.optimize(
        tenant_id=user.get("tenant_id", ""), **body.model_dump(),
    )


@router.post("/transfers/generate")
async def generate_transfer_batch(body: OptimizeReq, user: dict = Depends(_dep_user)):
    """Run the IST optimizer + persist results as a draft batch."""
    from domains.buy_planning.transfers import TransfersRepository, TransfersService
    svc = TransfersService(TransfersRepository(get_db()))
    return await svc.generate_batch(
        tenant_id=user.get("tenant_id", ""),
        user_email=user.get("email", ""),
        **body.model_dump(),
    )


@router.get("/transfers")
async def list_transfer_batches(status: Optional[str] = None, limit: int = 20, user: dict = Depends(_dep_user)):
    """List IST batches (metadata only)."""
    from domains.buy_planning.transfers import TransfersRepository, TransfersService
    svc = TransfersService(TransfersRepository(get_db()))
    return await svc.list_batches(
        tenant_id=user.get("tenant_id", ""), status=status, limit=limit,
    )


@router.get("/transfers/{batch_id}")
async def get_transfer_batch(batch_id: str, user: dict = Depends(_dep_user)):
    """Get a single batch with full recommendations."""
    from domains.buy_planning.transfers import (
        TransfersRepository, TransfersService, NotFoundError,
    )
    svc = TransfersService(TransfersRepository(get_db()))
    try:
        return await svc.get_batch(
            tenant_id=user.get("tenant_id", ""), batch_id=batch_id,
        )
    except NotFoundError as e:
        raise HTTPException(404, str(e))


class StatusTransitionReq(BaseModel):
    action: str  # approve / reject / execute


_ACTION_TO_STATUS = {"approve": "approved", "reject": "rejected", "execute": "executed"}


@router.post("/transfers/{batch_id}/transition")
async def transition_transfer_batch(batch_id: str, body: StatusTransitionReq, user: dict = Depends(_dep_user)):
    """Approve / reject / execute a batch."""
    from domains.buy_planning.transfers import (
        TransfersRepository, TransfersService, NotFoundError, ValidationError,
    )
    new_status = _ACTION_TO_STATUS.get(body.action)
    if not new_status:
        raise HTTPException(400, f"action must be one of {list(_ACTION_TO_STATUS)}")
    svc = TransfersService(TransfersRepository(get_db()))
    try:
        return await svc.transition(
            tenant_id=user.get("tenant_id", ""), batch_id=batch_id,
            new_status=new_status, user_email=user.get("email", ""),
        )
    except NotFoundError as e:
        raise HTTPException(404, str(e))
    except ValidationError as e:
        raise HTTPException(400, str(e))
