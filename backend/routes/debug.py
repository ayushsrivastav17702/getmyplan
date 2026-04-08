"""
Temporary debug endpoints for production MongoDB configuration diagnostics.
REMOVE THIS FILE after debugging is complete.
"""
from fastapi import APIRouter, Request
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/config")
async def debug_config():
    """Shows environment variable resolution for database configuration."""
    mongo_url = os.getenv("MONGO_URL", "")
    return {
        "environment": {
            "SHARED_DB_NAME": os.getenv("SHARED_DB_NAME", "NOT_SET"),
            "DB_NAME": os.getenv("DB_NAME", "NOT_SET"),
            "MONGO_URL_prefix": (mongo_url[:30] + "...") if mongo_url else "NOT_SET",
            "SHARED_DB_NAME_RAW": repr(os.getenv("SHARED_DB_NAME")),
            "IS_MERCH_SHARED": os.getenv("SHARED_DB_NAME") == "merch_shared",
        },
        "resolved": {
            "get_shared_db_name_result": _get_resolved_name(),
        }
    }


@router.get("/database")
async def debug_database():
    """Check actual database being used and connection status."""
    from multi_tenant.tenant_db import get_shared_db, get_mongo_client
    try:
        shared = get_shared_db()
        db_name = shared.name

        # Try listing collections to verify read access
        try:
            collections = await shared.list_collection_names()
            read_access = True
        except Exception as e:
            collections = []
            read_access = False

        # Try connectionStatus command
        conn_status = {}
        try:
            client = get_mongo_client()
            status = await client.admin.command("connectionStatus")
            conn_status = status.get("authInfo", {})
        except Exception as e:
            conn_status = {"error": str(e)}

        return {
            "current_shared_db_name": db_name,
            "read_access": read_access,
            "collections_found": collections,
            "connection_status": conn_status,
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/db-permission-test")
async def debug_db_permission_test():
    """Test read/write access to the resolved shared DB and merch_shared separately."""
    from multi_tenant.tenant_db import get_mongo_client, get_shared_db_name

    client = get_mongo_client()
    resolved_name = get_shared_db_name()
    results = {}

    # Test resolved DB
    for db_name in [resolved_name, "merch_shared"]:
        test_db = client[db_name]
        entry = {"db_name": db_name}
        try:
            count = await test_db.users.count_documents({})
            entry["read_access"] = True
            entry["users_count"] = count
        except Exception as e:
            entry["read_access"] = False
            entry["error"] = str(e)
        results[db_name] = entry

    return {
        "resolved_shared_db": resolved_name,
        "permission_tests": results,
    }


def _get_resolved_name():
    try:
        from multi_tenant.tenant_db import get_shared_db_name
        return get_shared_db_name()
    except Exception as e:
        return f"ERROR: {e}"
