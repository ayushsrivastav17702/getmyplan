import { useState, useRef } from "react";
import { motion, useInView } from "framer-motion";
import { ChevronDown } from "lucide-react";

const faqs = [
  { q: "How accurate is GetMyPlan's AI forecasting?", a: "Our 3-model ensemble achieves 91% accuracy on average across all categories. Every forecast includes confidence intervals so you understand the prediction reliability. Models used: Holt-Winters, Random Forest, and Seasonal Decomposition." },
  { q: "What data do I need to get started?", a: "You need 7 CSV files: Style Master, SKU-EAN Master, Store Master, Warehouse Master, Daily Sales (ideally 12+ months), Store Inventory, and Warehouse Inventory. Our upload wizard validates data automatically." },
  { q: "How long does it take to see results?", a: "Most customers see their first AI forecast within 15 minutes of uploading data. Full insights, stock-out alerts, and buy plans are available immediately after data processing completes." },
  { q: "Can I integrate with my existing ERP?", a: "Yes! GetMyPlan supports SFTP integration for automated data ingestion from any ERP system. We also provide a REST API for custom integrations. Our team provides free onboarding support." },
  { q: "Is my data secure?", a: "Absolutely. We use per-tenant database isolation (each customer gets their own MongoDB database), encryption at rest and in transit, enterprise security headers (HSTS, CSP, X-Frame-Options), rate limiting, and NoSQL injection prevention." },
  { q: "What happens after the 7-day trial?", a: "You choose to subscribe to a Starter or Professional plan, or contact us for Enterprise pricing. No automatic charges after trial ends. Your data is preserved for 30 days after trial expiry." },
];

export default function FAQ() {
  const [openIdx, setOpenIdx] = useState(null);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  return (
    <section id="faq" data-testid="faq-section" className="py-20 bg-white" ref={ref}>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <motion.h2 initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : {}}
            className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900">
            Frequently asked questions
          </motion.h2>
          <motion.p initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : {}} transition={{ delay: 0.1 }}
            className="mt-4 text-base sm:text-lg text-gray-600">
            Everything you need to know about GetMyPlan
          </motion.p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: i * 0.05 }}
              className="border border-gray-200 rounded-xl overflow-hidden"
            >
              <button
                onClick={() => setOpenIdx(openIdx === i ? null : i)}
                data-testid={`faq-toggle-${i}`}
                className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-gray-50 transition"
              >
                <span className="font-semibold text-gray-900 pr-4">{faq.q}</span>
                <ChevronDown className={`h-5 w-5 text-gray-500 transition-transform duration-300 flex-shrink-0 ${openIdx === i ? "rotate-180" : ""}`} />
              </button>
              {openIdx === i && (
                <div className="px-6 pb-4 text-gray-600 text-sm leading-relaxed border-t border-gray-100 pt-4">
                  {faq.a}
                </div>
              )}
            </motion.div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <p className="text-gray-600">
            Still have questions?{" "}
            <a href="mailto:info@getmyplan.in" className="text-blue-600 hover:text-blue-700 font-medium">
              Contact our team
            </a>
          </p>
        </div>
      </div>
    </section>
  );
}
