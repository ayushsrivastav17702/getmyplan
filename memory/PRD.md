# GetMyPlan PRD — AI-Powered Demand Planning Platform

## Original Problem Statement
Multi-tenant SaaS demand planning platform for fashion retailers.

## Architecture
React 19 + Tailwind + Chart.js | FastAPI + MongoDB + Redis | JWT + MFA + Google OAuth

## Production Readiness — April 16, 2026

### Super Admin Suite (6 pages)
| Page | Path | Features | Test |
|------|------|----------|------|
| Tenant Management | `/admin/tenants` | CRUD, suspend/activate, impersonation | iter 86-87 |
| User Management | `/admin/users` | Cross-tenant CRUD, role edit, status, password reset | iter 88 |
| Audit Trail | `/admin/audit-logs` | SOC2 logging, 5 anomaly rules, alerts, CSV export | iter 89-90 |
| Platform Analytics | `/admin/analytics` | MRR, tenant health, plan distribution, WAU/MAU | iter 91 |
| Feature Flags | `/admin/feature-flags` | CRUD flags, per-tenant overrides, phased rollouts | iter 92 |

### Authentication
- JWT + MFA (TOTP + Email OTP) — existing
- Google OAuth via Emergent Auth — iter 92 ("Sign in with Google" on login page)
- Plan limits enforcement (user count caps) — iter 91
- Trial expiration automation (hourly scheduler) — iter 91

### Feature Flags System (iter 92)
- Global flags with default_enabled toggle
- Per-tenant overrides (enable/disable per tenant)
- Resolved flags endpoint: `/api/admin/platform/feature-flags/tenant/{tenant_id}`
- Frontend `FeatureFlags.jsx` management page with expandable overrides panel

### Existing Platform Features
- Multi-tenant RBAC, Invoice gen, Backup/Restore, User Funnel, Drip Campaigns
- SFTP scheduling, Chunked uploads, 42 SEO blogs, Pre-rendering
- MongoDB aggregation analytics (zero Pandas), Help Center, Onboarding, FAQ Chatbot

### Future/Backlog
- P2: Payment integration (Stripe/Razorpay)
- P2: Full SAML/OIDC SSO (Okta, Azure AD)
- P3: Upload speed optimization, subdomain routing, IP whitelisting
