# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build the same app as the Streamlit Merchandising Gap Analysis app with better UI/UX using React + FastAPI. Features include CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, warehouse analysis, a GPT-5.2 FAQ Chatbot, redesigned data upload workflow, SFTP Data Pipeline Monitor, Data Quality & SLA Dashboard, PRD-based ROS Gap Analysis, Stock-Out Analysis, Replenishment Planner, and DOH Analysis.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python
- **Database**: MongoDB (data, presets, upload history, SFTP logs/config)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2
- **SFTP**: paramiko + apscheduler (demo mode when unconfigured)

## Pages & Routes (13 total)
| Route | Page | Description |
|-------|------|-------------|
| / | Getting Started | App overview |
| /upload | Data Upload | Master vs Daily file upload with history |
| /config | Configuration | Analysis config |
| /core-logics | Core Logics | TrueROS + Store-Style with charts |
| /gap-analysis | Gap Analysis | NOOS + Size Gap + ROS Gap (3 tabs) |
| /stock-out | Stock-Out Analysis | PRD stock-out formulas, risk analysis |
| /replenishment | Replenishment Planner | PO suggestions, lead time/safety config |
| /doh | DOH Analysis | Days on Hand, classification, trend |
| /bi-dashboards | BI Dashboards | Revenue, units, store/style analytics |
| /warehouse | Warehouse | Inventory, velocity, fulfillment |
| /sftp-monitor | SFTP Monitor | Data pipeline monitoring |
| /data-quality | Data Quality | Store SLA, quality scorecards |
| /chatbot | FAQ Chatbot | GPT-5.2 powered Q&A |

## What's Been Implemented

### Phase 1-3 — MVP, Filtering, Presets
- [x] Full backend API with all analytics endpoints
- [x] 7-file CSV upload with validation
- [x] GPT-5.2 FAQ Chatbot
- [x] Salesforce light theme
- [x] Dynamic filter panels + Personal/Team presets with import/export

### Phase 4 — Charts & Warehouse
- [x] Chart.js on all analytics pages
- [x] Warehouse Analysis page with 4 tabs

### Phase 5 — Data Upload Redesign
- [x] Master vs Daily separation, upload history, template downloads

### Phase 6 — SFTP Data Pipeline
- [x] Backend SFTP module with paramiko + apscheduler
- [x] 11 admin API endpoints, SFTP Monitor Dashboard with demo mode

### Phase 7 — Data Quality & SLA
- [x] Store Upload Tracker, SLA Monitor, Data Quality Scorecard

### Phase 8 — ROS Gap Analysis
- [x] `/api/analytics/ros-gap` with PRD formulas
- [x] Testing: 100% pass (Iteration 8)

### Phase 9 — Stock-Out Analysis
- [x] `/api/analytics/stock-out` with PRD formulas
- [x] Testing: 100% pass (Iteration 9)

### Phase 10 — Replenishment Planner
- [x] `/api/analytics/replenishment` with configurable sliders
- [x] Testing: 100% pass (Iteration 10)

### Phase 11 — DOH Analysis (Feb 2026)
- [x] **Backend endpoint** `/api/analytics/doh` computing PRD formulas from real CSV data:
  - DOH(store,sku) = Inventory / Daily Raw ROS
  - Channel DOH = Sum(DOH x Inventory) / Sum(Inventory)
  - Classification: Optimal ±20%, Overstocked >120%, Understocked <80%
- [x] **Configurable Ideal DOH slider** (1-60 days) with dynamic optimal range display
- [x] **PRD Formula Cards** — 3 cards + config panel
- [x] **KPI Cards** — Overall DOH, Optimal count, At Risk count, Stocked Out count
- [x] **DOH Trend & Stock-Outs** — Weekly line chart with dual-axis
- [x] **DOH Status Distribution** — Doughnut chart with legend
- [x] **Recommendations** — Context-aware action items based on store status
- [x] **Store/Category View Toggle** — Switch between store-level and category-level analysis
- [x] **DOH Bar Chart** — Current DOH vs Ideal DOH per store/category
- [x] **Summary Table** — Store/Category, Inventory, DOH, Ideal DOH, SKUs, Status
- [x] **Detail Table** — Store-SKU level data sorted by most urgent (lowest DOH)
- [x] **CSV Export** — Downloads full detail with ideal DOH in filename
- [x] **FilterPanel + Navigation** — Full filter integration, new sidebar item
- [x] **Testing** — 100% pass rate (Iteration 11: 19 backend + all frontend tests)

## Prioritized Backlog
### P1
- Real SFTP integration (when credentials available)
- PDF report generation
- Email alerts for SFTP failures + SLA reminders

### P2
- Scheduled analysis jobs
- Product lifecycle timeline visualization
- Preset sharing via URL
- Migrate in-memory Pandas to persistent MongoDB collections
