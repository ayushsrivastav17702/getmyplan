"""
SFTP Auto-Scheduled Uploads + Chunked Upload with Async Processing.
"""
import os
import io
import uuid
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from multi_tenant.auth import get_current_user
from multi_tenant.tenant_db import get_shared_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["Data Operations"])

# In-memory chunk storage and processing status
_chunk_storage = {}  # upload_id -> { chunks: {}, metadata: {} }
_processing_status = {}  # upload_id -> { status, progress, ... }

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── SFTP Auto-Schedule Models ──

class SFTPScheduleConfig(BaseModel):
    enabled: bool = True
    frequency: str = Field("daily", pattern="^(daily|weekly|monthly)$")
    day_of_week: Optional[int] = Field(None, ge=0, le=6)  # 0=Monday
    hour: int = Field(2, ge=0, le=23)  # Default 2 AM
    file_types: list = Field(default=["daily_sales", "store_inventory"])
    destination_path: str = Field(default="/exports")


# ── SFTP Auto-Schedule Endpoints ──

@router.get("/sftp-schedule")
async def get_sftp_schedule(user: dict = Depends(get_current_user)):
    """Get current SFTP auto-upload schedule configuration."""
    shared = get_shared_db()
    tenant_id = user.get("tenant_id")
    config = await shared.sftp_schedules.find_one(
        {"tenant_id": tenant_id}, {"_id": 0}
    )
    if not config:
        config = {
            "tenant_id": tenant_id,
            "enabled": False,
            "frequency": "daily",
            "hour": 2,
            "file_types": ["daily_sales", "store_inventory"],
            "destination_path": "/exports",
            "last_run": None,
            "next_run": None,
        }
    return config


@router.put("/sftp-schedule")
async def update_sftp_schedule(body: SFTPScheduleConfig, user: dict = Depends(get_current_user)):
    """Update SFTP auto-upload schedule."""
    shared = get_shared_db()
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    config = {
        "tenant_id": tenant_id,
        "enabled": body.enabled,
        "frequency": body.frequency,
        "day_of_week": body.day_of_week,
        "hour": body.hour,
        "file_types": body.file_types,
        "destination_path": body.destination_path,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user.get("email", ""),
    }

    await shared.sftp_schedules.update_one(
        {"tenant_id": tenant_id},
        {"$set": config},
        upsert=True,
    )

    return {"success": True, "config": config}


@router.get("/sftp-schedule/history")
async def sftp_schedule_history(user: dict = Depends(get_current_user)):
    """Get SFTP auto-upload run history."""
    shared = get_shared_db()
    tenant_id = user.get("tenant_id")
    runs = []
    async for doc in shared.sftp_schedule_runs.find(
        {"tenant_id": tenant_id}, {"_id": 0}
    ).sort("run_at", -1).limit(20):
        runs.append(doc)
    return {"runs": runs}


# ── Chunked Upload Endpoints ──

@router.post("/upload/init")
async def init_chunked_upload(
    file_name: str = Form(...),
    file_type: str = Form(...),
    file_size: int = Form(...),
    total_chunks: int = Form(...),
    user: dict = Depends(get_current_user),
):
    """Initialize a chunked upload session."""
    upload_id = str(uuid.uuid4())

    _chunk_storage[upload_id] = {
        "chunks": {},
        "metadata": {
            "file_name": file_name,
            "file_type": file_type,
            "file_size": file_size,
            "total_chunks": total_chunks,
            "tenant_id": user.get("tenant_id", ""),
            "uploaded_by": user.get("email", ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    }

    _processing_status[upload_id] = {
        "status": "uploading",
        "progress": 0,
        "chunks_received": 0,
        "total_chunks": total_chunks,
        "file_name": file_name,
    }

    logger.info(f"Chunked upload init: {upload_id} for {file_name} ({total_chunks} chunks)")
    return {
        "upload_id": upload_id,
        "total_chunks": total_chunks,
        "status": "ready",
    }


@router.post("/upload/chunk/{upload_id}")
async def upload_chunk(
    upload_id: str,
    chunk_index: int = Form(...),
    chunk: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a single chunk of a file."""
    if upload_id not in _chunk_storage:
        raise HTTPException(status_code=404, detail="Upload session not found or expired")

    session = _chunk_storage[upload_id]
    total = session["metadata"]["total_chunks"]

    if chunk_index < 0 or chunk_index >= total:
        raise HTTPException(status_code=400, detail=f"Invalid chunk index: {chunk_index}")

    data = await chunk.read()
    session["chunks"][chunk_index] = data

    received = len(session["chunks"])
    progress = round(received / total * 100, 1)

    _processing_status[upload_id]["chunks_received"] = received
    _processing_status[upload_id]["progress"] = progress

    return {
        "upload_id": upload_id,
        "chunk_index": chunk_index,
        "chunks_received": received,
        "total_chunks": total,
        "progress": progress,
    }


@router.post("/upload/complete/{upload_id}")
async def complete_chunked_upload(upload_id: str, user: dict = Depends(get_current_user)):
    """Finalize chunked upload — reassemble and process the file."""
    if upload_id not in _chunk_storage:
        raise HTTPException(status_code=404, detail="Upload session not found")

    session = _chunk_storage[upload_id]
    meta = session["metadata"]
    total = meta["total_chunks"]
    chunks = session["chunks"]

    # Verify all chunks received
    missing = [i for i in range(total) if i not in chunks]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing chunks: {missing}")

    _processing_status[upload_id]["status"] = "processing"
    _processing_status[upload_id]["progress"] = 100

    # Reassemble file
    file_data = b""
    for i in range(total):
        file_data += chunks[i]

    # Save to disk
    file_path = os.path.join(UPLOAD_DIR, f"{upload_id}_{meta['file_name']}")
    with open(file_path, "wb") as f:
        f.write(file_data)

    file_size_mb = round(len(file_data) / (1024 * 1024), 2)

    # Store upload record
    shared = get_shared_db()
    await shared.upload_history.insert_one({
        "file_type": meta["file_type"],
        "file_name": meta["file_name"],
        "status": "success",
        "rows_processed": 0,
        "columns": [],
        "errors": [],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": meta["uploaded_by"],
        "upload_method": "chunked",
        "file_size_mb": file_size_mb,
        "upload_id": upload_id,
    })

    # Clean up in-memory chunks
    del _chunk_storage[upload_id]
    _processing_status[upload_id]["status"] = "complete"
    _processing_status[upload_id]["file_size_mb"] = file_size_mb

    # Clean up file after a delay
    async def _cleanup():
        await asyncio.sleep(300)
        try:
            os.remove(file_path)
        except Exception:
            pass
        _processing_status.pop(upload_id, None)

    asyncio.create_task(_cleanup())

    logger.info(f"Chunked upload complete: {upload_id}, {file_size_mb}MB")
    return {
        "upload_id": upload_id,
        "status": "complete",
        "file_name": meta["file_name"],
        "file_size_mb": file_size_mb,
    }


@router.get("/upload/status/{upload_id}")
async def get_upload_status(upload_id: str, user: dict = Depends(get_current_user)):
    """Get the processing status of a chunked upload."""
    if upload_id not in _processing_status:
        raise HTTPException(status_code=404, detail="Upload not found")
    return _processing_status[upload_id]


@router.delete("/upload/{upload_id}")
async def cancel_upload(upload_id: str, user: dict = Depends(get_current_user)):
    """Cancel an in-progress chunked upload."""
    _chunk_storage.pop(upload_id, None)
    _processing_status.pop(upload_id, None)
    return {"success": True, "upload_id": upload_id}
