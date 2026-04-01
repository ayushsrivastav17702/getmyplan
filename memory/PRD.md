# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build the same app as the Streamlit Merchandising Gap Analysis app from the zip file with better UI/UX using React + FastAPI, light theme. Added comprehensive filtering with Salesforce theme.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme - blue primary color)
- **Backend**: FastAPI with Python
- **Database**: MongoDB
- **AI Integration**: GPT 5.2 via Emergent LLM Key for FAQ Chatbot

## User Personas
1. **CXO Executives**: High-level metrics and revenue impact views
2. **Merchandisers**: Detailed style-level analysis and data tables
3. **Consultants**: Methodology explanations and calculation details

## Core Requirements (Static)
### Required Data Files (7 total)
1. Style Master - Style codes, brands, categories, gender, season
2. SKU-EAN Master - SKU to EAN mapping with sizes and MRP
3. Store Master - Store information and hierarchy (includes region)
4. Warehouse Master - Warehouse information
5. Daily Sales - Transaction-level sales data
6. Store Inventory - Current store stock levels
7. Warehouse Inventory - Current warehouse stock levels

### Analytics Modules with Filtering
1. NOOS Analysis - Date, Category, Channel, Region filters
2. ROS Comparison - Date, Category, Channel, Region, Min Size % filters
3. Size Set Gap Analysis - Date, Category, Channel, Region, Threshold filters
4. BI Dashboards - Date, Category, Channel, Region filters
5. Store-Style Ranking
6. FAQ Chatbot

### Filter Features (Added Jan 1, 2026)
- Collapsible filter panel at top of each analytics page
- Common filters: Start Date, End Date, Category, Channel, Region
- Gap Analysis specific: Understocking Threshold (≤), Overstocking Threshold (≥)
- Core Logics specific: Min Size (Healthy), Min Size % (Healthy)
- Auto-populated filter options from uploaded data
- Reset Filters button
- Apply Filters button (collapses panel after applying)
- Active filter count badge on collapsed panel
- Smooth expand/collapse animation

## What's Been Implemented
### Phase 1 - MVP (Jan 1, 2026)
- [x] Complete backend API with all analytics endpoints
- [x] File upload system with validation
- [x] Configuration management
- [x] NOOS, ROS, Size Gap, BI analytics
- [x] AI-powered FAQ Chatbot with GPT 5.2
- [x] Modern React UI with light theme
- [x] Sidebar navigation with file status

### Phase 2 - Filtering & Salesforce Theme (Jan 1, 2026)
- [x] Salesforce blue theme (#0176D3 primary)
- [x] IBM Plex Sans + Chivo fonts
- [x] FilterPanel component with animation
- [x] Date range filters with auto-population
- [x] Multi-select dropdowns for Category, Channel, Region
- [x] Threshold sliders for gap analysis
- [x] Min size filters for core logics
- [x] Filter options API endpoint
- [x] Backend filter parameter support
- [x] Active filter count badge
- [x] Reset and Apply filter buttons

## Known Limitations
- Charts temporarily display as data tables (Recharts compatibility issue)

## Prioritized Backlog
### P0 - Critical (Future)
- Add charts using compatible library (Chart.js/Victory)

### P1 - Important
- Add filter presets/saved filters
- Add warehouse inventory analysis
- Add product lifecycle timeline

### P2 - Nice to Have
- Add PDF report generation
- Add scheduled analysis jobs
- Add multi-currency support

## Next Tasks
1. Implement charts with Chart.js or Victory
2. Add filter presets functionality
3. Add warehouse inventory analysis page
