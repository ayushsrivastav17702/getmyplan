// CMS-Style Product Content Mapping
// Edit this file to update any product page content without touching components.
// Each product has full metadata (title, meta, features, howItWorks, formula, benefits, useCases, relatedProducts, faq, ctaTitle).

export const productContent = {
  // ───────────────────────────────────────────────────────────── Demand Planning
  "demand-planning": {
    slug: "demand-planning",
    title: "AI Demand Forecasting",
    fullTitle: "AI-Powered Demand Planning",
    tagline: "Predict what you'll sell, where, and when — with 92.7% forecast accuracy.",
    metaDescription: "Enterprise AI demand forecasting for fashion retail. 92.7% accuracy. 12-month horizon with confidence intervals. Reduce stockouts by 41%.",
    metaKeywords: "demand forecasting, AI demand planning, retail forecasting, fashion demand prediction",
    heroBadge: "92.7% Forecast Accuracy",
    heroGradient: "from-indigo-500 to-rose-500",
    icon: "🎯",

    features: [
      { icon: "🤖", title: "3-Model Ensemble", description: "Holt-Winters + Random Forest + Seasonal Decomposition for maximum accuracy.", badge: "Core" },
      { icon: "📈", title: "12-Month Horizon", description: "Long-term forecasts with confidence intervals for better planning.", badge: "Core" },
      { icon: "🎯", title: "Promotional Lift Factors", description: "Automatically adjust forecasts for sales, holidays, and events.", badge: "Enterprise" },
      { icon: "🔄", title: "Multi-Channel Forecasting", description: "Amazon, Shopify, Zalando, and more — separate forecasts per channel.", badge: "Enterprise" },
      { icon: "🆕", title: "New Product Launch", description: "Analog SKU forecasting for products with no history.", badge: "Enterprise" },
      { icon: "📅", title: "Seasonal Pattern Detection", description: "Automatic detection of Diwali, Christmas, Monsoon patterns.", badge: "Core" },
    ],

    howItWorks: [
      { step: "1", title: "Upload Historical Data", description: "90+ days of sales data, SKU master, store master." },
      { step: "2", title: "AI Training", description: "Our 3-model ensemble learns your demand patterns." },
      { step: "3", title: "Forecast Generation", description: "Get 12-month forecasts with confidence intervals." },
      { step: "4", title: "Review & Adjust", description: "Review forecasts, apply promotional lifts, and export." },
    ],

    technicalFormula: "Forecast = Ensemble(Holt-Winters + Random Forest + Seasonal Decomposition) + Promotional Lift Factor + New Product Analog Adjustment",

    benefits: [
      { icon: "📉", title: "41% Stockout Reduction", description: "Never run out of bestsellers." },
      { icon: "💰", title: "32% Dead Stock Reduction", description: "Buy exactly what you need." },
      { icon: "⏱️", title: "11.5 Hours Saved Weekly", description: "Automate manual planning." },
    ],

    useCases: [
      { title: "Multi-Store Chains", description: "Optimize inventory across 500+ stores with A/B/C wedge classification." },
      { title: "E-commerce + Retail", description: "Unified demand planning across online and physical channels." },
      { title: "New Product Launches", description: "Forecast demand for new collections using analog SKU analysis." },
    ],

    relatedProducts: ["buy-planning", "inventory-planning", "allocation-replenishment"],

    faq: [
      { question: "How accurate is the AI forecasting?", answer: "92.7% forecast accuracy backtested on 50+ real-world fashion retail datasets." },
      { question: "How much historical data do I need?", answer: "90+ days of sales data for optimal results. Less data still works with reduced accuracy." },
      { question: "Can I forecast for new products with no history?", answer: "Yes, using analog SKU forecasting based on similar products." },
    ],

    ctaTitle: "Ready to predict demand with 92.7% accuracy?",
    ctaButton: "Start Free Trial",
  },

  // ───────────────────────────────────────────────────────────── Buy Planning
  "buy-planning": {
    slug: "buy-planning",
    title: "Buy Plan Generator",
    fullTitle: "AI-Powered Buy Plan Generator",
    tagline: "Generate optimal purchase quantities using our Full Buy Formula.",
    metaDescription: "AI-powered buy plan generator for fashion retail. Full Buy Formula with store wedge classification and style mix tagging. Reduce overstock by 32%.",
    metaKeywords: "buy plan generator, purchase order optimization, retail buying, inventory purchasing",
    heroBadge: "Full Buy Formula",
    heroGradient: "from-emerald-500 to-teal-500",
    icon: "🛒",

    features: [
      { icon: "🏪", title: "Store Wedge Classification", description: "A/B/C store classification based on 90-day revenue.", badge: "Enterprise" },
      { icon: "🏷️", title: "Style Mix Tagging", description: "Auto-classify SKUs as Core/Fashion/Test.", badge: "Enterprise" },
      { icon: "🔗", title: "Attribution Matrix", description: "SKU to store wedge allocation percentages.", badge: "Enterprise" },
      { icon: "✓", title: "Multi-Level Approval", description: "6-stage approval workflow with full audit trail.", badge: "Enterprise" },
      { icon: "📦", title: "Order Consolidation", description: "Combine store POs into supplier POs automatically.", badge: "Enterprise" },
      { icon: "🔄", title: "Phased Replenishment", description: "Split orders into multiple shipments across weeks.", badge: "Enterprise" },
    ],

    howItWorks: [
      { step: "1", title: "Select Store Wedges", description: "Choose A, B, and/or C stores for your buy plan." },
      { step: "2", title: "Set Parameters", description: "Define horizon, categories, and filters." },
      { step: "3", title: "Generate Plan", description: "AI generates optimized buy quantities." },
      { step: "4", title: "Review & Submit", description: "Edit, bulk update, and submit for approval." },
    ],

    technicalFormula: "Buy Qty = MAX((Target Multiplier × Forecast) − Current Stock, Display Minimum Units, Safety Stock Units) × Attribution %",

    benefits: [
      { icon: "📉", title: "32% Overstock Reduction", description: "Buy exactly what you need." },
      { icon: "⏱️", title: "11.5 Hours Saved Weekly", description: "Automate manual planning." },
      { icon: "✅", title: "98% Approval Rate", description: "First-time approval with accurate plans." },
    ],

    useCases: [
      { title: "Seasonal Buying", description: "Plan purchases for Diwali, Christmas, and monsoon seasons." },
      { title: "New Collection Launch", description: "Optimize buy quantities for new product launches." },
      { title: "Replenishment Buying", description: "Automated replenishment for core products." },
    ],

    relatedProducts: ["demand-planning", "inventory-planning", "allocation-replenishment"],

    faq: [
      { question: "What is the Full Buy Formula?", answer: "Buy Qty = MAX((Target Multiplier × Forecast) − Current Stock, Display Minimum, Safety Stock) × Attribution %." },
      { question: "How are target multipliers determined?", answer: "Core = 1.2×, Fashion = 0.8×, Test = 0.4× (configurable per tenant)." },
      { question: "Can I edit the plan after generation?", answer: "Yes, the buy plan table is fully editable with a full audit trail." },
    ],

    ctaTitle: "Ready to generate your first buy plan?",
    ctaButton: "Start Free Trial",
  },

  // ───────────────────────────────────────────────────────────── Allocation & Replenishment
  "allocation-replenishment": {
    slug: "allocation-replenishment",
    title: "Allocation & Replenishment",
    fullTitle: "Multi-Echelon Allocation & Replenishment Planning",
    tagline: "Optimize inventory distribution from warehouse to 3,000+ stores.",
    metaDescription: "AI-powered allocation and replenishment planning. Multi-echelon inventory optimization with statistical safety stock. Reduce stockouts by 41%.",
    metaKeywords: "allocation planning, replenishment planning, inventory distribution, warehouse to store",
    heroBadge: "Multi-Echelon Optimization",
    heroGradient: "from-blue-500 to-cyan-500",
    icon: "📦",

    features: [
      { icon: "🏭", title: "Warehouse to Store", description: "Multi-echelon inventory optimization.", badge: "Enterprise" },
      { icon: "📊", title: "Dynamic Reorder Points", description: "ROS × Lead Time + Safety Stock calculation.", badge: "Core" },
      { icon: "🔄", title: "Inter-Store Transfer", description: "Optimize transfers between stores.", badge: "Enterprise" },
      { icon: "📈", title: "DOH Analysis", description: "Days on hand tracking and alerts.", badge: "Core" },
      { icon: "⚠️", title: "Stockout Prediction", description: "Proactive alerts with severity levels.", badge: "Core" },
      { icon: "🛡️", title: "Statistical Safety Stock", description: "z × MAD × √(LT/RP) formula.", badge: "Enterprise" },
    ],

    howItWorks: [
      { step: "1", title: "Calculate Reorder Point", description: "ROS × Lead Time + Safety Stock." },
      { step: "2", title: "Generate Replenishment Plan", description: "Identify stores below reorder point." },
      { step: "3", title: "Allocate from Warehouse", description: "Optimize allocation based on priority." },
      { step: "4", title: "Transfer Optimization", description: "Suggest inter-store transfers when needed." },
    ],

    technicalFormula: "Reorder Point = (ROS × Lead Time) + (z × MAD × √(LT / RP))",

    benefits: [
      { icon: "📉", title: "41% Stockout Reduction", description: "Never run out of stock." },
      { icon: "💰", title: "25% Lower Inventory Cost", description: "Optimize safety stock levels." },
      { icon: "⏱️", title: "Automated Replenishment", description: "No manual reorder calculations." },
    ],

    useCases: [
      { title: "Multi-Store Chains", description: "Optimize allocation across 500+ stores." },
      { title: "Warehouse Management", description: "Efficient warehouse-to-store distribution." },
      { title: "Seasonal Peaks", description: "Handle demand spikes during festivals." },
    ],

    relatedProducts: ["demand-planning", "buy-planning", "inventory-planning"],

    faq: [
      { question: "How is reorder point calculated?", answer: "Reorder Point = (Rate of Sale × Lead Time) + Safety Stock." },
      { question: "What is statistical safety stock?", answer: "Safety Stock = z × MAD × √(Lead Time / Review Period)." },
      { question: "Can I transfer stock between stores?", answer: "Yes — the system suggests optimal inter-store transfers." },
    ],

    ctaTitle: "Ready to optimize your replenishment?",
    ctaButton: "Start Free Trial",
  },

  // ───────────────────────────────────────────────────────────── Assortment Planning
  "assortment-planning": {
    slug: "assortment-planning",
    title: "Assortment Planning",
    fullTitle: "AI-Powered Assortment Planning",
    tagline: "Optimize product range across 3,000+ stores with style mix tagging.",
    metaDescription: "AI-powered assortment planning for fashion retail. Store wedge classification, style mix tagging, and 70/20/10 assortment optimization.",
    metaKeywords: "assortment planning, range planning, product assortment optimization, retail assortment",
    heroBadge: "70/20/10 Assortment Rule",
    heroGradient: "from-purple-500 to-pink-500",
    icon: "🗂️",

    features: [
      { icon: "🏪", title: "Store Wedge Classification", description: "A/B/C store segmentation for targeted assortment.", badge: "Enterprise" },
      { icon: "🏷️", title: "Style Mix Tagging", description: "Core / Fashion / Test SKU classification.", badge: "Enterprise" },
      { icon: "🔗", title: "Attribution Matrix", description: "Which SKUs go to which store wedges.", badge: "Enterprise" },
      { icon: "📊", title: "70/20/10 Rule", description: "70% Core, 20% Fashion, 10% Test assortment.", badge: "Core" },
      { icon: "📐", title: "Planogram Fill Rate", description: "Optimize shelf space allocation.", badge: "Enterprise" },
      { icon: "🏗️", title: "New Store Templates", description: "Pre-built assortment for new store openings.", badge: "Enterprise" },
    ],

    howItWorks: [
      { step: "1", title: "Classify Stores", description: "A/B/C wedge based on 90-day revenue." },
      { step: "2", title: "Tag SKUs", description: "Core / Fashion / Test based on sales patterns." },
      { step: "3", title: "Build Attribution", description: "Map SKUs to store wedges." },
      { step: "4", title: "Generate Assortment", description: "Create store-specific assortments." },
    ],

    technicalFormula: "A-Store Assortment = 100% of SKUs  |  B-Store = 70%  |  C-Store = 30%",

    benefits: [
      { icon: "📈", title: "25% Higher Sell-Through", description: "Right products in right stores." },
      { icon: "💰", title: "20% Lower Inventory", description: "No dead stock in C-stores." },
      { icon: "⭐", title: "95% Customer Satisfaction", description: "Always find what they want." },
    ],

    useCases: [
      { title: "New Store Opening", description: "Pre-built assortment templates for quick setup." },
      { title: "Seasonal Refresh", description: "Update assortments for new seasons." },
      { title: "Data-Driven Decisions", description: "Use sales data to optimize assortment." },
    ],

    relatedProducts: ["demand-planning", "buy-planning", "allocation-replenishment"],

    faq: [
      { question: "What is the 70/20/10 rule?", answer: "70% Core SKUs (stable products), 20% Fashion SKUs (seasonal), 10% Test SKUs (new launches)." },
      { question: "How are store wedges determined?", answer: "Based on 90-day revenue: A (top 20%), B (next 30%), C (bottom 50%)." },
      { question: "Can I customize assortment per store?", answer: "Yes, with manual override and audit trail." },
    ],

    ctaTitle: "Ready to optimize your assortment?",
    ctaButton: "Start Free Trial",
  },

  // ───────────────────────────────────────────────────────────── IBP
  "integrated-business-planning": {
    slug: "integrated-business-planning",
    title: "Integrated Business Planning",
    fullTitle: "Integrated Business Planning (IBP)",
    tagline: "Connect sales, inventory, and financial planning in one platform.",
    metaDescription: "Integrated Business Planning (IBP) for fashion retail. Connect sales forecasting, inventory planning, and financial planning in one platform.",
    metaKeywords: "integrated business planning, IBP, S&OP, sales and operations planning",
    heroBadge: "Sales → Inventory → Finance",
    heroGradient: "from-orange-500 to-red-500",
    icon: "🔄",

    features: [
      { icon: "📊", title: "Sales Planning", description: "Demand forecasting with promotional lift.", badge: "Core" },
      { icon: "📦", title: "Inventory Planning", description: "DOH analysis and safety stock.", badge: "Core" },
      { icon: "💰", title: "Financial Planning", description: "OTB, WSSI, margin analysis.", badge: "Enterprise" },
      { icon: "🏭", title: "Supply Chain Planning", description: "Supplier collaboration and lead time management.", badge: "Enterprise" },
      { icon: "📈", title: "Executive Dashboard", description: "Single source of truth for leadership.", badge: "Core" },
    ],

    howItWorks: [
      { step: "1", title: "Sales Forecast", description: "AI predicts demand by SKU-store." },
      { step: "2", title: "Inventory Plan", description: "Calculate required stock levels." },
      { step: "3", title: "Buy Plan", description: "Generate purchase orders." },
      { step: "4", title: "Financial Close", description: "Track actual vs plan." },
    ],

    technicalFormula: "Connected Planning Cycle: Sales Forecast → Inventory Plan → Buy Plan → Allocation → Replenishment → Financial Close",

    benefits: [
      { icon: "🎯", title: "Aligned Planning", description: "One source of truth across teams." },
      { icon: "⏱️", title: "50% Faster Planning", description: "No more siloed spreadsheets." },
      { icon: "📈", title: "15% Higher Forecast Accuracy", description: "Connected data improves accuracy." },
    ],

    useCases: [
      { title: "Enterprise Retailers", description: "Connect planning across departments." },
      { title: "Monthly S&OP", description: "Streamline monthly planning cycles." },
      { title: "Financial Close", description: "Track actual vs plan variance." },
    ],

    relatedProducts: ["demand-planning", "buy-planning", "merchandise-financial-planning"],

    faq: [
      { question: "What is Integrated Business Planning?", answer: "IBP connects sales, inventory, and financial planning in one platform." },
      { question: "How is this different from S&OP?", answer: "IBP includes financial planning, not just sales and operations." },
      { question: "Can I see actual vs plan variance?", answer: "Yes, the executive dashboard shows variance analysis." },
    ],

    ctaTitle: "Ready to connect your planning?",
    ctaButton: "Start Free Trial",
  },

  // ───────────────────────────────────────────────────────────── Inventory Planning
  "inventory-planning": {
    slug: "inventory-planning",
    title: "Inventory Planning",
    fullTitle: "AI-Powered Inventory Planning",
    tagline: "Optimize stock levels across 130,000+ SKUs with real-time analytics.",
    metaDescription: "AI-powered inventory planning for fashion retail. DOH analysis, stockout prediction, and statistical safety stock. Reduce inventory costs by 25%.",
    metaKeywords: "inventory planning, inventory optimization, DOH analysis, stockout prediction",
    heroBadge: "Real-Time Inventory Analytics",
    heroGradient: "from-green-500 to-emerald-500",
    icon: "📊",

    features: [
      { icon: "📈", title: "DOH Analysis", description: "Days on hand tracking and classification.", badge: "Core" },
      { icon: "⚠️", title: "Stockout Prediction", description: "Proactive alerts with lost sales calculation.", badge: "Core" },
      { icon: "🛡️", title: "Statistical Safety Stock", description: "z × MAD × √(LT/RP) formula.", badge: "Enterprise" },
      { icon: "🔄", title: "Inter-Store Transfer", description: "Optimize transfers between stores.", badge: "Enterprise" },
      { icon: "🏷️", title: "Dead Stock Identification", description: "Markdown recommendations for slow movers.", badge: "Enterprise" },
      { icon: "📊", title: "Real-Time Dashboard", description: "Inventory health at a glance.", badge: "Core" },
    ],

    howItWorks: [
      { step: "1", title: "Track Inventory", description: "Real-time SOH across all stores." },
      { step: "2", title: "Analyze DOH", description: "Identify overstocked/understocked items." },
      { step: "3", title: "Predict Stockouts", description: "Get alerts before stockouts occur." },
      { step: "4", title: "Optimize Safety Stock", description: "Statistical safety stock calculation." },
    ],

    technicalFormula: "DOH Classification: Optimal (14–21 days)  |  Overstocked (>21)  |  Understocked (<14)  |  Stocked Out (0)",

    benefits: [
      { icon: "📉", title: "25% Lower Inventory Cost", description: "Optimize stock levels." },
      { icon: "📈", title: "41% Stockout Reduction", description: "Never run out of bestsellers." },
      { icon: "💰", title: "32% Dead Stock Reduction", description: "Better inventory health." },
    ],

    useCases: [
      { title: "Multi-Store Chains", description: "Unified inventory view across all stores." },
      { title: "Seasonal Inventory", description: "Manage inventory for peak seasons." },
      { title: "Health Monitoring", description: "Daily inventory health dashboard." },
    ],

    relatedProducts: ["demand-planning", "buy-planning", "allocation-replenishment"],

    faq: [
      { question: "What is DOH and why does it matter?", answer: "Days on Hand measures how many days of inventory you have. Optimal is 14–21 days." },
      { question: "How is safety stock calculated?", answer: "Safety Stock = z × MAD × √(Lead Time / Review Period)." },
      { question: "Can I see real-time inventory?", answer: "Yes, with daily inventory sync from your WMS." },
    ],

    ctaTitle: "Ready to optimize your inventory?",
    ctaButton: "Start Free Trial",
  },

  // ───────────────────────────────────────────────────────────── MFP
  "merchandise-financial-planning": {
    slug: "merchandise-financial-planning",
    title: "Merchandise Financial Planning",
    fullTitle: "Merchandise Financial Planning (MFP)",
    tagline: "Plan budgets, margins, and profitability across your merchandise portfolio.",
    metaDescription: "Merchandise Financial Planning (MFP) for fashion retail. OTB planning, WSSI tracking, and margin optimization. Improve GM by 5–8%.",
    metaKeywords: "merchandise financial planning, MFP, OTB planning, WSSI, retail financial planning",
    heroBadge: "Plan Budgets & Margins",
    heroGradient: "from-yellow-500 to-orange-500",
    icon: "💰",

    features: [
      { icon: "📊", title: "Open-to-Buy (OTB)", description: "Budget for future inventory purchases.", badge: "Enterprise" },
      { icon: "📈", title: "Weekly Sales Stock Index", description: "Measure inventory productivity.", badge: "Enterprise" },
      { icon: "📉", title: "Gross Margin Optimization", description: "Improve profitability by 5–8%.", badge: "Enterprise" },
      { icon: "🏷️", title: "Markdown Optimization", description: "Timing and depth recommendations.", badge: "Enterprise" },
      { icon: "📊", title: "ROI Analysis", description: "By category, store, and SKU.", badge: "Enterprise" },
      { icon: "📈", title: "Financial Dashboard", description: "KPI tracking for leadership.", badge: "Core" },
    ],

    howItWorks: [
      { step: "1", title: "Set Financial Targets", description: "Sales, margin, and inventory goals." },
      { step: "2", title: "Plan OTB", description: "Calculate open-to-buy budget." },
      { step: "3", title: "Track WSSI", description: "Monitor inventory productivity." },
      { step: "4", title: "Optimize Margins", description: "Markdown timing and depth." },
    ],

    technicalFormula: "OTB = Sales Forecast + End-of-Month Stock Target − Current Stock − On-Order  |  WSSI = Weekly Sales / Average Stock",

    benefits: [
      { icon: "📈", title: "5–8% GM Improvement", description: "Better margin management." },
      { icon: "💰", title: "15% Lower Inventory Investment", description: "Optimized OTB planning." },
      { icon: "📊", title: "Real-Time Financial Visibility", description: "Daily KPI tracking." },
    ],

    useCases: [
      { title: "Enterprise Retailers", description: "Multi-brand financial consolidation." },
      { title: "Monthly Planning", description: "Monthly OTB and WSSI reviews." },
      { title: "Margin Improvement", description: "Identify margin improvement opportunities." },
    ],

    relatedProducts: ["integrated-business-planning", "buy-planning", "demand-planning"],

    faq: [
      { question: "What is Open-to-Buy (OTB)?", answer: "OTB is the budget allocated for future inventory purchases." },
      { question: "What is WSSI?", answer: "Weekly Sales Stock Index measures inventory productivity. Target is 2.0–3.0." },
      { question: "How much can I improve margins?", answer: "Customers typically see 5–8% gross margin improvement." },
    ],

    ctaTitle: "Ready to improve your margins?",
    ctaButton: "Start Free Trial",
  },

  // ───────────────────────────────────────────────────────────── OTB/WSSI
  "otb-wssi": {
    slug: "otb-wssi",
    title: "OTB & WSSI Planning",
    fullTitle: "Open-to-Buy & Weekly Sales Stock Index",
    tagline: "Control inventory budgets and measure productivity in real time.",
    metaDescription: "OTB and WSSI planning for fashion retail. Control inventory budgets and measure productivity with real-time dashboards.",
    metaKeywords: "OTB planning, WSSI, open to buy, weekly sales stock index, retail financial metrics",
    heroBadge: "OTB + WSSI Analytics",
    heroGradient: "from-cyan-500 to-blue-500",
    icon: "📊",

    features: [
      { icon: "💰", title: "OTB Calculator", description: "Interactive OTB budget calculator.", badge: "Core" },
      { icon: "📈", title: "WSSI Tracker", description: "Real-time inventory productivity.", badge: "Core" },
      { icon: "📉", title: "Variance Analysis", description: "Plan vs actual tracking.", badge: "Enterprise" },
      { icon: "📊", title: "What-If Scenarios", description: "Test different OTB scenarios.", badge: "Enterprise" },
      { icon: "📋", title: "Automated Reports", description: "Weekly OTB/WSSI reports.", badge: "Enterprise" },
    ],

    howItWorks: [
      { step: "1", title: "Input Sales Forecast", description: "AI-generated or manual forecast." },
      { step: "2", title: "Calculate OTB", description: "Determine purchase budget." },
      { step: "3", title: "Track WSSI", description: "Monitor inventory productivity." },
      { step: "4", title: "Adjust Plans", description: "React to actual performance." },
    ],

    technicalFormula: "OTB = Sales Forecast + EOM Stock Target − Current Stock − On-Order  |  WSSI = Weekly Sales / Avg Stock  |  Target WSSI 2.0–3.0",

    benefits: [
      { icon: "💰", title: "Optimized Inventory Investment", description: "Right budget, right time." },
      { icon: "📈", title: "Better Inventory Productivity", description: "Higher WSSI = better turns." },
      { icon: "📊", title: "Real-Time Visibility", description: "Daily OTB/WSSI tracking." },
    ],

    useCases: [
      { title: "Monthly Budgeting", description: "Plan monthly OTB budgets." },
      { title: "Weekly Reviews", description: "Track WSSI every week." },
      { title: "Cash Flow Management", description: "Optimize inventory investment." },
    ],

    relatedProducts: ["merchandise-financial-planning", "buy-planning", "demand-planning"],

    faq: [
      { question: "How do I calculate OTB?", answer: "OTB = Sales Forecast + EOM Stock Target − Current Stock − On-Order." },
      { question: "What is a good WSSI score?", answer: "Target WSSI is 2.0–3.0. Below 1.5 indicates overstock, above 4.0 indicates understock." },
      { question: "How often should I review OTB?", answer: "Weekly for fashion retail, monthly for basics." },
    ],

    ctaTitle: "Ready to control your inventory budget?",
    ctaButton: "Start Free Trial",
  },

  // ───────────────────────────────────────────────────────────── Range & Assortment
  "range-assortment": {
    slug: "range-assortment",
    title: "Range & Assortment Planning",
    fullTitle: "Range & Assortment Planning",
    tagline: "Optimize product range width and depth across 3,000+ stores.",
    metaDescription: "Range and assortment planning for fashion retail. Optimize product range width and depth with store segmentation.",
    metaKeywords: "range planning, assortment planning, product range optimization, retail assortment",
    heroBadge: "Optimize Range Width & Depth",
    heroGradient: "from-rose-500 to-pink-500",
    icon: "📐",

    features: [
      { icon: "📊", title: "Range Planning", description: "Which products to carry.", badge: "Core" },
      { icon: "🎨", title: "Assortment Planning", description: "Which sizes/colors/variants.", badge: "Core" },
      { icon: "🏪", title: "Store Segmentation", description: "A/B/C wedge allocation.", badge: "Enterprise" },
      { icon: "📐", title: "Planogram Optimization", description: "Shelf space allocation.", badge: "Enterprise" },
      { icon: "🏗️", title: "New Store Templates", description: "Pre-built range for new stores.", badge: "Enterprise" },
      { icon: "📅", title: "Seasonal Planning", description: "Range refresh for seasons.", badge: "Core" },
    ],

    howItWorks: [
      { step: "1", title: "Define Range", description: "Select products for the season." },
      { step: "2", title: "Segment Stores", description: "A/B/C wedge classification." },
      { step: "3", title: "Build Assortment Matrix", description: "Map SKUs to store segments." },
      { step: "4", title: "Optimize Planogram", description: "Allocate shelf space." },
    ],

    technicalFormula: "Assortment Matrix: A-Stores = 100% of SKUs  |  B-Stores = 70%  |  C-Stores = 30%",

    benefits: [
      { icon: "📈", title: "25% Higher Sell-Through", description: "Right products in right stores." },
      { icon: "💰", title: "20% Lower Inventory", description: "No dead stock in C-stores." },
      { icon: "⭐", title: "95% Customer Satisfaction", description: "Always find what they want." },
    ],

    useCases: [
      { title: "New Store Opening", description: "Pre-built range templates for quick setup." },
      { title: "Seasonal Refresh", description: "Update ranges for new seasons." },
      { title: "Data-Driven Decisions", description: "Use sales data to optimize range." },
    ],

    relatedProducts: ["assortment-planning", "buy-planning", "demand-planning"],

    faq: [
      { question: "What's the difference between range and assortment?", answer: "Range is which products to carry. Assortment is which sizes/colors/variants." },
      { question: "How do I decide which products go to which stores?", answer: "Using A/B/C store wedge classification and attribution matrix." },
      { question: "Can I customize range per store?", answer: "Yes, with manual override and audit trail." },
    ],

    ctaTitle: "Ready to optimize your range?",
    ctaButton: "Start Free Trial",
  },
};

// Helper: get one product by slug
export const getProductBySlug = (slug) => productContent[slug] || null;

// Helper: get all products (for listing page)
export const getAllProducts = () => Object.values(productContent);
