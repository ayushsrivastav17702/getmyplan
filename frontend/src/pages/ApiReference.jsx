import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import Navbar from "../components/landing/Navbar";
import Footer from "../components/landing/Footer";

function Method({ verb, path, description }) {
  const verbClass = {
    GET: "bg-blue-500/15 border-blue-500/30 text-blue-300",
    POST: "bg-emerald-500/15 border-emerald-500/30 text-emerald-300",
    PUT: "bg-amber-500/15 border-amber-500/30 text-amber-300",
    DELETE: "bg-rose-500/15 border-rose-500/30 text-rose-300",
  }[verb] || "bg-slate-500/15 border-slate-500/30 text-slate-300";

  return (
    <div className="mb-6 last:mb-0">
      <div className="flex items-center gap-3 mb-2">
        <span className={`px-2 py-0.5 text-xs font-bold rounded border ${verbClass}`}>{verb}</span>
        <code className="text-slate-200 font-mono text-sm">{path}</code>
      </div>
      <p className="text-sm text-slate-400">{description}</p>
    </div>
  );
}

function Section({ id, title, children }) {
  return (
    <section id={id} className="bg-white/[0.04] border border-indigo-500/10 rounded-2xl p-6 sm:p-8 mb-6" data-testid={`api-section-${id}`}>
      <h2 className="text-xl sm:text-2xl font-bold text-white mb-4">{title}</h2>
      {children}
    </section>
  );
}

export default function ApiReference() {
  return (
    <div className="min-h-screen bg-[#0a0e27]" data-testid="api-reference-page">
      <Helmet>
        <title>API Reference | GetMyPlan Developer Docs</title>
        <meta name="description" content="GetMyPlan REST API documentation. Integrate demand planning and forecasting into your applications." />
        <meta name="keywords" content="GetMyPlan API, demand planning API, retail forecasting API, REST API" />
      </Helmet>

      <Navbar />

      <main className="pt-28 pb-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          {/* Hero */}
          <div className="text-center mb-12">
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-sm font-medium mb-6">
              Developer Docs
            </span>
            <h1 className="text-3xl sm:text-5xl font-extrabold mb-4" data-testid="api-title">
              <span className="bg-gradient-to-r from-indigo-400 to-rose-400 bg-clip-text text-transparent">
                API Reference
              </span>
            </h1>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto">
              Build powerful integrations with GetMyPlan's REST API.
            </p>
          </div>

          {/* Quick Links */}
          <div className="flex flex-wrap justify-center gap-2 mb-10" data-testid="api-quick-links">
            <a href="#auth" className="px-4 py-2 text-sm rounded-lg bg-white/[0.04] border border-white/10 text-slate-300 hover:bg-white/[0.08] hover:text-white transition">Authentication</a>
            <a href="#base-url" className="px-4 py-2 text-sm rounded-lg bg-white/[0.04] border border-white/10 text-slate-300 hover:bg-white/[0.08] hover:text-white transition">Base URL</a>
            <a href="#forecast" className="px-4 py-2 text-sm rounded-lg bg-white/[0.04] border border-white/10 text-slate-300 hover:bg-white/[0.08] hover:text-white transition">Forecasting</a>
            <a href="#inventory" className="px-4 py-2 text-sm rounded-lg bg-white/[0.04] border border-white/10 text-slate-300 hover:bg-white/[0.08] hover:text-white transition">Inventory</a>
            <a href="#buyplans" className="px-4 py-2 text-sm rounded-lg bg-white/[0.04] border border-white/10 text-slate-300 hover:bg-white/[0.08] hover:text-white transition">Buy Plans</a>
            <a href="#rate-limits" className="px-4 py-2 text-sm rounded-lg bg-white/[0.04] border border-white/10 text-slate-300 hover:bg-white/[0.08] hover:text-white transition">Rate Limits</a>
          </div>

          {/* Authentication */}
          <Section id="auth" title="Authentication">
            <p className="text-sm text-slate-400 mb-3">All API requests require a Bearer token in the Authorization header.</p>
            <pre className="bg-black/40 border border-indigo-500/20 rounded-xl p-4 font-mono text-sm text-indigo-300 overflow-x-auto">
{`Authorization: Bearer <your_api_key>`}
            </pre>
          </Section>

          {/* Base URL */}
          <Section id="base-url" title="Base URL">
            <pre className="bg-black/40 border border-indigo-500/20 rounded-xl p-4 font-mono text-sm text-emerald-300 overflow-x-auto">
{`https://api.getmyplan.in/v1/`}
            </pre>
          </Section>

          {/* Forecasting */}
          <Section id="forecast" title="Forecasting API">
            <Method
              verb="POST"
              path="/forecast/generate"
              description="Generate a demand forecast for a list of SKUs and store wedges."
            />
            <pre className="bg-black/40 border border-indigo-500/20 rounded-xl p-4 font-mono text-sm text-slate-200 overflow-x-auto mb-4">
{`{
  "sku_ids": ["SKU-001", "SKU-002"],
  "store_wedges": ["A", "B"],
  "horizon_days": 90
}`}
            </pre>
            <Method
              verb="GET"
              path="/forecast/{sku_id}"
              description="Get the latest forecast for a specific SKU."
            />
          </Section>

          {/* Inventory */}
          <Section id="inventory" title="Inventory API">
            <Method
              verb="POST"
              path="/inventory/upload"
              description="Bulk upload inventory data (CSV or JSON body)."
            />
            <Method
              verb="GET"
              path="/inventory/{store_id}/{sku_id}"
              description="Get the current SOH for a store-SKU combination."
            />
          </Section>

          {/* Buy Plans */}
          <Section id="buyplans" title="Buy Plans API">
            <Method
              verb="POST"
              path="/buy-plans/generate"
              description="Generate a new buy plan using the Full Buy Formula."
            />
            <Method
              verb="GET"
              path="/buy-plans/{plan_id}"
              description="Get details, line items, and approval status for a buy plan."
            />
            <Method
              verb="PUT"
              path="/buy-plans/{plan_id}/approve"
              description="Advance a buy plan through its approval stage."
            />
          </Section>

          {/* Rate Limits */}
          <Section id="rate-limits" title="Rate Limits">
            <ul className="space-y-2 text-sm text-slate-300">
              <li className="flex items-start gap-2"><span className="text-indigo-400 mt-0.5">•</span> 1,000 requests per minute per tenant</li>
              <li className="flex items-start gap-2"><span className="text-indigo-400 mt-0.5">•</span> 10,000 requests per hour per tenant</li>
              <li className="flex items-start gap-2"><span className="text-indigo-400 mt-0.5">•</span> Responses include <code className="text-indigo-300 font-mono text-xs">X-RateLimit-*</code> headers</li>
            </ul>
          </Section>

          {/* CTA */}
          <div className="mt-10 text-center">
            <Link
              to="/signup"
              className="inline-block px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-rose-500 text-white font-semibold hover:shadow-[0_10px_40px_-10px_rgba(99,102,241,0.6)] transition"
              data-testid="api-cta-button"
            >
              Get Your API Key
            </Link>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
