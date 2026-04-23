"""DNA tagging endpoints."""

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ._shared import router, _dep_user, get_db


class DNATagReq(BaseModel):
    sku: str
    launch_date: Optional[str] = None
    flow_rank: Optional[int] = None  # 1=Hero, 2=Core, 3=Fill-in
    lifecycle_stage: Optional[str] = None  # Pre-launch, Launch, Peak, Decline, Exit
    expected_weeks: Optional[int] = None


class DNABulkTagReq(BaseModel):
    style: str
    launch_date: Optional[str] = None
    flow_rank: Optional[int] = None
    lifecycle_stage: Optional[str] = None
    expected_weeks: Optional[int] = None


@router.post("/dna-tag")
async def tag_sku_dna(body: DNATagReq, user: dict = Depends(_dep_user)):
    """Tag a single SKU with DNA attributes."""
    from domains.buy_planning import DnaTagsRepository, DnaTagsService, DnaTagsNotFoundError
    svc = DnaTagsService(DnaTagsRepository(get_db()))
    try:
        return await svc.tag_sku(
            sku=body.sku, launch_date=body.launch_date, flow_rank=body.flow_rank,
            lifecycle_stage=body.lifecycle_stage, expected_weeks=body.expected_weeks,
        )
    except DnaTagsNotFoundError as e:
        raise HTTPException(404, str(e))


@router.post("/dna-tag/bulk")
async def tag_style_dna_bulk(body: DNABulkTagReq, user: dict = Depends(_dep_user)):
    """Tag all SKUs of a style with DNA attributes."""
    from domains.buy_planning import DnaTagsRepository, DnaTagsService
    svc = DnaTagsService(DnaTagsRepository(get_db()))
    return await svc.tag_style_bulk(
        style=body.style, launch_date=body.launch_date, flow_rank=body.flow_rank,
        lifecycle_stage=body.lifecycle_stage, expected_weeks=body.expected_weeks,
    )


@router.post("/dna-tag/auto")
async def auto_tag_dna(user: dict = Depends(_dep_user)):
    """
    Auto-tag DNA from sales data:
      flow_rank: 1=Hero (top 80% rev), 2=Core (next 15%), 3=Fill-in (bottom 5%)
      lifecycle_stage: Launch (≤4w) / Peak / Decline / Exit (no sale 30d+)
    """
    from domains.buy_planning import DnaTagsRepository, DnaTagsService
    svc = DnaTagsService(DnaTagsRepository(get_db()))
    return await svc.auto_tag(user.get("tenant_id", ""))


@router.get("/dna-tags")
async def get_dna_tags(user: dict = Depends(_dep_user)):
    """Get DNA tags grouped by style."""
    from domains.buy_planning import DnaTagsRepository, DnaTagsService
    svc = DnaTagsService(DnaTagsRepository(get_db()))
    return await svc.list_tags(user.get("tenant_id", ""))
