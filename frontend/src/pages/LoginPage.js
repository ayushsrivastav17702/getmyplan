import { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { API } from "../App";
import { useAuth } from "../context/AuthContext";
import {
  Lock, Mail, Building2, ChevronRight, AlertCircle,
  Eye, EyeOff, Loader2, UserPlus, LogIn, Rocket
} from "lucide-react";
import MFAChallenge from "./MFAChallenge";

const LoginPage = () => {
  const { login, sessionExpired, clearSessionExpired, mfaChallenge, completeMfaLogin, cancelMfa } = useAuth();
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
      const result = await login(email, password);
      // If MFA required, the challenge will appear via mfaChallenge state
      if (result?.mfa_required) {
        // No error — MFA challenge component will render
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  // Show MFA challenge if needed
  if (mfaChallenge) {
    return (
      <MFAChallenge
        mfaToken={mfaChallenge.mfa_token}
        mfaMethods={mfaChallenge.mfa_methods}
        email={mfaChallenge.email}
        onVerified={completeMfaLogin}
        onCancel={cancelMfa}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex items-center justify-center p-4" data-testid="login-page">
      <div className="w-full max-w-md">
        {/* Logo / Header */}
        <div className="text-center mb-8">
          <img 
            src="/getmyplan-logo-sm.png" 
            alt="Getmyplan - AI Demand Forecasting for Fashion Retail" 
            className="h-12 w-auto mx-auto mb-4"
            data-testid="login-logo"
          />
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
                    id="email"
                    name="email"
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
                    id="password"
                    name="password"
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

            {/* Divider */}
            <div className="flex items-center gap-3 my-4">
              <div className="flex-1 h-px bg-slate-200" />
              <span className="text-xs text-slate-400">or</span>
              <div className="flex-1 h-px bg-slate-200" />
            </div>

            {/* Google OAuth */}
            {/* REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH */}
            <button
              data-testid="google-login-btn"
              type="button"
              onClick={() => {
                const redirectUrl = window.location.origin + '/dashboard';
                window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
              }}
              className="w-full border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
              Sign in with Google
            </button>

            <div className="mt-3 text-right">
              <Link to="/forgot-password" className="text-xs text-[#0176D3] hover:text-[#0161B0] font-medium" data-testid="forgot-password-link">
                Forgot password?
              </Link>
            </div>
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
