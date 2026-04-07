import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X, ChevronLeft, ChevronRight, Play, Pause,
  Upload, LayoutDashboard, Brain, AlertTriangle, ShoppingCart,
  FileSpreadsheet, CheckCircle, TrendingUp, Package, BarChart3,
  ArrowRight, Clock, Target, Zap, Eye
} from "lucide-react";

const AUTOPLAY_INTERVAL = 6000;

const steps = [
  {
    id: 1,
    icon: Upload,
    title: "Upload Your Data",
    subtitle: "Drag & drop CSV files — validated in seconds",
    description: "Upload 7 CSV file types including Style Master, Sales, Inventory, and Store data. Our engine auto-validates column headers, data types, and cross-references instantly.",
    highlights: ["7 CSV file types supported", "Auto-validation & error reporting", "Bulk upload with progress tracking"],
    accent: "#3b82f6",
    accentLight: "#dbeafe",
  },
  {
    id: 2,
    icon: LayoutDashboard,
    title: "Executive Dashboard",
    subtitle: "Real-time KPIs and health scores at a glance",
    description: "Get a bird's-eye view of your retail performance. Track revenue, inventory health, sell-through rates, and business health score — all updated in real time.",
    highlights: ["4 KPI metric cards", "Business Health Score gauge", "Revenue & sell-through trends"],
    accent: "#8b5cf6",
    accentLight: "#ede9fe",
  },
  {
    id: 3,
    icon: Brain,
    title: "AI Demand Forecast",
    subtitle: "12-month predictions with 91% accuracy",
    description: "Our 3-model ensemble ML engine (ARIMA + Prophet + XGBoost) generates demand forecasts with confidence bands, seasonal decomposition, and category-level breakdowns.",
    highlights: ["3-model ensemble ML", "Confidence interval bands", "Seasonal pattern detection"],
    accent: "#06b6d4",
    accentLight: "#cffafe",
  },
  {
    id: 4,
    icon: AlertTriangle,
    title: "Stock-Out Alerts",
    subtitle: "Catch risks before they cost you revenue",
    description: "Identify stock-out risks across stores and SKUs with Red/Orange/Yellow severity levels. Get actionable replenishment recommendations before you lose sales.",
    highlights: ["3-tier severity levels", "Store × SKU risk matrix", "Auto replenishment suggestions"],
    accent: "#ef4444",
    accentLight: "#fee2e2",
  },
  {
    id: 5,
    icon: ShoppingCart,
    title: "Buy Plan Generator",
    subtitle: "Set revenue target → get ML-powered buying plan",
    description: "Enter your target revenue and let AI calculate optimal quantities, channel splits, and category allocations. Export the complete buy plan as an Excel workbook.",
    highlights: ["Revenue-target driven planning", "Channel & category splits", "One-click Excel export"],
    accent: "#10b981",
    accentLight: "#d1fae5",
  },
];

/* ── Inline Mockup Components ─────────────────────── */

function UploadMockup() {
  const files = [
    { name: "style_master.csv", size: "2.4 MB", status: "done" },
    { name: "sales_data.csv", size: "8.1 MB", status: "done" },
    { name: "inventory.csv", size: "5.6 MB", status: "progress" },
    { name: "store_master.csv", size: "1.2 MB", status: "pending" },
  ];
  return (
    <div className="space-y-3 p-4">
      <div className="border-2 border-dashed border-blue-300 bg-blue-50/50 rounded-xl p-6 text-center">
        <Upload className="h-8 w-8 text-blue-400 mx-auto mb-2" />
        <p className="text-sm font-medium text-blue-700">Drop CSV files here</p>
        <p className="text-xs text-blue-400 mt-1">or click to browse</p>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {["Style Master", "Sales", "Inventory", "Stores", "SKU", "Marketplace", "Categories"].map((t) => (
          <span key={t} className="text-[10px] px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full font-medium">{t}</span>
        ))}
      </div>
      <div className="space-y-2">
        {files.map((f, i) => (
          <motion.div
            key={f.name}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 + i * 0.15 }}
            className="flex items-center gap-3 bg-white border border-gray-100 rounded-lg px-3 py-2"
          >
            <FileSpreadsheet className="h-4 w-4 text-green-600 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-800 truncate">{f.name}</p>
              <p className="text-[10px] text-gray-400">{f.size}</p>
            </div>
            {f.status === "done" && <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />}
            {f.status === "progress" && (
              <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden flex-shrink-0">
                <motion.div
                  className="h-full bg-blue-500 rounded-full"
                  initial={{ width: "20%" }}
                  animate={{ width: "75%" }}
                  transition={{ duration: 2, repeat: Infinity, repeatType: "reverse" }}
                />
              </div>
            )}
            {f.status === "pending" && <Clock className="h-4 w-4 text-gray-300 flex-shrink-0" />}
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function DashboardMockup() {
  const kpis = [
    { label: "Revenue", value: "12.4 Cr", change: "+18%", up: true },
    { label: "Sell-Through", value: "73%", change: "+5%", up: true },
    { label: "Inventory", value: "8,420", change: "-12%", up: false },
    { label: "Health Score", value: "87/100", change: "+3", up: true },
  ];
  const bars = [68, 82, 55, 91, 74, 60, 85];
  const months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan"];
  return (
    <div className="space-y-3 p-4">
      <div className="grid grid-cols-2 gap-2">
        {kpis.map((k, i) => (
          <motion.div
            key={k.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 + i * 0.1 }}
            className="bg-white border border-gray-100 rounded-lg p-3"
          >
            <p className="text-[10px] text-gray-400 uppercase tracking-wide">{k.label}</p>
            <p className="text-lg font-bold text-gray-900 mt-0.5">{k.value}</p>
            <span className={`text-[10px] font-medium ${k.up ? "text-green-600" : "text-red-500"}`}>{k.change}</span>
          </motion.div>
        ))}
      </div>
      <div className="bg-white border border-gray-100 rounded-lg p-3">
        <p className="text-xs font-medium text-gray-700 mb-2">Monthly Revenue Trend</p>
        <div className="flex items-end gap-2 h-32">
          {bars.map((h, i) => (
            <div key={i} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
              <motion.div
                className="w-full rounded-t bg-gradient-to-t from-purple-500 to-purple-400"
                initial={{ height: 0 }}
                animate={{ height: `${h}%` }}
                transition={{ delay: 0.4 + i * 0.08, duration: 0.5 }}
              />
              <span className="text-[9px] text-gray-400">{months[i]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ForecastMockup() {
  const points = [30, 35, 28, 42, 55, 50, 62, 58, 70, 75, 68, 82];
  const w = 280;
  const h = 120;
  const xStep = w / (points.length - 1);
  const maxVal = 100;
  const toY = (v) => h - (v / maxVal) * h;

  const line = points.map((p, i) => `${i === 0 ? "M" : "L"}${i * xStep},${toY(p)}`).join(" ");
  const upperBand = points.map((p, i) => `${i === 0 ? "M" : "L"}${i * xStep},${toY(Math.min(p + 12, 100))}`).join(" ");
  const lowerBand = points.map((p, i) => `L${(points.length - 1 - i) * xStep},${toY(Math.max(p - 12, 0))}`).join(" ");
  const bandPath = `${upperBand} ${points.map((p, i) => `L${(points.length - 1 - i) * xStep},${toY(Math.max(points[points.length - 1 - i] - 12, 0))}`).join(" ")} Z`;

  const months = ["Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan"];

  return (
    <div className="space-y-3 p-4">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-0.5 bg-cyan-500 rounded" />
          <span className="text-[10px] text-gray-500">Forecast</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-cyan-100 rounded-sm border border-cyan-200" />
          <span className="text-[10px] text-gray-500">Confidence Band</span>
        </div>
        <div className="ml-auto px-2 py-0.5 bg-cyan-50 border border-cyan-200 rounded text-[10px] text-cyan-700 font-medium">91% Accuracy</div>
      </div>
      <div className="bg-white border border-gray-100 rounded-lg p-3">
        <p className="text-xs font-medium text-gray-700 mb-2">12-Month Demand Forecast</p>
        <div className="h-32 relative">
          <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full" preserveAspectRatio="none">
            <motion.path
              d={bandPath}
              fill="#06b6d4"
              fillOpacity="0.1"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5, duration: 0.8 }}
            />
            <motion.path
              d={line}
              fill="none"
              stroke="#06b6d4"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ delay: 0.3, duration: 1.5 }}
            />
            {points.map((p, i) => (
              <motion.circle
                key={i}
                cx={i * xStep}
                cy={toY(p)}
                r="3"
                fill="white"
                stroke="#06b6d4"
                strokeWidth="2"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 + i * 0.1 }}
              />
            ))}
          </svg>
        </div>
        <div className="flex justify-between mt-1">
          {months.filter((_, i) => i % 2 === 0).map((m) => (
            <span key={m} className="text-[9px] text-gray-400">{m}</span>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {[
          { label: "Peak Month", value: "Jan", sub: "82 units" },
          { label: "Growth", value: "+173%", sub: "vs baseline" },
          { label: "Seasonality", value: "Detected", sub: "Q4 spike" },
        ].map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 + i * 0.1 }}
            className="bg-white border border-gray-100 rounded-lg p-2 text-center"
          >
            <p className="text-[10px] text-gray-400">{s.label}</p>
            <p className="text-sm font-bold text-gray-900">{s.value}</p>
            <p className="text-[9px] text-gray-400">{s.sub}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function StockOutMockup() {
  const alerts = [
    { sku: "SKU-1042", store: "Mumbai Central", level: "Critical", days: "0 days left", color: "red" },
    { sku: "SKU-2891", store: "Delhi NCR Hub", level: "Warning", days: "3 days left", color: "orange" },
    { sku: "SKU-0567", store: "Bangalore M.G.", level: "Watch", days: "7 days left", color: "yellow" },
    { sku: "SKU-3214", store: "Chennai T.Nagar", level: "Critical", days: "1 day left", color: "red" },
  ];
  const colorMap = {
    red: { bg: "bg-red-50", border: "border-red-200", badge: "bg-red-100 text-red-700", dot: "bg-red-500" },
    orange: { bg: "bg-orange-50", border: "border-orange-200", badge: "bg-orange-100 text-orange-700", dot: "bg-orange-500" },
    yellow: { bg: "bg-yellow-50", border: "border-yellow-200", badge: "bg-yellow-100 text-yellow-700", dot: "bg-yellow-500" },
  };
  return (
    <div className="space-y-3 p-4">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-2.5 py-1 bg-red-50 border border-red-200 rounded-lg">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          <span className="text-xs font-semibold text-red-700">2 Critical</span>
        </div>
        <div className="flex items-center gap-2 px-2.5 py-1 bg-orange-50 border border-orange-200 rounded-lg">
          <span className="w-2 h-2 rounded-full bg-orange-500" />
          <span className="text-xs font-semibold text-orange-700">1 Warning</span>
        </div>
        <div className="flex items-center gap-2 px-2.5 py-1 bg-yellow-50 border border-yellow-200 rounded-lg">
          <span className="w-2 h-2 rounded-full bg-yellow-500" />
          <span className="text-xs font-semibold text-yellow-700">1 Watch</span>
        </div>
      </div>
      <div className="space-y-2">
        {alerts.map((a, i) => {
          const c = colorMap[a.color];
          return (
            <motion.div
              key={a.sku}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + i * 0.12 }}
              className={`${c.bg} ${c.border} border rounded-lg px-3 py-2.5 flex items-center gap-3`}
            >
              <span className={`w-2 h-2 rounded-full ${c.dot} flex-shrink-0`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-xs font-semibold text-gray-900">{a.sku}</p>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${c.badge}`}>{a.level}</span>
                </div>
                <p className="text-[10px] text-gray-500 mt-0.5">{a.store}</p>
              </div>
              <span className="text-[10px] text-gray-500 font-medium flex-shrink-0">{a.days}</span>
            </motion.div>
          );
        })}
      </div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="bg-white border border-gray-200 rounded-lg p-3 flex items-center gap-3"
      >
        <Zap className="h-4 w-4 text-blue-500 flex-shrink-0" />
        <div>
          <p className="text-xs font-medium text-gray-800">Auto Replenishment</p>
          <p className="text-[10px] text-gray-500">Transfer 240 units from Pune warehouse to cover critical gaps</p>
        </div>
      </motion.div>
    </div>
  );
}

function BuyPlanMockup() {
  const rows = [
    { category: "Topwear", qty: "2,400", value: "36L", pct: 42 },
    { category: "Bottomwear", qty: "1,800", value: "27L", pct: 31 },
    { category: "Dresses", qty: "960", value: "18.5L", pct: 21 },
    { category: "Accessories", qty: "540", value: "5.2L", pct: 6 },
  ];
  return (
    <div className="space-y-3 p-4">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-3 flex items-center gap-3"
      >
        <Target className="h-6 w-6 text-green-600 flex-shrink-0" />
        <div>
          <p className="text-[10px] text-green-600 uppercase tracking-wide font-medium">Revenue Target</p>
          <p className="text-lg font-bold text-green-800">1.2 Crore</p>
        </div>
        <div className="ml-auto text-right">
          <p className="text-[10px] text-green-600">Computed Plan</p>
          <p className="text-sm font-bold text-green-800">5,700 units</p>
        </div>
      </motion.div>
      <div className="bg-white border border-gray-100 rounded-lg overflow-hidden">
        <div className="grid grid-cols-4 gap-0 bg-gray-50 px-3 py-2 border-b border-gray-100">
          <span className="text-[10px] font-semibold text-gray-500 uppercase">Category</span>
          <span className="text-[10px] font-semibold text-gray-500 uppercase text-right">Qty</span>
          <span className="text-[10px] font-semibold text-gray-500 uppercase text-right">Value</span>
          <span className="text-[10px] font-semibold text-gray-500 uppercase text-right">Share</span>
        </div>
        {rows.map((r, i) => (
          <motion.div
            key={r.category}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 + i * 0.1 }}
            className="grid grid-cols-4 gap-0 px-3 py-2.5 border-b border-gray-50 items-center"
          >
            <span className="text-xs font-medium text-gray-800">{r.category}</span>
            <span className="text-xs text-gray-600 text-right">{r.qty}</span>
            <span className="text-xs text-gray-600 text-right">{r.value}</span>
            <div className="flex items-center justify-end gap-1.5">
              <div className="w-12 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-green-500 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${r.pct}%` }}
                  transition={{ delay: 0.6 + i * 0.1, duration: 0.6 }}
                />
              </div>
              <span className="text-[10px] text-gray-500 w-6 text-right">{r.pct}%</span>
            </div>
          </motion.div>
        ))}
      </div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
      >
        <div className="h-9 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg flex items-center justify-center gap-2 text-white text-xs font-semibold">
          <Package className="h-3.5 w-3.5" />
          Export Buy Plan (.xlsx)
        </div>
      </motion.div>
    </div>
  );
}

const mockups = [UploadMockup, DashboardMockup, ForecastMockup, StockOutMockup, BuyPlanMockup];

/* ── Slide Variants ────────────────────────────────── */

const slideVariants = {
  enter: (dir) => ({ x: dir > 0 ? 300 : -300, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (dir) => ({ x: dir > 0 ? -300 : 300, opacity: 0 }),
};

/* ── Main ProductTour Component ───────────────────── */

export default function ProductTour({ isOpen, onClose }) {
  const [current, setCurrent] = useState(0);
  const [direction, setDirection] = useState(1);
  const [autoPlay, setAutoPlay] = useState(false);
  const [progress, setProgress] = useState(0);
  const intervalRef = useRef(null);
  const progressRef = useRef(null);

  const step = steps[current];
  const Mockup = mockups[current];
  const Icon = step.icon;

  const goTo = useCallback((idx, dir) => {
    setDirection(dir);
    setCurrent(idx);
    setProgress(0);
  }, []);

  const next = useCallback(() => {
    if (current < steps.length - 1) {
      goTo(current + 1, 1);
    } else {
      goTo(0, 1);
    }
  }, [current, goTo]);

  const prev = useCallback(() => {
    if (current > 0) goTo(current - 1, -1);
  }, [current, goTo]);

  // Auto-play
  useEffect(() => {
    if (!autoPlay || !isOpen) return;
    progressRef.current = setInterval(() => {
      setProgress((p) => {
        if (p >= 100) return 100;
        return p + (100 / (AUTOPLAY_INTERVAL / 50));
      });
    }, 50);
    intervalRef.current = setInterval(next, AUTOPLAY_INTERVAL);
    return () => {
      clearInterval(intervalRef.current);
      clearInterval(progressRef.current);
    };
  }, [autoPlay, isOpen, next]);

  // Reset progress on step change
  useEffect(() => {
    setProgress(0);
  }, [current]);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight") next();
      if (e.key === "ArrowLeft") prev();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, next, prev, onClose]);

  // Reset on open
  useEffect(() => {
    if (isOpen) {
      setCurrent(0);
      setDirection(1);
      setAutoPlay(false);
      setProgress(0);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          data-testid="product-tour-overlay"
          className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

          {/* Modal */}
          <motion.div
            data-testid="product-tour-modal"
            className="relative w-full max-w-4xl bg-white rounded-2xl shadow-2xl overflow-hidden"
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
          >
            {/* Auto-play progress bar */}
            {autoPlay && (
              <div className="absolute top-0 left-0 right-0 h-1 bg-gray-100 z-10">
                <motion.div
                  className="h-full rounded-r"
                  style={{ backgroundColor: step.accent, width: `${progress}%` }}
                  transition={{ duration: 0.05 }}
                />
              </div>
            )}

            {/* Close button */}
            <button
              onClick={onClose}
              data-testid="product-tour-close"
              className="absolute top-4 right-4 z-20 w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 transition text-gray-500 hover:text-gray-700"
            >
              <X className="h-4 w-4" />
            </button>

            {/* Content */}
            <div className="flex flex-col md:flex-row min-h-[480px]">
              {/* Left Panel — Info */}
              <div className="w-full md:w-[340px] p-6 md:p-8 flex flex-col bg-gray-50/50 border-b md:border-b-0 md:border-r border-gray-100">
                {/* Step indicator */}
                <div className="flex items-center gap-2 mb-6">
                  <span
                    className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full"
                    style={{ backgroundColor: step.accentLight, color: step.accent }}
                  >
                    Step {step.id} of {steps.length}
                  </span>
                  {current === steps.length - 1 && (
                    <span className="text-[11px] font-medium text-gray-400">Final step</span>
                  )}
                </div>

                {/* Icon + Title */}
                <AnimatePresence mode="wait" custom={direction}>
                  <motion.div
                    key={current}
                    custom={direction}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.25 }}
                    className="flex-1"
                  >
                    <div
                      className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
                      style={{ backgroundColor: step.accentLight }}
                    >
                      <Icon className="h-6 w-6" style={{ color: step.accent }} />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-1">{step.title}</h3>
                    <p className="text-sm text-gray-500 mb-4">{step.subtitle}</p>
                    <p className="text-sm text-gray-600 leading-relaxed mb-5">{step.description}</p>
                    <ul className="space-y-2">
                      {step.highlights.map((h, i) => (
                        <motion.li
                          key={h}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.15 + i * 0.08 }}
                          className="flex items-center gap-2 text-sm text-gray-700"
                        >
                          <CheckCircle className="h-4 w-4 flex-shrink-0" style={{ color: step.accent }} />
                          {h}
                        </motion.li>
                      ))}
                    </ul>
                  </motion.div>
                </AnimatePresence>
              </div>

              {/* Right Panel — Mockup */}
              <div className="flex-1 relative overflow-hidden bg-gray-50">
                {/* Browser chrome */}
                <div className="flex items-center gap-1.5 px-4 py-2.5 bg-gray-100 border-b border-gray-200">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-400" />
                  <div className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
                  <div className="w-2.5 h-2.5 rounded-full bg-green-400" />
                  <span className="ml-2 text-[10px] text-gray-400 font-mono">app.getmyplan.in</span>
                </div>
                <div className="h-[calc(100%-36px)]">
                  <AnimatePresence mode="wait" custom={direction}>
                    <motion.div
                      key={current}
                      custom={direction}
                      variants={slideVariants}
                      initial="enter"
                      animate="center"
                      exit="exit"
                      transition={{ duration: 0.3, ease: "easeInOut" }}
                      className="h-full"
                      data-testid={`tour-mockup-step-${step.id}`}
                    >
                      <Mockup />
                    </motion.div>
                  </AnimatePresence>
                </div>
              </div>
            </div>

            {/* Bottom Bar */}
            <div className="flex items-center justify-between px-6 py-4 bg-white border-t border-gray-100">
              {/* Step dots */}
              <div className="flex items-center gap-2">
                {steps.map((s, i) => (
                  <button
                    key={s.id}
                    onClick={() => goTo(i, i > current ? 1 : -1)}
                    data-testid={`tour-dot-${i}`}
                    className="relative group"
                  >
                    <div
                      className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                        i === current ? "scale-125" : "bg-gray-300 hover:bg-gray-400"
                      }`}
                      style={i === current ? { backgroundColor: step.accent } : {}}
                    />
                    <span className="absolute -top-7 left-1/2 -translate-x-1/2 text-[10px] bg-gray-800 text-white px-2 py-0.5 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition pointer-events-none">
                      {s.title}
                    </span>
                  </button>
                ))}
              </div>

              {/* Controls */}
              <div className="flex items-center gap-2">
                {/* Auto-play toggle */}
                <button
                  onClick={() => setAutoPlay(!autoPlay)}
                  data-testid="tour-autoplay-toggle"
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                    autoPlay
                      ? "bg-gray-900 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {autoPlay ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
                  {autoPlay ? "Pause" : "Auto-play"}
                </button>

                <div className="w-px h-5 bg-gray-200" />

                {/* Skip */}
                <button
                  onClick={onClose}
                  data-testid="tour-skip-btn"
                  className="px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-gray-700 transition"
                >
                  Skip tour
                </button>

                {/* Prev */}
                <button
                  onClick={prev}
                  disabled={current === 0}
                  data-testid="tour-prev-btn"
                  className="w-8 h-8 flex items-center justify-center rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>

                {/* Next / Finish */}
                {current < steps.length - 1 ? (
                  <button
                    onClick={next}
                    data-testid="tour-next-btn"
                    className="flex items-center gap-1 px-4 py-1.5 rounded-lg text-xs font-semibold text-white transition hover:opacity-90"
                    style={{ backgroundColor: step.accent }}
                  >
                    Next <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                ) : (
                  <button
                    onClick={onClose}
                    data-testid="tour-finish-btn"
                    className="flex items-center gap-1 px-4 py-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg text-xs font-semibold text-white transition hover:opacity-90"
                  >
                    Start Free Trial <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
