import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import Navbar from "../components/landing/Navbar";
import Footer from "../components/landing/Footer";
import { getAllProducts } from "../data/productContent";

export default function ProductsListing() {
  const products = getAllProducts();

  return (
    <div className="min-h-screen bg-[#0a0e27]" data-testid="products-listing-page">
      <Helmet>
        <title>All Products | GetMyPlan Enterprise Platform</title>
        <meta
          name="description"
          content="Explore all GetMyPlan products: Demand Planning, Buy Planning, Allocation & Replenishment, Assortment Planning, Inventory Planning, MFP, OTB/WSSI, IBP, and Range & Assortment."
        />
      </Helmet>

      <Navbar />

      <main className="pt-28 pb-16">
        <section className="max-w-6xl mx-auto px-4 sm:px-6">
          {/* Header */}
          <div className="text-center max-w-3xl mx-auto mb-14">
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-sm font-medium mb-6">
              Complete Product Suite
            </span>
            <h1 className="text-3xl sm:text-5xl font-extrabold mb-4" data-testid="products-listing-title">
              <span className="bg-gradient-to-r from-indigo-400 to-rose-400 bg-clip-text text-transparent">
                All Products
              </span>
            </h1>
            <p className="text-lg text-slate-400">
              Nine AI-powered planning products for fashion retail — from demand forecasting to
              merchandise financial planning.
            </p>
          </div>

          {/* Grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {products.map((p) => (
              <Link
                key={p.slug}
                to={`/products/${p.slug}`}
                className="group bg-white/[0.04] border border-indigo-500/10 rounded-2xl p-6 hover:bg-white/[0.07] hover:border-indigo-500/40 hover:-translate-y-0.5 transition-all"
                data-testid={`product-listing-card-${p.slug}`}
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${p.heroGradient} flex items-center justify-center text-2xl mb-4`}>
                  {p.icon}
                </div>
                <h2 className="text-lg font-semibold text-white mb-2">{p.title}</h2>
                <p className="text-sm text-slate-400 leading-relaxed mb-4 line-clamp-3">
                  {p.tagline}
                </p>
                <span className="inline-flex items-center gap-1.5 text-sm text-indigo-400 group-hover:text-indigo-300">
                  Learn more
                  <span className="group-hover:translate-x-1 transition-transform">→</span>
                </span>
              </Link>
            ))}
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
