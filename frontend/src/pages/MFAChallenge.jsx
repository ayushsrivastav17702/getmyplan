import { useState, useEffect, useRef } from "react";
import { Shield, Smartphone, Mail, Loader2, ArrowLeft, AlertCircle, CheckCircle2 } from "lucide-react";
import axios from "axios";
import { API } from "../App";

const MFAChallenge = ({ mfaToken, mfaMethods, email, onVerified, onCancel }) => {
  const [method, setMethod] = useState("totp"); // "totp" or "email_otp"
  const [code, setCode] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [emailSent, setEmailSent] = useState(false);
  const [emailCooldown, setEmailCooldown] = useState(0);
  const inputRefs = useRef([]);

  useEffect(() => {
    if (emailCooldown > 0) {
      const t = setTimeout(() => setEmailCooldown(c => c - 1), 1000);
      return () => clearTimeout(t);
    }
  }, [emailCooldown]);

  useEffect(() => {
    // Focus first input on mount/method switch
    setCode(["", "", "", "", "", ""]);
    setError("");
    setTimeout(() => inputRefs.current[0]?.focus(), 100);
  }, [method]);

  const handleDigitChange = (idx, value) => {
    if (!/^\d?$/.test(value)) return;
    const next = [...code];
    next[idx] = value;
    setCode(next);
    if (value && idx < 5) {
      inputRefs.current[idx + 1]?.focus();
    }
    // Auto-submit when all 6 digits filled
    if (value && idx === 5 && next.every(d => d)) {
      handleVerify(next.join(""));
    }
  };

  const handleKeyDown = (idx, e) => {
    if (e.key === "Backspace" && !code[idx] && idx > 0) {
      inputRefs.current[idx - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (pasted.length === 6) {
      setCode(pasted.split(""));
      inputRefs.current[5]?.focus();
      handleVerify(pasted);
    }
  };

  const handleVerify = async (fullCode) => {
    const codeStr = fullCode || code.join("");
    if (codeStr.length !== 6) { setError("Please enter all 6 digits"); return; }
    setLoading(true);
    setError("");
    try {
      const endpoint = method === "totp" ? "/auth/mfa/verify-totp" : "/auth/mfa/verify-email-otp";
      const body = method === "totp"
        ? { mfa_token: mfaToken, totp_code: codeStr }
        : { mfa_token: mfaToken, otp_code: codeStr };
      const resp = await axios.post(`${API}${endpoint}`, body);
      onVerified(resp.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Verification failed");
      setCode(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  const handleSendEmail = async () => {
    if (emailCooldown > 0) return;
    setLoading(true);
    setError("");
    try {
      await axios.post(`${API}/auth/mfa/send-email-otp`, { mfa_token: mfaToken });
      setEmailSent(true);
      setEmailCooldown(60);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to send code");
    } finally {
      setLoading(false);
    }
  };

  const switchToEmail = () => {
    setMethod("email_otp");
    if (!emailSent) handleSendEmail();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex items-center justify-center p-4" data-testid="mfa-challenge-page">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-blue-100 mb-4">
            <Shield size={28} className="text-[#0176D3]" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900" data-testid="mfa-title">Two-Factor Authentication</h1>
          <p className="text-sm text-slate-500 mt-1">Extra security for your account</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden">
          {/* Method tabs */}
          <div className="flex border-b border-slate-200" data-testid="mfa-method-tabs">
            <button
              data-testid="mfa-tab-totp"
              onClick={() => setMethod("totp")}
              className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors ${
                method === "totp" ? "text-[#0176D3] border-b-2 border-[#0176D3] bg-blue-50/50" : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <Smartphone size={16} /> Authenticator
            </button>
            <button
              data-testid="mfa-tab-email"
              onClick={switchToEmail}
              className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors ${
                method === "email_otp" ? "text-[#0176D3] border-b-2 border-[#0176D3] bg-blue-50/50" : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <Mail size={16} /> Email Code
            </button>
          </div>

          <div className="p-6">
            <p className="text-sm text-slate-600 mb-6 text-center">
              {method === "totp"
                ? "Enter the 6-digit code from your authenticator app"
                : emailSent
                  ? `We sent a code to ${email ? email.replace(/(.{2})(.*)(@.*)/, "$1***$3") : "your email"}`
                  : "We'll send a verification code to your email"}
            </p>

            {error && (
              <div className="mb-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="mfa-error">
                <AlertCircle size={16} className="flex-shrink-0" /> {error}
              </div>
            )}

            {/* Code input */}
            <div className="flex justify-center gap-2 mb-6" data-testid="mfa-code-inputs" onPaste={handlePaste}>
              {code.map((digit, i) => (
                <input
                  key={i}
                  ref={el => inputRefs.current[i] = el}
                  data-testid={`mfa-code-${i}`}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={e => handleDigitChange(i, e.target.value)}
                  onKeyDown={e => handleKeyDown(i, e)}
                  className="w-11 h-12 text-center text-lg font-semibold border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent transition-all"
                  disabled={loading}
                />
              ))}
            </div>

            <button
              data-testid="mfa-verify-btn"
              onClick={() => handleVerify()}
              disabled={loading || code.join("").length !== 6}
              className="w-full bg-[#0176D3] hover:bg-[#0161B0] text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <CheckCircle2 size={18} />}
              {loading ? "Verifying..." : "Verify & Sign In"}
            </button>

            {method === "email_otp" && (
              <div className="text-center mt-4">
                <button
                  data-testid="mfa-resend-email"
                  onClick={handleSendEmail}
                  disabled={emailCooldown > 0 || loading}
                  className="text-sm text-[#0176D3] hover:text-[#0161B0] font-medium disabled:text-slate-400"
                >
                  {emailCooldown > 0 ? `Resend in ${emailCooldown}s` : "Resend code"}
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="text-center mt-4">
          <button
            data-testid="mfa-back-to-login"
            onClick={onCancel}
            className="text-sm text-slate-500 hover:text-slate-700 inline-flex items-center gap-1"
          >
            <ArrowLeft size={14} /> Back to login
          </button>
        </div>
      </div>
    </div>
  );
};

export default MFAChallenge;
