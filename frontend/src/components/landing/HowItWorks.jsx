import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Upload, Brain, ShoppingCart, LineChart } from "lucide-react";

const steps = [
  { icon: Upload, title: "Upload Data", desc: "Upload 7 CSV files — Style Master, Sales, Inventory, Stores. Auto-validation runs instantly.", color: "bg-blue-100 text-blue-600 group-hover:bg-blue-600 group-hover:text-white" },
  { icon: Brain, title: "AI Analyzes", desc: "3 ML models process your data: gap analysis, stock-out detection, demand forecasting.", color: "bg-indigo-100 text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white" },
  { icon: ShoppingCart, title: "Get Buy Plan", desc: "Set revenue target, let AI calculate what to buy, quantities, and channel splits.", color: "bg-purple-100 text-purple-600 group-hover:bg-purple-600 group-hover:text-white" },
  { icon: LineChart, title: "Execute & Track", desc: "Export Excel workbook, share with procurement. Monitor via live Executive Dashboard.", color: "bg-green-100 text-green-600 group-hover:bg-green-600 group-hover:text-white" },
];

export default function HowItWorks() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  return (
    <section id="how-it-works" data-testid="how-it-works-section" className="py-20 bg-white" ref={ref}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900"
          >
            From zero to insights<br className="hidden sm:block" />
            in <span className="text-blue-600">15 minutes</span>
          </motion.h2>
        </div>

        <div className="relative">
          <div className="absolute top-8 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-200 via-indigo-200 to-green-200 hidden lg:block" />
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 relative">
            {steps.map((step, i) => {
              const Icon = step.icon;
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={isInView ? { opacity: 1, y: 0 } : {}}
                  transition={{ delay: i * 0.12 }}
                  className="relative z-10 text-center group"
                >
                  <div className="flex justify-center mb-4">
                    <div className={`w-16 h-16 ${step.color} rounded-2xl flex items-center justify-center transition-all duration-300 group-hover:scale-110`}>
                      <Icon className="h-8 w-8" />
                    </div>
                  </div>
                  <div className="text-2xl font-bold text-gray-300 mb-2">0{i + 1}</div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{step.title}</h3>
                  <p className="text-gray-500 text-sm">{step.desc}</p>
                </motion.div>
              );
            })}
          </div>
        </div>

        <div className="mt-12 text-center">
          <div className="inline-flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-gray-500">
            <span className="flex items-center gap-1.5"><span className="w-4 h-4 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-xs font-bold">&#10003;</span> No technical skills required</span>
            <span className="hidden sm:inline w-1 h-1 bg-gray-300 rounded-full" />
            <span className="flex items-center gap-1.5"><span className="w-4 h-4 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-xs font-bold">&#10003;</span> Works with existing ERP</span>
            <span className="hidden sm:inline w-1 h-1 bg-gray-300 rounded-full" />
            <span className="flex items-center gap-1.5"><span className="w-4 h-4 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-xs font-bold">&#10003;</span> Free onboarding support</span>
          </div>
        </div>
      </div>
    </section>
  );
}
