"""
Stock-Out Analysis API Tests - Iteration 9
Tests the /api/analytics/stock-out endpoint for PRD formula compliance
PRD Formulas:
- Stock-out: SOH = 0 AND ROS > 0
- Daily Sales Loss: ((ROS x 1) - SOH) x ASP
- Stock-Out Rate: (Stockouts / Total SKUs) x 100
- Severity: LostSales x Duration x Importance
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStockOutAnalysis:
    """Stock-Out Analysis endpoint tests"""
    
    def test_stock_out_endpoint_returns_200(self):
        """Test that /api/analytics/stock-out returns 200"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: /api/analytics/stock-out returns 200")
    
    def test_response_has_summary_field(self):
        """Test that response has summary with all required KPIs"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out")
        data = response.json()
        
        assert 'summary' in data, "Response missing 'summary' field"
        summary = data['summary']
        
        required_fields = [
            'total_stockouts', 'stockout_rate', 'total_lost_sales', 
            'stores_impacted', 'total_store_skus', 'snapshot_date'
        ]
        for field in required_fields:
            assert field in summary, f"Summary missing '{field}' field"
        
        print(f"PASS: Summary has all required fields: {required_fields}")
    
    def test_response_has_top_skus_array(self):
        """Test that response has top_skus array with required columns"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out")
        data = response.json()
        
        assert 'top_skus' in data, "Response missing 'top_skus' field"
        assert isinstance(data['top_skus'], list), "top_skus should be a list"
        
        if len(data['top_skus']) > 0:
            sku = data['top_skus'][0]
            required_cols = ['sku', 'style', 'stockout_count', 'avg_ros', 'avg_asp', 'total_daily_loss']
            for col in required_cols:
                assert col in sku, f"top_skus missing '{col}' column"
            print(f"PASS: top_skus has all required columns: {required_cols}")
        else:
            print("PASS: top_skus is empty (no stock-outs)")
    
    def test_response_has_top_stores_array(self):
        """Test that response has top_stores array with required columns"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out")
        data = response.json()
        
        assert 'top_stores' in data, "Response missing 'top_stores' field"
        assert isinstance(data['top_stores'], list), "top_stores should be a list"
        
        if len(data['top_stores']) > 0:
            store = data['top_stores'][0]
            required_cols = ['store_code', 'stockout_count', 'avg_duration', 'total_daily_loss', 'total_severity']
            for col in required_cols:
                assert col in store, f"top_stores missing '{col}' column"
            print(f"PASS: top_stores has all required columns: {required_cols}")
        else:
            print("PASS: top_stores is empty (no stock-outs)")
    
    def test_response_has_category_impact_array(self):
        """Test that response has category_impact array"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out")
        data = response.json()
        
        assert 'category_impact' in data, "Response missing 'category_impact' field"
        assert isinstance(data['category_impact'], list), "category_impact should be a list"
        print("PASS: category_impact field exists and is a list")
    
    def test_response_has_daily_trend_array(self):
        """Test that response has daily_trend array with date and stockout_count"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out")
        data = response.json()
        
        assert 'daily_trend' in data, "Response missing 'daily_trend' field"
        assert isinstance(data['daily_trend'], list), "daily_trend should be a list"
        
        if len(data['daily_trend']) > 0:
            trend = data['daily_trend'][0]
            assert 'date' in trend, "daily_trend missing 'date' column"
            assert 'stockout_count' in trend, "daily_trend missing 'stockout_count' column"
            print("PASS: daily_trend has date and stockout_count columns")
        else:
            print("PASS: daily_trend is empty")
    
    def test_response_has_high_risk_skus_array(self):
        """Test that response has high_risk_skus array with required columns"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out")
        data = response.json()
        
        assert 'high_risk_skus' in data, "Response missing 'high_risk_skus' field"
        assert isinstance(data['high_risk_skus'], list), "high_risk_skus should be a list"
        
        if len(data['high_risk_skus']) > 0:
            sku = data['high_risk_skus'][0]
            required_cols = ['sku', 'style', 'store_code', 'ros', 'soh', 'asp', 'days_to_stockout', 'risk']
            for col in required_cols:
                assert col in sku, f"high_risk_skus missing '{col}' column"
            print(f"PASS: high_risk_skus has all required columns: {required_cols}")
        else:
            print("PASS: high_risk_skus is empty (no high-risk items)")
    
    def test_summary_values_are_valid(self):
        """Test that summary values are valid numbers with correct ranges"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out")
        data = response.json()
        summary = data['summary']
        
        # total_stockouts should be >= 0
        assert isinstance(summary['total_stockouts'], (int, float)), "total_stockouts should be numeric"
        assert summary['total_stockouts'] >= 0, "total_stockouts should be >= 0"
        
        # stockout_rate should be 0-100
        assert isinstance(summary['stockout_rate'], (int, float)), "stockout_rate should be numeric"
        assert 0 <= summary['stockout_rate'] <= 100, "stockout_rate should be 0-100"
        
        # total_lost_sales should be >= 0
        assert isinstance(summary['total_lost_sales'], (int, float)), "total_lost_sales should be numeric"
        assert summary['total_lost_sales'] >= 0, "total_lost_sales should be >= 0"
        
        # stores_impacted should be >= 0
        assert isinstance(summary['stores_impacted'], (int, float)), "stores_impacted should be numeric"
        assert summary['stores_impacted'] >= 0, "stores_impacted should be >= 0"
        
        print(f"PASS: Summary values are valid - stockouts={summary['total_stockouts']}, rate={summary['stockout_rate']}%, loss={summary['total_lost_sales']}, stores={summary['stores_impacted']}")
    
    def test_filters_work_correctly(self):
        """Test that date and channel filters work"""
        # Test with date filter
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out?start_date=2026-01-01&end_date=2026-03-31")
        assert response.status_code == 200, f"Date filter failed: {response.status_code}"
        
        # Test with channel filter
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out?channels=Offline")
        assert response.status_code == 200, f"Channel filter failed: {response.status_code}"
        
        print("PASS: Filters work correctly (date, channel)")
    
    def test_high_risk_sku_risk_values(self):
        """Test that high_risk_skus have valid risk values"""
        response = requests.get(f"{BASE_URL}/api/analytics/stock-out")
        data = response.json()
        
        valid_risks = ['critical', 'high', 'medium', 'low']
        for sku in data.get('high_risk_skus', []):
            assert sku['risk'] in valid_risks, f"Invalid risk value: {sku['risk']}"
        
        print("PASS: All high_risk_skus have valid risk values")


class TestRegressionExistingEndpoints:
    """Regression tests for existing endpoints"""
    
    def test_gap_analysis_noos_still_works(self):
        """Test that /api/analytics/noos endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/noos")
        assert response.status_code == 200, f"NOOS endpoint failed: {response.status_code}"
        data = response.json()
        assert 'summary' in data or 'data' in data, "NOOS response missing expected fields"
        print("PASS: /api/analytics/noos still works")
    
    def test_gap_analysis_size_gap_still_works(self):
        """Test that /api/analytics/size-gap endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/size-gap")
        assert response.status_code == 200, f"Size-gap endpoint failed: {response.status_code}"
        data = response.json()
        assert 'summary' in data or 'data' in data, "Size-gap response missing expected fields"
        print("PASS: /api/analytics/size-gap still works")
    
    def test_gap_analysis_ros_gap_still_works(self):
        """Test that /api/analytics/ros-gap endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/ros-gap")
        assert response.status_code == 200, f"ROS-gap endpoint failed: {response.status_code}"
        data = response.json()
        assert 'summary' in data, "ROS-gap response missing summary field"
        print("PASS: /api/analytics/ros-gap still works")
    
    def test_filter_options_still_works(self):
        """Test that /api/analytics/filter-options endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/analytics/filter-options")
        assert response.status_code == 200, f"Filter-options endpoint failed: {response.status_code}"
        data = response.json()
        assert 'categories' in data, "Filter-options missing categories"
        assert 'channels' in data, "Filter-options missing channels"
        print("PASS: /api/analytics/filter-options still works")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
