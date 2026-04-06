import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import axios from "axios";
import { API } from "../App";
import { CheckCircle, XCircle, Loader2, Building2 } from "lucide-react";

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState("verifying"); // verifying | success | error
  const [message, setMessage] = useState("");
  const [tenantId, setTenantId] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      setMessage("No verification token found in URL.");
      return;
    }

    const verify = async () => {
      try {
        const resp = await axios.post(`${API}/signup/verify-email`, { token });
        setStatus("success");
        setMessage(resp.data.message);
        setTenantId(resp.data.tenant_id || "");
      } catch (err) {
        setStatus("error");
        setMessage(err.response?.data?.detail || "Verification failed. The link may have expired.");
      }
    };
    verify();
  }, [searchParams]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex items-center justify-center p-4" data-testid="verify-email-page">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden">
          <div className="p-8 text-center">
            {/* Logo */}
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-[#0176D3] mb-6">
              <Building2 size={28} className="text-white" />
            </div>

            {/* Verifying */}
            {status === "verifying" && (
              <>
                <Loader2 size={40} className="text-[#0176D3] animate-spin mx-auto mb-4" />
                <h2 className="text-xl font-bold text-slate-900 mb-2" data-testid="verify-status-loading">Verifying your email...</h2>
                <p className="text-slate-500">Please wait while we verify your account.</p>
              </>
            )}

            {/* Success */}
            {status === "success" && (
              <>
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle size={32} className="text-green-600" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2" data-testid="verify-status-success">Email Verified!</h2>
                <p className="text-slate-600 mb-6">{message}</p>
                <Link
                  to="/"
                  data-testid="verify-go-login"
                  className="inline-flex items-center gap-2 px-6 py-2.5 bg-[#0176D3] hover:bg-[#0161B0] text-white font-medium rounded-lg transition-colors"
                >
                  Go to Sign In
                </Link>
                {tenantId && (
                  <p className="text-xs text-slate-400 mt-4">
                    Your tenant: <strong className="text-slate-600">{tenantId}</strong>
                  </p>
                )}
              </>
            )}

            {/* Error */}
            {status === "error" && (
              <>
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <XCircle size={32} className="text-red-600" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2" data-testid="verify-status-error">Verification Failed</h2>
                <p className="text-slate-600 mb-6">{message}</p>
                <div className="space-y-2">
                  <Link
                    to="/signup"
                    data-testid="verify-go-signup"
                    className="block w-full py-2.5 bg-[#0176D3] hover:bg-[#0161B0] text-white font-medium rounded-lg transition-colors text-center"
                  >
                    Back to Signup
                  </Link>
                  <Link
                    to="/"
                    data-testid="verify-go-login-err"
                    className="block w-full py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-600 font-medium rounded-lg transition-colors text-center"
                  >
                    Go to Login
                  </Link>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;
