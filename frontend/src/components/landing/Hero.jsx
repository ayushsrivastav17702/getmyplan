import { ArrowRight, CheckCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";

export default function Hero({ onWatchDemo, onRequestDemo }) {
  return (
    <section data-testid="hero-section" className="relative pt-28 pb-16 overflow-hidden bg-gradient-to-br from-gray-50 via-white to-blue-50">
      {/* Animated blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-indigo-400 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left — Copy */}
          <motion.div initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6 }}>
            <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-full px-4 py-1.5 mb-6">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
              </span>
              <span className="text-sm text-blue-700 font-medium">AI-Powered Demand Planning</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight">
              Stop Guessing.{" "}
              <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Start Knowing.
              </span>
            </h1>

            <p className="mt-5 text-base sm:text-lg text-gray-600 max-w-lg">
              AI predicts what you'll sell, where, and when &mdash; with <strong>92.7% forecast accuracy</strong>.
              Upload 5 CSV files. Get 12-month forecasts, stockout warnings, and purchase orders in 15 minutes.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row gap-3">
              <Link to="/signup" data-testid="hero-signup-btn"
                className="group inline-flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-semibold hover:shadow-xl transition-all hover:scale-105">
                Start 7-Day Free Trial
                <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition" />
              </Link>
              <button onClick={onRequestDemo} data-testid="hero-demo-btn"
                className="inline-flex items-center justify-center gap-2 px-6 py-3.5 border-2 border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition">
                Watch Demo
              </button>
            </div>

            <div className="mt-5 flex flex-wrap gap-x-5 gap-y-1 text-sm text-gray-500">
              <span className="flex items-center gap-1.5"><CheckCircle className="h-4 w-4 text-green-500" /> No credit card</span>
              <span className="flex items-center gap-1.5"><CheckCircle className="h-4 w-4 text-green-500" /> 15-minute setup</span>
              <span className="flex items-center gap-1.5"><CheckCircle className="h-4 w-4 text-green-500" /> Cancel anytime</span>
            </div>
          </motion.div>

          {/* Right — Dashboard Preview */}
          <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.8, delay: 0.2 }}>
            <div className="rounded-xl overflow-hidden shadow-2xl border border-gray-200 bg-gradient-to-b from-slate-800 to-slate-900 p-1">
              <div className="flex items-center gap-1.5 px-3 py-2">
                <div className="w-2.5 h-2.5 rounded-full bg-red-400" />
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
                <div className="w-2.5 h-2.5 rounded-full bg-green-400" />
                <span className="ml-2 text-xs text-slate-400 font-mono">app.getmyplan.in/dashboard</span>
              </div>
              <img
                src="/dashboard-screenshot.webp"
                alt="GetMyPlan executive dashboard showing revenue trends, inventory health score, stock-out analysis, and KPI cards"
                className="w-full rounded-b-lg"
                loading="eager"
                data-testid="hero-dashboard-screenshot"
              />
            </div>
            <p className="text-center text-xs text-gray-400 mt-3">
              Actual GetMyPlan dashboard from a fashion retailer
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
