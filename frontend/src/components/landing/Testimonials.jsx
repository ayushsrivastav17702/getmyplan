import { useState, useRef } from "react";
import { motion, useInView, AnimatePresence } from "framer-motion";
import { Star, ChevronLeft, ChevronRight, Quote } from "lucide-react";

const testimonials = [
  { name: "Rahul Sharma", role: "CEO, FashionHub (Beta Customer)", content: "GetMyPlan reduced our stockouts by 40% and increased revenue by 25% in just 3 months. The AI forecasts are incredibly accurate and the team is amazing to work with.", rating: 5 },
  { name: "Priya Patel", role: "Head of Merchandising, StyleStore (Beta Customer)", content: "The buy plan generator saves us 2 days every week. We went from Excel guesswork to ML-powered buy plans overnight. Best decision we made for our inventory.", rating: 5 },
  { name: "Amit Kumar", role: "Operations Director, TrendyWear (Beta Customer)", content: "Best investment for our supply chain. ROI was evident within the first month. The explainable AI helps us understand exactly why forecasts are made.", rating: 5 },
  { name: "Neha Gupta", role: "Merchandising Manager, UrbanMatch (Beta Customer)", content: "The multi-channel analytics helped us optimize inventory across Amazon, Shopify, and our own website. Stockouts reduced by 60% in first quarter.", rating: 5 },
];

export default function Testimonials() {
  const [cur, setCur] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  const next = () => setCur((p) => (p + 1) % testimonials.length);
  const prev = () => setCur((p) => (p - 1 + testimonials.length) % testimonials.length);

  return (
    <section id="customers" data-testid="testimonials-section" className="py-20 bg-gradient-to-br from-gray-900 to-gray-800 text-white" ref={ref}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <motion.h2 initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : {}} className="text-3xl sm:text-4xl lg:text-5xl font-bold">
            Trusted by fashion retailers
          </motion.h2>
          <motion.p initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : {}} transition={{ delay: 0.1 }} className="mt-4 text-base sm:text-lg text-gray-300">
          Join fashion brands worldwide using GetMyPlan to plan smarter.
        </motion.p>
        </div>

        <div className="relative max-w-3xl mx-auto">
          <button onClick={prev} data-testid="testimonial-prev" className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-2 lg:-translate-x-14 z-10 p-2 rounded-full bg-white/10 hover:bg-white/20 transition">
            <ChevronLeft className="h-6 w-6" />
          </button>
          <button onClick={next} data-testid="testimonial-next" className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-2 lg:translate-x-14 z-10 p-2 rounded-full bg-white/10 hover:bg-white/20 transition">
            <ChevronRight className="h-6 w-6" />
          </button>

          <div className="overflow-hidden">
            <AnimatePresence mode="wait">
              <motion.div
                key={cur}
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ duration: 0.3 }}
                className="text-center px-8 sm:px-12"
              >
                <Quote className="h-10 w-10 text-blue-400 mx-auto mb-6 opacity-50" />
                <p className="text-lg sm:text-xl lg:text-2xl leading-relaxed mb-8">
                  "{testimonials[cur].content}"
                </p>
                <div className="flex justify-center gap-1 mb-4">
                  {[...Array(testimonials[cur].rating)].map((_, i) => (
                    <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <div className="flex items-center justify-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center text-white font-bold text-lg border-2 border-blue-400">
                    {testimonials[cur].name.split(" ").map(n => n[0]).join("")}
                  </div>
                  <div className="text-left">
                    <p className="font-semibold">{testimonials[cur].name}</p>
                    <p className="text-sm text-gray-300">{testimonials[cur].role}</p>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>

          <div className="flex justify-center gap-2 mt-8">
            {testimonials.map((_, i) => (
              <button key={i} onClick={() => setCur(i)} data-testid={`testimonial-dot-${i}`}
                className={`h-2 rounded-full transition-all ${cur === i ? "bg-blue-400 w-6" : "bg-white/30 w-2"}`}
              />
            ))}
          </div>
        </div>

        {/* Summary stats */}
        <div className="mt-12 pt-8 border-t border-white/10">
          <div className="flex flex-wrap justify-center gap-8 sm:gap-16">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400">92.7%</div>
              <div className="text-sm text-gray-300">Forecast Accuracy*</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400">41%</div>
              <div className="text-sm text-gray-300">Stockout Reduction**</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400">4.9<span className="text-yellow-400 text-xl ml-0.5">&#9733;</span></div>
              <div className="text-sm text-gray-300">Beta User Rating</div>
            </div>
          </div>
          <p className="text-center text-xs text-gray-500 mt-4">*Backtested on 50+ datasets | **Based on beta results</p>
        </div>
      </div>
    </section>
  );
}
