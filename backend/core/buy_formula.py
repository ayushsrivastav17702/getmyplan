"""
Canonical per-store Buy Formula.

CRITICAL RULE:
  display_minimum and safety_stock are ABSOLUTE per-store floors.
  They must NEVER be scaled by attribution_pct.

WHY:
  A store that needs 6 units on the floor to look presentable needs
  6 units regardless of whether it's an A-store (100%) or a C-store (20%).

CORRECT FORMULA:
  attributed_demand = target_multiplier * forecast * attribution_pct
  attributed_stock  = current_stock * attribution_pct
  demand_buy = max(attributed_demand - attributed_stock, 0)
  buy_qty = max(demand_buy, display_minimum, safety_stock)

BROKEN FORMULA (DO NOT USE):
  max((target_mult * forecast) - stock, display_min, safety_stock) * attribution_pct

The broken formula silently scales display_min + safety_stock down for B/C stores.
"""

from dataclasses import dataclass
from typing import Literal


BindingFactor = Literal["demand", "display_min", "safety_stock"]


@dataclass
class BuyInputs:
    forecast: float            # units forecasted for the period
    current_stock: float       # on-hand units at this store
    target_multiplier: float   # 1.2 Core / 0.8 Fashion / 0.4 Test
    attribution_pct: float     # 0.0-1.0  e.g. 0.6 for A-store
    display_minimum: int       # absolute floor — never scale this
    safety_stock: int          # absolute floor — never scale this


def calculate_buy_qty(inp: BuyInputs) -> dict:
    """
    Compute the per-store buy quantity with attribution applied ONLY
    to the demand signal, never to the absolute floors.

    Returns a dict with breakdown + the binding_factor that drove the result.
    """
    # Step 1: scale demand signal and existing stock by attribution
    attributed_demand = inp.target_multiplier * inp.forecast * inp.attribution_pct
    attributed_stock = inp.current_stock * inp.attribution_pct

    # Step 2: net demand after deducting attributed stock (floor at 0)
    demand_buy = max(attributed_demand - attributed_stock, 0)

    # Step 3: MAX against absolute per-store floors (NOT scaled)
    final_qty = max(demand_buy, inp.display_minimum, inp.safety_stock)

    # Which component drove the final quantity?
    if demand_buy >= inp.display_minimum and demand_buy >= inp.safety_stock:
        binding: BindingFactor = "demand"
    elif inp.display_minimum >= inp.safety_stock:
        binding = "display_min"
    else:
        binding = "safety_stock"

    return {
        "attributed_demand": round(attributed_demand, 1),
        "attributed_stock": round(attributed_stock, 1),
        "demand_buy": round(demand_buy, 1),
        "display_minimum": inp.display_minimum,
        "safety_stock": inp.safety_stock,
        "final_qty": round(final_qty),
        "binding_factor": binding,
    }
