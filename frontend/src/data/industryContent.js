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
    tagline: "From t-shirts to formal wear. Forecast demand across men's, women's, and kids' categories. Reduce stockouts, optimize inventory, and save planning time.",
    metaDescription: "AI-powered demand planning for apparel brands. Forecast for men's, women's, and kids' clothing across thousands of SKUs. Reduce stockouts by 41%.",
    metaKeywords: "apparel demand planning, clothing forecasting, fashion retail AI, menswear planning, womenswear inventory",

    categories: [
      { icon: "👕", title: "Men's Apparel", description: "Shirts, pants, jackets, suits, activewear, loungewear." },
      { icon: "👗", title: "Women's Apparel", description: "Dresses, tops, skirts, outerwear, loungewear, activewear." },
      { icon: "🧸", title: "Kids' Apparel", description: "Baby, toddler, and children's clothing across all sizes." },
    ],

    challenges: [
      { icon: "📏", title: "Size Curve Complexity", description: "Managing inventory across multiple sizes (XS–XXL) with different demand patterns." },
      { icon: "🎨", title: "Color Variants", description: "Forecasting demand for each colorway of the same style." },
      { icon: "📅", title: "Seasonal Transitions", description: "Managing Spring/Summer to Fall/Winter inventory transitions." },
      { icon: "⚡", title: "Fast Fashion Trends", description: "Keeping up with rapidly changing consumer preferences." },
    ],

    howWeHelp: [
      { icon: "🤖", title: "SKU-Level Forecasting", description: "Forecast demand for every style, size, and color combination." },
      { icon: "🏪", title: "Store-Specific Allocation", description: "Send the right assortment to each store based on wedge classification." },
      { icon: "📊", title: "Style Mix Optimization", description: "Balance Core, Fashion, and Test SKUs for optimal inventory." },
    ],

    keyFeatures: [
      "Store Wedge (A/B/C)",
      "Style Mix (Core/Fashion/Test)",
      "Attribution Matrix",
      "Full Buy Formula",
      "Multi-Level Approval",
      "Statistical Safety Stock",
    ],

    ctaTitle: "Ready to transform your apparel planning?",
    ctaSubtitle: "Join apparel brands using GetMyPlan to reduce stockouts by 41%.",
  },

  // ───────────────────────────────────────────── Footwear
  "footwear": {
    slug: "footwear",
    kicker: "Footwear Industry",
    kickerColor: "amber",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Footwear Brands",
    heroGradient: "from-amber-500 to-orange-500",
    tagline: "From sneakers to formal shoes. Forecast demand across sizes, styles, and categories.",
    metaDescription: "AI-powered demand planning for footwear brands. Forecast for sneakers, formal shoes, boots, and sandals across sizes.",
    metaKeywords: "footwear demand planning, shoe forecasting, sneaker inventory optimization, footwear retail AI",

    categories: [
      { icon: "👟", title: "Athletic & Sneakers", description: "Running shoes, basketball, training, lifestyle sneakers." },
      { icon: "👞", title: "Formal Footwear", description: "Oxfords, loafers, dress shoes, boots, monk straps." },
      { icon: "👡", title: "Casual & Sandals", description: "Flip-flops, slides, espadrilles, mules, clogs." },
    ],

    calloutTitle: "The Size Curve Challenge",
    calloutBody: "Footwear brands face unique size curve complexity. Different sizes have different demand patterns. GetMyPlan forecasts demand for each size-SKU combination, ensuring you never run out of popular sizes.",

    challenges: [
      { icon: "📏", title: "Size Run Complexity", description: "Full-run buys leave half your inventory in sizes that barely sell." },
      { icon: "⚖️", title: "Gender Splits", description: "Men's, women's, and kids' — each with a different size distribution." },
      { icon: "🔁", title: "Broken Size Runs", description: "Missing the one size a customer wants instantly kills the sale." },
    ],

    howWeHelp: [
      { icon: "📏", title: "Size-Level Forecasting", description: "Forecast demand for each size (US 6–13) independently." },
      { icon: "🏪", title: "Store-Level Allocation", description: "Send optimal size quantities to each store based on local demand." },
      { icon: "🔄", title: "Phased Replenishment", description: "Split orders into multiple shipments for flexibility." },
    ],

    keyFeatures: [
      "Size-Run Forecasting",
      "Gender Demand Splits",
      "Width-Aware Allocation",
      "Broken-Run Alerts",
      "Inter-Store Transfers",
      "Category Health Scorecard",
    ],

    ctaTitle: "Ready to optimize your footwear planning?",
  },

  // ───────────────────────────────────────────── Accessories
  "accessories": {
    slug: "accessories",
    kicker: "Accessories Industry",
    kickerColor: "pink",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Accessories Brands",
    heroGradient: "from-rose-500 to-pink-500",
    tagline: "From bags to watches. Forecast demand across thousands of accessory SKUs.",
    metaDescription: "AI-powered demand planning for accessories brands. Forecast for bags, watches, jewelry, and more.",
    metaKeywords: "accessories demand planning, bag forecasting, jewelry inventory, watch retail planning",

    categories: [
      { icon: "👜", title: "Bags & Luggage", description: "Handbags, backpacks, totes, suitcases, duffels, crossbody bags." },
      { icon: "⌚", title: "Watches & Jewelry", description: "Wristwatches, necklaces, rings, earrings, bracelets, pendants." },
      { icon: "🧣", title: "Other Accessories", description: "Scarves, belts, hats, sunglasses, wallets, gloves, ties." },
    ],

    challenges: [
      { icon: "💼", title: "High Unit Value", description: "One wrong buy decision equals thousands in dead stock capital." },
      { icon: "⭐", title: "Trend Volatility", description: "Hero SKUs can sell out in days or sit for months." },
      { icon: "🪞", title: "Display Dependency", description: "Without display presence, accessories sell-through collapses." },
    ],

    howWeHelp: [
      { icon: "📊", title: "High SKU Count Management", description: "Accessories brands have thousands of SKUs. GetMyPlan scales to 130,000+." },
      { icon: "🎨", title: "Color & Style Variants", description: "Forecast demand for each color and style combination independently." },
      { icon: "📦", title: "Seasonal Planning", description: "Plan for gift-giving seasons, holidays, and fashion cycles." },
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
    kicker: "Beauty & Cosmetics",
    kickerColor: "purple",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Beauty Brands",
    heroGradient: "from-purple-500 to-fuchsia-500",
    tagline: "From skincare to makeup. Forecast demand across thousands of SKU variants.",
    metaDescription: "AI-powered demand planning for beauty and cosmetics brands. Forecast for skincare, makeup, haircare, and fragrance.",
    metaKeywords: "beauty demand planning, cosmetics forecasting, skincare inventory, makeup retail planning",

    categories: [
      { icon: "💄", title: "Makeup", description: "Foundation, lipstick, eyeshadow, mascara, concealer, blush, bronzer." },
      { icon: "🧴", title: "Skincare", description: "Moisturizers, serums, cleansers, sunscreen, toners, masks, exfoliators." },
      { icon: "💇", title: "Haircare & Fragrance", description: "Shampoo, conditioner, perfume, cologne, hair styling products, body lotion." },
    ],

    calloutTitle: "Unique Beauty Industry Challenges",
    calloutBullets: [
      "Shade/color variants (foundation has 30+ shades)",
      "Short product lifecycles (new launches every season)",
      "GWP (Gift With Purchase) complexity",
      "Clean beauty and ingredient trends",
    ],

    challenges: [
      { icon: "🎨", title: "Shade Proliferation", description: "One lipstick × 30 shades × 5 finishes = 150 SKUs per product." },
      { icon: "⏳", title: "Expiry & Shelf Life", description: "Dead stock becomes write-off the moment it expires." },
      { icon: "🔥", title: "Viral Spikes", description: "A single TikTok can create 10× demand overnight." },
    ],

    howWeHelp: [
      { icon: "🎨", title: "Shade-Level Forecasting", description: "Forecast demand for each shade and SKU combination." },
      { icon: "🆕", title: "New Launch Forecasting", description: "Predict demand for new products using analog SKU analysis." },
      { icon: "📈", title: "Trend Detection", description: "Identify emerging ingredient and category trends." },
    ],

    keyFeatures: [
      "Shade-Level Forecasting",
      "Expiry Date Tracking",
      "Social Trend Signals",
      "Kit BOM Planning",
      "Sephora/Nykaa Integration",
      "Influencer Drop Planning",
    ],

    ctaTitle: "Ready to optimize your beauty planning?",
  },

  // ───────────────────────────────────────────── Home & Living
  "home-living": {
    slug: "home-living",
    kicker: "Home & Living",
    kickerColor: "teal",
    heroTitle: "AI Demand Planning for",
    heroHighlight: "Home & Living Brands",
    heroGradient: "from-teal-500 to-emerald-500",
    tagline: "From furniture to decor. Forecast demand across home goods categories.",
    metaDescription: "AI-powered demand planning for home and living brands. Forecast for furniture, decor, bedding, and kitchenware.",
    metaKeywords: "home goods demand planning, furniture forecasting, home decor inventory, kitchenware planning",

    categories: [
      { icon: "🛋️", title: "Furniture", description: "Sofas, beds, tables, chairs, storage, desks, shelves, cabinets." },
      { icon: "🖼️", title: "Home Decor", description: "Wall art, mirrors, vases, candles, rugs, clocks, figurines, planters." },
      { icon: "🍳", title: "Kitchen & Bedding", description: "Cookware, dinnerware, sheets, towels, pillows, utensils, bakeware." },
    ],

    challenges: [
      { icon: "🚚", title: "Long Lead Times", description: "Furniture orders can take 90–120 days — a forecast miss is costly." },
      { icon: "📦", title: "Bulky Storage", description: "Warehouse capacity constrains how much you can carry." },
      { icon: "🏠", title: "Seasonal Decor", description: "Diwali, Christmas, spring refresh — timed windows for quick sell-through." },
    ],

    howWeHelp: [
      { icon: "📦", title: "Bulky Item Logistics", description: "Optimize inventory for large, bulky items with high storage costs." },
      { icon: "📅", title: "Seasonal Planning", description: "Plan for seasonal peaks (holidays, spring refresh, back-to-school)." },
      { icon: "🏪", title: "Store-Specific Assortment", description: "Different store formats need different product ranges." },
    ],

    keyFeatures: [
      "Store Wedge (A/B/C)",
      "Display Minimums",
      "Statistical Safety Stock",
      "Phased Replenishment",
      "Order Consolidation",
    ],

    ctaTitle: "Ready to optimize your home goods planning?",
  },
};

export const getIndustryBySlug = (slug) => industryContent[slug] || null;
export const getAllIndustries = () => Object.values(industryContent);
