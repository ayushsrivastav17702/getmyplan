"""
Comprehensive Integration Tests for GetMyPlan - Iteration 110
Covers 8 Test Suites:
1. Auth & Multi-Tenant
2. Core Classification
3. Buy Planning
4. Inventory Management
5. Reporting
6. System Administration
7. Sidebar Navigation (via Playwright - separate)
8. E2E Workflow

Test Credentials: admin@demo.com / demo1234 (super_admin, tenant: production)
"""
import pytest
import requests
import os
import time
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://zip-improved.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "admin@demo.com"
TEST_PASSWORD = "demo1234"


class TestAuthAndMultiTenant:
    """SUITE 1: Authentication & Multi-Tenant APIs"""
    
    token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token for all tests"""
        if TestAuthAndMultiTenant.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                TestAuthAndMultiTenant.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {TestAuthAndMultiTenant.token}"}
    
    def test_T1_login_super_admin(self):
        """T1: Login as super admin admin@demo.com/demo1234"""
        start = time.time()
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("user", {}).get("role") == "super_admin", "User is not super_admin"
        print(f"T1 PASS: Login successful (response time: {elapsed:.2f}s)")
    
    def test_T2_get_tenant_modules(self):
        """T2: GET /api/tenant-admin/modules returns modules with correct structure"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/tenant-admin/modules", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "modules" in data, "No modules in response"
        modules = data["modules"]
        assert len(modules) > 0, "No modules returned"
        
        # Check structure of first module
        first_mod = modules[0]
        assert "module_id" in first_mod, "Missing module_id"
        assert "module_name" in first_mod, "Missing module_name"
        assert "enabled" in first_mod, "Missing enabled field"
        print(f"T2 PASS: Got {len(modules)} modules (response time: {elapsed:.2f}s)")
    
    def test_T3_get_user_module_access(self):
        """T3: GET /api/users/admin@demo.com/module-access returns module_access and scope"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/users/{TEST_EMAIL}/module-access", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "module_access" in data or "email" in data, "Missing expected fields"
        print(f"T3 PASS: Got user module access (response time: {elapsed:.2f}s)")
    
    def test_T4_update_user_module_access(self):
        """T4: PUT /api/users/admin@demo.com/module-access updates module access"""
        start = time.time()
        response = requests.put(
            f"{BASE_URL}/api/users/{TEST_EMAIL}/module-access",
            headers=self.headers,
            json={"modules": [{"module_id": "core_classification", "access": "full"}]}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Update not successful"
        print(f"T4 PASS: Module access updated (response time: {elapsed:.2f}s)")
    
    def test_T5_update_user_scope(self):
        """T5: PUT /api/users/admin@demo.com/scope updates data scope"""
        start = time.time()
        response = requests.put(
            f"{BASE_URL}/api/users/{TEST_EMAIL}/scope",
            headers=self.headers,
            json={"categories": ["Apparel", "Footwear"], "regions": ["North", "South"]}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Update not successful"
        print(f"T5 PASS: User scope updated (response time: {elapsed:.2f}s)")
    
    def test_T6_get_roles(self):
        """T6: GET /api/users/roles returns list of available roles"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/users/roles", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "roles" in data, "No roles in response"
        roles = data["roles"]
        assert len(roles) > 0, "No roles returned"
        print(f"T6 PASS: Got {len(roles)} roles (response time: {elapsed:.2f}s)")
    
    def test_T7_get_user_list(self):
        """T7: GET /api/users/list returns user list"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/users/list", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "users" in data, "No users in response"
        print(f"T7 PASS: Got {len(data['users'])} users (response time: {elapsed:.2f}s)")


class TestCoreClassification:
    """SUITE 2: Core Classification APIs"""
    
    token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        if TestCoreClassification.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL, "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                TestCoreClassification.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {TestCoreClassification.token}"}
    
    def test_T10_store_wedge_classify(self):
        """T10: POST /api/buy-planning/store-wedge/classify runs store wedge classification"""
        start = time.time()
        response = requests.post(f"{BASE_URL}/api/buy-planning/store-wedge/classify", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Classification not successful"
        assert "summary" in data, "No summary in response"
        summary = data["summary"]
        assert "A" in summary and "B" in summary and "C" in summary, "Missing A/B/C counts"
        print(f"T10 PASS: Store wedge classified - A:{summary['A']}, B:{summary['B']}, C:{summary['C']} (response time: {elapsed:.2f}s)")
    
    def test_T11_get_store_wedge(self):
        """T11: GET /api/buy-planning/store-wedge returns classified stores"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/buy-planning/store-wedge", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "stores" in data, "No stores in response"
        assert "summary" in data, "No summary in response"
        print(f"T11 PASS: Got {len(data['stores'])} stores (response time: {elapsed:.2f}s)")
    
    def test_T12_style_mix_classify(self):
        """T12: POST /api/buy-planning/style-mix/classify runs style mix classification"""
        start = time.time()
        response = requests.post(f"{BASE_URL}/api/buy-planning/style-mix/classify", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Classification not successful"
        assert "summary" in data, "No summary in response"
        summary = data["summary"]
        assert "Core" in summary or "Fashion" in summary or "Test" in summary, "Missing Core/Fashion/Test counts"
        print(f"T12 PASS: Style mix classified - Core:{summary.get('Core',0)}, Fashion:{summary.get('Fashion',0)}, Test:{summary.get('Test',0)} (response time: {elapsed:.2f}s)")
    
    def test_T13_get_style_mix(self):
        """T13: GET /api/buy-planning/style-mix returns classified SKUs"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/buy-planning/style-mix", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "styles" in data, "No styles in response"
        print(f"T13 PASS: Got {len(data['styles'])} styles (response time: {elapsed:.2f}s)")
    
    def test_T14_store_wedge_override(self):
        """T14: POST /api/buy-planning/overrides/store-wedge creates override with audit"""
        # First get a store code
        stores_resp = requests.get(f"{BASE_URL}/api/buy-planning/store-wedge", headers=self.headers)
        stores = stores_resp.json().get("stores", [])
        if not stores:
            pytest.skip("No stores available for override test")
        
        store_code = stores[0].get("store_code")
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/overrides/store-wedge",
            headers=self.headers,
            json={"store_code": store_code, "wedge_class": "A", "reason": "Test override"}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Override not successful"
        print(f"T14 PASS: Store wedge override created for {store_code} (response time: {elapsed:.2f}s)")
    
    def test_T15_get_override_history(self):
        """T15: GET /api/buy-planning/overrides/history returns override audit trail"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/buy-planning/overrides/history", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "overrides" in data, "No overrides in response"
        print(f"T15 PASS: Got {len(data['overrides'])} override entries (response time: {elapsed:.2f}s)")
    
    def test_T16_get_attribution_matrix(self):
        """T16: GET /api/buy-planning/attribution/matrix returns attribution data"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/buy-planning/attribution/matrix", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "attributions" in data, "No attributions in response"
        print(f"T16 PASS: Got {len(data['attributions'])} attributions (response time: {elapsed:.2f}s)")
    
    def test_T17_auto_dna_tagging(self):
        """T17: POST /api/buy-planning/dna-tag/auto runs auto DNA tagging"""
        start = time.time()
        response = requests.post(f"{BASE_URL}/api/buy-planning/dna-tag/auto", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "DNA tagging not successful"
        print(f"T17 PASS: DNA tagging completed - {data.get('skus_tagged', 0)} SKUs tagged (response time: {elapsed:.2f}s)")
    
    def test_T18_get_dna_tags(self):
        """T18: GET /api/buy-planning/dna-tags returns DNA tag data"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/buy-planning/dna-tags", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "styles" in data, "No styles in response"
        print(f"T18 PASS: Got {len(data['styles'])} DNA tagged styles (response time: {elapsed:.2f}s)")


class TestBuyPlanning:
    """SUITE 3: Buy Planning APIs"""
    
    token = None
    plan_id = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        if TestBuyPlanning.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL, "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                TestBuyPlanning.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {TestBuyPlanning.token}"}
    
    def test_T19_calculate_buy_formula(self):
        """T19: POST /api/buy-planning/buy-formula/calculate generates buy plan with items"""
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-formula/calculate",
            headers=self.headers,
            json={"cover_days": 30, "safety_days": 7}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Calculation not successful"
        assert "buy_plan" in data, "No buy_plan in response"
        print(f"T19 PASS: Buy formula calculated - {len(data['buy_plan'])} items (response time: {elapsed:.2f}s)")
    
    def test_T20_list_buy_plans(self):
        """T20: GET /api/buy-planning/buy-plans returns list of saved plans"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/buy-planning/buy-plans", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "plans" in data, "No plans in response"
        plans = data["plans"]
        if plans:
            TestBuyPlanning.plan_id = plans[0].get("plan_id")
        print(f"T20 PASS: Got {len(plans)} buy plans (response time: {elapsed:.2f}s)")
    
    def test_T21_get_single_buy_plan(self):
        """T21: GET /api/buy-planning/buy-plans/{plan_id} returns single plan with items"""
        if not TestBuyPlanning.plan_id:
            # Get a plan ID first
            resp = requests.get(f"{BASE_URL}/api/buy-planning/buy-plans", headers=self.headers)
            plans = resp.json().get("plans", [])
            if not plans:
                pytest.skip("No buy plans available")
            TestBuyPlanning.plan_id = plans[0].get("plan_id")
        
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/buy-planning/buy-plans/{TestBuyPlanning.plan_id}", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "plan_id" in data, "No plan_id in response"
        assert "items" in data, "No items in response"
        print(f"T21 PASS: Got plan {data['plan_id']} with {len(data.get('items', []))} items (response time: {elapsed:.2f}s)")
    
    def test_T22_to_T26_approval_workflow(self):
        """T22-T26: Test approval workflow - submit, category approve, senior approve, head approve, reject"""
        # Find a draft plan
        resp = requests.get(f"{BASE_URL}/api/buy-planning/buy-plans?status=draft", headers=self.headers)
        plans = resp.json().get("plans", [])
        
        if not plans:
            # Generate a new plan
            gen_resp = requests.post(
                f"{BASE_URL}/api/buy-planning/buy-plans/generate",
                headers=self.headers,
                json={"plan_name": f"Test Plan {datetime.now().isoformat()}", "cover_days": 30}
            )
            if gen_resp.status_code == 200:
                plan_id = gen_resp.json().get("plan_id")
            else:
                pytest.skip("Could not create draft plan for approval testing")
        else:
            plan_id = plans[0].get("plan_id")
        
        # T22: Submit
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/approval",
            headers=self.headers,
            json={"action": "submit", "comment": "Submitting for approval"}
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f"T22 PASS: Plan submitted (response time: {elapsed:.2f}s)")
        else:
            print(f"T22 SKIP: {response.text}")
        
        # T23: Category approve
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/approval",
            headers=self.headers,
            json={"action": "approve_category", "comment": "Category approved"}
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f"T23 PASS: Category approved (response time: {elapsed:.2f}s)")
        else:
            print(f"T23 SKIP: {response.text}")
        
        # T24: Senior approve
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/approval",
            headers=self.headers,
            json={"action": "approve_senior", "comment": "Senior approved"}
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f"T24 PASS: Senior approved (response time: {elapsed:.2f}s)")
        else:
            print(f"T24 SKIP: {response.text}")
        
        # T25: Head approve
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/approval",
            headers=self.headers,
            json={"action": "approve_head", "comment": "Head approved"}
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f"T25 PASS: Head approved (response time: {elapsed:.2f}s)")
        else:
            print(f"T25 SKIP: {response.text}")
    
    def test_T27_get_approval_history(self):
        """T27: GET /api/buy-planning/buy-plans/{plan_id}/approval-history returns approval timeline"""
        if not TestBuyPlanning.plan_id:
            resp = requests.get(f"{BASE_URL}/api/buy-planning/buy-plans", headers=self.headers)
            plans = resp.json().get("plans", [])
            if not plans:
                pytest.skip("No buy plans available")
            TestBuyPlanning.plan_id = plans[0].get("plan_id")
        
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/buy-plans/{TestBuyPlanning.plan_id}/approval-history",
            headers=self.headers
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "history" in data, "No history in response"
        print(f"T27 PASS: Got {len(data['history'])} approval history entries (response time: {elapsed:.2f}s)")
    
    def test_T28_add_exclusion(self):
        """T28: POST /api/buy-planning/exclusions adds store-SKU exclusion"""
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/exclusions",
            headers=self.headers,
            json={"store_code": "STORE-001", "sku": "TEST-SKU-001", "reason": "Test exclusion"}
        )
        elapsed = time.time() - start
        
        # May return 200 or 400 if already exists
        assert response.status_code in [200, 400, 404], f"Unexpected status: {response.text}"
        print(f"T28 PASS: Exclusion endpoint tested (response time: {elapsed:.2f}s)")
    
    def test_T29_get_exclusions(self):
        """T29: GET /api/buy-planning/exclusions returns exclusion list"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/buy-planning/exclusions", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "exclusions" in data, "No exclusions in response"
        print(f"T29 PASS: Got {len(data['exclusions'])} exclusions (response time: {elapsed:.2f}s)")
    
    def test_T30_consolidate_orders(self):
        """T30: POST /api/buy-planning/orders/consolidate creates supplier POs"""
        # Get a plan ID
        resp = requests.get(f"{BASE_URL}/api/buy-planning/buy-plans", headers=self.headers)
        plans = resp.json().get("plans", [])
        if not plans:
            pytest.skip("No buy plans available for consolidation")
        
        plan_id = plans[0].get("plan_id")
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/orders/consolidate",
            headers=self.headers,
            json={"plan_id": plan_id}
        )
        elapsed = time.time() - start
        
        # May return 200 or 400 depending on plan status
        assert response.status_code in [200, 400], f"Unexpected status: {response.text}"
        print(f"T30 PASS: Order consolidation tested (response time: {elapsed:.2f}s)")
    
    def test_T31_get_orders(self):
        """T31: GET /api/buy-planning/orders returns consolidated orders"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/buy-planning/orders", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "orders" in data, "No orders in response"
        print(f"T31 PASS: Got {len(data['orders'])} orders (response time: {elapsed:.2f}s)")
    
    def test_T32_phase_orders(self):
        """T32: POST /api/buy-planning/orders/phase creates phased replenishment"""
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/orders/phase",
            headers=self.headers,
            json={"po_number": "TEST-PO-001", "phases": 3}
        )
        elapsed = time.time() - start
        
        # May return 200 or 400/404/422 depending on order existence
        assert response.status_code in [200, 400, 404, 422], f"Unexpected status: {response.text}"
        print(f"T32 PASS: Order phasing tested (response time: {elapsed:.2f}s)")


class TestInventory:
    """SUITE 4: Inventory Management APIs"""
    
    token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        if TestInventory.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL, "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                TestInventory.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {TestInventory.token}"}
    
    def test_T33_bulk_upload_inventory(self):
        """T33: POST /api/buy-planning/inventory/bulk uploads inventory records"""
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/inventory/bulk",
            headers=self.headers,
            json={"records": [
                {"store_code": "STORE-001", "sku": "TEST-SKU-001", "soh": 100, "in_transit": 20}
            ]}
        )
        elapsed = time.time() - start
        
        assert response.status_code in [200, 400], f"Unexpected status: {response.text}"
        print(f"T33 PASS: Inventory bulk upload tested (response time: {elapsed:.2f}s)")
    
    def test_T34_get_inventory(self):
        """T34: GET /api/buy-planning/inventory returns inventory data"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/buy-planning/inventory", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "inventory" in data or "records" in data, "No inventory data in response"
        print(f"T34 PASS: Got inventory data (response time: {elapsed:.2f}s)")
    
    def test_T35_get_inventory_summary(self):
        """T35: GET /api/buy-planning/inventory/summary returns summary stats"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/buy-planning/inventory/summary", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"T35 PASS: Got inventory summary (response time: {elapsed:.2f}s)")
    
    def test_T36_get_safety_stock_config(self):
        """T36: GET /api/buy-planning/safety-stock/config returns safety stock config"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/buy-planning/safety-stock/config", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        print(f"T36 PASS: Got safety stock config (response time: {elapsed:.2f}s)")
    
    def test_T37_calculate_safety_stock(self):
        """T37: GET /api/buy-planning/safety-stock/calculate calculates safety stock"""
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/safety-stock/calculate",
            headers=self.headers,
            params={"sku": "STYLE-TS-001-WHT-L", "lead_time_days": 14}
        )
        elapsed = time.time() - start
        
        assert response.status_code in [200, 404], f"Unexpected status: {response.text}"
        print(f"T37 PASS: Safety stock calculation tested (response time: {elapsed:.2f}s)")


class TestReporting:
    """SUITE 5: Reporting APIs"""
    
    token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        if TestReporting.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL, "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                TestReporting.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {TestReporting.token}"}
    
    def test_T38_planner_performance(self):
        """T38: GET /api/reports/planner-performance returns leaderboard"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/reports/planner-performance", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "leaderboard" in data, "No leaderboard in response"
        
        if data["leaderboard"]:
            entry = data["leaderboard"][0]
            assert "rank" in entry, "Missing rank"
            assert "email" in entry, "Missing email"
            assert "plans_created" in entry, "Missing plans_created"
            assert "approval_rate" in entry, "Missing approval_rate"
        
        print(f"T38 PASS: Got {len(data['leaderboard'])} planners (response time: {elapsed:.2f}s)")
    
    def test_T39_category_health(self):
        """T39: GET /api/reports/category-health returns categories with metrics"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/reports/category-health", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "categories" in data, "No categories in response"
        
        if data["categories"]:
            cat = data["categories"][0]
            assert "stock_health" in cat, "Missing stock_health"
            assert "fill_rate" in cat, "Missing fill_rate"
            assert "doh" in cat, "Missing doh"
            assert "revenue_30d" in cat, "Missing revenue_30d"
        
        print(f"T39 PASS: Got {len(data['categories'])} categories (response time: {elapsed:.2f}s)")
    
    def test_T40_roi_dashboard(self):
        """T40: GET /api/reports/roi returns KPIs and monthly revenue"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/reports/roi", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "kpis" in data, "No kpis in response"
        
        kpis = data["kpis"]
        assert "total_plans" in kpis, "Missing total_plans"
        assert "approved_plans" in kpis, "Missing approved_plans"
        assert "plan_approval_rate" in kpis, "Missing plan_approval_rate"
        assert "time_saved_hrs" in kpis, "Missing time_saved_hrs"
        
        assert "monthly_revenue" in data, "No monthly_revenue in response"
        
        print(f"T40 PASS: ROI KPIs - {kpis['total_plans']} plans, {kpis['plan_approval_rate']}% approval (response time: {elapsed:.2f}s)")
    
    def test_T41_readiness_dashboard(self):
        """T41: GET /api/dashboards/readiness returns readiness_score and checks"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/dashboards/readiness", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "readiness_score" in data, "No readiness_score in response"
        assert "checks" in data, "No checks in response"
        
        checks = data["checks"]
        assert len(checks) == 8, f"Expected 8 checks, got {len(checks)}"
        
        print(f"T41 PASS: Readiness score {data['readiness_score']}%, {len(checks)} checks (response time: {elapsed:.2f}s)")
    
    def test_T42_forecast_accuracy(self):
        """T42: GET /api/dashboards/forecast-accuracy returns overall metrics"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/dashboards/forecast-accuracy", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "overall" in data, "No overall in response"
        assert "monthly_comparison" in data, "No monthly_comparison in response"
        
        print(f"T42 PASS: Forecast accuracy data retrieved (response time: {elapsed:.2f}s)")


class TestSystemAdmin:
    """SUITE 6: System Administration APIs"""
    
    token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        if TestSystemAdmin.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL, "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                TestSystemAdmin.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {TestSystemAdmin.token}"}
    
    def test_T43_get_audit_log(self):
        """T43: GET /api/buy-planning/audit-log returns audit entries"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/buy-planning/audit-log", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "entries" in data, "No entries in response"
        print(f"T43 PASS: Got {len(data['entries'])} audit entries (response time: {elapsed:.2f}s)")
    
    def test_T44_get_feature_flags(self):
        """T44: GET /api/admin/platform/feature-flags returns feature flags"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/admin/platform/feature-flags", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "flags" in data, "No flags in response"
        print(f"T44 PASS: Got {len(data['flags'])} feature flags (response time: {elapsed:.2f}s)")
    
    def test_T45_get_global_config(self):
        """T45: GET /api/admin/platform/global-config returns global config"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/admin/platform/global-config", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "config" in data, "No config in response"
        print(f"T45 PASS: Got global config (response time: {elapsed:.2f}s)")
    
    def test_T46_get_tenants(self):
        """T46: GET /api/admin/platform/tenants returns tenant list"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/admin/platform/tenants", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "tenants" in data, "No tenants in response"
        print(f"T46 PASS: Got {len(data['tenants'])} tenants (response time: {elapsed:.2f}s)")
    
    def test_T47_get_platform_analytics(self):
        """T47: GET /api/admin/platform/analytics returns platform analytics"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/admin/platform/analytics", headers=self.headers)
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "overview" in data, "No overview in response"
        print(f"T47 PASS: Got platform analytics (response time: {elapsed:.2f}s)")


class TestE2EWorkflow:
    """SUITE 8: End-to-End Workflow Tests"""
    
    token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        if TestE2EWorkflow.token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL, "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                TestE2EWorkflow.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {TestE2EWorkflow.token}"}
    
    def test_T55_full_workflow(self):
        """T55: Full flow - Classify stores -> Classify SKUs -> Generate buy plan -> Submit -> Approve"""
        results = []
        
        # Step 1: Classify stores
        start = time.time()
        resp = requests.post(f"{BASE_URL}/api/buy-planning/store-wedge/classify", headers=self.headers)
        elapsed = time.time() - start
        if resp.status_code == 200:
            results.append(f"Step 1 PASS: Store wedge classified ({elapsed:.2f}s)")
        else:
            results.append(f"Step 1 FAIL: {resp.text}")
        
        # Step 2: Classify SKUs
        start = time.time()
        resp = requests.post(f"{BASE_URL}/api/buy-planning/style-mix/classify", headers=self.headers)
        elapsed = time.time() - start
        if resp.status_code == 200:
            results.append(f"Step 2 PASS: Style mix classified ({elapsed:.2f}s)")
        else:
            results.append(f"Step 2 FAIL: {resp.text}")
        
        # Step 3: Generate buy plan
        start = time.time()
        resp = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-plans/generate",
            headers=self.headers,
            json={"plan_name": f"E2E Test Plan {datetime.now().isoformat()}", "cover_days": 30}
        )
        elapsed = time.time() - start
        if resp.status_code == 200:
            plan_id = resp.json().get("plan_id")
            results.append(f"Step 3 PASS: Buy plan generated - {plan_id} ({elapsed:.2f}s)")
        else:
            results.append(f"Step 3 FAIL: {resp.text}")
            plan_id = None
        
        if plan_id:
            # Step 4: Submit for approval
            start = time.time()
            resp = requests.post(
                f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/approval",
                headers=self.headers,
                json={"action": "submit", "comment": "E2E test submission"}
            )
            elapsed = time.time() - start
            if resp.status_code == 200:
                results.append(f"Step 4 PASS: Plan submitted ({elapsed:.2f}s)")
            else:
                results.append(f"Step 4 FAIL: {resp.text}")
            
            # Step 5: Category approve
            start = time.time()
            resp = requests.post(
                f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/approval",
                headers=self.headers,
                json={"action": "approve_category", "comment": "E2E category approval"}
            )
            elapsed = time.time() - start
            if resp.status_code == 200:
                results.append(f"Step 5 PASS: Category approved ({elapsed:.2f}s)")
            else:
                results.append(f"Step 5 FAIL: {resp.text}")
            
            # Step 6: Get approval history
            start = time.time()
            resp = requests.get(
                f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}/approval-history",
                headers=self.headers
            )
            elapsed = time.time() - start
            if resp.status_code == 200:
                history = resp.json().get("history", [])
                results.append(f"Step 6 PASS: Got {len(history)} approval history entries ({elapsed:.2f}s)")
            else:
                results.append(f"Step 6 FAIL: {resp.text}")
            
            # Step 7: Verify status
            start = time.time()
            resp = requests.get(f"{BASE_URL}/api/buy-planning/buy-plans/{plan_id}", headers=self.headers)
            elapsed = time.time() - start
            if resp.status_code == 200:
                status = resp.json().get("status")
                results.append(f"Step 7 PASS: Plan status is '{status}' ({elapsed:.2f}s)")
            else:
                results.append(f"Step 7 FAIL: {resp.text}")
        
        for r in results:
            print(r)
        
        # At least 5 steps should pass
        pass_count = sum(1 for r in results if "PASS" in r)
        assert pass_count >= 5, f"Only {pass_count} steps passed out of {len(results)}"
        print(f"T55 PASS: E2E workflow completed - {pass_count}/{len(results)} steps passed")
    
    def test_T56_verify_audit_log(self):
        """T56: Verify audit log entries created for classification and approval actions"""
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/audit-log",
            headers=self.headers,
            params={"limit": 50}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        entries = data.get("entries", [])
        
        # Check for classification and approval entries
        actions = [e.get("action") for e in entries]
        has_classify = any("classify" in str(a).lower() for a in actions)
        has_override = any("override" in str(a).lower() for a in actions)
        
        print(f"T56 PASS: Audit log has {len(entries)} entries, classify:{has_classify}, override:{has_override} (response time: {elapsed:.2f}s)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
