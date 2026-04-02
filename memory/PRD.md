# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build the same app as the Streamlit Merchandising Gap Analysis app with better UI/UX using React + FastAPI. Features include CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, warehouse analysis, a GPT-5.2 FAQ Chatbot, redesigned data upload workflow, SFTP Data Pipeline Monitor, Data Quality & SLA Dashboard, and PRD-based ROS Gap Analysis.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python
- **Database**: MongoDB (data, presets, upload history, SFTP logs/config)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2
- **SFTP**: paramiko + apscheduler (demo mode when unconfigured)

## Pages & Routes (10 total)
| Route | Page | Description |
|-------|------|-------------|
| / | Getting Started | App overview |
| /upload | Data Upload | Master vs Daily file upload with history |
| /config | Configuration | Analysis config |
| /core-logics | Core Logics | TrueROS + Store-Style with charts |
| /gap-analysis | Gap Analysis | NOOS + Size Gap + ROS Gap with charts |
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
- [x] **New Backend Endpoint** `/api/analytics/ros-gap` — Computes PRD formulas using real CSV data:
  - Raw ROS = Net Sales Qty / True Live Days
  - Healthy Size Set = >=75% sizes available per store-style-day
  - Sales Loss = (Healthy ROS x Broken Days) - Actual Broken Sales
  - NOOS = Sales >80% + Inventory >80% of period days
- [x] **PRD Formula Cards** — 4 prominent cards displaying each formula
- [x] **KPI Summary Cards** — Avg ROS Gap, Total Sales Loss, Healthy Coverage %, NOOS Qualified Styles
- [x] **Charts** — Style Health Distribution (Doughnut), Top 10 Sales Loss by Style (Bar), Store-wise Size Set Health (Stacked Bar)
- [x] **Style-wise ROS Gap Table** — Style, Healthy ROS, Actual ROS, Gap, Sales Loss, Stores, Status
- [x] **Store-wise Size Set Health Table** — Store, Healthy %, Broken %, Sales Loss, Styles
- [x] **NOOS Style Analysis Table** — Style, Stores, NOOS Stores, Sales/Inv Consistency, NOOS %, Status
- [x] **Persona Views** — CXO Executive Insight, Merchandiser detail tables, Consultant methodology cards
- [x] **Full Filter Integration** — Date, Category, Channel, Region filters work with ROS Gap tab
- [x] **Testing** — 100% pass rate (Iteration 8: 11 backend + all frontend tests passed)

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
