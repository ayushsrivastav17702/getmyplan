# GetMyPlan - AI-Powered Retail Analytics Platform — PRD

## Original Problem Statement
Build a Fashion Retail Gap Analysis platform (branded as **GetMyPlan**) with React + FastAPI featuring CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, GPT-5.2 FAQ Chatbot, multi-tenant architecture, and role-based access control.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme for dashboard, Enterprise SaaS for marketing)
- **Backend**: FastAPI with Python/Pandas
- **Database**: MongoDB (multi-tenant: separate DB per tenant, shared registry)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2 (NO Recharts)
- **Auth**: JWT with bcrypt, RBAC with 8 roles + custom roles
- **Email**: SMTP via Hostinger

## Data Architecture — Complete

### Upload Hub (10/10 Types)
| Upload Type | Endpoint | Collection | Category |
|-------------|----------|------------|----------|
| Store Master | `POST /api/upload/v2/store-master` | `store_master` | Master |
| SKU Master | `POST /api/upload/v2/sku-master` | `sku_master` | Master |
| Warehouse Master | `POST /api/upload/v2/warehouse-master` | `warehouse_master` | Master |
| Style Master | `POST /api/upload/v2/style-master` | `style_master` | Master |
| Planogram | `POST /api/upload/v2/planogram` | `planogram` | Master |
| Daily Sales | `POST /api/upload/v2/daily-sales` | `daily_sales` | Daily |
| Store Inventory | `POST /api/upload/v2/store-inventory` | `store_inventory` | Daily |
| Warehouse Inventory | `POST /api/upload/v2/warehouse-inventory` | `warehouse_inventory` | Daily |
| COGS | `POST /api/upload/v2/cogs` | `cogs` | Daily |
| Open Orders | `POST /api/upload/v2/open-orders` | `open_orders` | Daily |

### V2 Data Bridge — All 9 Modules Connected
### Cross-Module Wiring — All 3 Integrations Live
- COGS → Executive Dashboard (true margin: `(Revenue-COGS)/Revenue`)
- Planogram → Fill Rate (uploaded norms replace auto-derived)
- Open Orders → Replenishment (in-transit deducted from order qty)

## Recent Phases

### Phase 56 — V2 Bridge Migration (Apr 2026)
- Fixed 5 modules (core_logic, doh, bi, planogram, replenishment) to use V2 data bridge
- **Testing: 22/22 PASS (Iteration 59)**

### Phase 57 — New Upload Types (Apr 2026)
- Added COGS, Planogram, Open Orders, Style Master V2 with full validation
- **Testing: 26/26 PASS (Iteration 60)**

### Phase 58 — Wire Everything Together (Apr 2026)
- COGS → Executive KPIs: `margin_source`, `total_cogs`, `mrp_realisation_pct` fields
- Planogram upload → Fill Rate: `norm_source` field, prefers uploaded norms
- Open Orders → Replenishment: `total_in_transit`, `open_orders_source`, `in_transit_qty` per row
- **Testing: 26/26 PASS (Iteration 61)**

### Phase 60 — Admin Signup Notification (Apr 2026)
- Added `send_admin_signup_notification()` to SMTP email service
- Wired into `/api/signup/register` as background task — fires on every new tenant registration (including free trials)
- Email sent to `info@getmyplan.in` with company name, email, subdomain, tenant ID, plan type, timestamp
- **Testing: Verified via curl — both verification email and admin notification confirmed in logs**

### Phase 61 — Forecast Accuracy Tracking (Apr 2026)
- Auto-saves forecast snapshots to `forecast_snapshots` collection on every forecast generation
- New endpoint: `GET /api/analytics/ai-demand/forecast-accuracy` — compares snapshots vs actual monthly revenue, calculates MAPE
- Returns: per-snapshot MAPE, trend direction, grade (Excellent/Good/Fair/Needs Improvement), month-by-month errors
- New "Forecast Accuracy" tab in AI Demand Planning with KPIs, MAPE trend chart, forecast vs actual table, snapshot history
- **Testing: 27/27 PASS (Iteration 63)**

### Phase 62 — Gap Analysis UX Audit (Apr 2026)
- New endpoint: `GET /api/analytics/data-status` — returns per-file upload status for all 7 required file types
- Added Data Completeness progress bar (X/7 files with color-coded fill)
- Added Data Summary bar (Styles, Stores, Sales Records, Days History)
- Added actionable Missing Files checklist with green/red badges per file + "Upload Missing Files" CTA
- Added module readiness badges on tabs (Ready checkmark vs Locked lock icon based on file availability)
- Added clean header with "Back to Dashboard" breadcrumb + "Data Upload" button
- Preserved all existing analytics (ROS Gap, Size Gap, NOOS) untouched
- **Testing: 27/27 PASS (Iteration 63)**

### Phase 63 — Sidebar Redesign (Apr 2026)
- Extracted sidebar from inline App.js into dedicated `/components/Sidebar.jsx`
- Collapsible: 260px expanded / 72px collapsed with localStorage persistence
- Section grouping: MAIN, ANALYTICS, INVENTORY, OPERATIONS, ADMIN, TOOLS
- Workflow-ordered modules: Upload -> Executive -> Analytics -> Inventory -> Operations -> Admin
- Active page indicator (blue left bar + bg highlight)
- Keyboard shortcut: Ctrl+B toggle
- Hover tooltips in collapsed mode (CSS-only)
- Preserved RBAC, plan guards, upload status, tenant info, data files, user bar
- Dark theme (#0B1628) with proper contrast
- **Testing: 18/18 PASS, 1 INFO (Iteration 64)**

## Prioritized Backlog

### P1 — Next
- UI: Update Executive Dashboard KPI card to show "True Margin" vs "MRP Realisation" label
- UI: Update Replenishment formula display to include "- In Transit"
- Holiday/promotional calendar integration
- Custom validation rules per tenant

### P2
- USER-18: MFA
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- User Funnel Analytics Dashboard

### P3
- Auto-scheduled SFTP uploads
- Chunked file uploads for >50MB
- Async upload processing
- Pre-computed aggregation tables
