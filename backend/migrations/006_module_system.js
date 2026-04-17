// ============================================
// MODULE SYSTEM MIGRATION
// Run: mongosh <DB_NAME> --file migrations/006_module_system.js
// ============================================

print("Starting Module System Migration...");

// 1. Create module_definitions collection
print("Creating module_definitions collection...");
db.createCollection("module_definitions");

// 2. Seed module definitions
print("Seeding module definitions...");

// Clear existing definitions to make idempotent
db.module_definitions.deleteMany({});

db.module_definitions.insertMany([
  {
    module_id: "core_classification",
    module_name: "Core Classification",
    description: "Store wedge, style mix, and attribution matrix",
    category: "foundation",
    icon: "Tag",
    is_core: true,
    is_paid: false,
    order: 1,
    features: [
      { feature_id: "store_wedge", name: "Store Wedge", description: "A/B/C store classification", is_core: true },
      { feature_id: "style_mix", name: "Style Mix", description: "Core/Fashion/Test SKU tagging", is_core: true },
      { feature_id: "attribution", name: "Attribution", description: "SKU to store wedge allocation", is_core: true }
    ]
  },
  {
    module_id: "buy_planning",
    module_name: "Buy Planning",
    description: "Generate and manage purchase plans",
    category: "operations",
    icon: "ShoppingCart",
    is_core: true,
    is_paid: false,
    order: 2,
    features: [
      { feature_id: "full_buy_formula", name: "Full Buy Formula", description: "Advanced buy calculation", is_core: true },
      { feature_id: "multi_level_approval", name: "Multi-Level Approval", description: "Multi-stage approval workflow", is_core: false },
      { feature_id: "order_consolidation", name: "Order Consolidation", description: "Consolidate store orders into supplier POs", is_core: false },
      { feature_id: "phased_replenishment", name: "Phased Replenishment", description: "Split orders into multiple shipments", is_core: false }
    ]
  },
  {
    module_id: "inventory_management",
    module_name: "Inventory Management",
    description: "DOH analysis, stockout tracking, inventory health",
    category: "inventory",
    icon: "Package",
    is_core: true,
    is_paid: false,
    order: 3,
    features: [
      { feature_id: "doh_analysis", name: "DOH Analysis", description: "Days on hand tracking", is_core: true },
      { feature_id: "stockout_analysis", name: "Stockout Analysis", description: "Stockout detection and reporting", is_core: true },
      { feature_id: "statistical_safety_stock", name: "Statistical Safety Stock", description: "z-score x MAD x sqrt(LT/RP)", is_core: false }
    ]
  },
  {
    module_id: "space_planning",
    module_name: "Space Planning",
    description: "Planogram, facings optimization, store capacity",
    category: "space",
    icon: "Layout",
    is_core: false,
    is_paid: true,
    order: 4,
    features: [
      { feature_id: "planogram_library", name: "Planogram Library", description: "Shelf layout management", is_core: false },
      { feature_id: "facings_optimizer", name: "Facings Optimizer", description: "LP-based facing optimization", is_core: false }
    ]
  },
  {
    module_id: "ai_insights",
    module_name: "AI Insights",
    description: "AI-powered demand forecasting and readiness audit",
    category: "analytics",
    icon: "Brain",
    is_core: false,
    is_paid: true,
    order: 5,
    features: [
      { feature_id: "demand_forecasting", name: "Demand Forecasting", description: "ML-based demand prediction", is_core: false },
      { feature_id: "readiness_audit", name: "Readiness Audit", description: "LLM-powered pre-buy analysis", is_core: false }
    ]
  }
]);

// 3. Add module_access and scope to users (if not already present)
print("Adding module_access and scope to users...");
db.users.updateMany(
  { module_access: { $exists: false } },
  {
    $set: {
      module_access: {
        core_classification: { access: "full", actions: ["view", "edit"] },
        buy_planning: { access: "full", actions: ["view", "edit", "approve"] },
        inventory_management: { access: "read_only", actions: ["view"] },
        space_planning: { access: "none", actions: [] },
        ai_insights: { access: "none", actions: [] }
      },
      scope: {
        categories: [],
        regions: [],
        store_wedges: [],
        stores: []
      }
    }
  }
);

// 4. Add modules, subscription, limits, usage to tenants (if not already present)
print("Adding module config to tenants...");
db.tenants.updateMany(
  { modules: { $exists: false } },
  {
    $set: {
      modules: {
        core_classification: { enabled: true, features: ["store_wedge", "style_mix", "attribution"] },
        buy_planning: { enabled: true, features: ["full_buy_formula"] },
        inventory_management: { enabled: true, features: ["doh_analysis", "stockout_analysis"] },
        space_planning: { enabled: false, features: [] },
        ai_insights: { enabled: false, features: [] }
      },
      subscription: {
        plan: "enterprise",
        tier: "tier_1",
        start_date: new Date(),
        end_date: new Date(new Date().setFullYear(new Date().getFullYear() + 1)),
        billing_cycle: "annual",
        auto_renew: true,
        status: "active"
      },
      limits: {
        max_stores: 3000,
        max_skus: 130000,
        max_users: 200,
        max_api_calls_per_day: 1000000,
        storage_gb: 500,
        data_retention_days: 90
      },
      usage: {
        current_stores: 0,
        current_skus: 0,
        current_users: 0,
        api_calls_today: 0,
        storage_used_gb: 0,
        last_updated: new Date()
      }
    }
  }
);

// 5. Create indexes
print("Creating indexes...");
db.module_definitions.createIndex({ module_id: 1 }, { unique: true });
db.tenants.createIndex({ "subscription.end_date": 1 });

print("Module System Migration Complete!");
