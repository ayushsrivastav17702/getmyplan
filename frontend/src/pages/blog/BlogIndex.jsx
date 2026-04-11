import { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import { Search, Clock, ChevronRight, ArrowRight, Tag } from "lucide-react";
import { blogs, blogCategories } from "../../data/blogData";

export default function BlogIndex() {
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");

  useEffect(() => {
    window.scrollTo(0, 0);
    document.title = "Blog | GetMyPlan - AI Demand Planning Insights";
    const meta = document.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute("content", "Expert articles on demand planning, inventory optimization, AI forecasting, and retail analytics for fashion brands. Free guides, formulas, and benchmarks.");
  }, []);

  const filtered = useMemo(() => {
    return blogs.filter(b => {
      const matchCat = activeCategory === "All" || b.category === activeCategory;
      const matchSearch = !search || b.title.toLowerCase().includes(search.toLowerCase()) || b.tldr.toLowerCase().includes(search.toLowerCase());
      return matchCat && matchSearch;
    });
  }, [search, activeCategory]);

  const featured = blogs[0]; // Blog 1 as featured

  return (
    <div className="min-h-screen bg-white" data-testid="blog-index-page">
      {/* Nav */}
      <nav className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <img src="/getmyplan-logo-sm.png" alt="GetMyPlan" className="h-8 w-auto" />
          </Link>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm text-slate-600 hover:text-slate-900 transition">Log in</Link>
            <Link to="/signup" className="text-sm font-medium px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
              Start Free Trial
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <header className="bg-gradient-to-b from-slate-900 to-slate-800 text-white pt-16 pb-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4" data-testid="blog-hero-title">
            Demand Planning Insights
          </h1>
          <p className="text-slate-300 text-lg max-w-2xl mx-auto mb-8">
            Expert guides on AI forecasting, inventory optimization, KPI tracking, and retail analytics for fashion brands.
          </p>
          <div className="max-w-xl mx-auto relative">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              data-testid="blog-search"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search articles..."
              className="w-full pl-12 pr-4 py-3 bg-white/10 backdrop-blur border border-white/20 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 focus:bg-white/15 transition"
            />
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
        {/* Category Filters */}
        <div className="flex flex-wrap gap-2 mb-8" data-testid="blog-categories">
          <button
            onClick={() => setActiveCategory("All")}
            className={`px-4 py-2 text-sm font-medium rounded-full border transition ${
              activeCategory === "All"
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white text-slate-600 border-slate-200 hover:border-slate-400"
            }`}
            data-testid="blog-cat-all"
          >
            All ({blogs.length})
          </button>
          {blogCategories.map(cat => {
            const count = blogs.filter(b => b.category === cat).length;
            return (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                data-testid={`blog-cat-${cat.replace(/\s+/g, "-").toLowerCase()}`}
                className={`px-4 py-2 text-sm font-medium rounded-full border transition ${
                  activeCategory === cat
                    ? "bg-slate-900 text-white border-slate-900"
                    : "bg-white text-slate-600 border-slate-200 hover:border-slate-400"
                }`}
              >
                {cat} ({count})
              </button>
            );
          })}
        </div>

        {/* Featured (only when no search and "All" category) */}
        {!search && activeCategory === "All" && (
          <Link
            to={`/blog/${featured.slug}`}
            className="group block mb-10 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl overflow-hidden hover:shadow-lg transition"
            data-testid="blog-featured"
          >
            <div className="p-8 sm:p-10">
              <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 bg-blue-100 px-3 py-1 rounded-full">
                Featured
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 mt-4 mb-3 group-hover:text-blue-700 transition">
                {featured.title}
              </h2>
              <p className="text-slate-600 text-sm leading-relaxed mb-4 line-clamp-3">{featured.tldr}</p>
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1 text-xs text-slate-400"><Clock size={12} /> {featured.readTime}</span>
                <span className="flex items-center gap-1 text-xs text-slate-400"><Tag size={12} /> {featured.category}</span>
                <span className="flex items-center gap-1 text-sm font-medium text-blue-600 ml-auto group-hover:gap-2 transition-all">
                  Read article <ArrowRight size={14} />
                </span>
              </div>
            </div>
          </Link>
        )}

        {/* Blog Grid */}
        {filtered.length === 0 ? (
          <div className="text-center py-16" data-testid="blog-empty">
            <p className="text-slate-400 text-lg">No articles found matching your search.</p>
            <button onClick={() => { setSearch(""); setActiveCategory("All"); }} className="mt-3 text-blue-600 text-sm hover:underline">
              Clear filters
            </button>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="blog-grid">
            {filtered.map(blog => (
              <Link
                key={blog.slug}
                to={`/blog/${blog.slug}`}
                className="group flex flex-col bg-white border border-slate-200 rounded-xl overflow-hidden hover:shadow-md hover:border-blue-200 transition"
                data-testid={`blog-card-${blog.slug}`}
              >
                <div className="p-5 flex-1 flex flex-col">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
                      {blog.category}
                    </span>
                    <span className="text-[10px] text-slate-400 flex items-center gap-1">
                      <Clock size={10} /> {blog.readTime}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900 mb-2 group-hover:text-blue-700 transition line-clamp-2 leading-snug">
                    {blog.title}
                  </h3>
                  <p className="text-xs text-slate-500 line-clamp-3 flex-1 leading-relaxed">
                    {blog.tldr}
                  </p>
                  <div className="flex items-center gap-1 text-xs font-medium text-blue-600 mt-4 opacity-0 group-hover:opacity-100 transition">
                    Read article <ChevronRight size={12} />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Bottom CTA */}
        <div className="mt-16 bg-slate-900 rounded-2xl p-8 sm:p-10 text-center text-white" data-testid="blog-bottom-cta">
          <h3 className="text-2xl font-bold mb-2">Stop losing revenue to stockouts</h3>
          <p className="text-slate-300 text-sm mb-6 max-w-lg mx-auto">
            AI demand planning for fashion retail. 92.7% forecast accuracy. 14-day free trial.
          </p>
          <Link
            to="/signup"
            className="inline-block px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition"
          >
            Start Free Trial
          </Link>
        </div>
      </div>

      {/* Simple Footer */}
      <footer className="border-t border-slate-100 py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <p>&copy; 2026 GetMyPlan. All rights reserved.</p>
          <div className="flex gap-6">
            <Link to="/privacy" className="hover:text-slate-700 transition">Privacy Policy</Link>
            <Link to="/terms" className="hover:text-slate-700 transition">Terms of Service</Link>
            <Link to="/" className="hover:text-slate-700 transition">Home</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
