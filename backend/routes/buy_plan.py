"""
Buy Plan Engine — Backend Route Module
Endpoints: generate, export-excel, upload-edited-plan, history
"""
from fastapi import APIRouter, HTTPException, Query, Body, File, UploadFile, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, List
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import pandas as pd
import numpy as np
import io
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(tags=["buy-plan"])

_client: Optional[AsyncIOMotorClient] = None
_get_db = None
_get_current_user = None
_require_role = None

def init_buy_plan(mongo_client, get_db_func, get_current_user_func=None, require_role_func=None):
    global _client, _get_db, _get_current_user, _require_role
    _client = mongo_client
    _get_db = get_db_func
    _get_current_user = get_current_user_func
    _require_role = require_role_func

# ── Constants ────────────────────────────────────────────────

MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

DEFAULT_ASP = {
    "Jeans": 1499, "Shirts": 1199, "Jackets": 2499,
    "Belts": 799, "Socks": 299, "Shoes": 2999
}

DEFAULT_CHANNEL_SPLITS = {
    "STORE_A": 0.35, "STORE_B": 0.15,
    "AMAZON": 0.30, "FLIPKART": 0.12, "MYNTRA": 0.08
}

DEFAULT_SEASONAL_INDEX = {
    1: 0.85, 2: 0.80, 3: 0.90, 4: 0.95,
    5: 1.00, 6: 1.05, 7: 1.10, 8: 1.15,
    9: 1.40, 10: 1.20, 11: 1.10, 12: 1.50
}

ALL_CATEGORIES = ["Jeans", "Shirts", "Jackets", "Belts", "Socks", "Shoes"]
ALL_CHANNELS = ["STORE_A", "STORE_B", "AMAZON", "FLIPKART", "MYNTRA"]


# ── Rate Limiter ─────────────────────────────────────────────
_rate_buckets: Dict[str, list] = {}
RATE_LIMIT = 30

def _check_rate_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    if ip not in _rate_buckets:
        _rate_buckets[ip] = []
    _rate_buckets[ip] = [t for t in _rate_buckets[ip] if now - t < 60]
    if len(_rate_buckets[ip]) >= RATE_LIMIT:
        raise HTTPException(429, detail="Rate limit exceeded. Try again later.")
    _rate_buckets[ip].append(now)


# ── Service helpers ──────────────────────────────────────────

async def _get_historical_analysis(tenant_db, category: str):
    """Analyse historical sales data for a category."""
    pipeline = [
        {"$match": {"category": category}},
        {"$group": {
            "_id": {"channel": "$channel", "month": {"$month": {"$toDate": "$day"}}},
            "revenue": {"$sum": "$revenue"},
            "quantity": {"$sum": "$quantity"},
        }},
    ]
    try:
        results = await tenant_db.daily_sales.aggregate(pipeline).to_list(None)
    except Exception:
        results = []

    channel_data = defaultdict(lambda: {
        'monthly_sales': [0] * 12,
        'monthly_revenue': [0] * 12,
        'total_quantity': 0,
        'total_revenue': 0,
    })
    for r in results:
        ch = r["_id"].get("channel", "UNKNOWN")
        m_idx = (r["_id"].get("month", 1) or 1) - 1
        if 0 <= m_idx < 12:
            channel_data[ch]['monthly_sales'][m_idx] += r.get('quantity', 0)
            channel_data[ch]['monthly_revenue'][m_idx] += r.get('revenue', 0)
            channel_data[ch]['total_quantity'] += r.get('quantity', 0)
            channel_data[ch]['total_revenue'] += r.get('revenue', 0)

    for ch, data in channel_data.items():
        total = data['total_quantity']
        avg = total / 12 if total > 0 else 1
        data['seasonal_index'] = {
            i + 1: round(data['monthly_sales'][i] / avg, 2) if avg > 0 else 1.0
            for i in range(12)
        }
    return dict(channel_data)


async def _get_category_asp(tenant_db, category: str) -> float:
    """Get ASP from sales data or fallback to defaults."""
    pipeline = [
        {"$match": {"category": category}},
        {"$group": {"_id": None, "total_rev": {"$sum": "$revenue"}, "total_qty": {"$sum": "$quantity"}}},
    ]
    try:
        r = await tenant_db.daily_sales.aggregate(pipeline).to_list(None)
        if r and r[0].get("total_qty", 0) > 0:
            return round(r[0]["total_rev"] / r[0]["total_qty"], 2)
    except Exception:
        pass
    return DEFAULT_ASP.get(category, 1500)


async def _get_current_inventory(tenant_db, category: str, channel: str) -> int:
    """Get current inventory for a category-channel."""
    pipeline = [
        {"$match": {"category": category, "channel": channel}},
        {"$group": {"_id": None, "qty": {"$sum": "$quantity"}}},
    ]
    try:
        r = await tenant_db.store_inventory.aggregate(pipeline).to_list(None)
        return r[0]["qty"] if r else 0
    except Exception:
        return 0


async def _get_sell_through(tenant_db, category: str, channel: str) -> float:
    """Sell-through = units sold / avg inventory (last 90 days)."""
    try:
        sold_p = [
            {"$match": {"category": category, "channel": channel}},
            {"$group": {"_id": None, "sold": {"$sum": "$quantity"}}},
        ]
        inv_p = [
            {"$match": {"category": category, "channel": channel}},
            {"$group": {"_id": None, "inv": {"$avg": "$quantity"}}},
        ]
        sold_r = await tenant_db.daily_sales.aggregate(sold_p).to_list(None)
        inv_r = await tenant_db.store_inventory.aggregate(inv_p).to_list(None)
        sold = sold_r[0]["sold"] if sold_r else 0
        inv = inv_r[0]["inv"] if inv_r else 1
        if inv > 0:
            return round(sold / inv, 2)
    except Exception:
        pass
    return 0.0


def _apply_seasonal_phasing(total_units: int, seasonal_index: dict, months: int = 12):
    """Distribute units across months using seasonal weights."""
    if not seasonal_index:
        seasonal_index = DEFAULT_SEASONAL_INDEX
    total_weight = sum(seasonal_index.get(m, 1) for m in range(1, months + 1))
    results = []
    for m in range(1, months + 1):
        w = seasonal_index.get(m, 1) / total_weight if total_weight > 0 else 1.0 / months
        units = int(total_units * w)
        results.append((m, units, round(w, 4)))
    diff = total_units - sum(u for _, u, _ in results)
    if diff != 0 and results:
        results[0] = (results[0][0], results[0][1] + diff, results[0][2])
    return results


def _split_by_channel(total_units: int, channel_splits: dict):
    """Split units across channels by revenue share."""
    units = {}
    for ch, pct in channel_splits.items():
        units[ch] = int(total_units * pct)
    diff = total_units - sum(units.values())
    if diff != 0 and units:
        first = list(units.keys())[0]
        units[first] += diff
    return units


def _calculate_buy_quantity(required: int, safety_pct: float, current_inv: int,
                            intransit: int, lead_time_days: int, daily_demand: float):
    """Calculate final buy quantity with dynamic safety stock."""
    if daily_demand and daily_demand > 0:
        ss = int(daily_demand * lead_time_days * (safety_pct / 100))
    else:
        ss = int(required * (safety_pct / 100))
    buy = required + ss - current_inv - intransit
    return max(0, buy), ss


# ── Endpoints ────────────────────────────────────────────────

@router.post("/buy-plan/generate")
async def generate_buy_plan(
    request: Request,
    body: dict = Body(...),
    current_user: dict = Depends(lambda: None),
):
    _check_rate_limit(request)
    if _get_current_user:
        current_user = await _get_current_user(request)

    tenant_db = _get_db()

    # Parse params with defaults
    revenue_target_cr = body.get("revenue_target_cr", 1.1)
    revenue_increase_pct = body.get("revenue_increase_percent", 20)
    categories = body.get("categories", ALL_CATEGORIES)
    channels = body.get("channels", ALL_CHANNELS)
    months = min(body.get("months", 12), 24)
    safety_stock_pct = body.get("safety_stock_percent", 15)
    lead_time_days = body.get("lead_time_days", 30)
    return_rate_pct = body.get("return_rate_percent", 5) / 100

    revenue_target = revenue_target_cr * 10_000_000  # Cr → Rs

    # ── Category contributions from historical data ──────────
    cat_rev = {}
    for cat in categories:
        pipeline = [
            {"$match": {"category": cat}},
            {"$group": {"_id": None, "rev": {"$sum": "$revenue"}}},
        ]
        try:
            r = await tenant_db.daily_sales.aggregate(pipeline).to_list(None)
            cat_rev[cat] = r[0]["rev"] if r else 0
        except Exception:
            cat_rev[cat] = 0

    total_rev = sum(cat_rev.values())
    contributions = (
        {c: cat_rev[c] / total_rev for c in categories}
        if total_rev > 0
        else {c: 1 / len(categories) for c in categories}
    )

    # ── Channel splits from historical data ──────────────────
    channel_splits = {ch: DEFAULT_CHANNEL_SPLITS.get(ch, 0.1) for ch in channels}
    try:
        split_p = [
            {"$match": {"channel": {"$in": channels}}},
            {"$group": {"_id": "$channel", "rev": {"$sum": "$revenue"}}},
        ]
        real = await tenant_db.daily_sales.aggregate(split_p).to_list(None)
        if real:
            t = sum(s["rev"] for s in real)
            if t > 0:
                channel_splits = {s["_id"]: s["rev"] / t for s in real if s["_id"] in channels}
                # Fill missing channels
                for ch in channels:
                    if ch not in channel_splits:
                        channel_splits[ch] = DEFAULT_CHANNEL_SPLITS.get(ch, 0.05)
    except Exception:
        pass
    # Normalize
    total_split = sum(channel_splits.values())
    if total_split > 0:
        channel_splits = {k: v / total_split for k, v in channel_splits.items()}

    # ── Process each category ────────────────────────────────
    categories_plan = []
    for cat in categories:
        historical = await _get_historical_analysis(tenant_db, cat)
        asp = await _get_category_asp(tenant_db, cat)
        contribution = contributions.get(cat, 1 / len(categories))

        # Step 2: Revenue → units
        cat_revenue_target = revenue_target * contribution
        base_units = cat_revenue_target / asp if asp > 0 else 0
        required_units = max(1, int(base_units / (1 - return_rate_pct)))

        # Step 3: Seasonal phasing
        seasonal_idx = {}
        for ch_data in historical.values():
            if ch_data.get("seasonal_index"):
                seasonal_idx = ch_data["seasonal_index"]
                break
        monthly_raw = _apply_seasonal_phasing(required_units, seasonal_idx, months)

        monthly_breakdown = []
        for m, units, factor in monthly_raw:
            monthly_breakdown.append({
                "month": m,
                "month_name": MONTH_NAMES[m - 1] if m <= 12 else f"M{m}",
                "units": units,
                "revenue": round(units * asp, 2),
                "seasonal_factor": round(factor, 4),
            })

        # Step 4: Channel split
        ch_units = _split_by_channel(required_units, channel_splits)

        # Step 5: Buy quantity per channel
        channel_breakdown = []
        for ch, units in ch_units.items():
            curr_inv = await _get_current_inventory(tenant_db, cat, ch)
            sell_through = await _get_sell_through(tenant_db, cat, ch)
            daily_demand = units / 30 if units > 0 else 0

            buy_qty, safety = _calculate_buy_quantity(
                units, safety_stock_pct, curr_inv, 0,
                lead_time_days, daily_demand
            )

            channel_breakdown.append({
                "channel": ch,
                "channel_type": "store" if ch.startswith("STORE") else "marketplace",
                "revenue_target": round(units * asp, 2),
                "units_needed": units,
                "safety_stock": safety,
                "current_inventory": curr_inv,
                "intransit_stock": 0,
                "buy_quantity": buy_qty,
                "buy_value": round(buy_qty * asp, 2),
                "asp": asp,
                "sell_through_rate": sell_through,
            })

        cat_plan = {
            "category": cat,
            "asp": asp,
            "contribution_percent": round(contribution * 100, 1),
            "revenue_target": round(required_units * asp, 2),
            "required_units": required_units,
            "monthly_breakdown": monthly_breakdown,
            "channel_breakdown": channel_breakdown,
            "total_buy_quantity": sum(c["buy_quantity"] for c in channel_breakdown),
            "total_buy_value": sum(c["buy_value"] for c in channel_breakdown),
        }
        categories_plan.append(cat_plan)

    user_email = current_user.get("email", "system") if current_user else "system"

    response = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "revenue_target_cr": revenue_target_cr,
            "revenue_increase_percent": revenue_increase_pct,
            "user": user_email,
        },
        "summary": {
            "total_buy_quantity": sum(c["total_buy_quantity"] for c in categories_plan),
            "total_buy_value": round(sum(c["total_buy_value"] for c in categories_plan), 2),
            "total_revenue_target": revenue_target,
            "categories_processed": len(categories_plan),
            "channels_used": list(channel_splits.keys()),
        },
        "categories": categories_plan,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
    }

    # Save to history
    try:
        history_doc = {**response, "saved_at": datetime.now(timezone.utc).isoformat()}
        await tenant_db.buy_plan_history.insert_one(history_doc)
    except Exception as e:
        logger.warning(f"Failed to save buy plan history: {e}")

    return response


@router.post("/buy-plan/export-excel")
async def export_buy_plan_excel(
    request: Request,
    body: dict = Body(...),
    current_user: dict = Depends(lambda: None),
):
    """Export buy plan as a multi-sheet Excel workbook."""
    _check_rate_limit(request)
    if _get_current_user:
        current_user = await _get_current_user(request)

    # Generate the plan first
    plan = await generate_buy_plan(request, body, current_user)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:

        # Sheet 1: Executive Summary
        summary_rows = {
            "Metric": [
                "Total Revenue Target (Rs)", "Total Buy Quantity (Units)",
                "Total Buy Value (Rs)", "Safety Stock %",
                "Return Rate %", "Lead Time (Days)",
                "Categories Planned", "Channels Used",
                "Generated At", "Generated By",
            ],
            "Value": [
                plan["summary"]["total_revenue_target"],
                plan["summary"]["total_buy_quantity"],
                plan["summary"]["total_buy_value"],
                body.get("safety_stock_percent", 15),
                body.get("return_rate_percent", 5),
                body.get("lead_time_days", 30),
                plan["summary"]["categories_processed"],
                ", ".join(plan["summary"]["channels_used"]),
                plan["metadata"]["generated_at"],
                plan["metadata"].get("user", "System"),
            ],
        }
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="Executive Summary", index=False)

        # Sheet 2: Category Summary
        cat_rows = []
        for cat in plan["categories"]:
            cat_rows.append({
                "Category": cat["category"],
                "ASP (Rs)": cat["asp"],
                "Contribution %": cat["contribution_percent"],
                "Revenue Target (Rs)": cat["revenue_target"],
                "Required Units": cat["required_units"],
                "Total Buy Quantity": cat["total_buy_quantity"],
                "Total Buy Value (Rs)": cat["total_buy_value"],
                "Buy vs Required %": round(
                    (cat["total_buy_quantity"] / cat["required_units"]) * 100, 1
                ) if cat["required_units"] > 0 else 0,
            })
        pd.DataFrame(cat_rows).to_excel(writer, sheet_name="Category Summary", index=False)

        # Sheet 3: Monthly Breakdown
        monthly_rows = []
        for cat in plan["categories"]:
            for m in cat["monthly_breakdown"]:
                monthly_rows.append({
                    "Category": cat["category"],
                    "Month": m["month_name"],
                    "Month #": m["month"],
                    "Seasonal Factor": m["seasonal_factor"],
                    "Planned Units": m["units"],
                    "Planned Revenue (Rs)": m["revenue"],
                    "Adjustment": 0,
                    "Final Units": m["units"],
                })
        pd.DataFrame(monthly_rows).to_excel(writer, sheet_name="Monthly Plan (Editable)", index=False)

        # Sheet 4: Channel Buy Plan (main editable)
        ch_rows = []
        for cat in plan["categories"]:
            for ch in cat["channel_breakdown"]:
                ch_rows.append({
                    "Category": cat["category"],
                    "Channel": ch["channel"],
                    "Type": ch["channel_type"],
                    "ASP (Rs)": ch["asp"],
                    "Units Needed": ch["units_needed"],
                    "Safety Stock": ch["safety_stock"],
                    "Current Inventory": ch["current_inventory"],
                    "In-Transit": ch["intransit_stock"],
                    "Recommended Buy": ch["buy_quantity"],
                    "Buy Value (Rs)": ch["buy_value"],
                    "Sell-Through Rate": ch["sell_through_rate"],
                    "USER OVERRIDE ->": "",
                    "Final Buy Qty": ch["buy_quantity"],
                })
        pd.DataFrame(ch_rows).to_excel(writer, sheet_name="Buy Plan (Editable)", index=False)

        # Sheet 5: Instructions
        instr = pd.DataFrame({
            "Step": ["1", "2", "3", "4", "5"],
            "Action": [
                "Review the Monthly Plan sheet and adjust units if needed",
                'Go to "Buy Plan (Editable)" sheet',
                'Enter your override quantity in "USER OVERRIDE ->" column',
                "Save the file",
                'Upload back using the "Upload Edited Plan" button',
            ],
        })
        instr.to_excel(writer, sheet_name="Instructions", index=False)

        # Format sheets
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            ws.freeze_panes = "A2"
            for col in ws.columns:
                max_len = max((len(str(c.value or "")) for c in col), default=10)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 30)

    output.seek(0)
    fname = f"buy_plan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@router.post("/buy-plan/upload-edited-plan")
async def upload_edited_plan(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(lambda: None),
):
    """Upload an edited Excel plan and save overrides."""
    if _get_current_user:
        current_user = await _get_current_user(request)

    tenant_db = _get_db()
    contents = await file.read()

    try:
        df = pd.read_excel(io.BytesIO(contents), sheet_name="Buy Plan (Editable)")
    except Exception as e:
        raise HTTPException(400, f"Could not read 'Buy Plan (Editable)' sheet: {str(e)}")

    overrides = []
    user_email = current_user.get("email", "system") if current_user else "system"

    for _, row in df.iterrows():
        override_val = row.get("USER OVERRIDE ->")
        if pd.notna(override_val) and str(override_val).strip() != "":
            try:
                override_qty = int(float(override_val))
            except (ValueError, TypeError):
                continue
            overrides.append({
                "category": row.get("Category", ""),
                "channel": row.get("Channel", ""),
                "original_buy_qty": int(row.get("Recommended Buy", 0)),
                "user_override_buy_qty": override_qty,
                "modified_at": datetime.now(timezone.utc).isoformat(),
                "modified_by": user_email,
            })

    if overrides:
        await tenant_db.buy_plan_overrides.insert_many(overrides)

    return {
        "status": "success",
        "message": f"Applied {len(overrides)} user overrides",
        "overrides_count": len(overrides),
    }


@router.get("/buy-plan/history")
async def get_plan_history(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(lambda: None),
):
    """Get saved buy plan history."""
    if _get_current_user:
        await _get_current_user(request)

    tenant_db = _get_db()
    cursor = tenant_db.buy_plan_history.find(
        {}, {"_id": 0}
    ).sort("saved_at", -1).limit(limit)

    history = await cursor.to_list(None)
    return {"history": history, "count": len(history)}


@router.get("/buy-plan/summary")
async def get_plan_summary(request: Request, current_user: dict = Depends(lambda: None)):
    """Quick summary of categories, channels, and defaults."""
    return {
        "categories": ALL_CATEGORIES,
        "channels": ALL_CHANNELS,
        "channel_types": {ch: "store" if ch.startswith("STORE") else "marketplace" for ch in ALL_CHANNELS},
        "default_asp": DEFAULT_ASP,
        "default_channel_splits": DEFAULT_CHANNEL_SPLITS,
        "seasonal_index": DEFAULT_SEASONAL_INDEX,
    }
