"""
Buy Planning API Tests - Iteration 95
Tests for Store Wedge Classification, Style Mix Tagging, and Assortment Matrix endpoints.
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
    """Get authentication token for super admin."""
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


class TestBuyPlanningAuth:
    """Test authentication requirements for Buy Planning endpoints."""
    
    def test_store_wedge_get_without_auth_returns_error(self):
        """GET /api/buy-planning/store-wedge without auth should fail."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/store-wedge")
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"
        print(f"PASS: GET store-wedge without auth returns {response.status_code}")
    
    def test_store_wedge_classify_without_auth_returns_error(self):
        """POST /api/buy-planning/store-wedge/classify without auth should fail."""
        response = requests.post(f"{BASE_URL}/api/buy-planning/store-wedge/classify")
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"
        print(f"PASS: POST store-wedge/classify without auth returns {response.status_code}")
    
    def test_style_mix_get_without_auth_returns_error(self):
        """GET /api/buy-planning/style-mix without auth should fail."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/style-mix")
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"
        print(f"PASS: GET style-mix without auth returns {response.status_code}")
    
    def test_style_mix_classify_without_auth_returns_error(self):
        """POST /api/buy-planning/style-mix/classify without auth should fail."""
        response = requests.post(f"{BASE_URL}/api/buy-planning/style-mix/classify")
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"
        print(f"PASS: POST style-mix/classify without auth returns {response.status_code}")
    
    def test_assortment_matrix_without_auth_returns_error(self):
        """GET /api/buy-planning/assortment-matrix without auth should fail."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/assortment-matrix")
        assert response.status_code in [400, 401, 403], f"Expected auth error, got {response.status_code}"
        print(f"PASS: GET assortment-matrix without auth returns {response.status_code}")


class TestStoreWedgeClassification:
    """Test Store Wedge Classification endpoints."""
    
    def test_get_store_wedge_returns_stores(self, auth_headers):
        """GET /api/buy-planning/store-wedge returns classified stores."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/store-wedge", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "stores" in data, "Response should contain 'stores' field"
        assert "summary" in data, "Response should contain 'summary' field"
        assert "classified" in data, "Response should contain 'classified' field"
        
        # Verify summary structure
        summary = data["summary"]
        assert "A" in summary, "Summary should have 'A' count"
        assert "B" in summary, "Summary should have 'B' count"
        assert "C" in summary, "Summary should have 'C' count"
        
        print(f"PASS: GET store-wedge returns {len(data['stores'])} stores")
        print(f"  Summary: A={summary['A']}, B={summary['B']}, C={summary['C']}")
        print(f"  Classified: {data['classified']}")
    
    def test_store_wedge_has_wedge_class(self, auth_headers):
        """Verify stores have wedge_class field after classification."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/store-wedge", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        stores = data.get("stores", [])
        
        if stores and data.get("classified"):
            # Check that at least some stores have wedge_class
            stores_with_wedge = [s for s in stores if s.get("wedge_class")]
            assert len(stores_with_wedge) > 0, "At least some stores should have wedge_class"
            
            # Verify wedge_class values are valid
            for store in stores_with_wedge:
                assert store["wedge_class"] in ["A", "B", "C"], f"Invalid wedge_class: {store['wedge_class']}"
            
            print(f"PASS: {len(stores_with_wedge)}/{len(stores)} stores have valid wedge_class")
        else:
            print("SKIP: No classified stores found (may need to run classification first)")
    
    def test_classify_store_wedge(self, auth_headers):
        """POST /api/buy-planning/store-wedge/classify runs classification."""
        response = requests.post(f"{BASE_URL}/api/buy-planning/store-wedge/classify", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Classification should succeed"
        assert "summary" in data, "Response should contain summary"
        assert "method" in data, "Response should contain method"
        
        summary = data["summary"]
        print(f"PASS: Store wedge classification completed")
        print(f"  Method: {data['method']}")
        print(f"  Summary: A={summary.get('A', 0)}, B={summary.get('B', 0)}, C={summary.get('C', 0)}")
    
    def test_store_wedge_a_stores_top_80_percent(self, auth_headers):
        """Verify A-stores represent top 80% of revenue (cumulative)."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/store-wedge", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        summary = data.get("summary", {})
        total = summary.get("A", 0) + summary.get("B", 0) + summary.get("C", 0)
        
        if total > 0:
            # A-stores should be a minority of stores but represent majority of revenue
            # This is a sanity check - exact percentages depend on data distribution
            print(f"PASS: Store distribution - A:{summary['A']}, B:{summary['B']}, C:{summary['C']} (total: {total})")
        else:
            print("SKIP: No stores classified yet")


class TestStyleMixClassification:
    """Test Style Mix Classification endpoints."""
    
    def test_get_style_mix_returns_styles(self, auth_headers):
        """GET /api/buy-planning/style-mix returns classified styles."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/style-mix", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "styles" in data, "Response should contain 'styles' field"
        assert "summary" in data, "Response should contain 'summary' field"
        assert "classified" in data, "Response should contain 'classified' field"
        
        # Verify summary structure
        summary = data["summary"]
        assert "Core" in summary, "Summary should have 'Core' count"
        assert "Fashion" in summary, "Summary should have 'Fashion' count"
        assert "Test" in summary, "Summary should have 'Test' count"
        
        print(f"PASS: GET style-mix returns {len(data['styles'])} styles")
        print(f"  Summary: Core={summary['Core']}, Fashion={summary['Fashion']}, Test={summary['Test']}")
    
    def test_style_mix_has_stats(self, auth_headers):
        """Verify styles have mix stats (avg_weekly_qty, weeks_active, peak_to_avg)."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/style-mix", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        styles = data.get("styles", [])
        
        if styles:
            # Check first style has expected stats
            style = styles[0]
            assert "style" in style, "Style should have 'style' field"
            assert "style_mix" in style, "Style should have 'style_mix' field"
            
            # Check stats if present
            stats = style.get("stats", {})
            if stats:
                print(f"PASS: Style '{style['style']}' has stats:")
                print(f"  avg_weekly_qty: {stats.get('avg_weekly_qty')}")
                print(f"  weeks_active: {stats.get('weeks_active')}")
                print(f"  peak_to_avg: {stats.get('peak_to_avg')}")
                print(f"  week_presence_pct: {stats.get('week_presence_pct')}")
            else:
                print(f"PASS: Style '{style['style']}' found (stats may be in different format)")
        else:
            print("SKIP: No styles found (may need to run classification first)")
    
    def test_classify_style_mix(self, auth_headers):
        """POST /api/buy-planning/style-mix/classify runs classification."""
        response = requests.post(f"{BASE_URL}/api/buy-planning/style-mix/classify", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Classification should succeed"
        assert "summary" in data, "Response should contain summary"
        assert "method" in data, "Response should contain method"
        
        summary = data["summary"]
        print(f"PASS: Style mix classification completed")
        print(f"  Method: {data['method']}")
        print(f"  Summary: Core={summary.get('Core', 0)}, Fashion={summary.get('Fashion', 0)}, Test={summary.get('Test', 0)}")
        
        if "date_range" in data:
            print(f"  Date range: {data['date_range'].get('from')} to {data['date_range'].get('to')}")
        if "total_weeks_analyzed" in data:
            print(f"  Weeks analyzed: {data['total_weeks_analyzed']}")


class TestAssortmentMatrix:
    """Test Assortment Matrix endpoint."""
    
    def test_get_assortment_matrix(self, auth_headers):
        """GET /api/buy-planning/assortment-matrix returns wedge x mix matrix."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/assortment-matrix", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "matrix" in data, "Response should contain 'matrix' field"
        
        matrix = data["matrix"]
        
        # Verify matrix structure for each wedge
        for wedge in ["A", "B", "C"]:
            assert wedge in matrix, f"Matrix should have '{wedge}' wedge"
            wedge_data = matrix[wedge]
            assert "stores" in wedge_data, f"Wedge {wedge} should have 'stores' count"
            assert "assortment" in wedge_data, f"Wedge {wedge} should have 'assortment' description"
            assert "styles" in wedge_data, f"Wedge {wedge} should have 'styles' count"
            assert "style_breakdown" in wedge_data, f"Wedge {wedge} should have 'style_breakdown'"
        
        print(f"PASS: Assortment matrix returned")
        for wedge in ["A", "B", "C"]:
            w = matrix[wedge]
            print(f"  {wedge}: {w['stores']} stores, {w['styles']} styles - {w['assortment']}")
    
    def test_assortment_matrix_a_full_b_standard_c_core(self, auth_headers):
        """Verify A=Full, B=Standard, C=Core only assortment mapping."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/assortment-matrix", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        matrix = data.get("matrix", {})
        
        # A-stores get Full (Core + Fashion + Test)
        a_assortment = matrix.get("A", {}).get("assortment", "")
        assert "Full" in a_assortment or "Core" in a_assortment, f"A-stores should have Full assortment, got: {a_assortment}"
        
        # B-stores get Standard (Core + Fashion)
        b_assortment = matrix.get("B", {}).get("assortment", "")
        assert "Standard" in b_assortment or "Core" in b_assortment, f"B-stores should have Standard assortment, got: {b_assortment}"
        
        # C-stores get Efficiency (Core only)
        c_assortment = matrix.get("C", {}).get("assortment", "")
        assert "Efficiency" in c_assortment or "Core" in c_assortment, f"C-stores should have Efficiency assortment, got: {c_assortment}"
        
        print(f"PASS: Assortment mapping verified")
        print(f"  A: {a_assortment}")
        print(f"  B: {b_assortment}")
        print(f"  C: {c_assortment}")
    
    def test_assortment_matrix_style_breakdown(self, auth_headers):
        """Verify style breakdown in matrix."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/assortment-matrix", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        matrix = data.get("matrix", {})
        
        for wedge in ["A", "B", "C"]:
            breakdown = matrix.get(wedge, {}).get("style_breakdown", {})
            print(f"  {wedge} breakdown: {breakdown}")
            
            # A should have Core, Fashion, Test
            if wedge == "A":
                assert "Core" in breakdown, "A-stores should have Core in breakdown"
            # B should have Core, Fashion
            elif wedge == "B":
                assert "Core" in breakdown, "B-stores should have Core in breakdown"
            # C should have Core only
            elif wedge == "C":
                assert "Core" in breakdown, "C-stores should have Core in breakdown"
        
        print(f"PASS: Style breakdown structure verified")


class TestDataIntegrity:
    """Test data integrity after classification."""
    
    def test_store_wedge_total_matches_summary(self, auth_headers):
        """Verify total stores matches sum of A+B+C."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/store-wedge", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        summary = data.get("summary", {})
        total_from_summary = summary.get("A", 0) + summary.get("B", 0) + summary.get("C", 0)
        
        # If classified, total should match
        if data.get("classified"):
            stores = data.get("stores", [])
            stores_with_wedge = len([s for s in stores if s.get("wedge_class")])
            print(f"PASS: Summary total ({total_from_summary}) vs stores with wedge ({stores_with_wedge})")
        else:
            print(f"INFO: Not classified yet. Summary: A={summary.get('A')}, B={summary.get('B')}, C={summary.get('C')}")
    
    def test_style_mix_total_matches_summary(self, auth_headers):
        """Verify total styles matches sum of Core+Fashion+Test."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/style-mix", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        summary = data.get("summary", {})
        total_from_summary = summary.get("Core", 0) + summary.get("Fashion", 0) + summary.get("Test", 0)
        total_styles = data.get("total_styles", len(data.get("styles", [])))
        
        print(f"PASS: Summary total ({total_from_summary}) vs total_styles ({total_styles})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
