"""
Iteration 109: Backend Tests for Reporting Module APIs
- Planner Performance Leaderboard: GET /api/reports/planner-performance
- Category Health Scorecard: GET /api/reports/category-health
- ROI Dashboard: GET /api/reports/roi
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@demo.com"
TEST_PASSWORD = "demo1234"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for super admin"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestPlannerPerformanceAPI:
    """Tests for GET /api/reports/planner-performance"""
    
    def test_planner_performance_returns_200(self, auth_headers):
        """TEST_01: Endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/reports/planner-performance", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_planner_performance_has_leaderboard(self, auth_headers):
        """TEST_02: Response contains leaderboard array"""
        response = requests.get(f"{BASE_URL}/api/reports/planner-performance", headers=auth_headers)
        data = response.json()
        assert "leaderboard" in data, "Response missing 'leaderboard' key"
        assert isinstance(data["leaderboard"], list), "leaderboard should be a list"
    
    def test_planner_performance_has_totals(self, auth_headers):
        """TEST_03: Response contains total_plans and total_planners"""
        response = requests.get(f"{BASE_URL}/api/reports/planner-performance", headers=auth_headers)
        data = response.json()
        assert "total_plans" in data, "Response missing 'total_plans'"
        assert "total_planners" in data, "Response missing 'total_planners'"
        assert isinstance(data["total_plans"], int), "total_plans should be int"
        assert isinstance(data["total_planners"], int), "total_planners should be int"
    
    def test_planner_performance_leaderboard_structure(self, auth_headers):
        """TEST_04: Each leaderboard entry has required fields"""
        response = requests.get(f"{BASE_URL}/api/reports/planner-performance", headers=auth_headers)
        data = response.json()
        leaderboard = data.get("leaderboard", [])
        
        if len(leaderboard) > 0:
            entry = leaderboard[0]
            required_fields = ["rank", "email", "plans_created", "approval_rate"]
            for field in required_fields:
                assert field in entry, f"Leaderboard entry missing '{field}'"
            
            # Validate types
            assert isinstance(entry["rank"], int), "rank should be int"
            assert isinstance(entry["email"], str), "email should be string"
            assert isinstance(entry["plans_created"], int), "plans_created should be int"
            assert isinstance(entry["approval_rate"], (int, float)), "approval_rate should be numeric"
    
    def test_planner_performance_requires_auth(self):
        """TEST_05: Endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/reports/planner-performance")
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"


class TestCategoryHealthAPI:
    """Tests for GET /api/reports/category-health"""
    
    def test_category_health_returns_200(self, auth_headers):
        """TEST_06: Endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/reports/category-health", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_category_health_has_categories(self, auth_headers):
        """TEST_07: Response contains categories array"""
        response = requests.get(f"{BASE_URL}/api/reports/category-health", headers=auth_headers)
        data = response.json()
        assert "categories" in data, "Response missing 'categories' key"
        assert isinstance(data["categories"], list), "categories should be a list"
    
    def test_category_health_has_period(self, auth_headers):
        """TEST_08: Response contains period field"""
        response = requests.get(f"{BASE_URL}/api/reports/category-health", headers=auth_headers)
        data = response.json()
        assert "period" in data, "Response missing 'period'"
        assert data["period"] == "last_30_days", f"Expected 'last_30_days', got {data['period']}"
    
    def test_category_health_category_structure(self, auth_headers):
        """TEST_09: Each category has required health metrics"""
        response = requests.get(f"{BASE_URL}/api/reports/category-health", headers=auth_headers)
        data = response.json()
        categories = data.get("categories", [])
        
        if len(categories) > 0:
            cat = categories[0]
            required_fields = ["category", "stock_health", "fill_rate", "doh", "revenue_30d"]
            for field in required_fields:
                assert field in cat, f"Category entry missing '{field}'"
            
            # Validate types
            assert isinstance(cat["category"], str), "category should be string"
            assert isinstance(cat["stock_health"], (int, float)), "stock_health should be numeric"
            assert isinstance(cat["fill_rate"], (int, float)), "fill_rate should be numeric"
            assert isinstance(cat["doh"], (int, float)), "doh should be numeric"
            assert isinstance(cat["revenue_30d"], (int, float)), "revenue_30d should be numeric"
    
    def test_category_health_requires_auth(self):
        """TEST_10: Endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/reports/category-health")
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"


class TestROIDashboardAPI:
    """Tests for GET /api/reports/roi"""
    
    def test_roi_returns_200(self, auth_headers):
        """TEST_11: Endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/reports/roi", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_roi_has_kpis(self, auth_headers):
        """TEST_12: Response contains kpis object"""
        response = requests.get(f"{BASE_URL}/api/reports/roi", headers=auth_headers)
        data = response.json()
        assert "kpis" in data, "Response missing 'kpis' key"
        assert isinstance(data["kpis"], dict), "kpis should be a dict"
    
    def test_roi_kpis_structure(self, auth_headers):
        """TEST_13: KPIs object has required fields"""
        response = requests.get(f"{BASE_URL}/api/reports/roi", headers=auth_headers)
        data = response.json()
        kpis = data.get("kpis", {})
        
        required_fields = ["total_plans", "approved_plans", "plan_approval_rate", "time_saved_hrs"]
        for field in required_fields:
            assert field in kpis, f"KPIs missing '{field}'"
        
        # Validate types
        assert isinstance(kpis["total_plans"], int), "total_plans should be int"
        assert isinstance(kpis["approved_plans"], int), "approved_plans should be int"
        assert isinstance(kpis["plan_approval_rate"], (int, float)), "plan_approval_rate should be numeric"
        assert isinstance(kpis["time_saved_hrs"], (int, float)), "time_saved_hrs should be numeric"
    
    def test_roi_has_monthly_revenue(self, auth_headers):
        """TEST_14: Response contains monthly_revenue array"""
        response = requests.get(f"{BASE_URL}/api/reports/roi", headers=auth_headers)
        data = response.json()
        assert "monthly_revenue" in data, "Response missing 'monthly_revenue'"
        assert isinstance(data["monthly_revenue"], list), "monthly_revenue should be a list"
    
    def test_roi_monthly_revenue_structure(self, auth_headers):
        """TEST_15: Monthly revenue entries have required fields"""
        response = requests.get(f"{BASE_URL}/api/reports/roi", headers=auth_headers)
        data = response.json()
        monthly = data.get("monthly_revenue", [])
        
        if len(monthly) > 0:
            entry = monthly[0]
            required_fields = ["month", "revenue", "qty", "transactions"]
            for field in required_fields:
                assert field in entry, f"Monthly revenue entry missing '{field}'"
            
            # Validate month format (YYYY-MM)
            assert len(entry["month"]) == 7, f"Month format should be YYYY-MM, got {entry['month']}"
            assert "-" in entry["month"], "Month should contain hyphen"
    
    def test_roi_requires_auth(self):
        """TEST_16: Endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/reports/roi")
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"
    
    def test_roi_additional_kpis(self, auth_headers):
        """TEST_17: KPIs has additional operational metrics"""
        response = requests.get(f"{BASE_URL}/api/reports/roi", headers=auth_headers)
        data = response.json()
        kpis = data.get("kpis", {})
        
        # Check for additional KPIs
        additional_fields = ["total_stores", "total_skus", "inventory_records"]
        for field in additional_fields:
            assert field in kpis, f"KPIs missing additional field '{field}'"


class TestReportsDataIntegrity:
    """Tests for data integrity across reports"""
    
    def test_planner_performance_data_consistency(self, auth_headers):
        """TEST_18: Leaderboard ranks are sequential starting from 1"""
        response = requests.get(f"{BASE_URL}/api/reports/planner-performance", headers=auth_headers)
        data = response.json()
        leaderboard = data.get("leaderboard", [])
        
        if len(leaderboard) > 0:
            ranks = [entry["rank"] for entry in leaderboard]
            expected_ranks = list(range(1, len(leaderboard) + 1))
            assert ranks == expected_ranks, f"Ranks not sequential: {ranks}"
    
    def test_category_health_percentages_valid(self, auth_headers):
        """TEST_19: Health percentages are within 0-100 range"""
        response = requests.get(f"{BASE_URL}/api/reports/category-health", headers=auth_headers)
        data = response.json()
        categories = data.get("categories", [])
        
        for cat in categories:
            stock_health = cat.get("stock_health", 0)
            fill_rate = cat.get("fill_rate", 0)
            assert 0 <= stock_health <= 100, f"stock_health out of range: {stock_health}"
            assert 0 <= fill_rate <= 100, f"fill_rate out of range: {fill_rate}"
    
    def test_roi_approval_rate_valid(self, auth_headers):
        """TEST_20: Plan approval rate is within 0-100 range"""
        response = requests.get(f"{BASE_URL}/api/reports/roi", headers=auth_headers)
        data = response.json()
        kpis = data.get("kpis", {})
        
        approval_rate = kpis.get("plan_approval_rate", 0)
        assert 0 <= approval_rate <= 100, f"plan_approval_rate out of range: {approval_rate}"
    
    def test_roi_approved_less_than_total(self, auth_headers):
        """TEST_21: Approved plans <= total plans"""
        response = requests.get(f"{BASE_URL}/api/reports/roi", headers=auth_headers)
        data = response.json()
        kpis = data.get("kpis", {})
        
        total = kpis.get("total_plans", 0)
        approved = kpis.get("approved_plans", 0)
        assert approved <= total, f"approved_plans ({approved}) > total_plans ({total})"
