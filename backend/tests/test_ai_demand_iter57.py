"""
Iteration 57: AI Demand Planning - Full ML Pipeline Verification
Tests 25 months of seeded data (Apr 2024 - Apr 2026) with all 3 ML models active.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://zip-improved.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@demo.com"
TEST_PASSWORD = "demo1234"
TEST_TENANT = "demo"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for API calls."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "tenant": TEST_TENANT
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestDataHealth:
    """Data Health endpoint tests - verify 25 months of seeded data."""
    
    def test_data_health_returns_200(self, api_client):
        """TEST_01: Data health endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/data-health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("TEST_01 PASS: Data health returns 200")
    
    def test_data_health_days_available(self, api_client):
        """TEST_02: Data health shows 757+ days available (25 months)."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/data-health")
        data = response.json()
        
        # Check daily_sales days
        daily_sales = data.get("daily_sales", {})
        days_available = daily_sales.get("days_available", 0)
        
        # Should have ~757 days (Apr 2024 - Apr 2026)
        assert days_available >= 700, f"Expected 700+ days, got {days_available}"
        print(f"TEST_02 PASS: Daily sales has {days_available} days available")
    
    def test_data_health_using_demo_data_false(self, api_client):
        """TEST_03: using_demo_data should be false with 25 months of data."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/data-health")
        data = response.json()
        
        fr = data.get("forecast_readiness", {})
        using_demo = fr.get("using_demo_data", True)
        
        assert using_demo is False, f"Expected using_demo_data=false, got {using_demo}"
        print(f"TEST_03 PASS: using_demo_data={using_demo}")
    
    def test_data_health_progress_100(self, api_client):
        """TEST_04: Progress should be 100% with 757 days > 180 required."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/data-health")
        data = response.json()
        
        fr = data.get("forecast_readiness", {})
        progress = fr.get("progress_pct", 0)
        
        assert progress == 100, f"Expected progress_pct=100, got {progress}"
        print(f"TEST_04 PASS: progress_pct={progress}%")
    
    def test_data_health_row_counts(self, api_client):
        """TEST_05: Verify row counts match seeded data."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/data-health")
        data = response.json()
        
        # Expected: daily_sales=30961, store_inventory=37850, warehouse_inventory=15140
        daily_sales = data.get("daily_sales", {})
        store_inv = data.get("store_inventory", {})
        wh_inv = data.get("warehouse_inventory", {})
        sku_master = data.get("sku_master", {})
        store_master = data.get("store_master", {})
        
        assert daily_sales.get("row_count", 0) >= 30000, f"Expected 30000+ daily_sales rows"
        assert store_inv.get("row_count", 0) >= 37000, f"Expected 37000+ store_inventory rows"
        assert wh_inv.get("row_count", 0) >= 15000, f"Expected 15000+ warehouse_inventory rows"
        assert sku_master.get("count", 0) == 10, f"Expected 10 SKUs"
        assert store_master.get("count", 0) == 5, f"Expected 5 stores"
        
        print(f"TEST_05 PASS: Row counts - daily_sales={daily_sales.get('row_count')}, "
              f"store_inv={store_inv.get('row_count')}, wh_inv={wh_inv.get('row_count')}, "
              f"sku_master={sku_master.get('count')}, store_master={store_master.get('count')}")


class TestForecast:
    """ML Forecast endpoint tests - verify all 3 models active."""
    
    def test_forecast_returns_200(self, api_client):
        """TEST_06: Forecast endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("TEST_06 PASS: Forecast returns 200")
    
    def test_forecast_data_source_uploaded(self, api_client):
        """TEST_07: Forecast data_source should be 'uploaded' (not 'demo')."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        data = response.json()
        
        data_source = data.get("data_source", "")
        assert data_source == "uploaded", f"Expected data_source='uploaded', got '{data_source}'"
        print(f"TEST_07 PASS: data_source='{data_source}'")
    
    def test_forecast_insufficient_data_false(self, api_client):
        """TEST_08: insufficient_data should be false with 25 months."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        data = response.json()
        
        insufficient = data.get("insufficient_data", True)
        assert insufficient is False, f"Expected insufficient_data=false, got {insufficient}"
        print(f"TEST_08 PASS: insufficient_data={insufficient}")
    
    def test_forecast_all_3_models_active(self, api_client):
        """TEST_09: All 3 ML models should be active (Holt-Winters, Random Forest, Seasonal Decomposition)."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        data = response.json()
        
        models_used = data.get("models_used", [])
        expected_models = ["Holt-Winters", "Random Forest", "Seasonal Decomposition"]
        
        for model in expected_models:
            assert model in models_used, f"Expected model '{model}' not found in {models_used}"
        
        print(f"TEST_09 PASS: All 3 models active - {models_used}")
    
    def test_forecast_confidence_score_high(self, api_client):
        """TEST_10: Confidence score should be > 80 with real data."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        data = response.json()
        
        confidence = data.get("confidence_score", 0)
        assert confidence > 80, f"Expected confidence > 80, got {confidence}"
        print(f"TEST_10 PASS: confidence_score={confidence}")
    
    def test_forecast_12_months_predictions(self, api_client):
        """TEST_11: Forecast should return 12 months of predictions."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        data = response.json()
        
        forecast = data.get("forecast", [])
        months = data.get("months", [])
        
        assert len(forecast) == 12, f"Expected 12 forecast values, got {len(forecast)}"
        assert len(months) == 12, f"Expected 12 months, got {len(months)}"
        print(f"TEST_11 PASS: 12 months of predictions returned")
    
    def test_forecast_confidence_intervals(self, api_client):
        """TEST_12: Forecast should include confidence intervals."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        data = response.json()
        
        ci = data.get("confidence_intervals", {})
        lower = ci.get("lower", [])
        upper = ci.get("upper", [])
        
        assert len(lower) == 12, f"Expected 12 lower bounds, got {len(lower)}"
        assert len(upper) == 12, f"Expected 12 upper bounds, got {len(upper)}"
        print(f"TEST_12 PASS: Confidence intervals present (lower={len(lower)}, upper={len(upper)})")
    
    def test_forecast_seasonality_factors(self, api_client):
        """TEST_13: Forecast should include seasonality factors."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        data = response.json()
        
        sf = data.get("seasonality_factors", {})
        assert len(sf) == 12, f"Expected 12 seasonality factors, got {len(sf)}"
        
        # Check for realistic variation (not all 1.0)
        values = list(sf.values())
        has_variation = max(values) - min(values) > 0.1
        assert has_variation, f"Seasonality factors should have variation: {sf}"
        print(f"TEST_13 PASS: Seasonality factors with variation - min={min(values):.2f}, max={max(values):.2f}")
    
    def test_forecast_growth_trend(self, api_client):
        """TEST_14: Growth trend should show ~5% monthly growth."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        data = response.json()
        
        gt = data.get("growth_trend", {})
        avg_growth = gt.get("avg_monthly_growth", 0)
        trend = gt.get("trend", "")
        
        # With 5% monthly growth seeded, should show accelerating trend
        assert trend == "accelerating", f"Expected trend='accelerating', got '{trend}'"
        assert avg_growth > 3, f"Expected avg_monthly_growth > 3%, got {avg_growth}%"
        print(f"TEST_14 PASS: growth_trend={trend}, avg_monthly_growth={avg_growth}%")


class TestStockoutRisk:
    """Stockout Risk endpoint tests."""
    
    def test_stockout_risk_returns_200(self, api_client):
        """TEST_15: Stockout risk endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/stockout-risk")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("TEST_15 PASS: Stockout risk returns 200")
    
    def test_stockout_risk_data_source_uploaded(self, api_client):
        """TEST_16: Stockout risk data_source should be 'uploaded'."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/stockout-risk")
        data = response.json()
        
        data_source = data.get("data_source", "")
        assert data_source == "uploaded", f"Expected data_source='uploaded', got '{data_source}'"
        print(f"TEST_16 PASS: data_source='{data_source}'")
    
    def test_stockout_risk_new_skus(self, api_client):
        """TEST_17: Stockout risk should show new SKUs (TSHIRT-BLK-M, etc)."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/stockout-risk")
        data = response.json()
        
        items = data.get("items", [])
        skus = [item.get("sku", "") for item in items]
        
        # Check for at least one of the new SKUs
        new_skus = ["TSHIRT-BLK-M", "TSHIRT-BLK-L", "HOODIE-GRY-M", "HOODIE-GRY-L", 
                    "CAP-BLK-ONE", "SOCKS-WHT-3PK", "JOGGER-BLK-M", "SNEAKER-WHT-9",
                    "BACKPACK-BLK", "WATER-BOTTLE-500"]
        found_new = any(sku in new_skus for sku in skus)
        
        assert found_new, f"Expected new SKUs in stockout risk, got {skus[:5]}"
        print(f"TEST_17 PASS: New SKUs found in stockout risk - {skus[:3]}")


class TestReorderOptimisation:
    """Reorder Optimisation endpoint tests."""
    
    def test_reorder_returns_200(self, api_client):
        """TEST_18: Reorder optimisation endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("TEST_18 PASS: Reorder optimisation returns 200")
    
    def test_reorder_data_source_uploaded(self, api_client):
        """TEST_19: Reorder data_source should be 'uploaded'."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation")
        data = response.json()
        
        data_source = data.get("data_source", "")
        assert data_source == "uploaded", f"Expected data_source='uploaded', got '{data_source}'"
        print(f"TEST_19 PASS: data_source='{data_source}'")
    
    def test_reorder_10_skus(self, api_client):
        """TEST_20: Reorder should show 10 SKUs."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation")
        data = response.json()
        
        summary = data.get("summary", {})
        total_skus = summary.get("total_skus", 0)
        
        assert total_skus == 10, f"Expected 10 SKUs, got {total_skus}"
        print(f"TEST_20 PASS: total_skus={total_skus}")


class TestTopsellerPrediction:
    """Topseller Prediction endpoint tests."""
    
    def test_topseller_returns_200(self, api_client):
        """TEST_21: Topseller prediction endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/topseller-prediction")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("TEST_21 PASS: Topseller prediction returns 200")
    
    def test_topseller_data_source_uploaded(self, api_client):
        """TEST_22: Topseller data_source should be 'uploaded'."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/topseller-prediction")
        data = response.json()
        
        data_source = data.get("data_source", "")
        assert data_source == "uploaded", f"Expected data_source='uploaded', got '{data_source}'"
        print(f"TEST_22 PASS: data_source='{data_source}'")
    
    def test_topseller_identifies_topsellers(self, api_client):
        """TEST_23: Topseller should identify topsellers from real data."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/topseller-prediction")
        data = response.json()
        
        predictions = data.get("predictions", [])
        assert len(predictions) > 0, "Expected at least one topseller prediction"
        
        # Check for is_topseller flag
        topsellers = [p for p in predictions if p.get("is_topseller", False)]
        print(f"TEST_23 PASS: {len(topsellers)} topsellers identified from {len(predictions)} predictions")


class TestSupplyFeasibility:
    """Supply Feasibility endpoint tests."""
    
    def test_supply_feasibility_returns_200(self, api_client):
        """TEST_24: Supply feasibility endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/supply-feasibility")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("TEST_24 PASS: Supply feasibility returns 200")
    
    def test_supply_feasibility_data_source_uploaded(self, api_client):
        """TEST_25: Supply feasibility data_source should be 'uploaded'."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/supply-feasibility")
        data = response.json()
        
        data_source = data.get("data_source", "")
        assert data_source == "uploaded", f"Expected data_source='uploaded', got '{data_source}'"
        print(f"TEST_25 PASS: data_source='{data_source}'")


class TestOptions:
    """Options endpoint tests."""
    
    def test_options_returns_200(self, api_client):
        """TEST_26: Options endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/options")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("TEST_26 PASS: Options returns 200")
    
    def test_options_correct_categories(self, api_client):
        """TEST_27: Options should return correct categories (Tops, Accessories, Bottoms, Footwear)."""
        response = api_client.get(f"{BASE_URL}/api/analytics/ai-demand/options")
        data = response.json()
        
        categories = data.get("categories", [])
        expected = ["Tops", "Accessories", "Bottoms", "Footwear"]
        
        for cat in expected:
            assert cat in categories, f"Expected category '{cat}' not found in {categories}"
        
        print(f"TEST_27 PASS: Categories found - {categories}")


class TestGeneratePlan:
    """Generate Plan endpoint tests."""
    
    def test_generate_plan_returns_200(self, api_client):
        """TEST_28: Generate plan endpoint returns 200."""
        response = api_client.post(f"{BASE_URL}/api/analytics/ai-demand/generate-plan?annual_target=10000000")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("TEST_28 PASS: Generate plan returns 200")
    
    def test_generate_plan_from_real_data(self, api_client):
        """TEST_29: Generated plan should use real forecast data."""
        response = api_client.post(f"{BASE_URL}/api/analytics/ai-demand/generate-plan?annual_target=10000000")
        data = response.json()
        
        data_source = data.get("data_source", "")
        # With 25 months of data, should use uploaded data
        assert data_source == "uploaded", f"Expected data_source='uploaded', got '{data_source}'"
        print(f"TEST_29 PASS: Plan generated from real data - data_source='{data_source}'")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
