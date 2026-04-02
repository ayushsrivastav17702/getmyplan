# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build the same app as the Streamlit Merchandising Gap Analysis app with better UI/UX using React + FastAPI. Added comprehensive filtering with Salesforce theme, filter presets, Chart.js visualizations, warehouse analysis, and a redesigned data upload workflow.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python
- **Database**: MongoDB (uploaded data + team presets + upload history)
- **Local Storage**: Personal filter presets
- **AI Integration**: GPT 5.2 via Emergent LLM Key for FAQ Chatbot
- **Charts**: Chart.js + react-chartjs-2

## User Personas
1. **CXO Executives**: High-level metrics and revenue impact views
2. **Merchandisers**: Detailed style-level analysis and saved filter presets
3. **Consultants**: Methodology explanations and calculation details
4. **Operations Team**: Daily data uploads and warehouse monitoring

## What's Been Implemented

### Phase 1 - MVP
- [x] Complete backend API with all analytics endpoints
- [x] File upload system with validation for 7 data files
- [x] Configuration management
- [x] NOOS, ROS, Size Gap, BI analytics
- [x] AI-powered FAQ Chatbot with GPT 5.2
- [x] Modern React UI with Salesforce theme

### Phase 2 - Filtering
- [x] Collapsible filter panels with animation
- [x] Date range, Category, Channel, Region filters
- [x] Page-specific threshold filters
- [x] Filter options API with auto-population

### Phase 3 - Filter Presets
- [x] Personal Presets (localStorage) + Team Presets (MongoDB)
- [x] Preset Features (name, description, tags, favorites)
- [x] Preset Import/Export (JSON file sharing between users)

### Phase 4 - Charts & Warehouse (Apr 2, 2026)
- [x] Chart.js on all analytics pages (BI, CoreLogics, GapAnalysis)
- [x] Warehouse Inventory Analysis page with 4 tabs (Overview, By Warehouse, Top SKUs, Stock Velocity)

### Phase 5 - Data Upload Redesign (Apr 2, 2026)
- [x] **Master vs Daily Data separation** — Two-column layout clearly grouping one-time master files and daily transactional files
- [x] **Frequency badges** — Blue "MASTER" and amber "DAILY" badges on each file card
- [x] **Strategy info banner** — Explains data upload workflow to merchandising team
- [x] **Status bar** — Shows Master Data (x/4) and Daily Data (x/3) with color indicators + progress bar
- [x] **Upload History** — MongoDB-backed audit trail of all uploads with timestamp, status, row count
- [x] **Template Downloads** — GET /api/upload/template/{file_type} returns CSV template with required columns
- [x] **SFTP Info Card** — Informational card for future automated daily data ingestion

## Backend API Endpoints
- POST /api/upload/{file_type} - Upload CSV files (now logs to history)
- GET /api/upload/status - Upload status for all files
- GET /api/upload/history - Upload history log (audit trail)
- GET /api/upload/template/{file_type} - Download CSV template
- DELETE /api/upload/{file_type} - Delete a file
- DELETE /api/upload/all - Delete all files
- GET/POST /api/config - Analysis configuration
- GET /api/presets - List presets
- POST /api/presets - Create preset
- GET /api/presets/export - Export presets as JSON
- POST /api/presets/import - Import presets from JSON
- GET /api/presets/tags/all - All unique tags
- GET/PUT/PATCH/DELETE /api/presets/{id} - CRUD for individual presets
- GET /api/analytics/filter-options - Filter options
- GET /api/analytics/overview - Quick stats
- GET /api/analytics/ros - ROS analysis
- GET /api/analytics/size-gap - Size gap analysis
- GET /api/analytics/noos - NOOS analysis
- GET /api/analytics/bi-dashboard - BI dashboard
- GET /api/analytics/store-style-ranking - Store-style ranking
- GET /api/analytics/warehouse - Warehouse inventory analysis
- POST /api/chat - FAQ chatbot
- GET /api/chat/history/{session_id} - Chat history

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
### P1 - Important
- SFTP automated ingestion for daily files
- PDF report generation for analytics pages
- Product lifecycle timeline visualization

### P2 - Nice to Have
- Scheduled analysis jobs
- Preset sharing via URL
- Data validation rules configuration
- Migrate in-memory team presets to MongoDB (done)
