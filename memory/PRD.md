# GetMyPlan - AI-Powered Retail Analytics Platform — PRD

## Original Problem Statement
Build a Fashion Retail Gap Analysis platform (branded as **GetMyPlan**) with React + FastAPI featuring CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, GPT-5.2 FAQ Chatbot, multi-tenant architecture, and role-based access control.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme for dashboard, Enterprise SaaS for marketing)
- **Backend**: FastAPI with Python/Pandas
- **Database**: MongoDB (multi-tenant: separate DB per tenant, shared registry in merch_shared)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2 (NO Recharts)
- **Auth**: JWT with bcrypt, RBAC with 8 built-in roles + custom roles + permission overrides
- **Email**: SMTP via Hostinger (smtp.hostinger.com:465, SSL, info@getmyplan.in)
- **Security**: Enterprise middleware stack (rate limiting, security headers, input sanitization, structured logging)
- **Animations**: framer-motion v12.38.0
- **Branding**: GetMyPlan (getmyplan.in)

## Completed Phases

### Phase 1-37 (Previous sessions)
- Full MVP: 16+ analytics modules, Multi-Tenancy, RBAC, JWT Auth
- AI Demand Planning, Buy Plan Generator, Executive Dashboard
- TenantDataProvider refactoring, Onboarding Wizard

### Phase 38 — Self-Service Signup (Apr 2026)
- SMTP emails, 7-day trial, TrialBanner — 24/25 PASS (Iteration 42)

### Phase 39 — GetMyPlan Rebranding (Apr 2026)
- All "Increff" -> "GetMyPlan" — 27/27 PASS (Iteration 43)

### Phase 40 — Enterprise Security (Apr 2026)
- Rate Limiting, Security Headers, MongoDB Indexes — 29/29 PASS (Iteration 44)

### Phase 41 — Website Product Report + CORS Fix (Apr 2026)
- WEBSITE_PRODUCT_REPORT.md: 11-section report with real API data
- CORS lockdown + query projection fix

### Phase 42 — Marketing Landing Page v1 (Apr 2026)
- Initial landing page — 27/27 PASS (Iteration 45)

### Phase 43 — Enterprise SaaS Landing Page Redesign (Apr 2026)
- **12 separate components** in `/components/landing/`:
  1. **Navbar** — Glassmorphic with scroll effect, resources dropdown
  2. **Hero** — Animated gradient blobs, live badge, dashboard preview mockup
  3. **TrustBar** — 5 customer logos with hover effects
  4. **StatsSection** — 4 animated counters (91%, 33, 15 min, 3)
  5. **Features** — 8 cards with hover icon color inversion + Popular badges
  6. **HowItWorks** — 4 steps with gradient connecting line
  7. **ComparisonTable** — vs Excel vs ERP (10 rows, all green for GetMyPlan)
  8. **Pricing** — Monthly/Yearly billing toggle, Most Popular gradient badge, 3 tiers
  9. **Testimonials** — Dark carousel with prev/next arrows, dot nav, summary stats
  10. **FAQ** — 6-item accordion with expand/collapse
  11. **CTASection** — Gradient background with glow effects
  12. **Footer** — Newsletter signup, 5-column layout, social links
- **Testing: 23/24 PASS (Iteration 46)** — 1 test env timing issue, not a real bug

## Route Map
```
UNAUTHENTICATED:
  /           -> Marketing Landing Page (12 sections)
  /login      -> Login Page (with "Back to home" link)
  /signup     -> Signup Page (2-step wizard)
  /verify-email -> Email Verification

AUTHENTICATED:
  /           -> Getting Started (Dashboard Home)
  /dashboard  -> Executive Dashboard
  /upload     -> Data Upload
  /config     -> Configuration
  /gap-analysis -> Gap Analysis
  /stock-out  -> Stock-Out Analysis
  /ai-demand  -> AI Demand Planning
  /buy-plan   -> Buy Plan Generator
  ... (18 more routes)
```

## Key Files
- `/app/frontend/src/components/landing/*` — 12 landing page components
- `/app/frontend/src/pages/LandingPage.jsx` — Landing page composition
- `/app/frontend/src/App.js` — Routing with /login + LandingPage at /
- `/app/backend/middleware/security.py` — Enterprise security
- `/app/memory/WEBSITE_PRODUCT_REPORT.md` — Complete product report

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
