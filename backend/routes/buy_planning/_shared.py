"""
Shared infrastructure for the buy_planning route package.

Every sub-module in this package imports `router` from here and decorates it
with its endpoints. The `router` is created once with the `/buy-planning`
prefix and re-exported by `__init__.py`.

`init_buy_planning()` is called once at app startup by server.py to wire the
MongoDB factory + current-user dependency — the values are captured as module
globals so that every sub-module sees them through the `_db_func()` and
`_dep_user()` helpers.
"""

from fastapi import APIRouter, Request

# Single router shared across all sub-modules — each sub-module registers its
# routes by importing this object and decorating its handlers with it.
router = APIRouter(prefix="/buy-planning", tags=["buy-planning"])

# Wired at startup by init_buy_planning() from server.py.
_db_func = None
_get_current_user = None


def init_buy_planning(get_db_func, get_current_user_func):
    """Called once at app startup to wire deps into module globals."""
    global _db_func, _get_current_user
    _db_func = get_db_func
    _get_current_user = get_current_user_func


async def _dep_user(request: Request) -> dict:
    """FastAPI dependency: resolve the current user via the wired factory."""
    return await _get_current_user(request)


def _tenant_match(tenant_id: str) -> dict:
    """
    Match documents with or without tenant_id (handles pre-multi-tenant seed data).

    Exported for server.py which reaches into this helper for one legacy call.
    """
    return {"$or": [{"tenant_id": tenant_id}, {"tenant_id": {"$exists": False}}]}


def get_db():
    """Resolve the shared Motor DB (never store the return value across requests)."""
    return _db_func()
