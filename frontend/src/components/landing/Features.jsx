const FEATURES = [
  { icon: "brain", title: "AI Demand Forecasting", desc: "3-model ensemble with 12-month horizon and confidence intervals.", badge: "Popular" },
  { icon: "store", title: "Store Wedge Classification", desc: "A/B/C store classification based on 90-day revenue.", badge: "Enterprise" },
  { icon: "cart", title: "Buy Plan Generator", desc: "ML generates optimal buy quantities per SKU-store combination.", badge: "Popular" },
  { icon: "tag", title: "Style Mix Tagging", desc: "Auto-classify SKUs as Core/Fashion/Test based on sales velocity.", badge: "Enterprise" },
  { icon: "check", title: "Multi-Level Approval", desc: "6-stage approval workflow with full audit trail.", badge: "Enterprise" },
  { icon: "package", title: "Order Consolidation", desc: "Combine individual store POs into optimized supplier POs.", badge: "Enterprise" },
  { icon: "shield", title: "Statistical Safety Stock", desc: "z-score x MAD x sqrt(LT/RP) formula with configurable service levels.", badge: "Enterprise" },
  { icon: "alert", title: "Stock-Out Prediction", desc: "Real-time risk scoring with severity levels and revenue impact.", badge: "Popular" },
  { icon: "users", title: "Role-Based Access Control", desc: "11 predefined roles with granular module-level permissions.", badge: "Enterprise" },
];

const BADGE_COLORS = {
  Popular: "bg-rose-500/15 text-rose-400",
  Enterprise: "bg-indigo-500/15 text-indigo-400",
};

export default function Features() {
  return (
    <section id="features" className="relative py-20 bg-black/20" data-testid="features-section">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <h2 className="text-3xl sm:text-4xl font-bold text-center text-white mb-4">Everything you need to plan smarter</h2>
        <p className="text-center text-slate-400 mb-12 max-w-2xl mx-auto">From demand forecasting to order consolidation — a complete planning suite for fashion retail.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map((f) => (
            <div key={f.title} className="bg-white/[0.04] backdrop-blur-sm border border-indigo-500/10 rounded-2xl p-5 hover:bg-white/[0.07] hover:-translate-y-1 transition-all group" data-testid={`feature-${f.title.toLowerCase().replace(/\s/g, "-")}`}>
              <div className="w-10 h-10 rounded-xl bg-indigo-500/15 flex items-center justify-center text-indigo-400 mb-4 group-hover:bg-indigo-500/25 transition-colors">
                <FeatureIcon name={f.icon} />
              </div>
              <h3 className="text-base font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-sm text-slate-400 mb-3 leading-relaxed">{f.desc}</p>
              <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${BADGE_COLORS[f.badge]}`}>{f.badge}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FeatureIcon({ name }) {
  const icons = {
    brain: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>,
    store: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>,
    cart: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" /></svg>,
    tag: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>,
    check: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
    package: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>,
    shield: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>,
    alert: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>,
    users: <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>,
  };
  return icons[name] || icons.check;
}
