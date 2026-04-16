# GetMyPlan PRD — AI-Powered Demand Planning Platform

## Original Problem Statement
Multi-tenant SaaS demand planning platform for fashion retailers.

## Architecture
React 19 + Tailwind + Chart.js | FastAPI + MongoDB + Redis | JWT + MFA + Google OAuth

## Production State — April 16, 2026
Database reset to clean slate. Single tenant: production (GetMyPlan, enterprise).

### Super Admin Suite (7 pages)
| Page | Path | Features |
|------|------|----------|
| Tenant Management | `/admin/tenants` | CRUD, suspend/activate, impersonation, IP whitelisting |
| User Management | `/admin/users` | Cross-tenant CRUD, role edit, status, password reset |
| Platform Analytics | `/admin/analytics` | MRR, tenant health, plan dist, WAU/MAU, signup trend |
| Feature Flags | `/admin/feature-flags` | CRUD flags + per-tenant overrides |
| Global Config | `/admin/global-config` | Default settings template, apply to tenants |
| Audit Trail | `/admin/audit-logs` | SOC2 logging, 5 anomaly rules, alerts, CSV export |

### Security
- JWT + MFA (TOTP + Email OTP) + Google OAuth
- IP whitelisting per tenant (CIDR support, super_admin bypass)
- Login rate limiting, security headers
- Anomaly detection (5 rules), audit trail

### Plan Enforcement
- User count limits (starter: 3, professional: 10, enterprise: unlimited)
- Store count limits (starter: 10, professional: 50, enterprise: unlimited)
- Trial expiration automation (hourly scheduler, 3-day grace)

### Upload Performance
- Batch size: 5000 (was 2000)
- Parallel master data fetches (asyncio.gather)
- Bulk $in deletes (was per-day loops)

### Credentials
- admin@demo.com / demo1234 (super_admin, tenant: production)

### Remaining Backlog
- P2: Payment integration (Stripe/Razorpay)
- P2: Full SAML/OIDC SSO (Okta, Azure AD)
- P3: Subdomain-based tenant routing
