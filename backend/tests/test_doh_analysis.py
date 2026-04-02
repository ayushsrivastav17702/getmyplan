"""
DOH (Days on Hand) Analysis API Tests - Iteration 11
Tests the /api/analytics/doh endpoint with PRD formulas:
- DOH(store,sku) = Inventory / Daily ROS
- Channel DOH = Sum(DOH x Inv) / Sum(Inv)
- Classification: Optimal ±20%, Overstocked >120%, Understocked <80%
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDOHAnalysisAPI:
    """DOH Analysis endpoint tests"""
    
    def test_doh_endpoint_returns_200(self):
        """Test that /api/analytics/doh returns 200"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: /api/analytics/doh returns 200")
    
    def test_doh_response_has_summary(self):
        """Test that response has summary field with all required KPIs"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh")
        data = response.json()
        
        assert 'summary' in data, "Response missing 'summary' field"
        summary = data['summary']
        
        required_fields = [
            'overall_doh', 'ideal_doh', 'total_store_skus',
            'optimal_count', 'overstocked_count', 'understocked_count',
            'stockedout_count', 'snapshot_date'
        ]
        for field in required_fields:
            assert field in summary, f"Summary missing '{field}' field"
        
        print(f"PASS: Summary has all required fields: {required_fields}")
    
    def test_doh_response_has_store_data(self):
        """Test that response has store_data array with required columns"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh")
        data = response.json()
        
        assert 'store_data' in data, "Response missing 'store_data' field"
        assert isinstance(data['store_data'], list), "store_data should be a list"
        
        if len(data['store_data']) > 0:
            store = data['store_data'][0]
            required_cols = ['store_code', 'total_inventory', 'doh', 'sku_count', 'status', 'ideal_doh']
            for col in required_cols:
                assert col in store, f"store_data missing '{col}' column"
            print(f"PASS: store_data has all required columns: {required_cols}")
        else:
            print("WARN: store_data is empty")
    
    def test_doh_response_has_category_data(self):
        """Test that response has category_data array"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh")
        data = response.json()
        
        assert 'category_data' in data, "Response missing 'category_data' field"
        assert isinstance(data['category_data'], list), "category_data should be a list"
        print(f"PASS: category_data present (length: {len(data['category_data'])})")
    
    def test_doh_response_has_trend_data(self):
        """Test that response has trend_data array with weekly data"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh")
        data = response.json()
        
        assert 'trend_data' in data, "Response missing 'trend_data' field"
        assert isinstance(data['trend_data'], list), "trend_data should be a list"
        
        if len(data['trend_data']) > 0:
            trend = data['trend_data'][0]
            required_cols = ['week_label', 'doh', 'stockout_count']
            for col in required_cols:
                assert col in trend, f"trend_data missing '{col}' column"
            print(f"PASS: trend_data has all required columns: {required_cols}")
        else:
            print("WARN: trend_data is empty")
    
    def test_doh_response_has_detail(self):
        """Test that response has detail array with store-SKU level data"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh")
        data = response.json()
        
        assert 'detail' in data, "Response missing 'detail' field"
        assert isinstance(data['detail'], list), "detail should be a list"
        
        if len(data['detail']) > 0:
            detail = data['detail'][0]
            required_cols = ['store_code', 'sku', 'style', 'soh', 'ros', 'doh', 'status', 'ideal_doh']
            for col in required_cols:
                assert col in detail, f"detail missing '{col}' column"
            print(f"PASS: detail has all required columns: {required_cols}")
        else:
            print("WARN: detail is empty")
    
    def test_doh_response_has_recommendations(self):
        """Test that response has recommendations array"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh")
        data = response.json()
        
        assert 'recommendations' in data, "Response missing 'recommendations' field"
        assert isinstance(data['recommendations'], list), "recommendations should be a list"
        
        if len(data['recommendations']) > 0:
            rec = data['recommendations'][0]
            required_cols = ['priority', 'title', 'description']
            for col in required_cols:
                assert col in rec, f"recommendations missing '{col}' column"
            print(f"PASS: recommendations has all required columns: {required_cols}")
        else:
            print("INFO: No recommendations (may be expected if all optimal)")
    
    def test_ideal_doh_parameter_default(self):
        """Test that default ideal_doh is 9"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh")
        data = response.json()
        
        assert data['summary']['ideal_doh'] == 9, f"Expected default ideal_doh=9, got {data['summary']['ideal_doh']}"
        print("PASS: Default ideal_doh is 9")
    
    def test_ideal_doh_parameter_custom(self):
        """Test that ideal_doh query param works correctly"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh?ideal_doh=15")
        data = response.json()
        
        assert data['summary']['ideal_doh'] == 15, f"Expected ideal_doh=15, got {data['summary']['ideal_doh']}"
        
        # Check store_data also has updated ideal_doh
        if len(data['store_data']) > 0:
            assert data['store_data'][0]['ideal_doh'] == 15, "store_data should have ideal_doh=15"
        
        print("PASS: ideal_doh=15 parameter works correctly")
    
    def test_ideal_doh_recalculates_classification(self):
        """Test that changing ideal_doh recalculates classification counts"""
        # Get with default ideal_doh=9
        response1 = requests.get(f"{BASE_URL}/api/analytics/doh?ideal_doh=9")
        data1 = response1.json()
        
        # Get with higher ideal_doh=30
        response2 = requests.get(f"{BASE_URL}/api/analytics/doh?ideal_doh=30")
        data2 = response2.json()
        
        # With higher ideal_doh, more items should be understocked (DOH < 80% of 30 = 24)
        # and fewer should be overstocked (DOH > 120% of 30 = 36)
        assert data2['summary']['understocked_count'] >= data1['summary']['understocked_count'], \
            "Higher ideal_doh should result in more understocked items"
        
        print(f"PASS: Classification recalculates with ideal_doh change")
        print(f"  ideal_doh=9: optimal={data1['summary']['optimal_count']}, over={data1['summary']['overstocked_count']}, under={data1['summary']['understocked_count']}")
        print(f"  ideal_doh=30: optimal={data2['summary']['optimal_count']}, over={data2['summary']['overstocked_count']}, under={data2['summary']['understocked_count']}")
    
    def test_status_values_are_valid(self):
        """Test that status values are valid classification labels"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh")
        data = response.json()
        
        valid_statuses = {'OPTIMAL', 'OVERSTOCKED', 'UNDERSTOCKED', 'STOCKED_OUT', 'NO_SALES'}
        
        # Check store_data statuses
        for store in data.get('store_data', []):
            assert store['status'] in valid_statuses, f"Invalid status: {store['status']}"
        
        # Check detail statuses
        for detail in data.get('detail', []):
            assert detail['status'] in valid_statuses, f"Invalid status: {detail['status']}"
        
        print(f"PASS: All status values are valid: {valid_statuses}")
    
    def test_summary_values_are_valid_numbers(self):
        """Test that summary values are valid numbers with correct ranges"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh")
        data = response.json()
        summary = data['summary']
        
        assert isinstance(summary['overall_doh'], (int, float)), "overall_doh should be a number"
        assert summary['overall_doh'] >= 0, "overall_doh should be >= 0"
        
        assert isinstance(summary['total_store_skus'], int), "total_store_skus should be an integer"
        assert summary['total_store_skus'] >= 0, "total_store_skus should be >= 0"
        
        assert isinstance(summary['optimal_count'], int), "optimal_count should be an integer"
        assert isinstance(summary['overstocked_count'], int), "overstocked_count should be an integer"
        assert isinstance(summary['understocked_count'], int), "understocked_count should be an integer"
        assert isinstance(summary['stockedout_count'], int), "stockedout_count should be an integer"
        
        print("PASS: Summary values are valid numbers with correct ranges")
    
    def test_detail_sorted_by_lowest_doh(self):
        """Test that detail table is sorted by lowest DOH first"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh")
        data = response.json()
        
        detail = data.get('detail', [])
        if len(detail) > 1:
            # Check first few items have lower DOH than later items
            for i in range(min(5, len(detail) - 1)):
                assert detail[i]['doh'] <= detail[i + 1]['doh'], \
                    f"Detail not sorted by DOH: {detail[i]['doh']} > {detail[i + 1]['doh']}"
            print("PASS: Detail table is sorted by lowest DOH first")
        else:
            print("WARN: Not enough detail items to verify sorting")


class TestDOHAnalysisFilters:
    """Test filter parameters for DOH Analysis"""
    
    def test_date_filter(self):
        """Test that date filters work"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh?start_date=2026-03-01&end_date=2026-03-31")
        assert response.status_code == 200
        data = response.json()
        assert 'summary' in data or 'error' in data
        print("PASS: Date filter parameters accepted")
    
    def test_channel_filter(self):
        """Test that channel filter works"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh?channels=Online")
        assert response.status_code == 200
        data = response.json()
        assert 'summary' in data or 'error' in data
        print("PASS: Channel filter parameter accepted")
    
    def test_region_filter(self):
        """Test that region filter works"""
        response = requests.get(f"{BASE_URL}/api/analytics/doh?regions=North")
        assert response.status_code == 200
        data = response.json()
        assert 'summary' in data or 'error' in data
        print("PASS: Region filter parameter accepted")


class TestRegressionExistingEndpoints:
    """Regression tests for existing endpoints"""
    
    def test_stock_out_endpoint_still_works(self):
        """Test that /api/analytics/stock-out still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out")
        assert response.status_code == 200, f"stock-out endpoint failed: {response.status_code}"
        data = response.json()
        assert 'summary' in data or 'error' in data
        print("PASS: /api/analytics/stock-out still works (regression)")
    
    def test_replenishment_endpoint_still_works(self):
        """Test that /api/analytics/replenishment still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/replenishment")
        assert response.status_code == 200, f"replenishment endpoint failed: {response.status_code}"
        data = response.json()
        assert 'summary' in data or 'error' in data
        print("PASS: /api/analytics/replenishment still works (regression)")
    
    def test_filter_options_endpoint_still_works(self):
        """Test that /api/analytics/filter-options still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200, f"filter-options endpoint failed: {response.status_code}"
        data = response.json()
        assert 'categories' in data
        assert 'channels' in data
        assert 'regions' in data
        print("PASS: /api/analytics/filter-options still works (regression)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
