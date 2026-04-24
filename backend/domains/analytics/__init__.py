"""Analytics domain package.

Houses tenant-facing analytical primitives that sit alongside the core
buy_planning domain but stand on their own (they query SKU/sales data without
needing the buy-formula pipeline).

## Current verticals
- `attribute_grouping`: roll up sales by configurable SKU attribute levels
  (category / style / size / color / user-defined `attributes.*`) to surface
  trends, compare performers, and forecast demand for new attribute combos.

Follow the same Repository + pure-service pattern used by `domains/buy_planning/*`
so every algorithm is unit-testable without Mongo.
"""
