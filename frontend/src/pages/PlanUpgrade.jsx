import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../App";
import { useAuth } from "../context/AuthContext";
import {
  Crown, Zap, Building2, Users, HardDrive, Check, X,
  ArrowRight, Loader2, AlertCircle, ChevronUp, Mail
} from "lucide-react";

const PLANS = [
  {
    key: "starter",
    name: "Starter",
    desc: "For growing D2C brands",
    price: { INR: 30000, USD: 350 },
    color: "#64748b",
    icon: Zap,
    features: [
      { label: "Up to 10 stores", included: true },
      { label: "3 users included", included: true },
      { label: "Core analytics", included: true },
      { label: "Gap & stock analysis", included: true },
      { label: "CSV/Excel upload", included: true },
      { label: "Email support", included: true },
      { label: "AI demand forecasting", included: false },
      { label: "Buy plan generator", included: false },
      { label: "Multi-channel analytics", included: false },
      { label: "SFTP integration", included: false },
    ],
  },
  {
    key: "professional",
    name: "Professional",
    desc: "For multi-channel retailers",
    price: { INR: 50000, USD: 600 },
    color: "#0176D3",
    icon: Crown,
    popular: true,
    features: [
      { label: "Up to 50 stores", included: true },
      { label: "10 users included", included: true },
      { label: "All analytics modules", included: true },
      { label: "AI demand forecasting", included: true },
      { label: "Buy plan generator", included: true },
      { label: "Multi-channel analytics", included: true },
      { label: "SFTP integration", included: true },
      { label: "Priority support", included: true },
      { label: "API access", included: true },
      { label: "Custom integrations", included: false },
    ],
  },
  {
    key: "enterprise",
    name: "Enterprise",
    desc: "For large retail operations",
    price: { INR: 100000, USD: 1200 },
    color: "#7c3aed",
    icon: Building2,
    features: [
      { label: "Unlimited stores", included: true },
      { label: "Unlimited users", included: true },
      { label: "All analytics modules", included: true },
      { label: "AI demand forecasting", included: true },
      { label: "Buy plan generator", included: true },
      { label: "Custom integrations", included: true },
      { label: "Dedicated account manager", included: true },
      { label: "SLA guarantee", included: true },
      { label: "SSO / SAML", included: true },
      { label: "24/7 phone support", included: true },
    ],
  },
];

const PLAN_ORDER = ["trial", "starter", "professional", "enterprise"];

const fmt = (val, currency) => {
  if (currency === "INR") return `₹${val.toLocaleString("en-IN")}`;
  return `$${val.toLocaleString("en-US")}`;
};

const PlanUpgrade = () => {
  const { tenantId } = useAuth();
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currency, setCurrency] = useState("INR");
  const [requestSent, setRequestSent] = useState(null);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (!tenantId) return;
    axios.get(`${API}/tenants/${tenantId}/plan-usage`).then(r => {
      setUsage(r.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [tenantId]);

  const handleUpgradeRequest = async (targetPlan) => {
    setSending(true);
    // Simulate upgrade request (in production this would be a Stripe checkout or contact form)
    setTimeout(() => {
      setRequestSent(targetPlan);
      setSending(false);
    }, 800);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 size={24} className="animate-spin text-slate-400" />
      </div>
    );
  }

  const currentPlan = usage?.plan_type || "starter";
  const currentIdx = PLAN_ORDER.indexOf(currentPlan);
  const usageData = usage?.usage || {};
  const limits = usage?.limits || {};
  const trialInfo = usage?.trial_info;

  return (
    <div className="space-y-8" data-testid="plan-upgrade-page">
      {/* Page H1 */}
      <h1 className="text-3xl font-bold tracking-tight text-slate-900">Plan & Billing</h1>

      {/* Current Plan Banner */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6" data-testid="current-plan-banner">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                currentPlan === "trial" ? "bg-amber-100" :
                currentPlan === "starter" ? "bg-slate-100" :
                currentPlan === "professional" ? "bg-blue-100" : "bg-purple-100"
              }`}>
                <Crown size={20} className={
                  currentPlan === "trial" ? "text-amber-600" :
                  currentPlan === "starter" ? "text-slate-600" :
                  currentPlan === "professional" ? "text-blue-600" : "text-purple-600"
                } />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900 capitalize" data-testid="current-plan-name">
                  {currentPlan === "trial" ? "Free Trial" : `${currentPlan} Plan`}
                </h2>
                <p className="text-sm text-slate-500">{usage?.company_name}</p>
              </div>
            </div>
            {trialInfo && (
              <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium ${
                trialInfo.days_remaining <= 2
                  ? "bg-red-50 text-red-700 border border-red-200"
                  : "bg-amber-50 text-amber-700 border border-amber-200"
              }`} data-testid="trial-days-badge">
                <AlertCircle size={14} />
                {trialInfo.days_remaining > 0
                  ? `${trialInfo.days_remaining} days remaining in trial`
                  : "Trial expired — upgrade now"}
              </div>
            )}
          </div>

          {/* Usage Stats */}
          <div className="flex gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-slate-900" data-testid="usage-users">{usageData.active_users || 0}</div>
              <div className="text-xs text-slate-500">Users</div>
              <div className="text-[10px] text-slate-400">of {limits.max_users || "∞"}</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-slate-900" data-testid="usage-stores">{usageData.stores || 0}</div>
              <div className="text-xs text-slate-500">Stores</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-slate-900" data-testid="usage-files">{usageData.uploaded_files || 0}</div>
              <div className="text-xs text-slate-500">Files</div>
            </div>
          </div>
        </div>
      </div>

      {/* Currency Toggle */}
      <div className="flex justify-end">
        <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50">
          {["INR", "USD"].map(c => (
            <button
              key={c}
              onClick={() => setCurrency(c)}
              data-testid={`currency-${c}`}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition ${
                currency === c ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {c === "INR" ? "₹ INR" : "$ USD"}
            </button>
          ))}
        </div>
      </div>

      {/* Plan Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {PLANS.map(plan => {
          const planIdx = PLAN_ORDER.indexOf(plan.key);
          const isCurrent = plan.key === currentPlan;
          const isDowngrade = planIdx <= currentIdx && !isCurrent;
          const isUpgrade = planIdx > currentIdx;
          const Icon = plan.icon;

          return (
            <div
              key={plan.key}
              data-testid={`plan-card-${plan.key}`}
              className={`relative bg-white rounded-xl border-2 transition-all ${
                isCurrent
                  ? "border-[#0176D3] shadow-lg shadow-blue-100"
                  : plan.popular
                  ? "border-blue-200 shadow-md"
                  : "border-slate-200 shadow-sm"
              }`}
            >
              {plan.popular && !isCurrent && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-[#0176D3] text-white text-xs font-semibold rounded-full">
                  Most Popular
                </div>
              )}
              {isCurrent && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-green-500 text-white text-xs font-semibold rounded-full" data-testid="current-plan-badge">
                  Current Plan
                </div>
              )}

              <div className="p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${plan.color}15` }}>
                    <Icon size={20} style={{ color: plan.color }} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">{plan.name}</h3>
                    <p className="text-xs text-slate-500">{plan.desc}</p>
                  </div>
                </div>

                <div className="mb-5">
                  <span className="text-3xl font-bold text-slate-900">{fmt(plan.price[currency], currency)}</span>
                  <span className="text-sm text-slate-500">/mo</span>
                </div>

                <div className="space-y-2.5 mb-6">
                  {plan.features.map((f, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      {f.included ? (
                        <Check size={14} className="text-green-500 flex-shrink-0" />
                      ) : (
                        <X size={14} className="text-slate-300 flex-shrink-0" />
                      )}
                      <span className={f.included ? "text-slate-700" : "text-slate-400"}>
                        {f.label}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Action Button */}
                {isCurrent ? (
                  <div className="w-full py-2.5 text-center text-sm font-medium text-green-600 bg-green-50 rounded-lg border border-green-200">
                    Your Current Plan
                  </div>
                ) : requestSent === plan.key ? (
                  <div className="w-full py-2.5 text-center text-sm font-medium text-blue-600 bg-blue-50 rounded-lg border border-blue-200" data-testid={`request-sent-${plan.key}`}>
                    <Mail size={14} className="inline mr-1" /> Upgrade request sent
                  </div>
                ) : isUpgrade ? (
                  <button
                    onClick={() => handleUpgradeRequest(plan.key)}
                    disabled={sending}
                    data-testid={`upgrade-btn-${plan.key}`}
                    className="w-full py-2.5 text-sm font-medium text-white rounded-lg transition-all flex items-center justify-center gap-2"
                    style={{ backgroundColor: plan.color }}
                  >
                    {sending ? <Loader2 size={14} className="animate-spin" /> : <ChevronUp size={14} />}
                    {plan.key === "enterprise" ? "Contact Sales" : "Upgrade"}
                    <ArrowRight size={14} />
                  </button>
                ) : isDowngrade ? (
                  <div className="w-full py-2.5 text-center text-sm font-medium text-slate-400 bg-slate-50 rounded-lg">
                    Included in your plan
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>

      {/* Upgrade Request Confirmation */}
      {requestSent && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 flex items-start gap-3" data-testid="upgrade-confirmation">
          <Mail size={20} className="text-blue-500 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-blue-900 text-sm">Upgrade request submitted</h4>
            <p className="text-sm text-blue-700 mt-1">
              Our team will contact you at your registered email to complete the upgrade to <span className="font-semibold capitalize">{requestSent}</span>.
              For immediate assistance, email <a href="mailto:info@getmyplan.in" className="underline font-medium">info@getmyplan.in</a>.
            </p>
          </div>
        </div>
      )}

      {/* FAQ */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Frequently Asked Questions</h3>
        <div className="space-y-4">
          {[
            { q: "Can I change plans at any time?", a: "Yes, you can upgrade or downgrade your plan at any time. Upgrades take effect immediately." },
            { q: "What happens when my trial ends?", a: "After the 7-day trial + 3-day grace period, your account will be read-only until you choose a paid plan." },
            { q: "Do you offer annual discounts?", a: "Yes! Annual plans come with a 20% discount. Contact our sales team for details." },
          ].map((item, i) => (
            <div key={i}>
              <p className="text-sm font-medium text-slate-800">{item.q}</p>
              <p className="text-sm text-slate-500 mt-0.5">{item.a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PlanUpgrade;
