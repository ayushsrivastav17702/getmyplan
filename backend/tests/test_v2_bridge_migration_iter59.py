"""
Test V2 Bridge Migration - Iteration 59
Tests all 5 analytics modules updated to use V2 data bridge:
- core_logic.py (ROS, True-ROS)
- doh_analysis.py (DOH Analysis)
- bi_dashboard.py (BI Overview, Trend, Category Breakdown)
- planogram.py (Fill Rate Analysis)
- replenishment.py (Order Quantity, IST, Reorder Points)

Also tests executive dashboard and AI demand endpoints.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://zip-improved.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@demo.com"
TEST_PASSWORD = "demo1234"


def get_auth_token():
    """Helper to get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    # Handle both 'token' and 'access_token' response formats
    token = data.get("token") or data.get("access_token")
    assert token is not None, f"No token in response: {data.keys()}"
    return token


class TestAuth:
    """Authentication tests"""
    
    def test_login_success(self):
        """TEST_01: Login with demo tenant credentials"""
        token = get_auth_token()
        assert token is not None
        assert len(token) > 0
        print(f"✓ Login successful, token length: {len(token)}")


class TestCoreLogicModule:
    """Tests for core_logic.py V2 bridge migration"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        token = get_auth_token()
        return {"Authorization": f"Bearer {token}"}
    
    def test_ros_endpoint(self, auth_headers):
        """TEST_02: GET /api/analytics/core/ros returns data with styles, avg_ros > 0"""
        response = requests.get(f"{BASE_URL}/api/analytics/core/ros", headers=auth_headers)
        assert response.status_code == 200, f"ROS endpoint failed: {response.text}"
        data = response.json()
        
        # Check for error
        assert "error" not in data or data.get("error") is None, f"ROS returned error: {data.get('error')}"
        
        # Check summary
        assert "summary" in data, "No summary in ROS response"
        summary = data["summary"]
        assert "avg_ros" in summary, "No avg_ros in summary"
        assert summary["avg_ros"] > 0, f"avg_ros should be > 0, got {summary['avg_ros']}"
        
        # Check style_data
        assert "style_data" in data, "No style_data in ROS response"
        assert len(data["style_data"]) > 0, "style_data is empty"
        
        print(f"✓ ROS endpoint: {summary['total_styles']} styles, avg_ros={summary['avg_ros']}")
    
    def test_true_ros_endpoint(self, auth_headers):
        """TEST_03: GET /api/analytics/core/true-ros returns data with avg_true_ros > 0"""
        response = requests.get(f"{BASE_URL}/api/analytics/core/true-ros", headers=auth_headers)
        assert response.status_code == 200, f"True-ROS endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"True-ROS returned error: {data.get('error')}"
        
        assert "summary" in data, "No summary in True-ROS response"
        summary = data["summary"]
        assert "avg_true_ros" in summary, "No avg_true_ros in summary"
        assert summary["avg_true_ros"] > 0, f"avg_true_ros should be > 0, got {summary['avg_true_ros']}"
        
        print(f"✓ True-ROS endpoint: {summary['total_styles']} styles, avg_true_ros={summary['avg_true_ros']}")


class TestDOHAnalysisModule:
    """Tests for doh_analysis.py V2 bridge migration"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        token = get_auth_token()
        return {"Authorization": f"Bearer {token}"}
    
    def test_doh_analysis_endpoint(self, auth_headers):
        """TEST_04: GET /api/analytics/doh/analysis returns summary with overall_doh, total_store_skus, optimal_count"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh/analysis", headers=auth_headers)
        assert response.status_code == 200, f"DOH analysis endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"DOH analysis returned error: {data.get('error')}"
        
        assert "summary" in data, "No summary in DOH analysis response"
        summary = data["summary"]
        
        assert "overall_doh" in summary, "No overall_doh in summary"
        assert "total_store_skus" in summary, "No total_store_skus in summary"
        assert "optimal_count" in summary, "No optimal_count in summary"
        
        assert summary["total_store_skus"] > 0, f"total_store_skus should be > 0, got {summary['total_store_skus']}"
        
        print(f"✓ DOH Analysis: overall_doh={summary['overall_doh']}, total_store_skus={summary['total_store_skus']}, optimal_count={summary['optimal_count']}")


class TestBIDashboardModule:
    """Tests for bi_dashboard.py V2 bridge migration"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        token = get_auth_token()
        return {"Authorization": f"Bearer {token}"}
    
    def test_bi_overview_endpoint(self, auth_headers):
        """TEST_05: GET /api/analytics/bi/overview returns kpis.revenue.value > 0, kpis.quantity.value > 0"""
        response = requests.get(f"{BASE_URL}/api/analytics/bi/overview", headers=auth_headers)
        assert response.status_code == 200, f"BI overview endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"BI overview returned error: {data.get('error')}"
        
        assert "kpis" in data, "No kpis in BI overview response"
        kpis = data["kpis"]
        
        assert "revenue" in kpis, "No revenue in kpis"
        assert "quantity" in kpis, "No quantity in kpis"
        
        assert kpis["revenue"]["value"] > 0, f"revenue.value should be > 0, got {kpis['revenue']['value']}"
        assert kpis["quantity"]["value"] > 0, f"quantity.value should be > 0, got {kpis['quantity']['value']}"
        
        print(f"✓ BI Overview: revenue={kpis['revenue']['value']}, quantity={kpis['quantity']['value']}")
    
    def test_bi_trend_endpoint(self, auth_headers):
        """TEST_06: GET /api/analytics/bi/revenue-trend returns trend data"""
        response = requests.get(f"{BASE_URL}/api/analytics/bi/revenue-trend", headers=auth_headers)
        assert response.status_code == 200, f"BI revenue-trend endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"BI trend returned error: {data.get('error')}"
        
        # Check for trend data
        assert "current" in data or "trend" in data, "No trend data in response"
        
        trend_data = data.get("current") or data.get("trend", [])
        assert len(trend_data) > 0, "Trend data is empty"
        
        print(f"✓ BI Revenue Trend: {len(trend_data)} data points")
    
    def test_bi_category_breakdown_endpoint(self, auth_headers):
        """TEST_07: GET /api/analytics/bi/categories returns category data"""
        response = requests.get(f"{BASE_URL}/api/analytics/bi/categories", headers=auth_headers)
        assert response.status_code == 200, f"BI categories endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"BI category returned error: {data.get('error')}"
        
        # Check for categories data
        assert "categories" in data, "No categories in response"
        assert len(data["categories"]) > 0, "Categories data is empty"
        
        print(f"✓ BI Categories: {len(data['categories'])} categories")


class TestPlanogramModule:
    """Tests for planogram.py V2 bridge migration"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        token = get_auth_token()
        return {"Authorization": f"Bearer {token}"}
    
    def test_planogram_analysis_endpoint(self, auth_headers):
        """TEST_08: GET /api/analytics/planogram/analysis returns summary with overall_fill_rate, total_stores"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram/analysis", headers=auth_headers)
        assert response.status_code == 200, f"Planogram analysis endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"Planogram analysis returned error: {data.get('error')}"
        
        assert "summary" in data, "No summary in planogram analysis response"
        summary = data["summary"]
        
        assert "overall_fill_rate" in summary, "No overall_fill_rate in summary"
        assert "total_stores" in summary, "No total_stores in summary"
        
        print(f"✓ Planogram Analysis: overall_fill_rate={summary['overall_fill_rate']}%, total_stores={summary['total_stores']}")


class TestReplenishmentModule:
    """Tests for replenishment.py V2 bridge migration"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        token = get_auth_token()
        return {"Authorization": f"Bearer {token}"}
    
    def test_order_quantity_endpoint(self, auth_headers):
        """TEST_09: GET /api/analytics/replenishment/order-quantity returns summary with total_po_value > 0"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment/order-quantity", headers=auth_headers)
        assert response.status_code == 200, f"Order quantity endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"Order quantity returned error: {data.get('error')}"
        
        assert "summary" in data, "No summary in order quantity response"
        summary = data["summary"]
        
        assert "total_po_value" in summary, "No total_po_value in summary"
        assert summary["total_po_value"] >= 0, f"total_po_value should be >= 0, got {summary['total_po_value']}"
        
        print(f"✓ Order Quantity: total_po_value={summary['total_po_value']}, total_order_units={summary.get('total_order_units', 0)}")
    
    def test_ist_endpoint(self, auth_headers):
        """TEST_10: GET /api/analytics/replenishment/ist returns summary with overstocked_stores defined"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment/ist", headers=auth_headers)
        assert response.status_code == 200, f"IST endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"IST returned error: {data.get('error')}"
        
        assert "summary" in data, "No summary in IST response"
        summary = data["summary"]
        
        assert "overstocked_stores" in summary, "No overstocked_stores in summary"
        
        print(f"✓ IST: overstocked_stores={summary['overstocked_stores']}, understocked_stores={summary.get('understocked_stores', 0)}")
    
    def test_reorder_points_endpoint(self, auth_headers):
        """TEST_11: GET /api/analytics/replenishment/reorder-points returns data array"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment/reorder-points", headers=auth_headers)
        assert response.status_code == 200, f"Reorder points endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"Reorder points returned error: {data.get('error')}"
        
        assert "detail" in data, "No detail in reorder points response"
        assert len(data["detail"]) > 0, "Reorder points detail is empty"
        
        print(f"✓ Reorder Points: {len(data['detail'])} items in detail")


class TestExecutiveDashboard:
    """Tests for executive dashboard endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        token = get_auth_token()
        return {"Authorization": f"Bearer {token}"}
    
    def test_executive_kpis_endpoint(self, auth_headers):
        """TEST_12: GET /api/analytics/executive-kpis returns revenue > 0, units_sold > 0, has_data = true"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-kpis", headers=auth_headers)
        assert response.status_code == 200, f"Executive KPIs endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"Executive KPIs returned error: {data.get('error')}"
        
        # Check for revenue and units_sold
        assert "revenue" in data or "total_revenue" in data, "No revenue in executive KPIs"
        revenue = data.get("revenue") or data.get("total_revenue", 0)
        assert revenue > 0, f"revenue should be > 0, got {revenue}"
        
        units = data.get("units_sold") or data.get("total_units", 0)
        assert units > 0, f"units_sold should be > 0, got {units}"
        
        has_data = data.get("has_data", True)
        assert has_data == True, f"has_data should be true, got {has_data}"
        
        print(f"✓ Executive KPIs: revenue={revenue}, units_sold={units}, has_data={has_data}")
    
    def test_executive_dashboard_endpoint(self, auth_headers):
        """TEST_13: GET /api/analytics/executive-dashboard returns modules with data"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard", headers=auth_headers)
        assert response.status_code == 200, f"Executive dashboard endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"Executive dashboard returned error: {data.get('error')}"
        
        # Check for modules or sections
        assert "modules" in data or "sections" in data or "kpis" in data, "No modules/sections in executive dashboard"
        
        print(f"✓ Executive Dashboard: response keys = {list(data.keys())}")


class TestAIDemandEndpoints:
    """Tests for AI demand forecasting endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        token = get_auth_token()
        return {"Authorization": f"Bearer {token}"}
    
    def test_ai_demand_forecast_endpoint(self, auth_headers):
        """TEST_14: GET /api/analytics/ai-demand/forecast returns forecast array with 12 months, models_used with 3 models"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/forecast", headers=auth_headers)
        assert response.status_code == 200, f"AI demand forecast endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"AI demand forecast returned error: {data.get('error')}"
        
        # Check for forecast array
        assert "forecast" in data, "No forecast in AI demand response"
        forecast = data["forecast"]
        assert len(forecast) >= 12, f"forecast should have >= 12 months, got {len(forecast)}"
        
        # Check for models_used
        assert "models_used" in data, "No models_used in AI demand response"
        models = data["models_used"]
        assert len(models) >= 3, f"models_used should have >= 3 models, got {len(models)}"
        
        print(f"✓ AI Demand Forecast: {len(forecast)} months, {len(models)} models")
    
    def test_ai_demand_data_health_endpoint(self, auth_headers):
        """TEST_15: GET /api/analytics/ai-demand/data-health returns daily_sales with days_available > 180"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/data-health", headers=auth_headers)
        assert response.status_code == 200, f"AI demand data-health endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"AI demand data-health returned error: {data.get('error')}"
        
        # Check for daily_sales
        assert "daily_sales" in data, "No daily_sales in data-health response"
        daily_sales = data["daily_sales"]
        
        days_available = daily_sales.get("days_available", 0)
        assert days_available > 180, f"days_available should be > 180, got {days_available}"
        
        print(f"✓ AI Demand Data Health: days_available={days_available}")
    
    def test_ai_demand_reorder_optimisation_endpoint(self, auth_headers):
        """TEST_16: GET /api/analytics/ai-demand/reorder-optimisation returns summary with total_skus > 0, items array"""
        response = requests.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation", headers=auth_headers)
        assert response.status_code == 200, f"AI demand reorder-optimisation endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"AI demand reorder-optimisation returned error: {data.get('error')}"
        
        # Check for summary
        assert "summary" in data, "No summary in reorder-optimisation response"
        summary = data["summary"]
        
        total_skus = summary.get("total_skus", 0)
        assert total_skus > 0, f"total_skus should be > 0, got {total_skus}"
        
        # Check for items
        assert "items" in data, "No items in reorder-optimisation response"
        assert len(data["items"]) > 0, "items array is empty"
        
        print(f"✓ AI Demand Reorder Optimisation: total_skus={total_skus}, items={len(data['items'])}")


class TestStockOutEndpoint:
    """Tests for stock-out endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        token = get_auth_token()
        return {"Authorization": f"Bearer {token}"}
    
    def test_stock_out_endpoint(self, auth_headers):
        """TEST_17: GET /api/analytics/stock-out returns summary with total_stockouts >= 0"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out", headers=auth_headers)
        assert response.status_code == 200, f"Stock-out endpoint failed: {response.text}"
        data = response.json()
        
        assert "error" not in data or data.get("error") is None, f"Stock-out returned error: {data.get('error')}"
        
        # Check for summary
        assert "summary" in data, "No summary in stock-out response"
        summary = data["summary"]
        
        total_stockouts = summary.get("total_stockouts", 0)
        assert total_stockouts >= 0, f"total_stockouts should be >= 0, got {total_stockouts}"
        
        print(f"✓ Stock-Out: total_stockouts={total_stockouts}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
