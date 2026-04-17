"""
Buy Planning Phase 2+3 Tests - Iteration 96
Tests for:
- Display Minimums Configuration (POST/GET/DELETE)
- Full Buy Formula Calculation
- DNA Tagging (single, bulk, auto)
- Attribution Matrix
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@demo.com"
TEST_PASSWORD = "demo1234"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for all tests."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


# ═══════════════════════════════════════════════════
# DISPLAY MINIMUMS TESTS
# ═══════════════════════════════════════════════════

class TestDisplayMinimums:
    """Tests for display minimums configuration endpoints."""

    def test_get_display_minimums_returns_configs(self, auth_headers):
        """GET /api/buy-planning/display-minimums returns configs with computed total."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/display-minimums", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "configs" in data, "Response should have 'configs' key"
        assert "total" in data, "Response should have 'total' key"
        assert isinstance(data["configs"], list), "configs should be a list"
        
        # Verify each config has required fields
        for config in data["configs"]:
            assert "category" in config, "Config should have 'category'"
            assert "store_wedge" in config, "Config should have 'store_wedge'"
            assert "total_display_min_units" in config, "Config should have computed 'total_display_min_units'"
        
        print(f"✓ GET display-minimums: {len(data['configs'])} configs found")

    def test_post_display_minimum_creates_config(self, auth_headers):
        """POST /api/buy-planning/display-minimums creates/updates config."""
        payload = {
            "category": "TEST_CATEGORY",
            "store_wedge": "A",
            "min_facings": 4,
            "display_units_per_facing": 3
        }
        response = requests.post(f"{BASE_URL}/api/buy-planning/display-minimums", 
                                 json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        assert data.get("category") == "TEST_CATEGORY"
        assert data.get("store_wedge") == "A"
        assert data.get("total_display_min_units") == 12, "4 facings × 3 units = 12"
        
        print(f"✓ POST display-minimums: Created config with total={data['total_display_min_units']}")

    def test_display_minimum_computed_total_correct(self, auth_headers):
        """Verify computed total = min_facings × display_units_per_facing."""
        # Create with specific values
        payload = {
            "category": "TEST_COMPUTE",
            "store_wedge": "B",
            "min_facings": 5,
            "display_units_per_facing": 4
        }
        response = requests.post(f"{BASE_URL}/api/buy-planning/display-minimums", 
                                 json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        expected_total = 5 * 4  # 20
        assert data.get("total_display_min_units") == expected_total, f"Expected {expected_total}, got {data.get('total_display_min_units')}"
        
        print(f"✓ Display minimum computed total: {expected_total} (5×4)")

    def test_delete_display_minimum(self, auth_headers):
        """DELETE /api/buy-planning/display-minimums/{category}/{store_wedge} removes config."""
        # First create a config to delete
        payload = {
            "category": "TEST_DELETE",
            "store_wedge": "C",
            "min_facings": 2,
            "display_units_per_facing": 2
        }
        requests.post(f"{BASE_URL}/api/buy-planning/display-minimums", 
                      json=payload, headers=auth_headers)
        
        # Now delete it
        response = requests.delete(f"{BASE_URL}/api/buy-planning/display-minimums/TEST_DELETE/C", 
                                   headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        
        print("✓ DELETE display-minimums: Config removed successfully")

    def test_delete_nonexistent_config_returns_404(self, auth_headers):
        """DELETE non-existent config returns 404."""
        response = requests.delete(f"{BASE_URL}/api/buy-planning/display-minimums/NONEXISTENT/X", 
                                   headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        print("✓ DELETE non-existent config returns 404")


# ═══════════════════════════════════════════════════
# BUY FORMULA TESTS
# ═══════════════════════════════════════════════════

class TestBuyFormula:
    """Tests for buy formula calculation endpoint."""

    def test_buy_formula_calculate_returns_plan(self, auth_headers):
        """POST /api/buy-planning/buy-formula/calculate returns full buy plan."""
        payload = {
            "cover_days": 30,
            "safety_days": 7
        }
        response = requests.post(f"{BASE_URL}/api/buy-planning/buy-formula/calculate", 
                                 json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        assert "buy_plan" in data, "Response should have 'buy_plan'"
        assert "totals" in data, "Response should have 'totals'"
        assert "sku_count" in data, "Response should have 'sku_count'"
        assert "parameters" in data, "Response should have 'parameters'"
        
        print(f"✓ Buy formula calculate: {data['sku_count']} SKUs, totals={data['totals']}")

    def test_buy_formula_returns_required_fields_per_sku(self, auth_headers):
        """Each SKU in buy plan has demand_buy, display_minimum, safety_stock, buy_qty, binding_constraint."""
        payload = {"cover_days": 30, "safety_days": 7}
        response = requests.post(f"{BASE_URL}/api/buy-planning/buy-formula/calculate", 
                                 json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        buy_plan = data.get("buy_plan", [])
        
        if len(buy_plan) > 0:
            sku = buy_plan[0]
            required_fields = ["sku", "demand_buy", "display_minimum", "safety_stock", 
                               "buy_qty", "buy_value", "binding_constraint"]
            for field in required_fields:
                assert field in sku, f"SKU should have '{field}' field"
            
            print(f"✓ Buy plan SKU has all required fields: {required_fields}")
        else:
            print("⚠ No SKUs in buy plan to verify fields")

    def test_buy_formula_binding_constraint_logic(self, auth_headers):
        """Verify binding_constraint is 'demand' when demand > display+safety."""
        payload = {"cover_days": 30, "safety_days": 7}
        response = requests.post(f"{BASE_URL}/api/buy-planning/buy-formula/calculate", 
                                 json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        buy_plan = data.get("buy_plan", [])
        
        demand_constrained = 0
        display_constrained = 0
        safety_constrained = 0
        
        for sku in buy_plan:
            constraint = sku.get("binding_constraint", "")
            demand_buy = sku.get("demand_buy", 0)
            display_min = sku.get("display_minimum", 0)
            safety = sku.get("safety_stock", 0)
            
            if constraint == "demand":
                demand_constrained += 1
                # Verify demand is actually the max
                assert demand_buy >= display_min and demand_buy >= safety, \
                    f"demand constraint but demand_buy={demand_buy} < display={display_min} or safety={safety}"
            elif constraint == "display_min":
                display_constrained += 1
            elif constraint == "safety_stock":
                safety_constrained += 1
        
        print(f"✓ Binding constraints: demand={demand_constrained}, display={display_constrained}, safety={safety_constrained}")

    def test_buy_formula_totals_structure(self, auth_headers):
        """Verify totals has total_buy_qty, total_buy_value, total_display_qty, total_safety_qty."""
        payload = {"cover_days": 30, "safety_days": 7}
        response = requests.post(f"{BASE_URL}/api/buy-planning/buy-formula/calculate", 
                                 json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        totals = data.get("totals", {})
        
        required_totals = ["total_buy_qty", "total_buy_value", "total_display_qty", "total_safety_qty"]
        for field in required_totals:
            assert field in totals, f"Totals should have '{field}'"
            assert isinstance(totals[field], (int, float)), f"{field} should be numeric"
        
        print(f"✓ Buy formula totals: qty={totals['total_buy_qty']}, value=₹{totals['total_buy_value']:,.0f}")

    def test_buy_formula_custom_sell_through_targets(self, auth_headers):
        """Test custom sell-through targets override defaults."""
        payload = {
            "cover_days": 30,
            "safety_days": 7,
            "sell_through_targets": {"Core": 1.5, "Fashion": 1.0, "Test": 0.5}
        }
        response = requests.post(f"{BASE_URL}/api/buy-planning/buy-formula/calculate", 
                                 json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        params = data.get("parameters", {})
        targets = params.get("sell_through_targets", {})
        
        assert targets.get("Core") == 1.5, "Custom Core target should be 1.5"
        assert targets.get("Fashion") == 1.0, "Custom Fashion target should be 1.0"
        
        print(f"✓ Custom sell-through targets applied: {targets}")


# ═══════════════════════════════════════════════════
# DNA TAGGING TESTS
# ═══════════════════════════════════════════════════

class TestDNATagging:
    """Tests for DNA tagging endpoints."""

    def test_auto_dna_tag_tags_styles(self, auth_headers):
        """POST /api/buy-planning/dna-tag/auto auto-tags styles with flow_rank, lifecycle_stage, launch_date."""
        response = requests.post(f"{BASE_URL}/api/buy-planning/dna-tag/auto", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        assert "styles_processed" in data or "skus_tagged" in data or "message" in data, \
            "Response should have processing info"
        
        print(f"✓ Auto DNA tag: {data}")

    def test_get_dna_tags_returns_tagged_styles(self, auth_headers):
        """GET /api/buy-planning/dna-tags returns tagged styles grouped by style."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/dna-tags", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "styles" in data, "Response should have 'styles'"
        assert "total" in data, "Response should have 'total'"
        
        styles = data.get("styles", [])
        if len(styles) > 0:
            style = styles[0]
            # Verify DNA fields
            assert "style" in style, "Style should have 'style' field"
            assert "flow_rank" in style, "Style should have 'flow_rank'"
            assert "lifecycle_stage" in style, "Style should have 'lifecycle_stage'"
            assert "launch_date" in style, "Style should have 'launch_date'"
            
            # Verify flow_rank values (1=Hero, 2=Core, 3=Fill-in)
            flow_rank = style.get("flow_rank")
            assert flow_rank in [1, 2, 3, None], f"flow_rank should be 1, 2, or 3, got {flow_rank}"
        
        print(f"✓ GET dna-tags: {data['total']} tagged styles")

    def test_dna_tag_single_sku(self, auth_headers):
        """POST /api/buy-planning/dna-tag tags a single SKU."""
        # First get a valid SKU from buy plan
        bp_response = requests.post(f"{BASE_URL}/api/buy-planning/buy-formula/calculate", 
                                    json={"cover_days": 30, "safety_days": 7}, headers=auth_headers)
        if bp_response.status_code != 200:
            pytest.skip("Cannot get SKU list for single tag test")
        
        buy_plan = bp_response.json().get("buy_plan", [])
        if not buy_plan:
            pytest.skip("No SKUs available for single tag test")
        
        test_sku = buy_plan[0]["sku"]
        
        payload = {
            "sku": test_sku,
            "flow_rank": 1,
            "lifecycle_stage": "Peak",
            "expected_weeks": 12
        }
        response = requests.post(f"{BASE_URL}/api/buy-planning/dna-tag", 
                                 json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert data.get("sku") == test_sku
        
        print(f"✓ Single SKU DNA tag: {test_sku}")

    def test_dna_tag_bulk_style(self, auth_headers):
        """POST /api/buy-planning/dna-tag/bulk tags all SKUs of a style."""
        # Get a style from DNA tags
        tags_response = requests.get(f"{BASE_URL}/api/buy-planning/dna-tags", headers=auth_headers)
        if tags_response.status_code != 200:
            pytest.skip("Cannot get styles for bulk tag test")
        
        styles = tags_response.json().get("styles", [])
        if not styles:
            pytest.skip("No styles available for bulk tag test")
        
        test_style = styles[0]["style"]
        
        payload = {
            "style": test_style,
            "flow_rank": 2,
            "lifecycle_stage": "Decline",
            "expected_weeks": 8
        }
        response = requests.post(f"{BASE_URL}/api/buy-planning/dna-tag/bulk", 
                                 json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert data.get("style") == test_style
        assert "skus_updated" in data
        
        print(f"✓ Bulk style DNA tag: {test_style}, {data['skus_updated']} SKUs updated")

    def test_dna_tag_nonexistent_sku_returns_404(self, auth_headers):
        """POST /api/buy-planning/dna-tag with non-existent SKU returns 404."""
        payload = {
            "sku": "NONEXISTENT_SKU_12345",
            "flow_rank": 1
        }
        response = requests.post(f"{BASE_URL}/api/buy-planning/dna-tag", 
                                 json=payload, headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        print("✓ Non-existent SKU DNA tag returns 404")


# ═══════════════════════════════════════════════════
# ATTRIBUTION MATRIX TESTS
# ═══════════════════════════════════════════════════

class TestAttributionMatrix:
    """Tests for attribution matrix endpoint."""

    def test_get_attribution_matrix_returns_allocations(self, auth_headers):
        """GET /api/buy-planning/attribution/matrix returns wedge allocation per style."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/attribution/matrix", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "attributions" in data, "Response should have 'attributions'"
        assert "store_counts" in data, "Response should have 'store_counts'"
        assert "rules" in data, "Response should have 'rules'"
        
        print(f"✓ GET attribution/matrix: {len(data['attributions'])} styles")

    def test_attribution_rules_core_all_stores(self, auth_headers):
        """Core styles should be eligible for A, B, C stores (100% coverage)."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/attribution/matrix", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        rules = data.get("rules", {})
        
        # Verify Core → ALL stores
        core_rules = rules.get("Core", {})
        assert core_rules.get("A") == True, "Core should be eligible for A stores"
        assert core_rules.get("B") == True, "Core should be eligible for B stores"
        assert core_rules.get("C") == True, "Core should be eligible for C stores"
        
        print(f"✓ Attribution rules - Core: A={core_rules.get('A')}, B={core_rules.get('B')}, C={core_rules.get('C')}")

    def test_attribution_rules_fashion_a_b_only(self, auth_headers):
        """Fashion styles should be eligible for A and B stores only."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/attribution/matrix", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        rules = data.get("rules", {})
        
        # Verify Fashion → A+B only
        fashion_rules = rules.get("Fashion", {})
        assert fashion_rules.get("A") == True, "Fashion should be eligible for A stores"
        assert fashion_rules.get("B") == True, "Fashion should be eligible for B stores"
        assert fashion_rules.get("C") == False, "Fashion should NOT be eligible for C stores"
        
        print(f"✓ Attribution rules - Fashion: A={fashion_rules.get('A')}, B={fashion_rules.get('B')}, C={fashion_rules.get('C')}")

    def test_attribution_rules_test_a_only(self, auth_headers):
        """Test styles should be eligible for A stores only."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/attribution/matrix", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        rules = data.get("rules", {})
        
        # Verify Test → A only
        test_rules = rules.get("Test", {})
        assert test_rules.get("A") == True, "Test should be eligible for A stores"
        assert test_rules.get("B") == False, "Test should NOT be eligible for B stores"
        assert test_rules.get("C") == False, "Test should NOT be eligible for C stores"
        
        print(f"✓ Attribution rules - Test: A={test_rules.get('A')}, B={test_rules.get('B')}, C={test_rules.get('C')}")

    def test_attribution_style_has_coverage_pct(self, auth_headers):
        """Each style attribution should have coverage_pct and wedge_allocation."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/attribution/matrix", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        attributions = data.get("attributions", [])
        
        if len(attributions) > 0:
            attr = attributions[0]
            assert "style" in attr, "Attribution should have 'style'"
            assert "style_mix" in attr, "Attribution should have 'style_mix'"
            assert "coverage_pct" in attr, "Attribution should have 'coverage_pct'"
            assert "wedge_allocation" in attr, "Attribution should have 'wedge_allocation'"
            
            # Verify wedge_allocation structure
            wedge_alloc = attr.get("wedge_allocation", {})
            for wedge in ["A", "B", "C"]:
                assert wedge in wedge_alloc, f"wedge_allocation should have '{wedge}'"
                assert "eligible" in wedge_alloc[wedge], f"{wedge} should have 'eligible'"
                assert "allocation_pct" in wedge_alloc[wedge], f"{wedge} should have 'allocation_pct'"
            
            print(f"✓ Attribution style structure verified: coverage={attr['coverage_pct']}%")
        else:
            print("⚠ No attributions to verify structure")


# ═══════════════════════════════════════════════════
# AUTH TESTS (without token)
# ═══════════════════════════════════════════════════

class TestAuthRequired:
    """Verify endpoints require authentication."""

    def test_display_minimums_requires_auth(self):
        """GET /api/buy-planning/display-minimums requires auth."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/display-minimums")
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"
        print("✓ display-minimums requires auth")

    def test_buy_formula_requires_auth(self):
        """POST /api/buy-planning/buy-formula/calculate requires auth."""
        response = requests.post(f"{BASE_URL}/api/buy-planning/buy-formula/calculate", 
                                 json={"cover_days": 30})
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"
        print("✓ buy-formula/calculate requires auth")

    def test_dna_tags_requires_auth(self):
        """GET /api/buy-planning/dna-tags requires auth."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/dna-tags")
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"
        print("✓ dna-tags requires auth")

    def test_attribution_matrix_requires_auth(self):
        """GET /api/buy-planning/attribution/matrix requires auth."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/attribution/matrix")
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"
        print("✓ attribution/matrix requires auth")


# Cleanup test data
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data(auth_headers):
    """Cleanup TEST_ prefixed configs after tests."""
    yield
    # Cleanup
    for cat in ["TEST_CATEGORY", "TEST_COMPUTE", "TEST_DELETE"]:
        for wedge in ["A", "B", "C"]:
            try:
                requests.delete(f"{BASE_URL}/api/buy-planning/display-minimums/{cat}/{wedge}", 
                               headers=auth_headers)
            except:
                pass
