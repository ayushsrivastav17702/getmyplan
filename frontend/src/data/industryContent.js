// CMS-Style Industries Content Mapping
// Used by the shared IndustryPage template at /industries/:slug

export const industryContent = {
  // ───────────────────────────────────────────── Apparel
  "apparel": {
    slug: "apparel",
    kicker: "Apparel Industry",
    kickerColor: "indigo",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Apparel Brands",
    heroGradient: "from-indigo-500 to-rose-500",
    tagline: "Manage SKU explosion across sizes, colors, and styles. Forecast demand for every variant across every store with AI-powered precision.",
    metaDescription: "AI demand planning for apparel brands. Handle size-color SKU explosion with 92.7% forecast accuracy across 130,000+ SKUs.",
    metaKeywords: "apparel planning, clothing inventory, size color planning, fashion SKU planning",

    challenges: [
      { icon: "🧵", title: "SKU Explosion", description: "One style × 5 colors × 8 sizes = 40 SKUs to plan for every single item." },
      { icon: "🗓️", title: "Seasonal Cycles", description: "Summer, Monsoon, Winter, Festival — each with its own buying rhythm." },
      { icon: "📉", title: "End-of-Season Markdowns", description: "Leftover stock erodes margin when forecasts miss the mark." },
    ],

    howWeHelp: [
      { icon: "🎨", title: "Variant-Level Forecasting", description: "Separate forecasts per size and color using variant-aware models." },
      { icon: "🍂", title: "Seasonal Pattern Detection", description: "Auto-detect Diwali, Christmas, monsoon, and back-to-school lifts." },
      { icon: "🏷️", title: "Style Mix Optimization", description: "Core / Fashion / Test tagging ensures the right product mix per store." },
      { icon: "📊", title: "Size Curve Planning", description: "Size-specific demand curves prevent size-level stockouts." },
    ],

    keyFeatures: [
      "Size × Color Forecasting",
      "Seasonal Lift Factors",
      "Size Curve Analytics",
      "Markdown Optimization",
      "Multi-Store Allocation",
      "Return Rate Modeling",
    ],

    ctaTitle: "Ready to solve apparel's SKU explosion?",
  },

  // ───────────────────────────────────────────── Footwear
  "footwear": {
    slug: "footwear",
    kicker: "Footwear Industry",
    kickerColor: "amber",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Footwear Brands",
    heroGradient: "from-amber-500 to-orange-500",
    tagline: "Plan across gender, size-runs, and widths with confidence. Keep bestsellers in stock without drowning in broken size runs.",
    metaDescription: "AI demand planning for footwear brands. Size run optimization, gender splits, and width planning with 92.7% forecast accuracy.",
    metaKeywords: "footwear planning, shoe inventory, size run planning, shoe demand forecasting",

    challenges: [
      { icon: "👟", title: "Size Run Complexity", description: "Full-run buys mean half your inventory is in sizes that barely sell." },
      { icon: "⚖️", title: "Gender Splits", description: "Men's, women's, kids — each with a different size distribution." },
      { icon: "📐", title: "Width Variants", description: "Narrow, regular, wide — another dimension of SKU complexity." },
      { icon: "🔁", title: "Broken Size Runs", description: "Missing the one size a customer wants kills the sale." },
    ],

    howWeHelp: [
      { icon: "📈", title: "Size-Run Forecasting", description: "Forecast each size independently — not as a percentage of a full run." },
      { icon: "🚻", title: "Gender-Aware Models", description: "Separate demand curves for men, women, and kids." },
      { icon: "🎯", title: "Fit-Profile Allocation", description: "Allocate wider widths to stores with that fit demographic." },
      { icon: "🔄", title: "Inter-Store Size Transfers", description: "Rebalance size runs across stores automatically." },
    ],

    keyFeatures: [
      "Size-Run Forecasting",
      "Gender Demand Splits",
      "Width-Aware Allocation",
      "Broken-Run Alerts",
      "Store Transfer Recommendations",
      "Category Health Scorecard",
    ],

    ctaTitle: "Ready to master footwear size runs?",
  },

  // ───────────────────────────────────────────── Accessories
  "accessories": {
    slug: "accessories",
    kicker: "Accessories Industry",
    kickerColor: "pink",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Accessories Brands",
    heroGradient: "from-rose-500 to-pink-500",
    tagline: "High margin, low volume, trend-driven. Forecast bags, jewelry, and belts with precision and protect brand value.",
    metaDescription: "AI demand planning for accessories — bags, jewelry, belts, watches. High-margin SKU planning with 92.7% forecast accuracy.",
    metaKeywords: "accessories planning, handbag inventory, jewelry planning, belt inventory",

    challenges: [
      { icon: "💼", title: "High Unit Value", description: "One wrong buy decision equals thousands in dead stock capital." },
      { icon: "⭐", title: "Trend Volatility", description: "Hero SKUs can sell out in days or sit for months." },
      { icon: "🪞", title: "Display Dependency", description: "Without display presence, accessories sell-through collapses." },
    ],

    howWeHelp: [
      { icon: "💎", title: "Low-Volume-Tuned Models", description: "Specialized algorithms for high-value, low-quantity SKUs." },
      { icon: "📈", title: "Trend Breakout Detection", description: "Identify hero SKUs within 48 hours of a trend signal." },
      { icon: "🪟", title: "Display Minimum Enforcement", description: "Never drop below display threshold — even in slow stores." },
      { icon: "🛡️", title: "Markdown Protection", description: "Predictive markdown timing safeguards your margin." },
    ],

    keyFeatures: [
      "High-Value SKU Forecasting",
      "Trend Breakout Alerts",
      "Display Minimum Rules",
      "Margin Optimization",
      "Hero SKU Replenishment",
      "VIP Store Prioritization",
    ],

    ctaTitle: "Ready to optimize your accessories planning?",
  },

  // ───────────────────────────────────────────── Beauty & Cosmetics
  "beauty-cosmetics": {
    slug: "beauty-cosmetics",
    kicker: "Beauty & Cosmetics Industry",
    kickerColor: "purple",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Beauty & Cosmetics",
    heroGradient: "from-purple-500 to-fuchsia-500",
    tagline: "Manage shades, formulations, and expiry dates. Plan demand across hundreds of variants with shelf-life awareness.",
    metaDescription: "AI demand planning for beauty and cosmetics brands. Shade-level forecasting with expiry and shelf-life awareness.",
    metaKeywords: "cosmetics planning, beauty inventory, shade planning, makeup inventory, skincare planning",

    challenges: [
      { icon: "🎨", title: "Shade Proliferation", description: "One lipstick × 30 shades × 5 finishes = 150 SKUs per product." },
      { icon: "⏳", title: "Expiry & Shelf Life", description: "Dead stock becomes write-off the moment it expires." },
      { icon: "🔥", title: "Viral Spikes", description: "A single TikTok can create 10× demand overnight." },
      { icon: "🧴", title: "Kit & Bundle Planning", description: "Holiday kits depend on component availability." },
    ],

    howWeHelp: [
      { icon: "💄", title: "Shade-Level Forecasting", description: "Forecast each shade independently — warm tones, cool tones, undertones." },
      { icon: "📅", title: "Shelf-Life Planning", description: "Route near-expiry stock to high-velocity stores first." },
      { icon: "📱", title: "Social Signal Ingestion", description: "Integrate social trend data into demand models." },
      { icon: "🎁", title: "Bundle-Aware Buy Plans", description: "Component BOM logic keeps kits buildable." },
    ],

    keyFeatures: [
      "Shade-Level Forecasting",
      "Expiry Date Tracking",
      "Social Trend Signals",
      "Kit BOM Planning",
      "Sephora/Nykaa Integration",
      "Influencer Drop Planning",
    ],

    ctaTitle: "Ready to plan beauty with precision?",
  },

  // ───────────────────────────────────────────── Home & Living
  "home-living": {
    slug: "home-living",
    kicker: "Home & Living Industry",
    kickerColor: "teal",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Home & Living",
    heroGradient: "from-teal-500 to-emerald-500",
    tagline: "Long lead times, bulky SKUs, and seasonal decor waves. Plan furniture, bedding, and decor with warehouse-level intelligence.",
    metaDescription: "AI demand planning for home and living retail. Furniture, bedding, and decor forecasting with long lead-time awareness.",
    metaKeywords: "home living planning, furniture inventory, bedding planning, decor forecasting",

    challenges: [
      { icon: "🚚", title: "Long Lead Times", description: "Furniture orders can take 90–120 days — a forecast miss is costly." },
      { icon: "📦", title: "Bulky Storage", description: "Warehouse capacity constrains how much you can carry." },
      { icon: "🏠", title: "Seasonal Decor", description: "Diwali, Christmas, spring refresh — timed windows for quick sell-through." },
      { icon: "💵", title: "High Capital Lock-In", description: "A single piece of dead stock ties up thousands in working capital." },
    ],

    howWeHelp: [
      { icon: "⏱️", title: "Lead-Time-Aware Forecasting", description: "Plans that respect 90+ day lead times with built-in buffers." },
      { icon: "🏭", title: "Warehouse Capacity Planning", description: "Forecasts include physical-space constraints by region." },
      { icon: "🗓️", title: "Seasonal Decor Cadence", description: "Pre-plan Diwali, Christmas, and refresh waves months in advance." },
      { icon: "💰", title: "Capital-Aware Buy Plans", description: "Keep working capital in balance with cash-flow guardrails." },
    ],

    keyFeatures: [
      "Long Lead-Time Planning",
      "Warehouse Capacity Modeling",
      "Seasonal Decor Cadence",
      "Cash Flow Guardrails",
      "Regional Allocation",
      "Supplier Lead-Time Tracking",
    ],

    ctaTitle: "Ready to optimize home & living inventory?",
  },
};

export const getIndustryBySlug = (slug) => industryContent[slug] || null;
export const getAllIndustries = () => Object.values(industryContent);
