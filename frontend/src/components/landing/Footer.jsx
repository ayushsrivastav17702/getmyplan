import { Mail, MapPin } from "lucide-react";
import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer data-testid="footer" className="bg-gray-900 text-white pt-12 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid sm:grid-cols-2 lg:grid-cols-6 gap-8">
          {/* Brand */}
          <div className="lg:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <img src="/getmyplan-logo-sm.png" alt="Getmyplan" className="h-8 w-auto" data-testid="footer-logo" />
            </div>
            <p className="text-gray-400 text-sm mb-5 max-w-xs leading-relaxed">
              AI-powered demand planning for fashion retailers. Forecast accurately, prevent stockouts, optimize inventory.
            </p>
            {/* Newsletter */}
            <div className="flex gap-2">
              <input
                type="email"
                placeholder="Enter your email"
                data-testid="newsletter-email"
                className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
              />
              <button data-testid="newsletter-submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition">
                Subscribe
              </button>
            </div>
          </div>

          {/* Product */}
          <div>
            <h4 className="font-semibold mb-4">Product</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><a href="#features" className="hover:text-white transition">Features</a></li>
              <li><a href="#pricing" className="hover:text-white transition">Pricing</a></li>
              <li><a href="#how-it-works" className="hover:text-white transition">How It Works</a></li>
              <li><Link to="/signup" className="hover:text-white transition">Start Trial</Link></li>
              <li><Link to="/help" className="hover:text-white transition">Help Center</Link></li>
              <li><a href="#" className="hover:text-white transition">API Reference</a></li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="font-semibold mb-4">Company</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><a href="#" className="hover:text-white transition">About</a></li>
              <li><Link to="/blog" className="hover:text-white transition">Blog</Link></li>
              <li><a href="#" className="hover:text-white transition">Careers</a></li>
              <li><a href="#" className="hover:text-white transition">Press</a></li>
              <li><a href="#" className="hover:text-white transition">Contact</a></li>
            </ul>
          </div>

          {/* Compare */}
          <div className="sm:hidden lg:block">
            <h4 className="font-semibold mb-4">Compare</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><Link to="/vs/anaplan" className="hover:text-white transition">Getmyplan vs Anaplan</Link></li>
              <li><Link to="/vs/blue-yonder" className="hover:text-white transition">Getmyplan vs Blue Yonder</Link></li>
              <li><Link to="/ai-demand-planning" className="hover:text-white transition">AI Demand Planning Guide</Link></li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-semibold mb-4">Contact</h4>
            <ul className="space-y-2.5 text-sm text-gray-400">
              <li className="flex items-center gap-2"><Mail size={14} /> <a href="mailto:info@getmyplan.in" className="hover:text-white transition">info@getmyplan.in</a></li>
              <li className="flex items-center gap-2"><MapPin size={14} /> <span>Serving fashion brands globally</span></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-10 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gray-500">
          <p>&copy; 2026 GetMyPlan. All rights reserved.</p>
          <div className="flex gap-6">
            <Link to="/privacy" data-testid="footer-privacy-link" className="hover:text-white transition">Privacy Policy</Link>
            <Link to="/terms" data-testid="footer-terms-link" className="hover:text-white transition">Terms of Service</Link>
            <a href="#" className="hover:text-white transition">Security</a>
            <a href="#" className="hover:text-white transition">GDPR</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
