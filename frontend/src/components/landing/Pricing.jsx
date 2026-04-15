import { useState, useRef } from "react";
import { motion, useInView } from "framer-motion";
import { Check, Zap } from "lucide-react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import ContactModal from "./ContactModal";

const PRICES = {
  INR: {
    starter:     { monthly: 30000, quarterly: 81000,  yearly: 288000 },
    professional:{ monthly: 50000, quarterly: 135000, yearly: 480000 },
    enterprise:  { monthly: 100000, quarterly: 270000, yearly: 960000 },
  },
  USD: {
    starter:     { monthly: 350,  quarterly: 945,   yearly: 3360 },
    professional:{ monthly: 600,  quarterly: 1620,  yearly: 5760 },
    enterprise:  { monthly: 1200, quarterly: 3240,  yearly: 11520 },
  },
};

const fmt = (val, currency) => {
  if (currency === "INR") return `₹${val.toLocaleString("en-IN")}`;
  return `$${val.toLocaleString("en-US")}`;
};

const plans = [
  {
    key: "starter",
    name: "Starter",
    desc: "Perfect for growing D2C brands",
    features: ["Up to 10 stores", "3 users included", "Basic analytics", "CSV/Excel upload", "Email support", "7-day free trial"],
    cta: "Start Free Trial",
    popular: false,
  },
  {
    key: "professional",
    name: "Professional",
    desc: "For multi-channel retailers",
    features: ["Up to 50 stores", "10 users included", "AI demand forecasting", "Buy plan generator", "SFTP integration", "Priority support", "API access", "Multi-channel sync"],
    cta: "Start Free Trial",
    popular: true,
  },
  {
    key: "enterprise",
    name: "Enterprise",
    desc: "For large retail operations",
    features: ["Unlimited stores", "Unlimited users", "Dedicated account manager", "Custom integrations", "SLA guarantee", "SSO / SAML", "On-premise option", "24/7 support"],
    cta: "Contact Sales",
    popular: false,
  },
];

const BILLING_OPTIONS = [
  { key: "monthly",   label: "Monthly",   period: "/mo",  discount: null },
  { key: "quarterly", label: "Quarterly", period: "/qtr", discount: "10% off" },
  { key: "yearly",    label: "Yearly",    period: "/yr",  discount: "20% off" },
];

export default function Pricing() {
  const [billing, setBilling] = useState("monthly");
  const [currency, setCurrency] = useState("USD");
  const [showContact, setShowContact] = useState(false);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  const activeBilling = BILLING_OPTIONS.find(b => b.key === billing);

  return (
    <>
    <Helmet>
      <script type="application/ld+json">{JSON.stringify([
        {"@context":"https://schema.org","@type":"Product","name":"GetMyPlan Starter","description":"AI demand planning for up to 10 stores","offers":{"@type":"Offer","price":"29000","priceCurrency":"INR","priceValidUntil":"2026-12-31","url":"https://getmyplan.in/pricing"}},
        {"@context":"https://schema.org","@type":"Product","name":"GetMyPlan Professional","description":"AI demand planning for up to 50 stores with AI forecasting and API access","offers":{"@type":"Offer","price":"50000","priceCurrency":"INR","priceValidUntil":"2026-12-31","url":"https://getmyplan.in/pricing"}}
      ])}</script>
    </Helmet>
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

          {/* AEO: TL;DR for pricing */}
          <p className="mt-3 text-sm text-gray-500 max-w-xl mx-auto">
            <strong>TL;DR:</strong> Starter ₹29K/mo (10 stores). Pro ₹50K/mo (50 stores + AI forecasting). Enterprise custom. 7-day free trial included. Annual plans save 20%.
          </p>

          {/* Currency toggle */}
          <div className="mt-6 inline-flex items-center gap-1 p-1 bg-gray-100 rounded-full">
            <button
              onClick={() => setCurrency("INR")}
              data-testid="currency-inr"
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition ${currency === "INR" ? "bg-white shadow-sm text-gray-900" : "text-gray-500"}`}
            >
              ₹ INR
            </button>
            <button
              onClick={() => setCurrency("USD")}
              data-testid="currency-usd"
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition ${currency === "USD" ? "bg-white shadow-sm text-gray-900" : "text-gray-500"}`}
            >
              $ USD
            </button>
          </div>

          {/* Billing toggle */}
          <div className="mt-3 inline-flex items-center gap-1 p-1 bg-gray-100 rounded-full">
            {BILLING_OPTIONS.map(opt => (
              <button
                key={opt.key}
                onClick={() => setBilling(opt.key)}
                data-testid={`billing-${opt.key}`}
                className={`px-4 py-2 rounded-full text-sm font-medium transition ${billing === opt.key ? "bg-white shadow-sm text-gray-900" : "text-gray-500"}`}
              >
                {opt.label}
                {opt.discount && (
                  <span className="text-green-600 text-xs ml-1">{opt.discount}</span>
                )}
              </button>
            ))}
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 items-start">
          {plans.map((plan, i) => {
            const price = PRICES[currency][plan.key][billing];
            const monthlyBase = PRICES[currency][plan.key].monthly;
            const isCustom = plan.key === "enterprise" && false; // enterprise now has pricing
            const taxNote = currency === "INR" ? "+ GST" : "+ tax";

            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: i * 0.1 }}
                data-testid={`pricing-card-${plan.key}`}
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
                    {fmt(price, currency)}
                  </span>
                  <span className={plan.popular ? "text-white/70" : "text-gray-500"}>
                    {activeBilling.period}
                  </span>
                </div>

                {/* Tax note */}
                <p className={`text-xs mt-1 ${plan.popular ? "text-white/50" : "text-gray-400"}`}>
                  {taxNote}
                </p>

                {/* Savings note for quarterly/yearly */}
                {billing !== "monthly" && (
                  <p className={`text-xs mt-1 font-medium ${plan.popular ? "text-green-300" : "text-green-600"}`}>
                    Save {fmt(
                      billing === "quarterly"
                        ? (monthlyBase * 3) - price
                        : (monthlyBase * 12) - price,
                      currency
                    )}{billing === "quarterly" ? " per quarter" : " per year"}
                  </p>
                )}

                <p className={`mt-2 text-sm ${plan.popular ? "text-white/70" : "text-gray-500"}`}>{plan.desc}</p>

                <ul className="mt-6 space-y-3">
                  {plan.features.map((f, fi) => (
                    <li key={fi} className="flex items-center gap-2 text-sm">
                      <Check size={15} className={plan.popular ? "text-white/80" : "text-green-500"} />
                      <span className={plan.popular ? "text-white/90" : "text-gray-600"}>{f}</span>
                    </li>
                  ))}
                </ul>

                {plan.key === "enterprise" ? (
                  <button
                    onClick={() => setShowContact(true)}
                    data-testid={`pricing-cta-${plan.key}`}
                    className="mt-8 w-full text-center py-3 rounded-lg font-semibold transition bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:shadow-lg"
                  >
                    {plan.cta}
                  </button>
                ) : (
                  <Link
                    to="/signup"
                    data-testid={`pricing-cta-${plan.key}`}
                    className={`mt-8 block text-center py-3 rounded-lg font-semibold transition ${
                      plan.popular
                        ? "bg-white text-blue-600 hover:bg-gray-100"
                        : "bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:shadow-lg"
                    }`}
                  >
                    {plan.cta}
                  </Link>
                )}

                {plan.key !== "enterprise" && (
                  <p className={`text-center text-xs mt-3 ${plan.popular ? "text-white/50" : "text-gray-400"}`}>
                    No credit card required
                  </p>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
    <ContactModal isOpen={showContact} onClose={() => setShowContact(false)} />
    </>
  );
}
