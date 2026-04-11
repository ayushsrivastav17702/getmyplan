# GetMyPlan PRD — AI-Powered Demand Planning Platform

## Original Problem Statement
Multi-tenant SaaS demand planning system with V2 data pipelines, ML forecasting, Redis caching, FTUE guided onboarding, comprehensive Technical SEO (SSG Pre-rendering, Sitemaps, JSON-LD, Blog Engine, RSS Feeds, Dynamic Meta), MFA, and enterprise features.

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
- **MFA: TOTP (Authenticator App) + Email OTP** (Feb 2026)
  - Setup TOTP with QR code + manual key
  - Login MFA challenge with authenticator/email tabs
  - Tenant admin MFA enforcement
  - MFA settings page at /security
- Redis-powered caching layer
- Onboarding wizard with FTUE flow
- Data upload V2 with validation pipelines
- AI demand forecasting module
- Buy plan generator
- Executive dashboard with health scores
- Configuration page with save/edit
- 15+ analytics modules (Gap Analysis, DOH, Stock-Out, Replenishment, etc.)

### Technical SEO (Complete)
- 28 SEO-optimized blog posts (Original + Saudi + UAE)
- Puppeteer pre-rendering for 37+ routes (prerender.js on postbuild)
- Dynamic meta via react-helmet-async
- XML sitemaps, news-sitemap, RSS feeds, JSON-LD, robots.txt, llms.txt

### UX/Branding
- Cookie consent banner (CookieConsent.jsx)
- Platform badge suppression (CSS + interval)
- Health Score states, icons, YoY units fixes
- Save button and description fixes on Configuration

### MFA Endpoints (Feb 2026)
- `GET /api/auth/mfa/status` - MFA status for authenticated user
- `POST /api/auth/mfa/setup-totp` - Generate TOTP secret + QR code
- `POST /api/auth/mfa/verify-setup` - Verify TOTP code to enable MFA
- `POST /api/auth/mfa/verify-totp` - Verify TOTP during login
- `POST /api/auth/mfa/send-email-otp` - Send email OTP for login
- `POST /api/auth/mfa/verify-email-otp` - Verify email OTP during login
- `POST /api/auth/mfa/disable` - Disable MFA (requires password)
- `POST /api/auth/mfa/tenant-enforce` - Admin MFA enforcement toggle

## Prioritized Backlog

### P1 — Next
- TENANT-10: Tenant backup/restore functionality

### P2
- TENANT-31: Invoice generation
- Build User Funnel Analytics Dashboard

### P3
- Auto-scheduled SFTP uploads for Data Upload V2
- Chunked uploads and Async processing

### Refactoring (Low Priority)
- Migrate Pandas in-memory aggregations to MongoDB aggregation pipelines

## Key Files
- `/app/backend/multi_tenant/auth.py` — Auth + MFA endpoints
- `/app/backend/services/mfa_service.py` — TOTP/OTP helper service
- `/app/frontend/src/pages/MFAChallenge.jsx` — Login MFA challenge UI
- `/app/frontend/src/pages/MFASettings.jsx` — MFA settings page
- `/app/frontend/src/context/AuthContext.js` — Auth context with MFA state
- `/app/frontend/src/pages/LoginPage.js` — Login with MFA challenge support
- `/app/frontend/prerender.js` — Puppeteer SSG script

## 3rd Party Integrations
- OpenAI GPT-5.2 (via Emergent LLM Key)
- Hostinger SMTP (info@getmyplan.in)
- Redis Cloud
- pyotp + segno (TOTP/QR code generation)
