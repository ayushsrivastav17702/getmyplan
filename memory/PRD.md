# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build the same app as the Streamlit Merchandising Gap Analysis app with better UI/UX using React + FastAPI. Added comprehensive filtering with Salesforce theme and filter presets feature.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python
- **Database**: MongoDB (analytics data + team presets)
- **Local Storage**: Personal filter presets
- **AI Integration**: GPT 5.2 via Emergent LLM Key for FAQ Chatbot

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
- [x] **Personal Presets** (localStorage)
  - Save/load/delete personal presets per browser
  - Unlimited presets
  - Toggle favorites
- [x] **Team Presets** (MongoDB)
  - Save/load/delete shared team presets
  - CRUD API endpoints
  - Shareable across all users
- [x] **Preset Features**
  - Name + description + tags
  - Page-specific (Gap Analysis, Core Logics, BI Dashboards)
  - Favorite presets with quick-access pills
  - Dropdown list in filter panel
  - Save as Preset button
  - Tag suggestions from existing tags
- [x] **Backend APIs**
  - POST /api/presets - Create preset
  - GET /api/presets - List presets (with page_type filter)
  - GET /api/presets/{id} - Get single preset
  - PUT /api/presets/{id} - Update preset
  - PATCH /api/presets/{id}/favorite - Toggle favorite
  - DELETE /api/presets/{id} - Delete preset
  - GET /api/presets/tags/all - List all tags

## Known Limitations
- Charts display as data tables (Recharts compatibility)

## Prioritized Backlog
### P0 - Critical
- Add charts using Chart.js or Victory

### P1 - Important
- Add preset import/export functionality
- Add warehouse inventory analysis
- Add product lifecycle timeline

### P2 - Nice to Have
- Add PDF report generation
- Add scheduled analysis jobs
- Add preset sharing via URL

## Next Tasks
1. Implement charts with compatible library
2. Add preset export/import feature
3. Add warehouse inventory analysis
