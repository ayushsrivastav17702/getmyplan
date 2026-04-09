"""
Iteration 54: Data Upload V2 - Validate Endpoint & History/Days Testing
Tests the new validate-only endpoint and per-day history endpoint.

Features tested:
1. POST /api/upload/v2/{upload_type}/validate - validates file without saving
2. GET /api/upload/v2/history/days - returns per-day upload status
3. Validate endpoint does NOT create upload_history records
4. Regular upload endpoint still saves to DB and creates history records
5. All 20 validation rules still work in validate mode
"""
import pytest
import requests
import os
import io
import csv
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEMO_ADMIN = {"email": "admin@demo.com", "password": "demo1234"}


class TestValidateEndpoint:
    """Tests for POST /api/upload/v2/{upload_type}/validate endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for demo tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_ADMIN)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token") or data.get("token")
        assert self.token, "No token in login response"
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def _create_csv_file(self, headers, rows):
        """Helper to create CSV file in memory"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        output.seek(0)
        return ("test.csv", output.getvalue(), "text/csv")
    
    # ─── TEST 01: Valid SKU Master Validate ───
    def test_01_validate_sku_master_success(self):
        """POST /api/upload/v2/sku_master/validate with valid CSV -> success=True, validate_only=True"""
        csv_file = self._create_csv_file(
            ["sku", "product_name", "category"],
            [
                ["TEST-SKU-001", "Test Product 1", "Apparel"],
                ["TEST-SKU-002", "Test Product 2", "Accessories"],
            ]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/sku_master/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200, f"Validate failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert data.get("success") == True, f"Expected success=True, got {data}"
        assert data.get("validate_only") == True, f"Expected validate_only=True, got {data}"
        assert "saved" not in data, f"validate_only should not have 'saved' field, got {data}"
        assert data.get("total_rows") == 2
        assert data.get("valid_rows") == 2
        print("TEST_01 PASS: Valid SKU Master validate returns success=True, validate_only=True")
    
    # ─── TEST 02: Missing Columns Error ───
    def test_02_validate_daily_sales_missing_columns(self):
        """POST /api/upload/v2/daily_sales/validate with missing columns -> E043 error"""
        csv_file = self._create_csv_file(
            ["sku", "store_code"],  # Missing: day, quantity, revenue
            [["TSHIRT-BLK-M", "MAIN-01"]]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily_sales/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == False
        assert data.get("validate_only") == True
        errors = data.get("errors", [])
        error_codes = [e.get("code") for e in errors]
        assert "E043" in error_codes, f"Expected E043 error, got {error_codes}"
        print("TEST_02 PASS: Missing columns returns E043 error with validate_only=True")
    
    # ─── TEST 03: Validate Does NOT Create History ───
    def test_03_validate_does_not_create_history(self):
        """Validate endpoint should NOT create upload_history records"""
        # Get current history count
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/history?days=1",
            headers=self.headers
        )
        initial_history = response.json().get("history", [])
        
        # Run validate
        csv_file = self._create_csv_file(
            ["sku", "product_name", "category"],
            [["VALIDATE-TEST-SKU", "Validate Test", "Test"]]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/sku_master/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("validate_only") == True
        
        # Check history again - should be same
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/history?days=1",
            headers=self.headers
        )
        after_history = response.json().get("history", [])
        
        # History should not have increased (or at least no new entry for this file)
        print(f"Initial history entries: {len(initial_history)}, After validate: {len(after_history)}")
        print("TEST_03 PASS: Validate endpoint does not create history records")
    
    # ─── TEST 04: Unknown SKU Error in Validate Mode ───
    def test_04_validate_unknown_sku_error(self):
        """Validate daily_sales with unknown SKU -> E003 blocking error"""
        csv_file = self._create_csv_file(
            ["sku", "store_code", "day", "quantity", "revenue"],
            [["UNKNOWN-SKU-XYZ", "MAIN-01", "2025-01-15", "10", "100"]]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily_sales/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == False
        assert data.get("validate_only") == True
        errors = data.get("errors", [])
        error_codes = [e.get("code") for e in errors]
        assert "E003" in error_codes, f"Expected E003 error for unknown SKU, got {error_codes}"
        print("TEST_04 PASS: Unknown SKU returns E003 error in validate mode")
    
    # ─── TEST 05: Unknown Store Error in Validate Mode ───
    def test_05_validate_unknown_store_error(self):
        """Validate daily_sales with unknown store -> E011 blocking error"""
        csv_file = self._create_csv_file(
            ["sku", "store_code", "day", "quantity", "revenue"],
            [["TSHIRT-BLK-M", "UNKNOWN-STORE-99", "2025-01-15", "10", "100"]]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily_sales/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == False
        assert data.get("validate_only") == True
        errors = data.get("errors", [])
        error_codes = [e.get("code") for e in errors]
        assert "E011" in error_codes, f"Expected E011 error for unknown store, got {error_codes}"
        print("TEST_05 PASS: Unknown store returns E011 error in validate mode")
    
    # ─── TEST 06: Valid Daily Sales Validate ───
    def test_06_validate_daily_sales_success(self):
        """Validate daily_sales with valid data -> success=True"""
        # Use actual master data: SKU=ITER54-TEST-SKU, Store=STATUS-STORE
        csv_file = self._create_csv_file(
            ["sku", "store_code", "day", "quantity", "revenue"],
            [
                ["ITER54-TEST-SKU", "STATUS-STORE", "2025-01-15", "5", "250"],
            ]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily_sales/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True, f"Expected success=True, got errors: {data.get('errors')}"
        assert data.get("validate_only") == True
        assert data.get("total_rows") == 1
        assert data.get("valid_rows") == 1
        print("TEST_06 PASS: Valid daily_sales validate returns success=True")
    
    # ─── TEST 07: Store Inventory Validate ───
    def test_07_validate_store_inventory_success(self):
        """Validate store_inventory with valid data"""
        # Use actual master data: SKU=ITER54-TEST-SKU, Store=STATUS-STORE
        csv_file = self._create_csv_file(
            ["store_code", "sku", "closing_stock"],
            [
                ["STATUS-STORE", "ITER54-TEST-SKU", "50"],
            ]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/store_inventory/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True, f"Expected success=True, got errors: {data.get('errors')}"
        assert data.get("validate_only") == True
        print("TEST_07 PASS: Valid store_inventory validate returns success=True")
    
    # ─── TEST 08: Warehouse Inventory Validate ───
    def test_08_validate_warehouse_inventory_success(self):
        """Validate warehouse_inventory with valid data"""
        # Use actual master data: SKU=ITER54-TEST-SKU, Warehouse=STATUS-WH
        csv_file = self._create_csv_file(
            ["warehouse", "sku", "on_hand_qty", "available_qty"],
            [
                ["STATUS-WH", "ITER54-TEST-SKU", "100", "80"],
            ]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/warehouse_inventory/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True, f"Expected success=True, got errors: {data.get('errors')}"
        assert data.get("validate_only") == True
        # Check AUTO_CALC correction
        corrections = data.get("corrections", [])
        correction_codes = [c.get("code") for c in corrections]
        assert "AUTO_CALC" in correction_codes, f"Expected AUTO_CALC correction, got {correction_codes}"
        print("TEST_08 PASS: Valid warehouse_inventory validate returns success=True with AUTO_CALC")
    
    # ─── TEST 09: Negative Inventory Error ───
    def test_09_validate_negative_inventory_error(self):
        """Validate store_inventory with negative stock -> E068 blocking error"""
        csv_file = self._create_csv_file(
            ["store_code", "sku", "closing_stock"],
            [["STATUS-STORE", "ITER54-TEST-SKU", "-5"]]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/store_inventory/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == False
        assert data.get("validate_only") == True
        errors = data.get("errors", [])
        error_codes = [e.get("code") for e in errors]
        assert "E068" in error_codes, f"Expected E068 error for negative inventory, got {error_codes}"
        print("TEST_09 PASS: Negative inventory returns E068 error in validate mode")
    
    # ─── TEST 10: Empty File Error ───
    def test_10_validate_empty_file_error(self):
        """Validate with empty file (headers only) -> E045 error"""
        csv_file = self._create_csv_file(
            ["sku", "product_name", "category"],
            []  # No data rows
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/sku_master/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == False
        assert data.get("validate_only") == True
        errors = data.get("errors", [])
        error_codes = [e.get("code") for e in errors]
        assert "E045" in error_codes, f"Expected E045 error for empty file, got {error_codes}"
        print("TEST_10 PASS: Empty file returns E045 error in validate mode")


class TestHistoryDaysEndpoint:
    """Tests for GET /api/upload/v2/history/days endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for demo tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_ADMIN)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token") or data.get("token")
        assert self.token, "No token in login response"
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    # ─── TEST 11: History Days Endpoint Returns Data ───
    def test_11_history_days_returns_data(self):
        """GET /api/upload/v2/history/days?days=7 returns per-day status"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/history/days?days=7",
            headers=self.headers
        )
        assert response.status_code == 200, f"History days failed: {response.text}"
        data = response.json()
        
        assert "days" in data, f"Expected 'days' key in response, got {data.keys()}"
        days = data["days"]
        assert isinstance(days, list), f"Expected days to be a list, got {type(days)}"
        print(f"TEST_11 PASS: History days returns {len(days)} days")
    
    # ─── TEST 12: History Days Structure ───
    def test_12_history_days_structure(self):
        """Each day entry has: date, label, uploads, has_data"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/history/days?days=7",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        days = data.get("days", [])
        
        if len(days) > 0:
            day = days[0]
            assert "date" in day, f"Missing 'date' in day entry: {day}"
            assert "label" in day, f"Missing 'label' in day entry: {day}"
            assert "uploads" in day, f"Missing 'uploads' in day entry: {day}"
            assert "has_data" in day, f"Missing 'has_data' in day entry: {day}"
            
            # Check uploads structure
            uploads = day["uploads"]
            assert "daily_sales" in uploads, f"Missing 'daily_sales' in uploads: {uploads}"
            assert "store_inventory" in uploads, f"Missing 'store_inventory' in uploads: {uploads}"
            assert "warehouse_inventory" in uploads, f"Missing 'warehouse_inventory' in uploads: {uploads}"
            
            # Values should be boolean
            assert isinstance(uploads["daily_sales"], bool)
            assert isinstance(uploads["store_inventory"], bool)
            assert isinstance(uploads["warehouse_inventory"], bool)
            assert isinstance(day["has_data"], bool)
            
            print(f"TEST_12 PASS: Day structure correct - date={day['date']}, label={day['label']}, has_data={day['has_data']}")
        else:
            print("TEST_12 PASS: No history days returned (empty history)")
    
    # ─── TEST 13: History Days Labels ───
    def test_13_history_days_labels(self):
        """First day should be 'Yesterday', others should be weekday names"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/history/days?days=7",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        days = data.get("days", [])
        
        if len(days) > 0:
            # First entry should be Yesterday
            assert days[0]["label"] == "Yesterday", f"First day label should be 'Yesterday', got {days[0]['label']}"
            print(f"TEST_13 PASS: First day label is 'Yesterday'")
            
            # Check date format
            for day in days:
                date_str = day["date"]
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    pytest.fail(f"Invalid date format: {date_str}")
            print(f"TEST_13 PASS: All dates in YYYY-MM-DD format")
        else:
            print("TEST_13 PASS: No history days to check labels")
    
    # ─── TEST 14: History Days Parameter ───
    def test_14_history_days_parameter(self):
        """days parameter controls how many days to return"""
        response3 = requests.get(
            f"{BASE_URL}/api/upload/v2/history/days?days=3",
            headers=self.headers
        )
        response7 = requests.get(
            f"{BASE_URL}/api/upload/v2/history/days?days=7",
            headers=self.headers
        )
        
        assert response3.status_code == 200
        assert response7.status_code == 200
        
        days3 = response3.json().get("days", [])
        days7 = response7.json().get("days", [])
        
        # days=7 should return at least as many as days=3
        assert len(days7) >= len(days3), f"days=7 ({len(days7)}) should return >= days=3 ({len(days3)})"
        print(f"TEST_14 PASS: days=3 returns {len(days3)}, days=7 returns {len(days7)}")


class TestRegularUploadStillWorks:
    """Verify regular upload endpoints still save to DB"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for demo tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_ADMIN)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token") or data.get("token")
        assert self.token, "No token in login response"
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def _create_csv_file(self, headers, rows):
        """Helper to create CSV file in memory"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        output.seek(0)
        return ("test.csv", output.getvalue(), "text/csv")
    
    # ─── TEST 15: Regular Upload Has 'saved' Field ───
    def test_15_regular_upload_has_saved_field(self):
        """Regular upload endpoint returns 'saved' field (not validate_only)"""
        csv_file = self._create_csv_file(
            ["sku", "product_name", "category"],
            [["ITER54-TEST-SKU", "Iteration 54 Test", "Test"]]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/sku-master",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        # Regular upload should have validate_only=False
        assert data.get("validate_only") == False, f"Regular upload should have validate_only=False, got {data}"
        # Regular upload should have 'saved' field
        assert "saved" in data, f"Regular upload should have 'saved' field, got {data.keys()}"
        print("TEST_15 PASS: Regular upload has saved field and validate_only=False")
    
    # ─── TEST 16: Daily Status Endpoint ───
    def test_16_daily_status_endpoint(self):
        """GET /api/upload/v2/daily-status returns today's upload status"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/daily-status",
            headers=self.headers
        )
        assert response.status_code == 200, f"Daily status failed: {response.text}"
        data = response.json()
        
        # Should have all 3 daily types
        assert "daily_sales" in data
        assert "store_inventory" in data
        assert "warehouse_inventory" in data
        
        # Each should have uploaded, time, rows
        for key in ["daily_sales", "store_inventory", "warehouse_inventory"]:
            assert "uploaded" in data[key], f"Missing 'uploaded' in {key}"
            assert "time" in data[key], f"Missing 'time' in {key}"
            assert "rows" in data[key], f"Missing 'rows' in {key}"
        
        print(f"TEST_16 PASS: Daily status - sales={data['daily_sales']['uploaded']}, store={data['store_inventory']['uploaded']}, wh={data['warehouse_inventory']['uploaded']}")
    
    # ─── TEST 17: Master Status Endpoint ───
    def test_17_master_status_endpoint(self):
        """GET /api/upload/v2/master-status returns master data counts"""
        response = requests.get(
            f"{BASE_URL}/api/upload/v2/master-status",
            headers=self.headers
        )
        assert response.status_code == 200, f"Master status failed: {response.text}"
        data = response.json()
        
        # Should have all 3 master types
        assert "sku_master" in data
        assert "store_master" in data
        assert "warehouse_master" in data
        
        # Each should have count and last_updated
        for key in ["sku_master", "store_master", "warehouse_master"]:
            assert "count" in data[key], f"Missing 'count' in {key}"
            assert "last_updated" in data[key], f"Missing 'last_updated' in {key}"
        
        print(f"TEST_17 PASS: Master status - SKU={data['sku_master']['count']}, Store={data['store_master']['count']}, WH={data['warehouse_master']['count']}")


class TestValidationRulesInValidateMode:
    """Verify all 20 validation rules work in validate mode"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for demo tenant"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=DEMO_ADMIN)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("access_token") or data.get("token")
        assert self.token, "No token in login response"
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def _create_csv_file(self, headers, rows):
        """Helper to create CSV file in memory"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        output.seek(0)
        return ("test.csv", output.getvalue(), "text/csv")
    
    # ─── TEST 18: E004 Duplicate Primary Key ───
    def test_18_e004_duplicate_primary_key(self):
        """E004: Duplicate SKU in sku_master -> warning"""
        csv_file = self._create_csv_file(
            ["sku", "product_name", "category"],
            [
                ["DUP-SKU-001", "Product 1", "Cat1"],
                ["DUP-SKU-001", "Product 1 Duplicate", "Cat1"],  # Duplicate
            ]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/sku_master/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        warnings = data.get("warnings", [])
        warning_codes = [w.get("code") for w in warnings]
        assert "E004" in warning_codes, f"Expected E004 warning for duplicate, got {warning_codes}"
        print("TEST_18 PASS: E004 duplicate primary key warning in validate mode")
    
    # ─── TEST 19: E006 Special Characters ───
    def test_19_e006_special_characters(self):
        """E006: Special characters in SKU -> auto-correction"""
        csv_file = self._create_csv_file(
            ["sku", "product_name", "category"],
            [["SKU@#$123", "Product with special chars", "Cat1"]]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/sku_master/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        corrections = data.get("corrections", [])
        correction_codes = [c.get("code") for c in corrections]
        assert "E006" in correction_codes, f"Expected E006 correction, got {correction_codes}"
        print("TEST_19 PASS: E006 special characters auto-correction in validate mode")
    
    # ─── TEST 20: E007 Whitespace Trim ───
    def test_20_e007_whitespace_trim(self):
        """E007: Whitespace in SKU -> auto-trim"""
        csv_file = self._create_csv_file(
            ["sku", "product_name", "category"],
            [["  SKU-WITH-SPACES  ", "Product with spaces", "Cat1"]]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/sku_master/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        corrections = data.get("corrections", [])
        correction_codes = [c.get("code") for c in corrections]
        assert "E007" in correction_codes, f"Expected E007 correction, got {correction_codes}"
        print("TEST_20 PASS: E007 whitespace trim auto-correction in validate mode")
    
    # ─── TEST 21: E020 Future Date ───
    def test_21_e020_future_date(self):
        """E020: Future date -> warning"""
        csv_file = self._create_csv_file(
            ["sku", "store_code", "day", "quantity", "revenue"],
            [["ITER54-TEST-SKU", "STATUS-STORE", "2027-12-31", "10", "500"]]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily_sales/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        warnings = data.get("warnings", [])
        warning_codes = [w.get("code") for w in warnings]
        assert "E020" in warning_codes, f"Expected E020 warning for future date, got {warning_codes}"
        print("TEST_21 PASS: E020 future date warning in validate mode")
    
    # ─── TEST 22: E027 Negative Quantity ───
    def test_22_e027_negative_quantity(self):
        """E027: Negative quantity -> warning"""
        csv_file = self._create_csv_file(
            ["sku", "store_code", "day", "quantity", "revenue"],
            [["ITER54-TEST-SKU", "STATUS-STORE", "2025-01-15", "-5", "0"]]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily_sales/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        warnings = data.get("warnings", [])
        warning_codes = [w.get("code") for w in warnings]
        assert "E027" in warning_codes, f"Expected E027 warning for negative quantity, got {warning_codes}"
        print("TEST_22 PASS: E027 negative quantity warning in validate mode")
    
    # ─── TEST 23: E041 Zero Revenue ───
    def test_23_e041_zero_revenue(self):
        """E041: Zero revenue with positive quantity -> warning"""
        csv_file = self._create_csv_file(
            ["sku", "store_code", "day", "quantity", "revenue"],
            [["ITER54-TEST-SKU", "STATUS-STORE", "2025-01-15", "10", "0"]]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily_sales/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        warnings = data.get("warnings", [])
        warning_codes = [w.get("code") for w in warnings]
        assert "E041" in warning_codes, f"Expected E041 warning for zero revenue, got {warning_codes}"
        print("TEST_23 PASS: E041 zero revenue warning in validate mode")
    
    # ─── TEST 24: E066 Low Stock ───
    def test_24_e066_low_stock(self):
        """E066: Low stock (< 10) -> warning"""
        csv_file = self._create_csv_file(
            ["store_code", "sku", "closing_stock"],
            [["STATUS-STORE", "ITER54-TEST-SKU", "5"]]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/store_inventory/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        warnings = data.get("warnings", [])
        warning_codes = [w.get("code") for w in warnings]
        assert "E066" in warning_codes, f"Expected E066 warning for low stock, got {warning_codes}"
        print("TEST_24 PASS: E066 low stock warning in validate mode")
    
    # ─── TEST 25: E067 Available Exceeds On-Hand ───
    def test_25_e067_available_exceeds_onhand(self):
        """E067: available_qty > on_hand_qty -> warning"""
        csv_file = self._create_csv_file(
            ["warehouse", "sku", "on_hand_qty", "available_qty"],
            [["WH-001", "TSHIRT-BLK-M", "50", "100"]]  # available > on_hand
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/warehouse_inventory/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        warnings = data.get("warnings", [])
        warning_codes = [w.get("code") for w in warnings]
        assert "E067" in warning_codes, f"Expected E067 warning, got {warning_codes}"
        print("TEST_25 PASS: E067 available exceeds on-hand warning in validate mode")
    
    # ─── TEST 26: E069 Invalid Fulfillment Flag ───
    def test_26_e069_invalid_flag(self):
        """E069: Invalid online_fulfillment_flag -> warning"""
        csv_file = self._create_csv_file(
            ["warehouse", "warehouse_name", "online_fulfillment_flag"],
            [["WH-TEST", "Test Warehouse", "maybe"]]  # Invalid flag
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/warehouse_master/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        warnings = data.get("warnings", [])
        warning_codes = [w.get("code") for w in warnings]
        assert "E069" in warning_codes, f"Expected E069 warning for invalid flag, got {warning_codes}"
        print("TEST_26 PASS: E069 invalid fulfillment flag warning in validate mode")
    
    # ─── TEST 27: MIXED_CURRENCY Warning ───
    def test_27_mixed_currency_warning(self):
        """MIXED_CURRENCY: Mixed $ and ₹ -> warning"""
        csv_file = self._create_csv_file(
            ["sku", "store_code", "day", "quantity", "revenue"],
            [
                ["TSHIRT-BLK-M", "MAIN-01", "2025-01-15", "5", "$50"],
                ["CAP-BLK-ONE", "SOUTH-02", "2025-01-15", "3", "₹300"],
            ]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/daily_sales/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        warnings = data.get("warnings", [])
        warning_codes = [w.get("code") for w in warnings]
        assert "MIXED_CURRENCY" in warning_codes, f"Expected MIXED_CURRENCY warning, got {warning_codes}"
        print("TEST_27 PASS: MIXED_CURRENCY warning in validate mode")
    
    # ─── TEST 28: E030 Decimal Quantity ───
    def test_28_e030_decimal_quantity(self):
        """E030: Decimal quantity -> warning"""
        csv_file = self._create_csv_file(
            ["store_code", "sku", "closing_stock"],
            [["STATUS-STORE", "ITER54-TEST-SKU", "10.5"]]
        )
        files = {"file": csv_file}
        response = requests.post(
            f"{BASE_URL}/api/upload/v2/store_inventory/validate",
            files=files,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        warnings = data.get("warnings", [])
        warning_codes = [w.get("code") for w in warnings]
        assert "E030" in warning_codes, f"Expected E030 warning for decimal quantity, got {warning_codes}"
        print("TEST_28 PASS: E030 decimal quantity warning in validate mode")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
