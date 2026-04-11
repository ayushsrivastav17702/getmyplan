# GetMyPlan PRD — AI-Powered Demand Planning Platform

## Original Problem Statement
Multi-tenant SaaS demand planning system with V2 data pipelines, ML forecasting, Redis caching, FTUE guided onboarding, comprehensive Technical SEO, MFA, tenant backup/restore, user funnel analytics, email drip campaigns, invoice generation, SFTP auto-uploads, chunked uploads, and enterprise features.

## Core Architecture
- **Frontend:** React 19 + Tailwind CSS + Shadcn/UI + Chart.js (react-chartjs-2)
- **Backend:** FastAPI + MongoDB (Motor async) + Redis Cloud
- **Auth:** JWT (pyjwt) + bcrypt + MFA (TOTP + Email OTP)
- **SEO:** react-helmet-async + Puppeteer pre-rendering
- **AI:** OpenAI GPT-5.2 via Emergent LLM Key
- **Email:** Hostinger SMTP (smtp.hostinger.com:465)

## What's Been Implemented (Complete)

### Core Platform
- Multi-tenant architecture with RBAC (8 roles, 21 permissions)
- JWT auth + MFA (TOTP + Email OTP)
- Redis caching, onboarding wizard, Data upload V2
- AI demand forecasting, Buy plan generator
- Executive dashboard, Configuration page
- 15+ analytics modules

### Invoice Generation (TENANT-31) — Feb 2026
- Auto-generates invoices from tenant plan data (trial/starter/pro/enterprise pricing)
- 18% GST auto-calculated, 8 usage metrics (users, uploads, sales records, storage, etc.)
- Invoice number format: GMP-YYYYMM-TENANT-NNNN
- Download as styled HTML (browser print-to-PDF)
- Status management: unpaid/paid/cancelled/overdue
- Tenant isolation verified
- **Endpoints:** generate, list, detail, download, update status, delete

### SFTP Auto-Scheduled Uploads — Feb 2026
- Configurable schedule (daily/weekly/monthly) with hour, file types, destination path
- Schedule history tracking
- **Endpoints:** GET/PUT /api/data/sftp-schedule, GET history

### Chunked Uploads & Async Processing — Feb 2026
- Initialize upload session, upload chunks individually, finalize and process
- Progress tracking per upload, missing chunk detection
- In-memory chunk storage with 5-min auto-cleanup
- **Endpoints:** init, chunk, complete, status, cancel

### Tenant Backup & Restore
- Compressed snapshots + ZIP export, Overwrite/Merge restore, Auto-cleanup (5 max)

### User Funnel Analytics Dashboard
- 5-stage funnel with KPI cards, charts, conversion visualization, user table

### Email Drip Campaigns
- 4 campaigns, Day 1/3/7 drip sequence, auto-daily + manual trigger

### Blog Engine & SEO (42 Total Blogs)
- 14 Original + 7 Saudi + 7 UAE + 7 South Africa + 7 USA
- sitemap.xml (51 URLs), news-sitemap, RSS, llms.txt, prerender.js

## Prioritized Backlog

### Refactoring (Low Priority)
- Migrate Pandas in-memory aggregations to MongoDB aggregation pipelines

## Key Files
- `/app/backend/routes/invoices.py` — Invoice CRUD + download
- `/app/backend/routes/data_operations.py` — SFTP schedule + chunked uploads
- `/app/backend/routes/funnel_analytics.py` — Funnel analytics
- `/app/backend/routes/drip_campaigns.py` — Drip campaign endpoints
- `/app/backend/routes/backup.py` — Backup & Restore
- `/app/frontend/src/pages/InvoiceManagement.jsx` — Invoice page
- `/app/frontend/src/pages/UserFunnelDashboard.jsx` — Funnel dashboard
- `/app/frontend/src/pages/DripCampaigns.jsx` — Campaign management
- `/app/frontend/src/pages/BackupRestore.jsx` — Backup page

## 3rd Party Integrations
- OpenAI GPT-5.2 (via Emergent LLM Key)
- Hostinger SMTP (info@getmyplan.in)
- Redis Cloud
- pyotp + segno (TOTP/QR)
