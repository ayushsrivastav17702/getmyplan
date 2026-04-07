import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Brain, ShoppingBag, TrendingUp, Package, BarChart3, Shield, Globe, RefreshCw } from "lucide-react";

const features = [
  { icon: Brain, title: "AI Demand Forecasting", desc: "3-model ensemble (Holt-Winters + Random Forest + Seasonal Decomposition) with 12-month horizon and confidence intervals.", color: "blue", popular: true },
  { icon: ShoppingBag, title: "Buy Plan Generator", desc: "Set revenue targets, select categories, configure channel splits. ML generates optimal buy quantities per SKU.", color: "green", popular: true },
  { icon: TrendingUp, title: "Stock-Out Prediction", desc: "Real-time risk scoring with 4 severity levels. Get alerts before you run out of bestsellers.", color: "orange" },
  { icon: Package, title: "Inventory Optimization", desc: "Days-on-Hand analysis, replenishment planning, inter-store transfer optimization.", color: "purple" },
  { icon: BarChart3, title: "Executive Dashboard", desc: "Health Score, KPI cards, revenue trends, critical alerts. Export PDF or Excel with one click.", color: "red" },
  { icon: Shield, title: "Enterprise Security", desc: "Per-tenant DB isolation, rate limiting, HSTS, CSP headers, NoSQL injection prevention. RBAC with 11 roles.", color: "indigo" },
  { icon: Globe, title: "Multi-Channel Analytics", desc: "Amazon, Flipkart, Myntra, Ajio, Nykaa marketplace support. Channel-split forecasting.", color: "teal" },
  { icon: RefreshCw, title: "Automated Replenishment", desc: "Statistical reorder points with safety stock. 5-tab planner: Reorder, Quantity, Transfer, Run, Orders.", color: "pink" },
];

const cc = {
  blue:   "bg-blue-50 text-blue-600 group-hover:bg-blue-600 group-hover:text-white",
  green:  "bg-green-50 text-green-600 group-hover:bg-green-600 group-hover:text-white",
  orange: "bg-orange-50 text-orange-600 group-hover:bg-orange-600 group-hover:text-white",
  purple: "bg-purple-50 text-purple-600 group-hover:bg-purple-600 group-hover:text-white",
  red:    "bg-red-50 text-red-600 group-hover:bg-red-600 group-hover:text-white",
  indigo: "bg-indigo-50 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white",
  teal:   "bg-teal-50 text-teal-600 group-hover:bg-teal-600 group-hover:text-white",
  pink:   "bg-pink-50 text-pink-600 group-hover:bg-pink-600 group-hover:text-white",
};

export default function Features() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  return (
    <section id="features" data-testid="features-section" className="py-20 bg-gray-50" ref={ref}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900"
          >
            Everything you need to{" "}
            <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">plan smarter</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.1 }}
            className="mt-4 text-base sm:text-lg text-gray-600 max-w-2xl mx-auto"
          >
            AI-powered tools that help fashion retailers optimize their entire supply chain
          </motion.p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f, i) => {
            const Icon = f.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: i * 0.05 }}
                className="group bg-white rounded-xl p-6 shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
              >
                <div className={`w-12 h-12 ${cc[f.color]} rounded-lg flex items-center justify-center mb-4 transition-all duration-300`}>
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{f.desc}</p>
                {f.popular && (
                  <span className="inline-block mt-3 text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
                    Popular
                  </span>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
