# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build the same app as the Streamlit Merchandising Gap Analysis app with better UI/UX using React + FastAPI. Features include CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, warehouse analysis, a GPT-5.2 FAQ Chatbot, redesigned data upload workflow with Master/Daily separation, and an SFTP Data Pipeline Monitor.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python
- **Database**: MongoDB (uploaded data, team presets, upload history, SFTP logs/config)
- **Local Storage**: Personal filter presets
- **AI Integration**: GPT 5.2 via Emergent LLM Key for FAQ Chatbot
- **Charts**: Chart.js + react-chartjs-2
- **SFTP**: paramiko + apscheduler (demo mode when unconfigured)

## Pages & Routes
| Route | Page | Description |
|-------|------|-------------|
| / | Getting Started | Landing page with app overview |
| /upload | Data Upload | Master vs Daily file upload with history |
| /config | Configuration | Analysis configuration |
| /core-logics | Core Logics | TrueROS + Store-Style ranking with charts |
| /gap-analysis | Gap Analysis | NOOS + Size Gap with charts |
| /bi-dashboards | BI Dashboards | Revenue, units, store/style analytics |
| /warehouse | Warehouse | Inventory, velocity, fulfillment analysis |
| /sftp-monitor | SFTP Monitor | Data pipeline monitoring dashboard |
| /chatbot | FAQ Chatbot | GPT-5.2 powered Q&A |

## What's Been Implemented

### Phase 1-3 — MVP, Filtering, Presets
- [x] Full backend API with all analytics endpoints
- [x] 7-file CSV upload with validation
- [x] GPT-5.2 FAQ Chatbot
- [x] Salesforce light theme
- [x] Collapsible filter panels (date, category, channel, region, thresholds)
- [x] Personal + Team presets with tags, favorites, import/export

### Phase 4 — Charts & Warehouse (Apr 2, 2026)
- [x] Chart.js on all analytics pages (BI, CoreLogics, GapAnalysis)
- [x] Warehouse Analysis page with 4 tabs

### Phase 5 — Data Upload Redesign (Apr 2, 2026)
- [x] Master vs Daily separation with frequency badges
- [x] Upload history (MongoDB audit trail)
- [x] Template downloads per file type
- [x] SFTP info card

### Phase 6 — SFTP Data Pipeline (Apr 2, 2026)
- [x] **Backend SFTP module** (`/app/backend/sftp/`)
  - SFTPService: paramiko client, file detection, demo data generation
  - SFTPSchedulerService: apscheduler background polling
  - Demo mode auto-activates when no SFTP credentials configured
- [x] **Admin API endpoints** (11 endpoints under `/api/admin/sftp/*`)
  - Status, config (get/save), test-connection
  - Trigger, seed-demo, retry-failed
  - Scheduler start/stop
  - Logs (with type/status filters), stats (trend, by_type, store SLA)
- [x] **SFTP Monitor Dashboard** (`/sftp-monitor`)
  - Demo Mode badge
  - Connection banner with scheduler controls
  - 5 KPI cards (total files, success rate, records, failed, stores today)
  - Processing Trend line chart (7 days)
  - Records by Data Source bar chart
  - 3 Data Source cards with success rate progress bars
  - Store Upload SLA (10 stores with green/red badges)
  - Processing logs table with type/status filters
  - SFTP configuration panel (host, port, username, etc.)
  - Manual trigger, seed demo, retry failed, auto-refresh

## Backend API Endpoints
### Data Upload
- POST /api/upload/{file_type}, GET /api/upload/status, GET /api/upload/history
- GET /api/upload/template/{file_type}, DELETE /api/upload/{file_type}, DELETE /api/upload/all

### Analytics
- GET /api/analytics/{overview,ros,size-gap,noos,bi-dashboard,store-style-ranking,warehouse}
- GET /api/analytics/filter-options

### Presets
- GET/POST /api/presets, GET /api/presets/export, POST /api/presets/import
- GET /api/presets/tags/all, GET/PUT/PATCH/DELETE /api/presets/{id}

### SFTP Admin
- GET /api/admin/sftp/{status,config,stats,logs}
- POST /api/admin/sftp/{config,test-connection,trigger,seed-demo,retry-failed}
- POST /api/admin/sftp/scheduler/{start,stop}

### Chat
- POST /api/chat, GET /api/chat/history/{session_id}

## Data Upload Strategy
| File | Type | Frequency | Who Uploads |
|------|------|-----------|-------------|
| Style Master | Master | Quarterly | Merchandising Team |
| SKU-EAN Master | Master | Quarterly | Merchandising Team |
| Store Master | Master | Monthly | Operations Team |
| Warehouse Master | Master | Rarely | Warehouse Team |
| Daily Sales | Daily | Daily | POS System / SFTP |
| Store Inventory | Daily | Daily | WMS System / SFTP |
| Warehouse Inventory | Daily | Daily | WMS System / SFTP |

## Prioritized Backlog
### P1
- Real SFTP integration (when credentials available)
- PDF report generation
- Email alerts for SFTP failures (SendGrid/SMTP)

### P2
- Scheduled analysis jobs
- Product lifecycle timeline visualization
- Preset sharing via URL
- Data validation rules configuration
