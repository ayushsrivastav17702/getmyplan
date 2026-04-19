import { useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import Navbar from "../components/landing/Navbar";
import Footer from "../components/landing/Footer";
import CTASection from "../components/landing/CTASection";

const PRODUCTS = {
  "demand-planning": {
    title: "AI-Powered Demand Planning",
    badge: "92.7% Forecast Accuracy",
    subtitle: "Predict what you'll sell, where, and when — with enterprise-grade accuracy.",
    features: [
      { title: "3-Model Ensemble", desc: "Holt-Winters + Random Forest + Seasonal Decomposition for maximum accuracy." },
      { title: "12-Month Horizon", desc: "Long-term forecasts with confidence intervals for better planning." },
      { title: "Promotional Lift Factors", desc: "Automatically adjust forecasts for sales, holidays, and events." },
      { title: "Multi-Channel Forecasting", desc: "Separate forecasts per channel — Amazon, Shopify, Zalando, and more." },
      { title: "New Product Launch", desc: "Analog SKU forecasting for products with no sales history." },
      { title: "Seasonal Pattern Detection", desc: "Automatic detection of Diwali, Christmas, Monsoon patterns." },
    ],
    formula: "Forecast = Ensemble(Holt-Winters + Random Forest + Seasonal Decomposition) + Promotional Lift + New Product Analog",
  },
  "buy-planning": {
    title: "Buy Plan Generator",
    badge: "One-Click Purchase Orders",
    subtitle: "ML generates optimal buy quantities per SKU-store combination with full formula transparency.",
    features: [
      { title: "Full Buy Formula", desc: "ROS x Horizon x Multiplier + Display Min + Safety Stock, adjusted by attribution." },
      { title: "Multi-Level Approval", desc: "6-stage workflow: Draft → Category → Senior → Head → Finance → Ordered." },
      { title: "Order Consolidation", desc: "Automatically combine store-level POs into supplier-level purchase orders." },
      { title: "Phased Replenishment", desc: "Split large orders into multiple shipments across weeks." },
      { title: "Exclusion Management", desc: "Prevent specific SKU-store combinations from appearing in plans." },
      { title: "Inline Editing", desc: "Edit quantities directly in the plan table with full audit trail." },
    ],
    formula: "Buy Qty = max(Demand Based Qty, Display Min) + Safety Stock × Attribution %",
  },
  "allocation-replenishment": {
    title: "Allocation & Replenishment",
    badge: "Optimized Store Distribution",
    subtitle: "Automatically allocate inventory across stores based on demand patterns, wedge classification, and capacity.",
    features: [
      { title: "Store Wedge-Based Allocation", desc: "Distribute inventory proportionally to A/B/C store tiers." },
      { title: "Demand-Driven Replenishment", desc: "Trigger replenishment based on rate of sale and safety stock levels." },
      { title: "Capacity Constraints", desc: "Respect store shelf capacity and warehouse availability." },
      { title: "Transfer Optimization", desc: "Recommend inter-store transfers to balance overstock and stockouts." },
      { title: "Lead Time Awareness", desc: "Factor supplier lead times into replenishment scheduling." },
      { title: "Automated PO Generation", desc: "Generate purchase orders automatically when thresholds are breached." },
    ],
    formula: "Allocation = Store Demand Share × Available Qty × Priority Weight",
  },
  "assortment-planning": {
    title: "Assortment Planning",
    badge: "Right Product, Right Store",
    subtitle: "Determine the optimal product mix for each store cluster based on local demand patterns.",
    features: [
      { title: "Store Clustering", desc: "Group stores by demographics, climate, and purchasing patterns." },
      { title: "Style Mix Optimization", desc: "Balance Core/Fashion/Test SKUs per cluster for optimal sell-through." },
      { title: "Depth & Width Planning", desc: "Set the right number of options and depth per category." },
      { title: "Localization", desc: "Adapt assortments to regional preferences and cultural events." },
      { title: "Performance Scoring", desc: "Score each SKU-store combination based on historical performance." },
      { title: "Exit Strategy", desc: "Identify underperforming SKUs for markdown or exit." },
    ],
    formula: "Assortment Score = (Sell-Through Rate × Revenue Contribution) / Weeks of Supply",
  },
  "integrated-business-planning": {
    title: "Integrated Business Planning",
    badge: "Cross-Functional Alignment",
    subtitle: "Align demand, supply, and financial plans in a single platform for better decision-making.",
    features: [
      { title: "Demand-Supply Balancing", desc: "Automatically reconcile demand forecasts with supply constraints." },
      { title: "Financial Integration", desc: "Link operational plans to P&L targets and margin goals." },
      { title: "Scenario Planning", desc: "Run what-if scenarios across demand, supply, and financial dimensions." },
      { title: "Executive Dashboard", desc: "One-view summary for leadership with drill-down capability." },
      { title: "Consensus Forecasting", desc: "Combine statistical forecasts with market intelligence from sales teams." },
      { title: "Cadence Management", desc: "Monthly S&OP cycles with automated agenda and action tracking." },
    ],
    formula: "IBP Score = Financial Alignment × Demand Accuracy × Supply Fill Rate",
  },
  "inventory-planning": {
    title: "Inventory Planning",
    badge: "Zero Stockouts, Zero Waste",
    subtitle: "Optimize inventory levels across your network with statistical safety stock and DOH analysis.",
    features: [
      { title: "Statistical Safety Stock", desc: "z-score × MAD × √(LT/RP) formula with configurable service levels." },
      { title: "DOH Analysis", desc: "Days on Hand tracking with automated alerts for overstock and understock." },
      { title: "Stockout Prediction", desc: "AI-powered risk scoring for upcoming stockout events." },
      { title: "Overstock Detection", desc: "Identify slow-moving inventory before it becomes dead stock." },
      { title: "Network Optimization", desc: "Balance inventory across warehouses, DCs, and stores." },
      { title: "ABC/XYZ Classification", desc: "Classify SKUs by revenue contribution and demand variability." },
    ],
    formula: "Safety Stock = z-score × MAD × √(Lead Time / Review Period)",
  },
  "merchandise-financial-planning": {
    title: "Merchandise Financial Planning",
    badge: "Plan to Profit",
    subtitle: "Build top-down and bottom-up financial plans that align merchandise strategy with profit targets.",
    features: [
      { title: "Top-Down / Bottom-Up", desc: "Reconcile company targets with department-level merchandise plans." },
      { title: "Open-to-Buy Management", desc: "Real-time OTB tracking with variance alerts." },
      { title: "Margin Planning", desc: "Plan initial markup, markdown cadence, and final margin targets." },
      { title: "Category Plans", desc: "Detailed plans per category, subcategory, and brand." },
      { title: "Historical Benchmarking", desc: "Compare planned vs actual across seasons and categories." },
      { title: "What-If Scenarios", desc: "Model pricing changes, mix shifts, and promotion impacts." },
    ],
    formula: "Planned Profit = (Sales × IMU%) - Markdowns - Shrinkage - Operating Costs",
  },
  "otb-wssi": {
    title: "OTB / WSSI",
    badge: "Real-Time Buy Control",
    subtitle: "Open-to-Buy and Weekly Sales, Stock & Intake tracking for complete merchandise control.",
    features: [
      { title: "Real-Time OTB", desc: "Live OTB calculation updated as sales and receipts flow in." },
      { title: "WSSI Dashboard", desc: "Weekly sales, stock, and intake monitoring with trend analysis." },
      { title: "Forward Cover", desc: "Weeks of cover projections based on forecasted demand." },
      { title: "Receipt Planning", desc: "Align purchase orders with planned intake windows." },
      { title: "Markdown Optimization", desc: "Time markdowns to maximize revenue and clear excess inventory." },
      { title: "Season Analysis", desc: "Post-season analysis with lessons learned for next season." },
    ],
    formula: "OTB = Planned Purchases - (On Order + In Transit + Committed Stock)",
  },
  "range-assortment": {
    title: "Range & Assortment",
    badge: "Curated Collections",
    subtitle: "Build range plans that balance commercial targets with brand strategy and customer needs.",
    features: [
      { title: "Range Architecture", desc: "Define option counts, price ladders, and category breadth." },
      { title: "Good-Better-Best", desc: "Price tier management with minimum representation rules." },
      { title: "Attribute Planning", desc: "Plan by color, fabric, silhouette, and other product attributes." },
      { title: "Seasonal Calendar", desc: "Map deliveries to selling windows and promotional events." },
      { title: "Competitive Analysis", desc: "Benchmark your range against competitor assortments." },
      { title: "Visual Line Boards", desc: "Digital line sheets for range review meetings." },
    ],
    formula: "Range Score = Customer Coverage × Margin Contribution × Brand Fit",
  },
};

export default function ProductPage() {
  const { slug } = useParams();
  const product = PRODUCTS[slug];

  // ROI calculator state
  const [skus, setSkus] = useState(10000);
  const [accuracy, setAccuracy] = useState(65);
  const [avgValue, setAvgValue] = useState(50);

  const stockoutSavings = Math.round(skus * avgValue * 0.15 * 0.41);
  const overstockSavings = Math.round(skus * avgValue * 0.15 * 0.32);
  const totalSavings = stockoutSavings + overstockSavings;

  if (!product) {
    return (
      <div className="min-h-screen bg-[#0a0e27]">
        <Navbar />
        <div className="pt-32 text-center text-white">
          <h1 className="text-3xl font-bold mb-4">Product Not Found</h1>
          <Link to="/" className="text-indigo-400 hover:text-indigo-300">Back to Home</Link>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0e27]" data-testid="product-page">
      <Navbar />

      {/* Hero */}
      <section className="pt-28 pb-16 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/5 via-rose-500/5 to-transparent pointer-events-none" />
        <div className="relative z-10 max-w-3xl mx-auto px-4 sm:px-6">
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm font-medium mb-6" data-testid="product-badge">
            {product.badge}
          </span>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white mb-4" data-testid="product-title">{product.title}</h1>
          <p className="text-lg text-slate-400 leading-relaxed">{product.subtitle}</p>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 max-w-6xl mx-auto px-4 sm:px-6">
        <h2 className="text-2xl font-bold text-white text-center mb-10">Key Features</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {product.features.map((f) => (
            <div key={f.title} className="bg-white/[0.04] border border-indigo-500/10 rounded-2xl p-5 hover:bg-white/[0.07] transition-all">
              <h3 className="text-base font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Formula */}
      {product.formula && (
        <section className="py-16 max-w-4xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-white text-center mb-8">Technical Specification</h2>
          <div className="bg-black/40 border border-indigo-500/20 rounded-2xl p-8 text-center font-mono text-sm text-indigo-300 leading-relaxed" data-testid="product-formula">
            {product.formula}
          </div>
        </section>
      )}

      {/* ROI Calculator */}
      <section className="py-16 max-w-4xl mx-auto px-4 sm:px-6">
        <h2 className="text-2xl font-bold text-white text-center mb-8">Calculate Your ROI</h2>
        <div className="bg-white/[0.04] border border-indigo-500/10 rounded-2xl p-6 sm:p-8" data-testid="roi-calculator">
          <div className="grid sm:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">Number of SKUs</label>
              <input type="number" value={skus} onChange={(e) => setSkus(+e.target.value)} className="w-full px-4 py-2.5 bg-black/30 border border-indigo-500/20 rounded-xl text-white text-sm focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500/40 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">Current Forecast Accuracy %</label>
              <input type="number" value={accuracy} onChange={(e) => setAccuracy(+e.target.value)} className="w-full px-4 py-2.5 bg-black/30 border border-indigo-500/20 rounded-xl text-white text-sm focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500/40 outline-none" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">Average SKU Value ($)</label>
              <input type="number" value={avgValue} onChange={(e) => setAvgValue(+e.target.value)} className="w-full px-4 py-2.5 bg-black/30 border border-indigo-500/20 rounded-xl text-white text-sm focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500/40 outline-none" />
            </div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-emerald-400 mb-1">${totalSavings.toLocaleString()}</div>
            <div className="text-sm text-slate-400">Estimated Annual Savings</div>
            <div className="flex justify-center gap-6 mt-3 text-xs text-slate-500">
              <span>Stockout Reduction: ${stockoutSavings.toLocaleString()}</span>
              <span>Overstock Reduction: ${overstockSavings.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </section>

      <CTASection />
      <Footer />
    </div>
  );
}
