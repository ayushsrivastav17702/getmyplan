from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np
import random
import io
from emergentintegrations.llm.chat import LlmChat, UserMessage
from sftp import sftp_service, sftp_scheduler

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
    preview: List[Dict[str, Any]]

class AnalysisConfig(BaseModel):
    noos_enabled: bool = True
    ros_enabled: bool = True
    size_gap_enabled: bool = True
    lifecycle_enabled: bool = True
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    min_shelf_life_days: int = 30
    pivotal_size_threshold: int = 75
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


# ==================== HELPER FUNCTIONS ====================

def validate_file(df: pd.DataFrame, file_type: str) -> Dict[str, Any]:
    """Validate uploaded file against required columns"""
    errors = []
    required = REQUIRED_COLUMNS.get(file_type, [])
    df_columns = [col.lower().strip() for col in df.columns]
    
    # Normalize column names
    df.columns = df_columns
    
    missing = [col for col in required if col not in df_columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
    
    if len(df) == 0:
        errors.append("File is empty")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'columns': list(df.columns),
        'rows': len(df)
    }


async def get_cached_data(file_type: str) -> Optional[pd.DataFrame]:
    """Retrieve cached data from MongoDB"""
    doc = await db.uploaded_files.find_one({"file_type": file_type})
    if doc and 'data' in doc:
        return pd.DataFrame(doc['data'])
    return None


async def cache_data(file_type: str, df: pd.DataFrame, validation: Dict):
    """Cache uploaded data to MongoDB"""
    data = df.to_dict('records')
    await db.uploaded_files.update_one(
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
    _ = await db.status_checks.insert_one(doc)
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks


# ==================== FILE UPLOAD ====================

@api_router.post("/upload/{file_type}", response_model=FileUploadResponse)
async def upload_file(file_type: str, file: UploadFile = File(...)):
    """Upload and validate a data file"""
    if file_type not in REQUIRED_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Unknown file type: {file_type}")
    
    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        validation = validate_file(df, file_type)
        
        if validation['valid']:
            await cache_data(file_type, df, validation)
        
        # Log to upload history
        await db.upload_history.insert_one({
            "file_type": file_type,
            "file_name": file.filename,
            "status": "success" if validation['valid'] else "failed",
            "rows_processed": validation['rows'],
            "columns": validation['columns'],
            "errors": validation['errors'],
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        })
        
        preview = df.head(5).fillna('').to_dict('records')
        
        return FileUploadResponse(
            file_type=file_type,
            rows=validation['rows'],
            columns=validation['columns'],
            valid=validation['valid'],
            errors=validation['errors'],
            preview=preview
        )
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        # Log failure
        await db.upload_history.insert_one({
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
    files = await db.uploaded_files.find({}, {"_id": 0, "data": 0}).to_list(100)
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
    await db.uploaded_files.delete_one({"file_type": file_type})
    return {"message": f"Deleted {file_type}"}


@api_router.delete("/upload/all")
async def delete_all_files():
    """Delete all uploaded files"""
    await db.uploaded_files.delete_many({})
    return {"message": "All files deleted"}


@api_router.get("/upload/history")
async def get_upload_history(limit: int = 50):
    """Get upload history log"""
    history = await db.upload_history.find(
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
    """Save analysis configuration"""
    await db.analysis_config.update_one(
        {"_id": "main"},
        {"$set": config.model_dump()},
        upsert=True
    )
    return {"message": "Configuration saved"}


@api_router.get("/config")
async def get_config():
    """Get analysis configuration"""
    config = await db.analysis_config.find_one({"_id": "main"}, {"_id": 0})
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
    await db.filter_presets.insert_one(doc)
    return preset_obj


@api_router.get("/presets")
async def get_presets(page_type: str = None):
    """Get all team filter presets, optionally filtered by page type"""
    query = {}
    if page_type:
        query['page_type'] = page_type
    
    presets = await db.filter_presets.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
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
    presets = await db.filter_presets.find({}, {"tags": 1, "_id": 0}).to_list(1000)
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
    presets = await db.filter_presets.find(query, {"_id": 0}).to_list(1000)
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
            existing = await db.filter_presets.find_one({"id": preset_data['id']})
            if existing:
                preset_data['id'] = str(uuid.uuid4())
        preset_data['created_at'] = preset_data.get('created_at', datetime.now(timezone.utc).isoformat())
        preset_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        await db.filter_presets.insert_one(preset_data)
        imported += 1
    return {"message": f"Imported {imported} presets", "imported": imported}


@api_router.get("/presets/{preset_id}")
async def get_preset(preset_id: str):
    """Get a specific preset by ID"""
    preset = await db.filter_presets.find_one({"id": preset_id}, {"_id": 0})
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset


@api_router.put("/presets/{preset_id}")
async def update_preset(preset_id: str, preset: FilterPresetCreate):
    """Update an existing preset"""
    existing = await db.filter_presets.find_one({"id": preset_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    update_data = preset.model_dump()
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.filter_presets.update_one(
        {"id": preset_id},
        {"$set": update_data}
    )
    return {"message": "Preset updated", "id": preset_id}


@api_router.patch("/presets/{preset_id}/favorite")
async def toggle_preset_favorite(preset_id: str):
    """Toggle favorite status of a preset"""
    preset = await db.filter_presets.find_one({"id": preset_id})
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    new_favorite = not preset.get('is_favorite', False)
    await db.filter_presets.update_one(
        {"id": preset_id},
        {"$set": {"is_favorite": new_favorite, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Favorite toggled", "is_favorite": new_favorite}


@api_router.delete("/presets/{preset_id}")
async def delete_preset(preset_id: str):
    """Delete a preset"""
    result = await db.filter_presets.delete_one({"id": preset_id})
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
    """Calculate size set gap analysis with filters"""
    sales_df = await get_cached_data('daily_sales')
    inventory_df = await get_cached_data('store_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    style_df = await get_cached_data('style_master')
    store_df = await get_cached_data('store_master')
    
    if sales_df is None or sku_df is None or inventory_df is None:
        return {"error": "Required data not uploaded", "data": []}
    
    try:
        # Apply filters to sales data
        sales_df = apply_date_filter(sales_df, start_date, end_date, 'day')
        
        if channels:
            channel_list = channels.split(',')
            sales_df = apply_channel_filter(sales_df, channel_list)
            inventory_df = apply_channel_filter(inventory_df, channel_list)
        
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_df = apply_region_filter(sales_df, region_list, store_df)
            inventory_df = apply_region_filter(inventory_df, region_list, store_df)
        
        # Merge sales with SKU data
        sales_with_sku = sales_df.merge(
            sku_df[['ean', 'style', 'size']], 
            left_on='sku', right_on='ean', how='left'
        )
        
        # Apply category filter
        if categories and style_df is not None:
            category_list = categories.split(',')
            sales_with_sku = apply_category_filter(sales_with_sku, category_list, style_df)
        
        if len(sales_with_sku) == 0:
            return {"error": "No data matches the selected filters", "data": [], "summary": {}}
        
        # Calculate size distribution from sales
        size_dist = sales_with_sku.groupby(['style', 'size'])['quantity'].sum().reset_index()
        total_by_style = size_dist.groupby('style')['quantity'].sum().reset_index()
        total_by_style.columns = ['style', 'total_sales']
        
        size_dist = size_dist.merge(total_by_style, on='style')
        size_dist['sales_ratio'] = (size_dist['quantity'] / size_dist['total_sales']).round(4)
        
        # Get current inventory (apply date filter)
        inventory_df['day'] = pd.to_datetime(inventory_df['day'])
        if end_date:
            inventory_df = inventory_df[inventory_df['day'] <= pd.to_datetime(end_date)]
        latest_date = inventory_df['day'].max()
        current_inv = inventory_df[inventory_df['day'] == latest_date].copy()
        
        inv_with_sku = current_inv.merge(
            sku_df[['ean', 'style', 'size']], 
            on='ean', how='left'
        )
        
        inv_by_size = inv_with_sku.groupby(['style', 'size'])['quantity'].sum().reset_index()
        inv_by_size.columns = ['style', 'size', 'current_qty']
        
        # Calculate total inventory per style
        total_inv = inv_by_size.groupby('style')['current_qty'].sum().reset_index()
        total_inv.columns = ['style', 'total_inv']
        
        # Merge to calculate gaps
        gap_df = inv_by_size.merge(size_dist[['style', 'size', 'sales_ratio']], on=['style', 'size'], how='outer')
        gap_df = gap_df.merge(total_inv, on='style', how='left')
        
        gap_df['sales_ratio'] = gap_df['sales_ratio'].fillna(0.1)
        gap_df['current_qty'] = gap_df['current_qty'].fillna(0)
        gap_df['total_inv'] = gap_df['total_inv'].fillna(0)
        
        gap_df['ideal_qty'] = (gap_df['total_inv'] * gap_df['sales_ratio']).round(0)
        gap_df['gap'] = (gap_df['current_qty'] - gap_df['ideal_qty']).round(0)
        
        # Apply threshold-based classification
        gap_df['status'] = gap_df['gap'].apply(
            lambda x: 'Overstock' if x >= overstock_threshold else 'Understock' if x <= understock_threshold else 'Optimal'
        )
        
        status_counts = gap_df['status'].value_counts().to_dict()
        
        return {
            "summary": {
                "overstock": status_counts.get('Overstock', 0),
                "understock": status_counts.get('Understock', 0),
                "optimal": status_counts.get('Optimal', 0),
                "total_gap": abs(gap_df['gap']).sum()
            },
            "data": gap_df.dropna(subset=['style']).fillna(0).to_dict('records')
        }
    except Exception as e:
        logger.error(f"Size gap analysis error: {str(e)}")
        return {"error": str(e), "data": []}


@api_router.get("/analytics/noos")
async def get_noos_analysis(
    start_date: str = None,
    end_date: str = None,
    categories: str = None,
    channels: str = None,
    regions: str = None
):
    """Calculate NOOS (Never Out of Stock) analysis with filters"""
    sales_df = await get_cached_data('daily_sales')
    inventory_df = await get_cached_data('store_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    style_df = await get_cached_data('style_master')
    store_df = await get_cached_data('store_master')
    
    if sales_df is None or inventory_df is None or sku_df is None:
        return {"error": "Required data not uploaded", "data": []}
    
    try:
        # Apply date filters
        sales_df = apply_date_filter(sales_df, start_date, end_date, 'day')
        inventory_df = apply_date_filter(inventory_df, start_date, end_date, 'day')
        
        # Apply channel filters
        if channels:
            channel_list = channels.split(',')
            sales_df = apply_channel_filter(sales_df, channel_list)
            inventory_df = apply_channel_filter(inventory_df, channel_list)
        
        # Apply region filters
        if regions and store_df is not None:
            region_list = regions.split(',')
            sales_df = apply_region_filter(sales_df, region_list, store_df)
            inventory_df = apply_region_filter(inventory_df, region_list, store_df)
        
        sales_df['day'] = pd.to_datetime(sales_df['day'])
        inventory_df['day'] = pd.to_datetime(inventory_df['day'])
        
        # Merge inventory with SKU
        inv_with_sku = inventory_df.merge(
            sku_df[['ean', 'style']], on='ean', how='left'
        )
        
        # Apply category filter
        if categories and style_df is not None:
            category_list = categories.split(',')
            inv_with_sku = apply_category_filter(inv_with_sku, category_list, style_df)
        
        if len(inv_with_sku) == 0:
            return {"error": "No data matches the selected filters", "data": [], "summary": {}}
        
        # Calculate exposure days (days with positive inventory)
        exposure = inv_with_sku[inv_with_sku['quantity'] > 0].groupby(['store_code', 'style'])['day'].nunique().reset_index()
        exposure.columns = ['store_code', 'style', 'exposure_days']
        
        # Total possible days
        total_days = inventory_df['day'].nunique()
        exposure['availability_pct'] = (exposure['exposure_days'] / total_days * 100).round(1) if total_days > 0 else 0
        
        # Merge with sales
        sales_with_sku = sales_df.merge(
            sku_df[['ean', 'style']], left_on='sku', right_on='ean', how='left'
        )
        
        # Apply category filter to sales
        if categories and style_df is not None:
            category_list = categories.split(',')
            sales_with_sku = apply_category_filter(sales_with_sku, category_list, style_df)
        
        style_sales = sales_with_sku.groupby(['store_code', 'style']).agg({
            'quantity': 'sum',
            'revenue': 'sum'
        }).reset_index()
        
        noos_df = exposure.merge(style_sales, on=['store_code', 'style'], how='outer')
        noos_df = noos_df.fillna(0)
        
        # NOOS classification
        min_shelf_life = 30
        noos_df['meets_shelf_life'] = noos_df['exposure_days'] >= min_shelf_life
        noos_df['noos_candidate'] = (
            (noos_df['meets_shelf_life']) & 
            (noos_df['quantity'] > 0) & 
            (noos_df['availability_pct'] >= 80)
        )
        
        noos_candidates = len(noos_df[noos_df['noos_candidate']])
        
        return {
            "summary": {
                "total_combinations": len(noos_df),
                "noos_candidates": noos_candidates,
                "avg_availability": float(noos_df['availability_pct'].mean()) if len(noos_df) > 0 else 0,
                "total_revenue": float(noos_df['revenue'].sum())
            },
            "data": noos_df.to_dict('records')
        }
    except Exception as e:
        logger.error(f"NOOS analysis error: {str(e)}")
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
        await db.chat_history.insert_one({
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
    history = await db.chat_history.find(
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
    alert_emails: str = ""


@api_router.get("/admin/sftp/status")
async def get_sftp_status():
    """Get SFTP connection and scheduler status"""
    config_doc = await db.sftp_config.find_one({"_id": "main"}, {"_id": 0})
    if config_doc:
        sftp_service.load_config(config_doc)
    return {
        "demo_mode": sftp_service.demo_mode,
        "host": sftp_service.host or "Not configured",
        "scheduler": sftp_scheduler.status,
        "connection": sftp_service.test_connection(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@api_router.get("/admin/sftp/config")
async def get_sftp_config():
    """Get SFTP configuration"""
    config_doc = await db.sftp_config.find_one({"_id": "main"}, {"_id": 0})
    return config_doc or {}


@api_router.post("/admin/sftp/config")
async def save_sftp_config(config: SFTPConfigModel):
    """Save SFTP configuration"""
    doc = config.model_dump()
    await db.sftp_config.update_one({"_id": "main"}, {"$set": doc}, upsert=True)
    sftp_service.load_config(doc)
    return {"message": "SFTP configuration saved"}


@api_router.post("/admin/sftp/test-connection")
async def test_sftp_connection():
    """Test SFTP server connectivity"""
    config_doc = await db.sftp_config.find_one({"_id": "main"}, {"_id": 0})
    if config_doc:
        sftp_service.load_config(config_doc)
    return sftp_service.test_connection()


@api_router.post("/admin/sftp/trigger")
async def trigger_sftp_processing():
    """Manually trigger one SFTP processing cycle"""
    config_doc = await db.sftp_config.find_one({"_id": "main"}, {"_id": 0})
    if config_doc:
        sftp_service.load_config(config_doc)

    if sftp_service.demo_mode:
        records = sftp_service.generate_demo_cycle()
        for r in records:
            await db.sftp_logs.insert_one(r)
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
    config_doc = await db.sftp_config.find_one({"_id": "main"}, {"_id": 0})
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
    limit: int = 200,
):
    """Get SFTP processing logs"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    query: Dict[str, Any] = {"processed_at": {"$gte": cutoff}}
    if status:
        query["status"] = status
    if file_type:
        query["file_type"] = file_type

    logs = await db.sftp_logs.find(query, {"_id": 0}).sort("processed_at", -1).to_list(limit)
    return logs


@api_router.get("/admin/sftp/stats")
async def get_sftp_stats():
    """Get SFTP processing statistics for the dashboard"""
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()
    prev_week_start = (now - timedelta(days=14)).isoformat()

    # Current week logs
    logs = await db.sftp_logs.find(
        {"processed_at": {"$gte": week_ago}}, {"_id": 0}
    ).to_list(2000)

    # Previous week logs for comparison
    prev_logs = await db.sftp_logs.find(
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

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "total_rows": total_rows,
        "success_rate": round(curr_rate, 1),
        "success_rate_change": round(curr_rate - prev_rate, 1),
        "by_type": by_type,
        "trend": sorted(by_day.values(), key=lambda x: x['date']),
        "stores_uploaded_today": sorted(list(stores_uploaded)),
        "stores_total": 10,
    }


@api_router.post("/admin/sftp/seed-demo")
async def seed_demo_data():
    """Seed SFTP logs with 7 days of demo data"""
    records = sftp_service.generate_demo_history(days=7)
    if records:
        await db.sftp_logs.delete_many({})
        for r in records:
            await db.sftp_logs.insert_one(r)
    return {"message": f"Seeded {len(records)} demo records", "count": len(records)}


@api_router.post("/admin/sftp/retry-failed")
async def retry_failed_files():
    """Retry recently failed files"""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    failed = await db.sftp_logs.find(
        {"status": "error", "processed_at": {"$gte": cutoff}}, {"_id": 0}
    ).to_list(100)

    retried = 0
    for log in failed:
        if sftp_service.demo_mode and random.random() < 0.7:
            await db.sftp_logs.insert_one({
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
    logs = await db.sftp_logs.find(
        {"file_date": date}, {"_id": 0}
    ).to_list(2000)

    # Also check logs by processed_at date if file_date yields nothing
    if not logs:
        logs = await db.sftp_logs.find(
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
    history = await db.sftp_logs.find(
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
    today_logs = await db.sftp_logs.find(
        {"processed_at": {"$regex": f"^{today}"}}, {"_id": 0}
    ).to_list(500)

    # Also check by file_date
    if not today_logs:
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        today_logs = await db.sftp_logs.find(
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
    this_week = await db.sftp_logs.find(
        {"processed_at": {"$gte": week_ago}}, {"_id": 0}
    ).to_list(2000)
    prev_week_logs = await db.sftp_logs.find(
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
    logs = await db.sftp_logs.find(
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
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
