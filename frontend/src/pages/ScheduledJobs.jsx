import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  Clock, Plus, Play, Pause, Trash2, Calendar,
  Loader2, AlertCircle, CheckCircle, RotateCw,
  ChevronDown, X
} from "lucide-react";

const ANALYSIS_TYPES = [
  { key: "executive_dashboard", label: "Executive Dashboard" },
  { key: "gap_analysis", label: "Gap Analysis" },
  { key: "stock_out", label: "Stock-Out Analysis" },
  { key: "replenishment", label: "Replenishment" },
  { key: "doh_analysis", label: "DOH Analysis" },
  { key: "planogram", label: "Planogram Fill Rate" },
  { key: "ai_demand", label: "AI Demand Forecast" },
  { key: "data_quality", label: "Data Quality Check" },
];

const FREQUENCY_OPTIONS = [
  { key: "daily", label: "Daily" },
  { key: "weekly", label: "Weekly" },
  { key: "monthly", label: "Monthly" },
];

const DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const STATUS_COLORS = {
  completed: "bg-green-50 text-green-700 border-green-200",
  failed: "bg-red-50 text-red-700 border-red-200",
  running: "bg-blue-50 text-blue-700 border-blue-200",
  null: "bg-slate-50 text-slate-500 border-slate-200",
};

const ScheduledJobs = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [actionLoading, setActionLoading] = useState(null);

  // Create form
  const [form, setForm] = useState({
    name: "",
    analysis_type: "executive_dashboard",
    frequency: "daily",
    run_time: "06:00",
    day_of_week: "monday",
    day_of_month: 1,
    notify_email: true,
  });

  const fetchJobs = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/scheduled-jobs/`);
      setJobs(resp.data.jobs || []);
    } catch {
      setError("Failed to load jobs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const clearMessages = () => { setError(""); setSuccess(""); };

  const handleCreate = async () => {
    clearMessages();
    if (!form.name.trim()) { setError("Job name is required"); return; }
    setActionLoading("create");
    try {
      const payload = {
        name: form.name,
        analysis_type: form.analysis_type,
        frequency: form.frequency,
        run_time: form.run_time,
        notify_email: form.notify_email,
        is_active: true,
      };
      if (form.frequency === "weekly") payload.day_of_week = form.day_of_week;
      if (form.frequency === "monthly") payload.day_of_month = form.day_of_month;

      await axios.post(`${API}/scheduled-jobs/`, payload);
      setSuccess("Job created successfully");
      setShowCreate(false);
      setForm({ name: "", analysis_type: "executive_dashboard", frequency: "daily", run_time: "06:00", day_of_week: "monday", day_of_month: 1, notify_email: true });
      fetchJobs();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create job");
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggle = async (jobId) => {
    clearMessages();
    setActionLoading(jobId);
    try {
      await axios.post(`${API}/scheduled-jobs/${jobId}/toggle`);
      fetchJobs();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to toggle job");
    } finally {
      setActionLoading(null);
    }
  };

  const handleRunNow = async (jobId) => {
    clearMessages();
    setActionLoading(`run-${jobId}`);
    try {
      const resp = await axios.post(`${API}/scheduled-jobs/${jobId}/run-now`);
      setSuccess(resp.data.message);
      fetchJobs();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to run job");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (jobId) => {
    clearMessages();
    setActionLoading(`del-${jobId}`);
    try {
      await axios.delete(`${API}/scheduled-jobs/${jobId}`);
      setSuccess("Job deleted");
      fetchJobs();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete job");
    } finally {
      setActionLoading(null);
    }
  };

  const getAnalysisLabel = (key) => ANALYSIS_TYPES.find(t => t.key === key)?.label || key;
  const getScheduleText = (job) => {
    const time = job.run_time || "06:00";
    if (job.frequency === "daily") return `Every day at ${time}`;
    if (job.frequency === "weekly") return `Every ${job.day_of_week || "monday"} at ${time}`;
    if (job.frequency === "monthly") return `${job.day_of_month || 1}${["st","nd","rd"][((job.day_of_month||1)-1)%10]||"th"} of every month at ${time}`;
    return job.frequency;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 size={24} className="animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="scheduled-jobs-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Scheduled Jobs</h1>
          <p className="text-sm text-slate-500 mt-0.5">Automate recurring analysis runs</p>
        </div>
        <button
          onClick={() => { setShowCreate(!showCreate); clearMessages(); }}
          data-testid="create-job-btn"
          className="px-4 py-2 bg-[#0176D3] hover:bg-[#0161B0] text-white text-sm font-medium rounded-lg transition flex items-center gap-2"
        >
          <Plus size={16} /> New Job
        </button>
      </div>

      {/* Messages */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="job-error">
          <AlertCircle size={16} /> {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 border border-green-100 p-3 rounded-lg" data-testid="job-success">
          <CheckCircle size={16} /> {success}
        </div>
      )}

      {/* Create Job Form */}
      {showCreate && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6" data-testid="create-job-form">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-900">Create New Scheduled Job</h3>
            <button onClick={() => setShowCreate(false)} className="text-slate-400 hover:text-slate-600"><X size={18} /></button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Job Name</label>
              <input
                data-testid="job-name-input"
                value={form.name}
                onChange={e => setForm({ ...form, name: e.target.value })}
                className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
                placeholder="e.g., Daily Stock Check"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Analysis Type</label>
              <select
                data-testid="job-analysis-type"
                value={form.analysis_type}
                onChange={e => setForm({ ...form, analysis_type: e.target.value })}
                className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] bg-white"
              >
                {ANALYSIS_TYPES.map(t => <option key={t.key} value={t.key}>{t.label}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Frequency</label>
              <select
                data-testid="job-frequency"
                value={form.frequency}
                onChange={e => setForm({ ...form, frequency: e.target.value })}
                className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] bg-white"
              >
                {FREQUENCY_OPTIONS.map(f => <option key={f.key} value={f.key}>{f.label}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Run Time (UTC)</label>
              <input
                data-testid="job-run-time"
                type="time"
                value={form.run_time}
                onChange={e => setForm({ ...form, run_time: e.target.value })}
                className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
              />
            </div>

            {form.frequency === "weekly" && (
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Day of Week</label>
                <select
                  data-testid="job-day-of-week"
                  value={form.day_of_week}
                  onChange={e => setForm({ ...form, day_of_week: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] bg-white"
                >
                  {DAYS_OF_WEEK.map(d => <option key={d.toLowerCase()} value={d.toLowerCase()}>{d}</option>)}
                </select>
              </div>
            )}

            {form.frequency === "monthly" && (
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Day of Month</label>
                <select
                  data-testid="job-day-of-month"
                  value={form.day_of_month}
                  onChange={e => setForm({ ...form, day_of_month: parseInt(e.target.value) })}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] bg-white"
                >
                  {Array.from({ length: 28 }, (_, i) => i + 1).map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="flex items-center gap-2 md:col-span-2">
              <input
                data-testid="job-notify-email"
                type="checkbox"
                checked={form.notify_email}
                onChange={e => setForm({ ...form, notify_email: e.target.checked })}
                className="rounded border-slate-300"
              />
              <label className="text-sm text-slate-600">Email notification on completion</label>
            </div>
          </div>

          <div className="mt-5 flex justify-end gap-3">
            <button
              onClick={() => setShowCreate(false)}
              className="px-4 py-2 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              onClick={handleCreate}
              disabled={actionLoading === "create"}
              data-testid="save-job-btn"
              className="px-4 py-2 bg-[#0176D3] hover:bg-[#0161B0] text-white text-sm font-medium rounded-lg transition flex items-center gap-2 disabled:opacity-60"
            >
              {actionLoading === "create" ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
              Create Job
            </button>
          </div>
        </div>
      )}

      {/* Jobs List */}
      {jobs.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-10 text-center" data-testid="no-jobs">
          <Clock size={40} className="mx-auto text-slate-300 mb-3" />
          <p className="text-slate-500 text-sm">No scheduled jobs yet</p>
          <p className="text-slate-400 text-xs mt-1">Create your first job to automate analysis runs</p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map(job => (
            <div
              key={job.job_id}
              data-testid={`job-card-${job.job_id}`}
              className={`bg-white rounded-xl border shadow-sm transition ${
                job.is_active ? "border-slate-200" : "border-slate-100 opacity-70"
              }`}
            >
              <div className="p-4 flex flex-col md:flex-row md:items-center gap-3">
                {/* Status indicator */}
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                  !job.is_active ? "bg-slate-300" :
                  job.last_status === "completed" ? "bg-green-400" :
                  job.last_status === "failed" ? "bg-red-400" : "bg-slate-300"
                }`} />

                {/* Job info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-slate-900 text-sm truncate" data-testid={`job-name-${job.job_id}`}>{job.name}</h4>
                    {!job.is_active && (
                      <span className="text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded font-medium uppercase">Paused</span>
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1">
                    <span className="text-xs text-slate-500">{getAnalysisLabel(job.analysis_type)}</span>
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Calendar size={11} /> {getScheduleText(job)}
                    </span>
                    {job.last_run && (
                      <span className={`text-xs px-1.5 py-0.5 rounded border ${STATUS_COLORS[job.last_status] || STATUS_COLORS.null}`}>
                        Last: {new Date(job.last_run).toLocaleString()}
                      </span>
                    )}
                    {job.run_count > 0 && (
                      <span className="text-xs text-slate-400">{job.run_count} runs</span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => handleRunNow(job.job_id)}
                    disabled={!!actionLoading}
                    data-testid={`run-job-${job.job_id}`}
                    className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                    title="Run now"
                  >
                    {actionLoading === `run-${job.job_id}` ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                  </button>
                  <button
                    onClick={() => handleToggle(job.job_id)}
                    disabled={!!actionLoading}
                    data-testid={`toggle-job-${job.job_id}`}
                    className={`p-2 rounded-lg transition ${
                      job.is_active ? "text-amber-500 hover:bg-amber-50" : "text-green-500 hover:bg-green-50"
                    }`}
                    title={job.is_active ? "Pause" : "Activate"}
                  >
                    {actionLoading === job.job_id ? <Loader2 size={16} className="animate-spin" /> : job.is_active ? <Pause size={16} /> : <RotateCw size={16} />}
                  </button>
                  <button
                    onClick={() => handleDelete(job.job_id)}
                    disabled={!!actionLoading}
                    data-testid={`delete-job-${job.job_id}`}
                    className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition"
                    title="Delete"
                  >
                    {actionLoading === `del-${job.job_id}` ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ScheduledJobs;
