import { useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import Navbar from "../components/landing/Navbar";
import Footer from "../components/landing/Footer";
import { getSolutionBySlug } from "../data/solutionContent";

const KICKER_CLASSES = {
  indigo: "bg-indigo-500/10 border-indigo-500/30 text-indigo-300",
  amber: "bg-amber-500/10 border-amber-500/30 text-amber-300",
  pink: "bg-pink-500/10 border-pink-500/30 text-pink-300",
  teal: "bg-teal-500/10 border-teal-500/30 text-teal-300",
  purple: "bg-purple-500/10 border-purple-500/30 text-purple-300",
};

export default function SolutionPage() {
  const { slug } = useParams();
  const sol = useMemo(() => getSolutionBySlug(slug), [slug]);

  if (!sol) {
    return (
      <div className="min-h-screen bg-[#0a0e27]">
        <Navbar />
        <div className="pt-32 pb-24 text-center text-white px-4">
          <h1 className="text-3xl font-bold mb-4" data-testid="solution-not-found-title">Solution Not Found</h1>
          <p className="text-slate-400 mb-8">The solution you're looking for doesn't exist.</p>
          <Link to="/" className="px-5 py-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/20 transition" data-testid="solution-back-home">
            Back to Home
          </Link>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0e27]" data-testid="solution-page">
      <Helmet>
        <title>{`${sol.kicker} | AI Demand Planning | GetMyPlan`}</title>
        <meta name="description" content={sol.metaDescription} />
        <meta name="keywords" content={sol.metaKeywords} />
      </Helmet>

      <Navbar />

      {/* ─── Hero ───────────────────────────────────────────────── */}
      <section className="pt-28 pb-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/5 via-rose-500/5 to-transparent pointer-events-none" />
        <div className="relative z-10 max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <span
            className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full border text-sm font-medium mb-6 ${KICKER_CLASSES[sol.kickerColor] || KICKER_CLASSES.indigo}`}
            data-testid="solution-kicker"
          >
            {sol.kicker}
          </span>
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white mb-4" data-testid="solution-title">
            {sol.heroTitle}{" "}
            <span className={`bg-gradient-to-r ${sol.heroGradient} bg-clip-text text-transparent`}>
              {sol.heroHighlight}
            </span>
          </h1>
          <p className="text-lg text-slate-400 leading-relaxed mb-8">{sol.tagline}</p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/signup"
              className={`px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r ${sol.heroGradient} hover:shadow-[0_10px_40px_-10px_rgba(99,102,241,0.6)] transition`}
              data-testid="solution-cta-trial"
            >
              Start Free Trial
            </Link>
            <Link
              to="/#demo"
              className="px-6 py-3 rounded-xl font-semibold text-white bg-white/[0.04] border border-white/10 hover:bg-white/[0.08] transition"
              data-testid="solution-cta-demo"
            >
              Watch Demo
            </Link>
          </div>
        </div>
      </section>

      {/* ─── Challenges ─────────────────────────────────────────── */}
      <section className="py-14 max-w-6xl mx-auto px-4 sm:px-6" data-testid="solution-challenges">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {sol.challenges.map((c) => (
            <div
              key={c.title}
              className="bg-white/[0.04] border border-indigo-500/10 rounded-2xl p-6 hover:bg-white/[0.07] hover:border-indigo-500/30 transition"
            >
              <div className="text-3xl mb-3">{c.icon}</div>
              <h3 className="text-base font-semibold text-white mb-2">{c.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{c.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ─── How We Help ────────────────────────────────────────── */}
      <section className="py-14 max-w-6xl mx-auto px-4 sm:px-6" data-testid="solution-how-we-help">
        <h2 className="text-2xl sm:text-3xl font-bold text-white text-center mb-10">How GetMyPlan Helps</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {sol.howWeHelp.map((h) => (
            <div key={h.title} className="bg-white/[0.04] border border-white/10 rounded-2xl p-6 hover:bg-white/[0.07] transition">
              <div className="text-3xl mb-3">{h.icon}</div>
              <h3 className="text-lg font-semibold text-white mb-2">{h.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{h.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ─── Key Features checklist ─────────────────────────────── */}
      <section className="py-14 max-w-5xl mx-auto px-4 sm:px-6" data-testid="solution-key-features">
        <h2 className="text-2xl sm:text-3xl font-bold text-white text-center mb-10">Key Features</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {sol.keyFeatures.map((f) => (
            <div key={f} className="flex items-center gap-3 bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3 text-sm text-slate-300">
              <span className="text-emerald-400 font-bold">✓</span>
              {f}
            </div>
          ))}
        </div>
      </section>

      {/* ─── Final CTA ──────────────────────────────────────────── */}
      <section className="py-16 px-4 sm:px-6">
        <div className={`max-w-5xl mx-auto rounded-3xl p-10 sm:p-12 text-center bg-gradient-to-r ${sol.heroGradient} shadow-[0_30px_80px_-30px_rgba(99,102,241,0.6)]`} data-testid="solution-final-cta">
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-6">{sol.ctaTitle}</h2>
          <Link
            to="/signup"
            className="inline-block px-8 py-3 rounded-xl bg-white text-slate-900 font-semibold hover:shadow-xl transition"
            data-testid="solution-final-cta-button"
          >
            Start Free Trial
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
