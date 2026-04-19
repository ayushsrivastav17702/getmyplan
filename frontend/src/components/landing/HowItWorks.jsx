export default function HowItWorks() {
  return (
    <section id="how-it-works" className="relative py-20" data-testid="how-it-works">
      <div className="max-w-5xl mx-auto px-4 sm:px-6">
        <h2 className="text-3xl sm:text-4xl font-bold text-center text-white mb-12">How It Works</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {[
            { step: "01", title: "Upload Data", desc: "Upload 5 CSV files: SKU Master, Store Master, Daily Sales, Inventory, COGS." },
            { step: "02", title: "AI Trains", desc: "Our 3-model ensemble learns your demand patterns in minutes." },
            { step: "03", title: "Get Forecasts", desc: "12-month forecasts with confidence intervals, stockout warnings." },
            { step: "04", title: "Generate Orders", desc: "One-click buy plans, PO consolidation, approval workflows." },
          ].map((s) => (
            <div key={s.step} className="bg-white/[0.04] backdrop-blur-sm border border-indigo-500/10 rounded-2xl p-5 hover:bg-white/[0.07] transition-all group">
              <div className="text-3xl font-extrabold text-indigo-500/30 mb-3 group-hover:text-indigo-500/50 transition-colors">{s.step}</div>
              <h3 className="text-base font-semibold text-white mb-2">{s.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
