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

### Blog Engine & SEO (42 Total Blogs)
- **14 Original** blogs (Software Reviews, How-To, Industry, KPIs, AI)
- **7 Saudi Arabia** blogs (Vision 2030, Ramadan, e-commerce, logistics)
- **7 UAE** blogs (Ramadan/DSS, multi-brand, luxury, tourist season, VAT)
- **7 South Africa** blogs (ZAR focus, Black Friday, multichannel, load shedding, local brands, festive season, value vs premium)
- **7 USA** blogs (USD focus, BFCM, regional planning, D2C/Shopify, Amazon Fashion, sustainability, supply chain/tariffs)
- Updated: sitemap.xml (51 URLs), news-sitemap.xml (42 articles), RSS feed (42 items), llms.txt, prerender.js (51 routes)

### Core Platform
- Multi-tenant architecture with RBAC (8 roles, 21 permissions)
- JWT auth + MFA (TOTP + Email OTP)
- Redis caching, onboarding wizard, Data upload V2
- AI demand forecasting, Buy plan generator
- Executive dashboard, Configuration page
- 15+ analytics modules

### Tenant Backup & Restore
- Compressed snapshots + ZIP export, Overwrite/Merge restore, Auto-cleanup (5 max)

### User Funnel Analytics Dashboard
- 5-stage funnel with KPI cards, charts, conversion visualization, user table
- Platform-wide vs tenant-scoped views, time range filtering

### Email Drip Campaigns
- 4 campaigns (Not Verified, Not Onboarded, No Upload, Inactive)
- Day 1/3/7 drip sequence, auto-daily + manual trigger, dedup

## Prioritized Backlog

### P2 — Next
- TENANT-31: Invoice generation

### P3
- Auto-scheduled SFTP uploads
- Chunked uploads and async processing

### Refactoring
- Migrate Pandas aggregations to MongoDB pipelines

## Key Files
- `/app/frontend/src/data/blogData.js` — 42 blog entries
- `/app/frontend/public/sitemap.xml` — Main sitemap
- `/app/frontend/public/news-sitemap.xml` — Google News sitemap
- `/app/frontend/public/blog/rss.xml` — RSS feed
- `/app/frontend/public/llms.txt` — LLM-readable content index
- `/app/frontend/prerender.js` — Puppeteer SSG (51 routes)

## 3rd Party Integrations
- OpenAI GPT-5.2 (via Emergent LLM Key)
- Hostinger SMTP (info@getmyplan.in)
- Redis Cloud
- pyotp + segno (TOTP/QR)
