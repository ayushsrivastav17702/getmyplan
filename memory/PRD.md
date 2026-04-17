# GetMyPlan PRD — AI-Powered Demand Planning Platform

## Architecture
React 19 + Tailwind + Chart.js | FastAPI + MongoDB + Redis | JWT + MFA + Google OAuth

## Buy Planning Module (Phase 1-3 Complete)

### Phase 1: Store Wedge + Style Mix (iter 95)
- Store Wedge: A (top 80% rev), B (next 15%), C (bottom 5%)
- Style Mix: Core (>5/wk + >80% presence), Fashion (peak:avg >3x), Test (<8wk or <2/wk)
- Assortment Matrix: A=Full, B=Standard, C=Core-only

### Phase 2: Buy Formula + Display Minimums (iter 96)
- Display minimums config: category × wedge (e.g. Apparel/A = 4×2=8 units)
- Full formula: MAX(sell_through × demand - SOH, display_min × stores, safety_stock)
- Sell-through targets: Core=1.2, Fashion=0.8, Test=0.4 (configurable)
- Binding constraint tracking (demand/display_min/safety_stock)

### Phase 3: DNA Tagging + Attribution (iter 96)
- Auto DNA: flow_rank (Hero/Core/Fill-in by revenue), lifecycle_stage (Launch/Peak/Decline/Exit)
- Single SKU + bulk style tagging endpoints
- Attribution: Core→ALL stores, Fashion→A+B, Test→A only

### Frontend: /buy-planning (6 tabs)
- Assortment Matrix, Buy Plan, Store Wedge, Style Mix, DNA Tags, Attribution

## Super Admin Suite (7 pages, iters 86-94)
- Tenant/User CRUD, Analytics, Feature Flags, Global Config, Audit Trail, IP Whitelisting

## Credentials
- admin@demo.com / demo1234 (super_admin, tenant: production)

## Remaining Backlog
- P2: Payment integration (Stripe/Razorpay)
- P2: Full SAML/OIDC SSO (Okta, Azure AD)
