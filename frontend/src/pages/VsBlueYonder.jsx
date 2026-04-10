import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import Navbar from "../components/landing/Navbar";
import Footer from "../components/landing/Footer";

export default function VsBlueYonder() {
  return (
    <>
      <Helmet>
        <title>Getmyplan vs Blue Yonder: AI Demand Planning Comparison 2026</title>
        <meta name="description" content="Getmyplan vs Blue Yonder comparison. Getmyplan: 15-min implementation, INR 30k/month. Blue Yonder: 6-month implementation, enterprise pricing." />
        <meta name="keywords" content="Blue Yonder alternative, Blue Yonder vs Getmyplan, demand planning software" />
        <link rel="canonical" href="https://getmyplan.in/vs/blue-yonder" />
      </Helmet>
      <div className="min-h-screen bg-white">
        <Navbar />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-16" data-testid="vs-blue-yonder-page">

          <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight mb-6">
            Getmyplan vs Blue Yonder: AI Demand Planning Comparison
          </h1>

          {/* Quick Verdict */}
          <section className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-10">
            <h2 className="text-lg font-semibold text-slate-800 mb-2">Quick Verdict</h2>
            <p className="text-slate-700 text-sm leading-relaxed">
              <strong>Getmyplan</strong> offers faster implementation (15 minutes vs 6 months) at lower cost for mid-market fashion retailers.{" "}
              <strong>Blue Yonder</strong> is built for Fortune 500 supply chains with complex global operations.
            </p>
          </section>

          {/* Comparison Table */}
          <h2 className="text-xl font-semibold text-slate-800 mb-4">Feature Comparison Table</h2>
          <div className="overflow-x-auto mb-10">
            <table className="w-full text-sm border border-slate-200 rounded-lg overflow-hidden">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left px-4 py-3 font-semibold text-slate-700 border-b">Feature</th>
                  <th className="text-left px-4 py-3 font-semibold text-blue-700 border-b">Getmyplan</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-500 border-b">Blue Yonder</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {[
                  ["Implementation time", "15 minutes", "6-12 months"],
                  ["AI demand forecasting", "91% accuracy", "Proprietary"],
                  ["Fashion retail specialization", "Built for apparel/footwear", "General retail"],
                  ["Free trial", "7 days, no credit card", "Not available"],
                  ["Transparent pricing", "\u20B930k-\u20B91L/month", "Custom quote only"],
                  ["Target customer", "Mid-market fashion (10-500 stores)", "Enterprise retail/CPG (500+ stores)"],
                ].map(([feat, gmp, by], i) => (
                  <tr key={i} className="hover:bg-slate-50/50">
                    <td className="px-4 py-3 text-slate-700 font-medium">{feat}</td>
                    <td className="px-4 py-3 text-blue-800">{gmp}</td>
                    <td className="px-4 py-3 text-slate-500">{by}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* When to choose */}
          <div className="grid sm:grid-cols-2 gap-6 mb-10">
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
              <h2 className="text-base font-semibold text-blue-900 mb-3">When to choose Getmyplan</h2>
              <ul className="text-sm text-blue-800 space-y-2">
                <li>You have 10-500 stores</li>
                <li>You need results in days, not months</li>
                <li>You want transparent, predictable pricing</li>
                <li>You are a fashion or D2C brand</li>
              </ul>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-5">
              <h2 className="text-base font-semibold text-slate-800 mb-3">When to choose Blue Yonder</h2>
              <ul className="text-sm text-slate-600 space-y-2">
                <li>Global enterprise with complex supply chains</li>
                <li>Dedicated implementation team of 5+ people</li>
                <li>Budget is $500,000+ per year</li>
                <li>Multi-country, multi-warehouse optimization</li>
              </ul>
            </div>
          </div>

          {/* Testimonial */}
          <blockquote className="border-l-4 border-blue-500 pl-5 py-3 bg-slate-50 rounded-r-lg mb-10">
            <p className="text-sm text-slate-700 italic">"GetMyPlan reduced our stockouts by 40% and increased revenue by 25% in just 3 months."</p>
            <footer className="text-xs text-slate-500 mt-2">&mdash; FashionHub CEO</footer>
          </blockquote>

          {/* CTA */}
          <div className="text-center py-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
            <p className="text-lg font-semibold text-slate-800 mb-3">Try the faster alternative</p>
            <Link to="/signup" className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition" data-testid="vs-blue-yonder-cta">
              Start 7-Day Free Trial &rarr;
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    </>
  );
}
