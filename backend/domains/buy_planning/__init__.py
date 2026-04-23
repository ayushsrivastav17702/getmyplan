"""
Buy Planning bounded context.

# Architecture
```
routes/buy_planning.py      ← thin HTTP adapters (Pydantic in/out, auth, HTTPException)
    ↓ imports
domains/buy_planning/       ← business logic (this package)
    ├── schemas.py          ← Pydantic request/response models
    ├── display_minimums.py ← vertical slice (repo + service)
    ├── style_mix.py        ← vertical slice (repo + service)
    ├── store_wedge.py      ← vertical slice (repo + service)
    └── ...                 ← future slices
    ↓ imports
core/buy_formula.py         ← pure math, no DB, no HTTP
```

# The strangler-fig migration pattern
The monolithic `routes/buy_planning.py` is being broken down one vertical slice
at a time. Each slice follows the same 3-layer shape:

  1. `<feature>.Repository`  — pure Motor/MongoDB calls, returns plain dicts
  2. `<feature>.Service`     — business logic, composes repo + core utils
  3. Thin route adapter      — stays in `routes/buy_planning.py`, delegates here

# How to extract the next slice
1. Pick a set of related endpoints (e.g. all `/style-mix/*`).
2. Create `domains/buy_planning/<slice>.py` with Repository + Service.
3. Lift logic out of `routes/buy_planning.py` — repo for DB, service for compute.
4. Replace the route body with a delegation:
       svc = XxxService(XxxRepository(_db_func()))
       return await svc.do_thing(...)
5. Run the full test suite + curl smoke each endpoint.
6. Commit.

# Non-negotiables
- `tenant_id` must appear in every Mongo query (enforced via repository layer).
- No direct Mongo access from routes — always through a repository.
- No Pydantic models in repositories — they return plain dicts.
- No HTTP types (HTTPException) leak into services — raise domain errors instead.
"""

from .display_minimums import (
    DisplayMinimumsRepository,
    DisplayMinimumsService,
    NotFoundError,
)
from .style_mix import (
    StyleMixRepository,
    StyleMixService,
    classify_style,
    compute_style_stats,
    ValidationError as StyleMixValidationError,
    NotFoundError as StyleMixNotFoundError,
)
from .store_wedge import (
    StoreWedgeRepository,
    StoreWedgeService,
    classify_wedge_by_cumulative_revenue,
    classify_stores_by_revenue,
    tier_to_wedge,
    ValidationError as StoreWedgeValidationError,
    NotFoundError as StoreWedgeNotFoundError,
    NoDataError as StoreWedgeNoDataError,
)
from .attribution import (
    AttributionRepository,
    AttributionService,
    WEDGE_RULES,
    eligible_wedges_for_mix,
    compute_wedge_allocation,
    build_attribution_row,
)
from .dna_tags import (
    DnaTagsRepository,
    DnaTagsService,
    classify_flow_rank,
    classify_lifecycle,
    compute_expected_weeks,
    NotFoundError as DnaTagsNotFoundError,
)
from .audit_log import (
    AuditLogRepository,
    AuditLogService,
)
from .exclusions import (
    ExclusionsRepository,
    ExclusionsService,
    NotFoundError as ExclusionsNotFoundError,
)
from .promotions import (
    PromotionsRepository,
    PromotionsService,
    NotFoundError as PromotionsNotFoundError,
    ValidationError as PromotionsValidationError,
)
from .orders import (
    OrdersRepository,
    OrdersService,
    PO_STATUSES,
    group_items_by_category,
    build_po_number,
    validate_phase_inputs,
    build_phase_shipments,
    NotFoundError as OrdersNotFoundError,
    ValidationError as OrdersValidationError,
)
from .sell_through import (
    SellThroughRepository,
    SellThroughService,
    DEFAULT_SELL_THROUGH,
    ValidationError as SellThroughValidationError,
)
from .store_attributes import (
    StoreAttributesRepository,
    StoreAttributesService,
    validate_and_build_updates,
    VALID_FORMATS,
    VALID_TIERS,
    VALID_REGIONS,
    NotFoundError as StoreAttrsNotFoundError,
    ValidationError as StoreAttrsValidationError,
)
from .inventory import (
    InventoryRepository,
    InventoryService,
    MAX_BULK_RECORDS,
    ValidationError as InventoryValidationError,
)
from .safety_stock import (
    SafetyStockRepository,
    SafetyStockService,
    DEFAULT_SAFETY_CONFIG,
    Z_SCORES,
    z_score_for,
    compute_safety_stock,
    validate_config as validate_safety_config,
    ValidationError as SafetyStockValidationError,
)
from .binding_analytics import (
    BindingAnalyticsRepository,
    BindingAnalyticsService,
    compute_binding_breakdown,
    aggregate_worst_categories,
    build_trend_series,
    ForbiddenError as BindingAnalyticsForbiddenError,
)
from .buy_plans import (
    BuyPlansRepository,
    BuyPlansService,
    PLAN_STATUS_CHAIN,
    APPROVAL_ACTIONS,
    APPROVAL_ROLES,
    NotFoundError as BuyPlansNotFoundError,
    ValidationError as BuyPlansValidationError,
    ForbiddenError as BuyPlansForbiddenError,
)
from .buy_formula import (
    BuyFormulaRepository,
    BuyFormulaService,
    compute_promo_lifts,
    best_lift_for,
    compute_demand_buy,
    compute_display_qty,
    compute_safety_qty_statistical,
    binding_factor,
    build_sku_row,
)
from .assortment_matrix import (
    AssortmentMatrixRepository,
    AssortmentMatrixService,
    mixes_eligible_for_wedge,
    build_matrix,
)

__all__ = [
    "DisplayMinimumsRepository",
    "DisplayMinimumsService",
    "NotFoundError",
    "StyleMixRepository",
    "StyleMixService",
    "classify_style",
    "compute_style_stats",
    "StyleMixValidationError",
    "StyleMixNotFoundError",
    "StoreWedgeRepository",
    "StoreWedgeService",
    "classify_wedge_by_cumulative_revenue",
    "classify_stores_by_revenue",
    "tier_to_wedge",
    "StoreWedgeValidationError",
    "StoreWedgeNotFoundError",
    "StoreWedgeNoDataError",
    "AttributionRepository",
    "AttributionService",
    "WEDGE_RULES",
    "eligible_wedges_for_mix",
    "compute_wedge_allocation",
    "build_attribution_row",
    "DnaTagsRepository",
    "DnaTagsService",
    "classify_flow_rank",
    "classify_lifecycle",
    "compute_expected_weeks",
    "DnaTagsNotFoundError",
    "AuditLogRepository",
    "AuditLogService",
    "ExclusionsRepository",
    "ExclusionsService",
    "ExclusionsNotFoundError",
    "PromotionsRepository",
    "PromotionsService",
    "PromotionsNotFoundError",
    "PromotionsValidationError",
    "OrdersRepository",
    "OrdersService",
    "PO_STATUSES",
    "group_items_by_category",
    "build_po_number",
    "validate_phase_inputs",
    "build_phase_shipments",
    "OrdersNotFoundError",
    "OrdersValidationError",
    "SellThroughRepository",
    "SellThroughService",
    "DEFAULT_SELL_THROUGH",
    "SellThroughValidationError",
    "StoreAttributesRepository",
    "StoreAttributesService",
    "validate_and_build_updates",
    "VALID_FORMATS",
    "VALID_TIERS",
    "VALID_REGIONS",
    "StoreAttrsNotFoundError",
    "StoreAttrsValidationError",
    "InventoryRepository",
    "InventoryService",
    "MAX_BULK_RECORDS",
    "InventoryValidationError",
    "SafetyStockRepository",
    "SafetyStockService",
    "DEFAULT_SAFETY_CONFIG",
    "Z_SCORES",
    "z_score_for",
    "compute_safety_stock",
    "validate_safety_config",
    "SafetyStockValidationError",
    "BindingAnalyticsRepository",
    "BindingAnalyticsService",
    "compute_binding_breakdown",
    "aggregate_worst_categories",
    "build_trend_series",
    "BindingAnalyticsForbiddenError",
    "BuyPlansRepository",
    "BuyPlansService",
    "PLAN_STATUS_CHAIN",
    "APPROVAL_ACTIONS",
    "APPROVAL_ROLES",
    "BuyPlansNotFoundError",
    "BuyPlansValidationError",
    "BuyPlansForbiddenError",
    "BuyFormulaRepository",
    "BuyFormulaService",
    "compute_promo_lifts",
    "best_lift_for",
    "compute_demand_buy",
    "compute_display_qty",
    "compute_safety_qty_statistical",
    "binding_factor",
    "build_sku_row",
    "AssortmentMatrixRepository",
    "AssortmentMatrixService",
    "mixes_eligible_for_wedge",
    "build_matrix",
]
