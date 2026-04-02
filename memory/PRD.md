# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build the same app as the Streamlit Merchandising Gap Analysis app with better UI/UX using React + FastAPI. Added comprehensive filtering with Salesforce theme, filter presets, Chart.js visualizations, and warehouse analysis.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python
- **Database**: MongoDB (uploaded data + team presets)
- **Local Storage**: Personal filter presets
- **AI Integration**: GPT 5.2 via Emergent LLM Key for FAQ Chatbot
- **Charts**: Chart.js + react-chartjs-2

## User Personas
1. **CXO Executives**: High-level metrics and revenue impact views
2. **Merchandisers**: Detailed style-level analysis and saved filter presets
3. **Consultants**: Methodology explanations and calculation details

## What's Been Implemented

### Phase 1 - MVP (Jan 1, 2026)
- [x] Complete backend API with all analytics endpoints
- [x] File upload system with validation for 7 data files
- [x] Configuration management
- [x] NOOS, ROS, Size Gap, BI analytics
- [x] AI-powered FAQ Chatbot with GPT 5.2
- [x] Modern React UI with Salesforce theme

### Phase 2 - Filtering (Jan 1, 2026)
- [x] Collapsible filter panels with animation
- [x] Date range, Category, Channel, Region filters
- [x] Page-specific threshold filters
- [x] Filter options API with auto-population
- [x] Reset and Apply filter buttons

### Phase 3 - Filter Presets (Jan 2, 2026)
- [x] Personal Presets (localStorage)
- [x] Team Presets (MongoDB)
- [x] Preset Features (name, description, tags, favorites)
- [x] Backend CRUD APIs for presets

### Phase 4 - Charts & Warehouse (Apr 2, 2026)
- [x] **Chart.js Integration**
  - BI Dashboards: Revenue trend (area), Units sold (bar), Top stores (horizontal bar), Top styles (horizontal bar), Region distribution (doughnut)
  - Core Logics: Healthy vs Broken (doughnut), Top 10 Styles by ROS (horizontal bar), Top combos by rev/day (bar)
  - Gap Analysis: NOOS Candidate Distribution (doughnut), Top Styles by Revenue (horizontal bar), Status Distribution (doughnut), Gap by Style (horizontal bar)
  - Fixed callback: undefined bug that caused Chart.js to show indices instead of category labels
- [x] **Preset Import/Export**
  - GET /api/presets/export - Download presets as JSON
  - POST /api/presets/import - Upload presets from JSON
  - Import/Export buttons in FilterPanel presets dropdown
- [x] **Warehouse Inventory Analysis** (/warehouse)
  - Overview tab: KPIs + Stock by Warehouse bar + Online/Offline doughnut + Inventory Trend line
  - By Warehouse tab: Comparison chart + detail table
  - Top SKUs tab: Bar chart + SKU table with style/size
  - Stock Velocity tab: Days of stock bar chart + risk assessment table

## Backend API Endpoints
- POST /api/upload/{file_type} - Upload CSV files
- GET /api/upload/status - Upload status for all files
- GET/POST /api/config - Analysis configuration
- GET /api/presets - List presets (with page_type filter)
- POST /api/presets - Create preset
- GET /api/presets/export - Export presets as JSON
- POST /api/presets/import - Import presets from JSON
- GET /api/presets/tags/all - All unique tags
- GET /api/presets/{id} - Get single preset
- PUT /api/presets/{id} - Update preset
- PATCH /api/presets/{id}/favorite - Toggle favorite
- DELETE /api/presets/{id} - Delete preset
- GET /api/analytics/filter-options - Filter options from data
- GET /api/analytics/overview - Quick overview stats
- GET /api/analytics/ros - ROS analysis with filters
- GET /api/analytics/size-gap - Size gap analysis with filters
- GET /api/analytics/noos - NOOS analysis with filters
- GET /api/analytics/bi-dashboard - BI dashboard with filters
- GET /api/analytics/store-style-ranking - Store-style ranking
- GET /api/analytics/warehouse - Warehouse inventory analysis
- POST /api/chat - FAQ chatbot
- GET /api/chat/history/{session_id} - Chat history

## Prioritized Backlog
### P1 - Important
- Add product lifecycle timeline visualization
- Add PDF report generation

### P2 - Nice to Have
- Add scheduled analysis jobs
- Add preset sharing via URL
- Add data validation rules configuration
