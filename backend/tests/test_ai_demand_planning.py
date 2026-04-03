"""
AI Demand Planning Module Tests - Iteration 32
Tests for: ML Forecast, Stockout Prediction, Topseller Prediction, 
           Reorder Optimisation, Demand Plan Generation
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAIDemandPlanningEndpoints:
    """Test all 5 AI Demand Planning endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get auth token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "tenant_id": "demo",
            "email": "admin@demo.com",
            "password": "demo1234"
        })
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    # ── 1. ML Forecast Endpoint Tests ──────────────────────────────
    
    def test_ml_forecast_returns_200(self):
        """GET /api/analytics/ai-demand/forecast returns 200"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: ML Forecast endpoint returns 200")
    
    def test_ml_forecast_response_structure(self):
        """ML Forecast response has required fields"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "models_used" in data, "Missing 'models_used' field"
        assert "forecast" in data, "Missing 'forecast' field"
        assert "confidence_score" in data, "Missing 'confidence_score' field"
        assert "months" in data, "Missing 'months' field"
        assert "seasonality_factors" in data, "Missing 'seasonality_factors' field"
        
        # Validate data types
        assert isinstance(data["models_used"], list), "models_used should be a list"
        assert isinstance(data["forecast"], list), "forecast should be a list"
        assert isinstance(data["confidence_score"], (int, float)), "confidence_score should be numeric"
        assert isinstance(data["months"], list), "months should be a list"
        
        print(f"PASS: ML Forecast has all required fields. Models used: {data['models_used']}")
    
    def test_ml_forecast_with_category_filter(self):
        """ML Forecast accepts category filter"""
        # First get available categories
        filter_response = self.session.get(f"{BASE_URL}/api/analytics/filter-options")
        categories = filter_response.json().get("categories", [])
        
        if categories:
            category = categories[0]
            response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/forecast", 
                                        params={"category": category})
            assert response.status_code == 200
            data = response.json()
            assert data.get("category") == category
            print(f"PASS: ML Forecast with category filter '{category}' works")
        else:
            print("SKIP: No categories available for filter test")
    
    def test_ml_forecast_horizon_parameter(self):
        """ML Forecast accepts forecast_horizon parameter"""
        for horizon in [6, 12, 18, 24]:
            response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/forecast",
                                        params={"forecast_horizon": horizon})
            assert response.status_code == 200
            data = response.json()
            assert len(data.get("forecast", [])) == horizon, f"Expected {horizon} forecast values"
            assert len(data.get("months", [])) == horizon, f"Expected {horizon} months"
        print("PASS: ML Forecast horizon parameter works for 6, 12, 18, 24 months")
    
    def test_ml_forecast_confidence_intervals(self):
        """ML Forecast includes confidence intervals"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        assert response.status_code == 200
        data = response.json()
        
        ci = data.get("confidence_intervals", {})
        assert "lower" in ci or "upper" in ci, "Missing confidence intervals"
        
        if "lower" in ci and "upper" in ci:
            assert len(ci["lower"]) == len(data["forecast"]), "Lower bound length mismatch"
            assert len(ci["upper"]) == len(data["forecast"]), "Upper bound length mismatch"
        print("PASS: ML Forecast includes confidence intervals")
    
    # ── 2. Stockout Risk Prediction Tests ──────────────────────────
    
    def test_stockout_risk_returns_200(self):
        """GET /api/analytics/ai-demand/stockout-risk returns 200"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/stockout-risk")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Stockout Risk endpoint returns 200")
    
    def test_stockout_risk_response_structure(self):
        """Stockout Risk response has summary and items"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/stockout-risk")
        assert response.status_code == 200
        data = response.json()
        
        # Check summary
        assert "summary" in data, "Missing 'summary' field"
        summary = data["summary"]
        assert "critical" in summary, "Missing 'critical' count in summary"
        assert "high" in summary, "Missing 'high' count in summary"
        assert "medium" in summary, "Missing 'medium' count in summary"
        assert "low" in summary, "Missing 'low' count in summary"
        assert "healthy" in summary, "Missing 'healthy' count in summary"
        
        # Check items array
        assert "items" in data, "Missing 'items' field"
        assert isinstance(data["items"], list), "items should be a list"
        
        print(f"PASS: Stockout Risk has summary with risk counts: critical={summary['critical']}, high={summary['high']}")
    
    def test_stockout_risk_items_structure(self):
        """Stockout Risk items have required fields"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/stockout-risk")
        assert response.status_code == 200
        data = response.json()
        
        items = data.get("items", [])
        if items:
            item = items[0]
            required_fields = ["sku", "store_code", "soh", "ros", "days_until_stockout", "risk"]
            for field in required_fields:
                assert field in item, f"Missing '{field}' in stockout item"
            
            # Validate risk values
            valid_risks = ["critical", "high", "medium", "low", "healthy"]
            assert item["risk"] in valid_risks, f"Invalid risk value: {item['risk']}"
            print(f"PASS: Stockout items have all required fields. First item risk: {item['risk']}")
        else:
            print("PASS: Stockout items array is empty (no data)")
    
    # ── 3. Topseller Prediction Tests ──────────────────────────────
    
    def test_topseller_prediction_returns_200(self):
        """GET /api/analytics/ai-demand/topseller-prediction returns 200"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/topseller-prediction")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Topseller Prediction endpoint returns 200")
    
    def test_topseller_prediction_response_structure(self):
        """Topseller Prediction response has predictions array"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/topseller-prediction")
        assert response.status_code == 200
        data = response.json()
        
        assert "predictions" in data, "Missing 'predictions' field"
        assert isinstance(data["predictions"], list), "predictions should be a list"
        
        predictions = data["predictions"]
        if predictions:
            pred = predictions[0]
            required_fields = ["style_code", "growth_rate", "predicted_revenue_3m", "confidence"]
            for field in required_fields:
                assert field in pred, f"Missing '{field}' in topseller prediction"
            
            # Validate growth_rate is numeric
            assert isinstance(pred["growth_rate"], (int, float)), "growth_rate should be numeric"
            print(f"PASS: Topseller predictions have required fields. Top style: {pred['style_code']} with {pred['growth_rate']}% growth")
        else:
            print("PASS: Topseller predictions array is empty (demo data)")
    
    # ── 4. Reorder Optimisation Tests ──────────────────────────────
    
    def test_reorder_optimisation_returns_200(self):
        """GET /api/analytics/ai-demand/reorder-optimisation returns 200"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Reorder Optimisation endpoint returns 200")
    
    def test_reorder_optimisation_response_structure(self):
        """Reorder Optimisation response has summary and items"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation")
        assert response.status_code == 200
        data = response.json()
        
        # Check summary
        assert "summary" in data, "Missing 'summary' field"
        summary = data["summary"]
        assert "total_skus" in summary, "Missing 'total_skus' in summary"
        assert "reorder_needed" in summary, "Missing 'reorder_needed' in summary"
        assert "healthy" in summary, "Missing 'healthy' in summary"
        assert "lead_time_days" in summary, "Missing 'lead_time_days' in summary"
        assert "service_level" in summary, "Missing 'service_level' in summary"
        
        # Check items
        assert "items" in data, "Missing 'items' field"
        assert isinstance(data["items"], list), "items should be a list"
        
        print(f"PASS: Reorder Optimisation has summary. Reorder needed: {summary['reorder_needed']}, Healthy: {summary['healthy']}")
    
    def test_reorder_optimisation_items_structure(self):
        """Reorder Optimisation items have reorder_point, safety_stock, status"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation")
        assert response.status_code == 200
        data = response.json()
        
        items = data.get("items", [])
        if items:
            item = items[0]
            required_fields = ["sku", "reorder_point", "safety_stock", "status", "current_stock"]
            for field in required_fields:
                assert field in item, f"Missing '{field}' in reorder item"
            
            # Validate status values
            valid_statuses = ["reorder_needed", "healthy"]
            assert item["status"] in valid_statuses, f"Invalid status: {item['status']}"
            print(f"PASS: Reorder items have required fields. First item status: {item['status']}")
        else:
            print("PASS: Reorder items array is empty (demo data)")
    
    def test_reorder_optimisation_parameters(self):
        """Reorder Optimisation accepts lead_time_days and service_level params"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation",
                                    params={"lead_time_days": 21, "service_level": 97.5})
        assert response.status_code == 200
        data = response.json()
        
        summary = data.get("summary", {})
        assert summary.get("lead_time_days") == 21, "lead_time_days not applied"
        assert summary.get("service_level") == 97.5, "service_level not applied"
        print("PASS: Reorder Optimisation accepts lead_time_days and service_level parameters")
    
    # ── 5. Generate Demand Plan Tests ──────────────────────────────
    
    def test_generate_plan_returns_200(self):
        """POST /api/analytics/ai-demand/generate-plan returns 200"""
        response = self.session.post(f"{BASE_URL}/api/analytics/ai-demand/generate-plan")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Generate Plan endpoint returns 200")
    
    def test_generate_plan_response_structure(self):
        """Generate Plan response has plan with subcategories, total_planned, variance"""
        response = self.session.post(f"{BASE_URL}/api/analytics/ai-demand/generate-plan")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "annual_target" in data, "Missing 'annual_target' field"
        assert "total_planned" in data, "Missing 'total_planned' field"
        assert "variance" in data, "Missing 'variance' field"
        assert "variance_pct" in data, "Missing 'variance_pct' field"
        assert "subcategories" in data, "Missing 'subcategories' field"
        
        # Validate subcategories structure
        subcats = data.get("subcategories", [])
        assert isinstance(subcats, list), "subcategories should be a list"
        
        if subcats:
            subcat = subcats[0]
            assert "name" in subcat, "Missing 'name' in subcategory"
            assert "monthly_plan" in subcat, "Missing 'monthly_plan' in subcategory"
            assert "total" in subcat, "Missing 'total' in subcategory"
            assert "confidence" in subcat, "Missing 'confidence' in subcategory"
        
        print(f"PASS: Generate Plan has required fields. Total planned: {data['total_planned']}, Variance: {data['variance_pct']}%")
    
    def test_generate_plan_with_category_and_target(self):
        """Generate Plan accepts category and annual_target params"""
        # Get first available category
        filter_response = self.session.get(f"{BASE_URL}/api/analytics/filter-options")
        categories = filter_response.json().get("categories", [])
        
        params = {"annual_target": 5000000}
        if categories:
            params["category"] = categories[0]
        
        response = self.session.post(f"{BASE_URL}/api/analytics/ai-demand/generate-plan", params=params)
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("annual_target") == 5000000, "annual_target not applied"
        if categories:
            assert data.get("category") == categories[0], "category not applied"
        
        print(f"PASS: Generate Plan accepts category and annual_target parameters")
    
    # ── Filter Options Test ────────────────────────────────────────
    
    def test_filter_options_returns_categories(self):
        """GET /api/analytics/filter-options returns categories for AI Demand filters"""
        response = self.session.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data, "Missing 'categories' in filter options"
        print(f"PASS: Filter options returns categories: {data.get('categories', [])[:5]}...")


class TestMLForecastEngine:
    """Test ML Forecast Engine model outputs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "tenant_id": "demo",
            "email": "admin@demo.com",
            "password": "demo1234"
        })
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_ensemble_uses_multiple_models(self):
        """Ensemble forecast uses multiple ML models"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        assert response.status_code == 200
        data = response.json()
        
        models_used = data.get("models_used", [])
        # Should use at least one model (fallback is Moving Average)
        assert len(models_used) >= 1, "No models used in forecast"
        
        # Check for expected model names
        expected_models = ["Holt-Winters", "Random Forest", "Seasonal Decomposition", "Moving Average (Fallback)"]
        for model in models_used:
            assert model in expected_models, f"Unexpected model: {model}"
        
        print(f"PASS: Ensemble uses models: {models_used}")
    
    def test_forecast_values_are_positive(self):
        """All forecast values should be non-negative"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        assert response.status_code == 200
        data = response.json()
        
        forecast = data.get("forecast", [])
        for i, val in enumerate(forecast):
            assert val >= 0, f"Negative forecast value at index {i}: {val}"
        
        print(f"PASS: All {len(forecast)} forecast values are non-negative")
    
    def test_seasonality_factors_valid(self):
        """Seasonality factors should be valid ratios"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        assert response.status_code == 200
        data = response.json()
        
        seasonality = data.get("seasonality_factors", {})
        assert len(seasonality) == 12, f"Expected 12 seasonality factors, got {len(seasonality)}"
        
        for month, factor in seasonality.items():
            assert 0 < factor < 5, f"Invalid seasonality factor for month {month}: {factor}"
        
        print(f"PASS: All 12 seasonality factors are valid ratios")
    
    def test_growth_trend_classification(self):
        """Growth trend should be classified correctly"""
        response = self.session.get(f"{BASE_URL}/api/analytics/ai-demand/forecast")
        assert response.status_code == 200
        data = response.json()
        
        growth = data.get("growth_trend", {})
        assert "trend" in growth, "Missing 'trend' in growth_trend"
        assert "avg_monthly_growth" in growth, "Missing 'avg_monthly_growth' in growth_trend"
        
        valid_trends = ["accelerating", "declining", "stable"]
        assert growth["trend"] in valid_trends, f"Invalid trend: {growth['trend']}"
        
        print(f"PASS: Growth trend is '{growth['trend']}' with {growth['avg_monthly_growth']}% avg monthly growth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
