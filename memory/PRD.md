# GetMyPlan - AI-Powered Retail Analytics Platform — PRD

## Original Problem Statement
Build a Fashion Retail Gap Analysis platform (branded as **GetMyPlan**) with React + FastAPI featuring CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, GPT-5.2 FAQ Chatbot, multi-tenant architecture, and role-based access control.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme for dashboard, Enterprise SaaS for marketing)
- **Backend**: FastAPI with Python/Pandas
- **Database**: MongoDB (multi-tenant: separate DB per tenant, shared registry in DB_NAME database)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2 (NO Recharts)
- **Auth**: JWT with bcrypt, RBAC with 8 built-in roles + custom roles + permission overrides
- **Email**: SMTP via Hostinger (smtp.hostinger.com:465, SSL, info@getmyplan.in)
- **Security**: Enterprise middleware stack (rate limiting, security headers, input sanitization, structured logging)

## Upload Types — Complete (10/10)

| # | Upload Type | Endpoint | Collection | Category |
|---|-------------|----------|------------|----------|
| 1 | Store Master | `POST /api/upload/v2/store-master` | `store_master` | Master |
| 2 | SKU Master | `POST /api/upload/v2/sku-master` | `sku_master` | Master |
| 3 | Warehouse Master | `POST /api/upload/v2/warehouse-master` | `warehouse_master` | Master |
| 4 | Style Master | `POST /api/upload/v2/style-master` | `style_master` | Master |
| 5 | Planogram | `POST /api/upload/v2/planogram` | `planogram` | Master |
| 6 | Daily Sales | `POST /api/upload/v2/daily-sales` | `daily_sales` | Daily |
| 7 | Store Inventory | `POST /api/upload/v2/store-inventory` | `store_inventory` | Daily |
| 8 | Warehouse Inventory | `POST /api/upload/v2/warehouse-inventory` | `warehouse_inventory` | Daily |
| 9 | COGS | `POST /api/upload/v2/cogs` | `cogs` | Daily |
| 10 | Open Orders | `POST /api/upload/v2/open-orders` | `open_orders` | Daily |

## V2 Data Bridge — Complete (9/9 modules)

All analytics modules use `get_cached_data()` V2→V1 bridge:
- `ai_demand.py`, `gap_analysis.py`, `stock_out.py`, `server.py` (exec) — Phase 53
- `core_logic.py`, `doh_analysis.py`, `bi_dashboard.py`, `planogram.py`, `replenishment.py` — Phase 56
- `warehouse.py` — Direct V2

## Completed Phases (Recent)

### Phase 56 — V2 Bridge Migration (Apr 2026)
- Fixed 5 modules to use V2→V1 data bridge
- **Testing: 22/22 PASS (Iteration 59)**

### Phase 57 — New Upload Types (Apr 2026)
- Added COGS, Planogram, Open Orders, Style Master V2 upload endpoints
- 75-rule validation, template downloads, MongoDB indexes for all new collections
- Frontend: 10-type dropdown, 5 master cards, 5 daily status cards
- **Testing: 26/26 PASS (Iteration 60)**

## Key Files
- `/app/backend/routes/upload.py` — All 10 V2 upload endpoints
- `/app/backend/services/upload_service.py` — 75-rule validation for 11 schemas
- `/app/backend/server.py` — V2 map, indexes, data bridge
- `/app/frontend/src/pages/DataUploadPage.jsx` — 10 upload types UI
- `/app/frontend/src/components/upload/DailyStatusCard.jsx` — 5 daily type cards
- `/app/frontend/src/components/upload/PreviousDaysList.jsx` — 5 status dots

## Prioritized Backlog

### P0 — Next
- Wire COGS into executive dashboard for true margin calculation (Revenue - COGS) / Revenue
- Wire planogram upload into planogram fill rate module (replace auto-derived norm)
- Wire open_orders into replenishment module (deduct in-pipeline stock from order qty)

### P1
- Forecast accuracy tracking (MAPE trend)
- Holiday/promotional calendar integration
- Custom validation rules per tenant (wire Data Quality Rules into upload pipeline)

### P2
- USER-18: MFA
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- User Funnel Analytics Dashboard

### P3
- Auto-scheduled SFTP uploads
- Chunked file uploads for >50MB files
- Async upload processing with job queues
- Pre-computed aggregation tables
