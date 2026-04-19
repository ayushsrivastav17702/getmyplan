// CMS-Style Solutions Content Mapping
// Used by the shared SolutionPage template at /solutions/:slug

export const solutionContent = {
  // ───────────────────────────────────────────── Fashion Retail
  "fashion-retail": {
    slug: "fashion-retail",
    kicker: "Fashion Retail Solution",
    kickerColor: "indigo",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Fashion Retailers",
    heroGradient: "from-indigo-500 to-rose-500",
    tagline: "Predict demand across thousands of SKUs and stores with AI-powered forecasting. Reduce stockouts, optimize inventory, and save planning time.",
    metaDescription: "AI-powered demand planning for fashion retailers. Forecast with 92.7% accuracy. Reduce stockouts and dead stock.",
    metaKeywords: "fashion retail AI, fashion demand planning, retail forecasting, apparel planning",

    challenges: [
      { icon: "📊", title: "Manual Spreadsheets", description: "Planners spend hours consolidating data across multiple Excel files." },
      { icon: "⚠️", title: "Stockouts", description: "Bestsellers run out due to inaccurate demand forecasts." },
      { icon: "📦", title: "Excess Inventory", description: "Over-ordering leads to markdowns and dead stock." },
    ],

    howWeHelp: [
      { icon: "🤖", title: "AI Demand Forecasting", description: "Generate accurate forecasts for every SKU-store combination using our 3-model ensemble AI." },
      { icon: "🏪", title: "Store Wedge Classification", description: "Classify stores into A, B, C tiers based on revenue to optimize allocation." },
      { icon: "🏷️", title: "Style Mix Tagging", description: "Auto-classify SKUs as Core, Fashion, or Test based on sales patterns." },
      { icon: "📋", title: "Buy Plan Generator", description: "Generate optimized purchase orders with our Full Buy Formula." },
    ],

    keyFeatures: [
      "Store Wedge (A/B/C)",
      "Style Mix (Core/Fashion/Test)",
      "Attribution Matrix",
      "Full Buy Formula",
      "Multi-Level Approval",
      "Order Consolidation",
    ],

    ctaTitle: "Ready to optimize your fashion retail planning?",
  },

  // ───────────────────────────────────────────── Luxury Goods
  "luxury-goods": {
    slug: "luxury-goods",
    kicker: "Luxury Goods Solution",
    kickerColor: "amber",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Luxury Brands",
    heroGradient: "from-amber-500 to-rose-500",
    tagline: "Optimize inventory for high-value products. Protect brand value with accurate demand forecasting.",
    metaDescription: "AI-powered demand planning for luxury goods. Optimize inventory for high-value products with accurate forecasting.",
    metaKeywords: "luxury brand planning, luxury inventory, limited edition planning, premium retail",

    challenges: [
      { icon: "💎", title: "Protect Brand Value", description: "Avoid unnecessary markdowns that dilute brand perception." },
      { icon: "🎯", title: "Limited Edition Planning", description: "Accurate forecasting for capsule collections and limited drops." },
      { icon: "🌍", title: "Global Allocation", description: "Optimize inventory distribution across international locations." },
      { icon: "📊", title: "Waitlist Management", description: "Convert waitlist data into accurate demand signals." },
    ],

    howWeHelp: [
      { icon: "🧠", title: "Premium Forecasting", description: "ML models tuned for low-volume, high-value SKUs." },
      { icon: "🗺️", title: "Multi-Region Planning", description: "Country-specific demand with VAT/currency awareness." },
      { icon: "🪙", title: "Margin Protection", description: "Minimize markdowns with precise replenishment." },
      { icon: "🕒", title: "Drop Cadence Planning", description: "Time seasonal drops with lead-time aware buy plans." },
    ],

    keyFeatures: [
      "Capsule Forecasting",
      "Waitlist Signal Ingestion",
      "Region-Specific Allocation",
      "Markdown Guardrails",
      "High-Touch Approval Flow",
      "VIP Store Wedge",
    ],

    ctaTitle: "Ready to optimize your luxury inventory?",
  },

  // ───────────────────────────────────────────── Fast Fashion
  "fast-fashion": {
    slug: "fast-fashion",
    kicker: "Fast Fashion Solution",
    kickerColor: "pink",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Fast Fashion",
    heroGradient: "from-pink-500 to-purple-500",
    tagline: "Keep up with rapidly changing trends. Reduce markdowns with rapid replenishment cycles.",
    metaDescription: "AI-powered demand planning for fast fashion. Keep up with rapidly changing trends with rapid replenishment cycles.",
    metaKeywords: "fast fashion planning, weekly replenishment, trend detection, apparel trends",

    challenges: [
      { icon: "⚡", title: "Rapid Replenishment", description: "Weekly replenishment cycles to keep up with trends." },
      { icon: "📱", title: "Trend Detection", description: "AI identifies emerging trends from sales data." },
      { icon: "🔄", title: "Phased Replenishment", description: "Split orders into multiple shipments for flexibility." },
    ],

    howWeHelp: [
      { icon: "📈", title: "Velocity Tracking", description: "Day-level ROS signals surface breakouts within 48 hours." },
      { icon: "🧵", title: "Short-Cycle Planning", description: "2–6 week horizons with rolling recalibration." },
      { icon: "🏷️", title: "Markdown Timing", description: "Optimize when to mark down to maximize sell-through." },
      { icon: "🚚", title: "Fast Allocation", description: "Auto-allocate intake to A-stores within hours of receiving." },
    ],

    keyFeatures: [
      "Weekly Replenishment",
      "Trend Breakout Alerts",
      "Short-Cycle Forecasting",
      "Phased Shipment Splits",
      "Markdown Optimization",
      "Fast Allocation Engine",
    ],

    ctaTitle: "Ready to accelerate your fast fashion planning?",
  },

  // ───────────────────────────────────────────── D2C Brands
  "d2c-brands": {
    slug: "d2c-brands",
    kicker: "D2C Brands Solution",
    kickerColor: "teal",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Direct-to-Consumer Brands",
    heroGradient: "from-teal-500 to-blue-500",
    tagline: "Scale your D2C brand with confidence. Optimize inventory and improve cash flow.",
    metaDescription: "AI-powered demand planning for D2C brands. Scale from 1 to 500 stores with confidence.",
    metaKeywords: "D2C planning, direct to consumer brands, inventory management, multi-channel D2C",

    challenges: [
      { icon: "📈", title: "Scale Confidently", description: "From 1 store to 500 stores with consistent planning." },
      { icon: "💰", title: "Optimize Cash Flow", description: "Reduce inventory holding costs with accurate forecasts." },
      { icon: "🛒", title: "Multi-Channel Sync", description: "Unified planning across online and offline channels." },
      { icon: "📊", title: "Real-time Insights", description: "Dashboard with KPIs for founders and operators." },
    ],

    howWeHelp: [
      { icon: "🌱", title: "Start Small, Grow Fast", description: "Onboard in minutes and scale as your store count grows." },
      { icon: "🔗", title: "Shopify + Marketplace Sync", description: "Pull sales data from every channel in one view." },
      { icon: "💸", title: "Cash-Flow-Aware Buy Plans", description: "Right-size buys to match your working capital." },
      { icon: "📱", title: "Founder Dashboard", description: "A one-screen view of the numbers that matter." },
    ],

    keyFeatures: [
      "Multi-Channel Forecasting",
      "Shopify Integration",
      "Cash Flow Guardrails",
      "Founder KPI Dashboard",
      "Lightweight Onboarding",
      "Growth-Scaled Pricing",
    ],

    ctaTitle: "Ready to scale your D2C brand?",
  },

  // ───────────────────────────────────────────── Multi-Channel Retail
  "multi-channel-retail": {
    slug: "multi-channel-retail",
    kicker: "Multi-Channel Retail Solution",
    kickerColor: "purple",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Multi-Channel Retailers",
    heroGradient: "from-purple-500 to-indigo-500",
    tagline: "Unified demand forecasting across online and offline channels. Optimize inventory allocation by channel.",
    metaDescription: "AI-powered demand planning for multi-channel retail. Unified forecasting across online and offline channels.",
    metaKeywords: "multi-channel retail, omnichannel planning, ecommerce forecasting, unified retail",

    challenges: [
      { icon: "🛍️", title: "E-commerce", description: "Demand forecasting for your online store." },
      { icon: "🏬", title: "Physical Retail", description: "Store-level forecasting with wedge classification." },
      { icon: "📱", title: "Marketplaces", description: "Channel-specific demand planning." },
    ],

    howWeHelp: [
      { icon: "🌐", title: "Channel-Aware Forecasts", description: "Separate models per channel accounting for promo and seasonality." },
      { icon: "📦", title: "Unified Inventory View", description: "Single source of truth across DCs, stores, and 3PLs." },
      { icon: "🔁", title: "Cross-Channel Rebalancing", description: "Move stock where demand is — automatically." },
      { icon: "🧭", title: "Channel P&L", description: "See profitability by channel, category, and SKU." },
    ],

    keyFeatures: [
      "Channel-Level Forecasting",
      "Unified Inventory View",
      "Cross-Channel Transfers",
      "Marketplace Integrations",
      "Channel P&L Reports",
      "Promo Lift Modeling",
    ],

    ctaTitle: "Ready to unify your multi-channel planning?",
  },
};

export const getSolutionBySlug = (slug) => solutionContent[slug] || null;
export const getAllSolutions = () => Object.values(solutionContent);
