import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Clock, TrendingDown, HelpCircle, Package } from "lucide-react";

const PAINS = [
  { icon: Clock, label: "Excel Hell", stat: "14 hours/week", desc: "in spreadsheets doing manual demand planning", color: "text-red-500 bg-red-50" },
  { icon: TrendingDown, label: "Stockouts", stat: "$50K-100K/mo", desc: "lost to empty shelves and missed sales", color: "text-orange-500 bg-orange-50" },
  { icon: HelpCircle, label: "Guesswork", stat: '"We think..."', desc: 'ordering based on gut feel, not data', color: "text-amber-500 bg-amber-50" },
  { icon: Package, label: "Dead Stock", stat: "30%", desc: "of inventory never sells at full price", color: "text-rose-500 bg-rose-50" },
];

const RESULTS = [
  { stat: "41%", label: "Stockouts reduced" },
  { stat: "32%", label: "Dead stock reduced" },
  { stat: "14hr → 2.5hr", label: "Planner time saved" },
];

export default function ProblemAgitation() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  return (
    <section ref={ref} data-testid="problem-section" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={inView ? { opacity: 1, y: 0 } : {}} className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
            This is what inventory planning looks like <span className="text-red-500">right now</span>
          </h2>
        </motion.div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {PAINS.map((p, i) => {
            const Icon = p.icon;
            return (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ delay: i * 0.1 }}
                className="rounded-xl border border-gray-100 p-6 hover:shadow-lg transition-shadow">
                <div className={`w-11 h-11 rounded-lg ${p.color} flex items-center justify-center mb-4`}>
                  <Icon className="h-5 w-5" />
                </div>
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-1">{p.label}</p>
                <p className="text-2xl font-bold text-gray-900 mb-1">{p.stat}</p>
                <p className="text-sm text-gray-500">{p.desc}</p>
              </motion.div>
            );
          })}
        </div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={inView ? { opacity: 1, y: 0 } : {}} transition={{ delay: 0.4 }}
          className="rounded-2xl bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 p-8 md:p-10">
          <p className="text-center text-sm font-semibold uppercase tracking-wider text-emerald-600 mb-6">
            Meanwhile, brands using AI demand planning
          </p>
          <div className="grid sm:grid-cols-3 gap-8">
            {RESULTS.map((r, i) => (
              <div key={i} className="text-center">
                <p className="text-3xl sm:text-4xl font-bold text-emerald-700">{r.stat}</p>
                <p className="text-sm text-emerald-600 mt-1">{r.label}</p>
              </div>
            ))}
          </div>
          <p className="text-center text-xs text-emerald-500 mt-6">*Based on actual GetMyPlan beta results</p>
        </motion.div>
      </div>
    </section>
  );
}
