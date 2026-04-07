# GetMyPlan - AI-Powered Retail Analytics Platform — PRD

## Original Problem Statement
Build a Fashion Retail Gap Analysis platform (branded as **GetMyPlan**) with React + FastAPI featuring CSV data uploading, multiple analytics dashboards, dynamic filtering with presets, Chart.js visualizations, GPT-5.2 FAQ Chatbot, multi-tenant architecture, and role-based access control.

## Architecture
- **Frontend**: React with Tailwind CSS (Salesforce theme)
- **Backend**: FastAPI with Python/Pandas
- **Database**: MongoDB (multi-tenant: separate DB per tenant, shared registry in merch_shared)
- **AI**: GPT 5.2 via Emergent LLM Key
- **Charts**: Chart.js + react-chartjs-2 (NO Recharts)
- **Auth**: JWT with bcrypt, RBAC with 8 built-in roles + custom roles + permission overrides
- **Email**: SMTP via Hostinger (smtp.hostinger.com:465, SSL, info@getmyplan.in)
- **Security**: Enterprise middleware stack (rate limiting, security headers, input sanitization, structured logging)
- **Branding**: GetMyPlan (getmyplan.in)

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
- **Rate Limiting**: slowapi — 10/min auth, 200/min general
- **Security Headers**: HSTS, X-Frame-Options=DENY, CSP, X-XSS-Protection, Referrer-Policy, Permissions-Policy, Cache-Control=no-store
- **MongoDB Indexes**: Performance indexes + TTL for verification tokens
- **Request Size Limits**: 1MB JSON, 50MB file uploads
- **Enhanced Health Check**: DB status, version, uptime, timestamp
- **Structured Logging**: JSON format, correlation IDs, tenant tracking
- **Global Error Handler**: Clean JSON errors, no stack traces
- **Input Sanitization**: NoSQL injection, XSS, path traversal detection
- **Middleware Stack Order**: CORS -> Error Handler -> Size Limiter -> Logging -> Security Headers -> Tenant
- Testing: **29/29 PASS (Iteration 44)**

### Phase 41 — Website Product Report + CORS/Projection Fix (Apr 2026)
- **WEBSITE_PRODUCT_REPORT.md**: Comprehensive 11-section report with real API data, screenshots, feature list, user flow, data models, differentiators, target customer — ready for website redesign
- **CORS Lockdown**: Restricted from `*` to specific domains (`getmyplan.in`, `*.getmyplan.in`, `localhost:3000`, preview URL) with `allow_origin_regex` for subdomain pattern matching
- **Query Projection Fix**: Added MongoDB projection to `get_cached_data()` at server.py:368 to exclude `_id` and limit returned fields

## Security Features Summary
```
Security Headers (every API response):
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-XSS-Protection: 1; mode=block
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'self'; frame-ancestors 'none'
  Cache-Control: no-store, no-cache, must-revalidate, private

CORS (production):
  Exact origins: https://getmyplan.in, http://localhost:3000
  Regex: https://*.getmyplan.in (via allow_origin_regex)

Rate Limiting:
  Auth endpoints: 10/minute (login, signup, verify-email)
  General API: 200/minute
  Resend verification: 3/minute

Input Sanitization:
  NoSQL: $gt, $lt, $ne, $regex, $exists, $or, $and, $where
  XSS: <script>, javascript:, on* event handlers
  Path Traversal: ../ and ..\\
```

## Key Files
- `/app/backend/middleware/security.py` — All security middleware
- `/app/backend/services/smtp_email_service.py` — SMTP email service
- `/app/backend/routes/signup.py` — Self-service signup
- `/app/backend/multi_tenant/auth.py` — JWT auth with trial checking
- `/app/memory/WEBSITE_PRODUCT_REPORT.md` — Complete website product report (11 sections)

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
