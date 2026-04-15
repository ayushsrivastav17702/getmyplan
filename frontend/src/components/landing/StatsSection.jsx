import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { TrendingUp, Shield, Clock, Star } from "lucide-react";

const stats = [
  { icon: TrendingUp, value: "92.7%", label: "Forecast Accuracy", sub: "*Backtested on 50+ datasets" },
  { icon: Shield, value: "41%", label: "Stockout Reduction", sub: "**Based on beta results" },
  { icon: Clock, value: "32%", label: "Dead Stock Reduction", sub: "**Based on beta results" },
  { icon: Star, value: "4.9", label: "User Rating", sub: "Out of 5 stars" },
];

export default function StatsSection() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  return (
    <section ref={ref} data-testid="stats-section" className="py-16 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((s, i) => {
            const Icon = s.icon;
            return (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ delay: i * 0.1 }}
                className="text-center">
                <div className="flex justify-center mb-3">
                  <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
                    <Icon className="h-6 w-6" />
                  </div>
                </div>
                <p className="text-3xl sm:text-4xl font-bold text-gray-900">
                  {s.value}{s.label === "User Rating" && <span className="text-yellow-500 text-xl ml-1">&#9733;</span>}
                </p>
                <p className="text-sm font-medium text-gray-700 mt-1">{s.label}</p>
                <p className="text-xs text-gray-400 mt-0.5">{s.sub}</p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
