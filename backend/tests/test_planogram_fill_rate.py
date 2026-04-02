"""
Planogram Fill Rate Analysis API Tests - Iteration 12
Tests the /api/analytics/planogram-fill-rate endpoint
PRD Formulas:
- Fill Rate = (Current Stock / Norm Allocated) x 100
- Overall Fill Rate = (Sum Stock / Sum Norm) x 100
- Lost Sales = Missing Facings x ROS x ASP
- Compliance: >=90% Good, 80-90% Moderate, <80% Critical
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPlanogramFillRateAPI:
    """Tests for /api/analytics/planogram-fill-rate endpoint"""
    
    def test_planogram_endpoint_returns_200(self):
        """Test that planogram fill rate endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: Planogram fill rate endpoint returns 200")
    
    def test_response_has_summary_field(self):
        """Test that response has summary field with all required KPIs"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        data = response.json()
        
        assert 'summary' in data, "Response missing 'summary' field"
        summary = data['summary']
        
        required_fields = [
            'overall_fill_rate', 'overall_status', 'target_fill_rate',
            'total_lost_sales', 'total_store_skus', 'good_count',
            'moderate_count', 'critical_count', 'total_stores', 'snapshot_date'
        ]
        
        for field in required_fields:
            assert field in summary, f"Summary missing '{field}' field"
        
        print(f"PASS: Summary has all required fields: {list(summary.keys())}")
    
    def test_response_has_store_data(self):
        """Test that response has store_data array with required columns"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        data = response.json()
        
        assert 'store_data' in data, "Response missing 'store_data' field"
        assert isinstance(data['store_data'], list), "store_data should be a list"
        
        if len(data['store_data']) > 0:
            store = data['store_data'][0]
            required_cols = ['store_code', 'current_stock', 'norm_allocated', 'fill_rate', 'status', 'lost_sales']
            for col in required_cols:
                assert col in store, f"Store data missing '{col}' column"
        
        print(f"PASS: store_data has {len(data['store_data'])} stores with required columns")
    
    def test_response_has_category_data(self):
        """Test that response has category_data array"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        data = response.json()
        
        assert 'category_data' in data, "Response missing 'category_data' field"
        assert isinstance(data['category_data'], list), "category_data should be a list"
        
        # Note: category_data may be empty if style_master doesn't have matching joins
        print(f"PASS: category_data present with {len(data['category_data'])} categories")
    
    def test_response_has_trend_data(self):
        """Test that response has trend_data array with weekly data"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        data = response.json()
        
        assert 'trend_data' in data, "Response missing 'trend_data' field"
        assert isinstance(data['trend_data'], list), "trend_data should be a list"
        
        if len(data['trend_data']) > 0:
            trend = data['trend_data'][0]
            required_cols = ['week_label', 'fill_rate', 'target']
            for col in required_cols:
                assert col in trend, f"Trend data missing '{col}' column"
        
        print(f"PASS: trend_data has {len(data['trend_data'])} weeks with required columns")
    
    def test_response_has_detail_data(self):
        """Test that response has detail array with store-SKU level data"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        data = response.json()
        
        assert 'detail' in data, "Response missing 'detail' field"
        assert isinstance(data['detail'], list), "detail should be a list"
        
        if len(data['detail']) > 0:
            detail = data['detail'][0]
            required_cols = ['store_code', 'ean', 'style', 'current_stock', 'norm_allocated', 
                           'fill_rate', 'missing_facings', 'ros', 'asp', 'lost_sales', 'status']
            for col in required_cols:
                assert col in detail, f"Detail data missing '{col}' column"
        
        print(f"PASS: detail has {len(data['detail'])} store-SKU records with required columns")
    
    def test_response_has_recommendations(self):
        """Test that response has recommendations array"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        data = response.json()
        
        assert 'recommendations' in data, "Response missing 'recommendations' field"
        assert isinstance(data['recommendations'], list), "recommendations should be a list"
        
        if len(data['recommendations']) > 0:
            rec = data['recommendations'][0]
            required_cols = ['priority', 'title', 'description']
            for col in required_cols:
                assert col in rec, f"Recommendation missing '{col}' column"
        
        print(f"PASS: recommendations has {len(data['recommendations'])} items")
    
    def test_default_target_fill_rate(self):
        """Test that default target_fill_rate is 85"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        data = response.json()
        
        assert data['summary']['target_fill_rate'] == 85, f"Expected target 85, got {data['summary']['target_fill_rate']}"
        print("PASS: Default target_fill_rate is 85")
    
    def test_custom_target_fill_rate(self):
        """Test that target_fill_rate query parameter works"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate?target_fill_rate=90")
        data = response.json()
        
        assert data['summary']['target_fill_rate'] == 90, f"Expected target 90, got {data['summary']['target_fill_rate']}"
        print("PASS: Custom target_fill_rate=90 works")
    
    def test_compliance_classification(self):
        """Test that compliance classification follows PRD rules: >=90% Good, 80-90% Moderate, <80% Critical"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        data = response.json()
        
        valid_statuses = ['GOOD', 'MODERATE', 'CRITICAL']
        
        # Check store_data statuses
        for store in data['store_data']:
            assert store['status'] in valid_statuses, f"Invalid status: {store['status']}"
            # Verify classification logic
            if store['fill_rate'] >= 90:
                assert store['status'] == 'GOOD', f"Fill rate {store['fill_rate']}% should be GOOD"
            elif store['fill_rate'] >= 80:
                assert store['status'] == 'MODERATE', f"Fill rate {store['fill_rate']}% should be MODERATE"
            else:
                assert store['status'] == 'CRITICAL', f"Fill rate {store['fill_rate']}% should be CRITICAL"
        
        # Check detail statuses
        for detail in data['detail'][:50]:  # Check first 50
            assert detail['status'] in valid_statuses, f"Invalid detail status: {detail['status']}"
        
        print("PASS: Compliance classification follows PRD rules")
    
    def test_summary_counts_match(self):
        """Test that summary counts (good, moderate, critical) add up to total_store_skus"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        data = response.json()
        
        summary = data['summary']
        total_from_counts = summary['good_count'] + summary['moderate_count'] + summary['critical_count']
        
        assert total_from_counts == summary['total_store_skus'], \
            f"Counts don't match: {total_from_counts} != {summary['total_store_skus']}"
        
        print(f"PASS: Summary counts match total_store_skus ({summary['total_store_skus']})")
    
    def test_fill_rate_formula(self):
        """Test that fill rate follows PRD formula: (Current Stock / Norm Allocated) x 100"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        data = response.json()
        
        # Check store-level fill rate calculation
        for store in data['store_data'][:5]:
            expected_fill = round((store['current_stock'] / max(store['norm_allocated'], 1)) * 100, 1)
            assert abs(store['fill_rate'] - expected_fill) < 0.2, \
                f"Store {store['store_code']}: Expected fill rate {expected_fill}, got {store['fill_rate']}"
        
        print("PASS: Fill rate formula verified for store data")
    
    def test_overall_fill_rate_formula(self):
        """Test that overall fill rate follows PRD formula: (Sum Stock / Sum Norm) x 100"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        data = response.json()
        
        total_stock = sum(s['current_stock'] for s in data['store_data'])
        total_norm = sum(s['norm_allocated'] for s in data['store_data'])
        expected_overall = round((total_stock / max(total_norm, 1)) * 100, 1)
        
        # Allow small rounding difference
        assert abs(data['summary']['overall_fill_rate'] - expected_overall) < 0.5, \
            f"Expected overall fill rate {expected_overall}, got {data['summary']['overall_fill_rate']}"
        
        print(f"PASS: Overall fill rate formula verified ({data['summary']['overall_fill_rate']}%)")
    
    def test_detail_sorted_by_lowest_fill_rate(self):
        """Test that detail table is sorted by lowest fill rate first (most critical)"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate")
        data = response.json()
        
        if len(data['detail']) > 1:
            fill_rates = [d['fill_rate'] for d in data['detail'][:20]]
            assert fill_rates == sorted(fill_rates), "Detail not sorted by fill rate ascending"
        
        print("PASS: Detail table sorted by lowest fill rate first")
    
    def test_date_filter_accepted(self):
        """Test that date filter parameters are accepted"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate?start_date=2026-01-01&end_date=2026-03-31")
        assert response.status_code == 200, f"Date filter failed: {response.status_code}"
        print("PASS: Date filter parameters accepted")
    
    def test_channel_filter_accepted(self):
        """Test that channel filter parameter is accepted"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate?channels=Retail")
        assert response.status_code == 200, f"Channel filter failed: {response.status_code}"
        print("PASS: Channel filter parameter accepted")
    
    def test_region_filter_accepted(self):
        """Test that region filter parameter is accepted"""
        response = requests.get(f"{BASE_URL}/api/analytics/planogram-fill-rate?regions=North")
        assert response.status_code == 200, f"Region filter failed: {response.status_code}"
        print("PASS: Region filter parameter accepted")


class TestRegressionExistingEndpoints:
    """Regression tests for existing endpoints"""
    
    def test_doh_endpoint_still_works(self):
        """Test that DOH Analysis endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh")
        assert response.status_code == 200, f"DOH endpoint failed: {response.status_code}"
        data = response.json()
        assert 'summary' in data, "DOH response missing summary"
        print("PASS: DOH Analysis endpoint still works (regression)")
    
    def test_replenishment_endpoint_still_works(self):
        """Test that Replenishment Planner endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment")
        assert response.status_code == 200, f"Replenishment endpoint failed: {response.status_code}"
        data = response.json()
        assert 'summary' in data, "Replenishment response missing summary"
        print("PASS: Replenishment Planner endpoint still works (regression)")
    
    def test_stock_out_endpoint_still_works(self):
        """Test that Stock-Out Analysis endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out")
        assert response.status_code == 200, f"Stock-out endpoint failed: {response.status_code}"
        data = response.json()
        assert 'summary' in data, "Stock-out response missing summary"
        print("PASS: Stock-Out Analysis endpoint still works (regression)")
    
    def test_filter_options_endpoint_still_works(self):
        """Test that filter options endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200, f"Filter options endpoint failed: {response.status_code}"
        data = response.json()
        assert 'categories' in data, "Filter options missing categories"
        assert 'channels' in data, "Filter options missing channels"
        assert 'regions' in data, "Filter options missing regions"
        print("PASS: Filter options endpoint still works (regression)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
