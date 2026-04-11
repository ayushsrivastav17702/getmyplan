# GetMyPlan PRD — AI-Powered Demand Planning Platform

## Original Problem Statement
Multi-tenant SaaS demand planning system with V2 data pipelines, ML forecasting, Redis caching, FTUE guided onboarding, comprehensive Technical SEO (SSG Pre-rendering, Sitemaps, JSON-LD, Blog Engine, RSS Feeds, Dynamic Meta), MFA, tenant backup/restore, user funnel analytics, and enterprise features.

## Core Architecture
- **Frontend:** React 19 + Tailwind CSS + Shadcn/UI + Chart.js (react-chartjs-2)
- **Backend:** FastAPI + MongoDB (Motor async) + Redis Cloud
- **Auth:** JWT (pyjwt) + bcrypt + MFA (TOTP + Email OTP)
- **SEO:** react-helmet-async + Puppeteer pre-rendering (prerender.js)
- **AI:** OpenAI GPT-5.2 via Emergent LLM Key
- **Email:** Hostinger SMTP (smtp.hostinger.com:465)

## What's Been Implemented (Complete)

### Core Platform
- Multi-tenant architecture with RBAC (8 roles, 21 permissions)
- JWT auth with email verification, password reset, forced password change
- MFA: TOTP (Authenticator App) + Email OTP (Feb 2026)
- Redis-powered caching layer
- Onboarding wizard with FTUE flow
- Data upload V2 with validation pipelines
- AI demand forecasting module
- Buy plan generator
- Executive dashboard with health scores
- Configuration page with save/edit
- 15+ analytics modules (Gap Analysis, DOH, Stock-Out, Replenishment, etc.)

### Tenant Backup & Restore (Feb 2026)
- Server-side compressed snapshots stored in MongoDB
- Downloadable ZIP export (JSON per collection + metadata)
- Restore modes: Overwrite (replace all) or Merge (add alongside)
- Auto-cleanup: retains last 5 backups per tenant

### User Funnel Analytics Dashboard (Feb 2026)
- **Funnel stages:** Signup → Email Verified → Onboarding Complete → First Upload → Active User
- 5 KPI cards with stage counts and conversion percentages
- Overall conversion rate bar (blue gradient)
- Funnel Breakdown horizontal bar chart (Chart.js)
- Signup Trend line chart (Chart.js)
- Stage-to-Stage conversion visualization with arrows and drop-off
- User details table with email, company, role, current stage, dates
- Stage filter dropdown for table filtering
- Time range: Preset buttons (7/30/90 days/All time) + Custom date range
- Access: Super admins see platform-wide, tenant admins see their tenant
- **Endpoint:** `GET /api/analytics/funnel?days=N&start_date=X&end_date=Y`

### Technical SEO (Complete)
- 28 SEO-optimized blog posts (Original + Saudi + UAE)
- Puppeteer pre-rendering for 37+ routes
- Dynamic meta via react-helmet-async
- XML sitemaps, news-sitemap, RSS feeds, JSON-LD

### UX/Branding
- Cookie consent banner
- Platform badge suppression
- Health Score states, icons, YoY units fixes

## Prioritized Backlog

### P2 — Next
- TENANT-31: Invoice generation

### P3
- Auto-scheduled SFTP uploads for Data Upload V2
- Chunked uploads and Async processing

### Refactoring (Low Priority)
- Migrate Pandas in-memory aggregations to MongoDB aggregation pipelines

## Key Files
- `/app/backend/routes/funnel_analytics.py` — Funnel analytics API
- `/app/backend/routes/backup.py` — Backup & Restore endpoints
- `/app/backend/multi_tenant/auth.py` — Auth + MFA endpoints
- `/app/backend/services/mfa_service.py` — TOTP/OTP helper service
- `/app/frontend/src/pages/UserFunnelDashboard.jsx` — Funnel analytics dashboard
- `/app/frontend/src/pages/BackupRestore.jsx` — Backup management page
- `/app/frontend/src/pages/MFAChallenge.jsx` — Login MFA challenge UI
- `/app/frontend/src/pages/MFASettings.jsx` — MFA settings page
- `/app/frontend/src/context/AuthContext.js` — Auth context with MFA state

## 3rd Party Integrations
- OpenAI GPT-5.2 (via Emergent LLM Key)
- Hostinger SMTP (info@getmyplan.in)
- Redis Cloud
- pyotp + segno (TOTP/QR code generation)
