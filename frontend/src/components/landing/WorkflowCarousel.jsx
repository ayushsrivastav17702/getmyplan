import { motion, useInView } from "framer-motion";
import { useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Upload, Brain, BarChart3, ShoppingCart } from "lucide-react";
import { Link } from "react-router-dom";

const SLIDES = [
  {
    step: 1, icon: Upload, title: "Upload Your Data",
    desc: "Drop 5 CSV files. Our 75-rule validation fixes errors automatically. Templates provided. Takes 5 minutes.",
    img: "/dashboard-screenshot.webp",
    alt: "GetMyPlan data upload page with validation",
  },
  {
    step: 2, icon: Brain, title: "AI Analyzes Your Data",
    desc: "3-model ensemble runs in parallel. 92.7% forecast accuracy. Get 12-month predictions with confidence intervals.",
    img: "/dashboard-screenshot.webp",
    alt: "GetMyPlan AI demand forecast with confidence bands",
  },
  {
    step: 3, icon: BarChart3, title: "See Exactly What's Happening",
    desc: "Color-coded DOH heatmap shows optimal, overstock, understock, and stockout at a glance. Drill down to SKU level.",
    img: "/dashboard-screenshot.webp",
    alt: "GetMyPlan DOH heatmap with store inventory health",
  },
  {
    step: 4, icon: ShoppingCart, title: "Take Action",
    desc: "Auto-generated purchase orders. IST recommendations. Know exactly what to order, how much, and where.",
    img: "/dashboard-screenshot.webp",
    alt: "GetMyPlan replenishment planner with purchase orders",
  },
];

export default function WorkflowCarousel() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });
  const [active, setActive] = useState(0);
  const slide = SLIDES[active];
  const Icon = slide.icon;

  const prev = () => setActive((a) => (a - 1 + SLIDES.length) % SLIDES.length);
  const next = () => setActive((a) => (a + 1) % SLIDES.length);

  return (
    <section ref={ref} id="how-it-works" data-testid="workflow-carousel" className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={inView ? { opacity: 1, y: 0 } : {}} className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
            From zero to forecast in <span className="text-blue-600">15 minutes</span>
          </h2>
        </motion.div>

        {/* Step indicators */}
        <div className="flex justify-center gap-3 mb-8">
          {SLIDES.map((s, i) => (
            <button key={i} onClick={() => setActive(i)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                i === active ? "bg-blue-600 text-white shadow-md" : "bg-gray-100 text-gray-500 hover:bg-gray-200"
              }`}>
              <span className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold">{i + 1}</span>
              <span className="hidden sm:inline">{s.title}</span>
            </button>
          ))}
        </div>

        {/* Carousel card */}
        <motion.div key={active} initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.3 }}
          className="bg-gray-50 rounded-2xl border border-gray-200 overflow-hidden">
          {/* Screenshot */}
          <div className="relative bg-gradient-to-b from-slate-800 to-slate-900 p-1">
            <div className="flex items-center gap-1.5 px-3 py-2">
              <div className="w-2.5 h-2.5 rounded-full bg-red-400" />
              <div className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
              <div className="w-2.5 h-2.5 rounded-full bg-green-400" />
              <span className="ml-2 text-xs text-slate-400 font-mono">app.getmyplan.in</span>
            </div>
            <img src={slide.img} alt={slide.alt} className="w-full rounded-b-lg" loading="lazy" />

            {/* Nav arrows */}
            <button onClick={prev} className="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/90 shadow flex items-center justify-center hover:bg-white transition">
              <ChevronLeft className="h-5 w-5 text-gray-700" />
            </button>
            <button onClick={next} className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/90 shadow flex items-center justify-center hover:bg-white transition">
              <ChevronRight className="h-5 w-5 text-gray-700" />
            </button>
          </div>

          {/* Description */}
          <div className="p-6 sm:p-8 flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center shrink-0">
              <Icon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider mb-1">Step {slide.step} of {SLIDES.length}</p>
              <h3 className="text-xl font-bold text-gray-900 mb-2">{slide.title}</h3>
              <p className="text-gray-600 text-sm leading-relaxed">{slide.desc}</p>
            </div>
          </div>
        </motion.div>

        {/* CTA */}
        <div className="mt-10 text-center">
          <Link to="/signup" className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-semibold hover:shadow-xl transition-all hover:scale-105">
            Start Free Trial
            <ChevronRight className="h-5 w-5" />
          </Link>
        </div>
      </div>
    </section>
  );
}
