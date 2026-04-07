import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Check, X } from "lucide-react";

const rows = [
  { feature: "AI Demand Forecasting",  gmp: true,  xl: false, erp: false },
  { feature: "Buy Plan Generator",     gmp: true,  xl: false, erp: false },
  { feature: "Stock-Out Prediction",   gmp: true,  xl: false, erp: false },
  { feature: "Multi-Channel Support",  gmp: true,  xl: false, erp: false },
  { feature: "Real-time Dashboard",    gmp: true,  xl: false, erp: false },
  { feature: "Team Collaboration",     gmp: true,  xl: false, erp: true },
  { feature: "Data Export (CSV/Excel)",gmp: true,  xl: true,  erp: true },
  { feature: "API Access",             gmp: true,  xl: false, erp: false },
  { feature: "Role-Based Access",      gmp: true,  xl: false, erp: false },
  { feature: "Automated Reports",      gmp: true,  xl: false, erp: false },
];

const Cell = ({ ok }) =>
  ok ? <Check className="h-5 w-5 text-green-500 mx-auto" /> : <X className="h-5 w-5 text-red-300 mx-auto" />;

export default function ComparisonTable() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  return (
    <section data-testid="comparison-section" className="py-20 bg-gray-50" ref={ref}>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900">Why choose GetMyPlan?</h2>
          <p className="mt-4 text-base sm:text-lg text-gray-600">
            Stop juggling spreadsheets. Get enterprise-grade AI at a fraction of the cost.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          className="bg-white rounded-2xl shadow-lg overflow-hidden"
        >
          <div className="overflow-x-auto">
            <table className="w-full min-w-[500px]">
              <thead>
                <tr className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
                  <th className="px-6 py-4 text-left text-sm font-semibold">Feature</th>
                  <th className="px-4 py-4 text-center text-sm font-semibold">GetMyPlan</th>
                  <th className="px-4 py-4 text-center text-sm font-semibold">Excel / Sheets</th>
                  <th className="px-4 py-4 text-center text-sm font-semibold">Traditional ERP</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className="border-t border-gray-100 hover:bg-gray-50 transition">
                    <td className="px-6 py-3.5 text-sm text-gray-900 font-medium">{r.feature}</td>
                    <td className="px-4 py-3.5 text-center"><Cell ok={r.gmp} /></td>
                    <td className="px-4 py-3.5 text-center"><Cell ok={r.xl} /></td>
                    <td className="px-4 py-3.5 text-center"><Cell ok={r.erp} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
