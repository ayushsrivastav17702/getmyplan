import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Brain, ShoppingBag, TrendingUp, Package, BarChart3, Shield, Zap, Clock,
  ArrowRight, Check, Menu, X, ChevronRight, Star, Upload, Search, FileCheck,
  Rocket, Mail, Phone, MapPin
} from "lucide-react";

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.5, ease: "easeOut" }
};

/* ─────────── NAVBAR ─────────── */
const Navbar = () => {
  const [open, setOpen] = useState(false);
  return (
    <nav data-testid="landing-navbar" className="fixed top-0 inset-x-0 z-50 bg-white/70 backdrop-blur-xl border-b border-black/5">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 flex items-center justify-between h-16">
        <span className="text-2xl font-black tracking-tight" style={{ fontFamily: "Cabinet Grotesk, sans-serif", color: "#2563eb" }}>
          GetMyPlan
        </span>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium" style={{ fontFamily: "Satoshi, sans-serif" }}>
          <a href="#features" className="text-neutral-600 hover:text-neutral-900 transition">Features</a>
          <a href="#how-it-works" className="text-neutral-600 hover:text-neutral-900 transition">How It Works</a>
          <a href="#pricing" className="text-neutral-600 hover:text-neutral-900 transition">Pricing</a>
          <a href="#testimonials" className="text-neutral-600 hover:text-neutral-900 transition">Customers</a>
          <Link to="/login" data-testid="nav-login-btn" className="text-neutral-700 hover:text-neutral-900 transition">Login</Link>
          <Link
            to="/signup"
            data-testid="nav-signup-btn"
            className="bg-[#2563eb] text-white px-5 py-2 rounded-full font-medium hover:bg-[#4f46e5] transition-all hover:-translate-y-0.5 shadow-lg shadow-blue-500/25"
          >
            Start Free Trial
          </Link>
        </div>
        <button className="md:hidden" onClick={() => setOpen(!open)} data-testid="mobile-nav-toggle">
          {open ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>
      {open && (
        <div className="md:hidden bg-white border-t border-black/5 px-6 pb-6 space-y-3" style={{ fontFamily: "Satoshi, sans-serif" }}>
          <a href="#features" onClick={() => setOpen(false)} className="block py-2 text-neutral-700">Features</a>
          <a href="#how-it-works" onClick={() => setOpen(false)} className="block py-2 text-neutral-700">How It Works</a>
          <a href="#pricing" onClick={() => setOpen(false)} className="block py-2 text-neutral-700">Pricing</a>
          <a href="#testimonials" onClick={() => setOpen(false)} className="block py-2 text-neutral-700">Customers</a>
          <Link to="/login" onClick={() => setOpen(false)} className="block py-2 text-neutral-700">Login</Link>
          <Link to="/signup" onClick={() => setOpen(false)} className="block py-2.5 text-center bg-[#2563eb] text-white rounded-full font-medium">Start Free Trial</Link>
        </div>
      )}
    </nav>
  );
};

/* ─────────── HERO ─────────── */
const Hero = () => (
  <section data-testid="hero-section" className="pt-28 pb-20 sm:pt-36 sm:pb-28 px-6 bg-[#fafafa] relative overflow-hidden">
    <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
      <motion.div {...fadeUp}>
        <span className="text-xs font-bold tracking-[0.2em] uppercase text-[#2563eb] mb-4 block" style={{ fontFamily: "Satoshi, sans-serif" }}>
          AI-Powered Demand Planning
        </span>
        <h1
          className="text-4xl sm:text-5xl lg:text-6xl tracking-tighter font-black leading-[1.05] text-[#0a0a0a]"
          style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}
        >
          Stop guessing.<br />
          <span className="text-[#2563eb]">Start planning</span> with AI.
        </h1>
        <p className="mt-6 text-lg leading-relaxed text-[#525252] max-w-lg" style={{ fontFamily: "Satoshi, sans-serif" }}>
          GetMyPlan uses 3-model ensemble ML to forecast demand with 91% accuracy.
          Upload your data, get actionable buy plans in 15 minutes. No consultants, no Excel.
        </p>
        <div className="mt-8 flex flex-wrap gap-4">
          <Link
            to="/signup"
            data-testid="hero-signup-btn"
            className="inline-flex items-center gap-2 bg-[#2563eb] text-white px-7 py-3.5 rounded-full font-medium hover:bg-[#4f46e5] transition-all hover:-translate-y-0.5 shadow-lg shadow-blue-500/25"
            style={{ fontFamily: "Satoshi, sans-serif" }}
          >
            Start Free Trial <ArrowRight size={18} />
          </Link>
          <a
            href="#features"
            className="inline-flex items-center gap-2 bg-white text-[#0a0a0a] border border-black/10 px-7 py-3.5 rounded-full font-medium hover:bg-black/5 transition-all"
            style={{ fontFamily: "Satoshi, sans-serif" }}
          >
            See Features
          </a>
        </div>
        <div className="mt-8 flex flex-wrap gap-6 text-sm text-[#525252]" style={{ fontFamily: "Satoshi, sans-serif" }}>
          <span className="flex items-center gap-2"><Check size={16} className="text-green-500" /> No credit card required</span>
          <span className="flex items-center gap-2"><Check size={16} className="text-green-500" /> 7-day free trial</span>
          <span className="flex items-center gap-2"><Check size={16} className="text-green-500" /> Cancel anytime</span>
        </div>
      </motion.div>
      <motion.div {...fadeUp} transition={{ duration: 0.5, delay: 0.15 }} className="relative hidden lg:block">
        <div className="rounded-[32px] overflow-hidden shadow-2xl shadow-blue-500/10 border border-black/5">
          <img
            src="https://static.prod-images.emergentagent.com/jobs/21697566-4f36-4e78-b414-71f3602c796e/images/50d31835ab63300b16f5667f742c693c54f447be6bd4b26cb2760023e3733b17.png"
            alt="GetMyPlan Dashboard"
            className="w-full object-cover"
          />
        </div>
      </motion.div>
    </div>
  </section>
);

/* ─────────── STATS BAR ─────────── */
const stats = [
  { value: "91%", label: "Forecast Accuracy" },
  { value: "33", label: "Analytics Features" },
  { value: "15 min", label: "Time to First Insight" },
  { value: "3", label: "ML Models Ensemble" },
];

const StatsBar = () => (
  <section data-testid="stats-section" className="py-12 bg-white border-y border-black/5">
    <div className="max-w-7xl mx-auto px-6 lg:px-8 grid grid-cols-2 md:grid-cols-4 gap-8">
      {stats.map((s, i) => (
        <motion.div key={i} {...fadeUp} transition={{ delay: i * 0.08 }} className="text-center">
          <div className="text-3xl sm:text-4xl font-black text-[#2563eb]" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>{s.value}</div>
          <div className="mt-1 text-sm text-[#525252] font-medium" style={{ fontFamily: "Satoshi, sans-serif" }}>{s.label}</div>
        </motion.div>
      ))}
    </div>
  </section>
);

/* ─────────── FEATURES ─────────── */
const features = [
  { icon: Brain, title: "AI Demand Forecasting", desc: "3-model ensemble (Holt-Winters + Random Forest + Seasonal Decomposition) with 12-month horizon and confidence intervals.", color: "bg-blue-50 text-blue-600" },
  { icon: ShoppingBag, title: "Buy Plan Generator", desc: "Set revenue targets, select categories, configure channel splits. ML generates optimal buy quantities per SKU.", color: "bg-emerald-50 text-emerald-600" },
  { icon: TrendingUp, title: "Stock-Out Prediction", desc: "Real-time risk scoring with 4 severity levels. Get alerts before you run out of bestsellers.", color: "bg-orange-50 text-orange-600" },
  { icon: Package, title: "Inventory Optimization", desc: "Days-on-Hand analysis, replenishment planning, inter-store transfer optimization.", color: "bg-purple-50 text-purple-600" },
  { icon: BarChart3, title: "Executive Dashboard", desc: "Health Score, KPI cards, revenue trends, critical alerts. Export PDF or Excel with one click.", color: "bg-rose-50 text-rose-600" },
  { icon: Shield, title: "Enterprise Security", desc: "Per-tenant DB isolation, rate limiting, HSTS, CSP headers, NoSQL injection prevention. RBAC with 11 roles.", color: "bg-indigo-50 text-indigo-600" },
  { icon: Zap, title: "Multi-Channel Analytics", desc: "Amazon, Flipkart, Myntra, Ajio, Nykaa marketplace support. Channel-split forecasting and regional analytics.", color: "bg-amber-50 text-amber-600" },
  { icon: Clock, title: "Automated Replenishment", desc: "Statistical reorder points with safety stock. 5-tab planner: Reorder, Quantity, Transfer, Run, Orders.", color: "bg-teal-50 text-teal-600" },
];

const Features = () => (
  <section id="features" data-testid="features-section" className="py-24 sm:py-32 bg-[#fafafa] relative">
    <div className="max-w-7xl mx-auto px-6 lg:px-8">
      <motion.div {...fadeUp} className="text-center mb-16">
        <span className="text-xs font-bold tracking-[0.2em] uppercase text-[#2563eb]" style={{ fontFamily: "Satoshi, sans-serif" }}>Features</span>
        <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl tracking-tight font-bold text-[#0a0a0a]" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>
          Everything you need to<br className="hidden sm:block" /> plan smarter
        </h2>
      </motion.div>

      {/* Bento grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map((f, i) => {
          const Icon = f.icon;
          const isLarge = i < 2;
          return (
            <motion.div
              key={i}
              {...fadeUp}
              transition={{ delay: i * 0.06 }}
              className={`bg-white rounded-2xl p-7 border border-black/[0.06] shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1 ${isLarge ? "lg:col-span-2" : ""}`}
            >
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-5 ${f.color}`}>
                <Icon size={22} strokeWidth={1.5} />
              </div>
              <h3 className="text-xl font-semibold text-[#0a0a0a] mb-2" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>{f.title}</h3>
              <p className="text-[#525252] text-sm leading-relaxed" style={{ fontFamily: "Satoshi, sans-serif" }}>{f.desc}</p>
            </motion.div>
          );
        })}
      </div>
    </div>
  </section>
);

/* ─────────── HOW IT WORKS ─────────── */
const steps = [
  { icon: Upload, title: "Upload Data", desc: "Upload 7 CSV files — Style Master, Sales, Inventory, Stores. Auto-validation runs instantly." },
  { icon: Search, title: "AI Analyzes", desc: "3 ML models process your data: gap analysis, stock-out detection, demand forecasting." },
  { icon: FileCheck, title: "Get Buy Plan", desc: "Set revenue target, let AI calculate what to buy, quantities, and channel splits." },
  { icon: Rocket, title: "Execute & Track", desc: "Export Excel workbook, share with procurement. Monitor via live Executive Dashboard." },
];

const HowItWorks = () => (
  <section id="how-it-works" data-testid="how-it-works-section" className="py-24 sm:py-32 bg-white">
    <div className="max-w-7xl mx-auto px-6 lg:px-8">
      <motion.div {...fadeUp} className="text-center mb-16">
        <span className="text-xs font-bold tracking-[0.2em] uppercase text-[#2563eb]" style={{ fontFamily: "Satoshi, sans-serif" }}>How It Works</span>
        <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl tracking-tight font-bold text-[#0a0a0a]" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>
          From zero to insights<br className="hidden sm:block" /> in 15 minutes
        </h2>
      </motion.div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
        {steps.map((step, i) => {
          const Icon = step.icon;
          return (
            <motion.div key={i} {...fadeUp} transition={{ delay: i * 0.1 }} className="relative">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-[#2563eb] text-white flex items-center justify-center text-sm font-bold" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>
                  {i + 1}
                </div>
                {i < 3 && <ChevronRight size={18} className="text-neutral-300 hidden lg:block absolute right-0 top-3" />}
              </div>
              <div className="w-11 h-11 rounded-xl bg-blue-50 text-[#2563eb] flex items-center justify-center mb-4">
                <Icon size={20} strokeWidth={1.5} />
              </div>
              <h3 className="text-lg font-semibold text-[#0a0a0a] mb-2" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>{step.title}</h3>
              <p className="text-sm text-[#525252] leading-relaxed" style={{ fontFamily: "Satoshi, sans-serif" }}>{step.desc}</p>
            </motion.div>
          );
        })}
      </div>

      <motion.div {...fadeUp} className="mt-16 rounded-2xl overflow-hidden border border-black/5 shadow-sm">
        <img
          src="https://images.unsplash.com/photo-1761952199686-e5d0f76e4f5e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NDh8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwcmV0YWlsJTIwd2FyZWhvdXNlJTIwaW52ZW50b3J5fGVufDB8fHx8MTc3NTU2MTMxOXww&ixlib=rb-4.1.0&q=85"
          alt="Fashion retail warehouse inventory"
          className="w-full h-64 object-cover"
        />
      </motion.div>
    </div>
  </section>
);

/* ─────────── PRICING ─────────── */
const plans = [
  {
    name: "Starter", price: "4,999", period: "/mo", yearly: "49,999/yr",
    desc: "For growing D2C brands",
    features: ["Up to 10 stores", "3 users", "All 33 analytics features", "CSV/Excel upload", "Email support", "7-day free trial"],
    popular: false
  },
  {
    name: "Professional", price: "9,999", period: "/mo", yearly: "99,999/yr",
    desc: "For multi-channel retailers",
    features: ["Up to 50 stores", "10 users", "AI demand forecasting", "Buy plan generator", "SFTP integration", "Priority support", "API access", "Multi-channel sync"],
    popular: true
  },
  {
    name: "Enterprise", price: "Custom", period: "", yearly: "Contact us",
    desc: "For large retail operations",
    features: ["Unlimited stores", "Unlimited users", "Dedicated account manager", "Custom integrations", "SLA guarantee", "SSO / SAML", "On-premise option", "24/7 support"],
    popular: false
  },
];

const Pricing = () => (
  <section id="pricing" data-testid="pricing-section" className="py-24 sm:py-32 bg-[#fafafa]">
    <div className="max-w-7xl mx-auto px-6 lg:px-8">
      <motion.div {...fadeUp} className="text-center mb-16">
        <span className="text-xs font-bold tracking-[0.2em] uppercase text-[#2563eb]" style={{ fontFamily: "Satoshi, sans-serif" }}>Pricing</span>
        <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl tracking-tight font-bold text-[#0a0a0a]" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>
          Simple, transparent pricing
        </h2>
        <p className="mt-4 text-lg text-[#525252]" style={{ fontFamily: "Satoshi, sans-serif" }}>Start free. Upgrade when you need more.</p>
      </motion.div>

      <div className="grid md:grid-cols-3 gap-8 items-start">
        {plans.map((plan, i) => (
          <motion.div
            key={i}
            {...fadeUp}
            transition={{ delay: i * 0.1 }}
            className={`rounded-2xl p-8 transition-all duration-300 ${
              plan.popular
                ? "bg-[#2563eb] text-white shadow-xl shadow-blue-500/20 ring-2 ring-blue-400/30 scale-[1.03]"
                : "bg-white text-[#0a0a0a] border border-black/[0.06] shadow-sm hover:shadow-md"
            }`}
          >
            {plan.popular && (
              <span className="inline-block px-3 py-1 bg-white/20 rounded-full text-xs font-bold tracking-wide mb-4">MOST POPULAR</span>
            )}
            <h3 className="text-2xl font-bold" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>{plan.name}</h3>
            <p className={`text-sm mt-1 ${plan.popular ? "text-white/70" : "text-[#525252]"}`} style={{ fontFamily: "Satoshi, sans-serif" }}>{plan.desc}</p>
            <div className="mt-5">
              <span className="text-4xl font-black" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>
                {plan.price !== "Custom" ? `₹${plan.price}` : plan.price}
              </span>
              <span className={`text-sm ${plan.popular ? "text-white/60" : "text-[#525252]"}`}>{plan.period}</span>
            </div>
            <p className={`text-xs mt-1 ${plan.popular ? "text-white/50" : "text-neutral-400"}`} style={{ fontFamily: "Satoshi, sans-serif" }}>
              Billed yearly: {plan.yearly}
            </p>
            <ul className="mt-6 space-y-3">
              {plan.features.map((f, fi) => (
                <li key={fi} className="flex items-center gap-2.5 text-sm" style={{ fontFamily: "Satoshi, sans-serif" }}>
                  <Check size={15} className={plan.popular ? "text-white/80" : "text-[#2563eb]"} />
                  {f}
                </li>
              ))}
            </ul>
            <Link
              to={plan.name === "Enterprise" ? "/signup" : "/signup"}
              data-testid={`pricing-cta-${plan.name.toLowerCase()}`}
              className={`mt-8 block text-center py-3 rounded-full font-medium transition-all ${
                plan.popular
                  ? "bg-white text-[#2563eb] hover:bg-blue-50"
                  : "bg-[#2563eb] text-white hover:bg-[#4f46e5] shadow-lg shadow-blue-500/25"
              }`}
              style={{ fontFamily: "Satoshi, sans-serif" }}
            >
              {plan.name === "Enterprise" ? "Contact Sales" : "Start Free Trial"}
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  </section>
);

/* ─────────── TESTIMONIALS ─────────── */
const testimonials = [
  {
    name: "Rahul Sharma",
    role: "CEO, FashionHub",
    quote: "GetMyPlan reduced our stockouts by 40% and increased revenue by 25%. The AI forecasts are incredibly accurate.",
    img: "https://images.unsplash.com/photo-1584940121258-c2553b66a739?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxODd8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwZXhlY3V0aXZlJTIwcG9ydHJhaXR8ZW58MHx8fHwxNzc1NTYxMzE5fDA&ixlib=rb-4.1.0&q=85"
  },
  {
    name: "Priya Patel",
    role: "Head of Merchandising, StyleStore",
    quote: "The buy plan generator saves us 2 days every week. We went from Excel guesswork to ML-powered buy plans overnight.",
    img: "https://images.unsplash.com/photo-1582274528667-1e8a10ded835?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxODd8MHwxfHNlYXJjaHwyfHxmYXNoaW9uJTIwZXhlY3V0aXZlJTIwcG9ydHJhaXR8ZW58MHx8fHwxNzc1NTYxMzE5fDA&ixlib=rb-4.1.0&q=85"
  },
  {
    name: "Amit Kumar",
    role: "Operations Director, TrendyWear",
    quote: "Best investment for our supply chain. ROI was evident within the first month. The explainable AI is a game changer.",
    img: "https://images.unsplash.com/photo-1584554376766-ac0f2c65e949?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxODd8MHwxfHNlYXJjaHwzfHxmYXNoaW9uJTIwZXhlY3V0aXZlJTIwcG9ydHJhaXR8ZW58MHx8fHwxNzc1NTYxMzE5fDA&ixlib=rb-4.1.0&q=85"
  },
];

const Testimonials = () => (
  <section id="testimonials" data-testid="testimonials-section" className="py-24 sm:py-32 bg-white">
    <div className="max-w-7xl mx-auto px-6 lg:px-8">
      <motion.div {...fadeUp} className="text-center mb-16">
        <span className="text-xs font-bold tracking-[0.2em] uppercase text-[#2563eb]" style={{ fontFamily: "Satoshi, sans-serif" }}>Customers</span>
        <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl tracking-tight font-bold text-[#0a0a0a]" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>
          Trusted by fashion retailers
        </h2>
      </motion.div>
      <div className="grid md:grid-cols-3 gap-8">
        {testimonials.map((t, i) => (
          <motion.div key={i} {...fadeUp} transition={{ delay: i * 0.1 }} className="bg-[#fafafa] rounded-2xl p-7 border border-black/[0.04]">
            <div className="flex gap-1 mb-5">
              {[...Array(5)].map((_, si) => <Star key={si} size={16} className="fill-amber-400 text-amber-400" />)}
            </div>
            <p className="text-[#0a0a0a] text-sm leading-relaxed mb-6" style={{ fontFamily: "Satoshi, sans-serif" }}>
              "{t.quote}"
            </p>
            <div className="flex items-center gap-3">
              <img src={t.img} alt={t.name} className="w-10 h-10 rounded-full object-cover" />
              <div>
                <p className="text-sm font-semibold text-[#0a0a0a]" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>{t.name}</p>
                <p className="text-xs text-[#525252]" style={{ fontFamily: "Satoshi, sans-serif" }}>{t.role}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  </section>
);

/* ─────────── CTA BANNER ─────────── */
const CtaBanner = () => (
  <section data-testid="cta-banner" className="py-20 bg-[#2563eb] relative overflow-hidden">
    <div className="absolute inset-0 opacity-10">
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-white rounded-full blur-3xl" />
      <div className="absolute bottom-0 right-1/4 w-72 h-72 bg-white rounded-full blur-3xl" />
    </div>
    <div className="max-w-4xl mx-auto px-6 text-center relative">
      <motion.div {...fadeUp}>
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>
          Ready to stop losing revenue to stockouts?
        </h2>
        <p className="mt-4 text-lg text-white/70" style={{ fontFamily: "Satoshi, sans-serif" }}>
          Join 500+ fashion brands using GetMyPlan to plan smarter.
        </p>
        <Link
          to="/signup"
          data-testid="cta-banner-signup"
          className="inline-flex items-center gap-2 mt-8 bg-white text-[#2563eb] px-8 py-3.5 rounded-full font-medium hover:bg-blue-50 transition-all hover:-translate-y-0.5 shadow-xl"
          style={{ fontFamily: "Satoshi, sans-serif" }}
        >
          Start Your Free 7-Day Trial <ArrowRight size={18} />
        </Link>
      </motion.div>
    </div>
  </section>
);

/* ─────────── FOOTER ─────────── */
const Footer = () => (
  <footer data-testid="footer" className="bg-[#0a0a0a] text-white pt-16 pb-8">
    <div className="max-w-7xl mx-auto px-6 lg:px-8">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-10">
        <div>
          <span className="text-xl font-black tracking-tight" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>GetMyPlan</span>
          <p className="mt-3 text-sm text-neutral-400 leading-relaxed" style={{ fontFamily: "Satoshi, sans-serif" }}>
            AI-powered demand planning for fashion retailers. Forecast accurately, prevent stockouts, optimize inventory.
          </p>
        </div>
        <div>
          <h4 className="font-semibold text-sm mb-4" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>Product</h4>
          <ul className="space-y-2.5 text-sm text-neutral-400" style={{ fontFamily: "Satoshi, sans-serif" }}>
            <li><a href="#features" className="hover:text-white transition">Features</a></li>
            <li><a href="#pricing" className="hover:text-white transition">Pricing</a></li>
            <li><a href="#how-it-works" className="hover:text-white transition">How It Works</a></li>
            <li><Link to="/signup" className="hover:text-white transition">Start Trial</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold text-sm mb-4" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>Company</h4>
          <ul className="space-y-2.5 text-sm text-neutral-400" style={{ fontFamily: "Satoshi, sans-serif" }}>
            <li><a href="#" className="hover:text-white transition">About</a></li>
            <li><a href="#" className="hover:text-white transition">Blog</a></li>
            <li><a href="#" className="hover:text-white transition">Careers</a></li>
            <li><a href="#" className="hover:text-white transition">Contact</a></li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold text-sm mb-4" style={{ fontFamily: "Cabinet Grotesk, sans-serif" }}>Contact</h4>
          <ul className="space-y-2.5 text-sm text-neutral-400" style={{ fontFamily: "Satoshi, sans-serif" }}>
            <li className="flex items-center gap-2"><Mail size={14} /> <a href="mailto:info@getmyplan.in" className="hover:text-white transition">info@getmyplan.in</a></li>
            <li className="flex items-center gap-2"><Phone size={14} /> <span>+91-XXXXXXXXXX</span></li>
            <li className="flex items-center gap-2"><MapPin size={14} /> <span>Mumbai, India</span></li>
          </ul>
        </div>
      </div>
      <div className="mt-12 pt-8 border-t border-neutral-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-neutral-500" style={{ fontFamily: "Satoshi, sans-serif" }}>
        <p>&copy; 2026 GetMyPlan. All rights reserved.</p>
        <div className="flex gap-6">
          <a href="#" className="hover:text-white transition">Privacy Policy</a>
          <a href="#" className="hover:text-white transition">Terms of Service</a>
          <a href="#" className="hover:text-white transition">Security</a>
        </div>
      </div>
    </div>
  </footer>
);

/* ─────────── LANDING PAGE ─────────── */
export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <Hero />
      <StatsBar />
      <Features />
      <HowItWorks />
      <Pricing />
      <Testimonials />
      <CtaBanner />
      <Footer />
    </div>
  );
}
