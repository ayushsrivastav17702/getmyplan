import { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { API } from "../App";
import { useAuth } from "../context/AuthContext";
import {
  Lock, Mail, Building2, ChevronRight, AlertCircle,
  Eye, EyeOff, Loader2, UserPlus, LogIn, Rocket
} from "lucide-react";

const LoginPage = () => {
  const { login, sessionExpired, clearSessionExpired } = useAuth();
  const [mode, setMode] = useState("login"); // login | register | selectTenant
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [tenantId, setTenantId] = useState("");
  const [tenants, setTenants] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Show session expired message
  useEffect(() => {
    if (sessionExpired) {
      setError("Session expired. Please log in again.");
      clearSessionExpired();
    }
  }, [sessionExpired, clearSessionExpired]);

  // Registration fields
  const [regCompany, setRegCompany] = useState("");
  const [regSubdomain, setRegSubdomain] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [subdomainAvailable, setSubdomainAvailable] = useState(null);

  // Load available tenants for login
  useEffect(() => {
    axios.get(`${API}/tenants/`)
      .then(r => setTenants(r.data.tenants || []))
      .catch(() => {});
  }, []);

  const checkSubdomain = async (sub) => {
    if (sub.length < 3) { setSubdomainAvailable(null); return; }
    try {
      const resp = await axios.get(`${API}/tenants/check-subdomain?subdomain=${sub}`);
      setSubdomainAvailable(resp.data.available);
    } catch { setSubdomainAvailable(null); }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!tenantId) { setError("Please select a tenant"); return; }
    setLoading(true);
    setError("");
    try {
      await login(email, password, tenantId);
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const resp = await axios.post(`${API}/tenants/create`, {
        company_name: regCompany,
        subdomain: regSubdomain,
        admin_email: regEmail,
        admin_password: regPassword,
        plan_type: "starter",
      });
      // Auto-login after registration
      await login(regEmail, regPassword, resp.data.tenant_id);
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex items-center justify-center p-4" data-testid="login-page">
      <div className="w-full max-w-md">
        {/* Logo / Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-[#0176D3] mb-4">
            <Building2 size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">GetMyPlan</h1>
          <p className="text-sm text-slate-500 mt-1">AI-Powered Retail Analytics</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-slate-200">
            <button
              data-testid="login-tab"
              onClick={() => { setMode("login"); setError(""); }}
              className={`flex-1 py-3 text-sm font-medium transition-colors ${
                mode === "login"
                  ? "text-[#0176D3] border-b-2 border-[#0176D3] bg-blue-50/50"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <LogIn size={16} className="inline mr-1.5 -mt-0.5" /> Sign In
            </button>
            <button
              data-testid="register-tab"
              onClick={() => { setMode("register"); setError(""); }}
              className={`flex-1 py-3 text-sm font-medium transition-colors ${
                mode === "register"
                  ? "text-[#0176D3] border-b-2 border-[#0176D3] bg-blue-50/50"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <UserPlus size={16} className="inline mr-1.5 -mt-0.5" /> Create Tenant
            </button>
          </div>

          <div className="p-6">
            {error && (
              <div className="mb-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="auth-error">
                <AlertCircle size={16} /> {error}
              </div>
            )}

            {/* ========== LOGIN ========== */}
            {mode === "login" && (
              <form onSubmit={handleLogin} className="space-y-4">
                {/* Tenant selector */}
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Tenant</label>
                  <select
                    data-testid="tenant-select"
                    value={tenantId}
                    onChange={e => setTenantId(e.target.value)}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent bg-white"
                    required
                  >
                    <option value="">Select tenant...</option>
                    {tenants.map(t => (
                      <option key={t.tenant_id} value={t.tenant_id}>
                        {t.company_name} ({t.subdomain})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Email</label>
                  <div className="relative">
                    <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="login-email"
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent"
                      placeholder="admin@company.com"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Password</label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="login-password"
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-10 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent"
                      placeholder="Enter password"
                      required
                    />
                    <button type="button" onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                <button
                  data-testid="login-submit"
                  type="submit"
                  disabled={loading}
                  className="w-full bg-[#0176D3] hover:bg-[#0161B0] text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
                >
                  {loading ? <Loader2 size={18} className="animate-spin" /> : <LogIn size={18} />}
                  {loading ? "Signing in..." : "Sign In"}
                </button>
              </form>
            )}

            {/* ========== REGISTER ========== */}
            {mode === "register" && (
              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Company Name</label>
                  <input
                    data-testid="reg-company"
                    type="text"
                    value={regCompany}
                    onChange={e => setRegCompany(e.target.value)}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent"
                    placeholder="Acme Corporation"
                    required
                    minLength={2}
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Subdomain</label>
                  <div className="relative">
                    <input
                      data-testid="reg-subdomain"
                      type="text"
                      value={regSubdomain}
                      onChange={e => {
                        const v = e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '');
                        setRegSubdomain(v);
                        checkSubdomain(v);
                      }}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent"
                      placeholder="acme"
                      required
                      minLength={3}
                      pattern="^[a-z0-9][a-z0-9-]*[a-z0-9]$"
                    />
                    {subdomainAvailable !== null && (
                      <span className={`absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium ${
                        subdomainAvailable ? "text-green-600" : "text-red-500"
                      }`}>
                        {subdomainAvailable ? "Available" : "Taken"}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{regSubdomain || "acme"}.yourdomain.com</p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Admin Email</label>
                  <div className="relative">
                    <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="reg-email"
                      type="email"
                      value={regEmail}
                      onChange={e => setRegEmail(e.target.value)}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent"
                      placeholder="admin@acme.com"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Password</label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      data-testid="reg-password"
                      type={showPassword ? "text" : "password"}
                      value={regPassword}
                      onChange={e => setRegPassword(e.target.value)}
                      className="w-full border border-slate-200 rounded-lg pl-10 pr-10 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent"
                      placeholder="Min 8 characters"
                      required
                      minLength={8}
                    />
                    <button type="button" onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                <button
                  data-testid="register-submit"
                  type="submit"
                  disabled={loading || subdomainAvailable === false}
                  className="w-full bg-[#0176D3] hover:bg-[#0161B0] text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
                >
                  {loading ? <Loader2 size={18} className="animate-spin" /> : <UserPlus size={18} />}
                  {loading ? "Creating..." : "Create Tenant & Sign In"}
                </button>
              </form>
            )}
          </div>

          {/* Demo credentials hint */}
          <div className="px-6 pb-5">
            <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 text-xs text-slate-500">
              <p className="font-medium text-slate-600 mb-1">Demo Access</p>
              <p>Tenant: <span className="font-mono text-slate-700">Demo Company</span></p>
              <p>Email: <span className="font-mono text-slate-700">admin@demo.com</span> / Password: <span className="font-mono text-slate-700">demo1234</span></p>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-slate-400 mt-6">
          GetMyPlan v2.0 &middot; Multi-Tenant
        </p>
        <div className="text-center mt-3">
          <Link to="/signup" className="text-sm text-[#0176D3] hover:text-[#0161B0] font-medium inline-flex items-center gap-1" data-testid="login-signup-link">
            <Rocket size={14} /> Start your 7-day free trial
          </Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
