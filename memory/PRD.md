# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build a Fashion Retail Gap Analysis platform with React + FastAPI featuring CSV data uploading, multiple analytics dashboards with PRD formulas, dynamic filtering with presets, Chart.js visualizations, and a GPT-5.2 FAQ Chatbot.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python/Pandas
- **Database**: MongoDB
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2 (NO Recharts)

## Pages & Routes (14 total)
| Route | Page | Description |
|-------|------|-------------|
| / | Getting Started | App overview |
| /upload | Data Upload | Master vs Daily file upload |
| /config | Configuration | Analysis config |
| /core-logics | Core Logics | TrueROS + Store-Style |
| /gap-analysis | Gap Analysis | NOOS + Size Gap + ROS Gap |
| /stock-out | Stock-Out Analysis | PRD stock-out formulas |
| /replenishment | Replenishment Planner | PO suggestions |
| /doh | DOH Analysis | Days on Hand classification |
| /planogram | Planogram Fill Rate | Fill rate compliance |
| /bi-dashboards | BI Dashboards | Revenue/units analytics |
| /warehouse | Warehouse | Inventory/velocity |
| /sftp-monitor | SFTP Monitor | Data pipeline monitoring |
| /data-quality | Data Quality | Store SLA scorecards |
| /chatbot | FAQ Chatbot | GPT-5.2 Q&A |

## Completed Phases

### Phase 1-7 (Previous sessions)
- [x] Full MVP with 7-file CSV upload, GPT chatbot, Salesforce theme
- [x] Dynamic filters + Presets with import/export
- [x] Chart.js migration, Warehouse Analysis, Data Upload redesign
- [x] SFTP Monitor + Data Quality dashboards

### Phase 8 — ROS Gap Analysis
- [x] `/api/analytics/ros-gap` - Raw ROS, Healthy Size Set, Sales Loss, NOOS
- [x] Testing: 100% (Iteration 8)

### Phase 9 — Stock-Out Analysis
- [x] `/api/analytics/stock-out` - SOH=0 AND ROS>0, Sales Loss, Severity
- [x] Testing: 100% (Iteration 9)

### Phase 10 — Replenishment Planner
- [x] `/api/analytics/replenishment` - Reorder Qty, Safety Stock, PO Value
- [x] Testing: 100% (Iteration 10)

### Phase 11 — DOH Analysis
- [x] `/api/analytics/doh` - DOH=Inv/ROS, Classification ±20%, Weighted avg
- [x] Testing: 100% (Iteration 11)

### Phase 12 — Planogram Fill Rate (Feb 2026)
- [x] `/api/analytics/planogram-fill-rate` with PRD formulas:
  - Fill Rate = (Current Stock / Norm Allocated) x 100
  - Overall Fill Rate = (Sum Stock / Sum Norm) x 100
  - Lost Sales = Missing Facings x ROS x ASP
  - Compliance: >=90% Good, 80-90% Moderate, <80% Critical
- [x] PRD Formula Cards + compliance legend
- [x] KPI Cards: Overall Fill Rate, Good Compliance, Critical count, Est. Lost Sales
- [x] Fill Rate Trend line chart with target line
- [x] Compliance Distribution doughnut chart
- [x] Recommendations with store-level actions
- [x] Store/Category view toggle with bar charts
- [x] Summary + Detail tables with progress bars
- [x] CSV Export, FilterPanel, Navigation
- [x] Testing: 100% (Iteration 12: 21 backend + all frontend)

## Prioritized Backlog
### P1
- Real SFTP integration
- PDF report generation
- Email alerts for SLA/SFTP

### P2
- Scheduled analysis jobs
- Migrate Pandas to persistent MongoDB
- Product lifecycle timeline
- Preset sharing via URL
