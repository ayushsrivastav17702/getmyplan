"""
Analytics route package.

Sibling to `routes/buy_planning/*` but on a separate URL prefix
(`/analytics/...`). Today it hosts just `attribute_grouping`; future verticals
(markdown optimization, size curves, etc.) will join this package.

Wired in server.py via `init_analytics(get_db, get_current_user)` and
`api_router.include_router(analytics_router)`.
"""

from fastapi import APIRouter, Request

# Single router shared across sub-modules.
router = APIRouter(prefix="/analytics", tags=["analytics"])

# Wired at startup by init_analytics().
_db_func = None
_get_current_user = None


def init_analytics(get_db_func, get_current_user_func):
    """Called once at app startup to wire deps into module globals."""
    global _db_func, _get_current_user
    _db_func = get_db_func
    _get_current_user = get_current_user_func


async def _dep_user(request: Request) -> dict:
    return await _get_current_user(request)


def get_db():
    return _db_func()


# Import sub-modules so their route decorators execute against `router`.
# Must come after the globals are declared.
from . import attribute_grouping  # noqa: E402, F401
from . import size_curve  # noqa: E402, F401
