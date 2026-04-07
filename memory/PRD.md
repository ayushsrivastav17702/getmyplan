# GetMyPlan - AI-Powered Retail Analytics Platform — PRD

## Original Problem Statement
Build a Fashion Retail Gap Analysis platform (branded as **GetMyPlan**) with React + FastAPI featuring CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, GPT-5.2 FAQ Chatbot, multi-tenant architecture, and role-based access control.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme for dashboard, Swiss+High-Contrast for marketing)
- **Backend**: FastAPI with Python/Pandas
- **Database**: MongoDB (multi-tenant: separate DB per tenant, shared registry in merch_shared)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2 (NO Recharts)
- **Auth**: JWT with bcrypt, RBAC with 8 built-in roles + custom roles + permission overrides
- **Email**: SMTP via Hostinger (smtp.hostinger.com:465, SSL, info@getmyplan.in)
- **Security**: Enterprise middleware stack (rate limiting, security headers, input sanitization, structured logging)
- **Branding**: GetMyPlan (getmyplan.in)
- **Fonts**: Cabinet Grotesk + Satoshi (marketing), Inter (dashboard)

## Completed Phases

### Phase 1-37 (Previous sessions)
- Full MVP: 16+ analytics modules, Multi-Tenancy, RBAC, JWT Auth
- AI Demand Planning, Buy Plan Generator, Executive Dashboard
- TenantDataProvider refactoring, Onboarding Wizard
- Deployment health check passed

### Phase 38 — Self-Service Signup (Apr 2026)
- `/api/signup/register`, `/verify-email`, `/resend-verification`
- SMTP emails, 7-day trial, TrialBanner
- Testing: 24/25 PASS (Iteration 42)

### Phase 39 — GetMyPlan Rebranding (Apr 2026)
- All "Increff"/"Merchandising Tool" -> "GetMyPlan"
- Testing: 27/27 PASS (Iteration 43)

### Phase 40 — Enterprise Security Hardening (Apr 2026)
- Rate Limiting, Security Headers, MongoDB Indexes, Input Sanitization
- Testing: 29/29 PASS (Iteration 44)

### Phase 41 — Website Product Report + CORS/Projection Fix (Apr 2026)
- WEBSITE_PRODUCT_REPORT.md: 11-section report with real API data
- CORS lockdown + query projection fix

### Phase 42 — Marketing Landing Page (Apr 2026)
- **LandingPage.jsx**: Full marketing page with 9 sections: Navbar (glassmorphic), Hero, Stats Bar, Features Bento Grid (8 features), How It Works (4 steps), Pricing (3 tiers), Testimonials (3 reviews), CTA Banner, Footer
- **Routing changes**: `/` (unauth) → LandingPage, `/login` → LoginPage, `/signup` → Signup
- **Updated login links**: Signup, VerifyEmail, LoginPage all cross-link correctly
- **Design**: Cabinet Grotesk + Satoshi fonts, #2563eb primary, framer-motion animations, mobile responsive
- **Testing: 27/27 PASS (Iteration 45)**

## Key Files
- `/app/frontend/src/pages/LandingPage.jsx` — Marketing landing page (9 sections)
- `/app/frontend/src/App.js` — Routing: LandingPage at / for unauth, /login for login
- `/app/backend/middleware/security.py` — Enterprise security middleware
- `/app/backend/routes/signup.py` — Self-service signup
- `/app/memory/WEBSITE_PRODUCT_REPORT.md` — Complete website product report

## Route Map
```
UNAUTHENTICATED:
  /           → Marketing Landing Page
  /login      → Login Page
  /signup     → Signup Page (2-step wizard)
  /verify-email → Email Verification

AUTHENTICATED:
  /           → Getting Started (Dashboard Home)
  /dashboard  → Executive Dashboard
  /upload     → Data Upload
  /config     → Configuration
  /gap-analysis → Gap Analysis
  /stock-out  → Stock-Out Analysis
  /ai-demand  → AI Demand Planning
  /buy-plan   → Buy Plan Generator
  ... (18 more routes)
```

## Prioritized Backlog

### P1
- SFTP alert/notification system (SFTP-31 to SFTP-34)

### P2
- USER-17: Force password change on first login
- Plan upgrade page for trial users
- Scheduled analysis jobs

### P3
- USER-18: MFA
- TENANT-10: Tenant backup/restore
- TENANT-31: Invoice generation
- Data Quality Rules Engine
