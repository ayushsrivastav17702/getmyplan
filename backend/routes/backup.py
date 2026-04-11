"""
Tenant Backup & Restore API.
Stores compressed snapshots in MongoDB `backups` collection.
Supports downloadable ZIP export, server-side restore (overwrite / merge).
Retains last 5 backups per tenant.
"""
import gzip
import json
import io
import zipfile
import logging
from datetime import datetime, timezone
from typing import Optional
from bson import Binary, ObjectId
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from multi_tenant.auth import get_current_user
from multi_tenant.tenant_db import get_shared_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backup", tags=["Backup & Restore"])

MAX_BACKUPS_PER_TENANT = 5

# ── Collection categories ──

# Collections with a `tenant_id` field → filter by tenant
TENANT_FILTERED = [
    "api_keys", "audit_logs", "cogs", "daily_sales", "invitations",
    "ist_history", "onboarding_status", "open_orders", "permission_overrides",
    "planogram", "store_inventory", "style_master", "user_tenants",
]

# Shared / config collections → backup all docs
SHARED_COLLECTIONS = [
    "analysis_config", "buy_plan_history", "categories", "category_ideal_doh",
    "chat_history", "demand_plans", "filter_presets", "forecast_snapshots",
    "notifications", "ob_categories", "ob_marketplaces", "ob_stores",
    "reorder_overrides", "reorder_recommendations", "replenishment_orders",
    "replenishment_runs", "replenishment_schedule", "role_permissions",
    "sftp_config", "sftp_logs", "sku_master", "store_classes", "store_master",
    "upload_history", "uploaded_files", "ist_transfers",
    "warehouse_adjustments", "warehouse_config", "warehouse_inventory",
    "warehouse_master", "warehouse_movements", "warehouse_reconciliations",
    "warehouse_transfers",
]

# Excluded from backup (system / temporary)
EXCLUDED = {"mfa_sessions", "sessions", "backups", "tenants", "roles", "permissions", "demo_requests"}


def _serialize_doc(doc: dict) -> dict:
    """Convert ObjectId and other non-JSON types for serialization."""
    out = {}
    for k, v in doc.items():
        if k == "_id":
            continue  # exclude Mongo _id
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, bytes):
            continue  # skip binary blobs
        else:
            out[k] = v
    return out


# ── Models ──

class BackupCreateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class RestoreRequest(BaseModel):
    mode: str = Field(..., pattern="^(overwrite|merge)$")


# ── Endpoints ──

@router.post("/create")
async def create_backup(body: BackupCreateRequest = None, user: dict = Depends(get_current_user)):
    """Create a compressed backup of all tenant data."""
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    shared = get_shared_db()
    backup_data = {}
    total_docs = 0

    # 1. Tenant-filtered collections
    for col_name in TENANT_FILTERED:
        col = shared[col_name]
        docs = []
        async for doc in col.find({"tenant_id": tenant_id}):
            docs.append(_serialize_doc(doc))
        backup_data[col_name] = docs
        total_docs += len(docs)

    # 2. Users — map via user_tenants
    tenant_emails = set()
    for ut in backup_data.get("user_tenants", []):
        if ut.get("email"):
            tenant_emails.add(ut["email"])

    user_docs = []
    if tenant_emails:
        async for doc in shared.users.find({"email": {"$in": list(tenant_emails)}}):
            serialized = _serialize_doc(doc)
            # Remove sensitive fields from backup
            serialized.pop("hashed_password", None)
            serialized.pop("totp_secret", None)
            serialized.pop("reset_token", None)
            serialized.pop("reset_token_expires", None)
            user_docs.append(serialized)
    backup_data["users"] = user_docs
    total_docs += len(user_docs)

    # 3. Tenant document (reference only)
    tenant_doc = await shared.tenants.find_one({"tenant_id": tenant_id})
    if tenant_doc:
        backup_data["_tenant_info"] = _serialize_doc(tenant_doc)

    # 4. Shared collections
    for col_name in SHARED_COLLECTIONS:
        col = shared[col_name]
        docs = []
        async for doc in col.find():
            docs.append(_serialize_doc(doc))
        backup_data[col_name] = docs
        total_docs += len(docs)

    # Compress
    json_bytes = json.dumps(backup_data, default=str).encode("utf-8")
    compressed = gzip.compress(json_bytes)
    size_mb = round(len(compressed) / (1024 * 1024), 2)

    # Count collections with data
    collections_count = sum(1 for k, v in backup_data.items() if isinstance(v, list) and len(v) > 0)

    now = datetime.now(timezone.utc)
    name = (body.name if body and body.name else None) or f"Backup {now.strftime('%d %b %Y, %H:%M')}"
    description = (body.description if body and body.description else None) or ""

    backup_record = {
        "tenant_id": tenant_id,
        "name": name,
        "description": description,
        "created_by": user.get("email", "unknown"),
        "created_at": now.isoformat(),
        "total_docs": total_docs,
        "collections_count": collections_count,
        "size_mb": size_mb,
        "compressed_data": Binary(compressed),
    }

    result = await shared.backups.insert_one(backup_record)
    backup_id = str(result.inserted_id)

    # Auto-cleanup: keep only last MAX_BACKUPS_PER_TENANT
    all_backups = await shared.backups.find(
        {"tenant_id": tenant_id}, {"_id": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(100)

    if len(all_backups) > MAX_BACKUPS_PER_TENANT:
        to_delete = [b["_id"] for b in all_backups[MAX_BACKUPS_PER_TENANT:]]
        await shared.backups.delete_many({"_id": {"$in": to_delete}})

    logger.info(f"Backup created: {backup_id} for tenant {tenant_id} ({total_docs} docs, {size_mb}MB)")
    return {
        "backup_id": backup_id,
        "name": name,
        "total_docs": total_docs,
        "collections_count": collections_count,
        "size_mb": size_mb,
        "created_at": now.isoformat(),
    }


@router.get("/list")
async def list_backups(user: dict = Depends(get_current_user)):
    """List all backups for the current tenant."""
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    shared = get_shared_db()
    backups = []
    async for doc in shared.backups.find(
        {"tenant_id": tenant_id},
        {"compressed_data": 0},
    ).sort("created_at", -1):
        backups.append({
            "backup_id": str(doc["_id"]),
            "name": doc.get("name", "Unnamed"),
            "description": doc.get("description", ""),
            "created_by": doc.get("created_by", ""),
            "created_at": doc.get("created_at", ""),
            "total_docs": doc.get("total_docs", 0),
            "collections_count": doc.get("collections_count", 0),
            "size_mb": doc.get("size_mb", 0),
        })
    return {"backups": backups, "max_backups": MAX_BACKUPS_PER_TENANT}


@router.get("/{backup_id}/download")
async def download_backup(backup_id: str, user: dict = Depends(get_current_user)):
    """Download backup as a ZIP file containing JSON files per collection."""
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    shared = get_shared_db()
    try:
        doc = await shared.backups.find_one({"_id": ObjectId(backup_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid backup ID")

    if not doc:
        raise HTTPException(status_code=404, detail="Backup not found")

    # Decompress
    compressed = doc["compressed_data"]
    json_bytes = gzip.decompress(bytes(compressed))
    data = json.loads(json_bytes)

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write metadata
        meta = {
            "backup_id": str(doc["_id"]),
            "tenant_id": tenant_id,
            "name": doc.get("name", ""),
            "created_by": doc.get("created_by", ""),
            "created_at": doc.get("created_at", ""),
            "total_docs": doc.get("total_docs", 0),
            "collections_count": doc.get("collections_count", 0),
        }
        zf.writestr("_metadata.json", json.dumps(meta, indent=2))

        # Write each collection
        for col_name, docs_list in data.items():
            if col_name == "_tenant_info":
                zf.writestr("_tenant_info.json", json.dumps(docs_list, indent=2, default=str))
            else:
                zf.writestr(f"{col_name}.json", json.dumps(docs_list, indent=2, default=str))

    zip_buffer.seek(0)
    safe_name = doc.get("name", "backup").replace(" ", "_").replace(",", "")
    filename = f"{tenant_id}_{safe_name}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{backup_id}/restore")
async def restore_backup(backup_id: str, body: RestoreRequest, user: dict = Depends(get_current_user)):
    """Restore from a backup snapshot.
    mode='overwrite': Drop existing data and replace with backup data.
    mode='merge': Insert backup data alongside existing data (skip duplicates).
    """
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    shared = get_shared_db()
    try:
        doc = await shared.backups.find_one({"_id": ObjectId(backup_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid backup ID")

    if not doc:
        raise HTTPException(status_code=404, detail="Backup not found")

    # Decompress
    compressed = doc["compressed_data"]
    json_bytes = gzip.decompress(bytes(compressed))
    data = json.loads(json_bytes)

    mode = body.mode
    restored_collections = []
    total_restored = 0
    errors = []

    for col_name, docs_list in data.items():
        if col_name in ("_tenant_info",):
            continue  # Skip reference-only data
        if not isinstance(docs_list, list) or len(docs_list) == 0:
            continue
        if col_name == "users":
            # Users are read-only in restore to prevent credential issues
            continue

        col = shared[col_name]

        try:
            if mode == "overwrite":
                # For tenant-filtered collections, only delete tenant's data
                if col_name in TENANT_FILTERED:
                    await col.delete_many({"tenant_id": tenant_id})
                else:
                    await col.delete_many({})
                if docs_list:
                    await col.insert_many(docs_list)

            elif mode == "merge":
                # Insert one by one, skip duplicates
                inserted = 0
                for d in docs_list:
                    try:
                        await col.insert_one(d)
                        inserted += 1
                    except Exception:
                        pass  # Skip duplicates / conflicts
                docs_list = [None] * inserted  # for counting

            restored_collections.append(col_name)
            total_restored += len(docs_list)

        except Exception as e:
            logger.error(f"Restore error on {col_name}: {e}")
            errors.append({"collection": col_name, "error": str(e)})

    logger.info(f"Restore complete: {backup_id} for tenant {tenant_id} mode={mode} "
                f"({total_restored} docs in {len(restored_collections)} collections)")

    return {
        "success": True,
        "mode": mode,
        "restored_collections": len(restored_collections),
        "total_docs_restored": total_restored,
        "collections": restored_collections,
        "errors": errors,
    }


@router.delete("/{backup_id}")
async def delete_backup(backup_id: str, user: dict = Depends(get_current_user)):
    """Delete a specific backup."""
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    shared = get_shared_db()
    try:
        result = await shared.backups.delete_one({"_id": ObjectId(backup_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid backup ID")

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Backup not found")

    return {"success": True, "message": "Backup deleted"}
