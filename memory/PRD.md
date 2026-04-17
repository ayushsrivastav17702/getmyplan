# GetMyPlan PRD — AI-Powered Demand Planning Platform

## Original Problem Statement
Multi-tenant SaaS demand planning platform for fashion retailers.

## Architecture
React 19 + Tailwind + Chart.js | FastAPI + MongoDB + Redis | JWT + MFA + Google OAuth

## Production State — April 17, 2026

### Buy Planning Module (NEW — Phase 1)
**Store Wedge Classification:**
- Revenue-based: A = top 80% revenue, B = next 15%, C = bottom 5%
- Fallback: uses existing tier from store_master
- Updates store_master with `wedge_class` field

**Style Mix Tagging:**
- Core = avg >5 units/wk + >80% week presence
- Fashion = peak/avg >3x + lifecycle <26 weeks
- Test = <8 weeks old OR <2 units/wk
- Updates sku_ean_master with `style_mix` + stats

**Assortment Matrix:**
- A-Stores → Full (Core + Fashion + Test)
- B-Stores → Standard (Core + Fashion)
- C-Stores → Efficiency (Core NOS only)

### Super Admin Suite (7 pages)
- Tenant Management, User Management, Platform Analytics
- Feature Flags, Global Config, Audit Trail + Anomaly Detection

### Security
- JWT + MFA + Google OAuth + IP whitelisting per tenant
- SOC2 audit trail, 5 anomaly detection rules

### Performance
- Upload: batch 5000, parallel fetches, $in bulk deletes

### Credentials
- admin@demo.com / demo1234 (super_admin, tenant: production)

### Remaining Backlog
- P1: Buy Planning Phase 2 (Buy Formula + Display Minimums)
- P1: Buy Planning Phase 3 (AI Readiness Audit)
- P2: Payment integration (Stripe/Razorpay)
- P2: Full SAML/OIDC SSO (Okta, Azure AD)
