import { Link } from "react-router-dom";

const PLANS = [
  {
    name: "Startup", price: "$350", period: "/mo",
    features: ["Up to 10 stores", "3 users included", "Basic analytics", "CSV/Excel upload", "Email support"],
    cta: "Start Free Trial", popular: false,
  },
  {
    name: "Professional", price: "$750", period: "/mo",
    features: ["Up to 50 stores", "10 users included", "AI demand forecasting", "Buy plan generator", "API access", "Priority support"],
    cta: "Start Free Trial", popular: true,
  },
  {
    name: "Business", price: "$1,500", period: "/mo",
    features: ["Up to 200 stores", "25 users included", "Advanced AI features", "Store wedge classification", "Style mix tagging", "SSO/SAML"],
    cta: "Start Free Trial", popular: false,
  },
  {
    name: "Enterprise", price: "Custom", period: "",
    features: ["Unlimited stores", "Unlimited users", "All features", "Dedicated account manager", "SLA guarantee", "On-premise option"],
    cta: "Contact Sales", popular: false,
  },
];

export default function Pricing() {
  return (
    <section id="pricing" className="relative py-20" data-testid="pricing-section">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <h2 className="text-3xl sm:text-4xl font-bold text-center text-white mb-4">Simple, transparent pricing</h2>
        <p className="text-center text-slate-400 mb-12 max-w-xl mx-auto">Start with a 7-day free trial. No credit card required.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              data-testid={`pricing-${plan.name.toLowerCase()}`}
              className={`relative bg-white/[0.04] backdrop-blur-sm rounded-2xl border p-6 flex flex-col ${
                plan.popular
                  ? "border-rose-500/50 shadow-lg shadow-rose-500/10 scale-[1.02]"
                  : "border-indigo-500/10 hover:border-indigo-500/25"
              } transition-all`}
            >
              {plan.popular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-rose-500 to-indigo-500 text-white text-[10px] font-bold uppercase tracking-wider rounded-full shadow-lg">
                  Most Popular
                </span>
              )}
              <h3 className="text-lg font-semibold text-white mb-1">{plan.name}</h3>
              <div className="mb-5">
                <span className="text-3xl font-extrabold text-white">{plan.price}</span>
                {plan.period && <span className="text-sm text-slate-400">{plan.period}</span>}
              </div>
              <ul className="space-y-2.5 mb-6 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-slate-300">
                    <svg className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                    {f}
                  </li>
                ))}
              </ul>
              {plan.cta === "Contact Sales" ? (
                <button className="w-full py-2.5 border border-indigo-500/40 text-indigo-300 rounded-xl text-sm font-semibold hover:bg-indigo-500/10 transition-all">
                  {plan.cta}
                </button>
              ) : (
                <Link to="/signup" className={`block w-full py-2.5 text-center rounded-xl text-sm font-semibold transition-all ${
                  plan.popular
                    ? "bg-gradient-to-r from-indigo-500 to-rose-500 text-white hover:shadow-lg hover:shadow-indigo-500/25"
                    : "border border-indigo-500/40 text-indigo-300 hover:bg-indigo-500/10"
                }`}>
                  {plan.cta}
                </Link>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
