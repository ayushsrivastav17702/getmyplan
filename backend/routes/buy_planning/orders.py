"""Order consolidation + phased replenishment endpoints."""

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ._shared import router, _dep_user, get_db


# PO status lifecycle (mirrored in domains/buy_planning/orders.PO_STATUSES).
PO_STATUSES = ["draft", "sent", "confirmed", "shipped", "received", "cancelled"]

# Default phase splits by style mix — kept for any client that wants them.
DEFAULT_PHASE_SPLITS = {
    "Core": [50, 30, 20],
    "Fashion": [40, 35, 25],
    "Test": [30, 30, 40],
}


class ConsolidateReq(BaseModel):
    plan_id: str


class POStatusReq(BaseModel):
    status: str


class PhasedReq(BaseModel):
    po_number: str
    phase_weeks: list = [0, 2, 4]
    phase_percentages: list = [50, 30, 20]


@router.post("/orders/consolidate")
async def consolidate_orders(body: ConsolidateReq, user: dict = Depends(_dep_user)):
    """Consolidate an approved buy plan into supplier-level POs grouped by category."""
    from domains.buy_planning import (
        OrdersRepository, OrdersService,
        OrdersNotFoundError, OrdersValidationError,
    )
    svc = OrdersService(OrdersRepository(get_db()))
    try:
        return await svc.consolidate(
            tenant_id=user.get("tenant_id", ""),
            plan_id=body.plan_id, user_email=user.get("email", ""),
        )
    except OrdersNotFoundError as e:
        raise HTTPException(404, str(e))
    except OrdersValidationError as e:
        raise HTTPException(400, str(e))


@router.get("/orders")
async def list_orders(plan_id: Optional[str] = None, status: Optional[str] = None, user: dict = Depends(_dep_user)):
    """List consolidated POs."""
    from domains.buy_planning import OrdersRepository, OrdersService
    svc = OrdersService(OrdersRepository(get_db()))
    return await svc.list_pos(
        tenant_id=user.get("tenant_id", ""), plan_id=plan_id, status=status,
    )


@router.get("/orders/phased")
async def list_phased_pos(user: dict = Depends(_dep_user)):
    """List all phased POs."""
    from domains.buy_planning import OrdersRepository, OrdersService
    svc = OrdersService(OrdersRepository(get_db()))
    return await svc.list_phased(user.get("tenant_id", ""))


@router.get("/orders/{po_number}")
async def get_order(po_number: str, user: dict = Depends(_dep_user)):
    """Get a single PO with full item details."""
    from domains.buy_planning import OrdersRepository, OrdersService, OrdersNotFoundError
    svc = OrdersService(OrdersRepository(get_db()))
    try:
        return await svc.get_po(user.get("tenant_id", ""), po_number)
    except OrdersNotFoundError as e:
        raise HTTPException(404, str(e))


@router.put("/orders/{po_number}/status")
async def update_po_status(po_number: str, body: POStatusReq, user: dict = Depends(_dep_user)):
    """Update PO status (draft → sent → confirmed → shipped → received)."""
    from domains.buy_planning import (
        OrdersRepository, OrdersService,
        OrdersNotFoundError, OrdersValidationError,
    )
    svc = OrdersService(OrdersRepository(get_db()))
    try:
        return await svc.update_status(
            tenant_id=user.get("tenant_id", ""),
            po_number=po_number, status=body.status,
            user_email=user.get("email", ""),
        )
    except OrdersNotFoundError as e:
        raise HTTPException(404, str(e))
    except OrdersValidationError as e:
        raise HTTPException(400, str(e))


@router.post("/orders/phase")
async def create_phased_replenishment(body: PhasedReq, user: dict = Depends(_dep_user)):
    """Split a PO into phased shipments over time."""
    from domains.buy_planning import (
        OrdersRepository, OrdersService,
        OrdersNotFoundError, OrdersValidationError,
    )
    svc = OrdersService(OrdersRepository(get_db()))
    try:
        return await svc.create_phased(
            tenant_id=user.get("tenant_id", ""),
            po_number=body.po_number,
            phase_weeks=body.phase_weeks,
            phase_pcts=body.phase_percentages,
            user_email=user.get("email", ""),
        )
    except OrdersNotFoundError as e:
        raise HTTPException(404, str(e))
    except OrdersValidationError as e:
        raise HTTPException(400, str(e))
