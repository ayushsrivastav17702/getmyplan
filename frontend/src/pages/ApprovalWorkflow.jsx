import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import { toast } from "sonner";
import {
  FileSpreadsheet, Clock, CheckCircle, XCircle, ArrowRight,
  Loader2, RefreshCw, Send, ThumbsUp, ThumbsDown, AlertCircle,
  ChevronDown, ChevronRight, Eye, MessageSquare, User,
} from "lucide-react";

const STAGES = [
  { key: "draft", label: "Draft", color: "bg-slate-100 text-slate-700 border-slate-200", icon: FileSpreadsheet },
  { key: "submitted", label: "Submitted", color: "bg-blue-100 text-blue-700 border-blue-200", icon: Send },
  { key: "category_approved", label: "Category Approved", color: "bg-indigo-100 text-indigo-700 border-indigo-200", icon: ThumbsUp },
  { key: "senior_approved", label: "Senior Approved", color: "bg-violet-100 text-violet-700 border-violet-200", icon: ThumbsUp },
  { key: "head_approved", label: "Head Approved", color: "bg-emerald-100 text-emerald-700 border-emerald-200", icon: CheckCircle },
  { key: "ordered", label: "Ordered", color: "bg-green-100 text-green-800 border-green-200", icon: CheckCircle },
  { key: "rejected", label: "Rejected", color: "bg-red-100 text-red-700 border-red-200", icon: XCircle },
];

const ACTIONS = {
  draft: [{ action: "submit", label: "Submit for Approval", icon: Send, color: "bg-blue-600 hover:bg-blue-700" }],
  submitted: [
    { action: "approve_category", label: "Category Approve", icon: ThumbsUp, color: "bg-indigo-600 hover:bg-indigo-700" },
    { action: "reject", label: "Reject", icon: ThumbsDown, color: "bg-red-600 hover:bg-red-700", needsComment: true },
    { action: "request_changes", label: "Request Changes", icon: MessageSquare, color: "bg-amber-600 hover:bg-amber-700", needsComment: true },
  ],
  category_approved: [
    { action: "approve_senior", label: "Senior Approve", icon: ThumbsUp, color: "bg-violet-600 hover:bg-violet-700" },
    { action: "reject", label: "Reject", icon: ThumbsDown, color: "bg-red-600 hover:bg-red-700", needsComment: true },
  ],
  senior_approved: [
    { action: "approve_head", label: "Head Approve", icon: ThumbsUp, color: "bg-emerald-600 hover:bg-emerald-700" },
    { action: "reject", label: "Reject", icon: ThumbsDown, color: "bg-red-600 hover:bg-red-700", needsComment: true },
  ],
  head_approved: [
    { action: "finance_ack", label: "Finance Acknowledge", icon: CheckCircle, color: "bg-green-600 hover:bg-green-700" },
  ],
};

export default function ApprovalWorkflow() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState({});
  const [expandedPlan, setExpandedPlan] = useState(null);
  const [history, setHistory] = useState({});
  const [comment, setComment] = useState("");
  const [commentPlan, setCommentPlan] = useState(null);
  const [filterStage, setFilterStage] = useState("all");

  const fetchPlans = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/buy-planning/buy-plans?limit=100`);
      setPlans(res.data.plans || []);
    } catch { toast.error("Failed to load plans"); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchPlans(); }, [fetchPlans]);

  const doAction = async (planId, action, requireComment) => {
    if (requireComment && !comment.trim()) {
      toast.error("Comment is required");
      return;
    }
    setActing(p => ({ ...p, [planId]: action }));
    try {
      await axios.post(`${API}/buy-planning/buy-plans/${planId}/approval`, {
        action,
        comment: comment || `${action} via workflow dashboard`,
      });
      toast.success(`Action "${action}" completed`);
      setComment("");
      setCommentPlan(null);
      fetchPlans();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Action failed");
    }
    setActing(p => ({ ...p, [planId]: null }));
  };

  const loadHistory = async (planId) => {
    if (expandedPlan === planId) { setExpandedPlan(null); return; }
    setExpandedPlan(planId);
    if (!history[planId]) {
      try {
        const res = await axios.get(`${API}/buy-planning/buy-plans/${planId}/approval-history`);
        setHistory(h => ({ ...h, [planId]: res.data.history || [] }));
      } catch { /* silent */ }
    }
  };

  // Count plans per stage
  const counts = {};
  STAGES.forEach(s => { counts[s.key] = 0; });
  plans.forEach(p => { counts[p.status] = (counts[p.status] || 0) + 1; });

  const filtered = filterStage === "all" ? plans : plans.filter(p => p.status === filterStage);
  const pending = plans.filter(p => !["draft", "ordered", "rejected"].includes(p.status));

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24" data-testid="approval-loading">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div data-testid="approval-workflow-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" data-testid="approval-title">Approval Workflow</h1>
          <p className="text-sm text-slate-500 mt-1">
            {pending.length} plan{pending.length !== 1 ? "s" : ""} awaiting action across {STAGES.length} stages
          </p>
        </div>
        <button onClick={fetchPlans} data-testid="approval-refresh-btn" className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      {/* Pipeline Overview */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 mb-6" data-testid="approval-pipeline">
        {STAGES.map(s => {
          const Icon = s.icon;
          const isActive = filterStage === s.key;
          return (
            <button
              key={s.key}
              data-testid={`stage-filter-${s.key}`}
              onClick={() => setFilterStage(filterStage === s.key ? "all" : s.key)}
              className={`rounded-xl border p-3 text-center transition-all ${isActive ? "ring-2 ring-indigo-400 shadow-md" : "hover:shadow-sm"} ${s.color}`}
            >
              <Icon className="h-4 w-4 mx-auto mb-1 opacity-70" />
              <div className="text-xl font-bold">{counts[s.key] || 0}</div>
              <div className="text-[10px] font-medium uppercase tracking-wide opacity-70 truncate">{s.label}</div>
            </button>
          );
        })}
      </div>

      {/* Plans List */}
      {filtered.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-10 text-center" data-testid="approval-empty">
          <FileSpreadsheet className="h-10 w-10 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-700">No Plans {filterStage !== "all" ? `in "${filterStage}" stage` : ""}</h3>
          <p className="text-sm text-slate-500 mt-1">Generate a buy plan to start the approval workflow.</p>
        </div>
      ) : (
        <div className="space-y-3" data-testid="approval-plans-list">
          {filtered.map(plan => {
            const stage = STAGES.find(s => s.key === plan.status) || STAGES[0];
            const StageIcon = stage.icon;
            const actions = ACTIONS[plan.status] || [];
            const isExpanded = expandedPlan === plan.plan_id;
            const planHistory = history[plan.plan_id] || [];

            return (
              <div key={plan.plan_id} data-testid={`plan-row-${plan.plan_id}`} className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                {/* Plan Header */}
                <div className="p-4">
                  <div className="flex items-center justify-between gap-4 flex-wrap">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className={`flex-shrink-0 p-2 rounded-lg border ${stage.color}`}>
                        <StageIcon className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <h3 className="font-semibold text-slate-900 truncate">{plan.plan_name || "Untitled Plan"}</h3>
                        <div className="flex items-center gap-3 text-xs text-slate-500 mt-0.5 flex-wrap">
                          <span className="flex items-center gap-1"><User className="h-3 w-3" /> {plan.generated_by}</span>
                          <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {plan.generated_at ? new Date(plan.generated_at).toLocaleDateString() : "N/A"}</span>
                          <span>{plan.sku_count} SKUs</span>
                          {plan.totals?.total_value > 0 && <span className="font-medium">{fmtCur(plan.totals.total_value)}</span>}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      {/* Status badge */}
                      <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border ${stage.color}`}>
                        <StageIcon className="h-3 w-3" /> {stage.label}
                      </span>

                      {/* Action buttons */}
                      {actions.map(a => {
                        const isActing = acting[plan.plan_id] === a.action;
                        if (a.needsComment && commentPlan !== plan.plan_id) {
                          return (
                            <button key={a.action} data-testid={`action-${a.action}-${plan.plan_id}`}
                              onClick={() => { setCommentPlan(plan.plan_id); setComment(""); }}
                              className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg text-white transition-colors ${a.color}`}>
                              <a.icon className="h-3 w-3" /> {a.label}
                            </button>
                          );
                        }
                        if (a.needsComment) return null; // Handled by comment box below
                        return (
                          <button key={a.action} data-testid={`action-${a.action}-${plan.plan_id}`}
                            onClick={() => doAction(plan.plan_id, a.action, false)}
                            disabled={isActing}
                            className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg text-white transition-colors ${a.color} disabled:opacity-50`}>
                            {isActing ? <Loader2 className="h-3 w-3 animate-spin" /> : <a.icon className="h-3 w-3" />} {a.label}
                          </button>
                        );
                      })}

                      {/* History toggle */}
                      <button data-testid={`history-toggle-${plan.plan_id}`}
                        onClick={() => loadHistory(plan.plan_id)}
                        className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 px-2 py-1.5 rounded-lg hover:bg-slate-50 transition-colors">
                        <Eye className="h-3 w-3" /> {isExpanded ? "Hide" : "History"}
                        {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                      </button>
                    </div>
                  </div>

                  {/* Comment box for reject/request_changes */}
                  {commentPlan === plan.plan_id && (
                    <div className="mt-3 flex items-center gap-2" data-testid={`comment-box-${plan.plan_id}`}>
                      <input
                        type="text"
                        value={comment}
                        onChange={e => setComment(e.target.value)}
                        placeholder="Enter comment (required)..."
                        className="flex-1 text-sm border border-slate-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none"
                        data-testid={`comment-input-${plan.plan_id}`}
                      />
                      {actions.filter(a => a.needsComment).map(a => (
                        <button key={a.action} data-testid={`confirm-${a.action}-${plan.plan_id}`}
                          onClick={() => doAction(plan.plan_id, a.action, true)}
                          disabled={acting[plan.plan_id] === a.action}
                          className={`inline-flex items-center gap-1 text-xs font-medium px-3 py-2 rounded-lg text-white ${a.color} disabled:opacity-50`}>
                          {acting[plan.plan_id] === a.action ? <Loader2 className="h-3 w-3 animate-spin" /> : <a.icon className="h-3 w-3" />} {a.label}
                        </button>
                      ))}
                      <button onClick={() => setCommentPlan(null)} className="text-xs text-slate-400 hover:text-slate-600 px-2 py-2">Cancel</button>
                    </div>
                  )}
                </div>

                {/* Approval History Timeline */}
                {isExpanded && (
                  <div className="border-t border-slate-100 bg-slate-50/50 px-4 py-3" data-testid={`history-${plan.plan_id}`}>
                    {planHistory.length === 0 ? (
                      <p className="text-xs text-slate-400 text-center py-2">No approval history yet</p>
                    ) : (
                      <div className="space-y-2">
                        {planHistory.map((h, i) => (
                          <div key={i} className="flex items-start gap-3 text-xs">
                            <div className={`flex-shrink-0 w-2 h-2 rounded-full mt-1.5 ${
                              h.action.includes("approve") || h.action === "finance_ack" ? "bg-emerald-500" :
                              h.action === "reject" ? "bg-red-500" :
                              h.action === "request_changes" ? "bg-amber-500" : "bg-blue-500"
                            }`} />
                            <div className="flex-1 min-w-0">
                              <span className="font-medium text-slate-700 capitalize">{h.action.replace(/_/g, " ")}</span>
                              <span className="text-slate-400 ml-2">by {h.performed_by}</span>
                              <span className="text-slate-400 ml-2">{h.performed_at ? new Date(h.performed_at).toLocaleString() : ""}</span>
                              {h.comment && <p className="text-slate-500 mt-0.5 italic">"{h.comment}"</p>}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function fmtCur(v) {
  if (!v) return "";
  if (v >= 1e7) return `${(v / 1e7).toFixed(2)} Cr`;
  if (v >= 1e5) return `${(v / 1e5).toFixed(2)} L`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)} K`;
  return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
}
