# GetMyPlan PRD — AI-Powered Demand Planning Platform

## Original Problem Statement
Multi-tenant SaaS demand planning system with V2 data pipelines, ML forecasting, Redis caching, FTUE guided onboarding, comprehensive Technical SEO, MFA, tenant backup/restore, user funnel analytics, email drip campaigns, and enterprise features.

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
- JWT auth with email verification, password reset, forced password change
- MFA: TOTP (Authenticator App) + Email OTP
- Redis-powered caching layer
- Onboarding wizard with FTUE flow
- Data upload V2 with validation pipelines
- AI demand forecasting module
- Buy plan generator
- Executive dashboard with health scores
- Configuration page with save/edit
- 15+ analytics modules

### Tenant Backup & Restore
- Server-side compressed snapshots + downloadable ZIP export
- Restore modes: Overwrite or Merge
- Auto-cleanup: retains last 5 backups per tenant

### User Funnel Analytics Dashboard
- 5-stage funnel: Signup → Verified → Onboarded → Upload → Active
- KPI cards, funnel bar chart, signup trend line chart, conversion visualization
- User details table with stage filter
- Platform-wide (super admins) vs tenant-scoped views
- Time range presets + custom date range

### Email Drip Campaigns (Feb 2026)
- 4 automated campaigns for funnel drop-offs:
  - Not Verified, Not Onboarded, No Upload, Inactive User
- Drip sequence: Day 1, 3, 7 (escalating urgency emails)
- Toggle on/off per campaign
- Auto-runs daily via background scheduler
- Manual trigger via "Run Now" button
- Dedup: won't re-send same email within 30 days
- Send history and run logs
- **Endpoints:** `GET /api/drip/campaigns`, `PUT /api/drip/campaigns/{id}/toggle`, `POST /api/drip/run`, `GET /api/drip/history`, `GET /api/drip/runs`

### Technical SEO
- 28 SEO-optimized blogs, Puppeteer pre-rendering, dynamic meta, sitemaps, RSS, JSON-LD

## Prioritized Backlog

### P2 — Next
- TENANT-31: Invoice generation

### P3
- Auto-scheduled SFTP uploads
- Chunked uploads and async processing

### Refactoring (Low Priority)
- Migrate Pandas in-memory aggregations to MongoDB aggregation pipelines

## Key Files
- `/app/backend/services/drip_engine.py` — Drip campaign engine
- `/app/backend/routes/drip_campaigns.py` — Drip API endpoints
- `/app/backend/routes/funnel_analytics.py` — Funnel analytics API
- `/app/backend/routes/backup.py` — Backup & Restore endpoints
- `/app/backend/multi_tenant/auth.py` — Auth + MFA endpoints
- `/app/frontend/src/pages/DripCampaigns.jsx` — Campaign management page
- `/app/frontend/src/pages/UserFunnelDashboard.jsx` — Funnel dashboard
- `/app/frontend/src/pages/BackupRestore.jsx` — Backup management
- `/app/frontend/src/pages/MFASettings.jsx` — MFA settings

## 3rd Party Integrations
- OpenAI GPT-5.2 (via Emergent LLM Key)
- Hostinger SMTP (info@getmyplan.in)
- Redis Cloud
- pyotp + segno (TOTP/QR code generation)
