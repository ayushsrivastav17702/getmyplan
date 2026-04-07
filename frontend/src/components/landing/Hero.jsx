import { ArrowRight, CheckCircle, Play } from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";

export default function Hero() {
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
            <a
              href="#how-it-works"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50 transition"
              data-testid="hero-demo-btn"
            >
              <Play className="h-5 w-5" />
              Watch Demo
            </a>
          </div>

          <div className="mt-6 flex flex-wrap justify-center gap-6 text-sm text-gray-500">
            <span className="flex items-center gap-2"><CheckCircle className="h-5 w-5 text-green-500" /> No credit card required</span>
            <span className="flex items-center gap-2"><CheckCircle className="h-5 w-5 text-green-500" /> 7-day free trial</span>
            <span className="flex items-center gap-2"><CheckCircle className="h-5 w-5 text-green-500" /> Cancel anytime</span>
          </div>
        </motion.div>

        {/* Dashboard preview */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="mt-16 relative"
        >
          <div className="rounded-xl overflow-hidden shadow-2xl border border-gray-200 bg-gradient-to-b from-slate-800 to-slate-900 p-1">
            <div className="flex items-center gap-1.5 px-3 py-2">
              <div className="w-3 h-3 rounded-full bg-red-400" />
              <div className="w-3 h-3 rounded-full bg-yellow-400" />
              <div className="w-3 h-3 rounded-full bg-green-400" />
              <span className="ml-2 text-xs text-slate-400">app.getmyplan.in/dashboard</span>
            </div>
            <img
              src="https://images.unsplash.com/photo-1569320378109-30221689a282?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1OTV8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwcmV0YWlsJTIwYW5hbHl0aWNzJTIwZGFzaGJvYXJkfGVufDB8fHx8MTc3NTU2MjY3N3ww&ixlib=rb-4.1.0&q=85"
              alt="GetMyPlan Executive Dashboard"
              className="w-full rounded-b-lg object-cover"
              style={{ maxHeight: 480 }}
            />
          </div>
          <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 bg-white rounded-full px-6 py-2 shadow-lg border border-gray-200">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="flex -space-x-2">
                <div className="w-6 h-6 rounded-full bg-blue-500 border-2 border-white" />
                <div className="w-6 h-6 rounded-full bg-indigo-500 border-2 border-white" />
                <div className="w-6 h-6 rounded-full bg-purple-500 border-2 border-white" />
              </div>
              <span>Trusted by 500+ fashion brands</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
