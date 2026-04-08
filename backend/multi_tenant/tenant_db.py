"""
MongoDB Multi-Tenant Database Utilities.
Each tenant gets its own MongoDB database (tenant_{tenant_id}).
Shared collections (tenants registry, users) live in a shared DB.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from contextvars import ContextVar
from typing import Optional, Dict
from dataclasses import dataclass
import os
import logging

logger = logging.getLogger(__name__)

# Context variable holding the current tenant for this request
tenant_context: ContextVar[Optional["TenantContext"]] = ContextVar("tenant_context", default=None)

_mongo_client: Optional[AsyncIOMotorClient] = None
_tenant_cache: Dict[str, dict] = {}
_resolved_shared_db_name: Optional[str] = None


def _extract_db_from_mongo_url() -> Optional[str]:
    """Extract database name from MONGO_URL connection string path component."""
    try:
        url = os.environ.get("MONGO_URL", "")
        if not url:
            return None
        from urllib.parse import urlparse
        parsed = urlparse(url)
        db = parsed.path.strip("/")
        if db and "?" not in db:
            return db
        if "?" in db:
            return db.split("?")[0]
    except Exception:
        pass
    return None


def get_shared_db_name() -> str:
    """Lazily resolve the shared DB name at first call, not at import time.
    Fallback chain: DB_NAME env (Emergent-authorized) > SHARED_DB_NAME env > MONGO_URL path.
    Never falls back to hardcoded 'merch_shared' — if nothing is configured, fails fast.
    """
    global _resolved_shared_db_name
    if _resolved_shared_db_name is not None:
        return _resolved_shared_db_name

    # DB_NAME is the primary source — Emergent platform guarantees this is the authorized database
    name = os.environ.get("DB_NAME")
    if not name:
        name = os.environ.get("SHARED_DB_NAME")
    if not name:
        name = _extract_db_from_mongo_url()
    if not name:
        logger.error("FATAL: No database name configured. Set DB_NAME environment variable.")
        raise RuntimeError("No database name configured. Set DB_NAME environment variable.")

    _resolved_shared_db_name = name
    logger.info(f"Shared DB resolved to: {name}")
    return name


@dataclass
class TenantContext:
    tenant_id: str
    db_name: str
    company_name: str
    plan_type: str


def get_mongo_client() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return _mongo_client


def get_shared_db() -> AsyncIOMotorDatabase:
    return get_mongo_client()[get_shared_db_name()]


def get_tenant_db(tenant_id: Optional[str] = None) -> AsyncIOMotorDatabase:
    if tenant_id:
        return get_mongo_client()[f"tenant_{tenant_id}"]
    ctx = tenant_context.get()
    if ctx is None:
        raise RuntimeError("No tenant context — use default tenant or set middleware")
    return get_mongo_client()[ctx.db_name]


def get_current_tenant() -> Optional[TenantContext]:
    return tenant_context.get()


async def resolve_tenant(tenant_id: str) -> Optional[dict]:
    """Look up tenant from shared registry, with in-memory cache."""
    if tenant_id in _tenant_cache:
        return _tenant_cache[tenant_id]
    shared = get_shared_db()
    doc = await shared.tenants.find_one({"tenant_id": tenant_id, "status": "active"}, {"_id": 0})
    if doc:
        _tenant_cache[tenant_id] = doc
    return doc


async def resolve_tenant_by_subdomain(subdomain: str) -> Optional[dict]:
    shared = get_shared_db()
    doc = await shared.tenants.find_one({"subdomain": subdomain, "status": "active"}, {"_id": 0})
    if doc:
        _tenant_cache[doc["tenant_id"]] = doc
    return doc


def clear_tenant_cache(tenant_id: str = None):
    if tenant_id:
        _tenant_cache.pop(tenant_id, None)
    else:
        _tenant_cache.clear()


async def ensure_shared_indexes():
    """Create indexes on shared collections — call once at startup."""
    shared = get_shared_db()
    try:
        await shared.tenants.create_index("tenant_id", unique=True)
        await shared.tenants.create_index("subdomain", unique=True)
        await shared.users.create_index("email", unique=True)
        await shared.user_tenants.create_index([("user_id", 1), ("tenant_id", 1)], unique=True)
        logger.info("Shared DB indexes ensured")
    except Exception as e:
        logger.warning(f"Could not create shared DB indexes (may lack permissions): {e}")
        logger.info("Continuing startup without index creation — indexes may already exist")
