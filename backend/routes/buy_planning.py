"""Buy Planning module: Store Wedge Classification + Style Mix Tagging."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import io
import csv
from bson import ObjectId

router = APIRouter(prefix="/buy-planning", tags=["buy-planning"])

_db_func = None
_get_current_user = None


def init_buy_planning(get_db_func, get_current_user_func):
    global _db_func, _get_current_user
    _db_func = get_db_func
    _get_current_user = get_current_user_func


async def _dep_user(request: Request) -> dict:
    return await _get_current_user(request)


def _tenant_match(tenant_id: str) -> dict:
    """Match documents with or without tenant_id (handles sample data)."""
    return {"$or": [{"tenant_id": tenant_id}, {"tenant_id": {"$exists": False}}]}


# ── Store Wedge Classification ──

@router.post("/store-wedge/classify")
async def classify_store_wedge(user: dict = Depends(_dep_user)):
    """
    Classify stores into A/B/C wedge based on revenue contribution.
    A = Top 20% by revenue (≈80% of sales)
    B = Next 30% by revenue (≈15% of sales)
    C = Bottom 50% by revenue (≈5% of sales)
    """
    from domains.buy_planning import (
        StoreWedgeRepository, StoreWedgeService, StoreWedgeNoDataError,
    )
    svc = StoreWedgeService(StoreWedgeRepository(_db_func()))
    try:
        return await svc.classify(
            tenant_id=user.get("tenant_id", ""),
            user_email=user.get("email", "system"),
        )
    except StoreWedgeNoDataError as e:
        raise HTTPException(400, str(e))


@router.get("/store-wedge")
async def get_store_wedge(user: dict = Depends(_dep_user)):
    """Get current store wedge classification."""
    from domains.buy_planning import StoreWedgeRepository, StoreWedgeService
    svc = StoreWedgeService(StoreWedgeRepository(_db_func()))
    return await svc.list_classifications(user.get("tenant_id", ""))


# ── Style Mix Tagging ──

@router.post("/style-mix/classify")
async def classify_style_mix(user: dict = Depends(_dep_user)):
    """
    Classify SKU styles into Core / Fashion / Test.
    Core  = avg >5 units/week, present >80% of weeks
    Fashion = peak-to-avg ratio >3x, lifecycle <26 weeks
    Test  = <8 weeks old OR <2 units/week avg
    """
    from domains.buy_planning import StyleMixRepository, StyleMixService
    svc = StyleMixService(StyleMixRepository(_db_func()))
    return await svc.classify(
        tenant_id=user.get("tenant_id", ""),
        user_email=user.get("email", "system"),
    )


@router.get("/style-mix")
async def get_style_mix(user: dict = Depends(_dep_user)):
    """Get current style mix classification for all SKUs."""
    from domains.buy_planning import StyleMixRepository, StyleMixService
    svc = StyleMixService(StyleMixRepository(_db_func()))
    return await svc.list_classifications()


# ── Assortment Matrix (Wedge × Mix) ──

@router.get("/assortment-matrix")
async def get_assortment_matrix(user: dict = Depends(_dep_user)):
    """
    Return the Wedge × Style Mix assortment matrix:
    A-Stores: Core + Fashion + Test (Full assortment)
    B-Stores: Core + Fashion (Standard assortment)
    C-Stores: Core only (Efficiency assortment)
    """
    from domains.buy_planning import AssortmentMatrixRepository, AssortmentMatrixService
    svc = AssortmentMatrixService(AssortmentMatrixRepository(_db_func()))
    return await svc.get_matrix(user.get("tenant_id", ""))


# ═══════════════════════════════════════════════════
# PHASE 2: Display Minimums + Full Buy Formula
# ═══════════════════════════════════════════════════

class DisplayMinimumReq(BaseModel):
    category: str
    store_wedge: str  # A, B, C
    min_facings: int = 2
    display_units_per_facing: int = 2


@router.get("/display-minimums")
async def get_display_minimums(user: dict = Depends(_dep_user)):
    """Get display minimum configuration per category × wedge."""
    from domains.buy_planning import DisplayMinimumsRepository, DisplayMinimumsService
    svc = DisplayMinimumsService(DisplayMinimumsRepository(_db_func()))
    return await svc.list_configs()


@router.post("/display-minimums")
async def set_display_minimum(body: DisplayMinimumReq, user: dict = Depends(_dep_user)):
    """Set display minimum for a category × wedge combination."""
    from domains.buy_planning import DisplayMinimumsRepository, DisplayMinimumsService
    svc = DisplayMinimumsService(DisplayMinimumsRepository(_db_func()))
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
    svc = DisplayMinimumsService(DisplayMinimumsRepository(_db_func()))
    try:
        return await svc.delete_config(category=category, store_wedge=store_wedge)
    except NotFoundError as e:
        raise HTTPException(404, str(e))


class SellThroughConfigReq(BaseModel):
    style_mix: str  # Core, Fashion, Test
    target_multiplier: float


@router.get("/sell-through-config")
async def get_sell_through_config(user: dict = Depends(_dep_user)):
    """Get sell-through multiplier config (tenant-specific + defaults)."""
    from domains.buy_planning import SellThroughRepository, SellThroughService
    svc = SellThroughService(SellThroughRepository(_db_func()))
    return await svc.list_configs()


@router.put("/sell-through-config")
async def set_sell_through_config(body: SellThroughConfigReq, user: dict = Depends(_dep_user)):
    """Set sell-through multiplier for a style mix."""
    from domains.buy_planning import (
        SellThroughRepository, SellThroughService, SellThroughValidationError,
    )
    svc = SellThroughService(SellThroughRepository(_db_func()))
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
    svc = SellThroughService(SellThroughRepository(_db_func()))
    return await svc.reset()


class BuyFormulaReq(BaseModel):
    cover_days: int = 30
    safety_days: int = 7
    sell_through_targets: Optional[dict] = None  # override defaults


@router.post("/buy-formula/calculate")
async def calculate_buy_formula(body: BuyFormulaReq, user: dict = Depends(_dep_user)):
    """
    Full Buy Formula:
    buy_qty = MAX(
        (target_sell_through × forecasted_demand) - current_SOH,
        display_minimum_units × store_count,
        safety_stock_units
    )
    """
    from domains.buy_planning import BuyFormulaRepository, BuyFormulaService
    svc = BuyFormulaService(BuyFormulaRepository(_db_func()))
    return await svc.calculate(
        tenant_id=user.get("tenant_id", ""),
        cover_days=body.cover_days, safety_days=body.safety_days,
        sell_through_targets=body.sell_through_targets,
    )


# ═══════════════════════════════════════════════════
# PHASE 3: DNA Tagging + Piece-Level Attribution
# ═══════════════════════════════════════════════════

class DNATagReq(BaseModel):
    sku: str
    launch_date: Optional[str] = None
    flow_rank: Optional[int] = None  # 1=Hero, 2=Core, 3=Fill-in
    lifecycle_stage: Optional[str] = None  # Pre-launch, Launch, Peak, Decline, Exit
    expected_weeks: Optional[int] = None


class DNABulkTagReq(BaseModel):
    style: str
    launch_date: Optional[str] = None
    flow_rank: Optional[int] = None
    lifecycle_stage: Optional[str] = None
    expected_weeks: Optional[int] = None


@router.post("/dna-tag")
async def tag_sku_dna(body: DNATagReq, user: dict = Depends(_dep_user)):
    """Tag a single SKU with DNA attributes."""
    from domains.buy_planning import DnaTagsRepository, DnaTagsService, DnaTagsNotFoundError
    svc = DnaTagsService(DnaTagsRepository(_db_func()))
    try:
        return await svc.tag_sku(
            sku=body.sku, launch_date=body.launch_date, flow_rank=body.flow_rank,
            lifecycle_stage=body.lifecycle_stage, expected_weeks=body.expected_weeks,
        )
    except DnaTagsNotFoundError as e:
        raise HTTPException(404, str(e))


@router.post("/dna-tag/bulk")
async def tag_style_dna_bulk(body: DNABulkTagReq, user: dict = Depends(_dep_user)):
    """Tag all SKUs of a style with DNA attributes."""
    from domains.buy_planning import DnaTagsRepository, DnaTagsService
    svc = DnaTagsService(DnaTagsRepository(_db_func()))
    return await svc.tag_style_bulk(
        style=body.style, launch_date=body.launch_date, flow_rank=body.flow_rank,
        lifecycle_stage=body.lifecycle_stage, expected_weeks=body.expected_weeks,
    )


@router.post("/dna-tag/auto")
async def auto_tag_dna(user: dict = Depends(_dep_user)):
    """
    Auto-tag DNA from sales data:
      flow_rank: 1=Hero (top 80% rev), 2=Core (next 15%), 3=Fill-in (bottom 5%)
      lifecycle_stage: Launch (≤4w) / Peak / Decline / Exit (no sale 30d+)
    """
    from domains.buy_planning import DnaTagsRepository, DnaTagsService
    svc = DnaTagsService(DnaTagsRepository(_db_func()))
    return await svc.auto_tag(user.get("tenant_id", ""))


@router.get("/dna-tags")
async def get_dna_tags(user: dict = Depends(_dep_user)):
    """Get DNA tags grouped by style."""
    from domains.buy_planning import DnaTagsRepository, DnaTagsService
    svc = DnaTagsService(DnaTagsRepository(_db_func()))
    return await svc.list_tags(user.get("tenant_id", ""))


# ── Piece-Level Attribution Matrix ──

@router.get("/attribution/matrix")
async def get_attribution_matrix(user: dict = Depends(_dep_user)):
    """
    Return SKU → Store cluster attribution.
    Core → ALL stores (A+B+C)
    Fashion → A + B only
    Test → A only
    """
    from domains.buy_planning import AttributionRepository, AttributionService
    svc = AttributionService(AttributionRepository(_db_func()))
    return await svc.get_matrix(user.get("tenant_id", ""))

# ═══════════════════════════════════════════════════
# FEATURE B: Manual Overrides with Audit
# ═══════════════════════════════════════════════════

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
    svc = StoreWedgeService(StoreWedgeRepository(_db_func()))
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
    svc = StoreWedgeService(StoreWedgeRepository(_db_func()))
    return await svc.revert_override(store_code, user.get("email", ""))


@router.post("/overrides/style-mix")
async def override_style_mix(body: MixOverrideReq, user: dict = Depends(_dep_user)):
    """Manually override a style's mix classification with audit trail."""
    from domains.buy_planning import (
        StyleMixRepository, StyleMixService,
        StyleMixValidationError, StyleMixNotFoundError,
    )
    svc = StyleMixService(StyleMixRepository(_db_func()))
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
    svc = StyleMixService(StyleMixRepository(_db_func()))
    return await svc.revert_override(style, user.get("email", ""))


@router.get("/overrides/history")
async def get_override_history(entity_type: Optional[str] = None, limit: int = 50, user: dict = Depends(_dep_user)):
    """Get history of manual overrides."""
    from domains.buy_planning import AuditLogRepository, AuditLogService
    svc = AuditLogService(AuditLogRepository(_db_func()))
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
    svc = AuditLogService(AuditLogRepository(_db_func()))
    return await svc.get_audit_log(
        tenant_id=user.get("tenant_id", ""),
        entity_type=entity_type, source=source, limit=limit,
    )


# ═══════════════════════════════════════════════════
# FEATURE C: Export Buy Plan to CSV
# ═══════════════════════════════════════════════════

@router.get("/buy-formula/export/csv")
async def export_buy_plan_csv(cover_days: int = 30, safety_days: int = 7, user: dict = Depends(_dep_user)):
    """Export the full buy plan to CSV — uses the same BuyFormulaService as /calculate for consistency."""
    from domains.buy_planning import BuyFormulaRepository, BuyFormulaService
    repo = BuyFormulaRepository(_db_func())
    svc = BuyFormulaService(repo)
    tenant_id = user.get("tenant_id", "")
    result = await svc.calculate(
        tenant_id=tenant_id, cover_days=cover_days, safety_days=safety_days,
    )
    sku_meta = await repo.load_sku_meta(tenant_id)  # for DNA columns (flow_rank, lifecycle, launch_date)
    rows = svc.to_csv_rows(result, sku_meta)

    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        buf.write("No data available\n")
    buf.seek(0)

    filename = f"buy_plan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ═══════════════════════════════════════════════════
# BUY PLAN PERSISTENCE & APPROVAL WORKFLOW
# ═══════════════════════════════════════════════════

class GeneratePlanReq(BaseModel):
    plan_name: Optional[str] = None
    cover_days: int = 30
    safety_days: int = 7
    notes: Optional[str] = None


class UpdateItemQtyReq(BaseModel):
    item_index: int
    new_qty: int


@router.post("/buy-plans/generate")
async def generate_and_save_plan(body: GeneratePlanReq, user: dict = Depends(_dep_user)):
    """Generate a buy plan using the full formula and save to database."""
    from domains.buy_planning import BuyPlansRepository, BuyPlansService
    # Reuse existing buy-formula calculation
    calc_body = BuyFormulaReq(cover_days=body.cover_days, safety_days=body.safety_days)
    calc_result = await calculate_buy_formula(calc_body, user)
    svc = BuyPlansService(BuyPlansRepository(_db_func()))
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
    svc = BuyPlansService(BuyPlansRepository(_db_func()))
    return await svc.list_plans(
        tenant_id=user.get("tenant_id", ""), status=status, limit=limit,
    )


@router.get("/buy-plans/{plan_id}")
async def get_buy_plan(plan_id: str, user: dict = Depends(_dep_user)):
    """Get a single buy plan with full item details."""
    from domains.buy_planning import (
        BuyPlansRepository, BuyPlansService, BuyPlansNotFoundError,
    )
    svc = BuyPlansService(BuyPlansRepository(_db_func()))
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
    svc = BuyPlansService(BuyPlansRepository(_db_func()))
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


# ═══════════════════════════════════════════════════
# MULTI-LEVEL APPROVAL WORKFLOW (workflow tables live in domains/buy_planning/buy_plans.py)
# ═══════════════════════════════════════════════════


class ApprovalActionReq(BaseModel):
    action: str
    comment: Optional[str] = None


@router.post("/buy-plans/{plan_id}/approval")
async def process_plan_approval(plan_id: str, body: ApprovalActionReq, user: dict = Depends(_dep_user)):
    """Process a multi-level approval action on a buy plan."""
    from domains.buy_planning import (
        BuyPlansRepository, BuyPlansService,
        BuyPlansNotFoundError, BuyPlansValidationError, BuyPlansForbiddenError,
    )
    svc = BuyPlansService(BuyPlansRepository(_db_func()))
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
    svc = BuyPlansService(BuyPlansRepository(_db_func()))
    return await svc.approval_history(
        tenant_id=user.get("tenant_id", ""), plan_id=plan_id,
    )


# Keep old simple approve for backward compat
@router.post("/buy-plans/{plan_id}/approve")
async def approve_buy_plan(plan_id: str, user: dict = Depends(_dep_user)):
    """Simple approve (backward compat) - calls multi-level submit+approve chain."""
    from domains.buy_planning import (
        BuyPlansRepository, BuyPlansService,
        BuyPlansNotFoundError, BuyPlansValidationError,
    )
    svc = BuyPlansService(BuyPlansRepository(_db_func()))
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
    svc = BuyPlansService(BuyPlansRepository(_db_func()))
    try:
        return await svc.delete(
            tenant_id=user.get("tenant_id", ""), plan_id=plan_id,
        )
    except BuyPlansNotFoundError as e:
        raise HTTPException(404, str(e))
    except BuyPlansValidationError as e:
        raise HTTPException(400, str(e))



# ═══════════════════════════════════════════════════
# STORE ATTRIBUTES (Format, City Tier, Region)
# ═══════════════════════════════════════════════════

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
    svc = StoreAttributesService(StoreAttributesRepository(_db_func()))
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


# ═══════════════════════════════════════════════════
# EXCLUSION LIST MANAGEMENT
# ═══════════════════════════════════════════════════

class ExclusionCreateReq(BaseModel):
    store_code: str
    sku: str
    reason: str = ""
    expires_at: Optional[str] = None


@router.post("/exclusions")
async def add_exclusion(body: ExclusionCreateReq, user: dict = Depends(_dep_user)):
    """Add a store-SKU exclusion (excluded from buy plans)."""
    from domains.buy_planning import ExclusionsRepository, ExclusionsService
    svc = ExclusionsService(ExclusionsRepository(_db_func()))
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
    svc = ExclusionsService(ExclusionsRepository(_db_func()))
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
    svc = ExclusionsService(ExclusionsRepository(_db_func()))
    return await svc.list_all(user.get("tenant_id", ""))


# ═══════════════════════════════════════════════════
# INVENTORY INGESTION
# ═══════════════════════════════════════════════════

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
    svc = InventoryService(InventoryRepository(_db_func()))
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
    svc = InventoryService(InventoryRepository(_db_func()))
    return await svc.list_records(
        tenant_id=user.get("tenant_id", ""),
        store_code=store_code, sku=sku, limit=limit,
    )


@router.get("/inventory/summary")
async def inventory_summary(user: dict = Depends(_dep_user)):
    """Get inventory summary stats."""
    from domains.buy_planning import InventoryRepository, InventoryService
    svc = InventoryService(InventoryRepository(_db_func()))
    return await svc.summary(user.get("tenant_id", ""))


@router.get("/inventory/sync-status")
async def inventory_sync_status(user: dict = Depends(_dep_user)):
    """Get last inventory sync info."""
    from domains.buy_planning import InventoryRepository, InventoryService
    svc = InventoryService(InventoryRepository(_db_func()))
    return await svc.sync_status(user.get("tenant_id", ""))


# ═══════════════════════════════════════════════════
# SAFETY STOCK CONFIGURATION & CALCULATION
# ═══════════════════════════════════════════════════

class SafetyStockConfigReq(BaseModel):
    service_level: float = 0.95
    review_period_days: int = 7
    max_safety_weeks: int = 12


@router.get("/safety-stock/config")
async def get_safety_stock_config(user: dict = Depends(_dep_user)):
    """Get safety stock config for the tenant."""
    from domains.buy_planning import SafetyStockRepository, SafetyStockService
    svc = SafetyStockService(SafetyStockRepository(_db_func()))
    return await svc.get_config(user.get("tenant_id", ""))


@router.put("/safety-stock/config")
async def set_safety_stock_config(body: SafetyStockConfigReq, user: dict = Depends(_dep_user)):
    """Update safety stock config."""
    from domains.buy_planning import (
        SafetyStockRepository, SafetyStockService, SafetyStockValidationError,
    )
    svc = SafetyStockService(SafetyStockRepository(_db_func()))
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
    svc = SafetyStockService(SafetyStockRepository(_db_func()))
    return await svc.reset(user.get("tenant_id", ""))


@router.get("/safety-stock/calculate")
async def calculate_safety_stock(sku: str, lead_time_days: int = 14, user: dict = Depends(_dep_user)):
    """Calculate statistical safety stock for a single SKU."""
    from domains.buy_planning import SafetyStockRepository, SafetyStockService
    svc = SafetyStockService(SafetyStockRepository(_db_func()))
    return await svc.calculate(
        tenant_id=user.get("tenant_id", ""),
        sku=sku, lead_time_days=lead_time_days,
    )



# ═══════════════════════════════════════════════════
# PHASE 1: ORDER CONSOLIDATION & PO MANAGEMENT
# ═══════════════════════════════════════════════════

PO_STATUSES = ["draft", "sent", "confirmed", "shipped", "received", "cancelled"]


class ConsolidateReq(BaseModel):
    plan_id: str


@router.post("/orders/consolidate")
async def consolidate_orders(body: ConsolidateReq, user: dict = Depends(_dep_user)):
    """Consolidate an approved buy plan into supplier-level POs grouped by category."""
    from domains.buy_planning import (
        OrdersRepository, OrdersService,
        OrdersNotFoundError, OrdersValidationError,
    )
    svc = OrdersService(OrdersRepository(_db_func()))
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
    svc = OrdersService(OrdersRepository(_db_func()))
    return await svc.list_pos(
        tenant_id=user.get("tenant_id", ""), plan_id=plan_id, status=status,
    )


@router.get("/orders/phased")
async def list_phased_pos(user: dict = Depends(_dep_user)):
    """List all phased POs."""
    from domains.buy_planning import OrdersRepository, OrdersService
    svc = OrdersService(OrdersRepository(_db_func()))
    return await svc.list_phased(user.get("tenant_id", ""))


@router.get("/orders/{po_number}")
async def get_order(po_number: str, user: dict = Depends(_dep_user)):
    """Get a single PO with full item details."""
    from domains.buy_planning import OrdersRepository, OrdersService, OrdersNotFoundError
    svc = OrdersService(OrdersRepository(_db_func()))
    try:
        return await svc.get_po(user.get("tenant_id", ""), po_number)
    except OrdersNotFoundError as e:
        raise HTTPException(404, str(e))


class POStatusReq(BaseModel):
    status: str


@router.put("/orders/{po_number}/status")
async def update_po_status(po_number: str, body: POStatusReq, user: dict = Depends(_dep_user)):
    """Update PO status (draft → sent → confirmed → shipped → received)."""
    from domains.buy_planning import (
        OrdersRepository, OrdersService,
        OrdersNotFoundError, OrdersValidationError,
    )
    svc = OrdersService(OrdersRepository(_db_func()))
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


# ═══════════════════════════════════════════════════
# PHASE 2: PHASED REPLENISHMENT
# ═══════════════════════════════════════════════════

DEFAULT_PHASE_SPLITS = {
    "Core": [50, 30, 20],
    "Fashion": [40, 35, 25],
    "Test": [30, 30, 40],
}


class PhasedReq(BaseModel):
    po_number: str
    phase_weeks: list = [0, 2, 4]
    phase_percentages: list = [50, 30, 20]


@router.post("/orders/phase")
async def create_phased_replenishment(body: PhasedReq, user: dict = Depends(_dep_user)):
    """Split a PO into phased shipments over time."""
    from domains.buy_planning import (
        OrdersRepository, OrdersService,
        OrdersNotFoundError, OrdersValidationError,
    )
    svc = OrdersService(OrdersRepository(_db_func()))
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


# ═══════════════════════════════════════════════════
# PHASE 3: PROMOTION CALENDAR & LIFT FACTORS
# ═══════════════════════════════════════════════════

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
    svc = PromotionsService(PromotionsRepository(_db_func()))
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
    svc = PromotionsService(PromotionsRepository(_db_func()))
    return await svc.list_all(user.get("tenant_id", ""), status)


@router.put("/promotions/{promo_id}")
async def update_promotion(promo_id: str, body: PromotionCreateReq, user: dict = Depends(_dep_user)):
    """Update a promotion."""
    from domains.buy_planning import (
        PromotionsRepository, PromotionsService,
        PromotionsNotFoundError, PromotionsValidationError,
    )
    svc = PromotionsService(PromotionsRepository(_db_func()))
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
    svc = PromotionsService(PromotionsRepository(_db_func()))
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
    svc = PromotionsService(PromotionsRepository(_db_func()))
    return await svc.get_active_lifts(user.get("tenant_id", ""))


# ═══════════════════════════════════════════════════
# BINDING FACTOR ANALYTICS  (display-min misconfiguration detector)
# ═══════════════════════════════════════════════════

@router.post("/analytics/backfill-binding-breakdown")
async def backfill_binding_breakdown(user: dict = Depends(_dep_user)):
    """
    One-shot: backfill `binding_breakdown` onto historical buy_plans that
    pre-date the field. Idempotent — existing breakdowns are recomputed.
    """
    from domains.buy_planning import (
        BindingAnalyticsRepository, BindingAnalyticsService,
        BindingAnalyticsForbiddenError,
    )
    svc = BindingAnalyticsService(BindingAnalyticsRepository(_db_func()))
    try:
        return await svc.backfill(
            tenant_id=user.get("tenant_id", ""),
            role=user.get("role", "viewer"),
        )
    except BindingAnalyticsForbiddenError as e:
        raise HTTPException(403, str(e))


@router.get("/analytics/binding-factor")
async def binding_factor_analytics(limit: int = 10, user: dict = Depends(_dep_user)):
    """
    Analytics for the "where did the buy qty come from?" question.
    Returns:
      - `latest`: the most recent plan's breakdown (for doughnut chart)
      - `trend`: last N plans ordered oldest→newest (for time-series line)
      - `worst_categories`: categories with highest floor_override_pct across last N plans
      - `plan_count`, `total_skus_analyzed`
    """
    from domains.buy_planning import BindingAnalyticsRepository, BindingAnalyticsService
    svc = BindingAnalyticsService(BindingAnalyticsRepository(_db_func()))
    return await svc.get_analytics(tenant_id=user.get("tenant_id", ""), limit=limit)
