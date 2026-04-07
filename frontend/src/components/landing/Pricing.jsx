import { useState, useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Check, Zap } from "lucide-react";
import { Link } from "react-router-dom";
import ContactModal from "./ContactModal";

const plans = [
  {
    name: "Starter", priceM: "15,000", priceY: "1,50,000", periodM: "/month", periodY: "/year",
    desc: "Perfect for growing D2C brands",
    features: ["Up to 10 stores", "3 users included", "Basic analytics", "CSV/Excel upload", "Email support", "7-day free trial"],
    cta: "Start Free Trial", popular: false
  },
  {
    name: "Professional", priceM: "25,000", priceY: "2,50,000", periodM: "/month", periodY: "/year",
    desc: "For multi-channel retailers",
    features: ["Up to 50 stores", "10 users included", "AI demand forecasting", "Buy plan generator", "SFTP integration", "Priority support", "API access", "Multi-channel sync"],
    cta: "Start Free Trial", popular: true
  },
  {
    name: "Enterprise", priceM: "Custom", priceY: "Custom", periodM: "", periodY: "",
    desc: "For large retail operations",
    features: ["Unlimited stores", "Unlimited users", "Dedicated account manager", "Custom integrations", "SLA guarantee", "SSO / SAML", "On-premise option", "24/7 support"],
    cta: "Contact Sales", popular: false
  },
];

export default function Pricing() {
  const [billing, setBilling] = useState("monthly");
  const [showContact, setShowContact] = useState(false);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  return (
    <>
    <section id="pricing" data-testid="pricing-section" className="py-20 bg-white" ref={ref}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900"
          >
            Simple, transparent pricing
          </motion.h2>
          <motion.p initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : {}} transition={{ delay: 0.1 }}
            className="mt-4 text-base sm:text-lg text-gray-600">
            Start free. Upgrade when you need more.
          </motion.p>

          {/* Billing toggle */}
          <div className="mt-8 inline-flex items-center gap-1 p-1 bg-gray-100 rounded-full">
            <button
              onClick={() => setBilling("monthly")}
              data-testid="billing-monthly"
              className={`px-4 py-2 rounded-full text-sm font-medium transition ${billing === "monthly" ? "bg-white shadow-sm text-gray-900" : "text-gray-500"}`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBilling("yearly")}
              data-testid="billing-yearly"
              className={`px-4 py-2 rounded-full text-sm font-medium transition ${billing === "yearly" ? "bg-white shadow-sm text-gray-900" : "text-gray-500"}`}
            >
              Yearly <span className="text-green-600 text-xs ml-1">Save 15%</span>
            </button>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 items-start">
          {plans.map((plan, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: i * 0.1 }}
              className={`relative rounded-2xl p-8 transition-all duration-300 ${
                plan.popular
                  ? "bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-2xl scale-105"
                  : "bg-gray-50 border border-gray-200 hover:shadow-xl"
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="inline-flex items-center gap-1 bg-gradient-to-r from-orange-500 to-pink-500 text-white px-4 py-1 rounded-full text-sm font-medium shadow-lg">
                    <Zap className="h-3 w-3" /> Most Popular
                  </span>
                </div>
              )}

              <h3 className="text-2xl font-bold">{plan.name}</h3>
              <div className="mt-4">
                <span className={`text-4xl font-bold ${plan.popular ? "text-white" : "text-gray-900"}`}>
                  {billing === "monthly" ? (plan.priceM !== "Custom" ? `₹${plan.priceM}` : "Custom") : (plan.priceY !== "Custom" ? `₹${plan.priceY}` : "Custom")}
                </span>
                <span className={plan.popular ? "text-white/70" : "text-gray-500"}>
                  {billing === "monthly" ? plan.periodM : plan.periodY}
                </span>
              </div>
              <p className={`mt-2 text-sm ${plan.popular ? "text-white/70" : "text-gray-500"}`}>{plan.desc}</p>

              <ul className="mt-6 space-y-3">
                {plan.features.map((f, fi) => (
                  <li key={fi} className="flex items-center gap-2 text-sm">
                    <Check size={15} className={plan.popular ? "text-white/80" : "text-green-500"} />
                    <span className={plan.popular ? "text-white/90" : "text-gray-600"}>{f}</span>
                  </li>
                ))}
              </ul>

              {plan.name === "Enterprise" ? (
                <button
                  onClick={() => setShowContact(true)}
                  data-testid={`pricing-cta-${plan.name.toLowerCase()}`}
                  className="mt-8 w-full text-center py-3 rounded-lg font-semibold transition bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:shadow-lg"
                >
                  {plan.cta}
                </button>
              ) : (
                <Link
                  to="/signup"
                  data-testid={`pricing-cta-${plan.name.toLowerCase()}`}
                  className={`mt-8 block text-center py-3 rounded-lg font-semibold transition ${
                    plan.popular
                      ? "bg-white text-blue-600 hover:bg-gray-100"
                      : "bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:shadow-lg"
                  }`}
                >
                  {plan.cta}
                </Link>
              )}

              {plan.priceM !== "Custom" && (
                <p className={`text-center text-xs mt-3 ${plan.popular ? "text-white/50" : "text-gray-400"}`}>
                  No credit card required
                </p>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
    <ContactModal isOpen={showContact} onClose={() => setShowContact(false)} />
    </>
  );
}
