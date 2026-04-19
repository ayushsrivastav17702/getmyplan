import { useState, useEffect, useRef } from "react";
import { Menu, X, ChevronDown } from "lucide-react";
import { Link } from "react-router-dom";
import ContactModal from "./ContactModal";

const PRODUCTS = [
  { label: "Planning Suite", items: [
    { href: "/products/demand-planning", icon: "chart", label: "Demand Planning" },
    { href: "/products/buy-planning", icon: "cart", label: "Buy Planning" },
    { href: "/products/allocation-replenishment", icon: "box", label: "Allocation & Replenishment" },
    { href: "/products/assortment-planning", icon: "grid", label: "Assortment Planning" },
  ]},
  { label: "Advanced Planning", items: [
    { href: "/products/integrated-business-planning", icon: "refresh", label: "Integrated Business Planning" },
    { href: "/products/inventory-planning", icon: "clipboard", label: "Inventory Planning" },
    { href: "/products/merchandise-financial-planning", icon: "dollar", label: "Merchandise Financial Planning" },
    { href: "/products/otb-wssi", icon: "trending", label: "OTB / WSSI" },
    { href: "/products/range-assortment", icon: "target", label: "Range & Assortment" },
  ]},
];

const SOLUTIONS = [
  { href: "/solutions/fashion-retail", label: "Fashion Retail" },
  { href: "/solutions/luxury-goods", label: "Luxury Goods" },
  { href: "/solutions/fast-fashion", label: "Fast Fashion" },
  { href: "/solutions/d2c-brands", label: "D2C Brands" },
  { href: "/solutions/multi-channel-retail", label: "Multi-Channel Retail" },
];

const INDUSTRIES = [
  { href: "/industries/apparel", label: "Apparel" },
  { href: "/industries/footwear", label: "Footwear" },
  { href: "/industries/accessories", label: "Accessories" },
  { href: "/industries/beauty-cosmetics", label: "Beauty & Cosmetics" },
  { href: "/industries/home-living", label: "Home & Living" },
];

const RESOURCES = [
  { href: "/help", label: "Help Center" },
  { href: "/blog", label: "Blog" },
  { href: "/resources/api-reference", label: "API Reference" },
];

const ICON_MAP = {
  chart: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>,
  cart: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" /></svg>,
  box: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>,
  grid: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>,
  refresh: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>,
  clipboard: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>,
  dollar: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  trending: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>,
  target: <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><circle cx="12" cy="12" r="10" strokeWidth={2}/><circle cx="12" cy="12" r="6" strokeWidth={2}/><circle cx="12" cy="12" r="2" strokeWidth={2}/></svg>,
};

function Dropdown({ label, children, wide }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const close = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  return (
    <div ref={ref} className="relative" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <button className="flex items-center gap-1 text-slate-300 hover:text-indigo-400 text-sm font-medium transition-colors py-2" onClick={() => setOpen(!open)}>
        {label} <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className={`absolute top-full left-0 ${wide ? "left-[-200px] w-[680px] grid grid-cols-2 gap-0" : "w-60"} bg-[#0f172a]/95 backdrop-blur-xl border border-indigo-500/20 rounded-xl shadow-2xl shadow-black/40 overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200`}>
          {children}
        </div>
      )}
    </div>
  );
}

function DropdownSection({ title, children }) {
  return (
    <div className="p-4">
      {title && <div className="text-[10px] uppercase tracking-widest text-indigo-400 font-semibold mb-3">{title}</div>}
      <div className="space-y-0.5">{children}</div>
    </div>
  );
}

function DropdownLink({ href, icon, label }) {
  return (
    <Link to={href} className="flex items-center gap-3 px-2 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-white/5 transition-colors text-sm group">
      {icon && <span className="w-7 h-7 rounded-md bg-indigo-500/15 flex items-center justify-center text-indigo-400 group-hover:bg-indigo-500/25 transition-colors">{ICON_MAP[icon] || icon}</span>}
      {label}
    </Link>
  );
}

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [showDemo, setShowDemo] = useState(false);

  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", h);
    return () => window.removeEventListener("scroll", h);
  }, []);

  return (
    <nav data-testid="landing-navbar" className={`fixed top-0 w-full z-50 transition-all duration-300 ${scrolled ? "bg-[#0a0e27]/95 backdrop-blur-xl shadow-lg shadow-black/20" : "bg-transparent"} border-b border-indigo-500/10`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <img src="/getmyplan-logo-sm.png" alt="GetMyPlan" className="h-9 w-auto" data-testid="navbar-logo" onError={(e) => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex"; }} />
            <span style={{ display: "none" }} className="items-center gap-1.5 text-xl font-bold bg-gradient-to-r from-indigo-400 to-rose-400 bg-clip-text text-transparent">GetMyPlan</span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden lg:flex items-center gap-6">
            <Dropdown label="Products" wide>
              {PRODUCTS.map((section) => (
                <DropdownSection key={section.label} title={section.label}>
                  {section.items.map((item) => <DropdownLink key={item.href} {...item} />)}
                </DropdownSection>
              ))}
            </Dropdown>

            <Dropdown label="Solutions">
              <DropdownSection>
                {SOLUTIONS.map((s) => <DropdownLink key={s.label} href={s.href} label={s.label} />)}
              </DropdownSection>
            </Dropdown>

            <Dropdown label="Industries">
              <DropdownSection>
                {INDUSTRIES.map((s) => <DropdownLink key={s.label} href={s.href} label={s.label} />)}
              </DropdownSection>
            </Dropdown>

            <Dropdown label="Resources">
              <DropdownSection>
                {RESOURCES.map((s) => <DropdownLink key={s.label} href={s.href} label={s.label} />)}
              </DropdownSection>
            </Dropdown>

            <a href="#pricing" className="text-slate-300 hover:text-indigo-400 text-sm font-medium transition-colors">Pricing</a>
          </div>

          {/* Desktop CTA */}
          <div className="hidden lg:flex items-center gap-3">
            <Link to="/login" data-testid="nav-login-btn" className="px-4 py-2 text-slate-300 hover:text-white text-sm font-medium transition-colors">Log in</Link>
            <button onClick={() => setShowDemo(true)} data-testid="nav-demo-btn" className="px-4 py-2 border border-indigo-500/50 text-indigo-300 rounded-lg text-sm font-semibold hover:bg-indigo-500/10 transition-all">Request a Demo</button>
            <Link to="/signup" data-testid="nav-signup-btn" className="px-5 py-2 bg-gradient-to-r from-indigo-500 to-rose-500 text-white rounded-lg text-sm font-semibold hover:shadow-lg hover:shadow-indigo-500/25 transition-all hover:-translate-y-0.5">Start Free Trial</Link>
          </div>

          {/* Mobile toggle */}
          <button className="lg:hidden text-slate-300" onClick={() => setMobileOpen(!mobileOpen)} data-testid="mobile-nav-toggle">
            {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileOpen && (
          <div className="lg:hidden pb-6 space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
            <a href="#features" onClick={() => setMobileOpen(false)} className="block py-2 text-slate-300 text-sm">Features</a>
            <a href="#pricing" onClick={() => setMobileOpen(false)} className="block py-2 text-slate-300 text-sm">Pricing</a>
            <Link to="/help" onClick={() => setMobileOpen(false)} className="block py-2 text-slate-300 text-sm">Help Center</Link>
            <Link to="/blog" onClick={() => setMobileOpen(false)} className="block py-2 text-slate-300 text-sm">Blog</Link>
            <div className="pt-3 border-t border-indigo-500/20 space-y-2">
              <Link to="/login" onClick={() => setMobileOpen(false)} className="block py-2 text-slate-300 text-sm">Log in</Link>
              <button onClick={() => { setMobileOpen(false); setShowDemo(true); }} className="block w-full py-2 text-center border border-indigo-500/50 text-indigo-300 rounded-lg text-sm">Request a Demo</button>
              <Link to="/signup" onClick={() => setMobileOpen(false)} className="block py-2 text-center bg-gradient-to-r from-indigo-500 to-rose-500 text-white rounded-lg text-sm font-semibold">Start Free Trial</Link>
            </div>
          </div>
        )}
      </div>
      <ContactModal isOpen={showDemo} onClose={() => setShowDemo(false)} />
    </nav>
  );
}
