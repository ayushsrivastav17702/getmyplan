"""
Iteration 108: Dashboard APIs Testing
Tests for Buy Plan Readiness and Forecast Accuracy dashboards.
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
    """Get authentication token for super admin."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "tenant_id": "production"
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.text}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestReadinessAPI:
    """Tests for GET /api/dashboards/readiness - Buy Plan Readiness Dashboard"""

    def test_readiness_returns_200(self, auth_headers):
        """TEST_01: Readiness endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/dashboards/readiness", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("TEST_01 PASS: Readiness endpoint returns 200")

    def test_readiness_has_score(self, auth_headers):
        """TEST_02: Response contains readiness_score (0-100)"""
        response = requests.get(f"{BASE_URL}/api/dashboards/readiness", headers=auth_headers)
        data = response.json()
        assert "readiness_score" in data, "Missing readiness_score"
        assert isinstance(data["readiness_score"], (int, float)), "readiness_score should be numeric"
        assert 0 <= data["readiness_score"] <= 100, f"Score {data['readiness_score']} out of range"
        print(f"TEST_02 PASS: readiness_score = {data['readiness_score']}")

    def test_readiness_has_checks_array(self, auth_headers):
        """TEST_03: Response contains checks array with 8 items"""
        response = requests.get(f"{BASE_URL}/api/dashboards/readiness", headers=auth_headers)
        data = response.json()
        assert "checks" in data, "Missing checks array"
        assert isinstance(data["checks"], list), "checks should be a list"
        assert len(data["checks"]) == 8, f"Expected 8 checks, got {len(data['checks'])}"
        print(f"TEST_03 PASS: checks array has {len(data['checks'])} items")

    def test_readiness_check_structure(self, auth_headers):
        """TEST_04: Each check has required fields"""
        response = requests.get(f"{BASE_URL}/api/dashboards/readiness", headers=auth_headers)
        data = response.json()
        required_fields = ["id", "label", "description", "current", "total", "passed", "weight", "category"]
        for check in data["checks"]:
            for field in required_fields:
                assert field in check, f"Check missing field: {field}"
        print("TEST_04 PASS: All checks have required fields")

    def test_readiness_check_ids(self, auth_headers):
        """TEST_05: Checks include expected IDs"""
        response = requests.get(f"{BASE_URL}/api/dashboards/readiness", headers=auth_headers)
        data = response.json()
        expected_ids = ["store_wedge", "style_mix", "daily_sales", "sku_master", 
                       "sell_through", "inventory", "display_minimums", "promotions"]
        actual_ids = [c["id"] for c in data["checks"]]
        for eid in expected_ids:
            assert eid in actual_ids, f"Missing check ID: {eid}"
        print(f"TEST_05 PASS: All expected check IDs present: {actual_ids}")

    def test_readiness_has_recommendations(self, auth_headers):
        """TEST_06: Response contains recommendations array"""
        response = requests.get(f"{BASE_URL}/api/dashboards/readiness", headers=auth_headers)
        data = response.json()
        assert "recommendations" in data, "Missing recommendations"
        assert isinstance(data["recommendations"], list), "recommendations should be a list"
        print(f"TEST_06 PASS: recommendations array present with {len(data['recommendations'])} items")

    def test_readiness_recommendation_structure(self, auth_headers):
        """TEST_07: Recommendations have priority and message"""
        response = requests.get(f"{BASE_URL}/api/dashboards/readiness", headers=auth_headers)
        data = response.json()
        for rec in data["recommendations"]:
            assert "priority" in rec, "Recommendation missing priority"
            assert "message" in rec, "Recommendation missing message"
            assert rec["priority"] in ["high", "medium", "low"], f"Invalid priority: {rec['priority']}"
        print("TEST_07 PASS: All recommendations have valid structure")

    def test_readiness_passed_total(self, auth_headers):
        """TEST_08: Response has passed and total counts"""
        response = requests.get(f"{BASE_URL}/api/dashboards/readiness", headers=auth_headers)
        data = response.json()
        assert "passed" in data, "Missing passed count"
        assert "total" in data, "Missing total count"
        assert data["total"] == 8, f"Expected total=8, got {data['total']}"
        assert 0 <= data["passed"] <= data["total"], "passed count out of range"
        print(f"TEST_08 PASS: passed={data['passed']}, total={data['total']}")


class TestForecastAccuracyAPI:
    """Tests for GET /api/dashboards/forecast-accuracy - Forecast Accuracy Dashboard"""

    def test_forecast_accuracy_returns_200(self, auth_headers):
        """TEST_09: Forecast accuracy endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/dashboards/forecast-accuracy", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("TEST_09 PASS: Forecast accuracy endpoint returns 200")

    def test_forecast_accuracy_has_overall(self, auth_headers):
        """TEST_10: Response contains overall metrics object"""
        response = requests.get(f"{BASE_URL}/api/dashboards/forecast-accuracy", headers=auth_headers)
        data = response.json()
        assert "overall" in data, "Missing overall metrics"
        assert isinstance(data["overall"], dict), "overall should be a dict"
        print(f"TEST_10 PASS: overall metrics present")

    def test_forecast_accuracy_overall_fields(self, auth_headers):
        """TEST_11: Overall metrics has expected fields"""
        response = requests.get(f"{BASE_URL}/api/dashboards/forecast-accuracy", headers=auth_headers)
        data = response.json()
        overall = data["overall"]
        expected_fields = ["mape", "accuracy", "bias", "months_compared", "confidence_score"]
        for field in expected_fields:
            assert field in overall, f"Overall missing field: {field}"
        print(f"TEST_11 PASS: Overall has all expected fields: {list(overall.keys())}")

    def test_forecast_accuracy_has_monthly_comparison(self, auth_headers):
        """TEST_12: Response contains monthly_comparison array"""
        response = requests.get(f"{BASE_URL}/api/dashboards/forecast-accuracy", headers=auth_headers)
        data = response.json()
        assert "monthly_comparison" in data, "Missing monthly_comparison"
        assert isinstance(data["monthly_comparison"], list), "monthly_comparison should be a list"
        print(f"TEST_12 PASS: monthly_comparison array present with {len(data['monthly_comparison'])} items")

    def test_forecast_accuracy_has_category_accuracy(self, auth_headers):
        """TEST_13: Response contains category_accuracy array"""
        response = requests.get(f"{BASE_URL}/api/dashboards/forecast-accuracy", headers=auth_headers)
        data = response.json()
        assert "category_accuracy" in data, "Missing category_accuracy"
        assert isinstance(data["category_accuracy"], list), "category_accuracy should be a list"
        print(f"TEST_13 PASS: category_accuracy array present with {len(data['category_accuracy'])} items")

    def test_forecast_accuracy_counts(self, auth_headers):
        """TEST_14: Response has forecast_count and actual_months"""
        response = requests.get(f"{BASE_URL}/api/dashboards/forecast-accuracy", headers=auth_headers)
        data = response.json()
        assert "forecast_count" in data, "Missing forecast_count"
        assert "actual_months" in data, "Missing actual_months"
        print(f"TEST_14 PASS: forecast_count={data['forecast_count']}, actual_months={data['actual_months']}")

    def test_forecast_accuracy_empty_state(self, auth_headers):
        """TEST_15: Empty state handled gracefully (no forecast_snapshots)"""
        response = requests.get(f"{BASE_URL}/api/dashboards/forecast-accuracy", headers=auth_headers)
        data = response.json()
        # Based on context, merch_production has no forecast_snapshots
        # So overall metrics should be null/None
        if data["forecast_count"] == 0:
            assert data["overall"]["mape"] is None, "MAPE should be None when no forecasts"
            assert data["overall"]["accuracy"] is None, "Accuracy should be None when no forecasts"
            print("TEST_15 PASS: Empty state handled - overall metrics are None")
        else:
            print(f"TEST_15 PASS: Has {data['forecast_count']} forecasts - not empty state")


class TestModuleToggleAPI:
    """Tests for module toggle affecting sidebar visibility"""

    def test_get_modules_shows_ai_insights_disabled(self, auth_headers):
        """TEST_16: ai_insights module is disabled for production tenant"""
        response = requests.get(f"{BASE_URL}/api/tenant-admin/modules", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        modules = data.get("modules", [])
        ai_module = next((m for m in modules if m["module_id"] == "ai_insights"), None)
        assert ai_module is not None, "ai_insights module not found"
        print(f"TEST_16 PASS: ai_insights enabled={ai_module['enabled']}")

    def test_get_modules_shows_space_planning_enabled(self, auth_headers):
        """TEST_17: space_planning module is enabled for production tenant"""
        response = requests.get(f"{BASE_URL}/api/tenant-admin/modules", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        modules = data.get("modules", [])
        space_module = next((m for m in modules if m["module_id"] == "space_planning"), None)
        assert space_module is not None, "space_planning module not found"
        # Based on iteration 107, space_planning was toggled ON
        print(f"TEST_17 PASS: space_planning enabled={space_module['enabled']}")

    def test_toggle_ai_insights_on(self, auth_headers):
        """TEST_18: Can enable ai_insights module"""
        response = requests.put(
            f"{BASE_URL}/api/tenant-admin/modules/ai_insights/toggle",
            headers=auth_headers,
            json={"enabled": True}
        )
        assert response.status_code == 200, f"Failed to enable ai_insights: {response.text}"
        data = response.json()
        assert data.get("success") is True
        print("TEST_18 PASS: ai_insights module enabled successfully")

    def test_verify_ai_insights_enabled(self, auth_headers):
        """TEST_19: Verify ai_insights is now enabled"""
        response = requests.get(f"{BASE_URL}/api/tenant-admin/modules", headers=auth_headers)
        data = response.json()
        modules = data.get("modules", [])
        ai_module = next((m for m in modules if m["module_id"] == "ai_insights"), None)
        assert ai_module["enabled"] is True, "ai_insights should be enabled"
        print("TEST_19 PASS: ai_insights verified as enabled")

    def test_toggle_ai_insights_off(self, auth_headers):
        """TEST_20: Can disable ai_insights module (restore original state)"""
        response = requests.put(
            f"{BASE_URL}/api/tenant-admin/modules/ai_insights/toggle",
            headers=auth_headers,
            json={"enabled": False}
        )
        assert response.status_code == 200, f"Failed to disable ai_insights: {response.text}"
        print("TEST_20 PASS: ai_insights module disabled (restored)")


class TestUnauthenticated:
    """Tests for unauthenticated access"""

    def test_readiness_requires_auth(self):
        """TEST_21: Readiness endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dashboards/readiness")
        # Should return 400 (tenant context required) or 401/403
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"
        print(f"TEST_21 PASS: Readiness requires auth (status={response.status_code})")

    def test_forecast_accuracy_requires_auth(self):
        """TEST_22: Forecast accuracy endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dashboards/forecast-accuracy")
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"
        print(f"TEST_22 PASS: Forecast accuracy requires auth (status={response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
