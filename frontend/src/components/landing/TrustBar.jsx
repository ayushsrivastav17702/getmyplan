import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Target, Zap, Shield, Globe } from "lucide-react";

const badges = [
  { icon: Target, stat: "92.7%", label: "Forecast Accuracy", sub: "3-model ensemble ML" },
  { icon: Zap, stat: "15 min", label: "Setup Time", sub: "Upload to insight" },
  { icon: Shield, stat: "Enterprise", label: "Security", sub: "Per-tenant isolation" },
  { icon: Globe, stat: "Multi-Channel", label: "Ready", sub: "Amazon, Shopify, D2C" },
];

export default function TrustBar() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  return (
    <section ref={ref} data-testid="trust-bar" className="py-12 bg-white border-y border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-10">
          {badges.map((b, i) => {
            const Icon = b.icon;
            return (
              <motion.div key={i} initial={{ opacity: 0, y: 15 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ delay: i * 0.08 }}
                className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-lg font-bold text-gray-900 leading-tight">{b.stat}</p>
                  <p className="text-xs text-gray-500">{b.label}</p>
                </div>
              </motion.div>
            );
          })}
        </div>
        <p className="text-center text-xs text-gray-400 mt-6">
          *Based on 12-month backtest across 50+ fashion retail datasets globally
        </p>
      </div>
    </section>
  );
}
