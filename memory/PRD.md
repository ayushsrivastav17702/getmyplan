# GetMyPlan PRD — AI-Powered Demand Planning Platform

## Architecture
React 19 + Tailwind + Chart.js | FastAPI + MongoDB + Redis | JWT + MFA + Google OAuth

## Buy Planning Module (Complete — Phases 1-3 + B/C/F)

### Phase 1: Store Wedge + Style Mix (iter 95)
### Phase 2: Buy Formula + Display Minimums (iter 96)
### Phase 3: DNA Tagging + Attribution (iter 96)

### Feature B: Manual Overrides (iter 97)
- Store wedge override: POST/DELETE with audit trail
- Style mix override: POST/DELETE with audit trail
- Override history endpoint, manual_override flag skips auto-refresh

### Feature C: CSV Export (iter 97)
- GET /buy-planning/buy-formula/export/csv — full buy plan with 19 columns
- Includes SKU, Style, Category, Mix, ROS, SOH, Demand, Display Min, Safety, Buy Qty, Value, Constraint, DNA

### Feature F: Weekly Auto-Refresh (iter 97)
- asyncio scheduler runs Sundays 2 AM UTC
- Reclassifies store wedges (skips manual overrides)
- Integrated into server.py startup

## Super Admin Suite (7 pages, iter 86-94)
## Security: JWT + MFA + Google OAuth + IP whitelisting + Anomaly Detection
## Credentials: admin@demo.com / demo1234 (super_admin, production)

## Remaining Backlog
- P2: Payment integration (Stripe/Razorpay)
- P2: Full SAML/OIDC SSO
