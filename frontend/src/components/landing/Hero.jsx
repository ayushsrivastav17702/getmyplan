import { ArrowRight, CheckCircle, Play } from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useState } from "react";

function VideoWalkthrough() {
  const [playing, setPlaying] = useState(false);
  const VIDEO_ID = null; // Replace with YouTube/Vimeo ID when ready

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.5 }}
      className="mt-16 max-w-3xl mx-auto"
      data-testid="video-walkthrough"
    >
      <h3 className="text-center text-lg font-semibold text-gray-900 mb-4">
        See it in action
      </h3>

      <div className="relative rounded-xl overflow-hidden shadow-xl border border-gray-200" style={{ paddingBottom: "56.25%" }}>
        {!playing || !VIDEO_ID ? (
          <button
            onClick={() => VIDEO_ID && setPlaying(true)}
            className="absolute inset-0 w-full h-full bg-gradient-to-br from-slate-800 to-slate-900 flex flex-col items-center justify-center gap-3 cursor-pointer group"
            data-testid="video-play-btn"
          >
            {/* Dashboard preview as thumbnail */}
            <img
              src="/dashboard-screenshot.webp"
              alt="Product tour thumbnail"
              className="absolute inset-0 w-full h-full object-cover opacity-40"
            />
            <div className="relative z-10 flex flex-col items-center">
              <div className="w-16 h-16 rounded-full bg-white/90 flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg">
                <Play className="h-7 w-7 text-blue-600 ml-1" />
              </div>
              <span className="mt-3 text-white font-medium text-sm">
                {VIDEO_ID ? "Watch 90-second product tour" : "Video walkthrough coming soon"}
              </span>
              <span className="text-white/50 text-xs mt-1">Upload data &rarr; AI forecast &rarr; Buy plan &rarr; Export</span>
            </div>
          </button>
        ) : (
          <iframe
            src={`https://www.youtube.com/embed/${VIDEO_ID}?autoplay=1&rel=0`}
            className="absolute inset-0 w-full h-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
            allowFullScreen
            title="GetMyPlan 90-second product tour"
          />
        )}
      </div>
    </motion.div>
  );
}

export default function Hero({ onWatchDemo, onRequestDemo }) {

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
            Stop losing revenue to{" "}
            <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              stockouts.
            </span>
          </h1>

          <p className="mt-3 text-lg sm:text-xl font-medium text-gray-800 max-w-2xl mx-auto">
            AI demand planning for fashion retail.
          </p>

          <p className="mt-4 text-base sm:text-lg text-gray-600 max-w-2xl mx-auto">
            GetMyPlan predicts what you'll sell, where, and when &mdash; so you always have
            stock without tying up cash. Trusted by fashion brands worldwide.
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

        {/* Real Dashboard Screenshot */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="mt-16 relative max-w-5xl mx-auto"
        >
          <div className="rounded-xl overflow-hidden shadow-2xl border border-gray-200 bg-gradient-to-b from-slate-800 to-slate-900 p-1">
            {/* Browser chrome */}
            <div className="flex items-center gap-1.5 px-3 py-2">
              <div className="w-3 h-3 rounded-full bg-red-400" />
              <div className="w-3 h-3 rounded-full bg-yellow-400" />
              <div className="w-3 h-3 rounded-full bg-green-400" />
              <span className="ml-2 text-xs text-slate-400 font-mono">app.getmyplan.in/dashboard</span>
            </div>

            <img
              src="/dashboard-screenshot.webp"
              alt="GetMyPlan executive dashboard showing revenue trends, inventory health score, stock-out analysis, and KPI cards"
              className="w-full rounded-b-lg"
              loading="lazy"
              data-testid="hero-dashboard-screenshot"
            />
          </div>

          <p className="text-center text-sm text-gray-500 mt-4">
            Live dashboard from a multi-store fashion brand. Your metrics update in real-time.
          </p>
        </motion.div>

        {/* Video Walkthrough */}
        <VideoWalkthrough />
      </div>
    </section>
  );
}
