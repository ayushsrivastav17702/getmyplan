import { useState } from "react";
import { Link } from "react-router-dom";
import { API } from "../App";
import {
  Mail, Lock, Building2, Globe, CheckCircle, AlertCircle,
  Loader2, ArrowRight, ArrowLeft, Eye, EyeOff, Rocket
} from "lucide-react";

// Use native fetch for ALL signup calls — completely isolated from axios defaults
async function signupFetch(url, options = {}) {
  let resp;
  try {
    resp = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch (networkErr) {
    throw { message: "Network error — cannot reach server. Please check your connection." };
  }
  let data;
  try {
    data = await resp.json();
  } catch {
    throw { message: `Server returned non-JSON response (HTTP ${resp.status})` };
  }
  if (!resp.ok) throw { response: { status: resp.status, data } };
  return data;
}

const Signup = () => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [subdomainAvailable, setSubdomainAvailable] = useState(null);
  const [checkingSubdomain, setCheckingSubdomain] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState("");
  const [registeredSubdomain, setRegisteredSubdomain] = useState("");
  const [formData, setFormData] = useState({
    company_name: "",
    email: "",
    password: "",
    confirm_password: "",
    subdomain: "",
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError("");
  };

  const checkSubdomain = async (sub) => {
    if (sub.length < 3) { setSubdomainAvailable(null); return; }
    setCheckingSubdomain(true);
    try {
      const data = await signupFetch(`${API}/tenants/check-subdomain?subdomain=${sub}`);
      setSubdomainAvailable(data.available);
    } catch {
      setSubdomainAvailable(null);
    } finally {
      setCheckingSubdomain(false);
    }
  };

  const handleSubdomainChange = (e) => {
    const val = e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "");
    setFormData({ ...formData, subdomain: val });
    setError("");
    if (val.length >= 3) {
      clearTimeout(window._subCheck);
      window._subCheck = setTimeout(() => checkSubdomain(val), 500);
    } else {
      setSubdomainAvailable(null);
    }
  };

  const handleContinue = () => {
    setError("");
    if (!formData.company_name.trim()) { setError("Company name is required"); return; }
    if (!formData.email.trim()) { setError("Email is required"); return; }
    if (formData.password.length < 8) { setError("Password must be at least 8 characters"); return; }
    if (formData.password !== formData.confirm_password) { setError("Passwords don't match"); return; }
    setStep(2);
    const suggested = formData.company_name.toLowerCase().replace(/[^a-z0-9]/g, "");
    if (!formData.subdomain && suggested.length >= 3) {
      setFormData(prev => ({ ...prev, subdomain: suggested }));
      checkSubdomain(suggested);
    }
  };

  const handleRegister = async () => {
    if (!formData.subdomain || formData.subdomain.length < 3) {
      setError("Workspace URL must be at least 3 characters"); return;
    }
    if (subdomainAvailable === false) {
      setError("This workspace URL is taken. Please choose another."); return;
    }

    setLoading(true);
    setError("");
    try {
      const data = await signupFetch(`${API}/signup/register`, {
        method: "POST",
        body: JSON.stringify({
          company_name: formData.company_name,
          email: formData.email,
          password: formData.password,
          subdomain: formData.subdomain,
        }),
      });
      setRegisteredEmail(formData.email);
      setRegisteredSubdomain(data.subdomain || formData.subdomain);
      setStep(3);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "object" && Array.isArray(detail)) {
        setError(detail.map(d => d.msg || d).join(", "));
      } else if (detail) {
        setError(detail);
      } else if (err.message) {
        setError(`Registration failed: ${err.message}`);
      } else {
        setError("Registration failed. Please check your connection and try again.");
      }
      console.error("Registration error:", err);
    } finally {
      setLoading(false);
    }
  };

  const resendVerification = async () => {
    setLoading(true);
    setError("");
    try {
      await signupFetch(`${API}/signup/resend-verification`, {
        method: "POST",
        body: JSON.stringify({ email: registeredEmail }),
      });
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to resend verification email.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex items-center justify-center p-4" data-testid="signup-page">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <img 
            src="/getmyplan-logo-sm.png" 
            alt="Getmyplan - AI Demand Forecasting for Fashion Retail" 
            className="h-12 w-auto mx-auto mb-4"
            data-testid="signup-logo"
          />
          <h1 className="text-2xl font-bold text-slate-900" data-testid="signup-title">Start Free Trial</h1>
          <p className="text-sm text-slate-500 mt-1">7-day free trial. No credit card required.</p>
        </div>

        {/* Step indicators */}
        {step < 3 && (
          <div className="flex justify-center gap-16 mb-8">
            {[
              { n: 1, label: "Account" },
              { n: 2, label: "Workspace" },
            ].map((s) => (
              <div key={s.n} className="flex flex-col items-center gap-1.5">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition
                    ${step >= s.n ? "bg-[#0176D3] text-white" : "bg-gray-200 text-gray-500"}`}
                >
                  {step > s.n ? <CheckCircle size={16} /> : s.n}
                </div>
                <span className={`text-xs font-medium ${step >= s.n ? "text-[#0176D3]" : "text-gray-400"}`}>{s.label}</span>
              </div>
            ))}
          </div>
        )}

        {/* Card */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden">
          <div className="p-6">
            {error && (
              <div className="mb-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="signup-error">
                <AlertCircle size={16} className="flex-shrink-0" /> {error}
              </div>
            )}

            {/* Step 1: Account */}
            {step === 1 && (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Company Name</label>
                  <div className="relative">
                    <Building2 size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="signup-company"
                      name="company_name"
                      value={formData.company_name}
                      onChange={handleChange}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
                      placeholder="Your company"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Email Address</label>
                  <div className="relative">
                    <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="signup-email"
                      name="email"
                      type="email"
                      value={formData.email}
                      onChange={handleChange}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
                      placeholder="you@company.com"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Password</label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="signup-password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      value={formData.password}
                      onChange={handleChange}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-10 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
                      placeholder="Min 8 characters"
                      required
                    />
                    <button type="button" onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">Must be at least 8 characters with letters and numbers</p>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Confirm Password</label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="signup-confirm-password"
                      name="confirm_password"
                      type={showPassword ? "text" : "password"}
                      value={formData.confirm_password}
                      onChange={handleChange}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
                      placeholder="Confirm password"
                      required
                    />
                  </div>
                </div>
                <button
                  data-testid="signup-continue-btn"
                  onClick={handleContinue}
                  className="w-full bg-[#0176D3] hover:bg-[#0161B0] text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  Continue <ArrowRight size={16} />
                </button>
              </div>
            )}

            {/* Step 2: Workspace */}
            {step === 2 && (
              <div className="space-y-5">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Your Workspace URL</label>
                  <div className="relative">
                    <Globe size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="signup-subdomain"
                      name="subdomain"
                      value={formData.subdomain}
                      onChange={handleSubdomainChange}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
                      placeholder="your-company"
                    />
                  </div>
                  {checkingSubdomain && <p className="text-xs text-slate-400 mt-1">Checking...</p>}
                  {!checkingSubdomain && subdomainAvailable === true && (
                    <p className="text-xs text-green-600 mt-1 flex items-center gap-1" data-testid="subdomain-available">
                      <CheckCircle size={12} /> Available
                    </p>
                  )}
                  {!checkingSubdomain && subdomainAvailable === false && (
                    <p className="text-xs text-red-500 mt-1" data-testid="subdomain-taken">Taken — please choose another</p>
                  )}
                  <p className="text-xs text-slate-400 mt-1">This will be your unique workspace identifier</p>
                </div>

                <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 text-xs text-blue-700">
                  Your 7-day free trial starts after email verification. No credit card required.
                </div>

                <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Account Summary</h4>
                  <div className="text-sm"><span className="text-slate-500">Company:</span> <span className="font-medium text-slate-800">{formData.company_name}</span></div>
                  <div className="text-sm"><span className="text-slate-500">Email:</span> <span className="font-medium text-slate-800">{formData.email}</span></div>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setStep(1)}
                    className="px-4 py-2.5 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition flex items-center gap-1"
                  >
                    <ArrowLeft size={14} /> Back
                  </button>
                  <button
                    data-testid="signup-submit-btn"
                    onClick={handleRegister}
                    disabled={loading || subdomainAvailable === false}
                    className="flex-1 bg-[#0176D3] hover:bg-[#0161B0] text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
                  >
                    {loading ? <Loader2 size={16} className="animate-spin" /> : null}
                    {loading ? "Creating..." : "Create Workspace"}
                  </button>
                </div>
              </div>
            )}

            {/* Step 3: Verification */}
            {step === 3 && (
              <div className="text-center py-4" data-testid="signup-step3">
                <div className="w-14 h-14 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Mail size={28} className="text-green-500" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">Check your email</h3>
                <p className="text-sm text-slate-500">
                  We've sent a verification link to<br />
                  <strong className="text-slate-800">{registeredEmail}</strong>
                </p>
                <div className="mt-4 bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600 text-left">
                  <p>Click the link in the email to verify your account and activate your 7-day trial.</p>
                  <p className="text-xs text-gray-400 mt-2">The link expires in 24 hours.</p>
                </div>
                <button
                  onClick={resendVerification}
                  disabled={loading}
                  className="mt-4 text-sm text-[#0176D3] hover:text-[#0161B0] font-medium"
                  data-testid="resend-btn"
                >
                  {loading ? "Sending..." : "Didn't receive it? Click to resend"}
                </button>
                <div className="mt-4">
                  <Link to="/login" className="text-sm text-slate-400 hover:text-slate-600 font-medium">Go to Sign In</Link>
                </div>
              </div>
            )}
          </div>
        </div>

        {step < 3 && (
          <div className="text-center mt-6 space-y-2">
            <p className="text-sm text-slate-500">
              Already have an account? <Link to="/login" className="text-[#0176D3] hover:text-[#0161B0] font-medium" data-testid="signup-login-link">Sign In</Link>
            </p>
            <Link to="/" className="text-xs text-slate-400 hover:text-slate-600 transition">&larr; Back to home</Link>
          </div>
        )}

        <p className="text-center text-xs text-slate-400 mt-6">GetMyPlan v2.0 - AI-powered retail analytics</p>
      </div>
    </div>
  );
};

export default Signup;
