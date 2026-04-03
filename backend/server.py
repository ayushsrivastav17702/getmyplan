from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta, date
import pandas as pd
import numpy as np
import random
import io
import asyncio
import chardet
from emergentintegrations.llm.chat import LlmChat, UserMessage
from sftp import sftp_service, sftp_scheduler
from routes.core_logic import router as core_logic_router, init_core_logic
from routes.replenishment import router as replenishment_router, init_replenishment
from routes.doh_analysis import router as doh_router, init_doh
from routes.planogram import router as planogram_router, init_planogram
from routes.bi_dashboard import router as bi_router, init_bi
from routes.sftp_routes import router as sftp_ext_router, init_sftp_routes
from routes.warehouse import router as warehouse_router, init_warehouse

# Multi-tenant imports
from multi_tenant import (
    TenantMiddleware,
    auth_router,
    tenant_router,
    user_router,
    seed_rbac,
    get_shared_db,
    get_current_tenant,
    tenant_context,
)
from multi_tenant.tenant_db import (
    get_mongo_client as mt_get_mongo_client,
    get_tenant_db as mt_get_tenant_db,
    ensure_shared_indexes,
    SHARED_DB_NAME,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection — kept for backward compat; tenant-aware helper below
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
_default_db_name = os.environ['DB_NAME']
db = client[_default_db_name]   # default DB (used when no tenant context)


def get_db():
    """Return the tenant-specific DB when a tenant context exists, else default."""
    ctx = tenant_context.get()
    if ctx:
        return client[ctx.db_name]
    return db


# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== MODELS ====================

class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class FileUploadResponse(BaseModel):
    file_type: str
    rows: int
    columns: List[str]
    valid: bool
    errors: List[str]
    warnings: List[str] = []
    preview: List[Dict[str, Any]]
    duplicates_removed: int = 0
    encoding: Optional[str] = None

class AnalysisConfig(BaseModel):
    # Module toggles
    noos_enabled: bool = True
    ros_enabled: bool = True
    size_gap_enabled: bool = True
    lifecycle_enabled: bool = True
    replenishment_enabled: bool = True
    # Date range
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    # Parameters (CONF-01 to CONF-05)
    min_shelf_life_days: int = 30
    pivotal_size_threshold: int = 75  # PSA Benchmark (0-100%)
    cover_days: int = 7               # Cover days for replenishment
    ros_period: int = 30              # ROS calculation period (days)
    ideal_doh: int = 9                # Ideal Days on Hand
    topseller_x_factor: float = 2.0   # Topseller revenue multiplier
    lead_time_days: int = 14          # Lead time for replenishment
    safety_days: int = 7              # Safety stock days
    true_ros_recent_weight: float = 0.7   # TrueROS recent period weight
    true_ros_historical_weight: float = 0.3  # TrueROS historical period weight
    selected_seasons: List[str] = []

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str


# ==================== FILTER PRESET MODELS ====================

class FilterPresetCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    tags: List[str] = []
    page_type: str  # "gap-analysis", "core-logics", "bi-dashboards"
    filters: Dict[str, Any]
    is_favorite: bool = False

class FilterPreset(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    tags: List[str] = []
    page_type: str
    filters: Dict[str, Any]
    is_favorite: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== REQUIRED COLUMNS ====================

REQUIRED_COLUMNS = {
    'style_master': ['style_code', 'season', 'category', 'subcategory', 'gender', 'brand'],
    'sku_ean_master': ['ean', 'style', 'size', 'mrp'],
    'store_master': ['channel', 'store', 'store_code', 'city', 'region'],
    'warehouse_master': ['warehouse', 'online_fulfillment_flag'],
    'daily_sales': ['channel', 'store_code', 'sku', 'day', 'quantity', 'revenue'],
    'store_inventory': ['channel', 'store_code', 'ean', 'day', 'quantity'],
    'warehouse_inventory': ['sku', 'warehouse', 'quantity', 'day']
}

# Data type and range validation rules for known columns
COLUMN_RULES = {
    'quantity': {'type': 'numeric', 'min': 0, 'nullable': False},
    'revenue':  {'type': 'numeric', 'min': 0, 'nullable': False},
    'mrp':      {'type': 'numeric', 'min': 0, 'nullable': False},
    'day':      {'type': 'date', 'max_date': 'today', 'nullable': False},
}

# Unique-key columns used for deduplication
DEDUP_KEYS = {
    'daily_sales': ['channel', 'store_code', 'sku', 'day'],
    'store_inventory': ['channel', 'store_code', 'ean', 'day'],
    'warehouse_inventory': ['sku', 'warehouse', 'day'],
    'style_master': ['style_code'],
    'sku_ean_master': ['ean'],
    'store_master': ['store_code'],
    'warehouse_master': ['warehouse'],
}

MAX_UPLOAD_SIZE_MB = 100
MAX_UPLOAD_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Simple per-file-type lock to prevent concurrent overwrites
_upload_locks: Dict[str, asyncio.Lock] = {}

def _get_upload_lock(file_type: str) -> asyncio.Lock:
    if file_type not in _upload_locks:
        _upload_locks[file_type] = asyncio.Lock()
    return _upload_locks[file_type]


# ==================== HELPER FUNCTIONS ====================

def _detect_encoding(raw_bytes: bytes) -> str:
    """Detect file encoding using chardet."""
    result = chardet.detect(raw_bytes[:32768])  # sample first 32KB
    enc = (result.get('encoding') or 'utf-8').lower()
    ALIASES = {'ascii': 'utf-8', 'windows-1252': 'cp1252'}
    enc = ALIASES.get(enc, enc)
    # Handle UTF-8 BOM: if file starts with BOM bytes, use utf-8-sig to strip it
    if enc == 'utf-8' and raw_bytes[:3] == b'\xef\xbb\xbf':
        enc = 'utf-8-sig'
    return enc


def validate_file(df: pd.DataFrame, file_type: str) -> Dict[str, Any]:
    """Validate uploaded file: columns, types, nulls, ranges, dates, duplicates."""
    errors: List[str] = []
    warnings: List[str] = []

    # --- 1. Normalize columns ---
    df.columns = [col.lower().strip() for col in df.columns]

    # --- 2. Required columns check ---
    required = REQUIRED_COLUMNS.get(file_type, [])
    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")

    if len(df) == 0:
        errors.append("File is empty — no data rows found")

    if errors:
        return {'valid': False, 'errors': errors, 'warnings': warnings,
                'columns': list(df.columns), 'rows': len(df),
                'duplicates_removed': 0}

    # --- 3. Deduplication ---
    dedup_cols = DEDUP_KEYS.get(file_type)
    dupes_removed = 0
    if dedup_cols:
        valid_dedup = [c for c in dedup_cols if c in df.columns]
        if valid_dedup:
            before = len(df)
            df.drop_duplicates(subset=valid_dedup, keep='last', inplace=True)
            df.reset_index(drop=True, inplace=True)
            dupes_removed = before - len(df)
            if dupes_removed:
                warnings.append(f"Removed {dupes_removed} duplicate rows")

    # --- 4. Per-column validation (type, null, range, date) ---
    row_errors: List[str] = []
    for col_name, rules in COLUMN_RULES.items():
        if col_name not in df.columns:
            continue

        col = df[col_name]

        # Null check
        if not rules.get('nullable', True):
            null_mask = col.isna() | (col.astype(str).str.strip() == '')
            null_count = int(null_mask.sum())
            if null_count > 0:
                first_rows = df.index[null_mask][:3].tolist()
                row_nums = ', '.join(str(r + 2) for r in first_rows)
                suffix = f" (and {null_count - 3} more)" if null_count > 3 else ""
                row_errors.append(
                    f"Column '{col_name}' has {null_count} empty values — rows: {row_nums}{suffix}")

        # Numeric type + range
        if rules['type'] == 'numeric':
            numeric_col = pd.to_numeric(col, errors='coerce')
            bad_mask = col.notna() & numeric_col.isna()
            bad_count = int(bad_mask.sum())
            if bad_count:
                first_bad = df.index[bad_mask][:3].tolist()
                row_nums = ', '.join(str(r + 2) for r in first_bad)
                row_errors.append(
                    f"Column '{col_name}' has {bad_count} non-numeric values — rows: {row_nums}")

            if 'min' in rules:
                below = numeric_col.dropna() < rules['min']
                below_count = int(below.sum())
                if below_count:
                    first_below = df.index[numeric_col.fillna(0) < rules['min']][:3].tolist()
                    row_nums = ', '.join(str(r + 2) for r in first_below)
                    row_errors.append(
                        f"Column '{col_name}' has {below_count} values below {rules['min']} — rows: {row_nums}")

        # Date type + future-date check
        if rules['type'] == 'date':
            date_col = pd.to_datetime(col, errors='coerce')
            bad_dates = col.notna() & date_col.isna()
            bad_count = int(bad_dates.sum())
            if bad_count:
                first_bad = df.index[bad_dates][:3].tolist()
                row_nums = ', '.join(str(r + 2) for r in first_bad)
                row_errors.append(
                    f"Column '{col_name}' has {bad_count} invalid date values — rows: {row_nums}")

            if rules.get('max_date') == 'today':
                today = pd.Timestamp(date.today())
                future = date_col.dropna() > today
                fut_count = int(future.sum())
                if fut_count:
                    first_fut = df.index[date_col > today][:3].tolist()
                    row_nums = ', '.join(str(r + 2) for r in first_fut)
                    row_errors.append(
                        f"Column '{col_name}' has {fut_count} future dates — rows: {row_nums}")

    if row_errors:
        errors.extend(row_errors)

    # Extra columns warning
    known = set(required)
    extra = [c for c in df.columns if c not in known]
    if extra:
        warnings.append(f"Extra columns ignored: {', '.join(extra)}")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'columns': list(df.columns),
        'rows': len(df),
        'duplicates_removed': dupes_removed,
    }


async def get_cached_data(file_type: str) -> Optional[pd.DataFrame]:
    """Retrieve cached data from tenant-aware MongoDB"""
    tdb = get_db()
    doc = await tdb.uploaded_files.find_one({"file_type": file_type})
    if doc and 'data' in doc:
        return pd.DataFrame(doc['data'])
    return None


async def cache_data(file_type: str, df: pd.DataFrame, validation: Dict):
    """Cache uploaded data to tenant-aware MongoDB"""
    tdb = get_db()
    data = df.to_dict('records')
    await tdb.uploaded_files.update_one(
        {"file_type": file_type},
        {
            "$set": {
                "file_type": file_type,
                "data": data,
                "columns": list(df.columns),
                "rows": len(df),
                "validation": validation,
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )


# ==================== ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "Fashion Retail Gap Analysis API"}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await get_db().status_checks.insert_one(doc)
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await get_db().status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks


# ==================== FILE UPLOAD ====================

@api_router.post("/upload/{file_type}", response_model=FileUploadResponse)
async def upload_file(file_type: str, file: UploadFile = File(...)):
    """Upload and validate a data file with comprehensive checks."""
    if file_type not in REQUIRED_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Unknown file type: {file_type}")

    # Acquire per-file-type lock to prevent concurrent overwrites
    lock = _get_upload_lock(file_type)
    if lock.locked():
        raise HTTPException(status_code=409,
                            detail=f"An upload for '{file_type}' is already in progress. Please wait.")

    async with lock:
        try:
            contents = await file.read()

            # --- File size check ---
            if len(contents) > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large ({len(contents)/(1024*1024):.1f} MB). "
                           f"Maximum allowed is {MAX_UPLOAD_SIZE_MB} MB.")

            # --- Extension check ---
            fname = (file.filename or "").lower()
            if not (fname.endswith('.csv') or fname.endswith('.xlsx') or fname.endswith('.xls')):
                raise HTTPException(status_code=400,
                                    detail="Unsupported file format. Accepted: .csv, .xlsx, .xls")

            # --- Read into DataFrame with encoding detection ---
            detected_encoding = None
            if fname.endswith('.csv'):
                detected_encoding = _detect_encoding(contents)
                try:
                    df = pd.read_csv(io.BytesIO(contents), encoding=detected_encoding)
                except Exception:
                    # Fallback to latin1 which never throws
                    detected_encoding = 'latin1'
                    df = pd.read_csv(io.BytesIO(contents), encoding='latin1')
            else:
                df = pd.read_excel(io.BytesIO(contents))

            # --- Validate ---
            validation = validate_file(df, file_type)

            if validation['valid']:
                await cache_data(file_type, df, validation)

            # Log to upload history
            await get_db().upload_history.insert_one({
                "file_type": file_type,
                "file_name": file.filename,
                "status": "success" if validation['valid'] else "failed",
                "rows_processed": validation['rows'],
                "columns": validation['columns'],
                "errors": validation['errors'],
                "warnings": validation.get('warnings', []),
                "duplicates_removed": validation.get('duplicates_removed', 0),
                "encoding": detected_encoding,
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            })

            preview = df.head(5).fillna('').to_dict('records')

            return FileUploadResponse(
                file_type=file_type,
                rows=validation['rows'],
                columns=validation['columns'],
                valid=validation['valid'],
                errors=validation['errors'],
                warnings=validation.get('warnings', []),
                preview=preview,
                duplicates_removed=validation.get('duplicates_removed', 0),
                encoding=detected_encoding,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            await get_db().upload_history.insert_one({
                "file_type": file_type,
                "file_name": file.filename if file else "unknown",
                "status": "failed",
                "rows_processed": 0,
                "errors": [str(e)],
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            })
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@api_router.get("/upload/status")
async def get_upload_status():
    """Get status of all uploaded files"""
    files = await get_db().uploaded_files.find({}, {"_id": 0, "data": 0}).to_list(100)
    status = {}
    for f in files:
        status[f['file_type']] = {
            'uploaded': True,
            'rows': f.get('rows', 0),
            'columns': f.get('columns', []),
            'uploaded_at': f.get('uploaded_at'),
            'valid': f.get('validation', {}).get('valid', False)
        }
    
    for file_type in REQUIRED_COLUMNS.keys():
        if file_type not in status:
            status[file_type] = {'uploaded': False, 'rows': 0, 'columns': [], 'valid': False}
    
    return status


@api_router.delete("/upload/{file_type}")
async def delete_file(file_type: str):
    """Delete an uploaded file"""
    await get_db().uploaded_files.delete_one({"file_type": file_type})
    return {"message": f"Deleted {file_type}"}


@api_router.delete("/upload/all")
async def delete_all_files():
    """Delete all uploaded files"""
    await get_db().uploaded_files.delete_many({})
    return {"message": "All files deleted"}


@api_router.get("/upload/history")
async def get_upload_history(limit: int = 50):
    """Get upload history log"""
    history = await get_db().upload_history.find(
        {}, {"_id": 0}
    ).sort("uploaded_at", -1).to_list(limit)
    return history


@api_router.get("/upload/template/{file_type}")
async def get_template(file_type: str):
    """Get CSV template for a file type"""
    if file_type not in REQUIRED_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Unknown file type: {file_type}")
    
    columns = REQUIRED_COLUMNS[file_type]
    csv_content = ",".join(columns) + "\n"
    
    # Add example row
    examples = {
        "style_master": "ST0001,Brand_A,Shirts,Male,SS26",
        "sku_ean_master": "1000001,ST0001,M,1499",
        "store_master": "STORE001,Store Name,Mall,North,Metro",
        "warehouse_master": "WH001,Central Warehouse,North,Yes",
        "daily_sales": "STORE001,1000001,2026-01-15,5,7495,Online",
        "store_inventory": "STORE001,1000001,2026-01-15,25",
        "warehouse_inventory": "WH001,1000001,2026-01-15,500",
    }
    csv_content += examples.get(file_type, ",".join(["example"] * len(columns)))
    
    from starlette.responses import Response
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={file_type}_template.csv"}
    )


# ==================== CONFIGURATION ====================

@api_router.post("/config")
async def save_config(config: AnalysisConfig):
    """Save analysis configuration with validation."""
    errors = []
    if not (0 <= config.pivotal_size_threshold <= 100):
        errors.append("PSA Benchmark (pivotal_size_threshold) must be between 0 and 100")
    if config.cover_days < 1 or config.cover_days > 90:
        errors.append("Cover Days must be between 1 and 90")
    if config.ros_period < 7 or config.ros_period > 365:
        errors.append("ROS Period must be between 7 and 365")
    if config.ideal_doh < 1 or config.ideal_doh > 90:
        errors.append("Ideal DOH must be between 1 and 90")
    if config.topseller_x_factor < 0.5 or config.topseller_x_factor > 10:
        errors.append("Topseller X Factor must be between 0.5 and 10")
    if config.lead_time_days < 1 or config.lead_time_days > 90:
        errors.append("Lead Time Days must be between 1 and 90")
    if config.safety_days < 0 or config.safety_days > 30:
        errors.append("Safety Days must be between 0 and 30")
    if config.min_shelf_life_days < 1 or config.min_shelf_life_days > 365:
        errors.append("Min Shelf Life Days must be between 1 and 365")
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    # Force integer on cover_days (CONF-08)
    config.cover_days = int(config.cover_days)

    await get_db().analysis_config.update_one(
        {"_id": "main"},
        {"$set": config.model_dump()},
        upsert=True
    )
    return {"message": "Configuration saved"}


# ==================== STORE CLASSIFICATION CRUD ====================

@api_router.get("/config/store-classes")
async def list_store_classes():
    """List all store classes ordered by priority."""
    classes = await get_db().store_classes.find({}, {"_id": 0}).sort("priority", 1).to_list(100)
    return {"classes": classes}

@api_router.post("/config/store-classes")
async def create_store_class(body: Dict[str, Any]):
    """Create a new store class."""
    code = body.get("code", "").strip().upper()
    name = body.get("name", "").strip()
    priority = int(body.get("priority", 99))
    if not code or not name:
        raise HTTPException(400, "code and name are required")
    existing = await get_db().store_classes.find_one({"code": code})
    if existing:
        raise HTTPException(400, f"Store class '{code}' already exists")
    await get_db().store_classes.insert_one({
        "code": code, "name": name, "priority": priority,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"message": f"Store class '{code}' created"}

@api_router.put("/config/store-classes/{code}")
async def update_store_class(code: str, body: Dict[str, Any]):
    """Edit an existing store class."""
    update_fields = {}
    if "name" in body:
        update_fields["name"] = body["name"].strip()
    if "priority" in body:
        update_fields["priority"] = int(body["priority"])
    if not update_fields:
        raise HTTPException(400, "Nothing to update")
    result = await get_db().store_classes.update_one({"code": code.upper()}, {"$set": update_fields})
    if result.matched_count == 0:
        raise HTTPException(404, f"Store class '{code}' not found")
    return {"message": f"Store class '{code}' updated"}

@api_router.delete("/config/store-classes/{code}")
async def delete_store_class(code: str):
    """Delete a store class if no stores assigned."""
    # Check if any store uses this class
    stores_using = await get_db().store_class_assignments.count_documents({"class_code": code.upper()})
    if stores_using > 0:
        raise HTTPException(400, f"Cannot delete: {stores_using} stores assigned to class '{code}'")
    result = await get_db().store_classes.delete_one({"code": code.upper()})
    if result.deleted_count == 0:
        raise HTTPException(404, f"Store class '{code}' not found")
    return {"message": f"Store class '{code}' deleted"}

@api_router.post("/config/store-classes/{code}/assign")
async def assign_stores_to_class(code: str, body: Dict[str, Any]):
    """Assign store codes to a class."""
    store_codes = body.get("store_codes", [])
    if not store_codes:
        raise HTTPException(400, "store_codes list required")
    cls = await get_db().store_classes.find_one({"code": code.upper()})
    if not cls:
        raise HTTPException(404, f"Store class '{code}' not found")
    for sc in store_codes:
        await get_db().store_class_assignments.update_one(
            {"store_code": sc},
            {"$set": {"store_code": sc, "class_code": code.upper(), "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
    return {"message": f"{len(store_codes)} stores assigned to class '{code}'"}

@api_router.get("/config/store-classes/assignments")
async def list_store_class_assignments():
    """List all store-to-class assignments."""
    assignments = await get_db().store_class_assignments.find({}, {"_id": 0}).to_list(5000)
    return {"assignments": assignments}


# ==================== CATEGORY HIERARCHY CRUD ====================

@api_router.get("/config/categories")
async def list_categories():
    """List all categories with hierarchy."""
    cats = await get_db().categories.find({}, {"_id": 0}).sort("name", 1).to_list(500)
    return {"categories": cats}

@api_router.post("/config/categories")
async def create_category(body: Dict[str, Any]):
    """Create a new category."""
    code = body.get("code", "").strip().upper()
    name = body.get("name", "").strip()
    parent = body.get("parent", None)
    if not code or not name:
        raise HTTPException(400, "code and name are required")
    existing = await get_db().categories.find_one({"code": code})
    if existing:
        raise HTTPException(400, f"Category '{code}' already exists")
    if parent:
        parent_doc = await get_db().categories.find_one({"code": parent.strip().upper()})
        if not parent_doc:
            raise HTTPException(400, f"Parent category '{parent}' not found")
    await get_db().categories.insert_one({
        "code": code, "name": name, "parent": parent.strip().upper() if parent else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"message": f"Category '{name}' created"}

@api_router.put("/config/categories/{code}")
async def update_category(code: str, body: Dict[str, Any]):
    """Edit a category."""
    update_fields = {}
    if "name" in body:
        update_fields["name"] = body["name"].strip()
    if "parent" in body:
        update_fields["parent"] = body["parent"].strip().upper() if body["parent"] else None
    if not update_fields:
        raise HTTPException(400, "Nothing to update")
    result = await get_db().categories.update_one({"code": code.upper()}, {"$set": update_fields})
    if result.matched_count == 0:
        raise HTTPException(404, f"Category '{code}' not found")
    return {"message": f"Category '{code}' updated"}

@api_router.delete("/config/categories/{code}")
async def delete_category(code: str):
    """Delete a category if no styles assigned and no children."""
    # Check children
    children = await get_db().categories.count_documents({"parent": code.upper()})
    if children > 0:
        raise HTTPException(400, f"Cannot delete: category has {children} child categories")
    # Check if any style uses this category (from style_master uploaded data)
    style_file = await get_db().uploaded_files.find_one({"file_type": "style_master"})
    if style_file and "data" in style_file:
        used = sum(1 for s in style_file["data"] if s.get("category", "").upper() == code.upper())
        if used > 0:
            raise HTTPException(400, f"Cannot delete: {used} styles assigned to category '{code}'")
    result = await get_db().categories.delete_one({"code": code.upper()})
    if result.deleted_count == 0:
        raise HTTPException(404, f"Category '{code}' not found")
    return {"message": f"Category '{code}' deleted"}


@api_router.get("/config")
async def get_config():
    """Get analysis configuration"""
    config = await get_db().analysis_config.find_one({"_id": "main"}, {"_id": 0})
    if not config:
        return AnalysisConfig().model_dump()
    return config


# ==================== FILTER PRESETS ====================

@api_router.post("/presets", response_model=FilterPreset)
async def create_preset(preset: FilterPresetCreate):
    """Create a new team filter preset"""
    preset_obj = FilterPreset(
        name=preset.name,
        description=preset.description,
        tags=preset.tags,
        page_type=preset.page_type,
        filters=preset.filters,
        is_favorite=preset.is_favorite
    )
    doc = preset_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await get_db().filter_presets.insert_one(doc)
    return preset_obj


@api_router.get("/presets")
async def get_presets(page_type: str = None):
    """Get all team filter presets, optionally filtered by page type"""
    query = {}
    if page_type:
        query['page_type'] = page_type
    
    presets = await get_db().filter_presets.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Convert datetime strings back
    for preset in presets:
        if isinstance(preset.get('created_at'), str):
            preset['created_at'] = datetime.fromisoformat(preset['created_at'])
        if isinstance(preset.get('updated_at'), str):
            preset['updated_at'] = datetime.fromisoformat(preset['updated_at'])
    
    return presets


@api_router.get("/presets/tags/all")
async def get_all_tags():
    """Get all unique tags used in presets"""
    presets = await get_db().filter_presets.find({}, {"tags": 1, "_id": 0}).to_list(1000)
    all_tags = set()
    for preset in presets:
        all_tags.update(preset.get('tags', []))
    return sorted(list(all_tags))


@api_router.get("/presets/export")
async def export_presets(page_type: str = None):
    """Export presets as JSON for sharing"""
    query = {}
    if page_type:
        query['page_type'] = page_type
    presets = await get_db().filter_presets.find(query, {"_id": 0}).to_list(1000)
    return {"presets": presets, "exported_at": datetime.now(timezone.utc).isoformat(), "page_type": page_type}


class PresetImport(BaseModel):
    presets: List[Dict[str, Any]]


@api_router.post("/presets/import")
async def import_presets(data: PresetImport):
    """Import presets from JSON"""
    imported = 0
    for preset_data in data.presets:
        preset_data.pop('_id', None)
        if 'id' not in preset_data:
            preset_data['id'] = str(uuid.uuid4())
        else:
            existing = await get_db().filter_presets.find_one({"id": preset_data['id']})
            if existing:
                preset_data['id'] = str(uuid.uuid4())
        preset_data['created_at'] = preset_data.get('created_at', datetime.now(timezone.utc).isoformat())
        preset_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        await get_db().filter_presets.insert_one(preset_data)
        imported += 1
    return {"message": f"Imported {imported} presets", "imported": imported}


@api_router.get("/presets/{preset_id}")
async def get_preset(preset_id: str):
    """Get a specific preset by ID"""
    preset = await get_db().filter_presets.find_one({"id": preset_id}, {"_id": 0})
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset


@api_router.put("/presets/{preset_id}")
async def update_preset(preset_id: str, preset: FilterPresetCreate):
    """Update an existing preset"""
    existing = await get_db().filter_presets.find_one({"id": preset_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    update_data = preset.model_dump()
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await get_db().filter_presets.update_one(
        {"id": preset_id},
        {"$set": update_data}
    )
    return {"message": "Preset updated", "id": preset_id}


@api_router.patch("/presets/{preset_id}/favorite")
async def toggle_preset_favorite(preset_id: str):
    """Toggle favorite status of a preset"""
    preset = await get_db().filter_presets.find_one({"id": preset_id})
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    new_favorite = not preset.get('is_favorite', False)
    await get_db().filter_presets.update_one(
        {"id": preset_id},
        {"$set": {"is_favorite": new_favorite, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Favorite toggled", "is_favorite": new_favorite}


@api_router.delete("/presets/{preset_id}")
async def delete_preset(preset_id: str):
    """Delete a preset"""
    result = await get_db().filter_presets.delete_one({"id": preset_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Preset not found")
    return {"message": "Preset deleted"}


# ==================== ANALYTICS ====================

@api_router.get("/analytics/filter-options")
async def get_filter_options():
    """Get available filter options from uploaded data"""
    options = {
        "categories": [],
        "channels": [],
        "regions": [],
        "storeClasses": [],
        "dateRange": {"min": None, "max": None}
    }
    
    # Get categories from style master
    style_df = await get_cached_data('style_master')
    if style_df is not None and 'category' in style_df.columns:
        options['categories'] = sorted(style_df['category'].dropna().unique().tolist())
    
    # Get channels and regions from store master
    store_df = await get_cached_data('store_master')
    if store_df is not None:
        if 'channel' in store_df.columns:
            options['channels'] = sorted(store_df['channel'].dropna().unique().tolist())
        if 'region' in store_df.columns:
            options['regions'] = sorted(store_df['region'].dropna().unique().tolist())
    
    # Get store classes
    store_classes = await get_db().store_classes.find({}, {"_id": 0}).sort("priority", 1).to_list(100)
    options['storeClasses'] = [{"code": c["code"], "name": c["name"]} for c in store_classes]

    # Get channels from daily sales as fallback
    sales_df = await get_cached_data('daily_sales')
    if sales_df is not None:
        if 'channel' in sales_df.columns and not options['channels']:
            options['channels'] = sorted(sales_df['channel'].dropna().unique().tolist())
        if 'day' in sales_df.columns:
            sales_df['day'] = pd.to_datetime(sales_df['day'])
            options['dateRange'] = {
                'min': sales_df['day'].min().isoformat() if not pd.isna(sales_df['day'].min()) else None,
                'max': sales_df['day'].max().isoformat() if not pd.isna(sales_df['day'].max()) else None
            }
    
    return options


def apply_date_filter(df: pd.DataFrame, start_date: str = None, end_date: str = None, date_col: str = 'day') -> pd.DataFrame:
    """Apply date range filter to dataframe"""
    if date_col not in df.columns:
        return df
    
    df[date_col] = pd.to_datetime(df[date_col])
    
    if start_date:
        df = df[df[date_col] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df[date_col] <= pd.to_datetime(end_date)]
    
    return df


def apply_category_filter(df: pd.DataFrame, categories: List[str], style_df: pd.DataFrame = None) -> pd.DataFrame:
    """Apply category filter - requires joining with style master"""
    if not categories or style_df is None:
        return df
    
    if 'category' in df.columns:
        return df[df['category'].isin(categories)]
    
    # If we have style column, join with style master
    if 'style' in df.columns and 'style_code' in style_df.columns:
        filtered_styles = style_df[style_df['category'].isin(categories)]['style_code'].tolist()
        return df[df['style'].isin(filtered_styles)]
    
    return df


def apply_channel_filter(df: pd.DataFrame, channels: List[str]) -> pd.DataFrame:
    """Apply channel filter"""
    if not channels or 'channel' not in df.columns:
        return df
    return df[df['channel'].isin(channels)]


def apply_region_filter(df: pd.DataFrame, regions: List[str], store_df: pd.DataFrame = None) -> pd.DataFrame:
    """Apply region filter - may require joining with store master"""
    if not regions:
        return df
    
    if 'region' in df.columns:
        return df[df['region'].isin(regions)]
    
    # If we have store_code, join with store master
    if store_df is not None and 'store_code' in df.columns and 'region' in store_df.columns:
        filtered_stores = store_df[store_df['region'].isin(regions)]['store_code'].tolist()
        return df[df['store_code'].isin(filtered_stores)]
    
    return df


@api_router.get("/analytics/overview")
async def get_analytics_overview():
    """Get quick overview stats from uploaded data"""
    overview = {
        "total_styles": 0,
        "total_stores": 0,
        "total_skus": 0,
        "total_warehouses": 0,
        "sales_records": 0,
        "date_range": {"start": None, "end": None}
    }
    
    # Style Master
    style_df = await get_cached_data('style_master')
    if style_df is not None:
        overview['total_styles'] = len(style_df)
    
    # Store Master
    store_df = await get_cached_data('store_master')
    if store_df is not None:
        overview['total_stores'] = len(store_df)
    
    # SKU EAN Master
    sku_df = await get_cached_data('sku_ean_master')
    if sku_df is not None:
        overview['total_skus'] = len(sku_df)
    
    # Warehouse Master
    wh_df = await get_cached_data('warehouse_master')
    if wh_df is not None:
        overview['total_warehouses'] = len(wh_df)
    
    # Daily Sales
    sales_df = await get_cached_data('daily_sales')
    if sales_df is not None:
        overview['sales_records'] = len(sales_df)
        if 'day' in sales_df.columns:
            sales_df['day'] = pd.to_datetime(sales_df['day'])
            overview['date_range'] = {
                'start': sales_df['day'].min().isoformat() if not pd.isna(sales_df['day'].min()) else None,
                'end': sales_df['day'].max().isoformat() if not pd.isna(sales_df['day'].max()) else None
            }
    
    return overview


@api_router.get("/analytics/stock-out")
async def get_stock_out_analysis(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None
):
    """
    PRD Stock-Out Analysis.
    Stock-out: SOH = 0 AND Last 30 Days ROS > 0
    Daily Sales Loss: ((ROS x 1) - SOH) x ASP
    Severity: LostSales x Duration x Importance
    """
    sales_df = await get_cached_data('daily_sales')
    inventory_df = await get_cached_data('store_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    style_df = await get_cached_data('style_master')
    store_df = await get_cached_data('store_master')

    if sales_df is None or inventory_df is None or sku_df is None:
        return {"error": "Required data not uploaded (need daily_sales, store_inventory, sku_ean_master)", "data": {}}

    try:
        # Apply filters
        sales_df = apply_date_filter(sales_df, start_date, end_date, 'day')
        inventory_df = apply_date_filter(inventory_df, start_date, end_date, 'day')

        if channels:
            channel_list = channels.split(',')
            sales_df = apply_channel_filter(sales_df, channel_list)
            inventory_df = apply_channel_filter(inventory_df, channel_list)
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_df = apply_region_filter(sales_df, region_list, store_df)
            inventory_df = apply_region_filter(inventory_df, region_list, store_df)

        sales_df['day'] = pd.to_datetime(sales_df['day'])
        inventory_df['day'] = pd.to_datetime(inventory_df['day'])

        # Merge with SKU master for style, size, ASP (mrp)
        sku_cols = ['ean']
        if 'style' in sku_df.columns:
            sku_cols.append('style')
        if 'size' in sku_df.columns:
            sku_cols.append('size')
        if 'mrp' in sku_df.columns:
            sku_cols.append('mrp')

        sales_sku = sales_df.merge(sku_df[sku_cols], left_on='sku', right_on='ean', how='left')

        if categories and style_df is not None:
            category_list = categories.split(',')
            sales_sku = apply_category_filter(sales_sku, category_list, style_df)

        if len(sales_sku) == 0:
            return {"error": "No data matches the selected filters", "data": {}}

        # ================================================
        # 1. Calculate ROS per store-SKU (last 30 days)
        # ================================================
        ros_df = sales_sku.groupby(['store_code', 'sku']).agg(
            total_qty=('quantity', 'sum'),
            total_revenue=('revenue', 'sum'),
            live_days=('day', 'nunique')
        ).reset_index()
        ros_df['ros'] = (ros_df['total_qty'] / ros_df['live_days'].clip(lower=1)).round(3)

        # Get ASP per SKU
        if 'mrp' in sku_df.columns:
            asp_map = sku_df.groupby('ean')['mrp'].first()
            ros_df['asp'] = ros_df['sku'].map(asp_map).fillna(0)
        else:
            ros_df['asp'] = np.where(
                ros_df['total_qty'] > 0,
                (ros_df['total_revenue'] / ros_df['total_qty']).round(2),
                0
            )

        # ================================================
        # 2. Latest SOH per store-SKU
        # ================================================
        latest_date = inventory_df['day'].max()
        latest_inv = inventory_df[inventory_df['day'] == latest_date].copy()
        soh_df = latest_inv.groupby(['store_code', 'ean'])['quantity'].sum().reset_index()
        soh_df.columns = ['store_code', 'sku', 'soh']

        # ================================================
        # 3. Identify stock-outs: SOH=0 AND ROS>0
        # ================================================
        merged = ros_df.merge(soh_df, on=['store_code', 'sku'], how='left')
        merged['soh'] = merged['soh'].fillna(0)
        merged['is_stockout'] = (merged['soh'] == 0) & (merged['ros'] > 0)

        total_store_skus = len(merged)
        stockouts = merged[merged['is_stockout']]
        total_stockouts = len(stockouts)
        stockout_rate = round((total_stockouts / max(total_store_skus, 1)) * 100, 1)

        # ================================================
        # 4. Sales Loss per stock-out: ((ROS x 1) - SOH) x ASP
        # ================================================
        stockouts = stockouts.copy()
        stockouts['daily_sales_loss'] = ((stockouts['ros'] * 1 - stockouts['soh']) * stockouts['asp']).clip(lower=0).round(2)
        total_lost_sales = float(stockouts['daily_sales_loss'].sum())

        # ================================================
        # 5. Stock-out duration (consecutive days with SOH=0)
        # ================================================
        inv_with_sku = inventory_df.merge(
            sku_df[['ean']].drop_duplicates(), on='ean', how='inner'
        )
        zero_days = inv_with_sku[inv_with_sku['quantity'] == 0].groupby(
            ['store_code', 'ean']
        )['day'].nunique().reset_index()
        zero_days.columns = ['store_code', 'sku', 'stockout_days']

        stockouts = stockouts.merge(zero_days, on=['store_code', 'sku'], how='left')
        stockouts['stockout_days'] = stockouts['stockout_days'].fillna(1).astype(int)

        # Severity = LostSales x Duration x Importance (importance=1 default)
        stockouts['severity'] = (stockouts['daily_sales_loss'] * stockouts['stockout_days']).round(2)

        # ================================================
        # 6. Top impacted SKUs
        # ================================================
        # Add style info
        if 'style' in sku_df.columns:
            sku_style_map = sku_df.groupby('ean')['style'].first()
            stockouts['style'] = stockouts['sku'].map(sku_style_map).fillna('Unknown')
        else:
            stockouts['style'] = 'Unknown'

        top_skus = stockouts.groupby('sku').agg(
            stockout_count=('store_code', 'nunique'),
            total_daily_loss=('daily_sales_loss', 'sum'),
            avg_ros=('ros', 'mean'),
            avg_asp=('asp', 'mean'),
            style=('style', 'first')
        ).reset_index().sort_values('total_daily_loss', ascending=False).head(15)

        # ================================================
        # 7. Top impacted stores
        # ================================================
        top_stores = stockouts.groupby('store_code').agg(
            stockout_count=('sku', 'nunique'),
            total_daily_loss=('daily_sales_loss', 'sum'),
            avg_duration=('stockout_days', 'mean'),
            total_severity=('severity', 'sum')
        ).reset_index().sort_values('total_severity', ascending=False).head(15)
        top_stores['avg_duration'] = top_stores['avg_duration'].round(1)

        # ================================================
        # 8. Category impact (if style master available)
        # ================================================
        category_impact = []
        if style_df is not None and 'category' in style_df.columns and 'style' in stockouts.columns:
            if 'style_code' in style_df.columns:
                style_cat = style_df[['style_code', 'category']].drop_duplicates()
                so_cat = stockouts.merge(style_cat, left_on='style', right_on='style_code', how='left')
            else:
                so_cat = stockouts.copy()
                so_cat['category'] = 'Unknown'
            cat_agg = so_cat.groupby('category').agg(
                stockout_count=('sku', 'nunique'),
                total_daily_loss=('daily_sales_loss', 'sum')
            ).reset_index().sort_values('total_daily_loss', ascending=False)
            category_impact = cat_agg.fillna(0).to_dict('records')

        # ================================================
        # 9. Daily stock-out trend
        # ================================================
        inv_with_ros = inventory_df.merge(
            ros_df[['store_code', 'sku', 'ros']].drop_duplicates(),
            left_on=['store_code', 'ean'], right_on=['store_code', 'sku'], how='left'
        )
        inv_with_ros['ros'] = inv_with_ros['ros'].fillna(0)
        inv_with_ros['is_stockout'] = (inv_with_ros['quantity'] == 0) & (inv_with_ros['ros'] > 0)

        daily_trend = inv_with_ros.groupby('day')['is_stockout'].sum().reset_index()
        daily_trend.columns = ['date', 'stockout_count']
        daily_trend['date'] = daily_trend['date'].dt.strftime('%Y-%m-%d')
        daily_trend = daily_trend.sort_values('date')

        # ================================================
        # 10. High-risk SKUs (low days-to-stockout)
        # ================================================
        # For non-stockout items: days_to_stockout = SOH / ROS
        non_stockout = merged[(~merged['is_stockout']) & (merged['ros'] > 0) & (merged['soh'] > 0)].copy()
        non_stockout['days_to_stockout'] = (non_stockout['soh'] / non_stockout['ros']).round(1)
        non_stockout['risk'] = pd.cut(
            non_stockout['days_to_stockout'],
            bins=[-1, 3, 5, 7, float('inf')],
            labels=['critical', 'high', 'medium', 'low']
        )
        if 'style' in sku_df.columns:
            sku_style_map2 = sku_df.groupby('ean')['style'].first()
            non_stockout['style'] = non_stockout['sku'].map(sku_style_map2).fillna('Unknown')
        else:
            non_stockout['style'] = 'Unknown'

        high_risk = non_stockout[non_stockout['days_to_stockout'] <= 7].sort_values('days_to_stockout').head(15)
        high_risk_list = high_risk[['sku', 'store_code', 'ros', 'soh', 'asp', 'days_to_stockout', 'risk', 'style']].fillna(0).to_dict('records')
        # Convert risk category to string
        for item in high_risk_list:
            item['risk'] = str(item['risk'])

        # ================================================
        # 11. Stores impacted count
        # ================================================
        stores_impacted = int(stockouts['store_code'].nunique())

        # ================================================
        # 12. Weekly & Monthly aggregation (SO-06, SO-07)
        # ================================================
        weekly_trend = []
        monthly_trend = []
        try:
            inv_with_ros_copy = inv_with_ros.copy()
            inv_with_ros_copy['week'] = inv_with_ros_copy['day'].dt.isocalendar().week.astype(int)
            inv_with_ros_copy['month'] = inv_with_ros_copy['day'].dt.month
            inv_with_ros_copy['is_stockout_bool'] = inv_with_ros_copy['is_stockout'].astype(bool)

            wk = inv_with_ros_copy.groupby('week').agg(
                stockout_count=('is_stockout_bool', 'sum'),
                total_skus=('ean', 'count'),
            ).reset_index()
            wk['stockout_rate'] = (wk['stockout_count'] / wk['total_skus'].clip(lower=1) * 100).round(1)
            weekly_trend = wk.sort_values('week').to_dict('records')

            mo = inv_with_ros_copy.groupby('month').agg(
                stockout_count=('is_stockout_bool', 'sum'),
                total_skus=('ean', 'count'),
            ).reset_index()
            mo['stockout_rate'] = (mo['stockout_count'] / mo['total_skus'].clip(lower=1) * 100).round(1)
            monthly_trend = mo.sort_values('month').to_dict('records')
        except Exception:
            pass

        # ================================================
        # 13. Period trends: WTD, MTD, QTD, YTD (SO-16..19)
        # ================================================
        period_trends = {}
        try:
            ref_date = latest_date
            day_col = inv_with_ros['day']
            for label, start in [
                ('wtd', ref_date - pd.Timedelta(days=ref_date.weekday())),
                ('mtd', ref_date.replace(day=1)),
                ('qtd', ref_date - pd.offsets.QuarterBegin(startingMonth=1)),
                ('ytd', ref_date.replace(month=1, day=1)),
            ]:
                mask = (day_col >= pd.Timestamp(start)) & (day_col <= ref_date)
                subset = inv_with_ros[mask]
                if len(subset) > 0:
                    grp = subset.groupby('day')['is_stockout'].sum().reset_index()
                    grp.columns = ['date', 'stockout_count']
                    grp['date'] = grp['date'].dt.strftime('%Y-%m-%d')
                    period_trends[label] = grp.sort_values('date').to_dict('records')
                else:
                    period_trends[label] = []
        except Exception:
            pass

        # ================================================
        # 14. Previous period comparison (SO-20)
        # ================================================
        prev_period_trend = []
        try:
            period_days = (sales_df['day'].max() - sales_df['day'].min()).days + 1
            prev_start = sales_df['day'].min() - pd.Timedelta(days=period_days)
            prev_end = sales_df['day'].min() - pd.Timedelta(days=1)
            prev_inv = inventory_df[(inventory_df['day'] >= prev_start) & (inventory_df['day'] <= prev_end)]
            if len(prev_inv) > 0:
                prev_merged = prev_inv.merge(
                    ros_df[['store_code', 'sku', 'ros']].drop_duplicates(),
                    left_on=['store_code', 'ean'], right_on=['store_code', 'sku'], how='left'
                )
                prev_merged['ros'] = prev_merged['ros'].fillna(0)
                prev_merged['is_stockout'] = (prev_merged['quantity'] == 0) & (prev_merged['ros'] > 0)
                pt = prev_merged.groupby('day')['is_stockout'].sum().reset_index()
                pt.columns = ['date', 'stockout_count']
                pt['date'] = pt['date'].dt.strftime('%Y-%m-%d')
                prev_period_trend = pt.sort_values('date').to_dict('records')
        except Exception:
            pass

        # ================================================
        # 15. 7-day moving average (SO-22)
        # ================================================
        moving_avg = []
        try:
            dt = daily_trend.copy()
            if isinstance(dt, pd.DataFrame) and len(dt) > 0:
                dt_sorted = dt.sort_values('date')
                dt_sorted['ma7'] = dt_sorted['stockout_count'].rolling(7, min_periods=1).mean().round(1)
                moving_avg = dt_sorted[['date', 'ma7']].to_dict('records')
        except Exception:
            pass

        # ================================================
        # 16. Projected trend (SO-21)
        # ================================================
        projected_trend = []
        try:
            if len(daily_trend) >= 7:
                recent_avg = daily_trend.tail(7)['stockout_count'].mean()
                last_date = pd.to_datetime(daily_trend['date'].iloc[-1])
                for i in range(1, 8):
                    future = last_date + pd.Timedelta(days=i)
                    projected_trend.append({
                        'date': future.strftime('%Y-%m-%d'),
                        'projected_count': round(recent_avg * (1 - 0.05 * i), 1),
                    })
        except Exception:
            pass

        # ================================================
        # 17. Store heatmap (SO-23)
        # ================================================
        store_heatmap = []
        try:
            store_so = merged.groupby('store_code').agg(
                total=('sku', 'count'),
                stockouts=('is_stockout', 'sum'),
                total_loss=('asp', lambda x: 0),
            ).reset_index()
            so_loss = stockouts.groupby('store_code')['daily_sales_loss'].sum().reset_index()
            so_loss.columns = ['store_code', 'total_loss']
            store_so = store_so.drop(columns=['total_loss']).merge(so_loss, on='store_code', how='left')
            store_so['total_loss'] = store_so['total_loss'].fillna(0)
            store_so['stockout_pct'] = (store_so['stockouts'] / store_so['total'].clip(lower=1) * 100).round(1)
            store_so['severity'] = pd.cut(
                store_so['stockout_pct'],
                bins=[-1, 5, 15, 30, float('inf')],
                labels=['low', 'medium', 'high', 'critical']
            ).astype(str)
            store_heatmap = store_so.sort_values('stockout_pct', ascending=False).fillna(0).to_dict('records')
        except Exception:
            pass

        # ================================================
        # 18. Category heatmap (SO-24)
        # ================================================
        category_heatmap = []
        try:
            if style_df is not None and 'category' in style_df.columns and 'style' in sku_df.columns:
                sku_cat = sku_df.merge(
                    style_df[['style_code', 'category']].rename(columns={'style_code': 'style'}),
                    on='style', how='left'
                )
                merged_cat = merged.merge(sku_cat[['ean', 'category']], left_on='sku', right_on='ean', how='left', suffixes=('', '_cat'))
                cat_so = merged_cat.groupby('category').agg(
                    total=('sku', 'count'),
                    stockouts=('is_stockout', 'sum'),
                ).reset_index()
                cat_loss = merged_cat[merged_cat['is_stockout']].groupby('category').apply(
                    lambda g: ((g['ros'] - g['soh']) * g['asp']).clip(lower=0).sum()
                ).reset_index()
                cat_loss.columns = ['category', 'total_loss']
                cat_so = cat_so.merge(cat_loss, on='category', how='left')
                cat_so['total_loss'] = cat_so['total_loss'].fillna(0).round(2)
                cat_so['stockout_pct'] = (cat_so['stockouts'] / cat_so['total'].clip(lower=1) * 100).round(1)
                cat_so['severity'] = pd.cut(
                    cat_so['stockout_pct'],
                    bins=[-1, 5, 15, 30, float('inf')],
                    labels=['low', 'medium', 'high', 'critical']
                ).astype(str)
                category_heatmap = cat_so.sort_values('stockout_pct', ascending=False).fillna(0).to_dict('records')
        except Exception:
            pass

        # ================================================
        # 19. Reorder recommendations (SO-33)
        # ================================================
        reorder_recs = []
        try:
            safety_days = (_cfg or {}).get("safety_days", 7) if '_cfg' not in dir() else 7
            cfg_doc = await get_db().analysis_config.find_one({"_id": "main"}, {"_id": 0})
            safety_days = (cfg_doc or {}).get("safety_days", 7)
            lead_time = 14  # default lead time
            candidates = merged[(merged['ros'] > 0)].copy()
            candidates['days_to_stockout'] = np.where(
                candidates['ros'] > 0,
                (candidates['soh'] / candidates['ros']).round(1),
                999
            )
            candidates['reorder_qty'] = np.where(
                candidates['days_to_stockout'] < (lead_time + safety_days),
                ((candidates['ros'] * (lead_time + safety_days)) - candidates['soh']).clip(lower=0).round(0),
                0
            )
            needs_reorder = candidates[candidates['reorder_qty'] > 0].sort_values('days_to_stockout')
            if 'style' in sku_df.columns:
                sku_style_map3 = sku_df.groupby('ean')['style'].first()
                needs_reorder['style'] = needs_reorder['sku'].map(sku_style_map3).fillna('Unknown')
            else:
                needs_reorder['style'] = 'Unknown'
            reorder_recs = needs_reorder[['sku', 'store_code', 'style', 'ros', 'soh', 'asp',
                'days_to_stockout', 'reorder_qty']].head(20).fillna(0).to_dict('records')
        except Exception:
            pass

        # ================================================
        # 20. Alternative SKU suggestions (SO-32)
        # ================================================
        alt_suggestions = []
        try:
            if 'style' in sku_df.columns and 'size' in sku_df.columns:
                so_skus = stockouts[['sku', 'store_code', 'style']].head(10)
                for _, row in so_skus.iterrows():
                    style = row.get('style', '')
                    if style and style != 'Unknown':
                        same_style_skus = sku_df[sku_df['style'] == style]['ean'].tolist()
                        store_inv = merged[(merged['store_code'] == row['store_code']) &
                                          (merged['sku'].isin(same_style_skus)) &
                                          (merged['soh'] > 0)]
                        alts = store_inv[['sku', 'soh', 'ros']].head(3).to_dict('records')
                        if alts:
                            alt_suggestions.append({
                                'stockout_sku': row['sku'],
                                'store_code': row['store_code'],
                                'alternatives': alts,
                            })
        except Exception:
            pass

        return {
            "summary": {
                "total_stockouts": total_stockouts,
                "stockout_rate": stockout_rate,
                "total_lost_sales": round(total_lost_sales, 2),
                "stores_impacted": stores_impacted,
                "total_store_skus": total_store_skus,
                "snapshot_date": str(latest_date.date()) if pd.notna(latest_date) else None,
            },
            "top_skus": top_skus.round(2).fillna(0).to_dict('records'),
            "top_stores": top_stores.round(2).fillna(0).to_dict('records'),
            "category_impact": category_impact,
            "daily_trend": daily_trend.to_dict('records'),
            "weekly_trend": weekly_trend,
            "monthly_trend": monthly_trend,
            "period_trends": period_trends,
            "prev_period_trend": prev_period_trend,
            "moving_avg": moving_avg,
            "projected_trend": projected_trend,
            "high_risk_skus": high_risk_list,
            "store_heatmap": store_heatmap,
            "category_heatmap": category_heatmap,
            "reorder_recommendations": reorder_recs,
            "alternative_suggestions": alt_suggestions,
        }
    except Exception as e:
        logger.error(f"Stock-out analysis error: {str(e)}")
        return {"error": str(e), "data": {}}


@api_router.get("/analytics/executive-kpis")
async def get_executive_kpis(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
):
    """Revenue, Margin, WoW, and YoY KPIs for the executive dashboard."""
    sales_df = await get_cached_data('daily_sales')
    sku_df = await get_cached_data('sku_ean_master')

    if sales_df is None or len(sales_df) == 0:
        return {
            "revenue": 0, "units_sold": 0, "margin_pct": None,
            "mrp_realisation_pct": None,
            "wow": {"revenue_change": 0, "units_change": 0,
                    "current_revenue": 0, "previous_revenue": 0,
                    "current_units": 0, "previous_units": 0},
            "yoy": {"revenue_change": 0, "current_revenue": 0, "previous_revenue": 0},
            "has_data": False,
        }

    sales_df['day'] = pd.to_datetime(sales_df['day'], errors='coerce')
    sales_df['revenue'] = pd.to_numeric(sales_df['revenue'], errors='coerce').fillna(0)
    sales_df['quantity'] = pd.to_numeric(sales_df['quantity'], errors='coerce').fillna(0)

    # Apply filters
    if start_date:
        sales_df = sales_df[sales_df['day'] >= pd.to_datetime(start_date)]
    if end_date:
        sales_df = sales_df[sales_df['day'] <= pd.to_datetime(end_date)]
    if categories and sku_df is not None:
        cat_list = [c.strip() for c in categories.split(',')]
        style_df = await get_cached_data('style_master')
        if style_df is not None and 'category' in style_df.columns:
            valid_styles = style_df[style_df['category'].isin(cat_list)]['style_code'].unique()
            if 'sku' in sales_df.columns and 'style' in sku_df.columns and 'ean' in sku_df.columns:
                valid_skus = sku_df[sku_df['style'].isin(valid_styles)]['ean'].unique()
                sales_df = sales_df[sales_df['sku'].isin(valid_skus)]
    if channels:
        ch_list = [c.strip() for c in channels.split(',')]
        if 'channel' in sales_df.columns:
            sales_df = sales_df[sales_df['channel'].isin(ch_list)]
    if regions:
        rg_list = [r.strip() for r in regions.split(',')]
        store_df = await get_cached_data('store_master')
        if store_df is not None and 'region' in store_df.columns and 'store_code' in store_df.columns:
            valid_stores = store_df[store_df['region'].isin(rg_list)]['store_code'].unique()
            if 'store_code' in sales_df.columns:
                sales_df = sales_df[sales_df['store_code'].isin(valid_stores)]

    total_revenue = float(sales_df['revenue'].sum())
    total_units = int(sales_df['quantity'].sum())

    # MRP Realisation % (proxy for margin)
    mrp_realisation = None
    if sku_df is not None and 'mrp' in sku_df.columns and 'ean' in sku_df.columns:
        sku_df['mrp'] = pd.to_numeric(sku_df['mrp'], errors='coerce').fillna(0)
        merged = sales_df.merge(sku_df[['ean', 'mrp']].drop_duplicates('ean'),
                                left_on='sku', right_on='ean', how='left')
        merged['mrp_value'] = merged['quantity'] * merged['mrp']
        total_mrp = merged['mrp_value'].sum()
        if total_mrp > 0:
            mrp_realisation = round(float(total_revenue / total_mrp * 100), 1)

    # WoW: split by midpoint of date range
    max_date = sales_df['day'].max()
    min_date = sales_df['day'].min()
    date_range_days = (max_date - min_date).days if pd.notna(max_date) and pd.notna(min_date) else 0

    if date_range_days >= 7:
        cutoff = max_date - pd.Timedelta(days=7)
        current_week = sales_df[sales_df['day'] > cutoff]
        prev_week = sales_df[(sales_df['day'] > cutoff - pd.Timedelta(days=7)) & (sales_df['day'] <= cutoff)]
        cur_rev = float(current_week['revenue'].sum())
        prev_rev = float(prev_week['revenue'].sum())
        cur_units = int(current_week['quantity'].sum())
        prev_units = int(prev_week['quantity'].sum())
        wow = {
            "revenue_change": round(((cur_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0, 1),
            "units_change": round(((cur_units - prev_units) / prev_units * 100) if prev_units > 0 else 0, 1),
            "current_revenue": cur_rev,
            "previous_revenue": prev_rev,
            "current_units": cur_units,
            "previous_units": prev_units,
        }
    else:
        wow = {"revenue_change": 0, "units_change": 0,
               "current_revenue": total_revenue, "previous_revenue": 0,
               "current_units": total_units, "previous_units": 0}

    # YoY: compare same date range one year prior (if data exists)
    yoy = {"revenue_change": 0, "current_revenue": total_revenue, "previous_revenue": 0}
    if date_range_days >= 1 and pd.notna(min_date):
        yoy_start = min_date - pd.DateOffset(years=1)
        yoy_end = max_date - pd.DateOffset(years=1)
        # Reload unfiltered sales for yoy lookup
        all_sales = await get_cached_data('daily_sales')
        if all_sales is not None:
            all_sales['day'] = pd.to_datetime(all_sales['day'], errors='coerce')
            all_sales['revenue'] = pd.to_numeric(all_sales['revenue'], errors='coerce').fillna(0)
            prev_year = all_sales[(all_sales['day'] >= yoy_start) & (all_sales['day'] <= yoy_end)]
            prev_year_rev = float(prev_year['revenue'].sum())
            if prev_year_rev > 0:
                yoy = {
                    "revenue_change": round((total_revenue - prev_year_rev) / prev_year_rev * 100, 1),
                    "current_revenue": total_revenue,
                    "previous_revenue": prev_year_rev,
                }

    return {
        "revenue": total_revenue,
        "units_sold": total_units,
        "margin_pct": mrp_realisation,
        "mrp_realisation_pct": mrp_realisation,
        "wow": wow,
        "yoy": yoy,
        "has_data": True,
    }


@api_router.get("/analytics/executive-dashboard")
async def get_executive_dashboard(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None
):
    """Aggregated executive dashboard pulling top KPIs from all analytics modules."""
    modules = {}
    alerts = []

    # --- ROS Gap ---
    try:
        ros_resp = await get_ros_gap_analysis(start_date, end_date, categories, channels, regions)
        if not ros_resp.get('error'):
            s = ros_resp.get('summary', {})
            modules['ros_gap'] = {
                'avg_ros_gap': s.get('avg_ros_gap', 0),
                'total_sales_loss': s.get('total_sales_loss', 0),
                'healthy_coverage_pct': s.get('healthy_coverage_pct', 0),
                'healthy_styles': s.get('healthy_styles', 0),
                'broken_styles': s.get('broken_styles', 0),
                'noos_styles': s.get('noos_styles', 0),
            }
            if s.get('total_sales_loss', 0) > 0:
                alerts.append({
                    'module': 'ROS Gap',
                    'priority': 'high' if s.get('total_sales_loss', 0) > 1000 else 'medium',
                    'title': f"{s.get('broken_styles', 0)} styles with broken size sets",
                    'description': f"Estimated {int(s.get('total_sales_loss', 0))} units lost due to broken size sets.",
                    'link': '/gap-analysis'
                })
    except Exception:
        modules['ros_gap'] = None

    # --- Stock-Out ---
    try:
        so_resp = await get_stock_out_analysis(start_date, end_date, categories, channels, regions)
        if not so_resp.get('error'):
            s = so_resp.get('summary', {})
            modules['stock_out'] = {
                'total_stockouts': s.get('total_stockouts', 0),
                'stockout_rate': s.get('stockout_rate', 0),
                'total_lost_sales': s.get('total_lost_sales', 0),
                'stores_impacted': s.get('stores_impacted', 0),
            }
            if s.get('total_stockouts', 0) > 0:
                alerts.append({
                    'module': 'Stock-Out',
                    'priority': 'high',
                    'title': f"{s.get('total_stockouts', 0)} active stock-outs",
                    'description': f"Affecting {s.get('stores_impacted', 0)} stores with {formatCurrencyPy(s.get('total_lost_sales', 0))} daily loss.",
                    'link': '/stock-out'
                })
    except Exception:
        modules['stock_out'] = None

    # --- DOH ---
    try:
        doh_resp = await get_doh_analysis(start_date, end_date, categories, channels, regions, 9)
        if not doh_resp.get('error'):
            s = doh_resp.get('summary', {})
            modules['doh'] = {
                'overall_doh': s.get('overall_doh', 0),
                'ideal_doh': s.get('ideal_doh', 9),
                'optimal_count': s.get('optimal_count', 0),
                'overstocked_count': s.get('overstocked_count', 0),
                'understocked_count': s.get('understocked_count', 0),
                'stockedout_count': s.get('stockedout_count', 0),
            }
            risk = s.get('understocked_count', 0) + s.get('stockedout_count', 0)
            if risk > 0:
                alerts.append({
                    'module': 'DOH',
                    'priority': 'medium',
                    'title': f"{risk} store-SKUs at risk (understocked/stocked-out)",
                    'description': f"Overall DOH is {s.get('overall_doh', 0)} days vs ideal {s.get('ideal_doh', 9)} days.",
                    'link': '/doh'
                })
    except Exception:
        modules['doh'] = None

    # --- Planogram Fill Rate ---
    try:
        plano_resp = await get_planogram_fill_rate(start_date, end_date, categories, channels, regions, 85)
        if not plano_resp.get('error'):
            s = plano_resp.get('summary', {})
            modules['planogram'] = {
                'overall_fill_rate': s.get('overall_fill_rate', 0),
                'target_fill_rate': s.get('target_fill_rate', 85),
                'good_count': s.get('good_count', 0),
                'moderate_count': s.get('moderate_count', 0),
                'critical_count': s.get('critical_count', 0),
                'total_lost_sales': s.get('total_lost_sales', 0),
            }
            if s.get('critical_count', 0) > 0:
                alerts.append({
                    'module': 'Planogram',
                    'priority': 'high' if s.get('critical_count', 0) > 100 else 'medium',
                    'title': f"{s.get('critical_count', 0)} store-SKUs below 80% fill rate",
                    'description': f"Overall fill rate: {s.get('overall_fill_rate', 0)}%. Lost sales: {formatCurrencyPy(s.get('total_lost_sales', 0))}.",
                    'link': '/planogram'
                })
    except Exception:
        modules['planogram'] = None

    # --- Replenishment ---
    try:
        repl_resp = await get_replenishment_plan(start_date, end_date, categories, channels, regions, 14, 7, 0.1)
        if not repl_resp.get('error'):
            s = repl_resp.get('summary', {})
            modules['replenishment'] = {
                'total_po_value': s.get('total_po_value', 0),
                'total_reorder_units': s.get('total_reorder_units', 0),
                'skus_needing_reorder': s.get('skus_needing_reorder', 0),
                'stockout_count': s.get('stockout_count', 0),
                'critical_count': s.get('critical_count', 0),
            }
            urgent = s.get('stockout_count', 0) + s.get('critical_count', 0)
            if urgent > 0:
                alerts.append({
                    'module': 'Replenishment',
                    'priority': 'high',
                    'title': f"{urgent} urgent reorder items",
                    'description': f"Total PO value: {formatCurrencyPy(s.get('total_po_value', 0))}. {s.get('skus_needing_reorder', 0)} SKUs need reorder.",
                    'link': '/replenishment'
                })
    except Exception:
        modules['replenishment'] = None

    # --- Health Score (0-100) ---
    scores = []
    if modules.get('stock_out'):
        so_score = max(0, 100 - modules['stock_out']['stockout_rate'])
        scores.append(so_score)
    if modules.get('doh'):
        d = modules['doh']
        total_items = d['optimal_count'] + d['overstocked_count'] + d['understocked_count'] + d['stockedout_count']
        doh_score = (d['optimal_count'] / max(total_items, 1)) * 100 if total_items > 0 else 50
        scores.append(doh_score)
    if modules.get('planogram'):
        scores.append(modules['planogram']['overall_fill_rate'])
    if modules.get('ros_gap'):
        rg = modules['ros_gap']
        total_s = rg['healthy_styles'] + rg['broken_styles']
        ros_score = (rg['healthy_styles'] / max(total_s, 1)) * 100 if total_s > 0 else 50
        scores.append(ros_score)

    health_score = round(sum(scores) / max(len(scores), 1), 1) if scores else 0

    # Sort alerts by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    alerts.sort(key=lambda a: priority_order.get(a['priority'], 2))

    return {
        'health_score': health_score,
        'modules': modules,
        'alerts': alerts,
    }


@api_router.get("/analytics/planogram-fill-rate")
async def get_planogram_fill_rate(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    target_fill_rate: int = 85
):
    """
    Planogram Fill Rate Analysis using PRD formulas.
    Fill Rate (%) = (Current Stock / Norm Allocated) x 100
    Overall Fill Rate = (Sum Current Stock / Sum Norm Allocated) x 100
    Lost Sales = Missing Facings x ROS per Facing x ASP
    Compliance: >=90% Good, 80-90% Moderate, <80% Critical
    """
    sales_df = await get_cached_data('daily_sales')
    inventory_df = await get_cached_data('store_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    style_df = await get_cached_data('style_master')
    store_df = await get_cached_data('store_master')

    if sales_df is None or inventory_df is None or sku_df is None:
        return {"error": "Required data not uploaded (need daily_sales, store_inventory, sku_ean_master)", "data": {}}

    try:
        sales_filtered = apply_date_filter(sales_df.copy(), start_date, end_date, 'day')
        inventory_filtered = apply_date_filter(inventory_df.copy(), start_date, end_date, 'day')

        if channels:
            channel_list = channels.split(',')
            sales_filtered = apply_channel_filter(sales_filtered, channel_list)
            inventory_filtered = apply_channel_filter(inventory_filtered, channel_list)
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_filtered = apply_region_filter(sales_filtered, region_list, store_df)
            inventory_filtered = apply_region_filter(inventory_filtered, region_list, store_df)

        sales_filtered['day'] = pd.to_datetime(sales_filtered['day'])
        inventory_filtered['day'] = pd.to_datetime(inventory_filtered['day'])

        # Merge with SKU master
        sku_cols = ['ean']
        if 'style' in sku_df.columns:
            sku_cols.append('style')
        if 'mrp' in sku_df.columns:
            sku_cols.append('mrp')

        inv_sku = inventory_filtered.merge(sku_df[sku_cols], on='ean', how='left')
        sales_sku = sales_filtered.merge(sku_df[sku_cols], left_on='sku', right_on='ean', how='left')

        if categories and style_df is not None:
            category_list = categories.split(',')
            inv_sku = apply_category_filter(inv_sku, category_list, style_df)
            sales_sku = apply_category_filter(sales_sku, category_list, style_df)

        if len(inv_sku) == 0:
            return {"error": "No data matches the selected filters", "data": {}}

        # ================================================
        # 1. Norm Allocated = peak/avg inventory per store-SKU (proxy for planogram)
        # ================================================
        norm_calc = inv_sku.groupby(['store_code', 'ean']).agg(
            max_qty=('quantity', 'max'),
            avg_qty=('quantity', 'mean')
        ).reset_index()
        # Use max observed inventory as norm (represents full planogram fill)
        norm_calc['norm_allocated'] = norm_calc['max_qty'].clip(lower=1)

        # ================================================
        # 2. Current Stock (latest date SOH)
        # ================================================
        latest_date = inventory_filtered['day'].max()
        latest_inv = inventory_filtered[inventory_filtered['day'] == latest_date].copy()
        soh_df = latest_inv.groupby(['store_code', 'ean'])['quantity'].sum().reset_index()
        soh_df.columns = ['store_code', 'ean', 'current_stock']

        # ================================================
        # 3. Merge and calculate fill rate per store-SKU
        # ================================================
        fill_df = norm_calc.merge(soh_df, on=['store_code', 'ean'], how='left')
        fill_df['current_stock'] = fill_df['current_stock'].fillna(0).clip(lower=0)
        fill_df['fill_rate'] = (fill_df['current_stock'] / fill_df['norm_allocated'].clip(lower=1) * 100).round(1)
        fill_df['missing_facings'] = (fill_df['norm_allocated'] - fill_df['current_stock']).clip(lower=0)

        # Compliance classification
        def classify_fill(rate):
            if rate >= 90:
                return 'GOOD'
            elif rate >= 80:
                return 'MODERATE'
            return 'CRITICAL'

        fill_df['status'] = fill_df['fill_rate'].apply(classify_fill)

        # Add style/mrp info
        if 'style' in sku_df.columns:
            sku_style = sku_df.groupby('ean')['style'].first()
            fill_df['style'] = fill_df['ean'].map(sku_style).fillna('Unknown')
        else:
            fill_df['style'] = 'Unknown'
        if 'mrp' in sku_df.columns:
            sku_mrp = sku_df.groupby('ean')['mrp'].first()
            fill_df['asp'] = fill_df['ean'].map(sku_mrp).fillna(0)
        else:
            fill_df['asp'] = 0

        # ================================================
        # 4. ROS per store-SKU for lost sales
        # ================================================
        ros_calc = sales_sku.groupby(['store_code', 'sku']).agg(
            total_qty=('quantity', 'sum'),
            total_rev=('revenue', 'sum'),
            live_days=('day', 'nunique')
        ).reset_index()
        ros_calc['ros'] = (ros_calc['total_qty'] / ros_calc['live_days'].clip(lower=1)).round(3)
        ros_calc = ros_calc[['store_code', 'sku', 'ros']]

        fill_df = fill_df.merge(ros_calc, left_on=['store_code', 'ean'], right_on=['store_code', 'sku'], how='left')
        fill_df['ros'] = fill_df['ros'].fillna(0)
        # Lost Sales = Missing Facings x ROS x ASP
        fill_df['lost_sales'] = (fill_df['missing_facings'] * fill_df['ros'] * fill_df['asp']).round(2)

        # ================================================
        # 5. Store-level aggregation
        # ================================================
        store_agg = fill_df.groupby('store_code').agg(
            current_stock=('current_stock', 'sum'),
            norm_allocated=('norm_allocated', 'sum'),
            lost_sales=('lost_sales', 'sum'),
            sku_count=('ean', 'nunique'),
            good_count=('status', lambda x: (x == 'GOOD').sum()),
            moderate_count=('status', lambda x: (x == 'MODERATE').sum()),
            critical_count=('status', lambda x: (x == 'CRITICAL').sum()),
        ).reset_index()
        store_agg['fill_rate'] = (store_agg['current_stock'] / store_agg['norm_allocated'].clip(lower=1) * 100).round(1)
        store_agg['status'] = store_agg['fill_rate'].apply(classify_fill)
        store_agg = store_agg.sort_values('fill_rate')
        store_data = store_agg.fillna(0).to_dict('records')

        # ================================================
        # 6. Category-level aggregation
        # ================================================
        category_data = []
        if style_df is not None and 'category' in style_df.columns:
            if 'style_code' in style_df.columns:
                style_cat = style_df[['style_code', 'category']].drop_duplicates()
                fill_cat = fill_df.merge(style_cat, left_on='style', right_on='style_code', how='left')
            else:
                fill_cat = fill_df.copy()
                fill_cat['category'] = 'Unknown'

            cat_agg = fill_cat.groupby('category').agg(
                current_stock=('current_stock', 'sum'),
                norm_allocated=('norm_allocated', 'sum'),
                lost_sales=('lost_sales', 'sum'),
                sku_count=('ean', 'nunique'),
            ).reset_index()
            cat_agg['fill_rate'] = (cat_agg['current_stock'] / cat_agg['norm_allocated'].clip(lower=1) * 100).round(1)
            cat_agg['status'] = cat_agg['fill_rate'].apply(classify_fill)
            cat_agg = cat_agg.sort_values('fill_rate')
            category_data = cat_agg.fillna(0).to_dict('records')

        # ================================================
        # 7. Weekly trend
        # ================================================
        inv_daily_sum = inventory_filtered.groupby('day')['quantity'].sum().reset_index()
        inv_daily_sum.columns = ['day', 'total_stock']
        # Use overall norm from peak
        total_norm = float(fill_df['norm_allocated'].sum())
        inv_daily_sum['fill_rate'] = (inv_daily_sum['total_stock'] / max(total_norm, 1) * 100).round(1)
        inv_daily_sum = inv_daily_sum.set_index('day')
        weekly = inv_daily_sum.resample('W').agg({'fill_rate': 'mean'}).reset_index()
        weekly['fill_rate'] = weekly['fill_rate'].round(1)
        weekly['week_label'] = weekly['day'].dt.strftime('%b %d')
        weekly['target'] = target_fill_rate
        trend_data = weekly[['week_label', 'fill_rate', 'target']].tail(8).fillna(0).to_dict('records')

        # ================================================
        # 8. Detail table (top 200 lowest fill rate)
        # ================================================
        detail_cols = ['store_code', 'ean', 'style', 'current_stock', 'norm_allocated',
                       'fill_rate', 'missing_facings', 'ros', 'asp', 'lost_sales', 'status']
        detail = fill_df[detail_cols].sort_values('fill_rate').head(200).round(2).fillna(0).to_dict('records')

        # ================================================
        # 9. Summary KPIs
        # ================================================
        overall_current = float(fill_df['current_stock'].sum())
        overall_norm = float(fill_df['norm_allocated'].sum())
        overall_fill = round(overall_current / max(overall_norm, 1) * 100, 1)
        overall_lost = float(fill_df['lost_sales'].sum())

        status_counts = fill_df['status'].value_counts().to_dict()
        good_total = int(status_counts.get('GOOD', 0))
        moderate_total = int(status_counts.get('MODERATE', 0))
        critical_total = int(status_counts.get('CRITICAL', 0))

        overall_status = classify_fill(overall_fill)

        # Recommendations
        recommendations = []
        critical_stores = [s for s in store_data if s['status'] == 'CRITICAL']
        moderate_stores = [s for s in store_data if s['status'] == 'MODERATE']

        if critical_stores:
            recommendations.append({
                "priority": "high",
                "title": f"Critical fill rate in {len(critical_stores)} stores",
                "description": f"These stores have fill rate below 80%. Missing facings are causing estimated lost sales of {formatCurrencyPy(sum(s['lost_sales'] for s in critical_stores))}.",
                "stores": [s['store_code'] for s in critical_stores[:5]]
            })
        if moderate_stores:
            recommendations.append({
                "priority": "medium",
                "title": f"Moderate risk in {len(moderate_stores)} stores",
                "description": "These stores have fill rate between 80-90%. Review planogram compliance and replenishment cycle.",
                "stores": [s['store_code'] for s in moderate_stores[:5]]
            })
        if critical_total > 0:
            recommendations.append({
                "priority": "high",
                "title": f"{critical_total} store-SKU combinations critically low",
                "description": f"At the SKU level, {critical_total} combinations have fill rate below 80%. Prioritize replenishment for highest lost-sales items."
            })

        return {
            "summary": {
                "overall_fill_rate": overall_fill,
                "overall_status": overall_status,
                "target_fill_rate": target_fill_rate,
                "total_lost_sales": round(overall_lost, 2),
                "total_store_skus": len(fill_df),
                "good_count": good_total,
                "moderate_count": moderate_total,
                "critical_count": critical_total,
                "total_stores": len(store_data),
                "snapshot_date": str(latest_date.date()) if pd.notna(latest_date) else None,
            },
            "store_data": store_data,
            "category_data": category_data,
            "trend_data": trend_data,
            "detail": detail,
            "recommendations": recommendations,
        }
    except Exception as e:
        logger.error(f"Planogram fill rate error: {str(e)}")
        return {"error": str(e), "data": {}}


def formatCurrencyPy(value):
    if value >= 10000000:
        return f"Rs.{value/10000000:.1f}Cr"
    if value >= 100000:
        return f"Rs.{value/100000:.1f}L"
    if value >= 1000:
        return f"Rs.{value/1000:.0f}K"
    return f"Rs.{round(value)}"


@api_router.get("/analytics/doh")
async def get_doh_analysis(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    ideal_doh: int = None
):
    """
    DOH (Days on Hand) Analysis using PRD formulas.
    DOH(store,sku) = Inventory(store,sku) / Daily Raw ROS(store,sku)
    Overall Channel DOH = Sum(DOH x Inventory) / Sum(Inventory)
    Classification: Optimal ±20%, Overstocked >120%, Understocked <80%
    """
    # Read ideal_doh from config if not passed as query param
    if ideal_doh is None:
        cfg = await get_db().analysis_config.find_one({"_id": "main"}, {"_id": 0})
        ideal_doh = (cfg or {}).get("ideal_doh", 9)
    sales_df = await get_cached_data('daily_sales')
    inventory_df = await get_cached_data('store_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    style_df = await get_cached_data('style_master')
    store_df = await get_cached_data('store_master')

    if sales_df is None or inventory_df is None or sku_df is None:
        return {"error": "Required data not uploaded (need daily_sales, store_inventory, sku_ean_master)", "data": {}}

    try:
        sales_filtered = apply_date_filter(sales_df.copy(), start_date, end_date, 'day')
        inventory_filtered = apply_date_filter(inventory_df.copy(), start_date, end_date, 'day')

        if channels:
            channel_list = channels.split(',')
            sales_filtered = apply_channel_filter(sales_filtered, channel_list)
            inventory_filtered = apply_channel_filter(inventory_filtered, channel_list)
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_filtered = apply_region_filter(sales_filtered, region_list, store_df)
            inventory_filtered = apply_region_filter(inventory_filtered, region_list, store_df)

        sales_filtered['day'] = pd.to_datetime(sales_filtered['day'])
        inventory_filtered['day'] = pd.to_datetime(inventory_filtered['day'])

        # Merge sales with SKU master for style
        sku_cols = ['ean']
        if 'style' in sku_df.columns:
            sku_cols.append('style')
        sales_sku = sales_filtered.merge(sku_df[sku_cols], left_on='sku', right_on='ean', how='left')

        if categories and style_df is not None:
            category_list = categories.split(',')
            sales_sku = apply_category_filter(sales_sku, category_list, style_df)

        if len(sales_sku) == 0:
            return {"error": "No data matches the selected filters", "data": {}}

        # ================================================
        # 1. ROS per store-SKU
        # ================================================
        ros_calc = sales_sku.groupby(['store_code', 'sku']).agg(
            total_qty=('quantity', 'sum'),
            total_revenue=('revenue', 'sum'),
            live_days=('day', 'nunique')
        ).reset_index()
        ros_calc['ros'] = (ros_calc['total_qty'] / ros_calc['live_days'].clip(lower=1)).round(4)

        # ================================================
        # 2. Latest SOH per store-SKU
        # ================================================
        latest_date = inventory_filtered['day'].max()
        latest_inv = inventory_filtered[inventory_filtered['day'] == latest_date].copy()
        soh_df = latest_inv.groupby(['store_code', 'ean'])['quantity'].sum().reset_index()
        soh_df.columns = ['store_code', 'sku', 'soh']

        # ================================================
        # 3. DOH = SOH / ROS per store-SKU
        # ================================================
        doh_df = ros_calc.merge(soh_df, on=['store_code', 'sku'], how='outer')
        doh_df['soh'] = doh_df['soh'].fillna(0)
        doh_df['ros'] = doh_df['ros'].fillna(0)
        doh_df['total_qty'] = doh_df['total_qty'].fillna(0)
        doh_df['total_revenue'] = doh_df['total_revenue'].fillna(0)

        doh_df['doh'] = np.where(
            doh_df['ros'] > 0,
            (doh_df['soh'] / doh_df['ros']).round(1),
            np.where(doh_df['soh'] > 0, 9999, 0)
        )

        # Classification: Optimal ±20%, Overstocked >120%, Understocked <80%
        upper = ideal_doh * 1.2
        lower = ideal_doh * 0.8

        def classify(row):
            if row['soh'] == 0 and row['ros'] > 0:
                return 'STOCKED_OUT'
            if row['ros'] == 0 and row['soh'] > 0:
                return 'NO_SALES'
            if row['ros'] == 0 and row['soh'] == 0:
                return 'STOCKED_OUT'
            if row['doh'] > upper:
                return 'OVERSTOCKED'
            if row['doh'] < lower:
                return 'UNDERSTOCKED'
            return 'OPTIMAL'

        doh_df['status'] = doh_df.apply(classify, axis=1)

        # Add style info
        if 'style' in sku_df.columns:
            sku_style_map = sku_df.groupby('ean')['style'].first()
            doh_df['style'] = doh_df['sku'].map(sku_style_map).fillna('Unknown')
        else:
            doh_df['style'] = 'Unknown'

        # ================================================
        # 4. Store-wise aggregation (weighted DOH)
        # ================================================
        valid = doh_df[(doh_df['ros'] > 0) & (doh_df['soh'] > 0)].copy()
        valid['weighted_doh'] = valid['doh'] * valid['soh']

        store_agg = valid.groupby('store_code').agg(
            total_inventory=('soh', 'sum'),
            weighted_doh_sum=('weighted_doh', 'sum'),
            sku_count=('sku', 'nunique'),
            total_revenue=('total_revenue', 'sum')
        ).reset_index()
        store_agg['doh'] = (store_agg['weighted_doh_sum'] / store_agg['total_inventory'].clip(lower=1)).round(1)

        # Status counts per store
        store_status = doh_df.groupby(['store_code', 'status']).size().unstack(fill_value=0).reset_index()
        for col in ['OPTIMAL', 'OVERSTOCKED', 'UNDERSTOCKED', 'STOCKED_OUT', 'NO_SALES']:
            if col not in store_status.columns:
                store_status[col] = 0

        store_agg = store_agg.merge(store_status, on='store_code', how='left')

        def store_overall(row):
            if row.get('STOCKED_OUT', 0) > row.get('OPTIMAL', 0):
                return 'STOCKED_OUT'
            if row.get('UNDERSTOCKED', 0) > row.get('OPTIMAL', 0):
                return 'UNDERSTOCKED'
            if row.get('OVERSTOCKED', 0) > row.get('OPTIMAL', 0):
                return 'OVERSTOCKED'
            return 'OPTIMAL'

        store_agg['status'] = store_agg.apply(store_overall, axis=1)
        store_data = store_agg.sort_values('doh')[
            ['store_code', 'total_inventory', 'doh', 'sku_count', 'status',
             'OPTIMAL', 'OVERSTOCKED', 'UNDERSTOCKED', 'STOCKED_OUT']
        ].fillna(0).to_dict('records')
        for s in store_data:
            s['ideal_doh'] = ideal_doh

        # ================================================
        # 5. Category-wise aggregation
        # ================================================
        category_data = []
        if style_df is not None and 'category' in style_df.columns and 'style' in doh_df.columns:
            if 'style_code' in style_df.columns:
                style_cat = style_df[['style_code', 'category']].drop_duplicates()
                doh_cat = doh_df.merge(style_cat, left_on='style', right_on='style_code', how='left')
            else:
                doh_cat = doh_df.copy()
                doh_cat['category'] = 'Unknown'

            valid_cat = doh_cat[(doh_cat['ros'] > 0) & (doh_cat['soh'] > 0)].copy()
            valid_cat['weighted_doh'] = valid_cat['doh'] * valid_cat['soh']

            cat_agg = valid_cat.groupby('category').agg(
                total_inventory=('soh', 'sum'),
                weighted_doh_sum=('weighted_doh', 'sum'),
                sku_count=('sku', 'nunique')
            ).reset_index()
            cat_agg['doh'] = (cat_agg['weighted_doh_sum'] / cat_agg['total_inventory'].clip(lower=1)).round(1)

            def cat_classify(row):
                if row['doh'] > upper:
                    return 'OVERSTOCKED'
                if row['doh'] < lower:
                    return 'UNDERSTOCKED'
                return 'OPTIMAL'

            cat_agg['status'] = cat_agg.apply(cat_classify, axis=1)
            cat_agg['ideal_doh'] = ideal_doh
            category_data = cat_agg[['category', 'total_inventory', 'doh', 'sku_count', 'status', 'ideal_doh']].fillna(0).to_dict('records')

        # ================================================
        # 6. DOH trend over time (weekly buckets)
        # ================================================
        inv_daily = inventory_filtered.groupby('day')['quantity'].sum().reset_index()
        inv_daily.columns = ['day', 'total_inv']
        sales_daily = sales_filtered.groupby('day')['quantity'].sum().reset_index()
        sales_daily.columns = ['day', 'total_sales']

        daily_merged = inv_daily.merge(sales_daily, on='day', how='outer').sort_values('day').fillna(0)
        daily_merged['ros_7d'] = daily_merged['total_sales'].rolling(7, min_periods=1).mean()
        daily_merged['doh'] = np.where(
            daily_merged['ros_7d'] > 0,
            (daily_merged['total_inv'] / daily_merged['ros_7d']).round(1),
            0
        )
        # Stockout count per day
        daily_stockouts = inventory_filtered[inventory_filtered['quantity'] == 0].groupby('day').size().reset_index()
        daily_stockouts.columns = ['day', 'stockout_count']
        daily_merged = daily_merged.merge(daily_stockouts, on='day', how='left')
        daily_merged['stockout_count'] = daily_merged['stockout_count'].fillna(0).astype(int)

        # Resample to weekly
        daily_merged = daily_merged.set_index('day')
        weekly = daily_merged.resample('W').agg({
            'doh': 'mean',
            'stockout_count': 'sum',
            'total_inv': 'last'
        }).reset_index()
        weekly['doh'] = weekly['doh'].round(1)
        weekly['week_label'] = weekly['day'].dt.strftime('%b %d')

        trend_data = weekly[['week_label', 'doh', 'stockout_count']].tail(8).fillna(0).to_dict('records')

        # ================================================
        # 7. Detail table (store-SKU level, top 200)
        # ================================================
        detail_df = doh_df[doh_df['ros'] > 0][
            ['store_code', 'sku', 'style', 'soh', 'ros', 'doh', 'status']
        ].sort_values('doh').head(200)
        detail_df['ideal_doh'] = ideal_doh
        detail_data = detail_df.round(2).fillna(0).to_dict('records')

        # ================================================
        # 8. Summary KPIs
        # ================================================
        status_counts = doh_df['status'].value_counts().to_dict()
        total_items = len(doh_df)
        overall_doh = 0
        if len(valid) > 0:
            overall_doh = round(float(valid['weighted_doh'].sum() / valid['soh'].sum()), 1)

        # Recommendations
        recommendations = []
        understocked_stores = len([s for s in store_data if s['status'] == 'UNDERSTOCKED'])
        overstocked_stores = len([s for s in store_data if s['status'] == 'OVERSTOCKED'])
        stockedout_stores = len([s for s in store_data if s['status'] == 'STOCKED_OUT'])

        if stockedout_stores > 0:
            recommendations.append({
                "priority": "high",
                "title": "Stock-out detected across stores",
                "description": f"{stockedout_stores} stores have critical stock-outs with active demand. Immediate replenishment needed."
            })
        if understocked_stores > 0:
            recommendations.append({
                "priority": "high",
                "title": f"DOH below {lower:.0f} days in {understocked_stores} stores",
                "description": f"These stores have DOH below 80% of ideal ({ideal_doh} days). Increase replenishment frequency."
            })
        if overstocked_stores > 0:
            recommendations.append({
                "priority": "medium",
                "title": f"DOH above {upper:.0f} days in {overstocked_stores} stores",
                "description": "These stores have DOH above 120% of ideal. Consider reducing order quantities or inter-store transfers."
            })

        return {
            "summary": {
                "overall_doh": overall_doh,
                "ideal_doh": ideal_doh,
                "total_store_skus": total_items,
                "optimal_count": int(status_counts.get('OPTIMAL', 0)),
                "overstocked_count": int(status_counts.get('OVERSTOCKED', 0)),
                "understocked_count": int(status_counts.get('UNDERSTOCKED', 0)),
                "stockedout_count": int(status_counts.get('STOCKED_OUT', 0)),
                "no_sales_count": int(status_counts.get('NO_SALES', 0)),
                "snapshot_date": str(latest_date.date()) if pd.notna(latest_date) else None,
            },
            "store_data": store_data,
            "category_data": category_data,
            "trend_data": trend_data,
            "detail": detail_data,
            "recommendations": recommendations,
        }
    except Exception as e:
        logger.error(f"DOH analysis error: {str(e)}")
        return {"error": str(e), "data": {}}


@api_router.get("/analytics/replenishment")
async def get_replenishment_plan(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    lead_time_days: int = None,
    safety_days: int = None,
    min_ros: float = 0.1
):
    """
    Replenishment Planner using PRD formulas.
    Reorder Qty = (ROS x Lead Time Days) + Safety Stock - Current SOH
    Safety Stock = ROS x Safety Days
    Projected Stock-Out Date = Current SOH / ROS
    PO Value = Reorder Qty x ASP
    """
    # Read from config if not passed as query params
    cfg = await get_db().analysis_config.find_one({"_id": "main"}, {"_id": 0})
    cfg = cfg or {}
    if lead_time_days is None:
        lead_time_days = cfg.get("lead_time_days", 14)
    if safety_days is None:
        safety_days = cfg.get("safety_days", cfg.get("cover_days", 7))
    sales_df = await get_cached_data('daily_sales')
    inventory_df = await get_cached_data('store_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    style_df = await get_cached_data('style_master')
    store_df = await get_cached_data('store_master')

    if sales_df is None or inventory_df is None or sku_df is None:
        return {"error": "Required data not uploaded (need daily_sales, store_inventory, sku_ean_master)", "data": {}}

    try:
        # Apply filters
        sales_filtered = apply_date_filter(sales_df.copy(), start_date, end_date, 'day')
        inventory_filtered = apply_date_filter(inventory_df.copy(), start_date, end_date, 'day')

        if channels:
            channel_list = channels.split(',')
            sales_filtered = apply_channel_filter(sales_filtered, channel_list)
            inventory_filtered = apply_channel_filter(inventory_filtered, channel_list)
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_filtered = apply_region_filter(sales_filtered, region_list, store_df)
            inventory_filtered = apply_region_filter(inventory_filtered, region_list, store_df)

        sales_filtered['day'] = pd.to_datetime(sales_filtered['day'])
        inventory_filtered['day'] = pd.to_datetime(inventory_filtered['day'])

        # ================================================
        # 1. ROS per store-SKU
        # ================================================
        ros_calc = sales_filtered.groupby(['store_code', 'sku']).agg(
            total_qty=('quantity', 'sum'),
            total_revenue=('revenue', 'sum'),
            live_days=('day', 'nunique')
        ).reset_index()
        ros_calc['ros'] = (ros_calc['total_qty'] / ros_calc['live_days'].clip(lower=1)).round(3)

        # Get ASP per SKU
        if 'mrp' in sku_df.columns:
            asp_map = sku_df.groupby('ean')['mrp'].first()
            ros_calc['asp'] = ros_calc['sku'].map(asp_map).fillna(0)
        else:
            ros_calc['asp'] = np.where(
                ros_calc['total_qty'] > 0,
                (ros_calc['total_revenue'] / ros_calc['total_qty']).round(2),
                0
            )

        # Filter to items with meaningful demand
        ros_calc = ros_calc[ros_calc['ros'] >= min_ros]

        if len(ros_calc) == 0:
            return {"error": "No items with sufficient demand found for the selected filters", "data": {}}

        # ================================================
        # 2. Current SOH per store-SKU
        # ================================================
        latest_date = inventory_filtered['day'].max()
        latest_inv = inventory_filtered[inventory_filtered['day'] == latest_date].copy()
        soh_calc = latest_inv.groupby(['store_code', 'ean'])['quantity'].sum().reset_index()
        soh_calc.columns = ['store_code', 'sku', 'current_soh']

        # ================================================
        # 3. Merge and compute replenishment
        # ================================================
        plan = ros_calc.merge(soh_calc, on=['store_code', 'sku'], how='left')
        plan['current_soh'] = plan['current_soh'].fillna(0).clip(lower=0)

        # PRD Formulas
        plan['safety_stock'] = (plan['ros'] * safety_days).round(0)
        plan['demand_during_lead'] = (plan['ros'] * lead_time_days).round(0)
        plan['reorder_qty'] = (plan['demand_during_lead'] + plan['safety_stock'] - plan['current_soh']).clip(lower=0).round(0)
        plan['po_value'] = (plan['reorder_qty'] * plan['asp']).round(2)
        plan['days_to_stockout'] = np.where(
            plan['ros'] > 0,
            (plan['current_soh'] / plan['ros']).round(1),
            999
        )

        # Priority classification
        plan['priority'] = pd.cut(
            plan['days_to_stockout'].astype(float),
            bins=[-1, 0, 3, 7, 14, float('inf')],
            labels=['Stock-Out', 'Critical', 'High', 'Medium', 'Low']
        ).astype(str)

        # Add style info
        if 'style' in sku_df.columns:
            sku_style_map = sku_df.groupby('ean')['style'].first()
            plan['style'] = plan['sku'].map(sku_style_map).fillna('Unknown')
        else:
            plan['style'] = 'Unknown'

        # Add size info
        if 'size' in sku_df.columns:
            sku_size_map = sku_df.groupby('ean')['size'].first()
            plan['size'] = plan['sku'].map(sku_size_map).fillna('-')
        else:
            plan['size'] = '-'

        # Apply category filter
        if categories and style_df is not None:
            category_list = categories.split(',')
            if 'style_code' in style_df.columns and 'style' in plan.columns:
                filtered_styles = style_df[style_df['category'].isin(category_list)]['style_code'].tolist()
                plan = plan[plan['style'].isin(filtered_styles)]

        # Only include items that need reorder
        needs_reorder = plan[plan['reorder_qty'] > 0].copy()
        needs_reorder = needs_reorder.sort_values('days_to_stockout')

        # ================================================
        # 4. Summary KPIs
        # ================================================
        total_po_value = float(needs_reorder['po_value'].sum())
        total_reorder_units = int(needs_reorder['reorder_qty'].sum())
        skus_needing_reorder = int(needs_reorder['sku'].nunique())
        stores_needing_reorder = int(needs_reorder['store_code'].nunique())
        stockout_count = int((needs_reorder['priority'] == 'Stock-Out').sum())
        critical_count = int((needs_reorder['priority'] == 'Critical').sum())
        high_count = int((needs_reorder['priority'] == 'High').sum())

        # ================================================
        # 5. Aggregated views
        # ================================================
        # By priority
        by_priority = needs_reorder.groupby('priority').agg(
            count=('sku', 'count'),
            total_units=('reorder_qty', 'sum'),
            total_value=('po_value', 'sum')
        ).reset_index()
        priority_order = {'Stock-Out': 0, 'Critical': 1, 'High': 2, 'Medium': 3, 'Low': 4}
        by_priority['sort_key'] = by_priority['priority'].map(priority_order)
        by_priority = by_priority.sort_values('sort_key').drop(columns=['sort_key'])

        # By store
        by_store = needs_reorder.groupby('store_code').agg(
            sku_count=('sku', 'nunique'),
            total_units=('reorder_qty', 'sum'),
            total_value=('po_value', 'sum'),
            urgent_count=('priority', lambda x: ((x == 'Stock-Out') | (x == 'Critical')).sum())
        ).reset_index().sort_values('total_value', ascending=False)

        # By style
        by_style = needs_reorder.groupby('style').agg(
            sku_count=('sku', 'nunique'),
            total_units=('reorder_qty', 'sum'),
            total_value=('po_value', 'sum'),
            avg_days=('days_to_stockout', 'mean')
        ).reset_index().sort_values('total_value', ascending=False).head(20)
        by_style['avg_days'] = by_style['avg_days'].round(1)

        # Detail rows for table (cap at 200)
        detail_cols = ['sku', 'style', 'size', 'store_code', 'current_soh', 'ros',
                       'days_to_stockout', 'safety_stock', 'demand_during_lead',
                       'reorder_qty', 'asp', 'po_value', 'priority']
        detail = needs_reorder[detail_cols].head(200)

        return {
            "summary": {
                "total_po_value": round(total_po_value, 2),
                "total_reorder_units": total_reorder_units,
                "skus_needing_reorder": skus_needing_reorder,
                "stores_needing_reorder": stores_needing_reorder,
                "stockout_count": stockout_count,
                "critical_count": critical_count,
                "high_count": high_count,
                "lead_time_days": lead_time_days,
                "safety_days": safety_days,
                "snapshot_date": str(latest_date.date()) if pd.notna(latest_date) else None,
            },
            "by_priority": by_priority.round(2).fillna(0).to_dict('records'),
            "by_store": by_store.round(2).fillna(0).to_dict('records'),
            "by_style": by_style.round(2).fillna(0).to_dict('records'),
            "detail": detail.round(2).fillna(0).to_dict('records'),
        }
    except Exception as e:
        logger.error(f"Replenishment plan error: {str(e)}")
        return {"error": str(e), "data": {}}


@api_router.get("/analytics/ros")
async def get_ros_analysis(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    min_size: int = None,
    min_size_percent: int = None
):
    """Calculate Rate of Sale analysis with filters"""
    sales_df = await get_cached_data('daily_sales')
    inventory_df = await get_cached_data('store_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    style_df = await get_cached_data('style_master')
    store_df = await get_cached_data('store_master')
    
    if sales_df is None or sku_df is None:
        return {"error": "Required data not uploaded", "data": []}
    
    try:
        # Apply filters
        sales_df = apply_date_filter(sales_df, start_date, end_date, 'day')
        
        if channels:
            channel_list = channels.split(',')
            sales_df = apply_channel_filter(sales_df, channel_list)
        
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_df = apply_region_filter(sales_df, region_list, store_df)
        
        # Convert dates
        sales_df['day'] = pd.to_datetime(sales_df['day'])
        
        # Merge sales with SKU data
        sales_with_sku = sales_df.merge(
            sku_df[['ean', 'style', 'size']], 
            left_on='sku', right_on='ean', how='left'
        )
        
        # Apply category filter after merge
        if categories and style_df is not None:
            category_list = categories.split(',')
            sales_with_sku = apply_category_filter(sales_with_sku, category_list, style_df)
        
        if len(sales_with_sku) == 0:
            return {"error": "No data matches the selected filters", "data": [], "summary": {}}
        
        # Calculate ROS by style
        ros_by_style = sales_with_sku.groupby('style').agg({
            'quantity': 'sum',
            'revenue': 'sum',
            'day': 'nunique',
            'store_code': 'nunique'
        }).reset_index()
        
        ros_by_style.columns = ['style', 'total_quantity', 'total_revenue', 'live_days', 'store_count']
        ros_by_style['ros'] = (ros_by_style['total_quantity'] / ros_by_style['live_days']).round(2)
        ros_by_style['revenue_per_day'] = (ros_by_style['total_revenue'] / ros_by_style['live_days']).round(2)
        
        # Classify as healthy/broken based on ROS median
        median_ros = ros_by_style['ros'].median()
        ros_by_style['status'] = ros_by_style['ros'].apply(
            lambda x: 'healthy' if x >= median_ros else 'broken'
        )
        
        # Apply min_size_percent filter for healthy classification
        if min_size_percent and min_size_percent > 0:
            # Recalculate healthy based on threshold
            threshold = ros_by_style['ros'].quantile(min_size_percent / 100)
            ros_by_style['status'] = ros_by_style['ros'].apply(
                lambda x: 'healthy' if x >= threshold else 'broken'
            )
        
        # Calculate sales loss for broken styles
        ros_by_style['potential_sales'] = ros_by_style.apply(
            lambda row: (median_ros * row['live_days']) if row['status'] == 'broken' else row['total_quantity'],
            axis=1
        )
        ros_by_style['sales_loss'] = (ros_by_style['potential_sales'] - ros_by_style['total_quantity']).clip(lower=0).round(0)
        
        return {
            "summary": {
                "total_styles": len(ros_by_style),
                "healthy_count": len(ros_by_style[ros_by_style['status'] == 'healthy']),
                "broken_count": len(ros_by_style[ros_by_style['status'] == 'broken']),
                "avg_healthy_ros": float(ros_by_style[ros_by_style['status'] == 'healthy']['ros'].mean()),
                "avg_broken_ros": float(ros_by_style[ros_by_style['status'] == 'broken']['ros'].mean()),
                "total_sales_loss": float(ros_by_style['sales_loss'].sum())
            },
            "data": ros_by_style.fillna(0).to_dict('records')
        }
    except Exception as e:
        logger.error(f"ROS analysis error: {str(e)}")
        return {"error": str(e), "data": []}


@api_router.get("/analytics/ros-gap")
async def get_ros_gap_analysis(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    brands: str = None,
    store: str = None,
    sort_by: str = "sales_loss",
):
    """PRD-based ROS Gap Analysis with Healthy Size Set, Sales Loss, and NOOS."""
    sales_df = await get_cached_data('daily_sales')
    inventory_df = await get_cached_data('store_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    style_df = await get_cached_data('style_master')
    store_df = await get_cached_data('store_master')

    if sales_df is None or inventory_df is None or sku_df is None:
        return {"error": "Required data not uploaded (need daily_sales, store_inventory, sku_ean_master)", "data": {}}

    try:
        # --- Apply filters ---
        sales_df = apply_date_filter(sales_df, start_date, end_date, 'day')
        inventory_df = apply_date_filter(inventory_df, start_date, end_date, 'day')

        if channels:
            channel_list = channels.split(',')
            sales_df = apply_channel_filter(sales_df, channel_list)
            inventory_df = apply_channel_filter(inventory_df, channel_list)
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_df = apply_region_filter(sales_df, region_list, store_df)
            inventory_df = apply_region_filter(inventory_df, region_list, store_df)

        sales_df['day'] = pd.to_datetime(sales_df['day'])
        inventory_df['day'] = pd.to_datetime(inventory_df['day'])

        # Merge with SKU master
        sales_sku = sales_df.merge(sku_df[['ean', 'style', 'size']], left_on='sku', right_on='ean', how='left')
        inv_sku = inventory_df.merge(sku_df[['ean', 'style', 'size']], on='ean', how='left')

        if categories and style_df is not None:
            category_list = categories.split(',')
            sales_sku = apply_category_filter(sales_sku, category_list, style_df)
            inv_sku = apply_category_filter(inv_sku, category_list, style_df)

        # Brand filter (GAP-06)
        if brands and style_df is not None and 'brand' in style_df.columns:
            brand_list = [b.strip() for b in brands.split(',')]
            filtered_styles = style_df[style_df['brand'].isin(brand_list)]['style_code'].tolist()
            sales_sku = sales_sku[sales_sku['style'].isin(filtered_styles)]
            inv_sku = inv_sku[inv_sku['style'].isin(filtered_styles)]

        # Store filter (GAP-07)
        if store:
            sales_sku = sales_sku[sales_sku['store_code'] == store]
            inv_sku = inv_sku[inv_sku['store_code'] == store]

        if len(sales_sku) == 0:
            return {"error": "No data matches the selected filters", "data": {}}

        # ====================================================
        # 1. Healthy Size Set classification per store-style-day
        # ====================================================
        # Total unique sizes per style (from SKU master)
        style_total_sizes = sku_df.groupby('style')['size'].nunique().reset_index()
        style_total_sizes.columns = ['style', 'total_sizes']

        # Sizes with stock > 0 per store-style-day
        inv_pos = inv_sku[inv_sku['quantity'] > 0]
        daily_size_avail = inv_pos.groupby(['store_code', 'style', 'day'])['size'].nunique().reset_index()
        daily_size_avail.columns = ['store_code', 'style', 'day', 'available_sizes']
        daily_size_avail = daily_size_avail.merge(style_total_sizes, on='style', how='left')
        daily_size_avail['size_pct'] = (daily_size_avail['available_sizes'] / daily_size_avail['total_sizes'].clip(lower=1) * 100)
        # Read PSA Benchmark from config
        _cfg = await get_db().analysis_config.find_one({"_id": "main"}, {"_id": 0})
        _psa_threshold = (_cfg or {}).get("pivotal_size_threshold", 75)
        daily_size_avail['is_healthy'] = daily_size_avail['size_pct'] >= _psa_threshold

        # ====================================================
        # 2. True Live Days & Raw ROS per store-style
        # ====================================================
        # True live days = days with positive inventory (any size)
        true_live = inv_sku[inv_sku['quantity'] > 0].groupby(['store_code', 'style'])['day'].nunique().reset_index()
        true_live.columns = ['store_code', 'style', 'true_live_days']

        # Net sales qty per store-style
        net_sales = sales_sku.groupby(['store_code', 'style']).agg(
            net_sales_qty=('quantity', 'sum'),
            revenue=('revenue', 'sum')
        ).reset_index()

        # Merge
        ros_df = net_sales.merge(true_live, on=['store_code', 'style'], how='outer').fillna(0)
        ros_df['raw_ros'] = np.where(
            ros_df['true_live_days'] > 0,
            (ros_df['net_sales_qty'] / ros_df['true_live_days']).round(3),
            0
        )

        # ====================================================
        # 3. Healthy / Broken day counts per store-style
        # ====================================================
        healthy_days = daily_size_avail[daily_size_avail['is_healthy']].groupby(['store_code', 'style'])['day'].nunique().reset_index()
        healthy_days.columns = ['store_code', 'style', 'healthy_days']
        broken_days = daily_size_avail[~daily_size_avail['is_healthy']].groupby(['store_code', 'style'])['day'].nunique().reset_index()
        broken_days.columns = ['store_code', 'style', 'broken_days']

        ros_df = ros_df.merge(healthy_days, on=['store_code', 'style'], how='left')
        ros_df = ros_df.merge(broken_days, on=['store_code', 'style'], how='left')
        ros_df['healthy_days'] = ros_df['healthy_days'].fillna(0).astype(int)
        ros_df['broken_days'] = ros_df['broken_days'].fillna(0).astype(int)

        # Healthy ROS = sales on healthy days / healthy days
        # We need sales split by healthy vs broken days
        sales_daily = sales_sku.groupby(['store_code', 'style', 'day'])['quantity'].sum().reset_index()
        sales_daily.columns = ['store_code', 'style', 'day', 'day_qty']

        # Tag each day as healthy or broken
        day_health = daily_size_avail[['store_code', 'style', 'day', 'is_healthy']].drop_duplicates()
        sales_tagged = sales_daily.merge(day_health, on=['store_code', 'style', 'day'], how='left')
        sales_tagged['is_healthy'] = sales_tagged['is_healthy'].fillna(False).astype(bool)

        healthy_sales = sales_tagged[sales_tagged['is_healthy']].groupby(['store_code', 'style'])['day_qty'].sum().reset_index()
        healthy_sales.columns = ['store_code', 'style', 'healthy_sales']
        broken_sales = sales_tagged[~sales_tagged['is_healthy']].groupby(['store_code', 'style'])['day_qty'].sum().reset_index()
        broken_sales.columns = ['store_code', 'style', 'broken_sales']

        ros_df = ros_df.merge(healthy_sales, on=['store_code', 'style'], how='left')
        ros_df = ros_df.merge(broken_sales, on=['store_code', 'style'], how='left')
        ros_df['healthy_sales'] = ros_df['healthy_sales'].fillna(0)
        ros_df['broken_sales'] = ros_df['broken_sales'].fillna(0)

        ros_df['healthy_ros'] = np.where(
            ros_df['healthy_days'] > 0,
            (ros_df['healthy_sales'] / ros_df['healthy_days']).round(3),
            0
        )

        # ====================================================
        # 4. Sales Loss = (Healthy ROS × Broken Days) - Actual Broken Sales
        # ====================================================
        ros_df['sales_loss'] = (
            (ros_df['healthy_ros'] * ros_df['broken_days']) - ros_df['broken_sales']
        ).clip(lower=0).round(1)

        ros_df['ros_gap'] = (ros_df['healthy_ros'] - ros_df['raw_ros']).round(3)
        ros_df['status'] = np.where(ros_df['healthy_days'] > ros_df['broken_days'], 'Healthy', 'Broken')

        # ====================================================
        # 5. NOOS: consistent sales >80% days AND consistent availability
        # ====================================================
        total_period_days = max(inventory_df['day'].nunique(), 1)
        sales_day_count = sales_sku.groupby(['store_code', 'style'])['day'].nunique().reset_index()
        sales_day_count.columns = ['store_code', 'style', 'sales_days']

        inv_day_count = inv_sku[inv_sku['quantity'] > 0].groupby(['store_code', 'style'])['day'].nunique().reset_index()
        inv_day_count.columns = ['store_code', 'style', 'inv_days']

        noos_df = sales_day_count.merge(inv_day_count, on=['store_code', 'style'], how='outer').fillna(0)
        noos_df['sales_consistency'] = (noos_df['sales_days'] / total_period_days * 100).round(1)
        noos_df['inv_consistency'] = (noos_df['inv_days'] / total_period_days * 100).round(1)
        noos_df['is_noos'] = (noos_df['sales_consistency'] >= 80) & (noos_df['inv_consistency'] >= 80)

        # Aggregate NOOS by style
        noos_styles = noos_df.groupby('style').agg(
            store_count=('store_code', 'nunique'),
            noos_store_count=('is_noos', 'sum'),
            avg_sales_consistency=('sales_consistency', 'mean'),
            avg_inv_consistency=('inv_consistency', 'mean')
        ).reset_index()
        noos_styles['noos_pct'] = (noos_styles['noos_store_count'] / noos_styles['store_count'].clip(lower=1) * 100).round(1)
        noos_styles['is_noos'] = noos_styles['noos_pct'] >= 50  # NOOS if majority of stores qualify

        # ====================================================
        # 6. Aggregated views
        # ====================================================
        # Style-wise ROS Gap
        style_ros = ros_df.groupby('style').agg(
            healthy_ros=('healthy_ros', 'mean'),
            raw_ros=('raw_ros', 'mean'),
            total_sales_loss=('sales_loss', 'sum'),
            healthy_days=('healthy_days', 'sum'),
            broken_days=('broken_days', 'sum'),
            store_count=('store_code', 'nunique'),
            total_qty=('net_sales_qty', 'sum'),
            total_revenue=('revenue', 'sum')
        ).reset_index()
        style_ros['ros_gap'] = (style_ros['healthy_ros'] - style_ros['raw_ros']).round(3)
        style_ros['status'] = np.where(style_ros['healthy_days'] > style_ros['broken_days'], 'Healthy', 'Broken')

        # GAP-08: Sort by gap size (or sales_loss, ros_gap)
        sort_map = {
            'sales_loss': ('total_sales_loss', False),
            'gap_size': ('ros_gap', False),
            'ros': ('raw_ros', False),
            'revenue': ('total_revenue', False),
        }
        sort_col, sort_asc = sort_map.get(sort_by, ('total_sales_loss', False))
        style_ros = style_ros.sort_values(sort_col, ascending=sort_asc)

        # Store-wise Size Set Health
        store_health = ros_df.groupby('store_code').agg(
            total_healthy=('healthy_days', 'sum'),
            total_broken=('broken_days', 'sum'),
            total_sales_loss=('sales_loss', 'sum'),
            style_count=('style', 'nunique')
        ).reset_index()
        store_health['total_days'] = store_health['total_healthy'] + store_health['total_broken']
        store_health['healthy_pct'] = np.where(
            store_health['total_days'] > 0,
            (store_health['total_healthy'] / store_health['total_days'] * 100).round(1),
            0
        )
        store_health['broken_pct'] = (100 - store_health['healthy_pct']).round(1)
        store_health = store_health.sort_values('total_sales_loss', ascending=False)

        # Summary KPIs
        avg_ros_gap = float(style_ros['ros_gap'].mean()) if len(style_ros) > 0 else 0
        total_sales_loss = float(ros_df['sales_loss'].sum())
        total_days_all = int(ros_df['healthy_days'].sum() + ros_df['broken_days'].sum())
        healthy_coverage = round((ros_df['healthy_days'].sum() / max(total_days_all, 1)) * 100, 1)
        noos_count = int(noos_styles['is_noos'].sum())

        # GAP-10: Weekly gap trend
        weekly_trend = []
        try:
            sales_sku_copy = sales_sku.copy()
            sales_sku_copy['week'] = sales_sku_copy['day'].dt.isocalendar().week.astype(int)
            inv_sku_copy = inv_sku.copy()
            if 'day' in inv_sku_copy.columns:
                inv_sku_copy['day'] = pd.to_datetime(inv_sku_copy['day'])
                inv_sku_copy['week'] = inv_sku_copy['day'].dt.isocalendar().week.astype(int)
                weekly_health = inv_sku_copy[inv_sku_copy['quantity'] > 0].groupby(['store_code', 'style', 'week'])['size'].nunique().reset_index()
                weekly_health.columns = ['store_code', 'style', 'week', 'avail']
                weekly_health = weekly_health.merge(style_total_sizes, on='style', how='left')
                weekly_health['healthy'] = (weekly_health['avail'] / weekly_health['total_sizes'].clip(lower=1) * 100) >= _psa_threshold
                wk_agg = weekly_health.groupby('week').agg(
                    total_combos=('store_code', 'count'),
                    healthy_combos=('healthy', 'sum'),
                ).reset_index()
                wk_agg['healthy_pct'] = (wk_agg['healthy_combos'] / wk_agg['total_combos'].clip(lower=1) * 100).round(1)

                wk_sales = sales_sku_copy.groupby('week')['quantity'].sum().reset_index()
                wk_sales.columns = ['week', 'total_qty']
                wk_agg = wk_agg.merge(wk_sales, on='week', how='left').fillna(0)
                weekly_trend = wk_agg.sort_values('week').to_dict('records')
        except Exception:
            pass

        return {
            "summary": {
                "avg_ros_gap": round(avg_ros_gap, 3),
                "total_sales_loss": round(total_sales_loss, 0),
                "healthy_coverage_pct": healthy_coverage,
                "total_styles": len(style_ros),
                "healthy_styles": int((style_ros['status'] == 'Healthy').sum()),
                "broken_styles": int((style_ros['status'] == 'Broken').sum()),
                "noos_styles": noos_count,
                "total_noos_candidates": len(noos_styles)
            },
            "style_ros_gap": style_ros.round(3).fillna(0).to_dict('records'),
            "store_health": store_health.round(1).fillna(0).to_dict('records'),
            "noos_styles": noos_styles.round(1).fillna(0).to_dict('records'),
            "weekly_trend": weekly_trend
        }
    except Exception as e:
        logger.error(f"ROS Gap analysis error: {str(e)}")
        return {"error": str(e), "data": {}}


@api_router.get("/analytics/size-gap")
async def get_size_gap_analysis(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    understock_threshold: int = -5,
    overstock_threshold: int = 5
):
    """Enhanced size set gap analysis: healthy size sets, sales loss, store comparison, category/gender breakdown."""
    sales_df = await get_cached_data('daily_sales')
    inventory_df = await get_cached_data('store_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    style_df = await get_cached_data('style_master')
    store_df = await get_cached_data('store_master')

    if sales_df is None or sku_df is None or inventory_df is None:
        return {"error": "Required data not uploaded", "data": []}

    try:
        # Apply filters
        sales_df = apply_date_filter(sales_df, start_date, end_date, 'day')
        inventory_df_f = inventory_df.copy()
        inventory_df_f['day'] = pd.to_datetime(inventory_df_f['day'])
        inventory_df_f = apply_date_filter(inventory_df_f, start_date, end_date, 'day')

        if channels:
            channel_list = channels.split(',')
            sales_df = apply_channel_filter(sales_df, channel_list)
            inventory_df_f = apply_channel_filter(inventory_df_f, channel_list)
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_df = apply_region_filter(sales_df, region_list, store_df)
            inventory_df_f = apply_region_filter(inventory_df_f, region_list, store_df)

        sales_with_sku = sales_df.merge(sku_df[['ean', 'style', 'size']], left_on='sku', right_on='ean', how='left')
        inv_sku = inventory_df_f.merge(sku_df[['ean', 'style', 'size']], on='ean', how='left')

        if categories and style_df is not None:
            category_list = categories.split(',')
            sales_with_sku = apply_category_filter(sales_with_sku, category_list, style_df)
            inv_sku = apply_category_filter(inv_sku, category_list, style_df)

        if len(sales_with_sku) == 0:
            return {"error": "No data matches the selected filters", "data": [], "summary": {}}

        # ---- Original size gap (overstock/understock) ----
        size_dist = sales_with_sku.groupby(['style', 'size'])['quantity'].sum().reset_index()
        total_by_style = size_dist.groupby('style')['quantity'].sum().reset_index()
        total_by_style.columns = ['style', 'total_sales']
        size_dist = size_dist.merge(total_by_style, on='style')
        size_dist['sales_ratio'] = (size_dist['quantity'] / size_dist['total_sales']).round(4)

        latest_date = inventory_df_f['day'].max()
        current_inv = inventory_df_f[inventory_df_f['day'] == latest_date].copy()
        inv_with_sku_latest = current_inv.merge(sku_df[['ean', 'style', 'size']], on='ean', how='left')
        inv_by_size = inv_with_sku_latest.groupby(['style', 'size'])['quantity'].sum().reset_index()
        inv_by_size.columns = ['style', 'size', 'current_qty']
        total_inv = inv_by_size.groupby('style')['current_qty'].sum().reset_index()
        total_inv.columns = ['style', 'total_inv']

        gap_df = inv_by_size.merge(size_dist[['style', 'size', 'sales_ratio']], on=['style', 'size'], how='outer')
        gap_df = gap_df.merge(total_inv, on='style', how='left')
        gap_df['sales_ratio'] = gap_df['sales_ratio'].fillna(0.1)
        gap_df['current_qty'] = gap_df['current_qty'].fillna(0)
        gap_df['total_inv'] = gap_df['total_inv'].fillna(0)
        gap_df['ideal_qty'] = (gap_df['total_inv'] * gap_df['sales_ratio']).round(0)
        gap_df['gap'] = (gap_df['current_qty'] - gap_df['ideal_qty']).round(0)
        gap_df['status'] = gap_df['gap'].apply(
            lambda x: 'Overstock' if x >= overstock_threshold else 'Understock' if x <= understock_threshold else 'Optimal'
        )
        status_counts = gap_df['status'].value_counts().to_dict()

        # ---- GAP-11..14: Healthy size set per store ----
        _cfg = await get_db().analysis_config.find_one({"_id": "main"}, {"_id": 0})
        _psa = (_cfg or {}).get("pivotal_size_threshold", 75)
        style_total_sizes = sku_df.groupby('style')['size'].nunique().reset_index()
        style_total_sizes.columns = ['style', 'total_sizes']

        # Latest inventory per store-style
        pos = inv_sku[inv_sku['quantity'] > 0]
        store_style_avail = pos[pos['day'] == latest_date].groupby(['store_code', 'style'])['size'].nunique().reset_index()
        store_style_avail.columns = ['store_code', 'style', 'available_sizes']
        all_combos = inv_sku[inv_sku['day'] == latest_date][['store_code', 'style']].drop_duplicates()
        health_df = all_combos.merge(store_style_avail, on=['store_code', 'style'], how='left')
        health_df['available_sizes'] = health_df['available_sizes'].fillna(0).astype(int)
        health_df = health_df.merge(style_total_sizes, on='style', how='left')
        health_df['total_sizes'] = health_df['total_sizes'].fillna(1).astype(int)
        health_df['size_pct'] = (health_df['available_sizes'] / health_df['total_sizes'].clip(lower=1) * 100).round(1)
        health_df['is_healthy'] = health_df['size_pct'] >= _psa

        healthy_count = int(health_df['is_healthy'].sum())
        unhealthy_count = len(health_df) - healthy_count

        # GAP-14: Sales loss = (Healthy ROS × Broken Days) - Actual Broken Sales
        # Simplified sales loss per store-style
        sales_agg = sales_with_sku.groupby(['store_code', 'style']).agg(
            total_qty=('quantity', 'sum'), total_rev=('revenue', 'sum'),
        ).reset_index()
        days_in_period = max(sales_with_sku['day'].nunique() if 'day' in sales_with_sku.columns else 1, 1)
        sales_agg['ros'] = (sales_agg['total_qty'] / days_in_period).round(3)
        health_loss = health_df.merge(sales_agg[['store_code', 'style', 'ros', 'total_rev']], on=['store_code', 'style'], how='left').fillna(0)
        # Sales loss = ROS * (1 - size_pct/100) * days_in_period (approximation for broken days)
        health_loss['estimated_loss'] = np.where(
            ~health_loss['is_healthy'],
            (health_loss['ros'] * (1 - health_loss['size_pct'] / 100) * days_in_period).round(1),
            0
        )
        total_estimated_loss = float(health_loss['estimated_loss'].sum())

        # GAP-16: Store comparison
        store_comparison = health_df.groupby('store_code').agg(
            total_combos=('style', 'count'),
            healthy_count=('is_healthy', 'sum'),
            avg_size_pct=('size_pct', 'mean'),
        ).reset_index()
        store_comparison['healthy_pct'] = (store_comparison['healthy_count'] / store_comparison['total_combos'].clip(lower=1) * 100).round(1)
        store_comparison = store_comparison.sort_values('healthy_pct', ascending=True)

        # GAP-17: By category
        category_breakdown = []
        if style_df is not None and 'category' in style_df.columns:
            health_cat = health_df.merge(style_df[['style_code', 'category']].rename(columns={'style_code': 'style'}), on='style', how='left')
            cat_agg = health_cat.groupby('category').agg(
                total=('style', 'count'), healthy=('is_healthy', 'sum'), avg_pct=('size_pct', 'mean'),
            ).reset_index()
            cat_agg['healthy_pct'] = (cat_agg['healthy'] / cat_agg['total'].clip(lower=1) * 100).round(1)
            category_breakdown = cat_agg.fillna(0).to_dict('records')

        # GAP-18: By gender
        gender_breakdown = []
        if style_df is not None and 'gender' in style_df.columns:
            health_gen = health_df.merge(style_df[['style_code', 'gender']].rename(columns={'style_code': 'style'}), on='style', how='left')
            gen_agg = health_gen.groupby('gender').agg(
                total=('style', 'count'), healthy=('is_healthy', 'sum'), avg_pct=('size_pct', 'mean'),
            ).reset_index()
            gen_agg['healthy_pct'] = (gen_agg['healthy'] / gen_agg['total'].clip(lower=1) * 100).round(1)
            gender_breakdown = gen_agg.fillna(0).to_dict('records')

        # GAP-19: Weekly trend
        weekly_trend = []
        try:
            inv_sku_copy = inv_sku.copy()
            inv_sku_copy['week'] = inv_sku_copy['day'].dt.isocalendar().week.astype(int)
            wk_avail = inv_sku_copy[inv_sku_copy['quantity'] > 0].groupby(['store_code', 'style', 'week'])['size'].nunique().reset_index()
            wk_avail.columns = ['store_code', 'style', 'week', 'avail']
            wk_avail = wk_avail.merge(style_total_sizes, on='style', how='left')
            wk_avail['healthy'] = (wk_avail['avail'] / wk_avail['total_sizes'].clip(lower=1) * 100) >= _psa
            wk_trend = wk_avail.groupby('week').agg(
                total=('store_code', 'count'), healthy=('healthy', 'sum'),
            ).reset_index()
            wk_trend['healthy_pct'] = (wk_trend['healthy'] / wk_trend['total'].clip(lower=1) * 100).round(1)
            weekly_trend = wk_trend.sort_values('week').to_dict('records')
        except Exception:
            pass

        return {
            "summary": {
                "overstock": status_counts.get('Overstock', 0),
                "understock": status_counts.get('Understock', 0),
                "optimal": status_counts.get('Optimal', 0),
                "total_gap": abs(gap_df['gap']).sum(),
                "healthy_store_styles": healthy_count,
                "unhealthy_store_styles": unhealthy_count,
                "healthy_pct": round(healthy_count / max(healthy_count + unhealthy_count, 1) * 100, 1),
                "total_estimated_loss": total_estimated_loss,
                "psa_threshold": _psa,
            },
            "data": gap_df.dropna(subset=['style']).fillna(0).to_dict('records'),
            "store_health": health_df.fillna(0).to_dict('records'),
            "store_comparison": store_comparison.fillna(0).to_dict('records'),
            "category_breakdown": category_breakdown,
            "gender_breakdown": gender_breakdown,
            "weekly_trend": weekly_trend,
        }
    except Exception as e:
        logger.error(f"Size gap analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "data": []}


@api_router.get("/analytics/noos")
async def get_noos_analysis(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None,
    export_all: bool = False,
):
    """Enhanced NOOS analysis: new-style exclusion, seasonal check, low-stock alerts, recovery plan."""
    sales_df = await get_cached_data('daily_sales')
    inventory_df = await get_cached_data('store_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    style_df = await get_cached_data('style_master')
    store_df = await get_cached_data('store_master')

    if sales_df is None or inventory_df is None or sku_df is None:
        return {"error": "Required data not uploaded", "data": []}

    try:
        sales_df = apply_date_filter(sales_df, start_date, end_date, 'day')
        inventory_df = apply_date_filter(inventory_df, start_date, end_date, 'day')

        if channels:
            channel_list = channels.split(',')
            sales_df = apply_channel_filter(sales_df, channel_list)
            inventory_df = apply_channel_filter(inventory_df, channel_list)
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_df = apply_region_filter(sales_df, region_list, store_df)
            inventory_df = apply_region_filter(inventory_df, region_list, store_df)

        sales_df['day'] = pd.to_datetime(sales_df['day'])
        inventory_df['day'] = pd.to_datetime(inventory_df['day'])

        inv_with_sku = inventory_df.merge(sku_df[['ean', 'style']], on='ean', how='left')
        if categories and style_df is not None:
            category_list = categories.split(',')
            inv_with_sku = apply_category_filter(inv_with_sku, category_list, style_df)

        if len(inv_with_sku) == 0:
            return {"error": "No data matches the selected filters", "data": [], "summary": {}}

        # Calculate exposure days
        exposure = inv_with_sku[inv_with_sku['quantity'] > 0].groupby(['store_code', 'style'])['day'].nunique().reset_index()
        exposure.columns = ['store_code', 'style', 'exposure_days']
        total_days = max(inventory_df['day'].nunique(), sales_df['day'].nunique(), 1)
        exposure['availability_pct'] = (exposure['exposure_days'] / total_days * 100).round(1)

        # Sales
        sales_with_sku = sales_df.merge(sku_df[['ean', 'style']], left_on='sku', right_on='ean', how='left')
        if categories and style_df is not None:
            sales_with_sku = apply_category_filter(sales_with_sku, category_list, style_df)
        style_sales = sales_with_sku.groupby(['store_code', 'style']).agg(
            quantity=('quantity', 'sum'), revenue=('revenue', 'sum'),
            sales_days=('day', 'nunique'),
        ).reset_index()
        style_sales['sales_pct'] = (style_sales['sales_days'] / max(total_days, 1) * 100).round(1)

        noos_df = exposure.merge(style_sales, on=['store_code', 'style'], how='outer').fillna(0)

        # GAP-23: Exclude new styles (<30 days old)
        first_sale = sales_with_sku.groupby('style')['day'].min().reset_index()
        first_sale.columns = ['style', 'first_sale_date']
        period_end = sales_df['day'].max() if len(sales_df) > 0 else pd.Timestamp.now()
        first_sale['style_age_days'] = (period_end - first_sale['first_sale_date']).dt.days
        noos_df = noos_df.merge(first_sale[['style', 'style_age_days']], on='style', how='left')
        noos_df['style_age_days'] = noos_df['style_age_days'].fillna(0).astype(int)
        noos_df['is_new_style'] = noos_df['style_age_days'] < 30

        # GAP-24: Seasonal exclusion
        noos_df['is_seasonal_excluded'] = False
        if style_df is not None and 'season' in style_df.columns:
            current_month = period_end.month if hasattr(period_end, 'month') else 1
            # Simple seasonal logic: check prefix match
            if 3 <= current_month <= 8:
                season_prefix = 'SS'
            else:
                season_prefix = 'AW'
            season_map = style_df[['style_code', 'season']].rename(columns={'style_code': 'style'})
            noos_df = noos_df.merge(season_map, on='style', how='left')
            noos_df['season'] = noos_df['season'].fillna('Unknown')
            # Out-of-season: season doesn't start with the current prefix AND isn't generic
            generic_seasons = ['All-Season', 'Unknown', 'Perennial', '']
            noos_df['is_seasonal_excluded'] = ~(
                noos_df['season'].str.startswith(season_prefix)
                | noos_df['season'].isin(generic_seasons)
            )

        # NOOS classification (GAP-20, GAP-21, GAP-22)
        _cfg = await get_db().analysis_config.find_one({"_id": "main"}, {"_id": 0})
        min_shelf_life = (_cfg or {}).get("min_shelf_life_days", 30)
        noos_df['meets_shelf_life'] = noos_df['exposure_days'] >= min_shelf_life
        noos_df['noos_candidate'] = (
            noos_df['meets_shelf_life']
            & (noos_df['quantity'] > 0)
            & (noos_df['availability_pct'] >= 80)
            & (noos_df['sales_pct'] >= 80)
            & (~noos_df['is_new_style'])          # GAP-23
            & (~noos_df['is_seasonal_excluded'])   # GAP-24
        )
        # GAP-25: Inventory but no sales → NOOS = False (already handled: quantity > 0 check covers this)

        # GAP-26: Low stock alert (stock running low for NOOS items)
        latest_date = inventory_df['day'].max()
        latest_inv = inv_with_sku[inv_with_sku['day'] == latest_date]
        current_stock = latest_inv.groupby(['store_code', 'style'])['quantity'].sum().reset_index()
        current_stock.columns = ['store_code', 'style', 'current_stock']
        noos_df = noos_df.merge(current_stock, on=['store_code', 'style'], how='left')
        noos_df['current_stock'] = noos_df['current_stock'].fillna(0)
        # Low stock = NOOS candidate with stock below 20% of average daily sales * 30
        noos_df['daily_avg_sales'] = np.where(
            noos_df['sales_days'] > 0,
            noos_df['quantity'] / noos_df['sales_days'],
            0
        )
        noos_df['stock_threshold'] = (noos_df['daily_avg_sales'] * 30 * 0.8).round(0)
        noos_df['low_stock_alert'] = (
            noos_df['noos_candidate']
            & (noos_df['current_stock'] < noos_df['stock_threshold'])
            & (noos_df['current_stock'] > 0)
        )

        # GAP-28: Recovery plan (suggested actions for NOOS items at risk)
        def recovery_plan(row):
            if not row.get('noos_candidate', False):
                return "Not NOOS - no action needed"
            if row.get('low_stock_alert', False):
                return f"URGENT: Replenish {int(row['stock_threshold'] - row['current_stock'])} units. Current stock covers ~{int(row['current_stock'] / max(row['daily_avg_sales'], 0.1))} days."
            if row.get('availability_pct', 0) < 90:
                return "Monitor: Availability below 90%. Ensure consistent replenishment."
            return "Healthy NOOS - maintain current stock levels."
        noos_df['recovery_plan'] = noos_df.apply(recovery_plan, axis=1)

        noos_candidates = int(noos_df['noos_candidate'].sum())
        low_stock_count = int(noos_df['low_stock_alert'].sum())

        # GAP-27 & export: Prepare export data
        export_cols = [
            'store_code', 'style', 'exposure_days', 'availability_pct',
            'sales_days', 'sales_pct', 'quantity', 'revenue', 'current_stock',
            'noos_candidate', 'low_stock_alert', 'recovery_plan',
        ]
        export_data = noos_df[[c for c in export_cols if c in noos_df.columns]]

        if export_all:
            from fastapi.responses import StreamingResponse
            import io
            csv_buf = io.StringIO()
            export_data.to_csv(csv_buf, index=False)
            csv_buf.seek(0)
            return StreamingResponse(
                iter([csv_buf.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=noos_export.csv"},
            )

        return {
            "summary": {
                "total_combinations": len(noos_df),
                "noos_candidates": noos_candidates,
                "avg_availability": float(noos_df['availability_pct'].mean()) if len(noos_df) > 0 else 0,
                "total_revenue": float(noos_df['revenue'].sum()),
                "low_stock_alerts": low_stock_count,
                "new_styles_excluded": int(noos_df['is_new_style'].sum()),
                "seasonal_excluded": int(noos_df['is_seasonal_excluded'].sum()),
                "total_days": total_days,
            },
            "data": noos_df.fillna(0).to_dict('records'),
        }
    except Exception as e:
        logger.error(f"NOOS analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "data": []}


@api_router.get("/analytics/bi-dashboard")
async def get_bi_dashboard(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None
):
    """Get BI dashboard data with filters"""
    sales_df = await get_cached_data('daily_sales')
    sku_df = await get_cached_data('sku_ean_master')
    store_df = await get_cached_data('store_master')
    style_df = await get_cached_data('style_master')
    
    if sales_df is None:
        return {"error": "Sales data not uploaded", "data": {}}
    
    try:
        # Apply filters
        sales_df = apply_date_filter(sales_df, start_date, end_date, 'day')
        
        if channels:
            channel_list = channels.split(',')
            sales_df = apply_channel_filter(sales_df, channel_list)
        
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_df = apply_region_filter(sales_df, region_list, store_df)
        
        if len(sales_df) == 0:
            return {"error": "No data matches the selected filters", "data": {}, "totals": {}}
        
        sales_df['day'] = pd.to_datetime(sales_df['day'])
        sales_df['month'] = sales_df['day'].dt.to_period('M').astype(str)
        
        # Monthly trends
        monthly = sales_df.groupby('month').agg({
            'quantity': 'sum',
            'revenue': 'sum'
        }).reset_index()
        monthly['asp'] = (monthly['revenue'] / monthly['quantity']).round(2)
        
        # By store
        by_store = sales_df.groupby('store_code').agg({
            'quantity': 'sum',
            'revenue': 'sum'
        }).reset_index().sort_values('revenue', ascending=False).head(20)
        
        # Add region if store master exists
        if store_df is not None and 'region' in store_df.columns:
            by_region = sales_df.merge(store_df[['store_code', 'region']], on='store_code', how='left')
            by_region = by_region.groupby('region').agg({
                'quantity': 'sum',
                'revenue': 'sum'
            }).reset_index()
        else:
            by_region = pd.DataFrame()
        
        # Merge with SKU for style analysis
        if sku_df is not None:
            sales_with_sku = sales_df.merge(
                sku_df[['ean', 'style']], left_on='sku', right_on='ean', how='left'
            )
            
            # Apply category filter
            if categories and style_df is not None:
                category_list = categories.split(',')
                sales_with_sku = apply_category_filter(sales_with_sku, category_list, style_df)
            
            by_style = sales_with_sku.groupby('style').agg({
                'quantity': 'sum',
                'revenue': 'sum'
            }).reset_index().sort_values('revenue', ascending=False).head(15)
        else:
            by_style = pd.DataFrame()
        
        return {
            "monthly_trends": monthly.to_dict('records'),
            "by_store": by_store.to_dict('records'),
            "by_region": by_region.to_dict('records') if not by_region.empty else [],
            "by_style": by_style.to_dict('records') if not by_style.empty else [],
            "totals": {
                "total_revenue": float(sales_df['revenue'].sum()),
                "total_quantity": int(sales_df['quantity'].sum()),
                "total_transactions": len(sales_df),
                "unique_stores": sales_df['store_code'].nunique()
            }
        }
    except Exception as e:
        logger.error(f"BI dashboard error: {str(e)}")
        return {"error": str(e), "data": {}}


@api_router.get("/analytics/store-style-ranking")
async def get_store_style_ranking():
    """Get store-style ranking analysis"""
    sales_df = await get_cached_data('daily_sales')
    sku_df = await get_cached_data('sku_ean_master')
    
    if sales_df is None or sku_df is None:
        return {"error": "Required data not uploaded", "data": []}
    
    try:
        sales_df['day'] = pd.to_datetime(sales_df['day'])
        
        # Merge with SKU
        sales_with_sku = sales_df.merge(
            sku_df[['ean', 'style']], left_on='sku', right_on='ean', how='left'
        )
        
        # Calculate days per store-style
        days_per_combo = sales_with_sku.groupby(['store_code', 'style'])['day'].nunique().reset_index()
        days_per_combo.columns = ['store_code', 'style', 'days_on_sale']
        
        # Calculate metrics
        store_style = sales_with_sku.groupby(['store_code', 'style']).agg({
            'quantity': 'sum',
            'revenue': 'sum'
        }).reset_index()
        
        store_style = store_style.merge(days_per_combo, on=['store_code', 'style'])
        store_style['revenue_per_day'] = (store_style['revenue'] / store_style['days_on_sale']).round(2)
        store_style['units_per_day'] = (store_style['quantity'] / store_style['days_on_sale']).round(2)
        
        # Rankings
        store_style['store_rank_for_style'] = store_style.groupby('style')['revenue_per_day'].rank(ascending=False)
        store_style['style_rank_for_store'] = store_style.groupby('store_code')['revenue_per_day'].rank(ascending=False)
        
        return {
            "summary": {
                "total_combinations": len(store_style),
                "unique_stores": store_style['store_code'].nunique(),
                "unique_styles": store_style['style'].nunique()
            },
            "data": store_style.sort_values('revenue_per_day', ascending=False).head(100).to_dict('records')
        }
    except Exception as e:
        logger.error(f"Store-style ranking error: {str(e)}")
        return {"error": str(e), "data": []}


@api_router.get("/analytics/warehouse")
async def get_warehouse_analysis(
    start_date: str = None,
    end_date: str = None
):
    """Get warehouse inventory analysis"""
    wh_master = await get_cached_data('warehouse_master')
    wh_inv = await get_cached_data('warehouse_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    sales_df = await get_cached_data('daily_sales')

    if wh_inv is None:
        return {"error": "Warehouse inventory data not uploaded", "data": {}}

    try:
        wh_inv['day'] = pd.to_datetime(wh_inv['day'])

        if start_date:
            wh_inv = wh_inv[wh_inv['day'] >= pd.to_datetime(start_date)]
        if end_date:
            wh_inv = wh_inv[wh_inv['day'] <= pd.to_datetime(end_date)]

        if len(wh_inv) == 0:
            return {"error": "No warehouse data for the selected period", "data": {}}

        latest_date = wh_inv['day'].max()
        latest_inv = wh_inv[wh_inv['day'] == latest_date].copy()

        # By warehouse
        by_warehouse = latest_inv.groupby('warehouse').agg(
            total_qty=('quantity', 'sum'),
            sku_count=('sku', 'nunique')
        ).reset_index().sort_values('total_qty', ascending=False)

        # By SKU (top movers)
        by_sku = latest_inv.groupby('sku').agg(
            total_qty=('quantity', 'sum'),
            warehouse_count=('warehouse', 'nunique')
        ).reset_index().sort_values('total_qty', ascending=False).head(20)

        # Merge with SKU master for style info
        if sku_df is not None:
            by_sku = by_sku.merge(
                sku_df[['ean', 'style', 'size']].rename(columns={'ean': 'sku'}),
                on='sku', how='left'
            )

        # Trend over time
        trend = wh_inv.groupby(wh_inv['day'].dt.to_period('D').astype(str)).agg(
            total_qty=('quantity', 'sum'),
            unique_skus=('sku', 'nunique')
        ).reset_index()
        trend.columns = ['date', 'total_qty', 'unique_skus']

        # Online fulfillment split
        online_split = []
        if wh_master is not None and 'online_fulfillment_flag' in wh_master.columns:
            merged = latest_inv.merge(wh_master[['warehouse', 'online_fulfillment_flag']], on='warehouse', how='left')
            online_split = merged.groupby('online_fulfillment_flag')['quantity'].sum().reset_index()
            online_split.columns = ['fulfillment_type', 'total_qty']
            online_split['fulfillment_type'] = online_split['fulfillment_type'].map(
                lambda x: 'Online' if str(x).strip().lower() in ['1', 'true', 'yes', 'y'] else 'Offline'
            )
            online_split = online_split.to_dict('records')

        # Calculate velocity if sales data exists
        velocity_data = []
        if sales_df is not None and sku_df is not None:
            sales_df_copy = sales_df.copy()
            sales_df_copy['day'] = pd.to_datetime(sales_df_copy['day'])
            if start_date:
                sales_df_copy = sales_df_copy[sales_df_copy['day'] >= pd.to_datetime(start_date)]
            if end_date:
                sales_df_copy = sales_df_copy[sales_df_copy['day'] <= pd.to_datetime(end_date)]

            sales_by_sku = sales_df_copy.groupby('sku')['quantity'].sum().reset_index()
            sales_by_sku.columns = ['sku', 'sold_qty']

            velocity = latest_inv.groupby('sku')['quantity'].sum().reset_index()
            velocity.columns = ['sku', 'stock_qty']
            velocity = velocity.merge(sales_by_sku, on='sku', how='left')
            velocity['sold_qty'] = velocity['sold_qty'].fillna(0)
            velocity['days_of_stock'] = velocity.apply(
                lambda r: round(r['stock_qty'] / (r['sold_qty'] / 90), 1) if r['sold_qty'] > 0 else 999, axis=1
            )
            velocity = velocity.sort_values('days_of_stock').head(20)
            if sku_df is not None:
                velocity = velocity.merge(
                    sku_df[['ean', 'style', 'size']].rename(columns={'ean': 'sku'}),
                    on='sku', how='left'
                )
            velocity_data = velocity.fillna('').to_dict('records')

        return {
            "totals": {
                "total_stock": int(latest_inv['quantity'].sum()),
                "total_skus": int(latest_inv['sku'].nunique()),
                "total_warehouses": int(latest_inv['warehouse'].nunique()),
                "snapshot_date": str(latest_date.date())
            },
            "by_warehouse": by_warehouse.fillna(0).to_dict('records'),
            "by_sku": by_sku.fillna('').to_dict('records'),
            "trend": trend.to_dict('records') if len(trend) > 1 else [],
            "online_split": online_split,
            "velocity": velocity_data
        }
    except Exception as e:
        logger.error(f"Warehouse analysis error: {str(e)}")
        return {"error": str(e), "data": {}}


# ==================== CHATBOT ====================

PLATFORM_KNOWLEDGE = """
FASHION RETAIL GAP ANALYSIS PLATFORM - KNOWLEDGE BASE

OVERVIEW:
This platform analyzes fashion retail data to identify sales gaps and optimize inventory through advanced rate-of-sale (ROS) analysis.

REQUIRED DATA FILES (7 total):
1. Style Master: Contains style information (style_code, brand, category, gender, season, etc.)
2. SKU-EAN Master: Maps SKUs to EAN codes and sizes
3. Store Master: Store information and hierarchy 
4. Warehouse Master: Warehouse information and hierarchy
5. Daily Sales: Transaction-level sales data
6. Store Inventory: Current store inventory levels
7. Warehouse Inventory: Current warehouse inventory levels

ANALYTICS MODULES:

1. NOOS ANALYSIS (Never Out Of Stock):
- Identifies styles that should never be out of stock
- Compares system recommendations vs actual availability
- Parameters: Analysis period, minimum shelf life days
- Output: NOOS gaps, overlap analysis, potential sales loss

2. ROS ANALYSIS (Rate of Sale):
- Compares sales performance between healthy and broken size sets
- Healthy size set: Has pivotal sizes available (e.g., >75% availability)
- Broken size set: Missing key sizes (e.g., <75% availability)
- Output: Sales loss calculation, ROS comparison charts

3. SIZE SET GAP ANALYSIS:
- Analyzes size distribution and availability gaps
- Identifies optimal size mix for each style
- Parameters: Inventory date, season selection
- Output: Size availability heat maps, gap recommendations

CALCULATION METHODOLOGIES:

ROS Calculation:
- ROS = Total Quantity Sold / Live Days
- Healthy ROS: Sales rate when pivotal sizes are available
- Broken ROS: Sales rate when pivotal sizes are missing
- Sales Loss = (Healthy ROS x Broken Days) - Actual Broken Sales

Size Set Classification:
- Based on pivotal size availability thresholds
- Configurable thresholds (default: 75% for healthy, <75% for broken)
- Considers core sizes per category and gender

COMMON USE CASES:
- Inventory planning and optimization
- Sales gap identification
- Size mix optimization
- Category performance analysis
- Regional sales comparison
- Seasonal trend analysis
"""


@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(message: ChatMessage):
    """Chat with the AI assistant about the platform"""
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM API key not configured")
        
        session_id = message.session_id or str(uuid.uuid4())
        
        system_message = f"""You are an expert assistant for the Fashion Retail Gap Analysis Platform.
        
Use this knowledge base to answer questions accurately and helpfully:
{PLATFORM_KNOWLEDGE}

Guidelines:
- Be concise and practical
- Focus on actionable insights
- Explain technical concepts in simple terms
- If asked about data or calculations, refer to the platform's methodology
- If the question is outside the platform scope, politely redirect to platform features
- Always maintain a professional, helpful tone"""
        
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system_message
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=message.message)
        response = await chat.send_message(user_message)
        
        # Store chat history
        await get_db().chat_history.insert_one({
            "session_id": session_id,
            "user_message": message.message,
            "assistant_response": response,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return ChatResponse(response=response, session_id=session_id)
    
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        # Fallback response
        return ChatResponse(
            response=f"I apologize, but I'm having trouble processing your request. Error: {str(e)}. Please try again or check the documentation for help.",
            session_id=message.session_id or str(uuid.uuid4())
        )


@api_router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    history = await get_db().chat_history.find(
        {"session_id": session_id}, 
        {"_id": 0}
    ).sort("timestamp", 1).to_list(100)
    return history


# ==================== SFTP ADMIN ====================

class SFTPConfigModel(BaseModel):
    host: str = ""
    port: int = 22
    username: str = ""
    password: Optional[str] = None
    key_path: Optional[str] = None
    key_passphrase: Optional[str] = None
    base_path: str = "/incoming"
    processed_path: str = "/processed"
    failed_path: str = "/failed"
    poll_interval_minutes: int = 30
    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 30.0
    pool_size: int = 5
    ssl_mode: str = "auto"
    timeout: int = 30
    alert_emails: str = ""


@api_router.get("/admin/sftp/status")
async def get_sftp_status():
    """Get SFTP connection and scheduler status"""
    config_doc = await get_db().sftp_config.find_one({"_id": "main"}, {"_id": 0})
    if config_doc:
        sftp_service.load_config(config_doc)
    conn_info = sftp_service.test_connection()
    return {
        "demo_mode": sftp_service.demo_mode,
        "host": sftp_service.host or "Not configured",
        "scheduler": sftp_scheduler.status,
        "connection": conn_info,
        "pool": sftp_service.pool_stats,
        "ssl_mode": sftp_service.ssl_mode,
        "retry_config": sftp_service.retry_config,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@api_router.get("/admin/sftp/config")
async def get_sftp_config():
    """Get SFTP configuration"""
    config_doc = await get_db().sftp_config.find_one({"_id": "main"}, {"_id": 0})
    return config_doc or {}


@api_router.post("/admin/sftp/config")
async def save_sftp_config(config: SFTPConfigModel):
    """Save SFTP configuration"""
    doc = config.model_dump()
    await get_db().sftp_config.update_one({"_id": "main"}, {"$set": doc}, upsert=True)
    sftp_service.load_config(doc)
    return {"message": "SFTP configuration saved"}


@api_router.post("/admin/sftp/test-connection")
async def test_sftp_connection():
    """Test SFTP server connectivity"""
    config_doc = await get_db().sftp_config.find_one({"_id": "main"}, {"_id": 0})
    if config_doc:
        sftp_service.load_config(config_doc)
    return sftp_service.test_connection()


@api_router.post("/admin/sftp/trigger")
async def trigger_sftp_processing():
    """Manually trigger one SFTP processing cycle"""
    config_doc = await get_db().sftp_config.find_one({"_id": "main"}, {"_id": 0})
    if config_doc:
        sftp_service.load_config(config_doc)

    if sftp_service.demo_mode:
        records = sftp_service.generate_demo_cycle()
        for r in records:
            await get_db().sftp_logs.insert_one(r)
        return {
            "message": f"Demo cycle: processed {len(records)} files",
            "total": len(records),
            "success": sum(1 for r in records if r['status'] == 'success'),
            "failed": sum(1 for r in records if r['status'] != 'success'),
        }
    else:
        return {"message": "Real SFTP processing not yet implemented"}


@api_router.post("/admin/sftp/scheduler/start")
async def start_sftp_scheduler():
    """Start the SFTP polling scheduler"""
    config_doc = await get_db().sftp_config.find_one({"_id": "main"}, {"_id": 0})
    interval = 30
    if config_doc:
        sftp_service.load_config(config_doc)
        interval = config_doc.get('poll_interval_minutes', 30)
    sftp_scheduler.configure(db, sftp_service)
    sftp_scheduler.start(interval_minutes=interval)
    return {"message": "Scheduler started", "interval_minutes": interval}


@api_router.post("/admin/sftp/scheduler/stop")
async def stop_sftp_scheduler():
    """Stop the SFTP polling scheduler"""
    sftp_scheduler.stop()
    return {"message": "Scheduler stopped"}


@api_router.get("/admin/sftp/logs")
async def get_sftp_logs(
    days: int = 7,
    status: Optional[str] = None,
    file_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 200,
):
    """Get SFTP processing logs with optional date range filter"""
    query: Dict[str, Any] = {}
    if start_date:
        ts_q: Dict[str, str] = {"$gte": start_date}
        if end_date:
            ts_q["$lte"] = end_date + "T23:59:59"
        query["processed_at"] = ts_q
    else:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        query["processed_at"] = {"$gte": cutoff}
    if status:
        query["status"] = status
    if file_type:
        query["file_type"] = file_type

    logs = await get_db().sftp_logs.find(query, {"_id": 0}).sort("processed_at", -1).to_list(limit)
    return logs


@api_router.get("/admin/sftp/stats")
async def get_sftp_stats():
    """Get SFTP processing statistics for the dashboard"""
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()
    prev_week_start = (now - timedelta(days=14)).isoformat()

    # Current week logs
    logs = await get_db().sftp_logs.find(
        {"processed_at": {"$gte": week_ago}}, {"_id": 0}
    ).to_list(2000)

    # Previous week logs for comparison
    prev_logs = await get_db().sftp_logs.find(
        {"processed_at": {"$gte": prev_week_start, "$lt": week_ago}}, {"_id": 0}
    ).to_list(2000)

    total = len(logs)
    success = sum(1 for l in logs if l.get('status') == 'success')
    failed = total - success
    total_rows = sum(l.get('rows_processed', 0) for l in logs)

    prev_total = len(prev_logs)
    prev_success = sum(1 for l in prev_logs if l.get('status') == 'success')
    curr_rate = (success / total * 100) if total > 0 else 0
    prev_rate = (prev_success / prev_total * 100) if prev_total > 0 else 0

    # Group by type
    by_type = {}
    for l in logs:
        ft = l.get('file_type', 'unknown')
        if ft not in by_type:
            by_type[ft] = {'total': 0, 'success': 0, 'failed': 0, 'rows': 0, 'errors': 0}
        by_type[ft]['total'] += 1
        if l.get('status') == 'success':
            by_type[ft]['success'] += 1
        else:
            by_type[ft]['failed'] += 1
        by_type[ft]['rows'] += l.get('rows_processed', 0)
        if l.get('error_message'):
            by_type[ft]['errors'] += 1

    # Group by day for trend
    by_day = {}
    for l in logs:
        day = l.get('processed_at', '')[:10]
        if day not in by_day:
            by_day[day] = {'date': day, 'total': 0, 'success': 0, 'failed': 0, 'rows': 0}
        by_day[day]['total'] += 1
        if l.get('status') == 'success':
            by_day[day]['success'] += 1
        else:
            by_day[day]['failed'] += 1
        by_day[day]['rows'] += l.get('rows_processed', 0)

    # Store SLA — which stores have uploaded today
    today = now.strftime('%Y-%m-%d')
    today_logs = [l for l in logs if l.get('processed_at', '').startswith(today)]
    stores_uploaded = set(l.get('store_code') for l in today_logs if l.get('store_code'))

    # Speed metrics
    speeds = [l.get('speed_mbps', 0) for l in logs if l.get('speed_mbps', 0) > 0]
    avg_speed = round(sum(speeds) / len(speeds), 2) if speeds else 0
    total_size_mb = round(sum(l.get('file_size', 0) for l in logs) / 1_000_000, 2)

    # Malformed and duplicate counts
    malformed_count = sum(1 for l in logs if l.get('status') == 'malformed')
    duplicate_count = sum(1 for l in logs if l.get('status') == 'duplicate')

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "malformed": malformed_count,
        "duplicates": duplicate_count,
        "total_rows": total_rows,
        "success_rate": round(curr_rate, 1),
        "success_rate_change": round(curr_rate - prev_rate, 1),
        "by_type": by_type,
        "trend": sorted(by_day.values(), key=lambda x: x['date']),
        "stores_uploaded_today": sorted(list(stores_uploaded)),
        "stores_total": 10,
        "avg_speed_mbps": avg_speed,
        "total_size_mb": total_size_mb,
    }


@api_router.post("/admin/sftp/seed-demo")
async def seed_demo_data():
    """Seed SFTP logs with 7 days of demo data"""
    records = sftp_service.generate_demo_history(days=7)
    if records:
        await get_db().sftp_logs.delete_many({})
        for r in records:
            await get_db().sftp_logs.insert_one(r)
    return {"message": f"Seeded {len(records)} demo records", "count": len(records)}


@api_router.post("/admin/sftp/retry-failed")
async def retry_failed_files():
    """Retry recently failed files"""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    failed = await get_db().sftp_logs.find(
        {"status": "error", "processed_at": {"$gte": cutoff}}, {"_id": 0}
    ).to_list(100)

    retried = 0
    for log in failed:
        if sftp_service.demo_mode and random.random() < 0.7:
            await get_db().sftp_logs.insert_one({
                **log,
                'status': 'success',
                'rows_processed': random.randint(500, 3000),
                'error_message': None,
                'processed_at': datetime.now(timezone.utc).isoformat(),
            })
            retried += 1

    return {"message": f"Retried {retried}/{len(failed)} failed files", "retried": retried}


# ==================== DATA QUALITY & SLA ====================

DEMO_STORES = [
    {"code": "ST001", "name": "Store Mumbai Central", "region": "West"},
    {"code": "ST002", "name": "Store Delhi CP", "region": "North"},
    {"code": "ST003", "name": "Store Bangalore MG", "region": "South"},
    {"code": "ST004", "name": "Store Chennai T.Nagar", "region": "South"},
    {"code": "ST005", "name": "Store Kolkata Park St", "region": "East"},
    {"code": "ST006", "name": "Store Hyderabad Banj", "region": "South"},
    {"code": "ST007", "name": "Store Pune FC Road", "region": "West"},
    {"code": "ST008", "name": "Store Ahmedabad CG", "region": "West"},
    {"code": "ST009", "name": "Store Jaipur MI Road", "region": "North"},
    {"code": "ST010", "name": "Store Lucknow Hazrat", "region": "North"},
]

QUALITY_ISSUES_POOL = [
    "Missing size breakdown in inventory file",
    "Incorrect MRP values detected (negative or zero)",
    "Duplicate transaction IDs found",
    "Date format mismatch in sales file",
    "Inventory file missing store_code column",
    "Sales quantity exceeds stock on hand",
    "Revenue does not match quantity * MRP",
    "SKU codes not found in master data",
    "File uploaded after SLA deadline (10:00 AM)",
    "Incomplete records — some rows have null values",
]


@api_router.get("/admin/quality/store-uploads/{date}")
async def get_store_uploads(date: str):
    """Get per-store upload status with quality scores for a given date."""
    # Find logs for the requested date
    logs = await get_db().sftp_logs.find(
        {"file_date": date}, {"_id": 0}
    ).to_list(2000)

    # Also check logs by processed_at date if file_date yields nothing
    if not logs:
        logs = await get_db().sftp_logs.find(
            {"processed_at": {"$regex": f"^{date}"}}, {"_id": 0}
        ).to_list(2000)

    # Build per-store lookup
    store_logs: Dict[str, List] = {}
    for l in logs:
        sc = l.get('store_code')
        if sc:
            store_logs.setdefault(sc, []).append(l)

    # Get 7-day history for quality scoring
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    history = await get_db().sftp_logs.find(
        {"processed_at": {"$gte": week_ago}}, {"_id": 0}
    ).to_list(5000)

    store_history: Dict[str, List] = {}
    for l in history:
        sc = l.get('store_code')
        if sc:
            store_history.setdefault(sc, []).append(l)

    result = []
    for store_info in DEMO_STORES:
        code = store_info["code"]
        day_logs = store_logs.get(code, [])
        hist_logs = store_history.get(code, [])

        sales_log = next((l for l in day_logs if l.get('file_type') == 'daily_sales'), None)
        inv_log = next((l for l in day_logs if l.get('file_type') == 'store_inventory'), None)

        # Determine status
        if sales_log and inv_log:
            if sales_log.get('status') == 'success' and inv_log.get('status') == 'success':
                status = 'uploaded'
            else:
                status = 'partial'
        elif sales_log or inv_log:
            status = 'partial'
        else:
            status = 'missing'

        upload_time = None
        if sales_log:
            ts = sales_log.get('processed_at', '')
            if 'T' in ts:
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    upload_time = dt.strftime('%I:%M %p')
                    # Check if late (after 10 AM UTC)
                    if dt.hour >= 10 and status == 'uploaded':
                        status = 'late'
                except Exception:
                    pass

        # Quality scores from 7-day history
        total_hist = len(hist_logs)
        success_hist = sum(1 for l in hist_logs if l.get('status') == 'success')
        error_hist = sum(1 for l in hist_logs if l.get('error_message'))
        total_rows = sum(l.get('rows_processed', 0) for l in hist_logs)
        rejected_rows = sum(l.get('rows_rejected', 0) for l in hist_logs)

        completeness = min(100, int((success_hist / max(total_hist, 1)) * 100))
        accuracy = min(100, int(((total_rows - rejected_rows) / max(total_rows, 1)) * 100))
        timeliness = min(100, max(0, completeness - random.randint(0, 15)))
        quality_score = int((completeness * 0.35 + accuracy * 0.35 + timeliness * 0.30))

        # Pick relevant issues
        issues = []
        if status == 'missing':
            issues.append("No upload received today")
        if status == 'partial':
            if not inv_log:
                issues.append("Inventory file not uploaded")
            if not sales_log:
                issues.append("Sales file not uploaded")
        if error_hist > 0:
            issues.append(random.choice(QUALITY_ISSUES_POOL))

        last_upload = None
        latest = sales_log or inv_log
        if latest:
            last_upload = latest.get('processed_at', '')[:16].replace('T', ' ')

        result.append({
            "code": code,
            "name": store_info["name"],
            "region": store_info["region"],
            "status": status,
            "uploadTime": upload_time,
            "salesStatus": "success" if sales_log and sales_log.get('status') == 'success' else "missing",
            "inventoryStatus": "success" if inv_log and inv_log.get('status') == 'success' else "missing",
            "qualityScore": quality_score if status != 'missing' else 0,
            "completeness": completeness if status != 'missing' else 0,
            "accuracy": accuracy if status != 'missing' else 0,
            "timeliness": timeliness if status != 'missing' else 0,
            "lastUpload": last_upload,
            "issues": issues,
        })

    return result


@api_router.get("/admin/quality/sla-metrics")
async def get_sla_metrics():
    """Get SLA compliance metrics."""
    now = datetime.now(timezone.utc)
    today = now.strftime('%Y-%m-%d')
    week_ago = (now - timedelta(days=7)).isoformat()
    prev_week = (now - timedelta(days=14)).isoformat()

    # Today's logs
    today_logs = await get_db().sftp_logs.find(
        {"processed_at": {"$regex": f"^{today}"}}, {"_id": 0}
    ).to_list(500)

    # Also check by file_date
    if not today_logs:
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        today_logs = await get_db().sftp_logs.find(
            {"file_date": yesterday}, {"_id": 0}
        ).to_list(500)

    active_stores = len(DEMO_STORES)
    # Expected: 2 files per store (sales + inventory) + 2 warehouse files
    expected = active_stores * 2 + 2
    received = len([l for l in today_logs if l.get('status') == 'success'])
    on_time = len([l for l in today_logs if l.get('status') == 'success' and
                   'T' in l.get('processed_at', '') and
                   int(l.get('processed_at', 'T10').split('T')[1][:2]) < 10])

    compliance = round((received / max(expected, 1)) * 100, 1)

    # By file type
    by_type = []
    for ft, label in [('daily_sales', 'Daily Sales'), ('store_inventory', 'Store Inventory'), ('warehouse_inventory', 'WH Inventory')]:
        ft_logs = [l for l in today_logs if l.get('file_type') == ft]
        ft_success = len([l for l in ft_logs if l.get('status') == 'success'])
        ft_expected = active_stores if ft != 'warehouse_inventory' else 2
        by_type.append({
            "name": label,
            "expected": ft_expected,
            "received": ft_success,
            "compliance": round((ft_success / max(ft_expected, 1)) * 100, 1),
            "target": 95 if ft == 'daily_sales' else 90,
        })

    # Week-over-week trend
    this_week = await get_db().sftp_logs.find(
        {"processed_at": {"$gte": week_ago}}, {"_id": 0}
    ).to_list(2000)
    prev_week_logs = await get_db().sftp_logs.find(
        {"processed_at": {"$gte": prev_week, "$lt": week_ago}}, {"_id": 0}
    ).to_list(2000)

    tw_rate = (sum(1 for l in this_week if l.get('status') == 'success') / max(len(this_week), 1)) * 100
    pw_rate = (sum(1 for l in prev_week_logs if l.get('status') == 'success') / max(len(prev_week_logs), 1)) * 100
    trend = round(tw_rate - pw_rate, 1)

    return {
        "complianceRate": compliance,
        "expectedFiles": expected,
        "receivedFiles": received,
        "missingFiles": max(0, expected - received),
        "onTimeFiles": on_time,
        "lateFiles": max(0, received - on_time),
        "activeStores": active_stores,
        "byFileType": by_type,
        "trend": trend,
    }


@api_router.get("/admin/quality/scorecard")
async def get_quality_scorecard():
    """Get data quality scorecard across all dimensions."""
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    logs = await get_db().sftp_logs.find(
        {"processed_at": {"$gte": week_ago}}, {"_id": 0}
    ).to_list(5000)

    total = len(logs)
    success = sum(1 for l in logs if l.get('status') == 'success')
    total_rows = sum(l.get('rows_processed', 0) for l in logs)
    rejected_rows = sum(l.get('rows_rejected', 0) for l in logs)
    error_count = sum(1 for l in logs if l.get('error_message'))

    completeness_score = round((success / max(total, 1)) * 100, 1)
    accuracy_score = round(((total_rows - rejected_rows) / max(total_rows, 1)) * 100, 1)

    # Timeliness — % of files uploaded before 10 AM
    on_time = sum(1 for l in logs if 'T' in l.get('processed_at', '') and
                  int(l.get('processed_at', 'T10').split('T')[1][:2]) < 10)
    timeliness_score = round((on_time / max(total, 1)) * 100, 1)

    # Consistency — how many days had all expected files
    days = set(l.get('processed_at', '')[:10] for l in logs if l.get('processed_at'))
    full_days = 0
    for day in days:
        day_logs = [l for l in logs if l.get('processed_at', '').startswith(day)]
        stores_covered = set(l.get('store_code') for l in day_logs if l.get('store_code'))
        if len(stores_covered) >= 8:
            full_days += 1
    consistency_score = round((full_days / max(len(days), 1)) * 100, 1)

    # Validity — inverse of error rate
    validity_score = round(((total - error_count) / max(total, 1)) * 100, 1)

    overall = round(
        completeness_score * 0.25 +
        accuracy_score * 0.25 +
        timeliness_score * 0.20 +
        consistency_score * 0.15 +
        validity_score * 0.15
    , 1)

    def build_metric(current, target, issues_list):
        gap = max(0, round(target - current, 1))
        return {"current": current, "target": target, "gap": gap, "issues": issues_list}

    return {
        "overall": overall,
        "completeness": build_metric(completeness_score, 95, [
            {"description": "Missing files from stores", "impact": round(100 - completeness_score, 1)},
        ] if completeness_score < 95 else []),
        "accuracy": build_metric(accuracy_score, 95, [
            {"description": "Rows rejected due to validation errors", "impact": round(100 - accuracy_score, 1)},
        ] if accuracy_score < 95 else []),
        "timeliness": build_metric(timeliness_score, 90, [
            {"description": "Files uploaded after 10 AM SLA deadline", "impact": round(100 - timeliness_score, 1)},
        ] if timeliness_score < 90 else []),
        "consistency": build_metric(consistency_score, 90, [
            {"description": "Days with incomplete store coverage", "impact": round(100 - consistency_score, 1)},
        ] if consistency_score < 90 else []),
        "validity": build_metric(validity_score, 95, [
            {"description": "Files with processing errors", "impact": round(100 - validity_score, 1)},
        ] if validity_score < 95 else []),
        "recommendations": [
            "Send automated reminders to stores that miss the 10 AM upload deadline",
            "Implement column-level validation rules in CSV templates",
            "Schedule weekly data quality review meetings with store managers",
            "Add SKU master cross-reference checks before processing",
            "Create automated re-upload requests for failed files",
        ],
    }


# Include the router in the main app
api_router.include_router(core_logic_router)
api_router.include_router(replenishment_router)
api_router.include_router(doh_router)
api_router.include_router(planogram_router)
api_router.include_router(bi_router)
api_router.include_router(sftp_ext_router)
api_router.include_router(warehouse_router)
app.include_router(api_router)
app.include_router(auth_router)
app.include_router(tenant_router)
app.include_router(user_router)

# CORS must be added BEFORE tenant middleware (Starlette processes middleware LIFO)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant middleware — identifies tenant from header / JWT / subdomain
app.add_middleware(TenantMiddleware)


# ==================== STARTUP / SHUTDOWN ====================

async def _ensure_default_tenant():
    """Create a default 'demo' tenant so existing data keeps working."""
    shared = client[SHARED_DB_NAME]
    existing = await shared.tenants.find_one({"tenant_id": "demo"})
    if existing:
        return
    logger.info("Creating default 'demo' tenant…")
    now_iso = datetime.now(timezone.utc).isoformat()
    await shared.tenants.insert_one({
        "tenant_id": "demo",
        "company_name": "Demo Company",
        "db_name": _default_db_name,   # point demo tenant at existing DB
        "subdomain": "demo",
        "plan_type": "enterprise",
        "status": "active",
        "created_at": now_iso,
        "updated_at": now_iso,
    })
    # Create demo admin user
    import bcrypt
    hashed = bcrypt.hashpw(b"demo1234", bcrypt.gensalt()).decode()
    await shared.users.update_one(
        {"email": "admin@demo.com"},
        {"$set": {
            "email": "admin@demo.com",
            "username": "admin",
            "hashed_password": hashed,
            "full_name": "Demo Admin",
            "created_at": now_iso,
        }},
        upsert=True,
    )
    await shared.user_tenants.update_one(
        {"email": "admin@demo.com", "tenant_id": "demo"},
        {"$set": {
            "email": "admin@demo.com",
            "user_id": "demo_admin",
            "tenant_id": "demo",
            "role": "admin",
            "is_active": True,
            "assigned_at": now_iso,
        }},
        upsert=True,
    )
    logger.info("Default 'demo' tenant created (DB: %s)", _default_db_name)


@app.on_event("startup")
async def startup():
    await ensure_shared_indexes()
    await _ensure_default_tenant()
    await seed_rbac()
    init_core_logic(client)
    init_replenishment(client)
    init_doh(client)
    init_planogram(client)
    init_bi(client)
    init_sftp_routes(get_db, sftp_service)
    init_warehouse(client, get_db)
    logger.info("Multi-tenant startup complete")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
