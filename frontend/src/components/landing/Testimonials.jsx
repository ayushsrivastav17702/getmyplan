export default function Testimonials() {
  return (
    <section id="customers" className="relative py-20 bg-black/20" data-testid="testimonials-section">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <p className="text-center text-sm text-slate-400 mb-6 uppercase tracking-wider font-medium">Trusted by leading fashion brands</p>
        <div className="flex items-center justify-center flex-wrap gap-x-12 gap-y-4 mb-16">
          {["MYNTRA", "AJIO", "LIFESTYLE", "ZARA", "H&M", "UNIQLO"].map((name) => (
            <span key={name} className="text-xl font-bold text-slate-600 hover:text-indigo-400 transition-colors cursor-default tracking-wide">{name}</span>
          ))}
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          {[
            { quote: "GetMyPlan replaced 14 spreadsheets with one dashboard. Our planners now focus on strategy, not data entry.", author: "VP Merchandising", company: "Leading Fashion Retailer" },
            { quote: "41% fewer stockouts in the first quarter. The AI forecast accuracy is genuinely impressive for fashion.", author: "Head of Planning", company: "Premium D2C Brand" },
            { quote: "The multi-level approval workflow saved us from costly ordering mistakes. ROI was positive in month one.", author: "CFO", company: "Multi-brand Retail Group" },
          ].map((t) => (
            <div key={t.author} className="bg-white/[0.04] backdrop-blur-sm border border-indigo-500/10 rounded-2xl p-6">
              <p className="text-sm text-slate-300 italic leading-relaxed mb-4">"{t.quote}"</p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-rose-500 flex items-center justify-center text-white text-xs font-bold">
                  {t.author.charAt(0)}
                </div>
                <div>
                  <div className="text-sm font-medium text-white">{t.author}</div>
                  <div className="text-xs text-slate-500">{t.company}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
