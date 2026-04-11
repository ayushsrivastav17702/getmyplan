"""
Invoice Generation API.
Auto-generates monthly invoices from tenant plan data.
Supports PDF download, usage metrics, and manual invoice creation.
"""
import io
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from multi_tenant.auth import get_current_user
from multi_tenant.tenant_db import get_shared_db
from core.plan_access import PLAN_FEATURES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])

# Plan pricing (monthly, base currency)
PLAN_PRICING = {
    "trial": {"amount": 0, "currency": "INR", "label": "Free Trial"},
    "starter": {"amount": 29000, "currency": "INR", "label": "Starter Plan"},
    "professional": {"amount": 99000, "currency": "INR", "label": "Professional Plan"},
    "enterprise": {"amount": 249000, "currency": "INR", "label": "Enterprise Plan"},
}

TAX_RATE = 0.18  # 18% GST


def _generate_invoice_number(tenant_id: str, seq: int) -> str:
    now = datetime.now(timezone.utc)
    return f"GMP-{now.strftime('%Y%m')}-{tenant_id[:6].upper()}-{seq:04d}"


async def _get_usage_metrics(shared, tenant_id: str) -> dict:
    """Gather usage metrics for a tenant."""
    user_count = await shared.user_tenants.count_documents({"tenant_id": tenant_id, "is_active": True})
    upload_count = await shared.upload_history.count_documents({})
    sales_rows = await shared.daily_sales.count_documents({"tenant_id": tenant_id})
    style_count = await shared.style_master.count_documents({"tenant_id": tenant_id})
    store_count = await shared.store_master.count_documents({"tenant_id": tenant_id})
    forecast_count = await shared.forecast_snapshots.count_documents({})
    buy_plans = await shared.buy_plan_history.count_documents({})

    # Estimate storage (rough)
    storage_mb = round((sales_rows * 0.0005) + (upload_count * 0.05) + (style_count * 0.001), 2)

    return {
        "active_users": user_count,
        "total_uploads": upload_count,
        "sales_records": sales_rows,
        "style_master_records": style_count,
        "store_count": store_count,
        "forecast_snapshots": forecast_count,
        "buy_plans_generated": buy_plans,
        "estimated_storage_mb": storage_mb,
    }


def _format_currency(amount: float, currency: str) -> str:
    if currency == "INR":
        return f"\u20b9{amount:,.2f}"
    elif currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "ZAR":
        return f"R{amount:,.2f}"
    elif currency == "AED":
        return f"AED {amount:,.2f}"
    return f"{currency} {amount:,.2f}"


# ── Models ──

class InvoiceCreateRequest(BaseModel):
    description: Optional[str] = None
    custom_amount: Optional[float] = None
    billing_period_start: Optional[str] = None
    billing_period_end: Optional[str] = None


class InvoiceUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(paid|cancelled|overdue)$")
    payment_reference: Optional[str] = None


# ── Endpoints ──

@router.post("/generate")
async def generate_invoice(body: InvoiceCreateRequest = None, user: dict = Depends(get_current_user)):
    """Generate a new invoice for the current tenant."""
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    shared = get_shared_db()
    tenant = await shared.tenants.find_one({"tenant_id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    plan_type = tenant.get("plan_type", "starter")
    pricing = PLAN_PRICING.get(plan_type, PLAN_PRICING["starter"])
    currency = tenant.get("currency", pricing["currency"])

    now = datetime.now(timezone.utc)
    period_start = now.replace(day=1).strftime("%Y-%m-%d")
    period_end = (now.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    period_end_str = period_end.strftime("%Y-%m-%d")

    if body and body.billing_period_start:
        period_start = body.billing_period_start
    if body and body.billing_period_end:
        period_end_str = body.billing_period_end

    # Calculate amounts
    subtotal = body.custom_amount if (body and body.custom_amount is not None) else pricing["amount"]
    tax_amount = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + tax_amount, 2)

    # Get usage metrics
    usage = await _get_usage_metrics(shared, tenant_id)

    # Generate invoice number
    existing_count = await shared.invoices.count_documents({"tenant_id": tenant_id})
    invoice_number = _generate_invoice_number(tenant_id, existing_count + 1)

    plan_limits = PLAN_FEATURES.get(plan_type, PLAN_FEATURES["starter"])["limits"]

    invoice = {
        "tenant_id": tenant_id,
        "invoice_number": invoice_number,
        "company_name": tenant.get("company_name", tenant_id),
        "plan_type": plan_type,
        "plan_label": pricing["label"],
        "billing_period": {"start": period_start, "end": period_end_str},
        "subtotal": subtotal,
        "tax_rate": TAX_RATE,
        "tax_amount": tax_amount,
        "total": total,
        "currency": currency,
        "status": "unpaid" if subtotal > 0 else "paid",
        "description": (body.description if body else None) or f"Monthly subscription - {pricing['label']}",
        "usage_metrics": usage,
        "plan_limits": plan_limits,
        "created_by": user.get("email", ""),
        "created_at": now.isoformat(),
        "due_date": (now + timedelta(days=15)).isoformat(),
    }

    result = await shared.invoices.insert_one(invoice)
    invoice_id = str(result.inserted_id)

    logger.info(f"Invoice {invoice_number} generated for tenant {tenant_id}")
    return {
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
        "total": total,
        "currency": currency,
        "status": invoice["status"],
        "created_at": invoice["created_at"],
    }


@router.get("")
async def list_invoices(
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """List all invoices for the current tenant."""
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    shared = get_shared_db()
    invoices = []
    async for doc in shared.invoices.find(
        {"tenant_id": tenant_id}, {"_id": 1}
    ).sort("created_at", -1).limit(limit):
        full = await shared.invoices.find_one({"_id": doc["_id"]})
        invoices.append({
            "invoice_id": str(full["_id"]),
            "invoice_number": full.get("invoice_number", ""),
            "company_name": full.get("company_name", ""),
            "plan_type": full.get("plan_type", ""),
            "plan_label": full.get("plan_label", ""),
            "billing_period": full.get("billing_period", {}),
            "subtotal": full.get("subtotal", 0),
            "tax_amount": full.get("tax_amount", 0),
            "total": full.get("total", 0),
            "currency": full.get("currency", "INR"),
            "status": full.get("status", "unpaid"),
            "description": full.get("description", ""),
            "created_at": full.get("created_at", ""),
            "due_date": full.get("due_date", ""),
            "usage_metrics": full.get("usage_metrics", {}),
        })
    return {"invoices": invoices}


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    """Get a single invoice with full details."""
    tenant_id = user.get("tenant_id")
    shared = get_shared_db()
    try:
        doc = await shared.invoices.find_one({"_id": ObjectId(invoice_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid invoice ID")
    if not doc:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return {
        "invoice_id": str(doc["_id"]),
        "invoice_number": doc.get("invoice_number", ""),
        "company_name": doc.get("company_name", ""),
        "plan_type": doc.get("plan_type", ""),
        "plan_label": doc.get("plan_label", ""),
        "billing_period": doc.get("billing_period", {}),
        "subtotal": doc.get("subtotal", 0),
        "tax_rate": doc.get("tax_rate", 0),
        "tax_amount": doc.get("tax_amount", 0),
        "total": doc.get("total", 0),
        "currency": doc.get("currency", "INR"),
        "status": doc.get("status", "unpaid"),
        "description": doc.get("description", ""),
        "usage_metrics": doc.get("usage_metrics", {}),
        "plan_limits": doc.get("plan_limits", {}),
        "created_by": doc.get("created_by", ""),
        "created_at": doc.get("created_at", ""),
        "due_date": doc.get("due_date", ""),
        "payment_reference": doc.get("payment_reference"),
        "paid_at": doc.get("paid_at"),
    }


@router.put("/{invoice_id}/status")
async def update_invoice_status(
    invoice_id: str, body: InvoiceUpdateRequest, user: dict = Depends(get_current_user),
):
    """Update invoice status (paid/cancelled/overdue)."""
    tenant_id = user.get("tenant_id")
    shared = get_shared_db()
    try:
        doc = await shared.invoices.find_one({"_id": ObjectId(invoice_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid invoice ID")
    if not doc:
        raise HTTPException(status_code=404, detail="Invoice not found")

    update = {"status": body.status}
    if body.status == "paid":
        update["paid_at"] = datetime.now(timezone.utc).isoformat()
        if body.payment_reference:
            update["payment_reference"] = body.payment_reference

    await shared.invoices.update_one({"_id": ObjectId(invoice_id)}, {"$set": update})
    return {"success": True, "status": body.status}


@router.get("/{invoice_id}/download")
async def download_invoice_pdf(invoice_id: str, user: dict = Depends(get_current_user)):
    """Download invoice as a styled HTML document (printable as PDF via browser)."""
    tenant_id = user.get("tenant_id")
    shared = get_shared_db()
    try:
        doc = await shared.invoices.find_one({"_id": ObjectId(invoice_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid invoice ID")
    if not doc:
        raise HTTPException(status_code=404, detail="Invoice not found")

    currency = doc.get("currency", "INR")
    usage = doc.get("usage_metrics", {})
    limits = doc.get("plan_limits", {})
    period = doc.get("billing_period", {})

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Invoice {doc.get('invoice_number','')}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 40px; color: #1e293b; }}
  .invoice {{ max-width: 800px; margin: 0 auto; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 40px; border-bottom: 3px solid #0176D3; padding-bottom: 20px; }}
  .logo h1 {{ margin: 0; color: #0176D3; font-size: 28px; }}
  .logo p {{ margin: 4px 0 0; color: #64748b; font-size: 13px; }}
  .inv-details {{ text-align: right; }}
  .inv-details h2 {{ margin: 0; font-size: 32px; color: #1e293b; text-transform: uppercase; letter-spacing: 2px; }}
  .inv-details p {{ margin: 4px 0; color: #64748b; font-size: 13px; }}
  .status {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
  .status-paid {{ background: #dcfce7; color: #166534; }}
  .status-unpaid {{ background: #fef3c7; color: #92400e; }}
  .status-overdue {{ background: #fee2e2; color: #991b1b; }}
  .status-cancelled {{ background: #f1f5f9; color: #64748b; }}
  .meta {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; }}
  .meta-box h3 {{ margin: 0 0 8px; font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; }}
  .meta-box p {{ margin: 2px 0; font-size: 14px; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
  th {{ text-align: left; padding: 10px 12px; background: #f8fafc; border-bottom: 2px solid #e2e8f0; font-size: 11px; text-transform: uppercase; color: #64748b; letter-spacing: 0.5px; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
  .totals {{ text-align: right; margin-top: 10px; }}
  .totals .row {{ display: flex; justify-content: flex-end; gap: 40px; padding: 6px 0; font-size: 14px; }}
  .totals .total-row {{ font-size: 18px; font-weight: 700; color: #0176D3; border-top: 2px solid #e2e8f0; padding-top: 10px; }}
  .usage {{ margin-top: 30px; }}
  .usage h3 {{ font-size: 14px; color: #1e293b; margin-bottom: 12px; }}
  .usage-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
  .usage-item {{ background: #f8fafc; padding: 12px; border-radius: 8px; text-align: center; }}
  .usage-item .val {{ font-size: 20px; font-weight: 700; color: #1e293b; }}
  .usage-item .lbl {{ font-size: 11px; color: #64748b; margin-top: 2px; }}
  .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #94a3b8; font-size: 12px; }}
  @media print {{ body {{ padding: 20px; }} }}
</style></head><body>
<div class="invoice">
  <div class="header">
    <div class="logo">
      <h1>GetMyPlan</h1>
      <p>AI-Powered Retail Analytics</p>
      <p>info@getmyplan.in</p>
    </div>
    <div class="inv-details">
      <h2>Invoice</h2>
      <p><strong>{doc.get('invoice_number','')}</strong></p>
      <p>Date: {doc.get('created_at','')[:10]}</p>
      <p>Due: {doc.get('due_date','')[:10]}</p>
      <p><span class="status status-{doc.get('status','unpaid')}">{doc.get('status','unpaid').upper()}</span></p>
    </div>
  </div>

  <div class="meta">
    <div class="meta-box">
      <h3>Bill To</h3>
      <p><strong>{doc.get('company_name','')}</strong></p>
      <p>Tenant ID: {doc.get('tenant_id','')}</p>
    </div>
    <div class="meta-box">
      <h3>Billing Period</h3>
      <p>{period.get('start','')} to {period.get('end','')}</p>
      <p>Plan: {doc.get('plan_label','')}</p>
    </div>
  </div>

  <table>
    <thead><tr><th>Description</th><th>Plan</th><th style="text-align:right">Amount</th></tr></thead>
    <tbody>
      <tr>
        <td>{doc.get('description','Monthly subscription')}</td>
        <td>{doc.get('plan_label','')}</td>
        <td style="text-align:right">{_format_currency(doc.get('subtotal',0), currency)}</td>
      </tr>
    </tbody>
  </table>

  <div class="totals">
    <div class="row"><span>Subtotal</span><span>{_format_currency(doc.get('subtotal',0), currency)}</span></div>
    <div class="row"><span>GST ({int(doc.get('tax_rate',0.18)*100)}%)</span><span>{_format_currency(doc.get('tax_amount',0), currency)}</span></div>
    <div class="row total-row"><span>Total</span><span>{_format_currency(doc.get('total',0), currency)}</span></div>
  </div>

  <div class="usage">
    <h3>Usage Metrics (Current Period)</h3>
    <div class="usage-grid">
      <div class="usage-item"><div class="val">{usage.get('active_users',0)}</div><div class="lbl">Active Users</div></div>
      <div class="usage-item"><div class="val">{usage.get('total_uploads',0)}</div><div class="lbl">Uploads</div></div>
      <div class="usage-item"><div class="val">{usage.get('sales_records',0):,}</div><div class="lbl">Sales Records</div></div>
      <div class="usage-item"><div class="val">{usage.get('estimated_storage_mb',0)}</div><div class="lbl">Storage (MB)</div></div>
      <div class="usage-item"><div class="val">{usage.get('store_count',0)}</div><div class="lbl">Stores</div></div>
      <div class="usage-item"><div class="val">{usage.get('forecast_snapshots',0)}</div><div class="lbl">Forecasts</div></div>
      <div class="usage-item"><div class="val">{usage.get('buy_plans_generated',0)}</div><div class="lbl">Buy Plans</div></div>
      <div class="usage-item"><div class="val">{usage.get('style_master_records',0)}</div><div class="lbl">SKUs</div></div>
    </div>
  </div>

  <div class="usage" style="margin-top:20px">
    <h3>Plan Limits</h3>
    <div class="usage-grid" style="grid-template-columns:repeat(3,1fr)">
      <div class="usage-item"><div class="val">{limits.get('max_stores','Unlimited')}</div><div class="lbl">Max Stores</div></div>
      <div class="usage-item"><div class="val">{limits.get('max_users','Unlimited')}</div><div class="lbl">Max Users</div></div>
      <div class="usage-item"><div class="val">{limits.get('data_retention_days','Unlimited')}</div><div class="lbl">Data Retention (days)</div></div>
    </div>
  </div>

  <div class="footer">
    <p>GetMyPlan &mdash; AI-powered retail analytics &mdash; getmyplan.in</p>
    <p>This is a computer-generated invoice. No signature required.</p>
  </div>
</div>
</body></html>"""

    return StreamingResponse(
        io.BytesIO(html.encode()),
        media_type="text/html",
        headers={"Content-Disposition": f'inline; filename="invoice_{doc.get("invoice_number","")}.html"'},
    )


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    """Delete an invoice (admin only)."""
    tenant_id = user.get("tenant_id")
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Only admins can delete invoices")

    shared = get_shared_db()
    try:
        result = await shared.invoices.delete_one({"_id": ObjectId(invoice_id), "tenant_id": tenant_id})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid invoice ID")
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"success": True}
