"""
Redis Cache Service — Module-specific TTL with invalidation on uploads.
"""
import json
import os
import logging
from datetime import date
from typing import Any, Callable, Optional

import redis

logger = logging.getLogger("cache")

# ─── TTL per module (seconds) ───
CACHE_TTL = {
    # Critical — inventory-dependent (1 hour)
    "doh_heatmap": 3600,
    "stockout": 3600,
    "replenishment": 3600,
    "planogram_fill": 3600,
    # Daily aggregates (6 hours)
    "executive_kpis": 21600,
    "executive_dashboard": 21600,
    "executive_trend": 21600,
    "bi_dashboard": 21600,
    "gap_ros": 21600,
    "gap_size": 21600,
    "gap_noos": 21600,
    "gap_data_status": 21600,
    # Slow-changing (24 hours)
    "topseller": 86400,
    # Expensive ML (7 days)
    "ai_forecast": 604800,
}

# ─── Upload → cache invalidation map ───
INVALIDATION_MAP = {
    "daily_sales": ["executive_kpis", "executive_dashboard", "executive_trend",
                     "bi_dashboard", "gap_ros", "gap_size", "gap_noos",
                     "gap_data_status", "topseller"],
    "store_inventory": ["doh_heatmap", "stockout", "planogram_fill",
                        "replenishment", "gap_data_status"],
    "warehouse_inventory": ["doh_heatmap", "replenishment", "gap_data_status"],
    "planogram": ["planogram_fill", "replenishment", "gap_data_status"],
    "cogs": ["executive_kpis", "executive_dashboard"],
    "open_orders": ["replenishment"],
    "sku_master": ["gap_data_status", "topseller"],
    "style_master": ["gap_data_status", "bi_dashboard"],
    "store_master": ["gap_data_status", "bi_dashboard"],
}


def _build_redis_client() -> Optional[redis.Redis]:
    """Build Redis client from env vars. Returns None if not configured."""
    host = os.environ.get("REDIS_HOST", "")
    if not host:
        logger.info("REDIS_HOST not set — caching disabled")
        return None
    try:
        client = redis.Redis(
            host=host,
            port=int(os.environ.get("REDIS_PORT", 6379)),
            password=os.environ.get("REDIS_PASSWORD", ""),
            decode_responses=True,
            ssl=False,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        client.ping()
        logger.info("Redis connected: %s:%s", host, os.environ.get("REDIS_PORT", 6379))
        return client
    except Exception as e:
        logger.warning("Redis connection failed (caching disabled): %s", e)
        return None


# Singleton
_redis: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    global _redis
    if _redis is None:
        _redis = _build_redis_client()
    return _redis


def cache_key(module: str, tenant_id: str, extra: str = "") -> str:
    """Build a namespaced cache key."""
    day = date.today().isoformat()
    parts = [module, tenant_id, day]
    if extra:
        parts.append(extra)
    return ":".join(parts)


async def cached(module: str, tenant_id: str, compute_fn: Callable, extra: str = "") -> Any:
    """Get from Redis or compute + store with module-specific TTL."""
    r = get_redis()
    key = cache_key(module, tenant_id, extra)

    if r:
        try:
            hit = r.get(key)
            if hit is not None:
                logger.debug("CACHE HIT: %s", key)
                return json.loads(hit)
        except Exception as e:
            logger.warning("Redis GET error (computing fresh): %s", e)

    # Compute fresh
    result = await compute_fn()

    if r and result is not None:
        ttl = CACHE_TTL.get(module, 3600)
        try:
            r.setex(key, ttl, json.dumps(result, default=str))
            logger.debug("CACHE SET: %s (TTL=%ds)", key, ttl)
        except Exception as e:
            logger.warning("Redis SET error: %s", e)

    return result


def invalidate_for_upload(tenant_id: str, upload_type: str):
    """Invalidate all cache keys affected by a specific upload type."""
    r = get_redis()
    if not r:
        return
    modules = INVALIDATION_MAP.get(upload_type, [])
    if not modules:
        return
    deleted = 0
    for mod in modules:
        pattern = f"{mod}:{tenant_id}:*"
        try:
            keys = r.keys(pattern)
            if keys:
                r.delete(*keys)
                deleted += len(keys)
        except Exception as e:
            logger.warning("Redis invalidation error for %s: %s", pattern, e)
    if deleted:
        logger.info("CACHE INVALIDATED: %d keys for tenant=%s upload=%s", deleted, tenant_id, upload_type)


def invalidate_tenant(tenant_id: str):
    """Invalidate ALL cache keys for a tenant (e.g., after config change)."""
    r = get_redis()
    if not r:
        return
    try:
        keys = r.keys(f"*:{tenant_id}:*")
        if keys:
            r.delete(*keys)
            logger.info("CACHE FULL INVALIDATE: %d keys for tenant=%s", len(keys), tenant_id)
    except Exception as e:
        logger.warning("Redis full invalidation error: %s", e)
