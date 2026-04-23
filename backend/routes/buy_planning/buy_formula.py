"""Buy-Formula calculate + CSV export endpoints."""

import io
import csv
from datetime import datetime, timezone

from fastapi import Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from ._shared import router, _dep_user, get_db


class BuyFormulaReq(BaseModel):
    cover_days: int = 30
    safety_days: int = 7
    sell_through_targets: Optional[dict] = None  # override defaults


@router.post("/buy-formula/calculate")
async def calculate_buy_formula(body: BuyFormulaReq, user: dict = Depends(_dep_user)):
    """
    Full Buy Formula:
    buy_qty = MAX(
        (target_sell_through × forecasted_demand) - current_SOH,
        display_minimum_units × store_count,
        safety_stock_units
    )
    """
    from domains.buy_planning import BuyFormulaRepository, BuyFormulaService
    svc = BuyFormulaService(BuyFormulaRepository(get_db()))
    return await svc.calculate(
        tenant_id=user.get("tenant_id", ""),
        cover_days=body.cover_days, safety_days=body.safety_days,
        sell_through_targets=body.sell_through_targets,
    )


@router.get("/buy-formula/export/csv")
async def export_buy_plan_csv(cover_days: int = 30, safety_days: int = 7, user: dict = Depends(_dep_user)):
    """Export the full buy plan to CSV — uses the same BuyFormulaService as /calculate for consistency."""
    from domains.buy_planning import BuyFormulaRepository, BuyFormulaService
    repo = BuyFormulaRepository(get_db())
    svc = BuyFormulaService(repo)
    tenant_id = user.get("tenant_id", "")
    result = await svc.calculate(
        tenant_id=tenant_id, cover_days=cover_days, safety_days=safety_days,
    )
    sku_meta = await repo.load_sku_meta(tenant_id)  # for DNA columns (flow_rank, lifecycle, launch_date)
    rows = svc.to_csv_rows(result, sku_meta)

    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        buf.write("No data available\n")
    buf.seek(0)

    filename = f"buy_plan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
