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
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (sessionExpired) {
      setError("Session expired. Please log in again.");
      clearSessionExpired();
    }
  }, [sessionExpired, clearSessionExpired]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Please check your credentials.");
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
          <div className="p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-1">Welcome back</h2>
            <p className="text-sm text-slate-500 mb-5">Sign in to your workspace</p>

            {error && (
              <div className="mb-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="auth-error">
                <AlertCircle size={16} className="flex-shrink-0" /> {error}
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
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
                    placeholder="you@company.com"
                    required
                    autoComplete="email"
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
                    autoComplete="current-password"
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
          </div>
        </div>

        <div className="text-center mt-6 space-y-2">
          <Link to="/signup" className="text-sm text-[#0176D3] hover:text-[#0161B0] font-medium inline-flex items-center gap-1" data-testid="login-signup-link">
            <Rocket size={14} /> Start your 7-day free trial
          </Link>
          <div>
            <Link to="/" className="text-xs text-slate-400 hover:text-slate-600 transition" data-testid="login-back-home">
              &larr; Back to home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
