"""
Regression test: pin the Buy Formula so the attribution-scaling bug cannot come back.

THE BUG (banned forever by this test):
    buy_qty = max(demand, display_min, safety_stock) * attribution_pct
    # ^ scales the absolute floors down for B/C stores — WRONG

THE FIX:
    demand_buy = max((target * forecast * attr_pct) - (stock * attr_pct), 0)
    buy_qty = max(demand_buy, display_min, safety_stock)
    # ^ attribution applied ONLY to demand signal; floors stay absolute
"""

import pytest
from backend.core.buy_formula import BuyInputs, calculate_buy_qty


# ────────────────────────────────────────────────────────────────────────────
# CANONICAL REGRESSION TEST — the one the user asked for explicitly.
# ────────────────────────────────────────────────────────────────────────────
def test_astore_and_cstore_get_same_display_min_when_demand_is_low():
    """
    When demand is low, an A-store (100% attribution) and a C-store (20% attribution)
    must both receive the FULL display_minimum. If either gets a scaled-down floor,
    the attribution bug has come back.
    """
    shared = dict(
        forecast=0,            # zero demand — floors must drive the answer
        current_stock=0,
        target_multiplier=1.2,  # Core
        display_minimum=6,
        safety_stock=2,
    )

    a_store = calculate_buy_qty(BuyInputs(attribution_pct=1.0, **shared))
    c_store = calculate_buy_qty(BuyInputs(attribution_pct=0.2, **shared))

    assert a_store["final_qty"] == 6, f"A-store expected 6, got {a_store['final_qty']}"
    assert c_store["final_qty"] == 6, f"C-store expected 6, got {c_store['final_qty']} — ATTRIBUTION BUG"
    assert a_store["final_qty"] == c_store["final_qty"], (
        "A-store and C-store floor quantities diverged — the attribution bug has returned."
    )
    assert a_store["binding_factor"] == "display_min"
    assert c_store["binding_factor"] == "display_min"


def test_astore_and_cstore_get_same_safety_stock_when_display_min_is_zero():
    """Same guarantee for safety_stock as the binding floor."""
    shared = dict(
        forecast=0, current_stock=0, target_multiplier=1.2,
        display_minimum=0,
        safety_stock=5,
    )
    a = calculate_buy_qty(BuyInputs(attribution_pct=1.0, **shared))
    c = calculate_buy_qty(BuyInputs(attribution_pct=0.2, **shared))
    assert a["final_qty"] == 5 and c["final_qty"] == 5
    assert a["binding_factor"] == "safety_stock"
    assert c["binding_factor"] == "safety_stock"


# ────────────────────────────────────────────────────────────────────────────
# Happy-path: when demand is high, attribution DOES scale the demand component.
# ────────────────────────────────────────────────────────────────────────────
def test_high_demand_scales_with_attribution():
    """A-store buys more than C-store when demand is the binding factor."""
    shared = dict(
        forecast=100, current_stock=0, target_multiplier=1.0,
        display_minimum=2, safety_stock=2,
    )
    a = calculate_buy_qty(BuyInputs(attribution_pct=1.0, **shared))  # 100 * 1.0 = 100
    c = calculate_buy_qty(BuyInputs(attribution_pct=0.2, **shared))  # 100 * 0.2 = 20

    assert a["final_qty"] == 100
    assert c["final_qty"] == 20
    assert a["binding_factor"] == "demand"
    assert c["binding_factor"] == "demand"


def test_demand_binding_uses_attributed_stock():
    """
    current_stock is also scaled by attribution — otherwise a store with very
    little allocated stock would look overstocked because we'd subtract the
    full company-wide SOH from a small attributed demand.
    """
    # Demand = 100 * 0.5 * 1.0 (mult) = 50, attributed_stock = 20 * 0.5 = 10
    # demand_buy = 50 - 10 = 40
    result = calculate_buy_qty(BuyInputs(
        forecast=100, current_stock=20, target_multiplier=1.0,
        attribution_pct=0.5, display_minimum=0, safety_stock=0,
    ))
    assert result["demand_buy"] == 40
    assert result["final_qty"] == 40


def test_negative_demand_floors_at_zero():
    """When attributed_stock > attributed_demand, demand_buy must floor at 0."""
    result = calculate_buy_qty(BuyInputs(
        forecast=10, current_stock=100, target_multiplier=1.0,
        attribution_pct=1.0, display_minimum=3, safety_stock=1,
    ))
    # attributed_demand=10, attributed_stock=100 -> demand_buy=0
    assert result["demand_buy"] == 0
    # Display min drives the result
    assert result["final_qty"] == 3
    assert result["binding_factor"] == "display_min"


# ────────────────────────────────────────────────────────────────────────────
# Meta test: explicitly demonstrate the broken formula FAILS this suite.
# This is here purely as documentation — if someone ever re-introduces the
# bug, the asserts above will flip. This test proves the broken formula
# would be caught.
# ────────────────────────────────────────────────────────────────────────────
def test_broken_formula_would_fail_the_regression():
    """
    Demonstrates that if someone re-introduces:
        buy_qty = max(demand, display_min, safety_stock) * attribution_pct
    the A==C display_min invariant breaks immediately.
    """
    def BROKEN_formula(forecast, stock, mult, attr, disp_min, safety):
        demand = max((mult * forecast) - stock, 0)
        return max(demand, disp_min, safety) * attr

    a = BROKEN_formula(forecast=0, stock=0, mult=1.2, attr=1.0, disp_min=6, safety=2)
    c = BROKEN_formula(forecast=0, stock=0, mult=1.2, attr=0.2, disp_min=6, safety=2)
    assert a == pytest.approx(6.0)
    assert c == pytest.approx(1.2)  # The bug: C-store would only receive 1.2 units of a 6-unit floor
    assert a != pytest.approx(c), "If this held, the broken formula would pass our test — it must not."
