"""
Drip Campaign API.
Manage email drip campaigns triggered by funnel drop-offs.
"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from multi_tenant.auth import get_current_user
from multi_tenant.tenant_db import get_shared_db
from services.drip_engine import get_campaigns, run_drip_check

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/drip", tags=["Drip Campaigns"])


class ToggleRequest(BaseModel):
    enabled: bool


@router.get("/campaigns")
async def list_campaigns(user: dict = Depends(get_current_user)):
    """List all drip campaigns with their enabled/disabled status."""
    shared = get_shared_db()
    campaigns = await get_campaigns(shared)
    # Add stats from drip_logs
    for c in campaigns:
        sent_count = await shared.drip_logs.count_documents({"campaign_id": c["campaign_id"]})
        c["total_sent"] = sent_count
    return {"campaigns": campaigns}


@router.put("/campaigns/{campaign_id}/toggle")
async def toggle_campaign(campaign_id: str, body: ToggleRequest, user: dict = Depends(get_current_user)):
    """Enable or disable a drip campaign."""
    shared = get_shared_db()
    result = await shared.drip_campaigns.update_one(
        {"campaign_id": campaign_id},
        {"$set": {"enabled": body.enabled, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")

    action = "enabled" if body.enabled else "disabled"
    logger.info(f"Drip campaign {campaign_id} {action} by {user.get('email')}")
    return {"success": True, "campaign_id": campaign_id, "enabled": body.enabled}


@router.post("/run")
async def run_drip(user: dict = Depends(get_current_user)):
    """Manually trigger drip campaign check and send emails."""
    shared = get_shared_db()
    from services.smtp_email_service import email_service
    result = await run_drip_check(shared, email_service)

    # Log the run
    await shared.drip_runs.insert_one({
        "triggered_by": user.get("email", "manual"),
        "run_at": result["run_at"],
        "sent": result["sent"],
        "skipped": result["skipped"],
        "errors": result["errors"],
    })

    return result


@router.get("/history")
async def drip_history(limit: int = 50, user: dict = Depends(get_current_user)):
    """Get recent drip email send history."""
    shared = get_shared_db()
    logs = []
    async for doc in shared.drip_logs.find(
        {}, {"_id": 0}
    ).sort("sent_at", -1).limit(limit):
        logs.append(doc)
    return {"logs": logs, "total": len(logs)}


@router.get("/runs")
async def drip_runs(limit: int = 10, user: dict = Depends(get_current_user)):
    """Get recent drip run history."""
    shared = get_shared_db()
    runs = []
    async for doc in shared.drip_runs.find(
        {}, {"_id": 0}
    ).sort("run_at", -1).limit(limit):
        runs.append(doc)
    return {"runs": runs}
