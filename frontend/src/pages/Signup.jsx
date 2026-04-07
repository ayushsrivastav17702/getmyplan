import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { API } from "../App";
import {
  Mail, Lock, Building2, Globe, CheckCircle, AlertCircle,
  Loader2, ArrowRight, ArrowLeft, Eye, EyeOff, Rocket
} from "lucide-react";

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
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError("");
  };

  const checkSubdomain = async (sub) => {
    if (sub.length < 3) { setSubdomainAvailable(null); return; }
    setCheckingSubdomain(true);
    try {
      const resp = await axios.get(`${API}/tenants/check-subdomain?subdomain=${sub}`, {
        transformRequest: [(data, headers) => {
          delete headers["Authorization"];
          delete headers["X-Tenant-ID"];
          return data;
        }],
      });
      setSubdomainAvailable(resp.data.available);
    } catch {
      setSubdomainAvailable(null);
    } finally {
      setCheckingSubdomain(false);
    }
  };

  const validateStep1 = () => {
    if (!formData.company_name.trim()) { setError("Company name is required"); return false; }
    if (!formData.email.trim()) { setError("Email is required"); return false; }
    if (!formData.password) { setError("Password is required"); return false; }
    if (formData.password.length < 8) { setError("Password must be at least 8 characters"); return false; }
    if (!/[A-Za-z]/.test(formData.password)) { setError("Password must contain at least one letter"); return false; }
    if (!/\d/.test(formData.password)) { setError("Password must contain at least one number"); return false; }
    if (formData.password !== formData.confirm_password) { setError("Passwords do not match"); return false; }
    return true;
  };

  const validateStep2 = () => {
    if (!formData.subdomain.trim()) { setError("Subdomain is required"); return false; }
    if (!/^[a-z0-9-]+$/.test(formData.subdomain)) { setError("Subdomain can only contain lowercase letters, numbers, and hyphens"); return false; }
    if (formData.subdomain.length < 3) { setError("Subdomain must be at least 3 characters"); return false; }
    const reserved = ["www", "api", "app", "admin", "mail", "ftp", "localhost", "demo", "test"];
    if (reserved.includes(formData.subdomain)) { setError("This subdomain is reserved"); return false; }
    if (subdomainAvailable === false) { setError("This subdomain is already taken"); return false; }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (step === 1) {
      if (!validateStep1()) return;
      setStep(2);
      return;
    }
    if (!validateStep2()) return;

    setLoading(true);
    setError("");
    try {
      // Use a clean axios instance without auth headers for registration
      const resp = await axios.post(`${API}/signup/register`, {
        company_name: formData.company_name,
        email: formData.email,
        password: formData.password,
        subdomain: formData.subdomain,
      }, {
        headers: {
          "Content-Type": "application/json",
          // Explicitly exclude any auth/tenant headers
        },
        transformRequest: [(data, headers) => {
          delete headers["Authorization"];
          delete headers["X-Tenant-ID"];
          return JSON.stringify(data);
        }],
      });
      setRegisteredEmail(formData.email);
      setRegisteredSubdomain(formData.subdomain);
      setStep(3);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "object" && Array.isArray(detail)) {
        setError(detail.map(d => d.msg || d).join(", "));
      } else if (detail) {
        setError(detail);
      } else if (err.response?.status === 429) {
        setError("Too many attempts. Please wait a minute and try again.");
      } else if (!err.response) {
        setError("Network error. Please check your connection and try again.");
      } else {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const resendVerification = async () => {
    setLoading(true);
    setError("");
    try {
      await axios.post(`${API}/signup/resend-verification`, { email: registeredEmail });
      setError(""); // clear any previous error
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
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-[#0176D3] mb-4">
            <Rocket size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900" data-testid="signup-title">Start Free Trial</h1>
          <p className="text-sm text-slate-500 mt-1">7-day free trial. No credit card required.</p>
        </div>

        {/* Step indicators */}
        {step < 3 && (
          <div className="flex justify-center gap-16 mb-8">
            {[
              { n: 1, label: "Account" },
              { n: 2, label: "Workspace" },
            ].map(({ n, label }) => (
              <div key={n} className="flex flex-col items-center">
                <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                  step > n ? "bg-green-500 text-white" : step === n ? "bg-[#0176D3] text-white" : "bg-slate-200 text-slate-400"
                }`}>
                  {step > n ? <CheckCircle size={18} /> : n}
                </div>
                <span className={`text-xs mt-1.5 font-medium ${step >= n ? "text-[#0176D3]" : "text-slate-400"}`}>{label}</span>
              </div>
            ))}
          </div>
        )}

        {/* Step 1: Account details */}
        {step === 1 && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden" data-testid="signup-step1">
            <div className="p-6">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Company Name</label>
                  <div className="relative">
                    <Building2 size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="signup-company"
                      type="text" name="company_name" value={formData.company_name} onChange={handleChange}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent"
                      placeholder="Acme Corporation" required
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Email Address</label>
                  <div className="relative">
                    <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="signup-email"
                      type="email" name="email" value={formData.email} onChange={handleChange}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent"
                      placeholder="admin@acme.com" required
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Password</label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="signup-password"
                      type={showPassword ? "text" : "password"} name="password" value={formData.password} onChange={handleChange}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-10 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent"
                      placeholder="Min 8 chars with letters & numbers" required
                    />
                    <button type="button" onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">Must be at least 8 characters with letters and numbers</p>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Confirm Password</label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="signup-confirm-password"
                      type="password" name="confirm_password" value={formData.confirm_password} onChange={handleChange}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent"
                      placeholder="Confirm password" required
                    />
                  </div>
                </div>

                {error && (
                  <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="signup-error">
                    <AlertCircle size={16} className="flex-shrink-0" /> <span>{error}</span>
                  </div>
                )}

                <button
                  data-testid="signup-continue-btn"
                  type="submit"
                  className="w-full bg-[#0176D3] hover:bg-[#0161B0] text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  Continue <ArrowRight size={16} />
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Step 2: Workspace / Subdomain */}
        {step === 2 && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden" data-testid="signup-step2">
            <div className="p-6">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Your Workspace URL</label>
                  <div className="relative">
                    <Globe size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="signup-subdomain"
                      type="text" name="subdomain" value={formData.subdomain}
                      onChange={(e) => {
                        const v = e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "");
                        setFormData({ ...formData, subdomain: v });
                        setError("");
                        checkSubdomain(v);
                      }}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent"
                      placeholder="acme" required
                    />
                    {checkingSubdomain && (
                      <Loader2 size={14} className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-slate-400" />
                    )}
                    {!checkingSubdomain && subdomainAvailable !== null && (
                      <span className={`absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium ${subdomainAvailable ? "text-green-600" : "text-red-500"}`}>
                        {subdomainAvailable ? "Available" : "Taken"}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-1">This will be your unique workspace identifier</p>
                </div>

                <div className="bg-blue-50 border border-blue-100 p-4 rounded-lg">
                  <p className="text-sm text-blue-800 flex items-start gap-2">
                    <CheckCircle size={16} className="mt-0.5 flex-shrink-0" />
                    Your 7-day free trial starts after email verification. No credit card required.
                  </p>
                </div>

                <div className="bg-slate-50 border border-slate-100 p-4 rounded-lg text-xs text-slate-500">
                  <p className="font-medium text-slate-600 mb-1">Account Summary</p>
                  <p>Company: <span className="text-slate-700 font-medium">{formData.company_name}</span></p>
                  <p>Email: <span className="text-slate-700 font-medium">{formData.email}</span></p>
                </div>

                {error && (
                  <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="signup-error">
                    <AlertCircle size={16} className="flex-shrink-0" /> <span>{error}</span>
                  </div>
                )}

                <div className="flex gap-3">
                  <button
                    data-testid="signup-back-btn"
                    type="button" onClick={() => { setStep(1); setError(""); }}
                    className="flex-1 py-2.5 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 font-medium flex items-center justify-center gap-2 transition-colors"
                  >
                    <ArrowLeft size={16} /> Back
                  </button>
                  <button
                    data-testid="signup-submit-btn"
                    type="submit" disabled={loading || subdomainAvailable === false}
                    className="flex-1 py-2.5 bg-[#0176D3] hover:bg-[#0161B0] text-white font-medium rounded-lg flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                  >
                    {loading ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                    {loading ? "Creating..." : "Create Workspace"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Step 3: Verification Sent */}
        {step === 3 && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden" data-testid="signup-step3">
            <div className="p-8 text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Mail size={28} className="text-green-600" />
              </div>
              <h2 className="text-xl font-bold text-slate-900 mb-2">Check your email</h2>
              <p className="text-slate-600 mb-4">
                We've sent a verification link to <strong className="text-slate-800">{registeredEmail}</strong>
              </p>
              <div className="bg-slate-50 border border-slate-100 p-4 rounded-lg mb-6 text-left">
                <p className="text-sm text-slate-600">Click the link in the email to verify your account and activate your 7-day trial.</p>
                <p className="text-xs text-slate-400 mt-2">The link expires in 24 hours.</p>
              </div>

              {error && (
                <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg mb-4" data-testid="signup-error">
                  <AlertCircle size={16} className="flex-shrink-0" /> <span>{error}</span>
                </div>
              )}

              <button
                data-testid="signup-resend-btn"
                onClick={resendVerification} disabled={loading}
                className="text-[#0176D3] hover:text-[#0161B0] text-sm font-medium flex items-center justify-center gap-1 mx-auto"
              >
                {loading && <Loader2 size={14} className="animate-spin" />}
                Didn't receive it? Click to resend
              </button>

              <div className="mt-6 pt-6 border-t border-slate-100">
                <Link to="/login" className="text-sm text-[#0176D3] hover:text-[#0161B0] font-medium" data-testid="signup-go-login">
                  Go to Sign In
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Footer link */}
        {step < 3 && (
          <div className="text-center mt-6">
            <p className="text-sm text-slate-500">
              Already have an account?{" "}
              <Link to="/login" className="text-[#0176D3] hover:text-[#0161B0] font-medium" data-testid="signup-login-link">
                Sign in
              </Link>
            </p>
          </div>
        )}

        <p className="text-center text-xs text-slate-400 mt-6">
          GetMyPlan v2.0 &middot; AI-powered retail analytics
        </p>
      </div>
    </div>
  );
};

export default Signup;
