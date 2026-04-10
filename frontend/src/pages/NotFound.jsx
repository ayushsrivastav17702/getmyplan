import { Helmet } from "react-helmet-async";
import { Link, useLocation } from "react-router-dom";
import { ArrowLeft, Search, Home, FileQuestion } from "lucide-react";

export default function NotFound() {
  const location = useLocation();

  return (
    <>
      <Helmet>
        <title>Page Not Found - Getmyplan</title>
        <meta name="description" content="The page you're looking for doesn't exist. Navigate back to Getmyplan's AI demand forecasting platform." />
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      <div className="min-h-screen bg-white flex items-center justify-center px-4" data-testid="not-found-page">
        <div className="max-w-md w-full text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-slate-100 rounded-full mb-6">
            <FileQuestion className="h-8 w-8 text-slate-400" />
          </div>

          <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 mb-3">404</h1>
          <p className="text-lg text-slate-600 mb-2">Page not found</p>
          <p className="text-sm text-slate-400 mb-8">
            The page <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs">{location.pathname}</code> doesn't exist or has been moved.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/"
              data-testid="not-found-home-link"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition text-sm"
            >
              <Home className="h-4 w-4" />
              Go to Homepage
            </Link>
            <Link
              to="/ai-demand-planning"
              data-testid="not-found-guide-link"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 border border-slate-200 text-slate-700 rounded-lg font-medium hover:bg-slate-50 transition text-sm"
            >
              <Search className="h-4 w-4" />
              Read Our Guide
            </Link>
          </div>

          <div className="mt-10 pt-8 border-t border-slate-100">
            <p className="text-xs text-slate-400 mb-3">Looking for something specific?</p>
            <div className="flex flex-wrap justify-center gap-2">
              {[
                { label: "AI Demand Planning", to: "/ai-demand-planning" },
                { label: "Getmyplan vs Anaplan", to: "/vs/anaplan" },
                { label: "Getmyplan vs Blue Yonder", to: "/vs/blue-yonder" },
                { label: "Sign Up", to: "/signup" },
              ].map(link => (
                <Link
                  key={link.to}
                  to={link.to}
                  className="text-xs text-blue-600 hover:underline px-2 py-1 bg-blue-50 rounded"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
