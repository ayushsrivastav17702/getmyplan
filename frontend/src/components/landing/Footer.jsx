import { Link } from "react-router-dom";

const FOOTER_COLS = [
  { title: "Product", links: [
    { label: "Demand Planning", href: "/products/demand-planning" },
    { label: "Buy Planning", href: "/products/buy-planning" },
    { label: "Allocation & Replenishment", href: "/products/allocation-replenishment" },
    { label: "Assortment Planning", href: "/products/assortment-planning" },
    { label: "Merchandise Financial Planning", href: "/products/merchandise-financial-planning" },
  ]},
  { title: "Solutions", links: [
    { label: "Fashion Retail", href: "/solutions/fashion-retail" },
    { label: "Luxury Goods", href: "/solutions/luxury-goods" },
    { label: "Fast Fashion", href: "/solutions/fast-fashion" },
    { label: "D2C Brands", href: "/solutions/d2c-brands" },
    { label: "Multi-Channel Retail", href: "/solutions/multi-channel-retail" },
  ]},
  { title: "Resources", links: [
    { label: "Help Center", href: "/help" },
    { label: "Blog", href: "/blog" },
    { label: "API Reference", href: "/resources/api-reference" },
  ]},
  { title: "Company", links: [
    { label: "Contact", href: "#" },
    { label: "Trust Center", href: "#" },
    { label: "Privacy", href: "/privacy" },
    { label: "Terms", href: "/terms" },
  ]},
  { title: "Compare", links: [
    { label: "vs Excel", href: "#" }, { label: "vs ERP", href: "#" },
    { label: "vs Anaplan", href: "#" }, { label: "vs Blue Yonder", href: "#" },
  ]},
];

export default function Footer() {
  return (
    <footer className="relative border-t border-indigo-500/10 bg-[#0a0e27]/90" data-testid="landing-footer">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-8 mb-10">
          {FOOTER_COLS.map((col) => (
            <div key={col.title}>
              <h4 className="text-sm font-semibold text-indigo-400 mb-4">{col.title}</h4>
              <ul className="space-y-2">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <Link to={link.href} className="text-sm text-slate-400 hover:text-indigo-300 transition-colors">{link.label}</Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="border-t border-indigo-500/10 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>2026 GetMyPlan. All rights reserved.</p>
          <div className="flex gap-4">
            <a href="#" className="hover:text-slate-300 transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-slate-300 transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-slate-300 transition-colors">Security</a>
            <a href="#" className="hover:text-slate-300 transition-colors">GDPR</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
