import { useState, useEffect } from "react";
import { Menu, X, ChevronDown } from "lucide-react";
import { Link } from "react-router-dom";
import ContactModal from "./ContactModal";

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [showDemo, setShowDemo] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav
      data-testid="landing-navbar"
      className={`fixed top-0 w-full z-50 transition-all duration-300 ${
        scrolled ? "bg-white/95 backdrop-blur-md shadow-lg" : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center gap-2 group">
            <img 
              src="/getmyplan-logo-sm.png" 
              alt="Getmyplan - AI Demand Forecasting for Fashion Retail"
              className="h-10 w-auto"
              data-testid="navbar-logo"
            />
          </Link>

          <div className="hidden md:flex items-center space-x-8">
            <a href="#features" className="text-gray-600 hover:text-gray-900 transition">Features</a>
            <a href="#how-it-works" className="text-gray-600 hover:text-gray-900 transition">How It Works</a>
            <a href="#pricing" className="text-gray-600 hover:text-gray-900 transition">Pricing</a>
            <a href="#customers" className="text-gray-600 hover:text-gray-900 transition">Customers</a>
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                onBlur={() => setTimeout(() => setDropdownOpen(false), 300)}
                className="flex items-center gap-1 text-gray-600 hover:text-gray-900 transition"
                data-testid="nav-resources-dropdown"
              >
                Resources
                <ChevronDown className={`h-4 w-4 transition-transform ${dropdownOpen ? "rotate-180" : ""}`} />
              </button>
              {dropdownOpen && (
                <div className="absolute top-8 right-0 w-48 bg-white rounded-xl shadow-lg py-2 border border-gray-100 animate-fadeIn">
                  <Link to="/help" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Help Center</Link>
                  <Link to="/blog" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">Blog</Link>
                  <a href="/#faq" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">FAQ</a>
                </div>
              )}
            </div>
          </div>

          <div className="hidden md:flex items-center gap-3">
            <Link to="/login" data-testid="nav-login-btn" className="px-4 py-2 text-gray-600 hover:text-gray-900 transition">
              Log in
            </Link>
            <button
              onClick={() => setShowDemo(true)}
              data-testid="nav-demo-btn"
              className="px-4 py-2 border border-blue-600 text-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition"
            >
              Request a Demo
            </button>
            <Link
              to="/signup"
              data-testid="nav-signup-btn"
              className="px-5 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all hover:scale-105"
            >
              Start Free Trial
            </Link>
          </div>

          <button className="md:hidden text-gray-600" onClick={() => setIsOpen(!isOpen)} data-testid="mobile-nav-toggle">
            {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {isOpen && (
          <div className="md:hidden pb-4 space-y-3 animate-fadeIn">
            <a href="#features" onClick={() => setIsOpen(false)} className="block py-2 text-gray-600">Features</a>
            <a href="#how-it-works" onClick={() => setIsOpen(false)} className="block py-2 text-gray-600">How It Works</a>
            <a href="#pricing" onClick={() => setIsOpen(false)} className="block py-2 text-gray-600">Pricing</a>
            <a href="#customers" onClick={() => setIsOpen(false)} className="block py-2 text-gray-600">Customers</a>
            <Link to="/help" onClick={() => setIsOpen(false)} className="block py-2 text-gray-600">Help Center</Link>
            <div className="pt-3 border-t border-gray-100">
              <Link to="/login" onClick={() => setIsOpen(false)} className="block py-2 text-gray-600">Log in</Link>
              <button onClick={() => { setIsOpen(false); setShowDemo(true); }} className="block w-full py-2 text-center border border-blue-600 text-blue-600 rounded-lg mt-2">
                Request a Demo
              </button>
              <Link to="/signup" onClick={() => setIsOpen(false)} className="block py-2 text-center bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg mt-2">
                Start Free Trial
              </Link>
            </div>
          </div>
        )}
      </div>
      <ContactModal isOpen={showDemo} onClose={() => setShowDemo(false)} />
    </nav>
  );
}
