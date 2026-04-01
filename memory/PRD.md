# Fashion Retail Gap Analysis Platform - PRD

## Original Problem Statement
Build the same app as the Streamlit Merchandising Gap Analysis app from the zip file with better UI/UX using React + FastAPI, light theme.

## Architecture
- **Frontend**: React with Tailwind CSS (Light theme)
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
3. Store Master - Store information and hierarchy
4. Warehouse Master - Warehouse information
5. Daily Sales - Transaction-level sales data
6. Store Inventory - Current store stock levels
7. Warehouse Inventory - Current warehouse stock levels

### Analytics Modules
1. NOOS Analysis (Never Out Of Stock)
2. ROS Comparison (Rate of Sale - Healthy vs Broken)
3. Size Set Gap Analysis
4. BI Dashboards
5. Store-Style Ranking
6. FAQ Chatbot

## What's Been Implemented (Jan 1, 2026)
- [x] Complete backend API with all analytics endpoints
- [x] File upload system with validation
- [x] Configuration management
- [x] NOOS analysis with exposure days calculation
- [x] ROS analysis with healthy/broken classification
- [x] Size gap analysis with overstock/understock detection
- [x] BI Dashboard with monthly trends and store/style performance
- [x] Store-Style ranking system
- [x] AI-powered FAQ Chatbot with GPT 5.2
- [x] Modern React UI with light theme
- [x] Sidebar navigation with file status tracking
- [x] Persona-based views (CXO, Merchandiser, Consultant)
- [x] Export functionality for all data tables

## Known Limitations
- Charts temporarily removed due to Recharts library compatibility issues (data tables used instead)
- Sample data files can be uploaded for testing

## Prioritized Backlog
### P0 - Critical (Future)
- Add charts back using a compatible charting library (Chart.js or Victory)
- Add product lifecycle timeline visualization

### P1 - Important
- Add warehouse inventory analysis page
- Add ROS trend over time visualization
- Add size distribution heatmaps

### P2 - Nice to Have
- Add PDF report generation
- Add scheduled analysis jobs
- Add multi-currency support
- Add comparison between seasons

## Next Tasks
1. Evaluate alternative charting libraries (Chart.js, Victory, Nivo)
2. Re-add charts with compatible library
3. Add data validation improvements
4. Add more interactive filters
