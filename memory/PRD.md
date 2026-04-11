# GetMyPlan PRD — AI-Powered Demand Planning Platform

## Original Problem Statement
Multi-tenant SaaS demand planning system with V2 data pipelines, ML forecasting, Redis caching, FTUE guided onboarding, comprehensive Technical SEO, MFA, tenant backup/restore, user funnel analytics, email drip campaigns, invoice generation, SFTP auto-uploads, chunked uploads, MongoDB aggregation pipelines, and enterprise features.

## Core Architecture
- **Frontend:** React 19 + Tailwind CSS + Shadcn/UI + Chart.js (react-chartjs-2)
- **Backend:** FastAPI + MongoDB (Motor async) + Redis Cloud
- **Auth:** JWT (pyjwt) + bcrypt + MFA (TOTP + Email OTP)
- **Data Pipeline:** MongoDB aggregation pipelines (Phase 1) + Pandas (remaining modules)
- **SEO:** react-helmet-async + Puppeteer pre-rendering
- **AI:** OpenAI GPT-5.2 via Emergent LLM Key
- **Email:** Hostinger SMTP (smtp.hostinger.com:465)

## What's Been Implemented (Complete)

### MongoDB Aggregation Migration (Phase 1) — Feb 2026
- **Executive KPIs** (`/api/analytics/executive-kpis`): Revenue, units, COGS margin, MRP realisation, WoW, YoY — all computed via MongoDB `$group`, `$match`, `$addFields`
- **Revenue Trend** (`/api/analytics/executive-revenue-trend`): Daily time series via `$group` by day substring
- **ROS Gap Summary** (for executive dashboard): Style-level ROS gap analysis via `$group` + `$lookup` pipelines
- Filter resolution (categories, channels, regions) done via pre-query lookups instead of in-memory joins
- **New file:** `/app/backend/core/mongo_aggregations.py` — shared aggregation pipeline module
- ~350ms response time for all endpoints (no Pandas DataFrame loading)

### Core Platform
- Multi-tenant RBAC, JWT + MFA, Redis caching, onboarding, data upload V2
- AI demand forecasting, buy plan generator, executive dashboard
- 15+ analytics modules (remaining modules still use Pandas)

### Enterprise Features
- Invoice generation (TENANT-31), tenant backup/restore
- User funnel analytics (super admin only), email drip campaigns (super admin only)
- SFTP auto-scheduled uploads, chunked uploads with async processing

### Blog Engine & SEO (42 Blogs)
- 14 Original + 7 Saudi + 7 UAE + 7 South Africa + 7 USA
- Sitemaps, RSS, news-sitemap, llms.txt, Puppeteer pre-rendering

## Remaining Backlog

### Phase 2-4 Aggregation Migration (Future)
- Phase 2: DOH Analysis, Stock-Out Analysis
- Phase 3: Replenishment, Forecasting, Buy Plans
- Phase 4: Warehouse, Planogram, remaining endpoints

## Key Files
- `/app/backend/core/mongo_aggregations.py` — MongoDB aggregation pipelines
- `/app/backend/server.py` — Main API (migrated endpoints use aggregations)
- `/app/backend/routes/gap_analysis.py` — Gap analysis (Pandas for detailed, MongoDB for summary)

## 3rd Party Integrations
- OpenAI GPT-5.2 (via Emergent LLM Key)
- Hostinger SMTP, Redis Cloud, pyotp + segno
