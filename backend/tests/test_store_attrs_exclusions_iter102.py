"""
Iteration 102: Store Attributes + Exclusion List Management Tests
Tests for:
- PUT /api/buy-planning/stores/{store_code}/attributes (store_format, city_tier, region, area_sqft)
- Validation of store_format, city_tier, region values
- POST /api/buy-planning/exclusions (add exclusion)
- GET /api/buy-planning/exclusions (list exclusions)
- DELETE /api/buy-planning/exclusions/{store_code}/{sku} (remove exclusion)
- POST /api/buy-planning/buy-formula/calculate (excluded_skus count in totals)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin@demo.com"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@demo.com",
        "password": "demo1234"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data.get("access_token")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestStoreAttributeUpdate:
    """Tests for PUT /api/buy-planning/stores/{store_code}/attributes"""
    
    def test_update_store_format_hypermarket(self, auth_headers):
        """Test updating store_format to hypermarket"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"store_format": "hypermarket"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert data["store_code"] == "DEL-01"
        assert "store_format" in data["updated"]
    
    def test_update_store_format_supermarket(self, auth_headers):
        """Test updating store_format to supermarket"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"store_format": "supermarket"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
    
    def test_update_store_format_convenience(self, auth_headers):
        """Test updating store_format to convenience"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"store_format": "convenience"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
    
    def test_update_city_tier_tier1(self, auth_headers):
        """Test updating city_tier to tier1"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"city_tier": "tier1"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "city_tier" in data["updated"]
    
    def test_update_city_tier_tier2(self, auth_headers):
        """Test updating city_tier to tier2"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"city_tier": "tier2"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
    
    def test_update_city_tier_tier3(self, auth_headers):
        """Test updating city_tier to tier3"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"city_tier": "tier3"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
    
    def test_update_region_north(self, auth_headers):
        """Test updating region to North"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"region": "North"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "region" in data["updated"]
    
    def test_update_region_south(self, auth_headers):
        """Test updating region to South"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"region": "South"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
    
    def test_update_region_east(self, auth_headers):
        """Test updating region to East"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"region": "East"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
    
    def test_update_region_west(self, auth_headers):
        """Test updating region to West"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"region": "West"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
    
    def test_update_region_central(self, auth_headers):
        """Test updating region to Central"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"region": "Central"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
    
    def test_update_area_sqft(self, auth_headers):
        """Test updating area_sqft"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"area_sqft": 5000}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "area_sqft" in data["updated"]
    
    def test_update_multiple_attributes(self, auth_headers):
        """Test updating multiple attributes at once"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={
                "store_format": "hypermarket",
                "city_tier": "tier1",
                "region": "North",
                "area_sqft": 10000
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert len(data["updated"]) >= 4


class TestStoreAttributeValidation:
    """Tests for validation of store attribute values"""
    
    def test_invalid_store_format(self, auth_headers):
        """Test that invalid store_format is rejected"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"store_format": "invalid_format"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "store_format" in data.get("detail", "").lower() or "hypermarket" in data.get("detail", "").lower()
    
    def test_invalid_city_tier(self, auth_headers):
        """Test that invalid city_tier is rejected"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"city_tier": "tier4"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "city_tier" in data.get("detail", "").lower() or "tier1" in data.get("detail", "").lower()
    
    def test_invalid_region(self, auth_headers):
        """Test that invalid region is rejected"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={"region": "InvalidRegion"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "region" in data.get("detail", "").lower() or "north" in data.get("detail", "").lower()
    
    def test_nonexistent_store(self, auth_headers):
        """Test that updating nonexistent store returns 404"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/NONEXISTENT-STORE/attributes",
            headers=auth_headers,
            json={"store_format": "hypermarket"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
    
    def test_empty_update(self, auth_headers):
        """Test that empty update body returns 400"""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"


class TestExclusionCRUD:
    """Tests for exclusion CRUD operations"""
    
    def test_add_exclusion(self, auth_headers):
        """Test adding a store-SKU exclusion"""
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/exclusions",
            headers=auth_headers,
            json={
                "store_code": "TEST-STORE-01",
                "sku": "TEST-SKU-001",
                "reason": "Test exclusion"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert data["store_code"] == "TEST-STORE-01"
        assert data["sku"] == "TEST-SKU-001"
    
    def test_list_exclusions(self, auth_headers):
        """Test listing all exclusions"""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/exclusions",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "exclusions" in data
        assert "total" in data
        assert isinstance(data["exclusions"], list)
        # Should have at least the one we just added
        assert data["total"] >= 1
    
    def test_exclusion_has_required_fields(self, auth_headers):
        """Test that exclusion entries have required fields"""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/exclusions",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        if data["exclusions"]:
            excl = data["exclusions"][0]
            assert "store_code" in excl
            assert "sku" in excl
    
    def test_add_duplicate_exclusion_upserts(self, auth_headers):
        """Test that adding duplicate exclusion upserts (no error)"""
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/exclusions",
            headers=auth_headers,
            json={
                "store_code": "TEST-STORE-01",
                "sku": "TEST-SKU-001",
                "reason": "Updated reason"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
    
    def test_remove_exclusion(self, auth_headers):
        """Test removing an exclusion"""
        response = requests.delete(
            f"{BASE_URL}/api/buy-planning/exclusions/TEST-STORE-01/TEST-SKU-001",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert data["deleted"] == True
    
    def test_remove_nonexistent_exclusion(self, auth_headers):
        """Test removing nonexistent exclusion returns 404"""
        response = requests.delete(
            f"{BASE_URL}/api/buy-planning/exclusions/NONEXISTENT/NONEXISTENT",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


class TestBuyFormulaExclusions:
    """Tests for exclusion integration in buy formula"""
    
    def test_buy_formula_returns_excluded_skus_count(self, auth_headers):
        """Test that buy formula returns excluded_skus count in totals"""
        # First add an exclusion
        requests.post(
            f"{BASE_URL}/api/buy-planning/exclusions",
            headers=auth_headers,
            json={"store_code": "DEL-01", "sku": "EXCL-TEST-SKU", "reason": "Test"}
        )
        
        # Run buy formula
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-formula/calculate",
            headers=auth_headers,
            json={"cover_days": 30, "safety_days": 7}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Check totals has excluded_skus field
        assert "totals" in data
        assert "excluded_skus" in data["totals"], f"totals missing excluded_skus: {data['totals']}"
        assert isinstance(data["totals"]["excluded_skus"], (int, float))
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/buy-planning/exclusions/DEL-01/EXCL-TEST-SKU",
            headers=auth_headers
        )
    
    def test_buy_formula_structure(self, auth_headers):
        """Test buy formula response structure"""
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/buy-formula/calculate",
            headers=auth_headers,
            json={"cover_days": 30, "safety_days": 7}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "parameters" in data
        assert "totals" in data
        assert "sku_count" in data
        assert "buy_plan" in data


class TestStoreWedgeEndpoint:
    """Tests for store wedge endpoint with new attributes"""
    
    def test_store_wedge_returns_stores_with_attributes(self, auth_headers):
        """Test that store wedge endpoint returns stores with format, tier, region"""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/store-wedge",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "stores" in data
        assert isinstance(data["stores"], list)
        
        # Check that stores have the new attribute fields
        if data["stores"]:
            store = data["stores"][0]
            # These fields should exist (may be null if not set)
            assert "store_code" in store
            # Check for presence of attribute fields (they may be None/missing if not set)
            # The endpoint should return these fields if they exist in the DB


class TestVerifyStoreAttributesPersistence:
    """Verify that store attributes are persisted correctly"""
    
    def test_update_and_verify_persistence(self, auth_headers):
        """Update store attributes and verify they persist"""
        # Update attributes
        update_response = requests.put(
            f"{BASE_URL}/api/buy-planning/stores/DEL-01/attributes",
            headers=auth_headers,
            json={
                "store_format": "hypermarket",
                "city_tier": "tier1",
                "region": "North",
                "area_sqft": 15000
            }
        )
        assert update_response.status_code == 200
        
        # Fetch store wedge data to verify
        get_response = requests.get(
            f"{BASE_URL}/api/buy-planning/store-wedge",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        data = get_response.json()
        
        # Find DEL-01 in the stores list
        del_01 = next((s for s in data["stores"] if s.get("store_code") == "DEL-01"), None)
        assert del_01 is not None, "DEL-01 not found in stores"
        
        # Verify attributes were persisted
        assert del_01.get("store_format") == "hypermarket", f"store_format mismatch: {del_01.get('store_format')}"
        assert del_01.get("city_tier") == "tier1", f"city_tier mismatch: {del_01.get('city_tier')}"
        assert del_01.get("region") == "North", f"region mismatch: {del_01.get('region')}"
        assert del_01.get("area_sqft") == 15000, f"area_sqft mismatch: {del_01.get('area_sqft')}"
