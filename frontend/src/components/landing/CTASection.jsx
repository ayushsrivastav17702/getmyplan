import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

export default function CTASection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  return (
    <section data-testid="cta-section" className="py-20 bg-gradient-to-r from-blue-600 to-indigo-600 relative overflow-hidden" ref={ref}>
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-20 -left-20 w-64 h-64 bg-white rounded-full opacity-10 blur-3xl" />
        <div className="absolute -bottom-20 -right-20 w-80 h-80 bg-white rounded-full opacity-10 blur-3xl" />
      </div>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative">
        <motion.h2 initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : {}}
          className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white">
          Ready to stop losing revenue to stockouts?
        </motion.h2>
        <motion.p initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : {}} transition={{ delay: 0.1 }}
          className="mt-4 text-base sm:text-lg text-blue-100">
          Join fashion brands worldwide using GetMyPlan to plan smarter.
        </motion.p>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : {}} transition={{ delay: 0.2 }} className="mt-8">
          <Link
            to="/signup"
            data-testid="cta-signup-btn"
            className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-blue-600 rounded-lg font-semibold text-lg hover:shadow-xl transition-all hover:scale-105"
          >
            Start Your Free 7-Day Trial
            <ArrowRight className="h-5 w-5" />
          </Link>
          <p className="mt-4 text-sm text-blue-100/70">No credit card required &middot; Cancel anytime</p>
        </motion.div>
      </div>
    </section>
  );
}
