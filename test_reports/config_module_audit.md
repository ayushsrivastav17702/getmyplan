# Configuration Module — Test Case Audit Report
## Date: Feb 2026

### Legend
- PASS: Feature exists and should pass the test
- GAP: Feature does not exist or is missing
- PARTIAL: Feature partially exists, needs enhancement

---

## Parameter Configuration Tests (8 tests)

| TC ID   | Test Case                           | Status   | Notes |
|---------|-------------------------------------|----------|-------|
| CONF-01 | Update PSA Benchmark                | PARTIAL  | `pivotal_size_threshold` exists (slider 50-100%) but name is "Pivotal Size Threshold" not "PSA Benchmark". No `psa_benchmark` field. Recalculation on analytics pages not verified. |
| CONF-02 | Update Cover Days                   | GAP      | No `cover_days` parameter in config. `AnalysisConfig` has no cover_days field. |
| CONF-03 | Update ROS Period                   | GAP      | No `ros_period` parameter. ROS period is hardcoded in analytics calculations. |
| CONF-04 | Update Ideal DOH                    | GAP      | No `ideal_doh` parameter. DOH ideal is hardcoded (typically 9 days) in server.py. |
| CONF-05 | Update Topseller X Factor           | GAP      | No `topseller_x_factor` parameter. X-factor hardcoded in analytics. |
| CONF-06 | Negative PSA Benchmark validation   | GAP      | Slider has min=50, prevents <50 but no backend validation for arbitrary values via API. |
| CONF-07 | Value >100 PSA Benchmark            | PARTIAL  | Slider has max=100 prevents >100 on UI. No backend range validation. |
| CONF-08 | Decimal Cover Days validation       | GAP      | No Cover Days field exists at all. |

## Module Toggle Tests (6 tests)

| TC ID   | Test Case                           | Status   | Notes |
|---------|-------------------------------------|----------|-------|
| CONF-09 | Enable NOOS                         | PASS     | `noos_enabled` toggle exists, persists via /api/config |
| CONF-10 | Disable NOOS                        | PARTIAL  | Toggle saves to DB. But Gap Analysis page doesn't check `noos_enabled` to hide/show NOOS tab. |
| CONF-11 | Enable Replenishment                | GAP      | No `replenishment_enabled` toggle. Replenishment page always shown. |
| CONF-12 | Disable Replenishment               | GAP      | No module toggle for Replenishment. |
| CONF-13 | Enable Size Set Gap                 | PASS     | `size_gap_enabled` toggle exists |
| CONF-14 | Disable Size Set Gap                | PARTIAL  | Toggle saves. Gap Analysis page doesn't check to hide/show Size Gap tab. |

## Store Classification Tests (6 tests)

| TC ID   | Test Case                           | Status   | Notes |
|---------|-------------------------------------|----------|-------|
| CONF-15 | Add new store class                 | GAP      | No Store Classification UI or backend. Store data comes from uploaded store_master CSV. |
| CONF-16 | Edit store class                    | GAP      | No store class CRUD. |
| CONF-17 | Delete unused store class           | GAP      | No store class management. |
| CONF-18 | Filter by single store class        | GAP      | No store class filter in dashboard. Filters use region/channel/store. |
| CONF-19 | Filter by multiple store classes    | GAP      | No store class filter. |
| CONF-20 | Store class priority ordering       | GAP      | No store class concept. |

## Category Hierarchy Tests (6 tests)

| TC ID   | Test Case                           | Status   | Notes |
|---------|-------------------------------------|----------|-------|
| CONF-21 | Add new category                    | GAP      | No category management UI. Categories come from style_master upload. |
| CONF-22 | Edit category name                  | GAP      | No category editing. |
| CONF-23 | Delete unused category              | GAP      | No category CRUD. |
| CONF-24 | Category to style mapping           | PASS     | Category filter works in analytics — styles correctly categorized from style_master. |
| CONF-25 | Nested category hierarchy           | GAP      | Flat category list only, no parent-child hierarchy. |
| CONF-26 | Category performance aggregation    | PASS     | Category filter aggregates revenue correctly across analytics pages. |

## User Role Configuration Tests (6 tests)

| TC ID   | Test Case                           | Status   | Notes |
|---------|-------------------------------------|----------|-------|
| CONF-27 | Assign role to user                 | PASS     | PUT /api/users/{email}/role works. Role change reflected on next login. |
| CONF-28 | Change user role                    | PASS     | Same endpoint as CONF-27. Promotion/demotion works. |
| CONF-29 | Remove user from tenant             | PASS     | DELETE /api/users/{email} soft-deletes (sets is_active=false). |
| CONF-30 | Create custom role                  | GAP      | No custom role creation. Roles are hardcoded in rbac.py (8 fixed roles). |
| CONF-31 | Role-based menu visibility          | PASS     | ProtectedRoute + navItems filter by permission. Verified in iteration 16. |
| CONF-32 | User permission override            | GAP      | No per-user permission override. Permissions are role-based only. |

---

## Summary

| Status   | Count | Percentage |
|----------|-------|------------|
| PASS     | 8     | 25%        |
| PARTIAL  | 4     | 13%        |
| GAP      | 20    | 63%        |
| **Total**| **32**| **100%**   |

## GAP List (Prioritized)

### P0 — Must Implement (Core Config Parameters)
1. **CONF-02**: Cover Days parameter
2. **CONF-03**: ROS Period parameter
3. **CONF-04**: Ideal DOH parameter
4. **CONF-05**: Topseller X Factor parameter
5. **CONF-06/07**: Backend range validation for all parameters
6. **CONF-10/14**: Module toggles actually hide/show tabs in analytics pages

### P1 — Should Implement
7. **CONF-11/12**: Replenishment module toggle
8. **CONF-15-20**: Store Classification CRUD + filter integration
9. **CONF-21-23/25**: Category Hierarchy CRUD with parent-child

### P2 — Nice to Have
10. **CONF-30**: Custom role creation
11. **CONF-32**: Per-user permission override
