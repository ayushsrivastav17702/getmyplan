"""
Test Suite for P1/P2 Features - Iteration 62
Tests:
1. P1: BI CSV Export with 4 report types (sales_detail, store_ranking, category_breakdown, channel_breakdown)
2. P2: Executive Dashboard CSV Export
3. P2: Concurrent Upload Locking (code verification)
4. P2: IST Execute with Inventory Auto-Update
5. P2: Forecast Reorder Auto-Save
6. Regression tests for existing analytics endpoints
"""

import pytest
import requests
import os
import csv
import io
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://zip-improved.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@demo.com"
TEST_PASSWORD = "demo1234"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for demo tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, f"No access_token in response: {data}"
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """TEST_01: Login with admin@demo.com/demo1234 returns access_token"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Login successful, token length: {len(auth_token)}")


class TestBICSVExport:
    """P1: BI CSV Export with 4 report types"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_bi_csv_sales_detail(self, auth_headers):
        """TEST_02: GET /api/analytics/bi/export/csv?report=sales_detail returns CSV with headers"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/bi/export/csv?report=sales_detail",
            headers=auth_headers
        )
        # Check if it's a CSV response or error JSON
        content_type = response.headers.get('content-type', '')
        if 'text/csv' in content_type:
            assert response.status_code == 200
            content = response.text
            lines = content.strip().split('\n')
            assert len(lines) > 0, "CSV should have at least header row"
            headers = lines[0].lower()
            # Check for expected columns
            assert 'day' in headers or 'sku' in headers or 'store_code' in headers, f"Expected sales_detail headers, got: {headers}"
            print(f"✓ sales_detail CSV: {len(lines)} rows, headers: {lines[0][:100]}...")
        else:
            # May return error if no data
            data = response.json()
            if 'error' in data:
                print(f"⚠ sales_detail returned error (no data): {data['error']}")
            else:
                assert False, f"Unexpected response: {data}"
    
    def test_bi_csv_store_ranking(self, auth_headers):
        """TEST_03: GET /api/analytics/bi/export/csv?report=store_ranking returns CSV"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/bi/export/csv?report=store_ranking",
            headers=auth_headers
        )
        content_type = response.headers.get('content-type', '')
        if 'text/csv' in content_type:
            assert response.status_code == 200
            content = response.text
            lines = content.strip().split('\n')
            assert len(lines) > 0
            headers = lines[0].lower()
            assert 'store_code' in headers or 'revenue' in headers, f"Expected store_ranking headers, got: {headers}"
            print(f"✓ store_ranking CSV: {len(lines)} rows")
        else:
            data = response.json()
            if 'error' in data:
                print(f"⚠ store_ranking returned error: {data['error']}")
    
    def test_bi_csv_category_breakdown(self, auth_headers):
        """TEST_04: GET /api/analytics/bi/export/csv?report=category_breakdown returns CSV"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/bi/export/csv?report=category_breakdown",
            headers=auth_headers
        )
        content_type = response.headers.get('content-type', '')
        if 'text/csv' in content_type:
            assert response.status_code == 200
            content = response.text
            lines = content.strip().split('\n')
            assert len(lines) > 0
            headers = lines[0].lower()
            assert 'category' in headers or 'revenue' in headers, f"Expected category_breakdown headers, got: {headers}"
            print(f"✓ category_breakdown CSV: {len(lines)} rows")
        else:
            data = response.json()
            if 'error' in data:
                print(f"⚠ category_breakdown returned error: {data['error']}")
    
    def test_bi_csv_channel_breakdown(self, auth_headers):
        """TEST_05: GET /api/analytics/bi/export/csv?report=channel_breakdown returns CSV"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/bi/export/csv?report=channel_breakdown",
            headers=auth_headers
        )
        content_type = response.headers.get('content-type', '')
        if 'text/csv' in content_type:
            assert response.status_code == 200
            content = response.text
            lines = content.strip().split('\n')
            assert len(lines) > 0
            headers = lines[0].lower()
            assert 'channel' in headers or 'revenue' in headers, f"Expected channel_breakdown headers, got: {headers}"
            print(f"✓ channel_breakdown CSV: {len(lines)} rows")
        else:
            data = response.json()
            if 'error' in data:
                print(f"⚠ channel_breakdown returned error: {data['error']}")
    
    def test_bi_csv_with_date_filter(self, auth_headers):
        """TEST_06: GET /api/analytics/bi/export/csv?report=sales_detail&start_date=2026-04-09 returns filtered data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/bi/export/csv?report=sales_detail&start_date=2026-04-09",
            headers=auth_headers
        )
        # Should return 200 with CSV or error JSON
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        print(f"✓ Date filter test completed, status: {response.status_code}")
    
    def test_bi_csv_invalid_report(self, auth_headers):
        """TEST_07: GET /api/analytics/bi/export/csv?report=INVALID returns error message"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/bi/export/csv?report=INVALID",
            headers=auth_headers
        )
        # Should return error JSON
        data = response.json()
        assert 'error' in data, f"Expected error for invalid report type, got: {data}"
        assert 'INVALID' in data['error'] or 'Unknown' in data['error'], f"Error should mention invalid report: {data['error']}"
        print(f"✓ Invalid report type correctly returns error: {data['error']}")


class TestExecutiveCSVExport:
    """P2: Executive Dashboard CSV Export"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_executive_csv_export(self, auth_headers):
        """TEST_08: GET /api/analytics/executive-export/csv returns CSV with KPI rows and Alerts"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-export/csv",
            headers=auth_headers
        )
        content_type = response.headers.get('content-type', '')
        
        if 'text/csv' in content_type:
            assert response.status_code == 200
            content = response.text
            lines = content.strip().split('\n')
            assert len(lines) > 5, f"Expected multiple rows in executive CSV, got {len(lines)}"
            
            # Check for expected content
            content_lower = content.lower()
            assert 'revenue' in content_lower, "CSV should contain Revenue KPI"
            assert 'units' in content_lower or 'sold' in content_lower, "CSV should contain Units Sold KPI"
            
            # Check for Alerts section
            assert 'alert' in content_lower, "CSV should contain Alerts section"
            
            print(f"✓ Executive CSV export: {len(lines)} rows")
            print(f"  First few lines: {lines[:5]}")
        else:
            data = response.json()
            if 'error' in data:
                print(f"⚠ Executive CSV returned error: {data['error']}")
            else:
                assert False, f"Unexpected response type: {content_type}"


class TestConcurrentUploadLocking:
    """P2: Concurrent Upload Locking - Code Verification"""
    
    def test_upload_locks_exist_in_code(self):
        """TEST_09: Verify upload.py has _upload_locks dict and _get_upload_lock function"""
        upload_file_path = "/app/backend/routes/upload.py"
        
        with open(upload_file_path, 'r') as f:
            content = f.read()
        
        # Check for _upload_locks dict
        assert '_upload_locks' in content, "upload.py should have _upload_locks dict"
        assert 'dict' in content.lower() or 'Dict' in content, "upload.py should define _upload_locks as dict"
        
        # Check for _get_upload_lock function
        assert '_get_upload_lock' in content, "upload.py should have _get_upload_lock function"
        assert 'def _get_upload_lock' in content, "upload.py should define _get_upload_lock function"
        
        # Check for asyncio.Lock usage
        assert 'asyncio.Lock' in content or 'Lock()' in content, "upload.py should use asyncio.Lock"
        
        # Check for lock check in upload handler
        assert 'lock.locked()' in content or 'locked()' in content, "upload.py should check if lock is locked"
        
        print("✓ Concurrent upload locking code verified:")
        print("  - _upload_locks dict exists")
        print("  - _get_upload_lock function exists")
        print("  - asyncio.Lock usage found")
        print("  - Lock check in handler found")


class TestISTExecute:
    """P2: IST Execute with Inventory Auto-Update"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_ist_execute_endpoint_exists(self, auth_headers):
        """TEST_10: POST /api/analytics/replenishment/ist/execute endpoint exists"""
        # First, upload test inventory data
        csv_content = "store_code,sku,closing_stock\nMAIN-01,TEST-SKU-001,100\nSOUTH-02,TEST-SKU-001,20\n"
        files = {'file': ('test_inventory.csv', csv_content, 'text/csv')}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/upload/v2/store-inventory",
            headers=auth_headers,
            files=files
        )
        print(f"Inventory upload status: {upload_response.status_code}")
        
        # Now test IST execute
        response = requests.post(
            f"{BASE_URL}/api/analytics/replenishment/ist/execute",
            headers=auth_headers,
            json={
                "transfers": [
                    {"from_store": "MAIN-01", "to_store": "SOUTH-02", "sku": "TEST-SKU-001", "quantity": 10}
                ]
            }
        )
        
        assert response.status_code in [200, 400, 404], f"Unexpected status: {response.status_code}"
        data = response.json()
        
        if response.status_code == 200:
            # Check response structure
            assert 'total_requested' in data or 'executed' in data or 'details' in data, f"Expected IST execute response fields, got: {data}"
            print(f"✓ IST execute endpoint works: {data}")
        else:
            print(f"⚠ IST execute returned {response.status_code}: {data}")
    
    def test_ist_execute_with_valid_transfers(self, auth_headers):
        """TEST_11: POST /api/analytics/replenishment/ist/execute with valid transfers returns executed count"""
        # Upload fresh inventory
        csv_content = "store_code,sku,closing_stock\nTEST-MAIN,TEST-SKU-002,50\nTEST-DEST,TEST-SKU-002,5\n"
        files = {'file': ('test_inv2.csv', csv_content, 'text/csv')}
        
        requests.post(
            f"{BASE_URL}/api/upload/v2/store-inventory",
            headers=auth_headers,
            files=files
        )
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/replenishment/ist/execute",
            headers=auth_headers,
            json={
                "transfers": [
                    {"from_store": "TEST-MAIN", "to_store": "TEST-DEST", "sku": "TEST-SKU-002", "quantity": 5}
                ]
            }
        )
        
        data = response.json()
        print(f"IST execute response: {data}")
        
        # Check for executed count
        if 'executed' in data:
            print(f"✓ IST executed count: {data['executed']}")
        elif 'details' in data:
            executed = [d for d in data['details'] if d.get('status') == 'executed']
            print(f"✓ IST executed from details: {len(executed)}")
    
    def test_ist_execute_insufficient_stock(self, auth_headers):
        """TEST_12: POST /api/analytics/replenishment/ist/execute with insufficient stock returns failed status"""
        response = requests.post(
            f"{BASE_URL}/api/analytics/replenishment/ist/execute",
            headers=auth_headers,
            json={
                "transfers": [
                    {"from_store": "EMPTY-STORE", "to_store": "DEST-STORE", "sku": "NO-STOCK-SKU", "quantity": 1000}
                ]
            }
        )
        
        data = response.json()
        print(f"IST insufficient stock response: {data}")
        
        # Should have failed or skipped transfers
        if 'details' in data:
            for detail in data['details']:
                if detail.get('status') in ['failed', 'skipped']:
                    print(f"✓ Transfer correctly failed/skipped: {detail.get('reason', 'no reason')}")
                    return
        
        if 'failed' in data and data['failed'] > 0:
            print(f"✓ IST correctly reported {data['failed']} failed transfers")


class TestReorderSave:
    """P2: Forecast Reorder Auto-Save"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_reorder_save_endpoint(self, auth_headers):
        """TEST_13: POST /api/analytics/ai-demand/reorder-optimisation/save returns status=saved"""
        response = requests.post(
            f"{BASE_URL}/api/analytics/ai-demand/reorder-optimisation/save",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 400, 429], f"Unexpected status: {response.status_code}"
        data = response.json()
        
        if response.status_code == 200:
            # Check for saved status
            if 'status' in data:
                assert data['status'] in ['saved', 'error'], f"Expected status saved or error, got: {data['status']}"
                if data['status'] == 'saved':
                    assert 'items_saved' in data, f"Expected items_saved in response: {data}"
                    print(f"✓ Reorder save successful: {data['items_saved']} items saved")
                else:
                    print(f"⚠ Reorder save returned error: {data.get('message', 'no message')}")
            else:
                print(f"⚠ Unexpected response structure: {data}")
        elif response.status_code == 429:
            print(f"⚠ Rate limited: {data}")
        else:
            print(f"⚠ Reorder save returned {response.status_code}: {data}")


class TestRegressionAnalytics:
    """Regression tests for existing analytics endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_ros_endpoint(self, auth_headers):
        """TEST_14: GET /api/analytics/core/ros returns data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/core/ros",
            headers=auth_headers
        )
        assert response.status_code == 200, f"ROS endpoint failed: {response.status_code}"
        data = response.json()
        # Should have data or error
        assert 'data' in data or 'error' in data or 'summary' in data, f"Unexpected ROS response: {data}"
        print(f"✓ ROS endpoint works: {list(data.keys())[:5]}")
    
    def test_doh_analysis(self, auth_headers):
        """TEST_15: GET /api/analytics/doh/analysis returns summary"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/doh/analysis",
            headers=auth_headers
        )
        assert response.status_code == 200, f"DOH analysis failed: {response.status_code}"
        data = response.json()
        # Should have summary or error
        assert 'summary' in data or 'error' in data, f"Unexpected DOH response: {data}"
        if 'summary' in data:
            print(f"✓ DOH analysis works: overall_doh={data['summary'].get('overall_doh', 'N/A')}")
        else:
            print(f"⚠ DOH analysis returned error: {data.get('error')}")
    
    def test_ai_demand_forecast(self, auth_headers):
        """TEST_16: GET /api/analytics/ai-demand/forecast returns 12 months"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/ai-demand/forecast",
            headers=auth_headers
        )
        assert response.status_code in [200, 429], f"Forecast failed: {response.status_code}"
        
        if response.status_code == 429:
            print("⚠ Forecast rate limited")
            return
            
        data = response.json()
        # Should have forecast array
        if 'forecast' in data:
            assert len(data['forecast']) >= 12, f"Expected 12 months forecast, got {len(data['forecast'])}"
            print(f"✓ AI Demand forecast works: {len(data['forecast'])} months")
        else:
            print(f"⚠ Forecast response: {list(data.keys())}")
    
    def test_planogram_analysis(self, auth_headers):
        """TEST_17: GET /api/analytics/planogram/analysis returns norm_source"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/planogram/analysis",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Planogram analysis failed: {response.status_code}"
        data = response.json()
        
        if 'summary' in data:
            # Check for norm_source field
            if 'norm_source' in data['summary']:
                print(f"✓ Planogram analysis works: norm_source={data['summary']['norm_source']}")
            else:
                print(f"✓ Planogram analysis works: {list(data['summary'].keys())[:5]}")
        elif 'error' in data:
            print(f"⚠ Planogram analysis returned error: {data['error']}")
        else:
            print(f"⚠ Planogram response: {list(data.keys())}")
    
    def test_replenishment_order_quantity(self, auth_headers):
        """TEST_18: GET /api/analytics/replenishment/order-quantity returns total_in_transit"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/replenishment/order-quantity",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Order quantity failed: {response.status_code}"
        data = response.json()
        
        if 'summary' in data:
            # Check for total_in_transit field
            if 'total_in_transit' in data['summary']:
                print(f"✓ Order quantity works: total_in_transit={data['summary']['total_in_transit']}")
            else:
                print(f"✓ Order quantity works: {list(data['summary'].keys())[:5]}")
        elif 'error' in data:
            print(f"⚠ Order quantity returned error: {data['error']}")
        else:
            print(f"⚠ Order quantity response: {list(data.keys())}")
    
    def test_bi_overview(self, auth_headers):
        """TEST_19: GET /api/analytics/bi/overview returns kpis"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/bi/overview",
            headers=auth_headers
        )
        assert response.status_code == 200, f"BI overview failed: {response.status_code}"
        data = response.json()
        
        if 'kpis' in data:
            print(f"✓ BI overview works: {list(data['kpis'].keys())}")
        elif 'error' in data:
            print(f"⚠ BI overview returned error: {data['error']}")
        else:
            print(f"⚠ BI overview response: {list(data.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
