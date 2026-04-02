import { Shield, ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const Unauthorized = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div className="flex flex-col items-center justify-center py-24 text-center" data-testid="unauthorized-page">
      <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mb-6">
        <Shield size={32} className="text-red-400" />
      </div>
      <h1 className="text-2xl font-bold text-slate-900 mb-2">Access Denied</h1>
      <p className="text-sm text-slate-500 max-w-md mb-1">
        Your role <span className="font-semibold text-slate-700 capitalize">({user?.role || "unknown"})</span> does not have permission to view this page.
      </p>
      <p className="text-xs text-slate-400 mb-8">Contact your tenant administrator to request access.</p>
      <button
        data-testid="go-home-btn"
        onClick={() => navigate("/")}
        className="inline-flex items-center gap-2 bg-[#0176D3] hover:bg-[#0161B0] text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
      >
        <ArrowLeft size={16} /> Back to Home
      </button>
    </div>
  );
};

export default Unauthorized;
