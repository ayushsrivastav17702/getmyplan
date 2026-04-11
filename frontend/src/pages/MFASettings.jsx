import { useState, useEffect, useRef } from "react";
import { Shield, Smartphone, QrCode, Copy, Check, Loader2, AlertCircle, X, Lock, ShieldCheck, ShieldOff } from "lucide-react";
import axios from "axios";
import { API } from "../App";
import { useAuth } from "../context/AuthContext";

const MFASettings = () => {
  const { token } = useAuth();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState("idle"); // idle, setup, verify, disabling
  const [setupData, setSetupData] = useState(null);
  const [code, setCode] = useState(["", "", "", "", "", ""]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [disablePassword, setDisablePassword] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const inputRefs = useRef([]);

  const fetchStatus = async () => {
    try {
      const resp = await axios.get(`${API}/auth/mfa/status`);
      setStatus(resp.data);
    } catch {
      setError("Failed to load MFA status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchStatus(); }, []);

  const handleSetup = async () => {
    setError("");
    setSuccess("");
    setActionLoading(true);
    try {
      const resp = await axios.post(`${API}/auth/mfa/setup-totp`);
      setSetupData(resp.data);
      setStep("setup");
      setCode(["", "", "", "", "", ""]);
      setTimeout(() => inputRefs.current[0]?.focus(), 200);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to start setup");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDigitChange = (idx, value) => {
    if (!/^\d?$/.test(value)) return;
    const next = [...code];
    next[idx] = value;
    setCode(next);
    if (value && idx < 5) inputRefs.current[idx + 1]?.focus();
  };

  const handleKeyDown = (idx, e) => {
    if (e.key === "Backspace" && !code[idx] && idx > 0) inputRefs.current[idx - 1]?.focus();
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (pasted.length >= 1) {
      const newCode = [...code];
      pasted.split("").forEach((d, i) => { if (i < 6) newCode[i] = d; });
      setCode(newCode);
      inputRefs.current[Math.min(pasted.length, 5)]?.focus();
    }
  };

  const handleVerifySetup = async () => {
    const codeStr = code.join("");
    if (codeStr.length !== 6) { setError("Enter all 6 digits"); return; }
    setError("");
    setActionLoading(true);
    try {
      await axios.post(`${API}/auth/mfa/verify-setup`, {
        totp_code: codeStr,
        setup_token: setupData.setup_token,
      });
      setSuccess("Two-factor authentication enabled successfully!");
      setStep("idle");
      setSetupData(null);
      fetchStatus();
    } catch (err) {
      setError(err.response?.data?.detail || "Verification failed");
      setCode(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    } finally {
      setActionLoading(false);
    }
  };

  const handleDisable = async () => {
    if (!disablePassword) { setError("Password required"); return; }
    setError("");
    setActionLoading(true);
    try {
      await axios.post(`${API}/auth/mfa/disable`, { password: disablePassword });
      setSuccess("Two-factor authentication has been disabled");
      setStep("idle");
      setDisablePassword("");
      fetchStatus();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to disable MFA");
    } finally {
      setActionLoading(false);
    }
  };

  const copySecret = () => {
    if (setupData?.secret) {
      navigator.clipboard.writeText(setupData.secret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center py-12">
      <Loader2 className="animate-spin text-slate-400" size={28} />
    </div>
  );

  return (
    <div data-testid="mfa-settings-page">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-blue-100">
          <Shield size={22} className="text-[#0176D3]" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Two-Factor Authentication</h2>
          <p className="text-sm text-slate-500">Add an extra layer of security to your account</p>
        </div>
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="mfa-settings-error">
          <AlertCircle size={16} className="flex-shrink-0" /> {error}
          <button onClick={() => setError("")} className="ml-auto"><X size={14} /></button>
        </div>
      )}
      {success && (
        <div className="mb-4 flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 border border-emerald-100 p-3 rounded-lg" data-testid="mfa-settings-success">
          <Check size={16} className="flex-shrink-0" /> {success}
          <button onClick={() => setSuccess("")} className="ml-auto"><X size={14} /></button>
        </div>
      )}

      {/* Current Status */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {status?.mfa_enabled ? (
              <ShieldCheck size={20} className="text-emerald-600" />
            ) : (
              <ShieldOff size={20} className="text-slate-400" />
            )}
            <div>
              <p className="text-sm font-medium text-slate-900" data-testid="mfa-status-label">
                {status?.mfa_enabled ? "MFA is enabled" : "MFA is not enabled"}
              </p>
              <p className="text-xs text-slate-500">
                {status?.mfa_enabled ? "Your account is protected with authenticator app" : "Enable MFA to protect your account"}
              </p>
            </div>
          </div>
          <div>
            {status?.mfa_enabled ? (
              <button
                data-testid="mfa-disable-btn"
                onClick={() => { setStep("disabling"); setError(""); setSuccess(""); }}
                className="px-4 py-2 text-sm font-medium text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition"
              >
                Disable
              </button>
            ) : (
              <button
                data-testid="mfa-enable-btn"
                onClick={handleSetup}
                disabled={actionLoading}
                className="px-4 py-2 text-sm font-medium text-white bg-[#0176D3] rounded-lg hover:bg-[#0161B0] transition disabled:opacity-60 flex items-center gap-2"
              >
                {actionLoading ? <Loader2 size={14} className="animate-spin" /> : <Smartphone size={14} />}
                Enable MFA
              </button>
            )}
          </div>
        </div>
        {status?.tenant_mfa_enforced && !status?.mfa_enabled && (
          <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800" data-testid="mfa-enforce-warning">
            <strong>Required:</strong> Your workspace admin requires all users to enable MFA.
          </div>
        )}
      </div>

      {/* Setup Flow */}
      {step === "setup" && setupData && (
        <div className="bg-white rounded-xl border border-slate-200 p-5" data-testid="mfa-setup-panel">
          <h3 className="text-base font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <QrCode size={18} /> Set Up Authenticator App
          </h3>
          <ol className="text-sm text-slate-600 space-y-2 mb-5 list-decimal list-inside">
            <li>Download an authenticator app (Google Authenticator, Authy, etc.)</li>
            <li>Scan the QR code below with your app</li>
            <li>Enter the 6-digit code shown in your app</li>
          </ol>

          <div className="flex flex-col items-center mb-5">
            <div className="p-3 bg-white border-2 border-slate-200 rounded-xl mb-3">
              <img src={setupData.qr_code} alt="TOTP QR Code" className="w-48 h-48" data-testid="mfa-qr-code" />
            </div>
            <p className="text-xs text-slate-500 mb-2">Can't scan? Enter this key manually:</p>
            <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 rounded-lg border border-slate-200">
              <code className="text-xs font-mono text-slate-700 select-all" data-testid="mfa-manual-key">{setupData.secret}</code>
              <button onClick={copySecret} className="text-slate-400 hover:text-slate-600">
                {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
              </button>
            </div>
          </div>

          <p className="text-sm text-slate-700 font-medium mb-3">Enter verification code:</p>
          <div className="flex justify-center gap-2 mb-4" onPaste={handlePaste} data-testid="mfa-setup-code-inputs">
            {code.map((digit, i) => (
              <input
                key={i}
                ref={el => inputRefs.current[i] = el}
                data-testid={`mfa-setup-code-${i}`}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={e => handleDigitChange(i, e.target.value)}
                onKeyDown={e => handleKeyDown(i, e)}
                className="w-11 h-12 text-center text-lg font-semibold border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0176D3] focus:border-transparent"
                disabled={actionLoading}
              />
            ))}
          </div>
          <div className="flex gap-3">
            <button
              data-testid="mfa-cancel-setup"
              onClick={() => { setStep("idle"); setSetupData(null); setError(""); }}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              data-testid="mfa-confirm-setup"
              onClick={handleVerifySetup}
              disabled={actionLoading || code.join("").length !== 6}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-[#0176D3] rounded-lg hover:bg-[#0161B0] disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {actionLoading ? <Loader2 size={14} className="animate-spin" /> : null}
              Verify & Enable
            </button>
          </div>
        </div>
      )}

      {/* Disable Flow */}
      {step === "disabling" && (
        <div className="bg-white rounded-xl border border-slate-200 p-5" data-testid="mfa-disable-panel">
          <h3 className="text-base font-semibold text-slate-900 mb-2">Disable Two-Factor Authentication</h3>
          <p className="text-sm text-slate-500 mb-4">Enter your password to confirm disabling MFA.</p>
          <div className="relative mb-4">
            <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              data-testid="mfa-disable-password"
              type="password"
              value={disablePassword}
              onChange={e => setDisablePassword(e.target.value)}
              placeholder="Enter your password"
              className="w-full border border-slate-200 rounded-lg pl-10 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-transparent"
            />
          </div>
          <div className="flex gap-3">
            <button
              data-testid="mfa-cancel-disable"
              onClick={() => { setStep("idle"); setDisablePassword(""); setError(""); }}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              data-testid="mfa-confirm-disable"
              onClick={handleDisable}
              disabled={actionLoading || !disablePassword}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {actionLoading ? <Loader2 size={14} className="animate-spin" /> : null}
              Disable MFA
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MFASettings;
