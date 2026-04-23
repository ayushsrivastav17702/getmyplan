"""Classification endpoints: store-wedge, style-mix, assortment-matrix, attribution."""

from fastapi import Depends, HTTPException

from ._shared import router, _dep_user, get_db


# ─────────────── Store Wedge Classification ───────────────

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
    svc = StoreWedgeService(StoreWedgeRepository(get_db()))
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
    svc = StoreWedgeService(StoreWedgeRepository(get_db()))
    return await svc.list_classifications(user.get("tenant_id", ""))


# ─────────────── Style Mix Tagging ───────────────

@router.post("/style-mix/classify")
async def classify_style_mix(user: dict = Depends(_dep_user)):
    """
    Classify SKU styles into Core / Fashion / Test.
    Core  = avg >5 units/week, present >80% of weeks
    Fashion = peak-to-avg ratio >3x, lifecycle <26 weeks
    Test  = <8 weeks old OR <2 units/week avg
    """
    from domains.buy_planning import StyleMixRepository, StyleMixService
    svc = StyleMixService(StyleMixRepository(get_db()))
    return await svc.classify(
        tenant_id=user.get("tenant_id", ""),
        user_email=user.get("email", "system"),
    )


@router.get("/style-mix")
async def get_style_mix(user: dict = Depends(_dep_user)):
    """Get current style mix classification for all SKUs."""
    from domains.buy_planning import StyleMixRepository, StyleMixService
    svc = StyleMixService(StyleMixRepository(get_db()))
    return await svc.list_classifications()


# ─────────────── Assortment Matrix (Wedge × Mix) ───────────────

@router.get("/assortment-matrix")
async def get_assortment_matrix(user: dict = Depends(_dep_user)):
    """
    Return the Wedge × Style Mix assortment matrix:
    A-Stores: Core + Fashion + Test (Full assortment)
    B-Stores: Core + Fashion (Standard assortment)
    C-Stores: Core only (Efficiency assortment)
    """
    from domains.buy_planning import AssortmentMatrixRepository, AssortmentMatrixService
    svc = AssortmentMatrixService(AssortmentMatrixRepository(get_db()))
    return await svc.get_matrix(user.get("tenant_id", ""))


# ─────────────── Piece-Level Attribution Matrix ───────────────

@router.get("/attribution/matrix")
async def get_attribution_matrix(user: dict = Depends(_dep_user)):
    """
    Return SKU → Store cluster attribution.
    Core → ALL stores (A+B+C)
    Fashion → A + B only
    Test → A only
    """
    from domains.buy_planning import AttributionRepository, AttributionService
    svc = AttributionService(AttributionRepository(get_db()))
    return await svc.get_matrix(user.get("tenant_id", ""))
