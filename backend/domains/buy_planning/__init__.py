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
]
