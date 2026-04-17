"""
Test Sell-Through Config API endpoints for Buy Planning module.
Iteration 98: Config tab with editable multipliers.

Endpoints tested:
- GET /api/buy-planning/sell-through-config
- PUT /api/buy-planning/sell-through-config
- POST /api/buy-planning/sell-through-config/reset
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
    """Get authentication token for tests."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping tests")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestSellThroughConfigGet:
    """Tests for GET /api/buy-planning/sell-through-config"""
    
    def test_get_sell_through_config_returns_200(self, auth_headers):
        """GET returns 200 status code."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_get_sell_through_config_has_configs_array(self, auth_headers):
        """Response contains configs array."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers
        )
        data = response.json()
        assert "configs" in data, "Response missing 'configs' key"
        assert isinstance(data["configs"], list), "configs should be a list"
    
    def test_get_sell_through_config_has_three_style_mixes(self, auth_headers):
        """Response contains Core, Fashion, Test configs."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers
        )
        data = response.json()
        style_mixes = [c["style_mix"] for c in data["configs"]]
        assert "Core" in style_mixes, "Missing Core config"
        assert "Fashion" in style_mixes, "Missing Fashion config"
        assert "Test" in style_mixes, "Missing Test config"
    
    def test_get_sell_through_config_has_required_fields(self, auth_headers):
        """Each config has style_mix, target_multiplier, is_default."""
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers
        )
        data = response.json()
        for config in data["configs"]:
            assert "style_mix" in config, "Config missing style_mix"
            assert "target_multiplier" in config, "Config missing target_multiplier"
            assert "is_default" in config, "Config missing is_default"
    
    def test_get_sell_through_config_default_values(self, auth_headers):
        """Default multipliers are Core:1.2, Fashion:0.8, Test:0.4."""
        # First reset to defaults
        requests.post(
            f"{BASE_URL}/api/buy-planning/sell-through-config/reset",
            headers=auth_headers
        )
        
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers
        )
        data = response.json()
        
        defaults = {"Core": 1.2, "Fashion": 0.8, "Test": 0.4}
        for config in data["configs"]:
            expected = defaults.get(config["style_mix"])
            assert config["target_multiplier"] == expected, \
                f"{config['style_mix']} should be {expected}, got {config['target_multiplier']}"
            assert config["is_default"] == True, \
                f"{config['style_mix']} should be default after reset"


class TestSellThroughConfigPut:
    """Tests for PUT /api/buy-planning/sell-through-config"""
    
    def test_put_sell_through_config_success(self, auth_headers):
        """PUT updates multiplier and returns success."""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers,
            json={"style_mix": "Core", "target_multiplier": 1.5}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["success"] == True
        assert data["style_mix"] == "Core"
        assert data["target_multiplier"] == 1.5
    
    def test_put_sell_through_config_persists(self, auth_headers):
        """PUT persists the value in database."""
        # Update Fashion to 0.9
        requests.put(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers,
            json={"style_mix": "Fashion", "target_multiplier": 0.9}
        )
        
        # Verify via GET
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers
        )
        data = response.json()
        fashion_config = next(c for c in data["configs"] if c["style_mix"] == "Fashion")
        assert fashion_config["target_multiplier"] == 0.9
        assert fashion_config["is_default"] == False
    
    def test_put_sell_through_config_sets_updated_by(self, auth_headers):
        """PUT sets updated_by to current user email."""
        requests.put(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers,
            json={"style_mix": "Test", "target_multiplier": 0.5}
        )
        
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers
        )
        data = response.json()
        test_config = next(c for c in data["configs"] if c["style_mix"] == "Test")
        assert test_config.get("updated_by") == TEST_EMAIL
        assert "updated_at" in test_config
    
    def test_put_sell_through_config_invalid_style_mix(self, auth_headers):
        """PUT with invalid style_mix returns 400."""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers,
            json={"style_mix": "Invalid", "target_multiplier": 1.0}
        )
        assert response.status_code == 400
    
    def test_put_sell_through_config_multiplier_too_high(self, auth_headers):
        """PUT with multiplier > 5 returns 400."""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers,
            json={"style_mix": "Core", "target_multiplier": 6.0}
        )
        assert response.status_code == 400
    
    def test_put_sell_through_config_multiplier_negative(self, auth_headers):
        """PUT with negative multiplier returns 400."""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers,
            json={"style_mix": "Core", "target_multiplier": -1.0}
        )
        assert response.status_code == 400


class TestSellThroughConfigReset:
    """Tests for POST /api/buy-planning/sell-through-config/reset"""
    
    def test_reset_sell_through_config_success(self, auth_headers):
        """POST reset returns success with defaults."""
        response = requests.post(
            f"{BASE_URL}/api/buy-planning/sell-through-config/reset",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "defaults" in data
        assert data["defaults"]["Core"] == 1.2
        assert data["defaults"]["Fashion"] == 0.8
        assert data["defaults"]["Test"] == 0.4
    
    def test_reset_sell_through_config_clears_custom(self, auth_headers):
        """POST reset clears custom configs and returns to defaults."""
        # First set custom values
        requests.put(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers,
            json={"style_mix": "Core", "target_multiplier": 2.0}
        )
        requests.put(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers,
            json={"style_mix": "Fashion", "target_multiplier": 1.5}
        )
        
        # Reset
        requests.post(
            f"{BASE_URL}/api/buy-planning/sell-through-config/reset",
            headers=auth_headers
        )
        
        # Verify all are defaults
        response = requests.get(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            headers=auth_headers
        )
        data = response.json()
        for config in data["configs"]:
            assert config["is_default"] == True, \
                f"{config['style_mix']} should be default after reset"


class TestSellThroughConfigAuth:
    """Tests for authentication requirements."""
    
    def test_get_requires_auth(self):
        """GET without auth returns 400/401."""
        response = requests.get(f"{BASE_URL}/api/buy-planning/sell-through-config")
        assert response.status_code in [400, 401, 403]
    
    def test_put_requires_auth(self):
        """PUT without auth returns 400/401."""
        response = requests.put(
            f"{BASE_URL}/api/buy-planning/sell-through-config",
            json={"style_mix": "Core", "target_multiplier": 1.0}
        )
        assert response.status_code in [400, 401, 403]
    
    def test_reset_requires_auth(self):
        """POST reset without auth returns 400/401."""
        response = requests.post(f"{BASE_URL}/api/buy-planning/sell-through-config/reset")
        assert response.status_code in [400, 401, 403]


# Cleanup fixture to reset to defaults after all tests
@pytest.fixture(scope="module", autouse=True)
def cleanup(auth_headers):
    """Reset to defaults after all tests."""
    yield
    requests.post(
        f"{BASE_URL}/api/buy-planning/sell-through-config/reset",
        headers=auth_headers
    )
