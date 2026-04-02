# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build the same app as the Streamlit Merchandising Gap Analysis app with better UI/UX using React + FastAPI. Features include CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, warehouse analysis, a GPT-5.2 FAQ Chatbot, redesigned data upload workflow, SFTP Data Pipeline Monitor, Data Quality & SLA Dashboard, PRD-based ROS Gap Analysis, and Stock-Out Analysis.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python
- **Database**: MongoDB (data, presets, upload history, SFTP logs/config)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2
- **SFTP**: paramiko + apscheduler (demo mode when unconfigured)

## Pages & Routes (11 total)
| Route | Page | Description |
|-------|------|-------------|
| / | Getting Started | App overview |
| /upload | Data Upload | Master vs Daily file upload with history |
| /config | Configuration | Analysis config |
| /core-logics | Core Logics | TrueROS + Store-Style with charts |
| /gap-analysis | Gap Analysis | NOOS + Size Gap + ROS Gap with charts |
| /stock-out | Stock-Out Analysis | PRD stock-out formulas, risk analysis |
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

### Phase 4 — Charts & Warehouse (Apr 2, 2026)
- [x] Chart.js on all analytics pages
- [x] Warehouse Analysis page with 4 tabs

### Phase 5 — Data Upload Redesign (Apr 2, 2026)
- [x] Master vs Daily separation, upload history, template downloads

### Phase 6 — SFTP Data Pipeline (Apr 2, 2026)
- [x] Backend SFTP module with paramiko + apscheduler
- [x] 11 admin API endpoints
- [x] SFTP Monitor Dashboard with demo mode

### Phase 7 — Data Quality & SLA (Apr 2, 2026)
- [x] Store Upload Tracker, SLA Monitor, Data Quality Scorecard
- [x] Quality by Store Chart, Quick Actions
- [x] Backend APIs for quality metrics

### Phase 8 — ROS Gap Analysis (Feb 2026)
- [x] Backend endpoint `/api/analytics/ros-gap` with PRD formulas (Raw ROS, Healthy Size Set, Sales Loss, NOOS)
- [x] PRD Formula Cards, KPI Cards, Charts, Tables
- [x] Persona views (CXO, Merchandiser, Consultant)
- [x] Testing: 100% pass (Iteration 8)

### Phase 9 — Stock-Out Analysis (Feb 2026)
- [x] **Backend endpoint** `/api/analytics/stock-out` computing all PRD formulas from real CSV data:
  - Stock-Out: SOH = 0 AND Last 30 Days ROS > 0
  - Daily Sales Loss: ((ROS x 1) - SOH) x ASP
  - Stock-Out Rate: (Stockouts / Total SKUs) x 100
  - Severity: LostSales x Duration x Importance
- [x] **PRD Formula Cards** — 4 cards (Stock-Out, Daily Sales Loss, Stock-Out Rate, Severity)
- [x] **KPI Cards** — Total Stock-Outs, Stock-Out Rate, Est. Daily Sales Loss, Stores Impacted
- [x] **Stock-Out Trend** — Line chart of daily stock-out counts
- [x] **Top Impacted Stores** — Bar chart ranked by severity score
- [x] **Top Stock-Out SKUs Table** — SKU, Style, Stores Affected, Avg ROS, Avg ASP, Daily Loss
- [x] **Store-wise Impact Table** — Store, Stock-Out SKUs, Avg Duration, Daily Loss, Severity
- [x] **High-Risk SKUs Table** — Predictive: SKUs approaching stock-out within 7 days (ROS vs SOH)
- [x] **SKU Detail Modal** — PRD calculation breakdown with SOH, ROS, ASP
- [x] **Actionable Recommendations** — Urgent replenishment, preventive monitoring, safety stock
- [x] **FilterPanel integration** — Date, Category, Channel, Region filters
- [x] **Navigation** — New /stock-out route in sidebar
- [x] **Testing** — 100% pass rate (Iteration 9: 14 backend + all frontend tests)

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
