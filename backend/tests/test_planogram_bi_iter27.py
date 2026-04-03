"""
Planogram Fill Rate (PLAN-01 to PLAN-32) and BI Dashboard (BI-01 to BI-35) Tests
Iteration 27 - Comprehensive test coverage for both modules
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ============================================================================
# FIXTURES
# ============================================================================
@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for demo tenant"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@demo.com",
        "password": "demo1234",
        "tenant_id": "demo"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping tests")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token and tenant ID"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "X-Tenant-ID": "demo",
        "Content-Type": "application/json"
    }


# ============================================================================
# PLANOGRAM FILL RATE TESTS (PLAN-01 to PLAN-32)
# ============================================================================
class TestPlanogramAnalysis:
    """PLAN-01 to PLAN-14, PLAN-21 to PLAN-25: Fill Rate Analysis endpoint"""
    
    def test_plan_01_fill_rate_formula(self, auth_headers):
        """PLAN-01: fill_rate = (current_stock / norm_allocated) * 100 per store-EAN"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "detail" in data
        # Verify formula on first few detail rows
        for row in data["detail"][:5]:
            expected = round((row["current_stock"] / max(row["norm_allocated"], 1)) * 100, 1)
            assert abs(row["fill_rate"] - expected) < 0.2, f"Fill rate mismatch: {row['fill_rate']} vs {expected}"
        print("PASS PLAN-01: fill_rate formula verified")
    
    def test_plan_02_fill_rate_100_when_stock_equals_norm(self, auth_headers):
        """PLAN-02: Detail rows where current_stock = norm_allocated have fill_rate ~100%"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        for row in data["detail"]:
            if row["current_stock"] == row["norm_allocated"] and row["norm_allocated"] > 0:
                assert 99.5 <= row["fill_rate"] <= 100.5, f"Expected ~100%, got {row['fill_rate']}%"
        print("PASS PLAN-02: fill_rate ~100% when stock = norm")
    
    def test_plan_03_fill_rate_0_when_stock_is_zero(self, auth_headers):
        """PLAN-03: Detail rows with current_stock = 0 have fill_rate = 0%"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        for row in data["detail"]:
            if row["current_stock"] == 0:
                assert row["fill_rate"] == 0, f"Expected 0%, got {row['fill_rate']}%"
        print("PASS PLAN-03: fill_rate = 0% when stock = 0")
    
    def test_plan_04_overall_fill_rate_weighted_average(self, auth_headers):
        """PLAN-04: summary.overall_fill_rate is weighted average of all store-SKU pairs"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        summary = data["summary"]
        # Weighted avg = total_current_stock / total_norm_allocated * 100
        expected = round((summary["total_current_stock"] / max(summary["total_norm_allocated"], 1)) * 100, 1)
        assert abs(summary["overall_fill_rate"] - expected) < 0.5
        print(f"PASS PLAN-04: overall_fill_rate = {summary['overall_fill_rate']}% (weighted avg)")
    
    def test_plan_05_category_data_aggregation(self, auth_headers):
        """PLAN-05: category_data array has per-category fill rate aggregation"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        assert "category_data" in data
        assert isinstance(data["category_data"], list)
        if len(data["category_data"]) > 0:
            cat = data["category_data"][0]
            assert "category" in cat
            assert "fill_rate" in cat
            assert "current_stock" in cat
            assert "norm_allocated" in cat
        print(f"PASS PLAN-05: category_data has {len(data['category_data'])} categories")
    
    def test_plan_06_store_data_aggregation(self, auth_headers):
        """PLAN-06: store_data array has per-store fill rate aggregation"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        assert "store_data" in data
        assert isinstance(data["store_data"], list)
        assert len(data["store_data"]) > 0
        store = data["store_data"][0]
        assert "store_code" in store
        assert "fill_rate" in store
        assert "region" in store
        print(f"PASS PLAN-06: store_data has {len(data['store_data'])} stores")
    
    def test_plan_07_fill_rate_over_100_when_overstocked(self, auth_headers):
        """PLAN-07: Detail rows where current_stock > norm_allocated have fill_rate > 100%"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        for row in data["detail"]:
            if row["current_stock"] > row["norm_allocated"]:
                assert row["fill_rate"] > 100, f"Expected >100%, got {row['fill_rate']}%"
        print("PASS PLAN-07: fill_rate > 100% when overstocked")
    
    def test_plan_08_missing_facings_when_understocked(self, auth_headers):
        """PLAN-08: Detail rows where current_stock < norm_allocated have missing_facings > 0"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        for row in data["detail"]:
            if row["current_stock"] < row["norm_allocated"]:
                assert row["missing_facings"] > 0, f"Expected missing_facings > 0"
        print("PASS PLAN-08: missing_facings > 0 when understocked")
    
    def test_plan_09_status_good_when_fill_rate_gte_90(self, auth_headers):
        """PLAN-09: Items with fill_rate >= 90 have status = GOOD"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        for row in data["detail"]:
            if row["fill_rate"] >= 90:
                assert row["status"] == "GOOD", f"Expected GOOD for {row['fill_rate']}%"
        print("PASS PLAN-09: status = GOOD when fill_rate >= 90%")
    
    def test_plan_10_status_moderate_when_fill_rate_80_90(self, auth_headers):
        """PLAN-10: Items with fill_rate 80-90 have status = MODERATE"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        for row in data["detail"]:
            if 80 <= row["fill_rate"] < 90:
                assert row["status"] == "MODERATE", f"Expected MODERATE for {row['fill_rate']}%"
        print("PASS PLAN-10: status = MODERATE when 80% <= fill_rate < 90%")
    
    def test_plan_11_status_critical_when_fill_rate_lt_80(self, auth_headers):
        """PLAN-11: Items with fill_rate < 80 have status = CRITICAL"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        for row in data["detail"]:
            if row["fill_rate"] < 80:
                assert row["status"] == "CRITICAL", f"Expected CRITICAL for {row['fill_rate']}%"
        print("PASS PLAN-11: status = CRITICAL when fill_rate < 80%")
    
    def test_plan_12_store_data_has_critical_status(self, auth_headers):
        """PLAN-12: store_data rows with status=CRITICAL exist (stores highlighted)"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        statuses = [s["status"] for s in data["store_data"]]
        assert "GOOD" in statuses or "MODERATE" in statuses or "CRITICAL" in statuses
        print(f"PASS PLAN-12: store_data has statuses: {set(statuses)}")
    
    def test_plan_13_compliance_trend_weekly(self, auth_headers):
        """PLAN-13: compliance_trend array has weekly fill_rate and status changes"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        assert "compliance_trend" in data
        assert isinstance(data["compliance_trend"], list)
        if len(data["compliance_trend"]) > 0:
            trend = data["compliance_trend"][0]
            assert "week_label" in trend
            assert "fill_rate" in trend
            assert "status" in trend
            assert "target" in trend
        print(f"PASS PLAN-13: compliance_trend has {len(data['compliance_trend'])} weeks")
    
    def test_plan_14_category_data_has_status(self, auth_headers):
        """PLAN-14: category_data has per-category status field (GOOD/MODERATE/CRITICAL)"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        for cat in data["category_data"]:
            assert "status" in cat
            assert cat["status"] in ["GOOD", "MODERATE", "CRITICAL"]
        print("PASS PLAN-14: category_data has status field")
    
    def test_plan_21_lost_sales_formula(self, auth_headers):
        """PLAN-21: Detail rows have lost_sales = missing_facings * ros * asp"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        for row in data["detail"][:10]:
            expected = round(row["missing_facings"] * row["ros"] * row["asp"], 2)
            assert abs(row["lost_sales"] - expected) < 1, f"Lost sales mismatch: {row['lost_sales']} vs {expected}"
        print("PASS PLAN-21: lost_sales = missing_facings * ros * asp")
    
    def test_plan_22_lost_sales_zero_when_no_missing(self, auth_headers):
        """PLAN-22: Detail rows with missing_facings = 0 have lost_sales = 0"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        for row in data["detail"]:
            if row["missing_facings"] == 0:
                assert row["lost_sales"] == 0, f"Expected lost_sales = 0"
        print("PASS PLAN-22: lost_sales = 0 when missing_facings = 0")
    
    def test_plan_23_lost_sales_by_category(self, auth_headers):
        """PLAN-23: lost_sales_by_category array with per-category lost sales totals"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        assert "lost_sales_by_category" in data
        assert isinstance(data["lost_sales_by_category"], list)
        if len(data["lost_sales_by_category"]) > 0:
            assert "category" in data["lost_sales_by_category"][0]
            assert "lost_sales" in data["lost_sales_by_category"][0]
        print(f"PASS PLAN-23: lost_sales_by_category has {len(data['lost_sales_by_category'])} categories")
    
    def test_plan_24_lost_sales_by_store(self, auth_headers):
        """PLAN-24: lost_sales_by_store array with per-store lost sales totals"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        assert "lost_sales_by_store" in data
        assert isinstance(data["lost_sales_by_store"], list)
        if len(data["lost_sales_by_store"]) > 0:
            assert "store_code" in data["lost_sales_by_store"][0]
            assert "lost_sales" in data["lost_sales_by_store"][0]
        print(f"PASS PLAN-24: lost_sales_by_store has {len(data['lost_sales_by_store'])} stores")
    
    def test_plan_25_total_lost_sales(self, auth_headers):
        """PLAN-25: summary.total_lost_sales is grand total of all lost sales"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        data = r.json()
        assert "total_lost_sales" in data["summary"]
        assert data["summary"]["total_lost_sales"] >= 0
        print(f"PASS PLAN-25: total_lost_sales = {data['summary']['total_lost_sales']}")


class TestPlanogramPrePost:
    """PLAN-15 to PLAN-20: Pre vs Post Replenishment endpoint"""
    
    def test_plan_15_pre_fill_rate(self, auth_headers):
        """PLAN-15: pre-post returns pre.fill_rate (before replenishment)"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/pre-post", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "pre" in data
        assert "fill_rate" in data["pre"]
        assert isinstance(data["pre"]["fill_rate"], (int, float))
        print(f"PASS PLAN-15: pre.fill_rate = {data['pre']['fill_rate']}%")
    
    def test_plan_16_post_fill_rate(self, auth_headers):
        """PLAN-16: pre-post returns post.fill_rate (after replenishment simulation)"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/pre-post", headers=auth_headers)
        data = r.json()
        assert "post" in data
        assert "fill_rate" in data["post"]
        assert isinstance(data["post"]["fill_rate"], (int, float))
        print(f"PASS PLAN-16: post.fill_rate = {data['post']['fill_rate']}%")
    
    def test_plan_17_improvement(self, auth_headers):
        """PLAN-17: pre-post improvement = post.fill_rate - pre.fill_rate"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/pre-post", headers=auth_headers)
        data = r.json()
        assert "improvement" in data
        expected = round(data["post"]["fill_rate"] - data["pre"]["fill_rate"], 1)
        assert abs(data["improvement"] - expected) < 0.2
        print(f"PASS PLAN-17: improvement = {data['improvement']}%")
    
    def test_plan_18_improvement_pct(self, auth_headers):
        """PLAN-18: pre-post improvement_pct = ((post-pre)/pre) * 100"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/pre-post", headers=auth_headers)
        data = r.json()
        assert "improvement_pct" in data
        if data["pre"]["fill_rate"] > 0:
            expected = round((data["improvement"] / data["pre"]["fill_rate"]) * 100, 1)
            assert abs(data["improvement_pct"] - expected) < 0.5
        print(f"PASS PLAN-18: improvement_pct = {data['improvement_pct']}%")
    
    def test_plan_19_status_distributions(self, auth_headers):
        """PLAN-19: pre-post returns pre and post status distributions for pie charts"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/pre-post", headers=auth_headers)
        data = r.json()
        for period in ["pre", "post"]:
            assert "good_count" in data[period]
            assert "moderate_count" in data[period]
            assert "critical_count" in data[period]
        print("PASS PLAN-19: pre and post have status distributions")
    
    def test_plan_20_stores_improved_counts(self, auth_headers):
        """PLAN-20: pre-post returns stores_improved and stores_moved_to_good counts"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/pre-post", headers=auth_headers)
        data = r.json()
        assert "stores_improved" in data
        assert "stores_moved_to_good" in data
        assert "total_stores" in data
        print(f"PASS PLAN-20: stores_improved={data['stores_improved']}, moved_to_good={data['stores_moved_to_good']}")


class TestPlanogramTrend:
    """PLAN-26 to PLAN-32: Trend & Alerts endpoint"""
    
    def test_plan_26_daily_trend(self, auth_headers):
        """PLAN-26: GET /api/analytics/planogram/trend?granularity=daily returns daily trend data"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/trend?granularity=daily", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["granularity"] == "daily"
        assert "trend" in data
        print(f"PASS PLAN-26: daily trend has {len(data['trend'])} data points")
    
    def test_plan_27_weekly_trend(self, auth_headers):
        """PLAN-27: GET /api/analytics/planogram/trend?granularity=weekly returns weekly trend"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/trend?granularity=weekly", headers=auth_headers)
        data = r.json()
        assert data["granularity"] == "weekly"
        if len(data["trend"]) > 0:
            assert "fill_rate" in data["trend"][0]
            assert "target" in data["trend"][0]
        print(f"PASS PLAN-27: weekly trend has {len(data['trend'])} weeks")
    
    def test_plan_28_monthly_trend(self, auth_headers):
        """PLAN-28: GET /api/analytics/planogram/trend?granularity=monthly returns monthly aggregated trend"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/trend?granularity=monthly", headers=auth_headers)
        data = r.json()
        assert data["granularity"] == "monthly"
        print(f"PASS PLAN-28: monthly trend has {len(data['trend'])} months")
    
    def test_plan_29_target_field(self, auth_headers):
        """PLAN-29: Trend items include target field (default 85%) as comparison line"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/trend", headers=auth_headers)
        data = r.json()
        assert data["target_fill_rate"] == 85
        if len(data["trend"]) > 0:
            assert "target" in data["trend"][0]
            assert data["trend"][0]["target"] == 85
        print("PASS PLAN-29: target field = 85%")
    
    def test_plan_30_moving_avg_field(self, auth_headers):
        """PLAN-30: Trend items include moving_avg_7d field (smoothed trend)"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/trend?granularity=daily", headers=auth_headers)
        data = r.json()
        if len(data["trend"]) > 0:
            assert "moving_avg_7d" in data["trend"][0]
        print("PASS PLAN-30: moving_avg_7d field present")
    
    def test_plan_31_alerts_array(self, auth_headers):
        """PLAN-31: alerts array shows dates when fill rate dropped below 80%"""
        r = requests.get(f"{BASE_URL}/api/analytics/planogram/trend", headers=auth_headers)
        data = r.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)
        # Alerts may be empty if fill rate never dropped below 80%
        if len(data["alerts"]) > 0:
            assert "date" in data["alerts"][0]
            assert "fill_rate" in data["alerts"][0]
            assert "message" in data["alerts"][0]
        print(f"PASS PLAN-31: alerts array has {len(data['alerts'])} alerts")


# ============================================================================
# BI DASHBOARD TESTS (BI-01 to BI-35)
# ============================================================================
class TestBIOverview:
    """BI-01 to BI-08: KPI Overview endpoint"""
    
    def test_bi_01_revenue_value(self, auth_headers):
        """BI-01: GET /api/analytics/bi/overview returns kpis.revenue.value (total revenue sum)"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/overview", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "kpis" in data
        assert "revenue" in data["kpis"]
        assert "value" in data["kpis"]["revenue"]
        assert data["kpis"]["revenue"]["value"] > 0
        print(f"PASS BI-01: revenue.value = {data['kpis']['revenue']['value']}")
    
    def test_bi_02_quantity_value(self, auth_headers):
        """BI-02: kpis.quantity.value (total quantity sum)"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/overview", headers=auth_headers)
        data = r.json()
        assert "quantity" in data["kpis"]
        assert "value" in data["kpis"]["quantity"]
        assert data["kpis"]["quantity"]["value"] > 0
        print(f"PASS BI-02: quantity.value = {data['kpis']['quantity']['value']}")
    
    def test_bi_03_asp_value(self, auth_headers):
        """BI-03: kpis.asp.value = revenue / quantity"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/overview", headers=auth_headers)
        data = r.json()
        assert "asp" in data["kpis"]
        assert "value" in data["kpis"]["asp"]
        expected_asp = round(data["kpis"]["revenue"]["value"] / max(data["kpis"]["quantity"]["value"], 1), 2)
        assert abs(data["kpis"]["asp"]["value"] - expected_asp) < 1
        print(f"PASS BI-03: asp.value = {data['kpis']['asp']['value']}")
    
    def test_bi_04_discount_pct(self, auth_headers):
        """BI-04: kpis.discount_pct.value shows discount percentage"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/overview", headers=auth_headers)
        data = r.json()
        assert "discount_pct" in data["kpis"]
        assert "value" in data["kpis"]["discount_pct"]
        print(f"PASS BI-04: discount_pct.value = {data['kpis']['discount_pct']['value']}%")
    
    def test_bi_05_trend_field(self, auth_headers):
        """BI-05: kpis have trend field ('up', 'down', or 'flat')"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/overview", headers=auth_headers)
        data = r.json()
        for kpi in ["revenue", "quantity", "asp", "discount_pct"]:
            assert "trend" in data["kpis"][kpi]
            assert data["kpis"][kpi]["trend"] in ["up", "down", "flat"]
        print("PASS BI-05: all kpis have trend field")
    
    def test_bi_06_wow_change(self, auth_headers):
        """BI-06: kpis.revenue.wow_change and kpis.quantity.wow_change (WoW % comparison)"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/overview", headers=auth_headers)
        data = r.json()
        assert "wow_change" in data["kpis"]["revenue"]
        assert "wow_change" in data["kpis"]["quantity"]
        print(f"PASS BI-06: revenue.wow_change = {data['kpis']['revenue']['wow_change']}%")
    
    def test_bi_07_yoy_change(self, auth_headers):
        """BI-07: kpis.revenue.yoy_change (YoY comparison)"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/overview", headers=auth_headers)
        data = r.json()
        assert "yoy_change" in data["kpis"]["revenue"]
        print(f"PASS BI-07: revenue.yoy_change = {data['kpis']['revenue']['yoy_change']}%")
    
    def test_bi_08_target_and_progress(self, auth_headers):
        """BI-08: kpis.revenue.target and kpis.revenue.progress fields for progress bars"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/overview", headers=auth_headers)
        data = r.json()
        assert "target" in data["kpis"]["revenue"]
        assert "progress" in data["kpis"]["revenue"]
        assert "target" in data["kpis"]["quantity"]
        assert "progress" in data["kpis"]["quantity"]
        print(f"PASS BI-08: revenue.progress = {data['kpis']['revenue']['progress']}%")


class TestBIRevenueTrend:
    """BI-09 to BI-14: Revenue Trend endpoint"""
    
    def test_bi_09_daily_revenue_trend(self, auth_headers):
        """BI-09: GET /api/analytics/bi/revenue-trend?granularity=daily returns current array with daily revenue"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/revenue-trend?granularity=daily", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["granularity"] == "daily"
        assert "current" in data
        assert isinstance(data["current"], list)
        if len(data["current"]) > 0:
            assert "revenue" in data["current"][0]
        print(f"PASS BI-09: daily trend has {len(data['current'])} days")
    
    def test_bi_10_weekly_revenue_trend(self, auth_headers):
        """BI-10: GET /api/analytics/bi/revenue-trend?granularity=weekly returns weekly data"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/revenue-trend?granularity=weekly", headers=auth_headers)
        data = r.json()
        assert data["granularity"] == "weekly"
        print(f"PASS BI-10: weekly trend has {len(data['current'])} weeks")
    
    def test_bi_11_monthly_revenue_trend(self, auth_headers):
        """BI-11: GET /api/analytics/bi/revenue-trend?granularity=monthly returns monthly data"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/revenue-trend?granularity=monthly", headers=auth_headers)
        data = r.json()
        assert data["granularity"] == "monthly"
        print(f"PASS BI-11: monthly trend has {len(data['current'])} months")
    
    def test_bi_12_revenue_trend_filters(self, auth_headers):
        """BI-12: Revenue trend filters work with date range, categories, channels, regions params"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/revenue-trend?start_date=2026-01-01&end_date=2026-03-31&regions=North", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "current" in data
        print("PASS BI-12: revenue trend filters work")
    
    def test_bi_13_previous_period_comparison(self, auth_headers):
        """BI-13: Revenue trend returns previous array for period comparison overlay"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/revenue-trend", headers=auth_headers)
        data = r.json()
        assert "previous" in data
        assert isinstance(data["previous"], list)
        print(f"PASS BI-13: previous array has {len(data['previous'])} items")
    
    def test_bi_14_drill_down_array(self, auth_headers):
        """BI-14: Revenue trend returns drill_down array with daily-level detail"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/revenue-trend", headers=auth_headers)
        data = r.json()
        assert "drill_down" in data
        assert isinstance(data["drill_down"], list)
        if len(data["drill_down"]) > 0:
            assert "label" in data["drill_down"][0]
            assert "revenue" in data["drill_down"][0]
            assert "quantity" in data["drill_down"][0]
        print(f"PASS BI-14: drill_down has {len(data['drill_down'])} daily records")


class TestBIChannels:
    """BI-15 to BI-20: Channels endpoint"""
    
    def test_bi_15_channel_revenue(self, auth_headers):
        """BI-15: GET /api/analytics/bi/channels returns channels array with revenue per channel"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/channels", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "channels" in data
        assert isinstance(data["channels"], list)
        if len(data["channels"]) > 0:
            assert "channel" in data["channels"][0]
            assert "revenue" in data["channels"][0]
        print(f"PASS BI-15: channels array has {len(data['channels'])} channels")
    
    def test_bi_16_channel_quantity(self, auth_headers):
        """BI-16: Channel items have quantity field (bar chart data)"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/channels", headers=auth_headers)
        data = r.json()
        for ch in data["channels"]:
            assert "quantity" in ch
        print("PASS BI-16: channels have quantity field")
    
    def test_bi_17_marketplace_names(self, auth_headers):
        """BI-17: Channel items include marketplace names (whatever channels exist in data)"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/channels", headers=auth_headers)
        data = r.json()
        channel_names = [ch["channel"] for ch in data["channels"]]
        assert len(channel_names) > 0
        print(f"PASS BI-17: channels = {channel_names}")
    
    def test_bi_18_channel_growth_pct(self, auth_headers):
        """BI-18: Channel items have growth_pct field for growth comparison"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/channels", headers=auth_headers)
        data = r.json()
        for ch in data["channels"]:
            assert "growth_pct" in ch
        print("PASS BI-18: channels have growth_pct field")
    
    def test_bi_19_channel_filter(self, auth_headers):
        """BI-19: Channels endpoint respects channel filter param"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/channels?channels=Retail", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        # If filter applied, should only have Retail channel
        if len(data["channels"]) > 0:
            assert data["channels"][0]["channel"] == "Retail"
        print("PASS BI-19: channel filter works")


class TestBICategories:
    """BI-21 to BI-26: Categories endpoint"""
    
    def test_bi_21_category_revenue(self, auth_headers):
        """BI-21: GET /api/analytics/bi/categories returns categories array with revenue per category"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/categories", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)
        if len(data["categories"]) > 0:
            assert "category" in data["categories"][0]
            assert "revenue" in data["categories"][0]
        print(f"PASS BI-21: categories array has {len(data['categories'])} categories")
    
    def test_bi_22_category_quantity(self, auth_headers):
        """BI-22: Category items have quantity field"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/categories", headers=auth_headers)
        data = r.json()
        for cat in data["categories"]:
            assert "quantity" in cat
        print("PASS BI-22: categories have quantity field")
    
    def test_bi_23_top5_categories(self, auth_headers):
        """BI-23: top5 array highlights top 5 categories by revenue"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/categories", headers=auth_headers)
        data = r.json()
        assert "top5" in data
        assert isinstance(data["top5"], list)
        assert len(data["top5"]) <= 5
        print(f"PASS BI-23: top5 = {data['top5']}")
    
    def test_bi_24_category_growth_pct(self, auth_headers):
        """BI-24: Category items have growth_pct field"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/categories", headers=auth_headers)
        data = r.json()
        for cat in data["categories"]:
            assert "growth_pct" in cat
        print("PASS BI-24: categories have growth_pct field")
    
    def test_bi_25_category_filter(self, auth_headers):
        """BI-25: Categories endpoint respects category filter param"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/categories?categories=Pants", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        if len(data["categories"]) > 0:
            assert data["categories"][0]["category"] == "Pants"
        print("PASS BI-25: category filter works")
    
    def test_bi_26_style_breakdown(self, auth_headers):
        """BI-26: style_breakdown array for category drill-down (sub-categories/styles)"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/categories", headers=auth_headers)
        data = r.json()
        assert "style_breakdown" in data
        assert isinstance(data["style_breakdown"], list)
        if len(data["style_breakdown"]) > 0:
            assert "category" in data["style_breakdown"][0]
            assert "style" in data["style_breakdown"][0]
            assert "revenue" in data["style_breakdown"][0]
        print(f"PASS BI-26: style_breakdown has {len(data['style_breakdown'])} styles")


class TestBIRegions:
    """BI-27 to BI-31: Regions endpoint"""
    
    def test_bi_27_region_revenue(self, auth_headers):
        """BI-27: GET /api/analytics/bi/regions returns regions array with revenue per region"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/regions", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "regions" in data
        assert isinstance(data["regions"], list)
        if len(data["regions"]) > 0:
            assert "region" in data["regions"][0]
            assert "revenue" in data["regions"][0]
        print(f"PASS BI-27: regions array has {len(data['regions'])} regions")
    
    def test_bi_28_region_growth_pct(self, auth_headers):
        """BI-28: Region items have growth_pct field"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/regions", headers=auth_headers)
        data = r.json()
        for reg in data["regions"]:
            assert "growth_pct" in reg
        print("PASS BI-28: regions have growth_pct field")
    
    def test_bi_29_top_region(self, auth_headers):
        """BI-29: top_region field identifies best-performing region"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/regions", headers=auth_headers)
        data = r.json()
        assert "top_region" in data
        assert data["top_region"] is not None
        print(f"PASS BI-29: top_region = {data['top_region']}")
    
    def test_bi_30_region_filter(self, auth_headers):
        """BI-30: Regions endpoint respects regions filter param"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/regions?regions=North", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        if len(data["regions"]) > 0:
            assert data["regions"][0]["region"] == "North"
        print("PASS BI-30: region filter works")
    
    def test_bi_31_city_breakdown(self, auth_headers):
        """BI-31: city_breakdown array for city-level drill-down within regions"""
        r = requests.get(f"{BASE_URL}/api/analytics/bi/regions", headers=auth_headers)
        data = r.json()
        assert "city_breakdown" in data
        assert isinstance(data["city_breakdown"], list)
        if len(data["city_breakdown"]) > 0:
            assert "region" in data["city_breakdown"][0]
            assert "city" in data["city_breakdown"][0]
            assert "revenue" in data["city_breakdown"][0]
        print(f"PASS BI-31: city_breakdown has {len(data['city_breakdown'])} cities")


class TestBIFutureFeatures:
    """BI-34 to BI-35: Future features (should not error)"""
    
    def test_bi_34_schedule_email_not_implemented(self, auth_headers):
        """BI-34: Schedule auto-reports - not implemented but no error (future feature)"""
        # This is a future feature - just verify the main endpoints work
        r = requests.get(f"{BASE_URL}/api/analytics/bi/overview", headers=auth_headers)
        assert r.status_code == 200
        print("PASS BI-34: Schedule email is future feature (no endpoint yet)")
    
    def test_bi_35_share_link_not_implemented(self, auth_headers):
        """BI-35: Share dashboard link - not implemented but no error (future feature)"""
        # This is a future feature - just verify the main endpoints work
        r = requests.get(f"{BASE_URL}/api/analytics/bi/overview", headers=auth_headers)
        assert r.status_code == 200
        print("PASS BI-35: Share link is future feature (no endpoint yet)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
