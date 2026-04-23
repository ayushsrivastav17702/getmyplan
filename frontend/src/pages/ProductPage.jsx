import { useState, useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import Navbar from "../components/landing/Navbar";
import Footer from "../components/landing/Footer";
import { getProductBySlug } from "../data/productContent";

export default function ProductPage() {
  const { slug } = useParams();
  const product = useMemo(() => getProductBySlug(slug), [slug]);

  // ROI calculator state
  const [skus, setSkus] = useState(10000);
  const [accuracy, setAccuracy] = useState(65);
  const [avgValue, setAvgValue] = useState(50);

  const stockoutSavings = Math.round(skus * avgValue * 0.15 * 0.41);
  const overstockSavings = Math.round(skus * avgValue * 0.15 * 0.32);
  const totalSavings = stockoutSavings + overstockSavings;

  if (!product) {
    return (
      <div className="min-h-screen bg-[#0a0e27]">
        <Navbar />
        <div className="pt-32 pb-24 text-center text-white px-4">
          <h1 className="text-3xl font-bold mb-4" data-testid="product-not-found-title">Product Not Found</h1>
          <p className="text-slate-400 mb-8">The product you're looking for doesn't exist.</p>
          <div className="flex items-center justify-center gap-3">
            <Link to="/" className="px-5 py-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/20 transition" data-testid="back-to-home-link">
              Back to Home
            </Link>
            <Link to="/products" className="px-5 py-2.5 rounded-xl bg-white/[0.04] border border-white/10 text-white hover:bg-white/[0.08] transition" data-testid="browse-products-link">
              Browse All Products
            </Link>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  const badgeClass = (badge) => {
    if (badge === "Core") return "bg-emerald-500/10 border-emerald-500/30 text-emerald-300";
    if (badge === "Enterprise") return "bg-purple-500/10 border-purple-500/30 text-purple-300";
    return "bg-indigo-500/10 border-indigo-500/30 text-indigo-300";
  };

  return (
    <div className="min-h-screen bg-[#0a0e27]" data-testid="product-page">
      <Helmet>
        <title>{`${product.fullTitle} | GetMyPlan`}</title>
        <meta name="description" content={product.metaDescription} />
        <meta name="keywords" content={product.metaKeywords} />
      </Helmet>

      <Navbar />

      {/* ─── Hero ───────────────────────────────────────────────────── */}
      <section className="pt-28 pb-16 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/5 via-rose-500/5 to-transparent pointer-events-none" />
        <div className="relative z-10 max-w-3xl mx-auto px-4 sm:px-6">
          <span
            className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full border text-sm font-medium mb-6 bg-gradient-to-r ${product.heroGradient} bg-clip-text text-transparent border-indigo-500/30`}
            style={{ WebkitTextFillColor: "transparent" }}
            data-testid="product-badge"
          >
            {product.heroBadge}
          </span>
          <h1 className="text-3xl sm:text-5xl font-extrabold mb-4" data-testid="product-title">
            <span className={`bg-gradient-to-r ${product.heroGradient} bg-clip-text text-transparent`}>
              {product.fullTitle}
            </span>
          </h1>
          <p className="text-lg text-slate-400 leading-relaxed" data-testid="product-tagline">
            {product.tagline}
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/signup"
              className={`px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r ${product.heroGradient} hover:shadow-[0_10px_40px_-10px_rgba(99,102,241,0.6)] transition`}
              data-testid="product-cta-trial"
            >
              {product.ctaButton}
            </Link>
            <Link
              to="/#demo"
              className="px-6 py-3 rounded-xl font-semibold text-white bg-white/[0.04] border border-white/10 hover:bg-white/[0.08] transition"
              data-testid="product-cta-demo"
            >
              Watch Demo
            </Link>
          </div>
        </div>
      </section>

      {/* ─── Key Features ───────────────────────────────────────────── */}
      <section className="py-16 max-w-6xl mx-auto px-4 sm:px-6" data-testid="features-section">
        <h2 className="text-2xl sm:text-3xl font-bold text-white text-center mb-10">Key Features</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {product.features.map((f) => (
            <div
              key={f.title}
              className="bg-white/[0.04] border border-indigo-500/10 rounded-2xl p-5 hover:bg-white/[0.07] hover:border-indigo-500/30 transition-all"
              data-testid={`feature-card-${f.title.replace(/\s+/g, "-").toLowerCase()}`}
            >
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="text-base font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed mb-3">{f.description}</p>
              <span className={`inline-block px-2 py-0.5 text-[11px] rounded-full border ${badgeClass(f.badge)}`}>
                {f.badge}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* ─── How It Works ───────────────────────────────────────────── */}
      <section className="py-16 max-w-6xl mx-auto px-4 sm:px-6" data-testid="how-it-works-section">
        <div className="bg-white/[0.02] border border-white/5 rounded-3xl p-8 sm:p-12">
          <h2 className="text-2xl sm:text-3xl font-bold text-white text-center mb-10">How It Works</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {product.howItWorks.map((s, idx) => (
              <div key={s.step} className="text-center">
                <div className={`w-12 h-12 rounded-full bg-gradient-to-r ${product.heroGradient} text-white font-bold flex items-center justify-center mx-auto mb-4`}>
                  {s.step}
                </div>
                <h3 className="text-base font-semibold text-white mb-2">{s.title}</h3>
                <p className="text-sm text-slate-400">{s.description}</p>
                {idx < product.howItWorks.length - 1 && (
                  <div className="hidden lg:block text-xl text-slate-400 mt-4">→</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Technical Formula ──────────────────────────────────────── */}
      {product.technicalFormula && (
        <section className="py-16 max-w-4xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-white text-center mb-8">Technical Specification</h2>
          <div className="bg-black/40 border border-indigo-500/20 rounded-2xl p-8 text-center font-mono text-sm text-indigo-300 leading-relaxed" data-testid="product-formula">
            {product.technicalFormula}
          </div>
        </section>
      )}

      {/* ─── Benefits ───────────────────────────────────────────────── */}
      <section className="py-16 max-w-6xl mx-auto px-4 sm:px-6" data-testid="benefits-section">
        <h2 className="text-2xl sm:text-3xl font-bold text-white text-center mb-10">Key Benefits</h2>
        <div className="grid sm:grid-cols-3 gap-4">
          {product.benefits.map((b) => (
            <div
              key={b.title}
              className="text-center bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 rounded-2xl p-6"
              data-testid={`benefit-card-${b.title.replace(/\s+/g, "-").toLowerCase()}`}
            >
              <div className="text-4xl mb-3">{b.icon}</div>
              <h3 className="text-lg font-semibold text-white mb-1">{b.title}</h3>
              <p className="text-sm text-slate-400">{b.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ─── Use Cases ──────────────────────────────────────────────── */}
      <section className="py-16 max-w-6xl mx-auto px-4 sm:px-6" data-testid="use-cases-section">
        <h2 className="text-2xl sm:text-3xl font-bold text-white text-center mb-10">Use Cases</h2>
        <div className="grid sm:grid-cols-3 gap-4">
          {product.useCases.map((u) => (
            <div key={u.title} className="bg-white/[0.04] border border-white/10 rounded-2xl p-5 hover:bg-white/[0.07] transition">
              <h3 className="text-base font-semibold text-white mb-2">{u.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{u.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ─── ROI Calculator ─────────────────────────────────────────── */}
      <section className="py-16 max-w-4xl mx-auto px-4 sm:px-6">
        <h2 className="text-2xl sm:text-3xl font-bold text-white text-center mb-8">Calculate Your ROI</h2>
        <div className="bg-white/[0.04] border border-indigo-500/10 rounded-2xl p-6 sm:p-8" data-testid="roi-calculator">
          <div className="grid sm:grid-cols-3 gap-4 mb-6">
            <div>
              <label htmlFor="roi-skus" className="block text-xs text-slate-400 mb-1.5">Number of SKUs</label>
              <input
                id="roi-skus"
                type="number"
                value={skus}
                onChange={(e) => setSkus(+e.target.value || 0)}
                className="w-full px-4 py-2.5 bg-black/30 border border-indigo-500/20 rounded-xl text-white text-sm focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500/40 outline-none"
                data-testid="roi-input-skus"
              />
            </div>
            <div>
              <label htmlFor="roi-accuracy" className="block text-xs text-slate-400 mb-1.5">Current Forecast Accuracy %</label>
              <input
                id="roi-accuracy"
                type="number"
                value={accuracy}
                onChange={(e) => setAccuracy(+e.target.value || 0)}
                className="w-full px-4 py-2.5 bg-black/30 border border-indigo-500/20 rounded-xl text-white text-sm focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500/40 outline-none"
                data-testid="roi-input-accuracy"
              />
            </div>
            <div>
              <label htmlFor="roi-value" className="block text-xs text-slate-400 mb-1.5">Average SKU Value ($)</label>
              <input
                id="roi-value"
                type="number"
                value={avgValue}
                onChange={(e) => setAvgValue(+e.target.value || 0)}
                className="w-full px-4 py-2.5 bg-black/30 border border-indigo-500/20 rounded-xl text-white text-sm focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500/40 outline-none"
                data-testid="roi-input-value"
              />
            </div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-emerald-400 mb-1" data-testid="roi-total-savings">
              ${totalSavings.toLocaleString()}
            </div>
            <div className="text-sm text-slate-400">Estimated Annual Savings</div>
            <div className="flex justify-center gap-6 mt-3 text-xs text-slate-400">
              <span>Stockout Reduction: ${stockoutSavings.toLocaleString()}</span>
              <span>Overstock Reduction: ${overstockSavings.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Related Products ───────────────────────────────────────── */}
      {product.relatedProducts?.length > 0 && (
        <section className="py-16 max-w-5xl mx-auto px-4 sm:px-6" data-testid="related-products-section">
          <h2 className="text-2xl sm:text-3xl font-bold text-white text-center mb-8">Related Products</h2>
          <div className="flex flex-wrap justify-center gap-3">
            {product.relatedProducts.map((rSlug) => {
              const rp = getProductBySlug(rSlug);
              if (!rp) return null;
              return (
                <Link
                  key={rSlug}
                  to={`/products/${rSlug}`}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/[0.04] border border-white/10 text-white text-sm hover:bg-white/[0.08] hover:border-indigo-500/30 transition"
                  data-testid={`related-product-${rSlug}`}
                >
                  <span className="text-lg">{rp.icon}</span>
                  <span>{rp.title}</span>
                  <span className="text-indigo-400">→</span>
                </Link>
              );
            })}
          </div>
        </section>
      )}

      {/* ─── FAQ ────────────────────────────────────────────────────── */}
      {product.faq?.length > 0 && (
        <section className="py-16 max-w-3xl mx-auto px-4 sm:px-6" data-testid="faq-section">
          <h2 className="text-2xl sm:text-3xl font-bold text-white text-center mb-8">Frequently Asked Questions</h2>
          <div className="space-y-3">
            {product.faq.map((item, idx) => (
              <details
                key={idx}
                className="group bg-white/[0.04] border border-white/10 rounded-xl overflow-hidden"
                data-testid={`faq-item-${idx}`}
              >
                <summary className="cursor-pointer p-4 font-medium text-white hover:bg-white/[0.02] transition flex items-center justify-between">
                  <span>{item.question}</span>
                  <span className="text-indigo-400 group-open:rotate-45 transition-transform text-xl leading-none">+</span>
                </summary>
                <div className="p-4 pt-0 text-sm text-slate-400 border-t border-white/5">
                  {item.answer}
                </div>
              </details>
            ))}
          </div>
        </section>
      )}

      {/* ─── Final CTA ──────────────────────────────────────────────── */}
      <section className="py-20 px-4 sm:px-6">
        <div className={`max-w-5xl mx-auto rounded-3xl p-10 sm:p-14 text-center bg-gradient-to-r ${product.heroGradient} shadow-[0_30px_80px_-30px_rgba(99,102,241,0.6)]`} data-testid="final-cta-section">
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">{product.ctaTitle}</h2>
          <p className="text-white/80 mb-8">Join leading fashion brands using GetMyPlan.</p>
          <Link
            to="/signup"
            className="inline-block px-8 py-3 rounded-xl bg-white text-slate-900 font-semibold hover:shadow-xl transition"
            data-testid="final-cta-button"
          >
            {product.ctaButton}
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
