"""Inventory ingestion + safety-stock config/calculation endpoints."""

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ._shared import router, _dep_user, get_db


# ─────────────── Inventory ───────────────

class InventoryRecordModel(BaseModel):
    store_code: str
    sku: str
    date: str  # ISO date string
    soh: int = 0
    in_transit: int = 0
    open_po_qty: int = 0


class BulkInventoryUploadReq(BaseModel):
    records: list
    source: str = "api"


@router.post("/inventory/bulk")
async def bulk_upload_inventory(body: BulkInventoryUploadReq, user: dict = Depends(_dep_user)):
    """Bulk upload store-level inventory data (SOH, in-transit, open PO)."""
    from domains.buy_planning import (
        InventoryRepository, InventoryService, InventoryValidationError,
    )
    svc = InventoryService(InventoryRepository(get_db()))
    try:
        return await svc.bulk_upload(
            tenant_id=user.get("tenant_id", ""),
            records=body.records, source=body.source,
            user_email=user.get("email", ""),
        )
    except InventoryValidationError as e:
        raise HTTPException(400, str(e))


@router.get("/inventory")
async def list_inventory(store_code: Optional[str] = None, sku: Optional[str] = None, limit: int = 200, user: dict = Depends(_dep_user)):
    """List inventory records, optionally filtered by store/sku."""
    from domains.buy_planning import InventoryRepository, InventoryService
    svc = InventoryService(InventoryRepository(get_db()))
    return await svc.list_records(
        tenant_id=user.get("tenant_id", ""),
        store_code=store_code, sku=sku, limit=limit,
    )


@router.get("/inventory/summary")
async def inventory_summary(user: dict = Depends(_dep_user)):
    """Get inventory summary stats."""
    from domains.buy_planning import InventoryRepository, InventoryService
    svc = InventoryService(InventoryRepository(get_db()))
    return await svc.summary(user.get("tenant_id", ""))


@router.get("/inventory/sync-status")
async def inventory_sync_status(user: dict = Depends(_dep_user)):
    """Get last inventory sync info."""
    from domains.buy_planning import InventoryRepository, InventoryService
    svc = InventoryService(InventoryRepository(get_db()))
    return await svc.sync_status(user.get("tenant_id", ""))


# ─────────────── Safety Stock ───────────────

class SafetyStockConfigReq(BaseModel):
    service_level: float = 0.95
    review_period_days: int = 7
    max_safety_weeks: int = 12


@router.get("/safety-stock/config")
async def get_safety_stock_config(user: dict = Depends(_dep_user)):
    """Get safety stock config for the tenant."""
    from domains.buy_planning import SafetyStockRepository, SafetyStockService
    svc = SafetyStockService(SafetyStockRepository(get_db()))
    return await svc.get_config(user.get("tenant_id", ""))


@router.put("/safety-stock/config")
async def set_safety_stock_config(body: SafetyStockConfigReq, user: dict = Depends(_dep_user)):
    """Update safety stock config."""
    from domains.buy_planning import (
        SafetyStockRepository, SafetyStockService, SafetyStockValidationError,
    )
    svc = SafetyStockService(SafetyStockRepository(get_db()))
    try:
        return await svc.set_config(
            tenant_id=user.get("tenant_id", ""),
            service_level=body.service_level,
            review_period_days=body.review_period_days,
            max_safety_weeks=body.max_safety_weeks,
            user_email=user.get("email", ""),
        )
    except SafetyStockValidationError as e:
        raise HTTPException(400, str(e))


@router.post("/safety-stock/config/reset")
async def reset_safety_stock_config(user: dict = Depends(_dep_user)):
    """Reset to default safety stock config."""
    from domains.buy_planning import SafetyStockRepository, SafetyStockService
    svc = SafetyStockService(SafetyStockRepository(get_db()))
    return await svc.reset(user.get("tenant_id", ""))


@router.get("/safety-stock/calculate")
async def calculate_safety_stock(sku: str, lead_time_days: int = 14, user: dict = Depends(_dep_user)):
    """Calculate statistical safety stock for a single SKU."""
    from domains.buy_planning import SafetyStockRepository, SafetyStockService
    svc = SafetyStockService(SafetyStockRepository(get_db()))
    return await svc.calculate(
        tenant_id=user.get("tenant_id", ""),
        sku=sku, lead_time_days=lead_time_days,
    )
