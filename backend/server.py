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
import io
from emergentintegrations.llm.chat import LlmChat, UserMessage

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


# ==================== ANALYTICS ====================

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
async def get_ros_analysis():
    """Calculate Rate of Sale analysis"""
    sales_df = await get_cached_data('daily_sales')
    inventory_df = await get_cached_data('store_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    
    if sales_df is None or sku_df is None:
        return {"error": "Required data not uploaded", "data": []}
    
    try:
        # Convert dates
        sales_df['day'] = pd.to_datetime(sales_df['day'])
        
        # Merge sales with SKU data
        sales_with_sku = sales_df.merge(
            sku_df[['ean', 'style', 'size']], 
            left_on='sku', right_on='ean', how='left'
        )
        
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
async def get_size_gap_analysis():
    """Calculate size set gap analysis"""
    sales_df = await get_cached_data('daily_sales')
    inventory_df = await get_cached_data('store_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    
    if sales_df is None or sku_df is None or inventory_df is None:
        return {"error": "Required data not uploaded", "data": []}
    
    try:
        # Merge sales with SKU data
        sales_with_sku = sales_df.merge(
            sku_df[['ean', 'style', 'size']], 
            left_on='sku', right_on='ean', how='left'
        )
        
        # Calculate size distribution from sales
        size_dist = sales_with_sku.groupby(['style', 'size'])['quantity'].sum().reset_index()
        total_by_style = size_dist.groupby('style')['quantity'].sum().reset_index()
        total_by_style.columns = ['style', 'total_sales']
        
        size_dist = size_dist.merge(total_by_style, on='style')
        size_dist['sales_ratio'] = (size_dist['quantity'] / size_dist['total_sales']).round(4)
        
        # Get current inventory
        inventory_df['day'] = pd.to_datetime(inventory_df['day'])
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
        
        gap_df['status'] = gap_df['gap'].apply(
            lambda x: 'Overstock' if x > 5 else 'Understock' if x < -5 else 'Optimal'
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
async def get_noos_analysis():
    """Calculate NOOS (Never Out of Stock) analysis"""
    sales_df = await get_cached_data('daily_sales')
    inventory_df = await get_cached_data('store_inventory')
    sku_df = await get_cached_data('sku_ean_master')
    
    if sales_df is None or inventory_df is None or sku_df is None:
        return {"error": "Required data not uploaded", "data": []}
    
    try:
        sales_df['day'] = pd.to_datetime(sales_df['day'])
        inventory_df['day'] = pd.to_datetime(inventory_df['day'])
        
        # Merge inventory with SKU
        inv_with_sku = inventory_df.merge(
            sku_df[['ean', 'style']], on='ean', how='left'
        )
        
        # Calculate exposure days (days with positive inventory)
        exposure = inv_with_sku[inv_with_sku['quantity'] > 0].groupby(['store_code', 'style'])['day'].nunique().reset_index()
        exposure.columns = ['store_code', 'style', 'exposure_days']
        
        # Total possible days
        total_days = inventory_df['day'].nunique()
        exposure['availability_pct'] = (exposure['exposure_days'] / total_days * 100).round(1)
        
        # Merge with sales
        sales_with_sku = sales_df.merge(
            sku_df[['ean', 'style']], left_on='sku', right_on='ean', how='left'
        )
        
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
                "avg_availability": float(noos_df['availability_pct'].mean()),
                "total_revenue": float(noos_df['revenue'].sum())
            },
            "data": noos_df.to_dict('records')
        }
    except Exception as e:
        logger.error(f"NOOS analysis error: {str(e)}")
        return {"error": str(e), "data": []}


@api_router.get("/analytics/bi-dashboard")
async def get_bi_dashboard():
    """Get BI dashboard data"""
    sales_df = await get_cached_data('daily_sales')
    sku_df = await get_cached_data('sku_ean_master')
    store_df = await get_cached_data('store_master')
    
    if sales_df is None:
        return {"error": "Sales data not uploaded", "data": {}}
    
    try:
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
