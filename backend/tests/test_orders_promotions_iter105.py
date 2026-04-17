"""
Iteration 105: Multi-Store Order Consolidation, Phased Replenishment, Promotion Calendar
Tests for:
- POST /api/buy-planning/orders/consolidate - groups plan items by category into POs
- GET /api/buy-planning/orders - lists POs with po_number, supplier_group, units, value, status
- GET /api/buy-planning/orders/{po_number} - returns PO with items
- PUT /api/buy-planning/orders/{po_number}/status - updates status workflow
- POST /api/buy-planning/orders/phase - creates phased shipments from a PO
- GET /api/buy-planning/orders/phased - lists phased POs
- POST /api/buy-planning/promotions - creates a promotion
- GET /api/buy-planning/promotions - lists promotions
- DELETE /api/buy-planning/promotions/{promo_id} - deletes a promotion
- GET /api/buy-planning/promotions/active-lift - returns active promotions
- POST /api/buy-planning/buy-formula/calculate - applies promo_lift to affected SKUs
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

class TestOrdersPromotions:
    """Tests for Order Consolidation, Phased Replenishment, and Promotions"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "demo1234"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("access_token")
        assert token, "No access_token in login response"
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        yield
        
        self.session.close()

    # ═══════════════════════════════════════════════════
    # ORDER CONSOLIDATION TESTS
    # ═══════════════════════════════════════════════════
    
    def test_01_list_orders_returns_array(self):
        """GET /api/buy-planning/orders returns orders array"""
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/orders")
        assert resp.status_code == 200, f"List orders failed: {resp.text}"
        data = resp.json()
        assert "orders" in data, "Response missing 'orders' field"
        assert "total" in data, "Response missing 'total' field"
        assert isinstance(data["orders"], list), "orders should be a list"
        print(f"TEST_01 PASS: List orders returned {data['total']} POs")
    
    def test_02_orders_have_required_fields(self):
        """Orders have po_number, supplier_group, total_units, total_value, status"""
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/orders")
        assert resp.status_code == 200
        data = resp.json()
        if data["orders"]:
            order = data["orders"][0]
            required_fields = ["po_number", "supplier_group", "total_units", "total_value", "status"]
            for field in required_fields:
                assert field in order, f"Order missing '{field}' field"
            print(f"TEST_02 PASS: Order has all required fields: {list(order.keys())}")
        else:
            print("TEST_02 SKIP: No orders to verify fields")
    
    def test_03_get_single_order_by_po_number(self):
        """GET /api/buy-planning/orders/{po_number} returns PO with items"""
        # First get list of orders
        list_resp = self.session.get(f"{BASE_URL}/api/buy-planning/orders")
        assert list_resp.status_code == 200
        orders = list_resp.json().get("orders", [])
        
        if orders:
            po_number = orders[0]["po_number"]
            resp = self.session.get(f"{BASE_URL}/api/buy-planning/orders/{po_number}")
            assert resp.status_code == 200, f"Get order failed: {resp.text}"
            data = resp.json()
            assert data["po_number"] == po_number, "PO number mismatch"
            assert "items" in data, "Response missing 'items' field"
            print(f"TEST_03 PASS: Got order {po_number} with {len(data.get('items', []))} items")
        else:
            print("TEST_03 SKIP: No orders to fetch")
    
    def test_04_get_nonexistent_order_returns_404(self):
        """GET /api/buy-planning/orders/NONEXISTENT returns 404"""
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/orders/NONEXISTENT-PO-12345")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("TEST_04 PASS: Nonexistent PO returns 404")
    
    # ═══════════════════════════════════════════════════
    # PO STATUS WORKFLOW TESTS
    # ═══════════════════════════════════════════════════
    
    def test_05_update_po_status_valid(self):
        """PUT /api/buy-planning/orders/{po_number}/status updates status"""
        list_resp = self.session.get(f"{BASE_URL}/api/buy-planning/orders")
        orders = list_resp.json().get("orders", [])
        
        if orders:
            # Find a draft order or any order
            po_number = orders[0]["po_number"]
            current_status = orders[0]["status"]
            
            # Try to update to 'sent' if draft, or back to 'draft' if not
            new_status = "sent" if current_status == "draft" else "draft"
            
            resp = self.session.put(f"{BASE_URL}/api/buy-planning/orders/{po_number}/status", json={
                "status": new_status
            })
            assert resp.status_code == 200, f"Update status failed: {resp.text}"
            data = resp.json()
            assert data["success"] == True
            assert data["status"] == new_status
            print(f"TEST_05 PASS: Updated {po_number} status to {new_status}")
            
            # Revert status
            self.session.put(f"{BASE_URL}/api/buy-planning/orders/{po_number}/status", json={
                "status": current_status
            })
        else:
            print("TEST_05 SKIP: No orders to update status")
    
    def test_06_update_po_status_invalid_returns_400(self):
        """PUT /api/buy-planning/orders/{po_number}/status with invalid status returns 400"""
        list_resp = self.session.get(f"{BASE_URL}/api/buy-planning/orders")
        orders = list_resp.json().get("orders", [])
        
        if orders:
            po_number = orders[0]["po_number"]
            resp = self.session.put(f"{BASE_URL}/api/buy-planning/orders/{po_number}/status", json={
                "status": "invalid_status"
            })
            assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
            print("TEST_06 PASS: Invalid status returns 400")
        else:
            print("TEST_06 SKIP: No orders to test invalid status")
    
    def test_07_po_status_workflow_all_valid_statuses(self):
        """All valid PO statuses are accepted: draft, sent, confirmed, shipped, received, cancelled"""
        valid_statuses = ["draft", "sent", "confirmed", "shipped", "received", "cancelled"]
        list_resp = self.session.get(f"{BASE_URL}/api/buy-planning/orders")
        orders = list_resp.json().get("orders", [])
        
        if orders:
            po_number = orders[0]["po_number"]
            original_status = orders[0]["status"]
            
            for status in valid_statuses:
                resp = self.session.put(f"{BASE_URL}/api/buy-planning/orders/{po_number}/status", json={
                    "status": status
                })
                assert resp.status_code == 200, f"Status '{status}' failed: {resp.text}"
            
            # Revert to original
            self.session.put(f"{BASE_URL}/api/buy-planning/orders/{po_number}/status", json={
                "status": original_status
            })
            print(f"TEST_07 PASS: All valid statuses accepted: {valid_statuses}")
        else:
            print("TEST_07 SKIP: No orders to test status workflow")
    
    # ═══════════════════════════════════════════════════
    # PHASED REPLENISHMENT TESTS
    # ═══════════════════════════════════════════════════
    
    def test_08_list_phased_pos(self):
        """GET /api/buy-planning/orders/phased returns phased POs"""
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/orders/phased")
        assert resp.status_code == 200, f"List phased POs failed: {resp.text}"
        data = resp.json()
        assert "phased_pos" in data, "Response missing 'phased_pos' field"
        assert "total" in data, "Response missing 'total' field"
        print(f"TEST_08 PASS: List phased POs returned {data['total']} records")
    
    def test_09_create_phased_po_percentages_must_sum_100(self):
        """POST /api/buy-planning/orders/phase requires percentages sum to 100"""
        list_resp = self.session.get(f"{BASE_URL}/api/buy-planning/orders")
        orders = list_resp.json().get("orders", [])
        
        # Find a non-phased order
        non_phased = [o for o in orders if not o.get("is_phased")]
        
        if non_phased:
            po_number = non_phased[0]["po_number"]
            
            # Test with percentages that don't sum to 100
            resp = self.session.post(f"{BASE_URL}/api/buy-planning/orders/phase", json={
                "po_number": po_number,
                "phase_weeks": [0, 2, 4],
                "phase_percentages": [40, 30, 20]  # Sum = 90, not 100
            })
            assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
            assert "100" in resp.text.lower() or "sum" in resp.text.lower(), "Error should mention sum to 100"
            print("TEST_09 PASS: Percentages not summing to 100 returns 400")
        else:
            print("TEST_09 SKIP: No non-phased orders to test")
    
    def test_10_create_phased_po_weeks_pcts_same_length(self):
        """POST /api/buy-planning/orders/phase requires weeks and percentages same length"""
        list_resp = self.session.get(f"{BASE_URL}/api/buy-planning/orders")
        orders = list_resp.json().get("orders", [])
        non_phased = [o for o in orders if not o.get("is_phased")]
        
        if non_phased:
            po_number = non_phased[0]["po_number"]
            
            resp = self.session.post(f"{BASE_URL}/api/buy-planning/orders/phase", json={
                "po_number": po_number,
                "phase_weeks": [0, 2],  # 2 items
                "phase_percentages": [50, 30, 20]  # 3 items
            })
            assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
            print("TEST_10 PASS: Mismatched weeks/percentages length returns 400")
        else:
            print("TEST_10 SKIP: No non-phased orders to test")
    
    def test_11_phased_po_has_shipments(self):
        """Phased POs have shipments array with phase, weeks_from_now, percentage, items"""
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/orders/phased")
        phased = resp.json().get("phased_pos", [])
        
        if phased:
            po = phased[0]
            assert "shipments" in po, "Phased PO missing 'shipments' field"
            assert "phase_count" in po, "Phased PO missing 'phase_count' field"
            
            if po["shipments"]:
                shipment = po["shipments"][0]
                required = ["phase", "weeks_from_now", "percentage", "items", "total_units", "total_value"]
                for field in required:
                    assert field in shipment, f"Shipment missing '{field}' field"
            print(f"TEST_11 PASS: Phased PO has {po['phase_count']} shipments with required fields")
        else:
            print("TEST_11 SKIP: No phased POs to verify")
    
    # ═══════════════════════════════════════════════════
    # PROMOTION CALENDAR TESTS
    # ═══════════════════════════════════════════════════
    
    def test_12_list_promotions(self):
        """GET /api/buy-planning/promotions returns promotions array"""
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/promotions")
        assert resp.status_code == 200, f"List promotions failed: {resp.text}"
        data = resp.json()
        assert "promotions" in data, "Response missing 'promotions' field"
        assert "total" in data, "Response missing 'total' field"
        print(f"TEST_12 PASS: List promotions returned {data['total']} records")
    
    def test_13_create_promotion(self):
        """POST /api/buy-planning/promotions creates a promotion"""
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/promotions", json={
            "name": "TEST-PROMO-ITER105",
            "promo_type": "national",
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
            "discount_type": "percentage",
            "discount_value": 20,
            "affected_categories": ["Footwear", "Apparel"],
            "lift_factor": 1.5,
            "notes": "Test promotion for iteration 105"
        })
        assert resp.status_code == 200, f"Create promotion failed: {resp.text}"
        data = resp.json()
        assert data["success"] == True
        assert "promo_id" in data
        self.test_promo_id = data["promo_id"]
        print(f"TEST_13 PASS: Created promotion {data['promo_id']}")
    
    def test_14_promotion_has_required_fields(self):
        """Promotions have name, promo_type, start_date, end_date, lift_factor, affected_categories"""
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/promotions")
        promos = resp.json().get("promotions", [])
        
        if promos:
            promo = promos[0]
            required = ["name", "promo_type", "start_date", "end_date", "lift_factor", "affected_categories", "status"]
            for field in required:
                assert field in promo, f"Promotion missing '{field}' field"
            print(f"TEST_14 PASS: Promotion has all required fields")
        else:
            print("TEST_14 SKIP: No promotions to verify")
    
    def test_15_create_promotion_lift_factor_validation(self):
        """POST /api/buy-planning/promotions validates lift_factor (0.5-5)"""
        # Test lift_factor too low
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/promotions", json={
            "name": "TEST-INVALID-LIFT",
            "start_date": "2026-07-01",
            "end_date": "2026-07-31",
            "lift_factor": 0.1  # Too low
        })
        assert resp.status_code == 400, f"Expected 400 for low lift_factor, got {resp.status_code}"
        
        # Test lift_factor too high
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/promotions", json={
            "name": "TEST-INVALID-LIFT",
            "start_date": "2026-07-01",
            "end_date": "2026-07-31",
            "lift_factor": 10  # Too high
        })
        assert resp.status_code == 400, f"Expected 400 for high lift_factor, got {resp.status_code}"
        print("TEST_15 PASS: lift_factor validation works (0.5-5 range)")
    
    def test_16_delete_promotion(self):
        """DELETE /api/buy-planning/promotions/{promo_id} deletes a promotion"""
        # First create a promotion to delete
        create_resp = self.session.post(f"{BASE_URL}/api/buy-planning/promotions", json={
            "name": "TEST-DELETE-PROMO",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "lift_factor": 1.2
        })
        assert create_resp.status_code == 200
        promo_id = create_resp.json()["promo_id"]
        
        # Delete it
        resp = self.session.delete(f"{BASE_URL}/api/buy-planning/promotions/{promo_id}")
        assert resp.status_code == 200, f"Delete promotion failed: {resp.text}"
        data = resp.json()
        assert data["success"] == True
        assert data["deleted"] == True
        
        # Verify it's gone
        get_resp = self.session.get(f"{BASE_URL}/api/buy-planning/promotions")
        promos = get_resp.json().get("promotions", [])
        promo_ids = [p.get("promo_id") for p in promos]
        assert promo_id not in promo_ids, "Deleted promotion still exists"
        print(f"TEST_16 PASS: Deleted promotion {promo_id}")
    
    def test_17_delete_nonexistent_promotion_returns_404(self):
        """DELETE /api/buy-planning/promotions/NONEXISTENT returns 404"""
        resp = self.session.delete(f"{BASE_URL}/api/buy-planning/promotions/NONEXISTENT-PROMO-12345")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("TEST_17 PASS: Delete nonexistent promotion returns 404")
    
    def test_18_get_active_lift_factors(self):
        """GET /api/buy-planning/promotions/active-lift returns active promotions"""
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/promotions/active-lift")
        assert resp.status_code == 200, f"Get active lift failed: {resp.text}"
        data = resp.json()
        assert "active_promotions" in data, "Response missing 'active_promotions' field"
        assert "total" in data, "Response missing 'total' field"
        
        if data["active_promotions"]:
            promo = data["active_promotions"][0]
            assert "lift_factor" in promo, "Active promo missing 'lift_factor'"
            assert "affected_categories" in promo, "Active promo missing 'affected_categories'"
        print(f"TEST_18 PASS: Active lift factors returned {data['total']} promotions")
    
    # ═══════════════════════════════════════════════════
    # BUY FORMULA PROMO LIFT INTEGRATION
    # ═══════════════════════════════════════════════════
    
    def test_19_buy_formula_includes_promo_lift(self):
        """POST /api/buy-planning/buy-formula/calculate includes promo_lift field"""
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/buy-formula/calculate", json={
            "cover_days": 30,
            "safety_days": 7
        })
        assert resp.status_code == 200, f"Buy formula failed: {resp.text}"
        data = resp.json()
        
        if data.get("buy_plan"):
            item = data["buy_plan"][0]
            assert "promo_lift" in item, "Buy plan item missing 'promo_lift' field"
            print(f"TEST_19 PASS: Buy formula items have promo_lift field (first item: {item['promo_lift']})")
        else:
            print("TEST_19 SKIP: No buy plan items to verify")
    
    # ═══════════════════════════════════════════════════
    # ORDER CONSOLIDATION TESTS
    # ═══════════════════════════════════════════════════
    
    def test_20_consolidate_orders_requires_plan_id(self):
        """POST /api/buy-planning/orders/consolidate requires plan_id"""
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/orders/consolidate", json={})
        # Should fail with validation error
        assert resp.status_code in [400, 422], f"Expected 400/422, got {resp.status_code}"
        print("TEST_20 PASS: Consolidate requires plan_id")
    
    def test_21_consolidate_orders_invalid_plan_returns_404(self):
        """POST /api/buy-planning/orders/consolidate with invalid plan_id returns 404"""
        resp = self.session.post(f"{BASE_URL}/api/buy-planning/orders/consolidate", json={
            "plan_id": "000000000000000000000000"  # Valid ObjectId format but doesn't exist
        })
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("TEST_21 PASS: Invalid plan_id returns 404")
    
    def test_22_orders_filter_by_status(self):
        """GET /api/buy-planning/orders?status=draft filters by status"""
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/orders?status=draft")
        assert resp.status_code == 200
        data = resp.json()
        
        for order in data.get("orders", []):
            assert order["status"] == "draft", f"Order status is {order['status']}, expected draft"
        print(f"TEST_22 PASS: Status filter works, returned {data['total']} draft orders")
    
    # ═══════════════════════════════════════════════════
    # CLEANUP
    # ═══════════════════════════════════════════════════
    
    def test_99_cleanup_test_promotions(self):
        """Cleanup: Delete test promotions created during tests"""
        resp = self.session.get(f"{BASE_URL}/api/buy-planning/promotions")
        promos = resp.json().get("promotions", [])
        
        deleted = 0
        for promo in promos:
            if promo.get("name", "").startswith("TEST-"):
                del_resp = self.session.delete(f"{BASE_URL}/api/buy-planning/promotions/{promo['promo_id']}")
                if del_resp.status_code == 200:
                    deleted += 1
        
        print(f"TEST_99 PASS: Cleaned up {deleted} test promotions")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
