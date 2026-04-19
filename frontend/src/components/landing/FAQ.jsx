import { useState } from "react";
import { ChevronDown } from "lucide-react";

const FAQS = [
  { q: "What is GetMyPlan?", a: "GetMyPlan is an AI-powered demand planning platform for fashion retailers. It predicts what you'll sell, where, and when with 92.7% forecast accuracy." },
  { q: "How accurate is GetMyPlan's AI forecasting?", a: "92.7% forecast accuracy based on 12-month backtest across 50+ fashion retail datasets globally." },
  { q: "How long does setup take?", a: "15 minutes. Upload 5 CSV files and our 75-rule validation fixes errors automatically." },
  { q: "Is there a free trial?", a: "Yes. 7-day free trial. No credit card required. Cancel anytime." },
  { q: "What data do I need to start?", a: "Five CSV files: SKU Master, Store Master, Daily Sales (90+ days), Store Inventory, and COGS." },
  { q: "Can I integrate with my existing ERP/POS?", a: "Yes. We support API integrations with SAP, Oracle, Shopify, and most ERP/POS systems." },
];

export default function FAQ() {
  const [open, setOpen] = useState(null);
  return (
    <section id="faq" className="relative py-20 max-w-3xl mx-auto px-4 sm:px-6" data-testid="faq-section">
      <h2 className="text-3xl sm:text-4xl font-bold text-center text-white mb-12">Frequently Asked Questions</h2>
      <div className="space-y-3">
        {FAQS.map((faq, i) => (
          <div key={i} className="bg-white/[0.04] backdrop-blur-sm border border-indigo-500/10 rounded-xl overflow-hidden">
            <button onClick={() => setOpen(open === i ? null : i)} className="w-full flex items-center justify-between px-5 py-4 text-left">
              <span className="text-sm font-medium text-white pr-4">{faq.q}</span>
              <ChevronDown className={`w-4 h-4 text-indigo-400 flex-shrink-0 transition-transform ${open === i ? "rotate-180" : ""}`} />
            </button>
            {open === i && (
              <div className="px-5 pb-4 text-sm text-slate-400 leading-relaxed animate-in fade-in slide-in-from-top-1 duration-200">{faq.a}</div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
