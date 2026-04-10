import { ArrowRight, CheckCircle, Play, Upload, LayoutDashboard, Brain, AlertTriangle, ShoppingCart } from "lucide-react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";

const TOUR_STEPS = [
  { id: 1, icon: Upload, label: "Upload Data", color: "#3b82f6", desc: "Drag & drop 7 CSV file types with auto-validation" },
  { id: 2, icon: LayoutDashboard, label: "Dashboard", color: "#8b5cf6", desc: "Real-time KPIs, health score & revenue trends" },
  { id: 3, icon: Brain, label: "AI Forecast", color: "#06b6d4", desc: "12-month demand predictions with 91% accuracy" },
  { id: 4, icon: AlertTriangle, label: "Stock Alerts", color: "#ef4444", desc: "Red/Orange/Yellow severity risk detection" },
  { id: 5, icon: ShoppingCart, label: "Buy Plan", color: "#10b981", desc: "Revenue-target driven ML purchasing plan" },
];

function MiniUpload() {
  const files = [
    { name: "style_master.csv", pct: 100 },
    { name: "sales_data.csv", pct: 100 },
    { name: "inventory.csv", pct: 72 },
  ];
  return (
    <div className="p-5 space-y-3">
      <div className="border-2 border-dashed border-blue-300 bg-blue-50/50 rounded-lg p-4 text-center">
        <Upload className="h-6 w-6 text-blue-400 mx-auto mb-1" />
        <p className="text-xs font-medium text-blue-700">Drop CSV files here</p>
      </div>
      {files.map((f, i) => (
        <motion.div key={f.name} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 + i * 0.15 }} className="flex items-center gap-3 bg-white border border-gray-100 rounded-lg px-3 py-2">
          <div className="w-6 h-6 bg-green-50 rounded flex items-center justify-center"><Upload className="h-3 w-3 text-green-600" /></div>
          <span className="text-xs text-gray-700 flex-1">{f.name}</span>
          {f.pct === 100 ? <CheckCircle className="h-4 w-4 text-green-500" /> : (
            <div className="w-14 h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <motion.div className="h-full bg-blue-500 rounded-full" initial={{ width: "30%" }} animate={{ width: `${f.pct}%` }} transition={{ duration: 2, repeat: Infinity, repeatType: "reverse" }} />
            </div>
          )}
        </motion.div>
      ))}
    </div>
  );
}

function MiniDashboard() {
  const kpis = [
    { label: "Revenue", value: "12.4Cr", up: true },
    { label: "Sell-Through", value: "73%", up: true },
    { label: "Inventory", value: "8,420", up: false },
    { label: "Health", value: "87/100", up: true },
  ];
  const bars = [68, 82, 55, 91, 74, 60, 85];
  return (
    <div className="p-5 space-y-3">
      <div className="grid grid-cols-4 gap-2">
        {kpis.map((k, i) => (
          <motion.div key={k.label} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.15 + i * 0.08 }} className="bg-white border border-gray-100 rounded-lg p-2 text-center">
            <p className="text-[9px] text-gray-400 uppercase">{k.label}</p>
            <p className="text-sm font-bold text-gray-900">{k.value}</p>
            <span className={`text-[9px] font-medium ${k.up ? "text-green-600" : "text-red-500"}`}>{k.up ? "+18%" : "-12%"}</span>
          </motion.div>
        ))}
      </div>
      <div className="bg-white border border-gray-100 rounded-lg p-3">
        <p className="text-[10px] font-medium text-gray-600 mb-2">Revenue Trend</p>
        <div className="flex items-end gap-1.5 h-20">
          {bars.map((h, i) => (
            <motion.div key={i} className="flex-1 bg-gradient-to-t from-purple-500 to-purple-400 rounded-t" initial={{ height: 0 }} animate={{ height: `${h}%` }} transition={{ delay: 0.3 + i * 0.06, duration: 0.5 }} />
          ))}
        </div>
      </div>
    </div>
  );
}

function MiniForecast() {
  const pts = [30, 35, 28, 42, 55, 50, 62, 58, 70, 75, 68, 82];
  const w = 300, h = 80;
  const xS = w / (pts.length - 1);
  const toY = (v) => h - (v / 100) * h;
  const line = pts.map((p, i) => `${i === 0 ? "M" : "L"}${i * xS},${toY(p)}`).join(" ");
  return (
    <div className="p-5 space-y-3">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1"><div className="w-3 h-0.5 bg-cyan-500 rounded" /><span className="text-[9px] text-gray-500">Forecast</span></div>
        <div className="flex items-center gap-1"><div className="w-3 h-3 bg-cyan-100 rounded-sm border border-cyan-200" /><span className="text-[9px] text-gray-500">Confidence</span></div>
        <div className="ml-auto px-2 py-0.5 bg-cyan-50 border border-cyan-200 rounded text-[9px] text-cyan-700 font-medium">91% Accuracy</div>
      </div>
      <div className="bg-white border border-gray-100 rounded-lg p-3">
        <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ height: 80 }} preserveAspectRatio="none">
          <motion.path d={line} fill="none" stroke="#06b6d4" strokeWidth="2.5" strokeLinecap="round" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 0.2, duration: 1.5 }} />
          {pts.map((p, i) => <motion.circle key={i} cx={i * xS} cy={toY(p)} r="2.5" fill="white" stroke="#06b6d4" strokeWidth="1.5" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 + i * 0.08 }} />)}
        </svg>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {[{ l: "Peak", v: "Jan" }, { l: "Growth", v: "+173%" }, { l: "Season", v: "Q4 spike" }].map((s, i) => (
          <motion.div key={s.l} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 + i * 0.1 }} className="bg-white border border-gray-100 rounded-lg p-2 text-center">
            <p className="text-[9px] text-gray-400">{s.l}</p>
            <p className="text-xs font-bold text-gray-900">{s.v}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function MiniAlerts() {
  const alerts = [
    { sku: "SKU-1042", store: "Mumbai Central", level: "Critical", color: "red" },
    { sku: "SKU-2891", store: "Delhi NCR Hub", level: "Warning", color: "orange" },
    { sku: "SKU-0567", store: "Bangalore M.G.", level: "Watch", color: "yellow" },
  ];
  const cm = { red: "bg-red-50 border-red-200 text-red-700", orange: "bg-orange-50 border-orange-200 text-orange-700", yellow: "bg-yellow-50 border-yellow-200 text-yellow-700" };
  const dm = { red: "bg-red-500", orange: "bg-orange-500", yellow: "bg-yellow-500" };
  return (
    <div className="p-5 space-y-3">
      <div className="flex items-center gap-2">
        <span className="flex items-center gap-1.5 px-2 py-0.5 bg-red-50 border border-red-200 rounded text-[10px] text-red-700 font-semibold"><span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />2 Critical</span>
        <span className="flex items-center gap-1.5 px-2 py-0.5 bg-orange-50 border border-orange-200 rounded text-[10px] text-orange-700 font-semibold"><span className="w-1.5 h-1.5 rounded-full bg-orange-500" />1 Warning</span>
      </div>
      {alerts.map((a, i) => (
        <motion.div key={a.sku} initial={{ opacity: 0, x: 15 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 + i * 0.12 }} className={`${cm[a.color]} border rounded-lg px-3 py-2 flex items-center gap-2`}>
          <span className={`w-2 h-2 rounded-full ${dm[a.color]}`} />
          <div className="flex-1">
            <p className="text-xs font-semibold text-gray-900">{a.sku} <span className={`text-[9px] px-1 py-0.5 rounded ${cm[a.color]} font-medium`}>{a.level}</span></p>
            <p className="text-[10px] text-gray-500">{a.store}</p>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

function MiniBuyPlan() {
  const rows = [
    { cat: "Topwear", qty: "2,400", pct: 42 },
    { cat: "Bottomwear", qty: "1,800", pct: 31 },
    { cat: "Dresses", qty: "960", pct: 21 },
  ];
  return (
    <div className="p-5 space-y-3">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-3 flex items-center gap-3">
        <div><p className="text-[9px] text-green-600 uppercase font-medium">Target</p><p className="text-base font-bold text-green-800">1.2 Cr</p></div>
        <div className="ml-auto text-right"><p className="text-[9px] text-green-600">Plan</p><p className="text-sm font-bold text-green-800">5,700 units</p></div>
      </motion.div>
      <div className="bg-white border border-gray-100 rounded-lg overflow-hidden">
        <div className="grid grid-cols-3 bg-gray-50 px-3 py-1.5 border-b border-gray-100">
          <span className="text-[9px] font-semibold text-gray-500 uppercase">Category</span>
          <span className="text-[9px] font-semibold text-gray-500 uppercase text-right">Qty</span>
          <span className="text-[9px] font-semibold text-gray-500 uppercase text-right">Share</span>
        </div>
        {rows.map((r, i) => (
          <motion.div key={r.cat} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 + i * 0.1 }} className="grid grid-cols-3 px-3 py-2 border-b border-gray-50 items-center">
            <span className="text-xs font-medium text-gray-800">{r.cat}</span>
            <span className="text-xs text-gray-600 text-right">{r.qty}</span>
            <div className="flex items-center justify-end gap-1">
              <div className="w-10 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <motion.div className="h-full bg-green-500 rounded-full" initial={{ width: 0 }} animate={{ width: `${r.pct}%` }} transition={{ delay: 0.5 + i * 0.1, duration: 0.5 }} />
              </div>
              <span className="text-[9px] text-gray-500 w-5 text-right">{r.pct}%</span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

const MOCKUPS = [MiniUpload, MiniDashboard, MiniForecast, MiniAlerts, MiniBuyPlan];
const CYCLE_MS = 4000;

export default function Hero({ onWatchDemo, onRequestDemo }) {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setActive((p) => (p + 1) % TOUR_STEPS.length), CYCLE_MS);
    return () => clearInterval(timer);
  }, []);

  const step = TOUR_STEPS[active];
  const Mockup = MOCKUPS[active];

  return (
    <section data-testid="hero-section" className="relative pt-32 pb-20 overflow-hidden bg-gradient-to-br from-gray-50 via-white to-blue-50">
      {/* Animated blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-indigo-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-purple-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center"
        >
          {/* Live badge */}
          <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-full px-4 py-1.5 mb-6">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
            </span>
            <span className="text-sm text-blue-700 font-medium">AI-Powered Demand Planning</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold text-gray-900 leading-tight max-w-4xl mx-auto">
            Predict demand with{" "}
            <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              91% accuracy
            </span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto">
            Stop guessing. Start planning with AI. GetMyPlan uses 3-model ensemble ML
            to forecast demand, optimize inventory, and prevent stockouts.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/signup"
              data-testid="hero-signup-btn"
              className="group inline-flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-semibold hover:shadow-xl transition-all hover:scale-105"
            >
              Start Free Trial
              <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition" />
            </Link>
            <button
              onClick={onRequestDemo}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 border-2 border-blue-600 text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition"
              data-testid="hero-demo-btn"
            >
              Request a Demo
            </button>
          </div>

          <div className="mt-6 flex flex-wrap justify-center gap-6 text-sm text-gray-500">
            <span className="flex items-center gap-2"><CheckCircle className="h-5 w-5 text-green-500" /> No credit card required</span>
            <span className="flex items-center gap-2"><CheckCircle className="h-5 w-5 text-green-500" /> 7-day free trial</span>
            <span className="flex items-center gap-2"><CheckCircle className="h-5 w-5 text-green-500" /> Cancel anytime</span>
          </div>
        </motion.div>

        {/* Interactive Tour Preview */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="mt-16 relative max-w-4xl mx-auto"
        >
          <div className="rounded-xl overflow-hidden shadow-2xl border border-gray-200 bg-gradient-to-b from-slate-800 to-slate-900 p-1">
            {/* Browser chrome */}
            <div className="flex items-center gap-1.5 px-3 py-2">
              <div className="w-3 h-3 rounded-full bg-red-400" />
              <div className="w-3 h-3 rounded-full bg-yellow-400" />
              <div className="w-3 h-3 rounded-full bg-green-400" />
              <span className="ml-2 text-xs text-slate-400 font-mono">app.getmyplan.in/dashboard</span>
            </div>

            {/* Content area */}
            <div className="bg-gray-50 rounded-b-lg">
              {/* Step tabs */}
              <div className="flex border-b border-gray-200 bg-white px-2">
                {TOUR_STEPS.map((s, i) => {
                  const Icon = s.icon;
                  const isActive = i === active;
                  return (
                    <button
                      key={s.id}
                      onClick={() => setActive(i)}
                      data-testid={`hero-tour-tab-${i}`}
                      className={`flex items-center gap-1.5 px-3 py-2.5 text-xs font-medium transition-all relative ${
                        isActive ? "text-gray-900" : "text-gray-400 hover:text-gray-600"
                      }`}
                    >
                      <Icon className="h-3.5 w-3.5" style={isActive ? { color: s.color } : {}} />
                      <span className="hidden sm:inline">{s.label}</span>
                      {isActive && (
                        <motion.div
                          layoutId="heroTabIndicator"
                          className="absolute bottom-0 left-0 right-0 h-0.5 rounded-t"
                          style={{ backgroundColor: s.color }}
                        />
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Mockup */}
              <div className="min-h-[260px] relative overflow-hidden">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={active}
                    initial={{ opacity: 0, x: 30 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -30 }}
                    transition={{ duration: 0.25 }}
                  >
                    <Mockup />
                  </motion.div>
                </AnimatePresence>
              </div>

              {/* Progress bar */}
              <div className="flex gap-1 px-4 pb-3">
                {TOUR_STEPS.map((s, i) => (
                  <div key={s.id} className="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                    {i === active && (
                      <motion.div
                        className="h-full rounded-full"
                        style={{ backgroundColor: s.color }}
                        initial={{ width: "0%" }}
                        animate={{ width: "100%" }}
                        transition={{ duration: CYCLE_MS / 1000, ease: "linear" }}
                      />
                    )}
                    {i < active && <div className="h-full w-full rounded-full bg-gray-400" />}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Caption pill */}
          <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 bg-white rounded-full px-5 py-2 shadow-lg border border-gray-200">
            <button
              onClick={onWatchDemo}
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-blue-600 transition"
              data-testid="hero-tour-expand-btn"
            >
              <Play className="h-4 w-4" />
              <span className="font-medium">Watch full interactive tour</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
