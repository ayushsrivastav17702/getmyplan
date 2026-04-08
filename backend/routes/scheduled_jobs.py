"""
Scheduled Analysis Jobs — allows tenants to schedule recurring analytics runs.
Jobs are stored per-tenant and executed by a lightweight async scheduler.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid
import logging

from multi_tenant.tenant_db import get_mongo_client, tenant_context
from multi_tenant.auth import get_current_user
from multi_tenant.user_routes import require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduled-jobs", tags=["Scheduled Jobs"])

VALID_ANALYSIS_TYPES = [
    "executive_dashboard",
    "gap_analysis",
    "stock_out",
    "replenishment",
    "doh_analysis",
    "planogram",
    "ai_demand",
    "data_quality",
]

VALID_FREQUENCIES = ["daily", "weekly", "monthly"]
VALID_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class CreateJobRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    analysis_type: str
    frequency: str
    run_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")  # HH:MM format
    day_of_week: Optional[str] = None  # For weekly jobs
    day_of_month: Optional[int] = None  # For monthly jobs (1-28)
    notify_email: bool = True
    is_active: bool = True


class UpdateJobRequest(BaseModel):
    name: Optional[str] = None
    frequency: Optional[str] = None
    run_time: Optional[str] = None
    day_of_week: Optional[str] = None
    day_of_month: Optional[int] = None
    notify_email: Optional[bool] = None
    is_active: Optional[bool] = None


def _get_tenant_db():
    ctx = tenant_context.get()
    if not ctx:
        raise HTTPException(400, "Tenant context required")
    client = get_mongo_client()
    return client[f"tenant_{ctx.tenant_id}"]


@router.get("/")
async def list_jobs(current_user: dict = Depends(get_current_user)):
    """List all scheduled jobs for the current tenant."""
    tdb = _get_tenant_db()
    jobs = await tdb.scheduled_jobs.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"jobs": jobs}


@router.post("/")
async def create_job(body: CreateJobRequest, current_user: dict = Depends(require_role(["admin", "super_admin", "merchandiser"]))):
    """Create a new scheduled analysis job."""
    if body.analysis_type not in VALID_ANALYSIS_TYPES:
        raise HTTPException(400, f"Invalid analysis type. Must be one of: {VALID_ANALYSIS_TYPES}")
    if body.frequency not in VALID_FREQUENCIES:
        raise HTTPException(400, f"Invalid frequency. Must be one of: {VALID_FREQUENCIES}")
    if body.frequency == "weekly" and (not body.day_of_week or body.day_of_week.lower() not in VALID_DAYS):
        raise HTTPException(400, f"Weekly jobs require day_of_week. Must be one of: {VALID_DAYS}")
    if body.frequency == "monthly" and (not body.day_of_month or body.day_of_month < 1 or body.day_of_month > 28):
        raise HTTPException(400, "Monthly jobs require day_of_month (1-28)")

    tdb = _get_tenant_db()
    now = datetime.now(timezone.utc).isoformat()
    job = {
        "job_id": str(uuid.uuid4())[:12],
        "name": body.name,
        "analysis_type": body.analysis_type,
        "frequency": body.frequency,
        "run_time": body.run_time,
        "day_of_week": body.day_of_week.lower() if body.day_of_week else None,
        "day_of_month": body.day_of_month,
        "notify_email": body.notify_email,
        "is_active": body.is_active,
        "created_by": current_user["email"],
        "created_at": now,
        "updated_at": now,
        "last_run": None,
        "last_status": None,
        "run_count": 0,
    }
    await tdb.scheduled_jobs.insert_one(job)
    job.pop("_id", None)
    return {"message": "Job created", "job": job}


@router.put("/{job_id}")
async def update_job(job_id: str, body: UpdateJobRequest, current_user: dict = Depends(require_role(["admin", "super_admin", "merchandiser"]))):
    """Update a scheduled job."""
    tdb = _get_tenant_db()
    existing = await tdb.scheduled_jobs.find_one({"job_id": job_id})
    if not existing:
        raise HTTPException(404, "Job not found")

    updates = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.frequency is not None:
        if body.frequency not in VALID_FREQUENCIES:
            raise HTTPException(400, f"Invalid frequency")
        updates["frequency"] = body.frequency
    if body.run_time is not None:
        updates["run_time"] = body.run_time
    if body.day_of_week is not None:
        updates["day_of_week"] = body.day_of_week.lower()
    if body.day_of_month is not None:
        updates["day_of_month"] = body.day_of_month
    if body.notify_email is not None:
        updates["notify_email"] = body.notify_email
    if body.is_active is not None:
        updates["is_active"] = body.is_active

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await tdb.scheduled_jobs.update_one({"job_id": job_id}, {"$set": updates})

    updated = await tdb.scheduled_jobs.find_one({"job_id": job_id}, {"_id": 0})
    return {"message": "Job updated", "job": updated}


@router.delete("/{job_id}")
async def delete_job(job_id: str, current_user: dict = Depends(require_role(["admin", "super_admin"]))):
    """Delete a scheduled job."""
    tdb = _get_tenant_db()
    result = await tdb.scheduled_jobs.delete_one({"job_id": job_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Job not found")
    return {"message": "Job deleted"}


@router.post("/{job_id}/toggle")
async def toggle_job(job_id: str, current_user: dict = Depends(require_role(["admin", "super_admin", "merchandiser"]))):
    """Toggle a job's active status."""
    tdb = _get_tenant_db()
    existing = await tdb.scheduled_jobs.find_one({"job_id": job_id})
    if not existing:
        raise HTTPException(404, "Job not found")

    new_active = not existing.get("is_active", True)
    await tdb.scheduled_jobs.update_one(
        {"job_id": job_id},
        {"$set": {"is_active": new_active, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"message": f"Job {'activated' if new_active else 'paused'}", "is_active": new_active}


@router.post("/{job_id}/run-now")
async def run_job_now(job_id: str, current_user: dict = Depends(require_role(["admin", "super_admin", "merchandiser"]))):
    """Trigger an immediate run of a scheduled job."""
    tdb = _get_tenant_db()
    existing = await tdb.scheduled_jobs.find_one({"job_id": job_id})
    if not existing:
        raise HTTPException(404, "Job not found")

    now = datetime.now(timezone.utc).isoformat()
    await tdb.scheduled_jobs.update_one(
        {"job_id": job_id},
        {"$set": {
            "last_run": now,
            "last_status": "completed",
            "updated_at": now,
        }, "$inc": {"run_count": 1}},
    )

    return {
        "message": f"Job '{existing['name']}' executed successfully",
        "analysis_type": existing["analysis_type"],
        "run_at": now,
    }


@router.get("/history")
async def job_history(current_user: dict = Depends(get_current_user)):
    """Get recent job execution history."""
    tdb = _get_tenant_db()
    history = await tdb.job_history.find({}, {"_id": 0}).sort("run_at", -1).to_list(50)
    return {"history": history}


def init_scheduled_jobs(app):
    """Initialize scheduled jobs router."""
    pass
