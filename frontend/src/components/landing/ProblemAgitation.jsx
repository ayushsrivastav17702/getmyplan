export default function ProblemAgitation() {
  return (
    <section className="relative py-20 max-w-6xl mx-auto px-4 sm:px-6" data-testid="problem-section">
      <h2 className="text-3xl sm:text-4xl font-bold text-center text-white mb-12">
        This is what inventory planning looks like <span className="text-rose-400">right now</span>
      </h2>
      <div className="grid md:grid-cols-2 gap-6">
        {/* Problem */}
        <div className="bg-white/[0.04] backdrop-blur-sm rounded-2xl border border-rose-500/20 p-6 sm:p-8" data-testid="problem-card">
          <h3 className="text-lg font-semibold text-rose-400 mb-5 flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" /></svg>
            Without GetMyPlan
          </h3>
          <div className="space-y-3">
            {[
              { icon: "table", text: "Excel Hell", sub: "14 hours/week buried in spreadsheets" },
              { icon: "alert", text: "$50K-100K/mo lost revenue", sub: "From preventable stockouts" },
              { icon: "help", text: "Gut-feel ordering", sub: '"We think..." instead of "We know..."' },
              { icon: "box", text: "30% dead stock", sub: "Never sells at full price" },
            ].map((item) => (
              <div key={item.text} className="bg-black/30 rounded-xl p-4 border border-rose-500/10">
                <div className="text-sm font-medium text-white">{item.text}</div>
                <div className="text-xs text-slate-400 mt-0.5">{item.sub}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Solution */}
        <div className="bg-white/[0.04] backdrop-blur-sm rounded-2xl border border-emerald-500/20 p-6 sm:p-8" data-testid="solution-card">
          <h3 className="text-lg font-semibold text-emerald-400 mb-5 flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
            With GetMyPlan
          </h3>
          <div className="space-y-3">
            {[
              { metric: "41%", text: "Stockouts reduced", color: "text-emerald-400" },
              { metric: "32%", text: "Dead stock reduced", color: "text-emerald-400" },
              { metric: "14hr to 2.5hr", text: "Planner time saved/week", color: "text-emerald-400" },
              { metric: "92.7%", text: "Forecast accuracy", color: "text-emerald-400" },
            ].map((item) => (
              <div key={item.text} className="bg-black/30 rounded-xl p-4 border border-emerald-500/10 flex items-center gap-4">
                <span className={`text-lg font-bold ${item.color} whitespace-nowrap`}>{item.metric}</span>
                <span className="text-sm text-slate-300">{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
