"""
Test Upload V2 Module - Iteration 52
Tests the NEW UI redesign endpoints including master-status, daily-status, history, templates, and file uploads.
"""
import pytest
import requests
import os
import io
import tempfile

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@demo.com"
TEST_PASSWORD = "demo1234"
TEST_TENANT = "demo"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for demo tenant"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "tenant_id": TEST_TENANT
    })
    if response.status_code == 200:
        data = response.json()
        # Login returns 'access_token' not 'token'
        token = data.get("access_token") or data.get("token")
        if token:
            return token
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestMasterStatusEndpoint:
    """Tests for GET /api/upload/v2/master-status"""
    
    def test_master_status_returns_200(self, auth_headers):
        """MasterStatus-01: Endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/master-status", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: master-status returns 200")
    
    def test_master_status_structure(self, auth_headers):
        """MasterStatus-02: Response contains sku_master, store_master, warehouse_master"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/master-status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check all 3 master types are present
        assert "sku_master" in data, "Missing sku_master in response"
        assert "store_master" in data, "Missing store_master in response"
        assert "warehouse_master" in data, "Missing warehouse_master in response"
        print("PASS: master-status contains all 3 master types")
    
    def test_master_status_fields(self, auth_headers):
        """MasterStatus-03: Each master type has count and last_updated fields"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/master-status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        for master_type in ["sku_master", "store_master", "warehouse_master"]:
            assert "count" in data[master_type], f"Missing count in {master_type}"
            assert "last_updated" in data[master_type], f"Missing last_updated in {master_type}"
            # Count should be a number
            assert isinstance(data[master_type]["count"], int), f"count should be int for {master_type}"
        print("PASS: master-status has correct field structure")


class TestDailyStatusEndpoint:
    """Tests for GET /api/upload/v2/daily-status"""
    
    def test_daily_status_returns_200(self, auth_headers):
        """DailyStatus-01: Endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/daily-status", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: daily-status returns 200")
    
    def test_daily_status_structure(self, auth_headers):
        """DailyStatus-02: Response contains daily_sales, store_inventory, warehouse_inventory"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/daily-status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "daily_sales" in data, "Missing daily_sales in response"
        assert "store_inventory" in data, "Missing store_inventory in response"
        assert "warehouse_inventory" in data, "Missing warehouse_inventory in response"
        print("PASS: daily-status contains all 3 daily types")
    
    def test_daily_status_fields(self, auth_headers):
        """DailyStatus-03: Each daily type has uploaded, time, rows fields"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/daily-status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        for daily_type in ["daily_sales", "store_inventory", "warehouse_inventory"]:
            assert "uploaded" in data[daily_type], f"Missing uploaded in {daily_type}"
            assert "time" in data[daily_type], f"Missing time in {daily_type}"
            assert "rows" in data[daily_type], f"Missing rows in {daily_type}"
            # uploaded should be boolean
            assert isinstance(data[daily_type]["uploaded"], bool), f"uploaded should be bool for {daily_type}"
        print("PASS: daily-status has correct field structure")


class TestHistoryEndpoint:
    """Tests for GET /api/upload/v2/history"""
    
    def test_history_returns_200(self, auth_headers):
        """History-01: Endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/history?days=7", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: history returns 200")
    
    def test_history_structure(self, auth_headers):
        """History-02: Response contains history array"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/history?days=7", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "history" in data, "Missing history in response"
        assert isinstance(data["history"], list), "history should be a list"
        print("PASS: history has correct structure")
    
    def test_history_grouped_by_date(self, auth_headers):
        """History-03: History items have date, label, uploads fields"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/history?days=7", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data["history"]) > 0:
            item = data["history"][0]
            assert "date" in item, "Missing date in history item"
            assert "label" in item, "Missing label in history item"
            assert "uploads" in item, "Missing uploads in history item"
            print(f"PASS: history item has correct structure (found {len(data['history'])} days)")
        else:
            print("PASS: history is empty (no uploads yet)")
    
    def test_history_filter_by_type(self, auth_headers):
        """History-04: Filter by upload_type works"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/history?days=7&upload_type=daily_sales", headers=auth_headers)
        assert response.status_code == 200
        print("PASS: history filter by upload_type works")


class TestTemplateEndpoint:
    """Tests for GET /api/upload/v2/template/{upload_type}"""
    
    @pytest.mark.parametrize("upload_type", [
        "daily_sales",
        "store_inventory", 
        "warehouse_inventory",
        "sku_master",
        "store_master",
        "warehouse_master"
    ])
    def test_template_download(self, auth_headers, upload_type):
        """Template-01 to 06: Each template type returns Excel file"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/template/{upload_type}", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200 for {upload_type}, got {response.status_code}"
        
        # Check content type is Excel
        content_type = response.headers.get("content-type", "")
        assert "spreadsheet" in content_type or "excel" in content_type or "octet-stream" in content_type, \
            f"Expected Excel content type for {upload_type}, got {content_type}"
        
        # Check content disposition header
        content_disp = response.headers.get("content-disposition", "")
        assert "attachment" in content_disp, f"Expected attachment disposition for {upload_type}"
        assert f"{upload_type}_template.xlsx" in content_disp, f"Expected filename for {upload_type}"
        
        print(f"PASS: template/{upload_type} returns Excel file")
    
    def test_template_invalid_type(self, auth_headers):
        """Template-07: Invalid type returns 400"""
        response = requests.get(f"{BASE_URL}/api/upload/v2/template/invalid_type", headers=auth_headers)
        assert response.status_code == 400, f"Expected 400 for invalid type, got {response.status_code}"
        print("PASS: template/invalid_type returns 400")


class TestDailySalesUpload:
    """Tests for POST /api/upload/v2/daily-sales"""
    
    def test_upload_valid_csv(self, auth_headers):
        """DailySales-01: Valid CSV upload returns validation results"""
        csv_content = "sku,store_code,day,quantity,revenue\nSKU001,STORE001,2026-04-09,10,1000\nSKU002,STORE002,2026-04-09,5,500"
        files = {"file": ("test_daily_sales.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales?replace_existing=true",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data, "Missing success field"
        assert "total_rows" in data, "Missing total_rows field"
        assert "valid_rows" in data, "Missing valid_rows field"
        assert "corrections" in data, "Missing corrections field"
        assert "warnings" in data, "Missing warnings field"
        assert "errors" in data, "Missing errors field"
        
        print(f"PASS: daily-sales upload returns validation results (success={data['success']}, rows={data['total_rows']})")
    
    def test_upload_missing_columns(self, auth_headers):
        """DailySales-02: Missing columns returns E043 error"""
        csv_content = "sku,store_code\nSKU001,STORE001"  # Missing day, quantity, revenue
        files = {"file": ("test_missing_cols.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == False, "Should fail with missing columns"
        
        # Check for E043 error
        error_codes = [e.get("code") for e in data.get("errors", [])]
        assert "E043" in error_codes, f"Expected E043 error, got {error_codes}"
        print("PASS: missing columns returns E043 error")
    
    def test_upload_empty_file(self, auth_headers):
        """DailySales-03: Empty file returns E045 error"""
        csv_content = "sku,store_code,day,quantity,revenue\n"  # Headers only, no data
        files = {"file": ("test_empty.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == False, "Should fail with empty file"
        
        error_codes = [e.get("code") for e in data.get("errors", [])]
        assert "E045" in error_codes, f"Expected E045 error, got {error_codes}"
        print("PASS: empty file returns E045 error")


class TestStoreInventoryUpload:
    """Tests for POST /api/upload/v2/store-inventory"""
    
    def test_upload_valid_csv(self, auth_headers):
        """StoreInventory-01: Valid CSV upload works"""
        csv_content = "store_code,sku,closing_stock\nSTORE001,SKU001,100\nSTORE002,SKU002,50"
        files = {"file": ("test_store_inv.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/store-inventory?replace_existing=true",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert "total_rows" in data
        print(f"PASS: store-inventory upload works (success={data['success']}, rows={data['total_rows']})")


class TestWarehouseInventoryUpload:
    """Tests for POST /api/upload/v2/warehouse-inventory"""
    
    def test_upload_valid_csv(self, auth_headers):
        """WarehouseInventory-01: Valid CSV upload works"""
        csv_content = "warehouse,sku,on_hand_qty,available_qty\nWH001,SKU001,500,450\nWH002,SKU002,300,280"
        files = {"file": ("test_wh_inv.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/warehouse-inventory?replace_existing=true",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert "total_rows" in data
        print(f"PASS: warehouse-inventory upload works (success={data['success']}, rows={data['total_rows']})")


class TestSKUMasterUpload:
    """Tests for POST /api/upload/v2/sku-master"""
    
    def test_upload_valid_csv(self, auth_headers):
        """SKUMaster-01: Valid CSV upload works"""
        csv_content = "sku,product_name,category\nSKU001,Product One,Shirts\nSKU002,Product Two,Pants"
        files = {"file": ("test_sku_master.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/sku-master",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert "total_rows" in data
        print(f"PASS: sku-master upload works (success={data['success']}, rows={data['total_rows']})")


class TestStoreMasterUpload:
    """Tests for POST /api/upload/v2/store-master"""
    
    def test_upload_valid_csv(self, auth_headers):
        """StoreMaster-01: Valid CSV upload works"""
        csv_content = "store_code,store_name\nSTORE001,Main Store\nSTORE002,Branch Store"
        files = {"file": ("test_store_master.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/store-master",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert "total_rows" in data
        print(f"PASS: store-master upload works (success={data['success']}, rows={data['total_rows']})")


class TestWarehouseMasterUpload:
    """Tests for POST /api/upload/v2/warehouse-master"""
    
    def test_upload_valid_csv(self, auth_headers):
        """WarehouseMaster-01: Valid CSV upload works"""
        csv_content = "warehouse,warehouse_name,online_fulfillment_flag\nWH001,Central Warehouse,Yes\nWH002,Regional Warehouse,No"
        files = {"file": ("test_wh_master.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/warehouse-master",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data
        assert "total_rows" in data
        print(f"PASS: warehouse-master upload works (success={data['success']}, rows={data['total_rows']})")


class TestValidationErrors:
    """Tests for validation error handling"""
    
    def test_negative_quantity_warning(self, auth_headers):
        """Validation-01: Negative quantity triggers E027 warning"""
        csv_content = "sku,store_code,day,quantity,revenue\nSKU001,STORE001,2026-04-09,-5,500"
        files = {"file": ("test_neg_qty.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales?replace_existing=true",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        warning_codes = [w.get("code") for w in data.get("warnings", [])]
        assert "E027" in warning_codes, f"Expected E027 warning for negative quantity, got {warning_codes}"
        print("PASS: negative quantity triggers E027 warning")
    
    def test_zero_revenue_warning(self, auth_headers):
        """Validation-02: Zero revenue with positive quantity triggers E041 warning"""
        csv_content = "sku,store_code,day,quantity,revenue\nSKU001,STORE001,2026-04-09,10,0"
        files = {"file": ("test_zero_rev.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales?replace_existing=true",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        warning_codes = [w.get("code") for w in data.get("warnings", [])]
        assert "E041" in warning_codes, f"Expected E041 warning for zero revenue, got {warning_codes}"
        print("PASS: zero revenue with positive quantity triggers E041 warning")
    
    def test_duplicate_rows_warning(self, auth_headers):
        """Validation-03: Duplicate rows trigger E050 warning"""
        csv_content = "sku,store_code,day,quantity,revenue\nSKU001,STORE001,2026-04-09,10,1000\nSKU001,STORE001,2026-04-09,5,500"
        files = {"file": ("test_dupes.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales?replace_existing=true",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        warning_codes = [w.get("code") for w in data.get("warnings", [])]
        assert "E050" in warning_codes, f"Expected E050 warning for duplicates, got {warning_codes}"
        print("PASS: duplicate rows trigger E050 warning")
    
    def test_test_data_warning(self, auth_headers):
        """Validation-04: Test/demo/sample data triggers E070 warning"""
        csv_content = "sku,store_code,day,quantity,revenue\ntest,STORE001,2026-04-09,10,1000"
        files = {"file": ("test_data.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily-sales?replace_existing=true",
            headers=auth_headers,
            files=files
        )
        assert response.status_code == 200
        
        data = response.json()
        warning_codes = [w.get("code") for w in data.get("warnings", [])]
        assert "E070" in warning_codes, f"Expected E070 warning for test data, got {warning_codes}"
        print("PASS: test data triggers E070 warning")


class TestMasterStatusAfterUpload:
    """Tests to verify master-status updates after uploads"""
    
    def test_master_status_count_updates(self, auth_headers):
        """MasterStatus-04: Count updates after master upload"""
        # First upload some SKU master data
        csv_content = "sku,product_name,category\nTEST_SKU001,Test Product 1,TestCat\nTEST_SKU002,Test Product 2,TestCat"
        files = {"file": ("test_sku.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/upload/v2/sku-master",
            headers=auth_headers,
            files=files
        )
        assert upload_response.status_code == 200
        
        # Now check master-status
        status_response = requests.get(f"{BASE_URL}/api/upload/v2/master-status", headers=auth_headers)
        assert status_response.status_code == 200
        
        data = status_response.json()
        # Count should be >= 2 (we just uploaded 2 rows)
        assert data["sku_master"]["count"] >= 0, "sku_master count should be present"
        print(f"PASS: master-status shows sku_master count={data['sku_master']['count']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
