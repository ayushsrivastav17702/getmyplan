import { useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { API } from "../App";
import { Mail, ArrowLeft, CheckCircle, AlertCircle, Loader2, Building2 } from "lucide-react";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const cleanAxios = axios.create({ headers: { "Content-Type": "application/json" } });
      await cleanAxios.post(`${API}/signup/forgot-password`, { email });
      setSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex items-center justify-center p-4" data-testid="forgot-password-page">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <img 
            src="/getmyplan-logo-sm.png" 
            alt="Getmyplan" 
            className="h-12 w-auto mx-auto mb-4"
            data-testid="forgot-password-logo"
          />
          <h1 className="text-2xl font-bold text-slate-900">GetMyPlan</h1>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden">
          <div className="p-6">
            {sent ? (
              <div className="text-center py-4" data-testid="reset-email-sent">
                <div className="w-14 h-14 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle size={28} className="text-green-500" />
                </div>
                <h2 className="text-lg font-semibold text-slate-900 mb-2">Check your email</h2>
                <p className="text-sm text-slate-500 mb-4">
                  If an account exists for <strong>{email}</strong>, we've sent a password reset link. Check your inbox and spam folder.
                </p>
                <p className="text-xs text-slate-400">The link expires in 1 hour.</p>
              </div>
            ) : (
              <>
                <h2 className="text-lg font-semibold text-slate-900 mb-1">Reset your password</h2>
                <p className="text-sm text-slate-500 mb-5">Enter your email and we'll send you a reset link.</p>

                {error && (
                  <div className="mb-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="forgot-error">
                    <AlertCircle size={16} className="flex-shrink-0" /> {error}
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Email</label>
                    <div className="relative">
                      <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                      <input
                        data-testid="forgot-email"
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
                  <button
                    data-testid="forgot-submit"
                    type="submit"
                    disabled={loading}
                    className="w-full bg-[#0176D3] hover:bg-[#0161B0] text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
                  >
                    {loading ? <Loader2 size={18} className="animate-spin" /> : <Mail size={18} />}
                    {loading ? "Sending..." : "Send Reset Link"}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>

        <div className="text-center mt-6">
          <Link to="/login" className="text-sm text-slate-500 hover:text-[#0176D3] font-medium inline-flex items-center gap-1" data-testid="forgot-back-login">
            <ArrowLeft size={14} /> Back to Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
