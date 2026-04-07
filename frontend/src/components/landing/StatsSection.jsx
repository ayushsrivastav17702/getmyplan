import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { TrendingUp, Package, Clock, Brain } from "lucide-react";

const stats = [
  { icon: TrendingUp, value: "91%", label: "Forecast Accuracy", desc: "3-model ensemble ML" },
  { icon: Package, value: "33", label: "Analytics Features", desc: "End-to-end planning" },
  { icon: Clock, value: "15 min", label: "Time to Insight", desc: "From data upload" },
  { icon: Brain, value: "3", label: "ML Models", desc: "Holt-Winters + RF + SD" },
];

export default function StatsSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  return (
    <section data-testid="stats-section" className="py-16 bg-white" ref={ref}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s, i) => {
            const Icon = s.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                className="text-center"
              >
                <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-50 rounded-xl mb-4 mx-auto">
                  <Icon className="h-6 w-6 text-blue-600" />
                </div>
                <div className="text-3xl sm:text-4xl font-bold text-gray-900">{s.value}</div>
                <div className="text-sm font-semibold text-gray-700 mt-1">{s.label}</div>
                <div className="text-xs text-gray-400 mt-1">{s.desc}</div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
