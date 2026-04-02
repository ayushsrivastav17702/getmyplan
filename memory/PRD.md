# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build the same app as the Streamlit Merchandising Gap Analysis app with better UI/UX using React + FastAPI. Features include CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, warehouse analysis, a GPT-5.2 FAQ Chatbot, redesigned data upload workflow, SFTP Data Pipeline Monitor, Data Quality & SLA Dashboard, PRD-based ROS Gap Analysis, Stock-Out Analysis, and Replenishment Planner.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python
- **Database**: MongoDB (data, presets, upload history, SFTP logs/config)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2
- **SFTP**: paramiko + apscheduler (demo mode when unconfigured)

## Pages & Routes (12 total)
| Route | Page | Description |
|-------|------|-------------|
| / | Getting Started | App overview |
| /upload | Data Upload | Master vs Daily file upload with history |
| /config | Configuration | Analysis config |
| /core-logics | Core Logics | TrueROS + Store-Style with charts |
| /gap-analysis | Gap Analysis | NOOS + Size Gap + ROS Gap with charts |
| /stock-out | Stock-Out Analysis | PRD stock-out formulas, risk analysis |
| /replenishment | Replenishment Planner | PO suggestions, lead time/safety config |
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
- [x] `/api/analytics/ros-gap` with PRD formulas (Raw ROS, Healthy Size Set, Sales Loss, NOOS)
- [x] PRD Formula Cards, KPI Cards, Charts, Tables, Persona views
- [x] Testing: 100% pass (Iteration 8)

### Phase 9 — Stock-Out Analysis
- [x] `/api/analytics/stock-out` with PRD formulas (SOH=0 AND ROS>0, Sales Loss, Severity)
- [x] KPI Cards, Trend chart, Top SKUs/Stores tables, High-Risk SKUs, Recommendations
- [x] Testing: 100% pass (Iteration 9)

### Phase 10 — Replenishment Planner (Feb 2026)
- [x] **Backend endpoint** `/api/analytics/replenishment` computing:
  - Reorder Qty = (ROS x Lead Time) + Safety Stock - SOH
  - Safety Stock = ROS x Safety Days
  - Days to Stock-Out = SOH / ROS
  - PO Value = Reorder Qty x ASP
- [x] **Configurable sliders**: Lead Time (1-60 days), Safety Days (0-30 days) with Recalculate
- [x] **PRD Formula Cards** — 4 cards with config panel
- [x] **KPI Cards** — Total PO Value, SKUs Needing Reorder, Urgent Count, Plan Configuration
- [x] **Charts** — Priority Distribution (Doughnut), PO Value by Store (Bar), Top Styles (Bar)
- [x] **Priority Breakdown Table** — Stock-Out/Critical/High/Medium/Low counts and values
- [x] **Replenishment Detail Table** — SKU, Style, Size, Store, SOH, ROS, Days Left, Safety Stock, Reorder Qty, PO Value, Priority
- [x] **Store-wise PO Summary** — Store, SKUs to Reorder, Total Units, PO Value, Urgent Items
- [x] **CSV Export** — Downloads PO plan with lead time/safety config in filename
- [x] **FilterPanel + Navigation** — Full filter integration, new sidebar item
- [x] **Testing** — 100% pass rate (Iteration 10: 17 backend + all frontend tests)

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
