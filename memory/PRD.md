# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build the same app as the Streamlit Merchandising Gap Analysis app with better UI/UX using React + FastAPI. Features include CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, warehouse analysis, a GPT-5.2 FAQ Chatbot, redesigned data upload workflow, SFTP Data Pipeline Monitor, and Data Quality & SLA Dashboard.

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
| /gap-analysis | Gap Analysis | NOOS + Size Gap with charts |
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
- [x] **Store Upload Tracker** — Grid of 10 color-coded store cards (green=uploaded, red=missing, amber=late, orange=partial). Click opens detail modal with sales/inventory status, quality ring, completeness/accuracy/timeliness breakdowns, and issues.
- [x] **SLA Monitor** — Overall compliance rate, expected/received/missing file counts, SLA by file type (Daily Sales, Store Inventory, WH Inventory) with progress bars and targets, week-over-week trend.
- [x] **Data Quality Scorecard** — Overall weighted score (completeness 25%, accuracy 25%, timeliness 20%, consistency 15%, validity 15%). 5 selectable metric tabs with current score, target, gap-to-target, issues, and recommendations.
- [x] **Quality by Store Chart** — Bar chart with color-coded quality scores per store.
- [x] **Quick Actions** — Send reminders, generate report, configure SLA targets.
- [x] **Backend APIs** — 3 endpoints: `/api/admin/quality/store-uploads/{date}`, `/api/admin/quality/sla-metrics`, `/api/admin/quality/scorecard`

## Prioritized Backlog
### P1
- Real SFTP integration (when credentials available)
- PDF report generation
- Email alerts for SFTP failures + SLA reminders

### P2
- Scheduled analysis jobs
- Product lifecycle timeline visualization
- Preset sharing via URL
