import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import Navbar from "../components/landing/Navbar";
import Footer from "../components/landing/Footer";

export default function VsAnaplan() {
  return (
    <>
      <Helmet>
        <title>Getmyplan vs Anaplan: Which AI Planning Platform Wins in 2026?</title>
        <meta name="description" content="Getmyplan vs Anaplan comparison: Features, pricing, and implementation. Getmyplan offers 91% AI forecast accuracy at 1/3 the cost." />
        <meta name="keywords" content="Anaplan alternative, Anaplan vs Getmyplan, AI demand planning comparison" />
        <link rel="canonical" href="https://getmyplan.in/vs/anaplan" />
      </Helmet>
      <div className="min-h-screen bg-white">
        <Navbar />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-16" data-testid="vs-anaplan-page">

          <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight mb-6">
            Getmyplan vs Anaplan: Which Planning Platform Wins in 2026?
          </h1>

          {/* Quick Verdict */}
          <section className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-10">
            <h2 className="text-lg font-semibold text-slate-800 mb-2">Quick Verdict (30 seconds)</h2>
            <p className="text-slate-700 text-sm leading-relaxed">
              <strong>Getmyplan wins for mid-market fashion retailers</strong> needing AI demand forecasting at 1/3 the cost.{" "}
              <strong>Anaplan wins for large enterprises</strong> with complex connected planning needs across finance, supply chain, and sales.
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
                  <th className="text-left px-4 py-3 font-semibold text-slate-500 border-b">Anaplan</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {[
                  ["AI-native demand forecasting", "91% accuracy, 3-model ensemble", "Requires marketplace app"],
                  ["Buy plan generation", "Included", "Not available"],
                  ["Stock-out prediction", "Real-time risk scoring", "Not available"],
                  ["Unlimited users", "Included", "Per-seat pricing"],
                  ["Implementation time", "15 minutes", "3-6 months"],
                  ["Regional support", "24/7", "US hours only"],
                  ["Free trial", "7 days, no credit card", "Not available"],
                  ["Starting price", "\u20B930,000/month", "$2,000+/month (~\u20B91,66,000)"],
                ].map(([feat, gmp, ana], i) => (
                  <tr key={i} className="hover:bg-slate-50/50">
                    <td className="px-4 py-3 text-slate-700 font-medium">{feat}</td>
                    <td className="px-4 py-3 text-blue-800">{gmp}</td>
                    <td className="px-4 py-3 text-slate-500">{ana}</td>
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
                <li>Fashion retailer or D2C brand with 10-500 stores</li>
                <li>Need AI demand forecasting out-of-the-box (91% accuracy)</li>
                <li>Budget is {"\u20B9"}30,000-{"\u20B9"}1,00,000 per month</li>
                <li>You want results in days, not months</li>
              </ul>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-5">
              <h2 className="text-base font-semibold text-slate-800 mb-3">When to choose Anaplan</h2>
              <ul className="text-sm text-slate-600 space-y-2">
                <li>500+ users across multiple departments</li>
                <li>Need connected planning (finance + supply chain + sales + HR)</li>
                <li>Budget is $50,000+ per year</li>
                <li>You have a dedicated implementation team</li>
              </ul>
            </div>
          </div>

          {/* Migration Guide */}
          <h2 className="text-xl font-semibold text-slate-800 mb-4">Migration Guide: Switch from Anaplan to Getmyplan</h2>
          <ol className="text-sm text-slate-700 space-y-2 mb-10 list-decimal list-inside">
            <li>Export your Anaplan models to CSV</li>
            <li>Upload to Getmyplan's import wizard (15 minutes)</li>
            <li>Run AI training on historical data</li>
            <li>Start forecasting with 91% accuracy</li>
          </ol>

          {/* Testimonial */}
          <blockquote className="border-l-4 border-blue-500 pl-5 py-3 bg-slate-50 rounded-r-lg mb-10">
            <p className="text-sm text-slate-700 italic">"GetMyPlan reduced our stockouts by 40% and increased revenue by 25% in just 3 months. The AI forecasts are incredibly accurate."</p>
            <footer className="text-xs text-slate-500 mt-2">&mdash; Rahul Sharma, CEO, FashionHub</footer>
          </blockquote>

          {/* CTA */}
          <div className="text-center py-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
            <p className="text-lg font-semibold text-slate-800 mb-3">Ready to switch?</p>
            <Link to="/signup" className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition" data-testid="vs-anaplan-cta">
              Start 7-Day Free Trial &rarr;
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    </>
  );
}
