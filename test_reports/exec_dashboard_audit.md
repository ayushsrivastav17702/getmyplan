# Executive Dashboard — Test Case Audit Report
## Date: Feb 2026

### Legend
- PASS: Feature exists and should pass the test
- GAP: Feature does not exist or is missing
- PARTIAL: Feature partially exists, needs enhancement

---

## MODULE 1: Data Validation Tests

| TC ID   | Test Case                                  | Status   | Notes |
|---------|--------------------------------------------|----------|-------|
| DASH-01 | KPI cards load within 3 seconds            | PASS     | Module cards render after API call; loading spinner shown |
| DASH-02 | Revenue calculation matches sales data     | GAP      | No revenue KPI card. Dashboard shows module summaries (ROS Gap, Stock-Out, DOH, etc.) not direct revenue/COGS |
| DASH-03 | Margin % calculation                       | GAP      | No margin metric exists anywhere in the dashboard |
| DASH-04 | Zero sales data shows "No data" message    | PASS     | Shows "No data available" + "Upload required files" when no data |
| DASH-05 | Partial data shows partial metrics         | PASS     | Each module fails silently to `null`; card shows "No data — upload files" |
| DASH-06 | Negative revenue handling                  | GAP      | No validation on negative values in backend or frontend |
| DASH-07 | Large numbers >1B in Cr/Lakhs format       | PASS     | `fmtCur()` formats: >=1Cr shows "₹X.XCr", >=1L shows "₹X.XL" |

## MODULE 2: Filter Tests

| TC ID   | Test Case                                  | Status   | Notes |
|---------|--------------------------------------------|----------|-------|
| DASH-08 | Date filter (Last 7 days)                  | GAP      | No quick-select presets ("Last 7 days", "Last 30 days"). Only manual start/end date pickers |
| DASH-09 | Custom date range filter                   | PASS     | Start date + End date inputs exist and pass params to API |
| DASH-10 | Category filter (Jeans)                    | PASS     | Multi-select category dropdown exists |
| DASH-11 | Multiple filters (Category + Region)       | PASS     | Categories, Channels, Regions all combinable |
| DASH-12 | Invalid date range (end < start)           | GAP      | No client-side or server-side validation for invalid date ranges |
| DASH-13 | Filter with no matching data               | PARTIAL  | API returns empty modules → cards show "No data", but no explicit "No results for this filter" message |
| DASH-14 | Reset all filters                          | PASS     | "Reset Filters" button resets to full date range + empty selections |

## MODULE 3: Chart Tests

| TC ID   | Test Case                                  | Status   | Notes |
|---------|--------------------------------------------|----------|-------|
| DASH-15 | Revenue trend chart renders                | GAP      | No line/trend chart. Only mini doughnut charts inside module cards |
| DASH-16 | Hover tooltip on chart                     | PASS     | Chart.js doughnut has default tooltips |
| DASH-17 | Click legend toggles data series           | PASS     | Chart.js default legend click behavior |
| DASH-18 | Chart responsiveness                       | PASS     | Chart.js responsive option enabled |
| DASH-19 | Single data point chart                    | PASS     | Doughnut handles single segment |
| DASH-20 | 365 days of data loads in <5s              | PARTIAL  | No specific optimization; performance depends on data volume |

## MODULE 4: Performance Tests

| TC ID   | Test Case                                  | Status   | Notes |
|---------|--------------------------------------------|----------|-------|
| DASH-21 | 50 stores load <5s                         | PARTIAL  | No benchmarks; depends on MongoDB query speed |
| DASH-22 | 500k sales records load <8s                | PARTIAL  | No pagination or chunking; single query per module |
| DASH-23 | 20 concurrent users                        | PARTIAL  | FastAPI handles concurrency, but no load testing done |
| DASH-24 | Auto-refresh every 30s                     | GAP      | No auto-refresh implemented; only manual "Refresh" button |

## MODULE 5: Edge Cases

| TC ID   | Test Case                                  | Status   | Notes |
|---------|--------------------------------------------|----------|-------|
| DASH-25 | No internet → offline message              | GAP      | No offline detection or network error UI |
| DASH-26 | Session timeout → redirect to login        | GAP      | No 401 Axios interceptor; expired token silently fails |
| DASH-27 | API 500 → user-friendly error              | PASS     | Catch block shows "Failed to fetch dashboard data" |
| DASH-28 | API 403 → access denied                    | PASS     | ProtectedRoute wraps with permission check |
| DASH-29 | Timezone handling                          | GAP      | No timezone conversion; dates displayed as-is from backend |
| DASH-30 | Leap year date (Feb 29)                    | PASS     | Standard JS/Python date handling |
| DASH-31 | Daylight savings transition                | PASS     | Backend uses UTC timestamps |
| DASH-32 | First/last day of month consistency        | PASS     | Standard date handling |
| DASH-33 | Week-over-Week comparison                  | GAP      | No comparison/growth calculation feature |
| DASH-34 | Year-over-Year comparison                  | GAP      | No YoY comparison feature |
| DASH-35 | Export dashboard to PDF                    | GAP      | No PDF export feature |

---

## Summary

| Status   | Count | Percentage |
|----------|-------|------------|
| PASS     | 18    | 51%        |
| PARTIAL  | 5     | 14%        |
| GAP      | 12    | 34%        |
| **Total**| **35**| **100%**   |

## GAP List (Prioritized for Implementation)

### P0 — Must Fix (Core Dashboard Functionality)
1. **DASH-26**: Session timeout → 401 interceptor that auto-redirects to login
2. **DASH-02 + DASH-03**: Revenue & Margin KPI cards (requires backend calc)
3. **DASH-33**: Week-over-Week growth % comparison
4. **DASH-08**: Quick date filter presets (Last 7d, 30d, 90d, custom)
5. **DASH-12**: Invalid date range validation (end < start)

### P1 — Should Fix (User Experience)
6. **DASH-15**: Revenue trend line chart (time-series visualization)
7. **DASH-34**: Year-over-Year comparison
8. **DASH-25**: Offline detection / network error handling
9. **DASH-24**: Auto-refresh toggle (every 30s)
10. **DASH-13**: Explicit "No results" empty state for filtered views

### P2 — Nice to Have
11. **DASH-35**: PDF export of dashboard
12. **DASH-06**: Negative revenue validation
13. **DASH-29**: Timezone-aware date display
