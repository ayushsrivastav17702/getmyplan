import { useState, useEffect, useCallback } from "react";
import {
  Mail, Play, Loader2, AlertCircle, CheckCircle2,
  X, Clock, Send, ToggleLeft, ToggleRight,
  ChevronDown, ChevronUp, Zap, Users, History
} from "lucide-react";
import axios from "axios";
import { API } from "../App";

const STAGE_COLORS = {
  not_verified: { bg: "bg-blue-50", border: "border-blue-200", text: "text-blue-700", icon: "bg-blue-100" },
  not_onboarded: { bg: "bg-violet-50", border: "border-violet-200", text: "text-violet-700", icon: "bg-violet-100" },
  no_upload: { bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-700", icon: "bg-amber-100" },
  inactive: { bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-700", icon: "bg-emerald-100" },
};

const DripCampaigns = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [logs, setLogs] = useState([]);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [toggling, setToggling] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showHistory, setShowHistory] = useState(false);
  const [runResult, setRunResult] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [campResp, histResp, runsResp] = await Promise.all([
        axios.get(`${API}/drip/campaigns`),
        axios.get(`${API}/drip/history?limit=20`),
        axios.get(`${API}/drip/runs?limit=5`),
      ]);
      setCampaigns(campResp.data.campaigns || []);
      setLogs(histResp.data.logs || []);
      setRuns(runsResp.data.runs || []);
    } catch {
      setError("Failed to load campaign data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleToggle = async (campaignId, currentEnabled) => {
    setToggling(campaignId);
    setError("");
    try {
      await axios.put(`${API}/drip/campaigns/${campaignId}/toggle`, {
        enabled: !currentEnabled,
      });
      setCampaigns(prev =>
        prev.map(c => c.campaign_id === campaignId ? { ...c, enabled: !currentEnabled } : c)
      );
    } catch {
      setError("Failed to update campaign");
    } finally {
      setToggling(null);
    }
  };

  const handleRunNow = async () => {
    setRunning(true);
    setError("");
    setSuccess("");
    setRunResult(null);
    try {
      const resp = await axios.post(`${API}/drip/run`);
      const r = resp.data;
      setRunResult(r);
      setSuccess(r.message);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to run drip check");
    } finally {
      setRunning(false);
    }
  };

  const formatDate = (iso) => {
    if (!iso) return "—";
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit",
    });
  };

  if (loading) return (
    <div className="flex items-center justify-center py-20" data-testid="drip-loading">
      <Loader2 className="animate-spin text-slate-400" size={32} />
    </div>
  );

  return (
    <div data-testid="drip-campaigns-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-purple-100">
            <Mail size={22} className="text-purple-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900" data-testid="drip-title">Drip Campaigns</h1>
            <p className="text-sm text-slate-500">Automated emails to re-engage users stuck in the funnel</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            data-testid="toggle-history-btn"
            onClick={() => setShowHistory(!showHistory)}
            className="px-4 py-2.5 text-sm font-medium text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50 flex items-center gap-2"
          >
            <History size={16} /> {showHistory ? "Hide History" : "Show History"}
          </button>
          <button
            data-testid="run-drip-btn"
            onClick={handleRunNow}
            disabled={running}
            className="px-4 py-2.5 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition flex items-center gap-2 disabled:opacity-60"
          >
            {running ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
            {running ? "Running..." : "Run Now"}
          </button>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="drip-error">
          <AlertCircle size={16} className="flex-shrink-0" /> {error}
          <button onClick={() => setError("")} className="ml-auto"><X size={14} /></button>
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 border border-emerald-100 p-3 rounded-lg" data-testid="drip-success">
          <CheckCircle2 size={16} className="flex-shrink-0" /> {success}
          <button onClick={() => setSuccess("")} className="ml-auto"><X size={14} /></button>
        </div>
      )}

      {/* Auto-run info */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 flex items-center gap-3 text-sm text-slate-600" data-testid="auto-run-info">
        <Zap size={16} className="text-purple-500" />
        <span>Campaigns run automatically once daily. You can also trigger a manual run anytime.</span>
        {runs.length > 0 && (
          <span className="ml-auto text-xs text-slate-400">
            Last run: {formatDate(runs[0].run_at)} ({runs[0].sent} sent)
          </span>
        )}
      </div>

      {/* Campaign Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="campaign-cards">
        {campaigns.map((c) => {
          const colors = STAGE_COLORS[c.campaign_id] || STAGE_COLORS.inactive;
          return (
            <div
              key={c.campaign_id}
              className={`rounded-xl border p-5 transition ${c.enabled ? `${colors.bg} ${colors.border}` : "bg-slate-50 border-slate-200 opacity-70"}`}
              data-testid={`campaign-${c.campaign_id}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${c.enabled ? colors.icon : "bg-slate-200"}`}>
                    <Send size={16} className={c.enabled ? colors.text : "text-slate-400"} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900" data-testid={`campaign-name-${c.campaign_id}`}>{c.name}</h3>
                    <p className="text-xs text-slate-500">{c.description}</p>
                  </div>
                </div>
                <button
                  data-testid={`toggle-${c.campaign_id}`}
                  onClick={() => handleToggle(c.campaign_id, c.enabled)}
                  disabled={toggling === c.campaign_id}
                  className="flex-shrink-0"
                >
                  {toggling === c.campaign_id ? (
                    <Loader2 size={24} className="animate-spin text-slate-400" />
                  ) : c.enabled ? (
                    <ToggleRight size={28} className="text-purple-600" />
                  ) : (
                    <ToggleLeft size={28} className="text-slate-400" />
                  )}
                </button>
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <Clock size={12} /> Drip: Day {(c.drip_days || [1, 3, 7]).join(", ")}
                </span>
                <span className="flex items-center gap-1">
                  <Users size={12} /> {c.total_sent || 0} sent total
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Run Result Detail */}
      {runResult && runResult.details && runResult.details.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5" data-testid="run-result">
          <h3 className="text-sm font-semibold text-slate-900 mb-3">Latest Run Result</h3>
          <div className="flex gap-4 mb-3 text-sm">
            <span className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-lg font-medium">{runResult.sent} sent</span>
            <span className="px-3 py-1 bg-slate-50 text-slate-600 rounded-lg">{runResult.skipped} skipped</span>
            {runResult.errors > 0 && <span className="px-3 py-1 bg-red-50 text-red-600 rounded-lg">{runResult.errors} errors</span>}
          </div>
          <div className="space-y-1">
            {runResult.details.map((d, i) => (
              <div key={i} className="flex items-center gap-3 text-xs py-1.5 border-b border-slate-50 last:border-0">
                <span className={`w-2 h-2 rounded-full ${d.status === "sent" ? "bg-emerald-500" : "bg-red-500"}`} />
                <span className="text-slate-600 w-56 truncate">{d.email}</span>
                <span className="text-slate-500">{d.campaign}</span>
                <span className="text-slate-400 ml-auto">Day {d.drip_day}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* History Section */}
      {showHistory && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden" data-testid="drip-history-section">
          <div className="p-4 border-b border-slate-100">
            <h3 className="text-sm font-semibold text-slate-900">Email Send History ({logs.length})</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="drip-history-table">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase">Recipient</th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase">Campaign</th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase">Subject</th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase">Drip Day</th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase">Sent At</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((l, i) => (
                  <tr key={i} className={`border-b border-slate-50 ${i % 2 === 0 ? "" : "bg-slate-50/50"}`}>
                    <td className="px-4 py-2.5 text-slate-700">{l.email}</td>
                    <td className="px-4 py-2.5 text-slate-600">{l.campaign_name}</td>
                    <td className="px-4 py-2.5 text-slate-500 truncate max-w-[200px]">{l.subject}</td>
                    <td className="px-4 py-2.5">
                      <span className="px-2 py-0.5 text-xs font-medium bg-purple-50 text-purple-700 rounded-full">Day {l.drip_day}</span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-400 text-xs">{formatDate(l.sent_at)}</td>
                  </tr>
                ))}
                {logs.length === 0 && (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-400 text-sm">No emails sent yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default DripCampaigns;
