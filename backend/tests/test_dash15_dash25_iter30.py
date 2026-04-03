"""
Test DASH-15: Revenue Trend Line Chart on Executive Dashboard
Test DASH-25: Offline Detection UI (global banner when network drops)

Iteration 30 - Testing new features:
1. Revenue Trend API endpoint (/api/analytics/executive-revenue-trend)
2. Offline Banner component in App.js
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDASH15RevenueTrendAPI:
    """DASH-15: Revenue Trend Line Chart API Tests"""
    
    def test_revenue_trend_endpoint_exists(self):
        """Test that the revenue trend endpoint exists and returns 200"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-revenue-trend")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: Revenue trend endpoint exists and returns 200")
    
    def test_revenue_trend_returns_correct_structure(self):
        """Test that the response has labels, revenue, and units arrays"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-revenue-trend")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields exist
        assert "labels" in data, "Missing 'labels' field in response"
        assert "revenue" in data, "Missing 'revenue' field in response"
        assert "units" in data, "Missing 'units' field in response"
        
        # Check they are arrays
        assert isinstance(data["labels"], list), "'labels' should be a list"
        assert isinstance(data["revenue"], list), "'revenue' should be a list"
        assert isinstance(data["units"], list), "'units' should be a list"
        
        print(f"PASS: Response has correct structure - labels: {len(data['labels'])}, revenue: {len(data['revenue'])}, units: {len(data['units'])}")
    
    def test_revenue_trend_arrays_same_length(self):
        """Test that all arrays have the same length"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-revenue-trend")
        assert response.status_code == 200
        data = response.json()
        
        labels_len = len(data["labels"])
        revenue_len = len(data["revenue"])
        units_len = len(data["units"])
        
        assert labels_len == revenue_len == units_len, \
            f"Array lengths don't match: labels={labels_len}, revenue={revenue_len}, units={units_len}"
        
        print(f"PASS: All arrays have same length ({labels_len})")
    
    def test_revenue_trend_has_data(self):
        """Test that the endpoint returns actual data (not empty)"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-revenue-trend")
        assert response.status_code == 200
        data = response.json()
        
        # Should have data if daily_sales is uploaded
        assert len(data["labels"]) > 0, "Expected non-empty labels array"
        assert len(data["revenue"]) > 0, "Expected non-empty revenue array"
        assert len(data["units"]) > 0, "Expected non-empty units array"
        
        print(f"PASS: Endpoint returns data - {len(data['labels'])} data points")
    
    def test_revenue_trend_labels_are_dates(self):
        """Test that labels are valid date strings (YYYY-MM-DD format)"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-revenue-trend")
        assert response.status_code == 200
        data = response.json()
        
        if len(data["labels"]) > 0:
            # Check first and last labels are date format
            import re
            date_pattern = r'^\d{4}-\d{2}-\d{2}$'
            
            first_label = data["labels"][0]
            last_label = data["labels"][-1]
            
            assert re.match(date_pattern, first_label), f"First label '{first_label}' is not YYYY-MM-DD format"
            assert re.match(date_pattern, last_label), f"Last label '{last_label}' is not YYYY-MM-DD format"
            
            print(f"PASS: Labels are valid dates - range: {first_label} to {last_label}")
    
    def test_revenue_trend_revenue_values_numeric(self):
        """Test that revenue values are numeric"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-revenue-trend")
        assert response.status_code == 200
        data = response.json()
        
        if len(data["revenue"]) > 0:
            for i, val in enumerate(data["revenue"][:5]):  # Check first 5
                assert isinstance(val, (int, float)), f"Revenue value at index {i} is not numeric: {val}"
            
            total_revenue = sum(data["revenue"])
            print(f"PASS: Revenue values are numeric - total: {total_revenue:,.2f}")
    
    def test_revenue_trend_units_values_numeric(self):
        """Test that units values are numeric (integers)"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-revenue-trend")
        assert response.status_code == 200
        data = response.json()
        
        if len(data["units"]) > 0:
            for i, val in enumerate(data["units"][:5]):  # Check first 5
                assert isinstance(val, (int, float)), f"Units value at index {i} is not numeric: {val}"
            
            total_units = sum(data["units"])
            print(f"PASS: Units values are numeric - total: {total_units:,}")
    
    def test_revenue_trend_with_date_filter(self):
        """Test that date filters work correctly"""
        # First get all data to find valid date range
        response = requests.get(f"{BASE_URL}/api/analytics/executive-revenue-trend")
        assert response.status_code == 200
        data = response.json()
        
        if len(data["labels"]) >= 7:
            # Use first 7 days as filter
            start_date = data["labels"][0]
            end_date = data["labels"][6]
            
            filtered_response = requests.get(
                f"{BASE_URL}/api/analytics/executive-revenue-trend",
                params={"start_date": start_date, "end_date": end_date}
            )
            assert filtered_response.status_code == 200
            filtered_data = filtered_response.json()
            
            # Should have 7 or fewer data points
            assert len(filtered_data["labels"]) <= 7, \
                f"Expected <= 7 data points, got {len(filtered_data['labels'])}"
            
            print(f"PASS: Date filter works - filtered to {len(filtered_data['labels'])} data points")
    
    def test_revenue_trend_with_channel_filter(self):
        """Test that channel filter parameter is accepted"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-revenue-trend",
            params={"channels": "Online"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return valid structure even if no data matches
        assert "labels" in data
        assert "revenue" in data
        assert "units" in data
        
        print(f"PASS: Channel filter accepted - returned {len(data['labels'])} data points")
    
    def test_revenue_trend_with_region_filter(self):
        """Test that region filter parameter is accepted"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-revenue-trend",
            params={"regions": "North"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "labels" in data
        assert "revenue" in data
        assert "units" in data
        
        print(f"PASS: Region filter accepted - returned {len(data['labels'])} data points")
    
    def test_revenue_trend_with_category_filter(self):
        """Test that category filter parameter is accepted"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-revenue-trend",
            params={"categories": "Pants"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "labels" in data
        assert "revenue" in data
        assert "units" in data
        
        print(f"PASS: Category filter accepted - returned {len(data['labels'])} data points")


class TestExecutiveDashboardIntegration:
    """Test Executive Dashboard loads with all sections including Revenue Trend"""
    
    def test_executive_dashboard_endpoint(self):
        """Test that executive dashboard endpoint returns data"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Check for key sections
        assert "health_score" in data or "error" in data, "Missing health_score or error"
        
        if "error" not in data:
            assert "modules" in data, "Missing modules section"
            assert "alerts" in data, "Missing alerts section"
            print(f"PASS: Executive dashboard returns data - health_score: {data.get('health_score', 'N/A')}")
        else:
            print(f"INFO: Executive dashboard returned error (expected if no data): {data.get('error')}")
    
    def test_executive_kpis_endpoint(self):
        """Test that executive KPIs endpoint returns data"""
        response = requests.get(f"{BASE_URL}/api/analytics/executive-kpis")
        assert response.status_code == 200
        data = response.json()
        
        # Check for key KPI fields
        assert "revenue" in data, "Missing revenue field"
        assert "units_sold" in data, "Missing units_sold field"
        assert "wow" in data, "Missing wow (week-over-week) field"
        assert "yoy" in data, "Missing yoy (year-over-year) field"
        
        print(f"PASS: Executive KPIs endpoint works - revenue: {data.get('revenue', 0):,.2f}, units: {data.get('units_sold', 0):,}")
    
    def test_all_executive_endpoints_together(self):
        """Test that all three executive endpoints work together (as frontend does)"""
        # This mimics what ExecutiveDashboard.js does in fetchData()
        dashboard_resp = requests.get(f"{BASE_URL}/api/analytics/executive-dashboard")
        kpi_resp = requests.get(f"{BASE_URL}/api/analytics/executive-kpis")
        trend_resp = requests.get(f"{BASE_URL}/api/analytics/executive-revenue-trend")
        
        assert dashboard_resp.status_code == 200, f"Dashboard failed: {dashboard_resp.status_code}"
        assert kpi_resp.status_code == 200, f"KPIs failed: {kpi_resp.status_code}"
        assert trend_resp.status_code == 200, f"Trend failed: {trend_resp.status_code}"
        
        trend_data = trend_resp.json()
        print(f"PASS: All 3 executive endpoints work together - trend has {len(trend_data.get('labels', []))} data points")


class TestDASH25OfflineBannerBackend:
    """DASH-25: Offline Detection - Backend health check for connectivity testing"""
    
    def test_api_root_accessible(self):
        """Test that API root is accessible (used for online detection)"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data, "Missing message in API root response"
        print(f"PASS: API root accessible - message: {data.get('message')}")
    
    def test_upload_status_accessible(self):
        """Test that upload status endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/upload/status")
        assert response.status_code == 200
        
        print("PASS: Upload status endpoint accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
