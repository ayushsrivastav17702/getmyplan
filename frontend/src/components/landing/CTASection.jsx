import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { ArrowRight, CheckCircle } from "lucide-react";
import { Link } from "react-router-dom";

export default function CTASection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  return (
    <section data-testid="cta-section" className="py-20 bg-[#0B2545] relative overflow-hidden" ref={ref}>
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-20 -left-20 w-64 h-64 bg-blue-400 rounded-full opacity-10 blur-3xl" />
        <div className="absolute -bottom-20 -right-20 w-80 h-80 bg-indigo-400 rounded-full opacity-10 blur-3xl" />
      </div>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative">
        <motion.h2 initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : {}}
          className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white">
          Stop Guessing. Start Knowing.
        </motion.h2>
        <motion.p initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : {}} transition={{ delay: 0.1 }}
          className="mt-4 text-base sm:text-lg text-blue-200 max-w-2xl mx-auto">
          Join fashion brands using AI to reduce stockouts by 41% and cut dead stock by 32%.
        </motion.p>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : {}} transition={{ delay: 0.2 }}
          className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/signup" data-testid="cta-signup-btn"
            className="group inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-[#0B2545] rounded-lg font-semibold text-lg hover:shadow-xl transition-all hover:scale-105">
            Start 7-Day Free Trial
            <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition" />
          </Link>
          <Link to="/login"
            className="inline-flex items-center justify-center gap-2 px-8 py-4 border-2 border-white/30 text-white rounded-lg font-semibold text-lg hover:bg-white/10 transition">
            Explore Live Demo
          </Link>
        </motion.div>
        <motion.div initial={{ opacity: 0 }} animate={isInView ? { opacity: 1 } : {}} transition={{ delay: 0.35 }}
          className="mt-6 flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-blue-200/70">
          <span className="flex items-center gap-1.5"><CheckCircle className="h-4 w-4 text-emerald-400" /> No credit card</span>
          <span className="flex items-center gap-1.5"><CheckCircle className="h-4 w-4 text-emerald-400" /> 15-minute setup</span>
          <span className="flex items-center gap-1.5"><CheckCircle className="h-4 w-4 text-emerald-400" /> Cancel anytime</span>
        </motion.div>
      </div>
    </section>
  );
}
