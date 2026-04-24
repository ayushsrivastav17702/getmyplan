"""
Buy Planning route package — Interactive SKU × store piece-level pipeline.

## What this package is
FastAPI route adapters for the piece-level (SKU × store-wedge) interactive
buy-planning workflow. Every endpoint here delegates to a service in
`/app/backend/domains/buy_planning/` (Repository + Service + pure helpers).
Endpoints live under `/api/buy-planning/*` (with an "-ing").

## How it differs from `routes/buy_plan.py`
`/app/backend/routes/buy_plan.py` (singular, no "-ing") is a completely
different workflow: bulk Excel-driven top-down category planning for
merchandisers who plan in spreadsheets. Its endpoints live under
`/api/buy-plan/*`.

Both workflows ship side-by-side intentionally. Do NOT merge them.

## Architecture
```
server.py
    └─ from routes.buy_planning import router, init_buy_planning
         ↓
       /app/backend/routes/buy_planning/  ← this package
         ├─ _shared.py              ← singleton router + deps + init (48 LOC)
         ├─ classification.py       ← store-wedge, style-mix, assortment, attribution
         ├─ config.py               ← display-minimums, sell-through
         ├─ buy_formula.py          ← calculate + CSV export
         ├─ dna_tags.py             ← DNA tagging (4 endpoints)
         ├─ overrides_audit.py      ← manual overrides + audit log
         ├─ buy_plans.py            ← plan CRUD + approval workflow
         ├─ stores_and_exclusions.py← store attrs + exclusion list
         ├─ inventory_safety.py     ← inventory ingestion + safety-stock
         ├─ orders.py               ← PO consolidation + phased replenishment
         ├─ promotions.py           ← promo calendar + lift factors
         └─ analytics.py            ← binding-factor analytics
             ↓
       /app/backend/domains/buy_planning/   ← business logic (Repos + Services)
```

## How route registration works
All sub-modules import the SAME `router` instance from `_shared.py` and
decorate their handlers with it. Importing a sub-module below triggers those
decorators — that's why the imports are "unused" by the linter but required
at package-init time.

## DO NOT
- Do NOT merge files in this package with `routes/buy_plan.py` — they are
  different pipelines with different URL contracts.
- Do NOT put business logic in the sub-modules — keep them as thin adapters
  that delegate to `domains/buy_planning/*`.
"""

# Core re-exports (used by server.py).
from ._shared import router, init_buy_planning, _tenant_match  # noqa: F401

# Import sub-modules to register routes on the shared router.
# The order doesn't affect URL routing but is kept stable for readable logs.
from . import classification        # noqa: F401
from . import config                # noqa: F401
from . import buy_formula           # noqa: F401
from . import dna_tags              # noqa: F401
from . import overrides_audit       # noqa: F401
from . import buy_plans             # noqa: F401
from . import stores_and_exclusions # noqa: F401
from . import inventory_safety      # noqa: F401
from . import orders                # noqa: F401
from . import promotions            # noqa: F401
from . import analytics             # noqa: F401

__all__ = ["router", "init_buy_planning", "_tenant_match"]
