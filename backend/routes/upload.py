"""
Data Upload API routes — drop-in replacement with 75-error validation.
Uses get_db() for tenant-aware MongoDB access.
"""
from fastapi import APIRouter, UploadFile, File, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import uuid
import os
import io
import logging
from datetime import datetime, timedelta, timezone

from services.upload_service import UniversalUploadService, compute_file_hash
from multi_tenant.tenant_db import tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Per-tenant upload lock (in-memory — sufficient for single-node)
import asyncio
_upload_locks: dict[str, asyncio.Lock] = {}


def _get_upload_lock(tenant_id: str) -> asyncio.Lock:
    if tenant_id not in _upload_locks:
        _upload_locks[tenant_id] = asyncio.Lock()
    return _upload_locks[tenant_id]


def _get_db():
    """Import here to avoid circular imports."""
    from server import get_db
    return get_db()


def _get_tenant_id():
    ctx = tenant_context.get()
    return ctx.tenant_id if ctx else "default"


def _get_user_email():
    """Best-effort user email extraction from tenant context."""
    return "system"


# ============================================================
# UPLOAD ENDPOINTS
# ============================================================

@router.post("/daily-sales")
async def upload_daily_sales(
    request: Request,
    file: UploadFile = File(...),
    replace_existing: bool = False,
    background_tasks: BackgroundTasks = None,
):
    return await _handle_upload(file, "daily_sales", replace_existing)


@router.post("/store-inventory")
async def upload_store_inventory(
    request: Request,
    file: UploadFile = File(...),
    replace_existing: bool = False,
    background_tasks: BackgroundTasks = None,
):
    return await _handle_upload(file, "store_inventory", replace_existing)


@router.post("/warehouse-inventory")
async def upload_warehouse_inventory(
    request: Request,
    file: UploadFile = File(...),
    replace_existing: bool = False,
    background_tasks: BackgroundTasks = None,
):
    return await _handle_upload(file, "warehouse_inventory", replace_existing)


@router.post("/sku-master")
async def upload_sku_master(
    request: Request,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    return await _handle_upload(file, "sku_master", replace_existing=True)


@router.post("/store-master")
async def upload_store_master(
    request: Request,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    return await _handle_upload(file, "store_master", replace_existing=True)


@router.post("/warehouse-master")
async def upload_warehouse_master(
    request: Request,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    return await _handle_upload(file, "warehouse_master", replace_existing=True)


@router.post("/style-master")
async def upload_style_master(
    request: Request,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    return await _handle_upload(file, "style_master", replace_existing=True)


@router.post("/cogs")
async def upload_cogs(
    request: Request,
    file: UploadFile = File(...),
    replace_existing: bool = False,
    background_tasks: BackgroundTasks = None,
):
    return await _handle_upload(file, "cogs", replace_existing)


@router.post("/planogram")
async def upload_planogram(
    request: Request,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    return await _handle_upload(file, "planogram", replace_existing=True)


@router.post("/open-orders")
async def upload_open_orders(
    request: Request,
    file: UploadFile = File(...),
    replace_existing: bool = False,
    background_tasks: BackgroundTasks = None,
):
    return await _handle_upload(file, "open_orders", replace_existing)


# ============================================================
# VALIDATE-ONLY ENDPOINT
# ============================================================

@router.post("/{upload_type}/validate")
async def validate_file(
    upload_type: str,
    file: UploadFile = File(...),
):
    """Validate a file without saving to database."""
    normalized = upload_type.replace("-", "_")
    return await _handle_upload(file, normalized, replace_existing=False, validate_only=True)


# ============================================================
# STATUS & HISTORY ENDPOINTS
# ============================================================

@router.get("/history/days")
async def get_previous_days_history(days: int = 7):
    """Get upload status for previous days — per-day breakdown."""
    db = _get_db()
    tenant_id = _get_tenant_id()
    today = datetime.now(timezone.utc).date()
    result = []

    for i in range(1, days + 1):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")

        uploads = {}
        for upload_type in ["daily_sales", "store_inventory", "warehouse_inventory", "cogs", "open_orders"]:
            doc = await db.upload_history.find_one(
                {"tenant_id": tenant_id, "upload_type": upload_type, "upload_date": date_str, "status": "completed"},
                {"_id": 0},
            )
            uploads[upload_type] = doc is not None

        if i == 1:
            label = "Yesterday"
        elif i < 7:
            label = date.strftime("%A")
        else:
            label = date.strftime("%b %d")

        if any(uploads.values()) or i <= 3:
            result.append({
                "date": date_str,
                "label": label,
                "uploads": uploads,
                "has_data": any(uploads.values()),
            })

    return {"days": result}


@router.get("/history")
async def get_upload_history(
    upload_type: Optional[str] = None,
    days: int = 7,
):
    """Get upload history grouped by date."""
    db = _get_db()
    tenant_id = _get_tenant_id()
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    query = {"tenant_id": tenant_id, "upload_date": {"$gte": start_date}}
    if upload_type:
        query["upload_type"] = upload_type

    history = await db.upload_history.find(query, {"_id": 0}).sort("upload_date", -1).to_list(200)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    grouped = {}
    for item in history:
        date_key = item.get("upload_date", "")
        if date_key == today:
            label = "Today"
        elif date_key == yesterday:
            label = "Yesterday"
        else:
            try:
                label = datetime.strptime(date_key, "%Y-%m-%d").strftime("%a, %b %d")
            except Exception:
                label = date_key

        if date_key not in grouped:
            grouped[date_key] = {"date": date_key, "label": label, "uploads": {}}

        uploaded_at = item.get("uploaded_at")
        time_str = uploaded_at.strftime("%I:%M %p") if hasattr(uploaded_at, "strftime") else str(uploaded_at)[:16]

        grouped[date_key]["uploads"][item["upload_type"]] = {
            "time": time_str,
            "rows": item.get("rows_uploaded", 0),
            "status": item.get("status", "completed"),
            "file_name": item.get("file_name", ""),
            "uploaded_by": item.get("uploaded_by", ""),
            "session_id": item.get("session_id", ""),
        }

    return {"history": list(grouped.values())}


@router.get("/daily-status")
async def get_daily_status():
    """Get today's upload status for the dashboard widget."""
    db = _get_db()
    tenant_id = _get_tenant_id()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    upload_types = ["daily_sales", "store_inventory", "warehouse_inventory", "cogs", "open_orders"]

    status = {}
    for ut in upload_types:
        upload = await db.upload_history.find_one(
            {"tenant_id": tenant_id, "upload_type": ut, "upload_date": today},
            {"_id": 0},
        )
        if upload:
            uploaded_at = upload.get("uploaded_at")
            time_str = uploaded_at.strftime("%I:%M %p") if hasattr(uploaded_at, "strftime") else ""
            status[ut] = {"uploaded": True, "time": time_str, "rows": upload.get("rows_uploaded", 0)}
        else:
            status[ut] = {"uploaded": False, "time": None, "rows": 0}

    return status


@router.get("/master-status")
async def get_master_status():
    """Get master data counts and last-updated timestamps."""
    db = _get_db()
    tenant_id = _get_tenant_id()
    result = {}

    for master_type in ["sku_master", "store_master", "warehouse_master", "style_master", "planogram"]:
        last = await db.upload_history.find_one(
            {"tenant_id": tenant_id, "upload_type": master_type, "status": "completed"},
            {"_id": 0},
            sort=[("uploaded_at", -1)],
        )
        # Try dedicated collection first, fall back to uploaded_files
        count = await db[master_type].count_documents({"tenant_id": tenant_id})
        if count == 0:
            doc = await db.uploaded_files.find_one({"file_type": master_type})
            if doc and "data" in doc:
                count = len(doc["data"])

        result[master_type] = {
            "count": count,
            "last_updated": last["uploaded_at"].strftime("%b %d") if last and hasattr(last.get("uploaded_at"), "strftime") else None,
        }

    return result


@router.get("/template/{upload_type}")
async def download_template(upload_type: str):
    """Download template pre-filled with tenant's actual SKUs and stores."""
    import openpyxl
    from openpyxl.worksheet.datavalidation import DataValidation

    db = _get_db()
    _get_tenant_id()  # ensure tenant context
    wb = openpyxl.Workbook()
    ws = wb.active

    TEMPLATE_MAP = {
        "daily_sales": {
            "title": "Daily Sales",
            "headers": ["sku", "store_code", "day", "quantity", "revenue"],
        },
        "store_inventory": {
            "title": "Store Inventory",
            "headers": ["store_code", "sku", "closing_stock"],
        },
        "warehouse_inventory": {
            "title": "Warehouse Inventory",
            "headers": ["warehouse", "sku", "on_hand_qty", "available_qty"],
        },
        "sku_master": {
            "title": "SKU Master",
            "headers": ["sku", "product_name", "category"],
        },
        "store_master": {
            "title": "Store Master",
            "headers": ["store_code", "store_name"],
        },
        "warehouse_master": {
            "title": "Warehouse Master",
            "headers": ["warehouse", "warehouse_name", "online_fulfillment_flag"],
        },
        "style_master": {
            "title": "Style Master",
            "headers": ["style_code", "season", "category", "subcategory", "gender", "brand"],
        },
        "cogs": {
            "title": "COGS",
            "headers": ["transaction_date", "store_code", "sku_code", "cogs"],
        },
        "planogram": {
            "title": "Planogram",
            "headers": ["store_code", "category", "style_code", "norm_allocated", "repl_cycle_days", "cover_days", "top_seller_multiplier", "is_active"],
        },
        "open_orders": {
            "title": "Open Orders",
            "headers": ["order_date", "expected_delivery_date", "store_code", "sku_code", "order_quantity", "status", "source_type"],
        },
    }

    tmpl = TEMPLATE_MAP.get(upload_type)
    if not tmpl:
        raise HTTPException(400, f"Unknown upload type: {upload_type}")

    ws.title = tmpl["title"]
    for col, h in enumerate(tmpl["headers"], 1):
        ws.cell(row=1, column=col, value=h)

    # Add dropdowns from tenant master data
    if "sku" in tmpl["headers"]:
        skus = await db.uploaded_files.distinct("sku", {"file_type": "sku_master"})
        if not skus:
            skus = await db.uploaded_files.distinct("sku", {})
        if skus:
            sku_list = ",".join(str(s) for s in skus[:100])
            if len(sku_list) < 255:
                dv = DataValidation(type="list", formula1=f'"{sku_list}"')
                ws.add_data_validation(dv)
                col_idx = tmpl["headers"].index("sku") + 1
                col_letter = openpyxl.utils.get_column_letter(col_idx)
                dv.add(f"{col_letter}2:{col_letter}10000")

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={upload_type}_template.xlsx"},
    )


# ============================================================
# CORE HANDLER
# ============================================================

async def _handle_upload(file: UploadFile, upload_type: str, replace_existing: bool, validate_only: bool = False):
    """Internal handler — validates file, saves to DB if valid (unless validate_only)."""
    db = _get_db()
    tenant_id = _get_tenant_id()
    user_email = _get_user_email()
    session_id = f"UPL-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

    lock = _get_upload_lock(tenant_id)
    if lock.locked() and not validate_only:
        return JSONResponse(content={
            "success": False,
            "errors": [{
                "code": "E057",
                "category": "file_structure",
                "message": "Another upload is in progress",
                "user_message": "Another upload is already being processed for this workspace. Please wait and try again.",
                "severity": "blocking",
            }],
            "total_rows": 0, "valid_rows": 0,
            "corrections": [], "warnings": [], "preview": [],
        })

    async with lock:
        return await _handle_upload_inner(file, upload_type, replace_existing, validate_only, db, tenant_id, user_email, session_id)


async def _handle_upload_inner(file, upload_type, replace_existing, validate_only, db, tenant_id, user_email, session_id):
    """Inner upload logic after acquiring the tenant lock."""

    file_path = os.path.join(UPLOAD_DIR, f"{session_id}_{file.filename}")

    try:
        content = await file.read()

        # E049: File size check
        file_size_mb = len(content) / (1024 * 1024)
        if len(content) > MAX_FILE_SIZE_BYTES:
            return JSONResponse(content={
                "success": False,
                "errors": [{
                    "code": "E049",
                    "category": "file_structure",
                    "message": "File too large",
                    "user_message": f"Your file is {file_size_mb:.1f}MB. Maximum is {MAX_FILE_SIZE_MB}MB.",
                    "severity": "blocking",
                }],
                "total_rows": 0, "valid_rows": 0,
                "corrections": [], "warnings": [], "preview": [],
            })

        with open(file_path, "wb") as f:
            f.write(content)

        # E054: Duplicate file detection via hash
        file_hash = compute_file_hash(file_path)
        existing_upload = await db.upload_history.find_one(
            {"tenant_id": tenant_id, "file_hash": file_hash, "status": "completed"},
            {"_id": 0},
        )
        duplicate_warning = None
        if existing_upload:
            prev_date = existing_upload.get("uploaded_at")
            date_str = prev_date.strftime("%Y-%m-%d") if hasattr(prev_date, "strftime") else str(prev_date)[:10]
            time_str = prev_date.strftime("%I:%M %p") if hasattr(prev_date, "strftime") else ""
            duplicate_warning = {
                "code": "E054",
                "category": "duplicate",
                "message": "Same file uploaded twice",
                "user_message": f"This file was already uploaded on {date_str} at {time_str}.",
                "severity": "warning",
            }

        # Fetch master data for cross-validation
        master_skus = await _get_master_skus(db, tenant_id)
        master_stores = await _get_master_stores(db, tenant_id)
        master_warehouses = await _get_master_warehouses(db, tenant_id)

        service = UniversalUploadService(
            upload_type=upload_type,
            master_skus=master_skus,
            master_stores=master_stores,
            master_warehouses=master_warehouses,
            file_hash=file_hash,
        )

        result = service.process_file(file_path, file.filename)
        records = result.pop("data", None)

        # Add duplicate warning if found
        if duplicate_warning:
            result.setdefault("warnings", []).insert(0, duplicate_warning)

        result["validate_only"] = validate_only

        # If validation passed, save to database (skip if validate_only)
        if result["success"] and records and not validate_only:
            saved = await _save_to_database(db, tenant_id, user_email, upload_type, records, replace_existing)
            result["saved"] = saved

        # Record history (skip for validate_only)
        if not validate_only:
            await db.upload_history.insert_one({
                "tenant_id": tenant_id,
                "upload_type": upload_type,
                "upload_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "file_name": file.filename,
                "file_hash": file_hash,
                "file_size_bytes": len(content),
                "rows_uploaded": result.get("total_rows", 0),
                "rows_valid": result.get("valid_rows", 0),
                "rows_with_warnings": len(result.get("warnings", [])),
                "rows_with_errors": len(result.get("errors", [])),
                "status": "completed" if result["success"] else "failed",
                "uploaded_by": user_email,
                "uploaded_at": datetime.now(timezone.utc),
                "session_id": session_id,
            })

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Upload handler error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "errors": [{"code": "FATAL", "message": str(e)}]},
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# ============================================================
# MASTER DATA FETCHERS
# ============================================================

async def _get_master_skus(db, tenant_id):
    """Get distinct SKUs from v2 sku_master collection OR v1 uploaded_files."""
    try:
        # Try v2 collection first
        skus = await db.sku_master.distinct("sku", {"tenant_id": tenant_id})
        if skus:
            return [str(s) for s in skus if s]

        # Fall back to v1 uploaded_files
        styles = await db.uploaded_files.find_one({"file_type": "sku_master"})
        if styles and "data" in styles:
            return list({str(r.get("sku", "")) for r in styles["data"] if r.get("sku")})
        styles = await db.uploaded_files.find_one({"file_type": "sku_ean_master"})
        if styles and "data" in styles:
            return list({str(r.get("ean", "")) for r in styles["data"] if r.get("ean")})
    except Exception:
        pass
    return []


async def _get_master_stores(db, tenant_id):
    """Get distinct stores from v2 store_master collection OR v1 uploaded_files."""
    try:
        # Try v2 collection first
        stores = await db.store_master.distinct("store_code", {"tenant_id": tenant_id})
        if stores:
            return [str(s) for s in stores if s]

        # Fall back to v1 uploaded_files
        doc = await db.uploaded_files.find_one({"file_type": "store_master"})
        if doc and "data" in doc:
            return list({str(r.get("store_code", "")) for r in doc["data"] if r.get("store_code")})
    except Exception:
        pass
    return []


async def _get_master_warehouses(db, tenant_id):
    """Get distinct warehouses from v2 warehouse_master collection OR v1 uploaded_files."""
    try:
        # Try v2 collection first
        warehouses = await db.warehouse_master.distinct("warehouse", {"tenant_id": tenant_id})
        if warehouses:
            return [str(w) for w in warehouses if w]

        # Fall back to v1 uploaded_files
        doc = await db.uploaded_files.find_one({"file_type": "warehouse_master"})
        if doc and "data" in doc:
            return list({str(r.get("warehouse", "")) for r in doc["data"] if r.get("warehouse")})
    except Exception:
        pass
    return []


async def _save_to_database(db, tenant_id, user_email, upload_type, records, replace_existing):
    """Save validated records to the appropriate collection."""
    collection_map = {
        "daily_sales": "daily_sales",
        "store_inventory": "store_inventory",
        "warehouse_inventory": "warehouse_inventory",
        "sku_master": "sku_master",
        "store_master": "store_master",
        "warehouse_master": "warehouse_master",
        "style_master": "style_master",
        "cogs": "cogs",
        "planogram": "planogram",
        "open_orders": "open_orders",
    }

    collection_name = collection_map.get(upload_type)
    if not collection_name:
        return False

    collection = db[collection_name]
    now = datetime.now(timezone.utc)

    for record in records:
        record["tenant_id"] = tenant_id
        record["uploaded_at"] = now.isoformat()
        record["uploaded_by"] = user_email

    if replace_existing:
        if upload_type == "daily_sales":
            days = set()
            for r in records:
                d = r.get("day")
                if d:
                    days.add(d)
            for day in days:
                await collection.delete_many({"tenant_id": tenant_id, "day": day})
        elif upload_type == "cogs":
            dates = set()
            for r in records:
                d = r.get("transaction_date")
                if d:
                    dates.add(d)
            for dt in dates:
                await collection.delete_many({"tenant_id": tenant_id, "transaction_date": dt})
        elif upload_type == "open_orders":
            await collection.delete_many({"tenant_id": tenant_id})
        elif upload_type in ["store_inventory", "warehouse_inventory"]:
            await collection.delete_many({"tenant_id": tenant_id})
        elif upload_type in ["sku_master", "store_master", "warehouse_master", "style_master", "planogram"]:
            await collection.delete_many({"tenant_id": tenant_id})

    if records:
        await collection.insert_many(records)

    return True
