import { useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { ArrowLeft, Clock, Calendar, Tag, ChevronRight } from "lucide-react";
import { getBlogBySlug, getRelatedBlogs } from "../../data/blogData";

export default function BlogPost() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const blog = getBlogBySlug(slug);
  const related = getRelatedBlogs(slug);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [slug]);

  // Inject JSON-LD via useEffect (Helmet doesn't handle script children well)
  useEffect(() => {
    if (!blog) return;
    let script = document.getElementById("blog-jsonld");
    if (!script) {
      script = document.createElement("script");
      script.id = "blog-jsonld";
      script.type = "application/ld+json";
      document.head.appendChild(script);
    }
    script.textContent = JSON.stringify({
      "@context": "https://schema.org",
      "@type": "Article",
      headline: blog.title,
      description: blog.metaDescription,
      author: { "@type": "Person", name: "Founder & CEO, GetMyPlan" },
      publisher: { "@type": "Organization", name: "GetMyPlan", url: "https://getmyplan.in" },
      datePublished: "2026-04-11",
      dateModified: "2026-04-11",
      mainEntityOfPage: { "@type": "WebPage", "@id": `https://getmyplan.in/blog/${blog.slug}` },
    });
    return () => { const el = document.getElementById("blog-jsonld"); if (el) el.remove(); };
  }, [blog, slug]);

  if (!blog) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-6xl font-bold text-slate-200 mb-4">404</p>
          <p className="text-slate-500 mb-6">Blog post not found</p>
          <Link to="/blog" className="text-blue-600 hover:underline">Back to Blog</Link>
        </div>
      </div>
    );
  }

  const pageTitle = `${blog.title} | GetMyPlan Blog`;

  return (
    <div className="min-h-screen bg-white" data-testid="blog-post-page">
      <Helmet>
        <title>{pageTitle}</title>
        <meta name="description" content={blog.metaDescription} />
        <link rel="canonical" href={`https://getmyplan.in/blog/${blog.slug}`} />
        <meta property="og:title" content={blog.title} />
        <meta property="og:description" content={blog.metaDescription} />
        <meta property="og:type" content="article" />
        <meta property="og:url" content={`https://getmyplan.in/blog/${blog.slug}`} />
      </Helmet>
      {/* Nav */}
      <nav className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-100">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <button
            onClick={() => navigate("/blog")}
            className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 transition"
            data-testid="blog-back-btn"
          >
            <ArrowLeft size={16} /> All Articles
          </button>
          <div className="flex items-center gap-3">
            <a
              href="/blog/rss.xml"
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 hover:text-orange-500 transition"
              title="RSS Feed"
              data-testid="blog-post-rss-link"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="6.18" cy="17.82" r="2.18"/><path d="M4 4.44v2.83c7.03 0 12.73 5.7 12.73 12.73h2.83c0-8.59-6.97-15.56-15.56-15.56zm0 5.66v2.83c3.9 0 7.07 3.17 7.07 7.07h2.83c0-5.47-4.43-9.9-9.9-9.9z"/></svg>
            </a>
            <Link to="/signup" className="text-sm font-medium text-blue-600 hover:text-blue-700">
              Start Free Trial
            </Link>
            <Link
              to="/"
              className="hidden sm:flex items-center gap-1"
            >
              <img src="/getmyplan-logo-sm.png" alt="GetMyPlan" className="h-7 w-auto" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <header className="bg-gradient-to-b from-slate-50 to-white pt-12 pb-8 border-b border-slate-100">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 bg-blue-50 px-3 py-1 rounded-full" data-testid="blog-category">
              {blog.category}
            </span>
            <span className="flex items-center gap-1 text-xs text-slate-400">
              <Clock size={12} /> {blog.readTime}
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 leading-tight mb-4" data-testid="blog-title">
            {blog.title}
          </h1>
          <p className="text-base text-slate-600 leading-relaxed border-l-4 border-blue-500 pl-4 bg-blue-50/50 py-3 rounded-r" data-testid="blog-tldr">
            <strong>TL;DR:</strong> {blog.tldr}
          </p>
          <div className="flex items-center gap-4 mt-6 text-xs text-slate-400">
            <span className="flex items-center gap-1"><Calendar size={12} /> Published: {blog.publishedDate}</span>
            <span>Last Updated: {blog.lastUpdated}</span>
          </div>
        </div>
      </header>

      {/* Content */}
      <article className="max-w-3xl mx-auto px-4 sm:px-6 py-10">
        <div
          className="blog-content"
          data-testid="blog-content"
          dangerouslySetInnerHTML={{ __html: blog.content }}
        />

        {/* Author */}
        <div className="mt-12 pt-8 border-t border-slate-200">
          <p className="text-sm text-slate-500">Author: <strong>Founder & CEO, GetMyPlan</strong></p>
          <p className="text-sm text-slate-400">Published: {blog.publishedDate}</p>
          <p className="text-sm text-slate-400">Last Updated: {blog.lastUpdated}</p>
        </div>

        {/* CTA */}
        <div className="mt-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-8 text-center text-white" data-testid="blog-cta">
          <h3 className="text-xl font-bold mb-2">Ready to reduce stockouts by 34%?</h3>
          <p className="text-blue-100 text-sm mb-5">14-day free trial. No credit card required. Enterprise-scale sample data included.</p>
          <Link
            to="/signup"
            className="inline-block px-6 py-3 bg-white text-blue-600 font-semibold rounded-lg hover:bg-blue-50 transition"
            data-testid="blog-cta-signup"
          >
            Start Free Trial
          </Link>
        </div>

        {/* Related */}
        {related.length > 0 && (
          <div className="mt-12" data-testid="blog-related">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Related Articles</h3>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {related.map(r => (
                <Link
                  key={r.slug}
                  to={`/blog/${r.slug}`}
                  className="group block p-4 bg-slate-50 rounded-xl border border-slate-100 hover:border-blue-200 hover:shadow-sm transition"
                  data-testid={`related-${r.slug}`}
                >
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-blue-500">{r.category}</span>
                  <h4 className="text-sm font-semibold text-slate-800 mt-1 group-hover:text-blue-600 transition line-clamp-2">
                    {r.title}
                  </h4>
                  <span className="flex items-center gap-1 text-xs text-blue-500 mt-2 opacity-0 group-hover:opacity-100 transition">
                    Read article <ChevronRight size={12} />
                  </span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </article>
    </div>
  );
}
