import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import Navbar from "../components/landing/Navbar";
import Footer from "../components/landing/Footer";

export default function AiDemandPlanning() {
  return (
    <>
      <Helmet>
        <title>Complete Guide to AI Demand Planning for Fashion Retail (2026)</title>
        <meta name="description" content="Learn how AI demand planning achieves 91% forecast accuracy. Complete guide with implementation steps, case studies, and ROI calculator." />
        <meta name="keywords" content="AI demand planning, demand forecasting machine learning, retail demand planning" />
        <link rel="canonical" href="https://getmyplan.in/ai-demand-planning" />
      </Helmet>
      <div className="min-h-screen bg-white">
        <Navbar />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-16" data-testid="ai-demand-planning-page">

          <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight mb-6">
            Complete Guide to AI Demand Planning for Fashion Retail (2026)
          </h1>

          {/* What is AI Demand Planning */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-slate-800 mb-3">What is AI Demand Planning?</h2>
            <p className="text-sm text-slate-700 leading-relaxed">
              AI demand planning uses machine learning algorithms to analyze historical sales data, market trends, and seasonal patterns to predict future demand with{" "}
              <strong>91% accuracy</strong>&mdash;compared to 60-70% with Excel.
            </p>
          </section>

          {/* Why Traditional Fails */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">Why Traditional Forecasting Fails</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border border-slate-200 rounded-lg overflow-hidden">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-4 py-3 font-semibold text-slate-700 border-b">Method</th>
                    <th className="text-left px-4 py-3 font-semibold border-b">Accuracy</th>
                    <th className="text-left px-4 py-3 font-semibold border-b">Time to Insights</th>
                    <th className="text-left px-4 py-3 font-semibold border-b">Scalability</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr><td className="px-4 py-3 text-slate-700">Excel / Sheets</td><td className="px-4 py-3 text-red-600">60-70%</td><td className="px-4 py-3">Days</td><td className="px-4 py-3 text-red-600">Breaks at 10K SKUs</td></tr>
                  <tr><td className="px-4 py-3 text-slate-700">Traditional ERP</td><td className="px-4 py-3 text-amber-600">70-75%</td><td className="px-4 py-3">Weeks</td><td className="px-4 py-3 text-amber-600">Expensive to scale</td></tr>
                  <tr className="bg-blue-50/50"><td className="px-4 py-3 text-blue-900 font-semibold">AI Demand Planning (Getmyplan)</td><td className="px-4 py-3 text-blue-700 font-bold">91%</td><td className="px-4 py-3 text-blue-700 font-bold">15 minutes</td><td className="px-4 py-3 text-blue-700">Unlimited SKUs</td></tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* 3-Model Ensemble */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">The 3-Model Ensemble Method</h2>
            <p className="text-sm text-slate-700 mb-4">Getmyplan uses three machine learning models in ensemble:</p>
            <div className="grid sm:grid-cols-3 gap-4 mb-4">
              {[
                ["Holt-Winters", "Captures seasonality and trends in fashion retail"],
                ["Random Forest", "Handles non-linear patterns and promotions"],
                ["Seasonal Decomposition", "Separates seasonal components from noise"],
              ].map(([name, desc]) => (
                <div key={name} className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-slate-800 mb-1">{name}</h3>
                  <p className="text-xs text-slate-600">{desc}</p>
                </div>
              ))}
            </div>
            <p className="text-sm text-slate-700">Each model votes on the final forecast, resulting in <strong>91% accuracy</strong>.</p>
          </section>

          {/* Implementation Steps */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">How to Implement AI Demand Planning in 4 Steps</h2>
            <div className="space-y-4">
              {[
                ["Upload Data (15 min)", "7 CSV files &mdash; Style Master, Sales (12+ months), Inventory, Stores, and optional marketing data"],
                ["AI Analyzes (real-time)", "3 ML models process your data, perform gap analysis, and detect stockout risks"],
                ["Generate Buy Plan (instant)", "Set revenue target, AI calculates optimal quantities per SKU and channel split"],
                ["Execute & Track (ongoing)", "Export Excel workbook, monitor via live Executive Dashboard with Health Score and KPIs"],
              ].map(([title, desc], i) => (
                <div key={i} className="flex gap-4">
                  <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0">{i + 1}</div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
                    <p className="text-xs text-slate-600 mt-0.5" dangerouslySetInnerHTML={{ __html: desc }} />
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Case Study */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">Case Study: FashionHub reduced stockouts by 40%</h2>
            <blockquote className="border-l-4 border-blue-500 pl-5 py-3 bg-slate-50 rounded-r-lg">
              <p className="text-sm text-slate-700 italic">"Getmyplan reduced our stockouts by 40% and increased revenue by 25% in just 3 months. The AI forecasts are incredibly accurate and the team is amazing to work with."</p>
              <footer className="text-xs text-slate-500 mt-2">&mdash; Rahul Sharma, CEO, FashionHub</footer>
            </blockquote>
          </section>

          {/* Comparison Table */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">Getmyplan vs Anaplan vs Blue Yonder</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border border-slate-200 rounded-lg overflow-hidden">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-4 py-3 font-semibold text-slate-700 border-b">Feature</th>
                    <th className="text-left px-4 py-3 font-semibold text-blue-700 border-b">Getmyplan</th>
                    <th className="text-left px-4 py-3 font-semibold text-slate-500 border-b">Anaplan</th>
                    <th className="text-left px-4 py-3 font-semibold text-slate-500 border-b">Blue Yonder</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr><td className="px-4 py-3 font-medium">Implementation</td><td className="px-4 py-3 text-blue-800 font-bold">15 min</td><td className="px-4 py-3 text-slate-500">3-6 months</td><td className="px-4 py-3 text-slate-500">6-12 months</td></tr>
                  <tr><td className="px-4 py-3 font-medium">Starting price</td><td className="px-4 py-3 text-blue-800 font-bold">{"\u20B9"}30,000/mo</td><td className="px-4 py-3 text-slate-500">{"\u20B9"}1,66,000+/mo</td><td className="px-4 py-3 text-slate-500">Enterprise (custom)</td></tr>
                  <tr><td className="px-4 py-3 font-medium">Free trial</td><td className="px-4 py-3 text-blue-800 font-bold">7 days</td><td className="px-4 py-3 text-slate-500">No</td><td className="px-4 py-3 text-slate-500">No</td></tr>
                  <tr><td className="px-4 py-3 font-medium">Fashion specialization</td><td className="px-4 py-3 text-blue-800 font-bold">Yes</td><td className="px-4 py-3 text-slate-500">Partial</td><td className="px-4 py-3 text-slate-500">Partial</td></tr>
                </tbody>
              </table>
            </div>
            <p className="text-xs text-slate-500 mt-3">
              See full comparisons: <Link to="/vs/anaplan" className="text-blue-600 hover:underline">Getmyplan vs Anaplan</Link>{" | "}
              <Link to="/vs/blue-yonder" className="text-blue-600 hover:underline">Getmyplan vs Blue Yonder</Link>
            </p>
          </section>

          {/* FAQ */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">FAQ: AI Demand Planning</h2>
            <div className="space-y-5">
              {[
                ["How accurate is AI demand planning?", "Getmyplan achieves 91% forecast accuracy using a 3-model ensemble ML approach (Holt-Winters + Random Forest + Seasonal Decomposition)."],
                ["How long does implementation take?", "From zero to insights in 15 minutes. Just upload your 7 CSV files \u2014 no technical skills required."],
                ["What data do I need?", "7 CSV files: Style Master, Sales (12+ months historical), Inventory, Stores, and optional marketing/price data. Auto-validation runs instantly."],
                ["Is there a free trial?", "Yes. 7-day free trial with no credit card required. Cancel anytime."],
                ["Does it work with my existing ERP?", "Yes. Getmyplan supports CSV/Excel uploads, SFTP integration, and REST API for custom integrations."],
              ].map(([q, a]) => (
                <div key={q}>
                  <h3 className="text-sm font-semibold text-slate-800 mb-1">{q}</h3>
                  <p className="text-sm text-slate-600">{a}</p>
                </div>
              ))}
            </div>
          </section>

          {/* CTA */}
          <div className="text-center py-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
            <p className="text-lg font-semibold text-slate-800 mb-3">Ready to achieve 91% forecast accuracy?</p>
            <Link to="/signup" className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition" data-testid="ai-planning-cta">
              Start Your 7-Day Free Trial &rarr;
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    </>
  );
}
