"""
Test Suite for AI Demand Planning P1 Features (Iteration 58)
Tests: EOQ Calculation, Per-SKU Lead Times, SKU-Level Forecasting

P1.1 EOQ: Economic Order Quantity replacing 1.5x ROP heuristic
P1.2 Lead Times: Per-SKU lead_time_days from SKU master
P1.3 SKU Forecast: New GET /api/analytics/ai-demand/forecast/sku/{sku} endpoint
"""

import pytest
import requests
import os
import math

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# SKU lead times from seed data
SKU_LEAD_TIMES = {
    "TSHIRT-BLK-M": 7,
    "TSHIRT-BLK-L": 7,
    "HOODIE-GRY-M": 14,
    "HOODIE-GRY-L": 14,
    "CAP-BLK-ONE": 5,
    "SOCKS-WHT-3PK": 3,
    "JOGGER-BLK-M": 10,
    "SNEAKER-WHT-9": 21,
    "BACKPACK-BLK": 12,
    "WATER-BOTTLE-500": 4,
}

ALL_SKUS = list(SKU_LEAD_TIMES.keys())


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for demo admin"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@demo.com",
        "password": "demo1234",
        "tenant": "demo"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ═══════════════════════════════════════════════════════════════
# P1.1 EOQ TESTS - Economic Order Quantity
# ═══════════════════════════════════════════════════════════════

class TestEOQCalculation:
    """P1.1: EOQ calculation replacing 1.5x ROP heuristic"""

    def test_reorder_endpoint_returns_eoq_field(self, authenticated_client):
        """P1.1: Reorder endpoint returns 'eoq' field per item"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should have 'items' array"
        assert len(data["items"]) > 0, "Should have at least one item"
        
        # Check first item has eoq field
        first_item = data["items"][0]
        assert "eoq" in first_item, f"Item should have 'eoq' field. Keys: {first_item.keys()}"
        assert isinstance(first_item["eoq"], (int, float)), "EOQ should be numeric"
        assert first_item["eoq"] > 0, "EOQ should be positive"
        print(f"PASS: First item EOQ = {first_item['eoq']}")

    def test_reorder_accepts_ordering_cost_param(self, authenticated_client):
        """P1.1: Reorder endpoint accepts ordering_cost query param"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation",
            params={"ordering_cost": 750}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["summary"]["ordering_cost"] == 750, f"Expected ordering_cost=750, got {data['summary'].get('ordering_cost')}"
        print(f"PASS: ordering_cost param accepted, summary shows {data['summary']['ordering_cost']}")

    def test_reorder_accepts_holding_cost_pct_param(self, authenticated_client):
        """P1.1: Reorder endpoint accepts holding_cost_pct query param"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation",
            params={"holding_cost_pct": 0.30}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["summary"]["holding_cost_pct"] == 0.30, f"Expected holding_cost_pct=0.30, got {data['summary'].get('holding_cost_pct')}"
        print(f"PASS: holding_cost_pct param accepted, summary shows {data['summary']['holding_cost_pct']}")

    def test_eoq_formula_correctness(self, authenticated_client):
        """P1.1: EOQ formula = sqrt(2*D*S/H) where D=annual_demand, S=ordering_cost, H=mrp*holding_cost_pct"""
        ordering_cost = 500
        holding_cost_pct = 0.25
        
        response = authenticated_client.get(
            f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation",
            params={"ordering_cost": ordering_cost, "holding_cost_pct": holding_cost_pct}
        )
        assert response.status_code == 200
        
        data = response.json()
        items = data["items"]
        
        # Verify EOQ formula for at least one item
        for item in items[:3]:  # Check first 3 items
            if item.get("annual_demand", 0) > 0 and item.get("holding_cost", 0) > 0:
                D = item["annual_demand"]
                S = ordering_cost
                H = item["holding_cost"]
                expected_eoq = round(math.sqrt(2 * D * S / H))
                actual_eoq = item["eoq"]
                
                # Allow small tolerance for rounding
                assert abs(actual_eoq - expected_eoq) <= 2, \
                    f"EOQ mismatch for {item['sku']}: expected ~{expected_eoq}, got {actual_eoq}"
                print(f"PASS: {item['sku']} EOQ={actual_eoq} (expected ~{expected_eoq}, D={D}, S={S}, H={H})")

    def test_recommended_order_is_eoq_multiple(self, authenticated_client):
        """P1.1: recommended_order is rounded up to nearest EOQ multiple (not 1.5×ROP)"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation")
        assert response.status_code == 200
        
        data = response.json()
        items = data["items"]
        
        # Find items that need reorder
        reorder_items = [i for i in items if i["status"] == "reorder_needed" and i["eoq"] > 0]
        
        for item in reorder_items[:3]:
            eoq = item["eoq"]
            recommended = item["recommended_order"]
            
            if recommended > 0:
                # recommended_order should be a multiple of EOQ
                remainder = recommended % eoq
                assert remainder == 0 or remainder < 1, \
                    f"{item['sku']}: recommended_order={recommended} should be multiple of EOQ={eoq}"
                print(f"PASS: {item['sku']} recommended_order={recommended} is multiple of EOQ={eoq}")

    def test_summary_includes_eoq_params(self, authenticated_client):
        """P1.1: Summary includes ordering_cost and holding_cost_pct"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation")
        assert response.status_code == 200
        
        data = response.json()
        summary = data["summary"]
        
        assert "ordering_cost" in summary, "Summary should include ordering_cost"
        assert "holding_cost_pct" in summary, "Summary should include holding_cost_pct"
        print(f"PASS: Summary includes ordering_cost={summary['ordering_cost']}, holding_cost_pct={summary['holding_cost_pct']}")

    def test_items_show_annual_demand_and_holding_cost(self, authenticated_client):
        """P1.1: Each item shows annual_demand and holding_cost fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation")
        assert response.status_code == 200
        
        data = response.json()
        items = data["items"]
        
        for item in items[:5]:
            assert "annual_demand" in item, f"{item['sku']} should have annual_demand"
            assert "holding_cost" in item, f"{item['sku']} should have holding_cost"
            assert item["annual_demand"] >= 0, "annual_demand should be non-negative"
            assert item["holding_cost"] >= 0, "holding_cost should be non-negative"
            print(f"PASS: {item['sku']} annual_demand={item['annual_demand']}, holding_cost={item['holding_cost']}")


# ═══════════════════════════════════════════════════════════════
# P1.2 LEAD TIMES TESTS - Per-SKU Lead Time from SKU Master
# ═══════════════════════════════════════════════════════════════

class TestLeadTimes:
    """P1.2: Lead time from SKU master — per-SKU lead_time_days field"""

    def test_sku_master_has_lead_time_days(self, authenticated_client):
        """P1.2: SKU master has lead_time_days field (10 SKUs each with different lead times)"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/data-health")
        assert response.status_code == 200
        
        data = response.json()
        lead_times = data.get("lead_times", {})
        
        assert lead_times.get("total_skus") == 10, f"Expected 10 SKUs, got {lead_times.get('total_skus')}"
        assert lead_times.get("with_lead_time") == 10, f"Expected 10 SKUs with lead_time, got {lead_times.get('with_lead_time')}"
        assert lead_times.get("status") == "complete", f"Expected status='complete', got {lead_times.get('status')}"
        print(f"PASS: Lead times status={lead_times['status']}, {lead_times['with_lead_time']}/{lead_times['total_skus']} SKUs")

    def test_reorder_uses_per_sku_lead_time(self, authenticated_client):
        """P1.2: Reorder endpoint uses per-SKU lead_time_days from SKU master"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation")
        assert response.status_code == 200
        
        data = response.json()
        items = data["items"]
        
        # Check that different SKUs have different lead times
        lead_times_found = {}
        for item in items:
            sku = item["sku"]
            lt = item.get("lead_time")
            if sku in SKU_LEAD_TIMES:
                expected_lt = SKU_LEAD_TIMES[sku]
                assert lt == expected_lt, f"{sku}: expected lead_time={expected_lt}, got {lt}"
                lead_times_found[sku] = lt
                print(f"PASS: {sku} lead_time={lt} (expected {expected_lt})")
        
        # Verify we found multiple different lead times
        unique_lts = set(lead_times_found.values())
        assert len(unique_lts) >= 3, f"Expected at least 3 different lead times, found {unique_lts}"

    def test_specific_sku_lead_times(self, authenticated_client):
        """P1.2: Verify specific SKU lead times (TSHIRT=7d, HOODIE=14d, SNEAKER=21d, SOCKS=3d)"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation")
        assert response.status_code == 200
        
        data = response.json()
        items = {i["sku"]: i for i in data["items"]}
        
        test_cases = [
            ("TSHIRT-BLK-M", 7),
            ("HOODIE-GRY-M", 14),
            ("SNEAKER-WHT-9", 21),
            ("SOCKS-WHT-3PK", 3),
        ]
        
        for sku, expected_lt in test_cases:
            if sku in items:
                actual_lt = items[sku].get("lead_time")
                assert actual_lt == expected_lt, f"{sku}: expected {expected_lt}d, got {actual_lt}d"
                print(f"PASS: {sku} lead_time={actual_lt}d (expected {expected_lt}d)")

    def test_reorder_items_show_lead_time_field(self, authenticated_client):
        """P1.2: Each reorder item shows 'lead_time' field"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation")
        assert response.status_code == 200
        
        data = response.json()
        items = data["items"]
        
        for item in items:
            assert "lead_time" in item, f"{item['sku']} should have 'lead_time' field"
            assert isinstance(item["lead_time"], (int, float)), f"{item['sku']} lead_time should be numeric"
            assert item["lead_time"] > 0, f"{item['sku']} lead_time should be positive"
        
        print(f"PASS: All {len(items)} items have lead_time field")

    def test_data_health_shows_lead_times_complete(self, authenticated_client):
        """P1.2: Data Health shows lead_times status='complete' with 10/10 SKUs"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/data-health")
        assert response.status_code == 200
        
        data = response.json()
        lead_times = data.get("lead_times", {})
        
        assert lead_times.get("status") == "complete", f"Expected status='complete', got {lead_times.get('status')}"
        assert lead_times.get("percent_complete") == 100, f"Expected 100%, got {lead_times.get('percent_complete')}%"
        print(f"PASS: Lead times complete - {lead_times['with_lead_time']}/{lead_times['total_skus']} SKUs ({lead_times['percent_complete']}%)")


# ═══════════════════════════════════════════════════════════════
# P1.3 SKU FORECAST TESTS - SKU-Level Forecasting
# ═══════════════════════════════════════════════════════════════

class TestSkuForecast:
    """P1.3: SKU-level forecasting — new GET /api/analytics/ai-demand/forecast/sku/{sku} endpoint"""

    def test_sku_forecast_endpoint_exists(self, authenticated_client):
        """P1.3: GET /api/analytics/ai-demand/forecast/sku/TSHIRT-BLK-M returns forecast data"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast/sku/TSHIRT-BLK-M")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["sku"] == "TSHIRT-BLK-M", f"Expected sku='TSHIRT-BLK-M', got {data.get('sku')}"
        print(f"PASS: SKU forecast endpoint returns data for TSHIRT-BLK-M")

    def test_sku_forecast_response_structure(self, authenticated_client):
        """P1.3: Response includes sku, sku_meta, forecast, confidence_intervals, models_used, confidence_score, reorder info"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast/sku/TSHIRT-BLK-M")
        assert response.status_code == 200
        
        data = response.json()
        
        # Required fields
        required_fields = ["sku", "sku_meta", "forecast", "confidence_intervals", "models_used", "confidence_score"]
        for field in required_fields:
            assert field in data, f"Response should have '{field}' field"
        
        # sku_meta should have style, mrp, lead_time_days, category, subcategory
        sku_meta = data["sku_meta"]
        meta_fields = ["style", "mrp", "lead_time_days"]
        for field in meta_fields:
            assert field in sku_meta, f"sku_meta should have '{field}' field"
        
        # reorder info
        assert "reorder" in data, "Response should have 'reorder' field"
        
        print(f"PASS: SKU forecast response has all required fields")
        print(f"  sku_meta: style={sku_meta.get('style')}, mrp={sku_meta.get('mrp')}, lead_time={sku_meta.get('lead_time_days')}")

    def test_sku_forecast_all_3_models_active(self, authenticated_client):
        """P1.3: All 3 models active (Holt-Winters, Random Forest, Seasonal Decomposition) since 25 months of data"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast/sku/TSHIRT-BLK-M")
        assert response.status_code == 200
        
        data = response.json()
        models_used = data.get("models_used", [])
        
        expected_models = ["Holt-Winters", "Random Forest", "Seasonal Decomposition"]
        for model in expected_models:
            assert model in models_used, f"Expected '{model}' in models_used, got {models_used}"
        
        print(f"PASS: All 3 ML models active: {models_used}")

    def test_sku_forecast_reorder_includes_eoq_and_lead_time(self, authenticated_client):
        """P1.3: Reorder info includes EOQ and per-SKU lead time"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast/sku/TSHIRT-BLK-M")
        assert response.status_code == 200
        
        data = response.json()
        reorder = data.get("reorder", {})
        
        assert "eoq" in reorder, "reorder should have 'eoq' field"
        assert "lead_time_days" in reorder, "reorder should have 'lead_time_days' field"
        assert reorder["lead_time_days"] == 7, f"TSHIRT-BLK-M should have lead_time=7, got {reorder.get('lead_time_days')}"
        
        print(f"PASS: Reorder info has EOQ={reorder['eoq']}, lead_time={reorder['lead_time_days']}d")

    def test_all_10_skus_return_valid_forecast(self, authenticated_client):
        """P1.3: Each of the 10 SKUs should return valid forecast"""
        for sku in ALL_SKUS:
            response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast/sku/{sku}")
            assert response.status_code == 200, f"{sku}: Expected 200, got {response.status_code}"
            
            data = response.json()
            assert data["sku"] == sku, f"Expected sku='{sku}', got {data.get('sku')}"
            assert "forecast" in data, f"{sku}: Response should have 'forecast' field"
            
            # Should not be insufficient data (we have 25 months)
            if not data.get("insufficient_data", False):
                assert len(data["forecast"]) > 0, f"{sku}: forecast should not be empty"
            
            print(f"PASS: {sku} returns valid forecast (confidence={data.get('confidence_score', 0)}%)")

    def test_options_endpoint_returns_skus_list(self, authenticated_client):
        """P1.3: Options endpoint returns 'skus' list with all 10 SKUs"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/options")
        assert response.status_code == 200
        
        data = response.json()
        skus = data.get("skus", [])
        
        assert len(skus) == 10, f"Expected 10 SKUs, got {len(skus)}"
        
        for sku in ALL_SKUS:
            assert sku in skus, f"Expected '{sku}' in skus list"
        
        print(f"PASS: Options endpoint returns all 10 SKUs: {skus}")


# ═══════════════════════════════════════════════════════════════
# REGRESSION TESTS - Existing Endpoints Still Work
# ═══════════════════════════════════════════════════════════════

class TestRegression:
    """Regression: All existing endpoints still work"""

    def test_forecast_endpoint(self, authenticated_client):
        """Regression: /api/analytics/ai-demand/forecast still works"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        assert response.status_code == 200
        data = response.json()
        assert "forecast" in data
        assert data.get("data_source") == "uploaded"
        print(f"PASS: Forecast endpoint works, data_source={data['data_source']}")

    def test_stockout_risk_endpoint(self, authenticated_client):
        """Regression: /api/analytics/ai-demand/stockout-risk still works"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/stockout-risk")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data.get("data_source") == "uploaded"
        print(f"PASS: Stockout risk endpoint works, data_source={data['data_source']}")

    def test_topseller_prediction_endpoint(self, authenticated_client):
        """Regression: /api/analytics/ai-demand/topseller-prediction still works"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/topseller-prediction")
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert data.get("data_source") == "uploaded"
        print(f"PASS: Topseller prediction endpoint works, data_source={data['data_source']}")

    def test_supply_feasibility_endpoint(self, authenticated_client):
        """Regression: /api/analytics/ai-demand/supply-feasibility still works"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/supply-feasibility")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert data.get("data_source") == "uploaded"
        print(f"PASS: Supply feasibility endpoint works, data_source={data['data_source']}")

    def test_options_endpoint(self, authenticated_client):
        """Regression: /api/analytics/ai-demand/options still works"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/options")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        print(f"PASS: Options endpoint works, categories={data.get('categories')}")

    def test_plans_endpoint(self, authenticated_client):
        """Regression: /api/analytics/ai-demand/plans still works"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        print(f"PASS: Plans endpoint works, {len(data.get('plans', []))} plans found")

    def test_data_health_endpoint(self, authenticated_client):
        """Regression: /api/analytics/ai-demand/data-health still works"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/data-health")
        assert response.status_code == 200
        data = response.json()
        assert "forecast_readiness" in data
        assert data["forecast_readiness"].get("using_demo_data") == False
        print(f"PASS: Data health endpoint works, using_demo_data={data['forecast_readiness']['using_demo_data']}")

    def test_data_health_shows_real_ml_forecast(self, authenticated_client):
        """Regression: Data Health shows REAL ML FORECAST badge"""
        response = authenticated_client.get(f"{BASE_URL}/api/analytics/ai-demand/data-health")
        assert response.status_code == 200
        data = response.json()
        
        fr = data.get("forecast_readiness", {})
        assert fr.get("using_demo_data") == False, "Should not be using demo data"
        assert fr.get("days_available", 0) >= 180, f"Should have >= 180 days, got {fr.get('days_available')}"
        assert fr.get("progress_pct", 0) >= 100, f"Progress should be >= 100%, got {fr.get('progress_pct')}"
        
        print(f"PASS: Data Health shows REAL ML FORECAST - {fr['days_available']} days, {fr['progress_pct']}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
