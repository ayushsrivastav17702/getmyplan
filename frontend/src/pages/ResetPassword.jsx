import { useState, useEffect } from "react";
import axios from "axios";
import { Link, useSearchParams } from "react-router-dom";
import { API } from "../App";
import { Lock, CheckCircle, AlertCircle, Loader2, Building2, Eye, EyeOff } from "lucide-react";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) setError("Invalid reset link. Please request a new one.");
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) { setError("Passwords don't match."); return; }
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }

    setLoading(true);
    setError("");
    try {
      await axios.post(`${API}/signup/reset-password`, { token, password }, {
        transformRequest: [(data, headers) => {
          delete headers["Authorization"];
          delete headers["X-Tenant-ID"];
          return JSON.stringify(data);
        }],
      });
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Reset failed. The link may have expired.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex items-center justify-center p-4" data-testid="reset-password-page">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-[#0176D3] mb-4">
            <Building2 size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">GetMyPlan</h1>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden">
          <div className="p-6">
            {success ? (
              <div className="text-center py-4" data-testid="reset-success">
                <div className="w-14 h-14 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle size={28} className="text-green-500" />
                </div>
                <h2 className="text-lg font-semibold text-slate-900 mb-2">Password updated!</h2>
                <p className="text-sm text-slate-500 mb-6">Your password has been reset. You can now sign in.</p>
                <Link
                  to="/login"
                  data-testid="reset-go-login"
                  className="inline-flex items-center gap-2 px-6 py-2.5 bg-[#0176D3] text-white rounded-lg font-medium hover:bg-[#0161B0] transition"
                >
                  Sign In
                </Link>
              </div>
            ) : (
              <>
                <h2 className="text-lg font-semibold text-slate-900 mb-1">Set new password</h2>
                <p className="text-sm text-slate-500 mb-5">Enter your new password below.</p>

                {error && (
                  <div className="mb-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="reset-error">
                    <AlertCircle size={16} className="flex-shrink-0" /> {error}
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">New Password</label>
                    <div className="relative">
                      <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                      <input
                        data-testid="reset-password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={e => setPassword(e.target.value)}
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

                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Confirm Password</label>
                    <div className="relative">
                      <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                      <input
                        data-testid="reset-confirm-password"
                        type={showPassword ? "text" : "password"}
                        value={confirmPassword}
                        onChange={e => setConfirmPassword(e.target.value)}
                        className="w-full border border-slate-200 rounded-lg pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent"
                        placeholder="Confirm password"
                        required
                        minLength={8}
                      />
                    </div>
                  </div>

                  <button
                    data-testid="reset-submit"
                    type="submit"
                    disabled={loading || !token}
                    className="w-full bg-[#0176D3] hover:bg-[#0161B0] text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
                  >
                    {loading ? <Loader2 size={18} className="animate-spin" /> : <Lock size={18} />}
                    {loading ? "Updating..." : "Reset Password"}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>

        <div className="text-center mt-6">
          <Link to="/login" className="text-sm text-slate-500 hover:text-[#0176D3] font-medium" data-testid="reset-back-login">
            Back to Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
