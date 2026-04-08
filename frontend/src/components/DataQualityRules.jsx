import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import {
  Plus, Play, Pause, Trash2, Settings2, CheckCircle, XCircle,
  AlertTriangle, Loader2, X, ChevronDown, Zap, Shield,
  ToggleLeft, ToggleRight, FileText, Columns
} from "lucide-react";

const FILE_TYPES = [
  { key: "daily_sales", label: "Daily Sales" },
  { key: "store_inventory", label: "Store Inventory" },
  { key: "sku_ean_master", label: "SKU/EAN Master" },
  { key: "style_master", label: "Style Master" },
  { key: "store_master", label: "Store Master" },
];

const RULE_TYPES = [
  { key: "threshold", label: "Threshold", desc: "Column value must satisfy a comparison (>, <, ==, etc.)" },
  { key: "null_check", label: "Null Check", desc: "Column must not have null/empty values beyond threshold" },
  { key: "pattern", label: "Pattern Match", desc: "Column values must match a regex pattern" },
  { key: "uniqueness", label: "Uniqueness", desc: "Column values must be unique (no duplicates)" },
  { key: "cross_reference", label: "Cross Reference", desc: "Values must exist in another file's column" },
  { key: "range", label: "Range", desc: "Numeric values must fall within a min-max range" },
];

const OPERATORS = [">", ">=", "<", "<=", "==", "!="];
const SEVERITIES = [
  { key: "error", label: "Error", color: "text-red-600 bg-red-50 border-red-200" },
  { key: "warning", label: "Warning", color: "text-amber-600 bg-amber-50 border-amber-200" },
  { key: "info", label: "Info", color: "text-blue-600 bg-blue-50 border-blue-200" },
];

const StatusIcon = ({ status, size = 14 }) => {
  if (status === "pass") return <CheckCircle size={size} className="text-green-500" />;
  if (status === "warn") return <AlertTriangle size={size} className="text-amber-500" />;
  if (status === "fail") return <XCircle size={size} className="text-red-500" />;
  if (status === "skip") return <FileText size={size} className="text-slate-400" />;
  return <AlertTriangle size={size} className="text-slate-400" />;
};

const INIT_FORM = {
  name: "", description: "", file_type: "daily_sales", rule_type: "threshold",
  column: "", operator: ">", value: 0, value_str: "", min_value: 0, max_value: 100,
  ref_file_type: "sku_ean_master", ref_column: "", severity: "warning", threshold_pct: 95,
};

const DataQualityRules = () => {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [form, setForm] = useState({ ...INIT_FORM });
  const [columns, setColumns] = useState([]);
  const [refColumns, setRefColumns] = useState([]);
  const [colLoading, setColLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [actionLoading, setActionLoading] = useState(null);
  const [evalResults, setEvalResults] = useState(null);
  const [evaluating, setEvaluating] = useState(false);

  const fetchRules = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/quality/rules/`);
      setRules(resp.data.rules || []);
    } catch { setError("Failed to load rules"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchRules(); }, [fetchRules]);

  // Load columns when file_type changes
  const loadColumns = useCallback(async (fileType, isRef = false) => {
    setColLoading(true);
    try {
      const resp = await axios.get(`${API}/quality/rules/file-columns/${fileType}`);
      if (isRef) setRefColumns(resp.data.columns || []);
      else setColumns(resp.data.columns || []);
    } catch {
      if (isRef) setRefColumns([]);
      else setColumns([]);
    } finally { setColLoading(false); }
  }, []);

  useEffect(() => {
    if (showCreate || editingRule) loadColumns(form.file_type);
  }, [form.file_type, showCreate, editingRule, loadColumns]);

  useEffect(() => {
    if ((showCreate || editingRule) && form.rule_type === "cross_reference" && form.ref_file_type) {
      loadColumns(form.ref_file_type, true);
    }
  }, [form.ref_file_type, form.rule_type, showCreate, editingRule, loadColumns]);

  const clearMessages = () => { setError(""); setSuccess(""); };

  const handleCreate = async () => {
    clearMessages();
    if (!form.name.trim()) { setError("Rule name is required"); return; }
    if (!form.column.trim()) { setError("Column name is required"); return; }
    setActionLoading("create");
    try {
      const payload = { ...form };
      // Clean payload based on rule type
      if (form.rule_type !== "threshold") { delete payload.operator; delete payload.value; }
      if (form.rule_type !== "pattern") { delete payload.value_str; }
      if (form.rule_type !== "range") { delete payload.min_value; delete payload.max_value; }
      if (form.rule_type !== "cross_reference") { delete payload.ref_file_type; delete payload.ref_column; }

      if (editingRule) {
        await axios.put(`${API}/quality/rules/${editingRule.rule_id}`, payload);
        setSuccess("Rule updated");
      } else {
        await axios.post(`${API}/quality/rules/`, payload);
        setSuccess("Rule created");
      }
      setShowCreate(false);
      setEditingRule(null);
      setForm({ ...INIT_FORM });
      fetchRules();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save rule");
    } finally { setActionLoading(null); }
  };

  const handleToggle = async (ruleId) => {
    clearMessages();
    setActionLoading(ruleId);
    try {
      await axios.post(`${API}/quality/rules/${ruleId}/toggle`);
      fetchRules();
    } catch (err) { setError(err.response?.data?.detail || "Toggle failed"); }
    finally { setActionLoading(null); }
  };

  const handleDelete = async (ruleId) => {
    clearMessages();
    setActionLoading(`del-${ruleId}`);
    try {
      await axios.delete(`${API}/quality/rules/${ruleId}`);
      setSuccess("Rule deleted");
      fetchRules();
    } catch (err) { setError(err.response?.data?.detail || "Delete failed"); }
    finally { setActionLoading(null); }
  };

  const handleEdit = (rule) => {
    setForm({
      name: rule.name, description: rule.description || "", file_type: rule.file_type,
      rule_type: rule.rule_type, column: rule.column, operator: rule.operator || ">",
      value: rule.value ?? 0, value_str: rule.value_str || "",
      min_value: rule.min_value ?? 0, max_value: rule.max_value ?? 100,
      ref_file_type: rule.ref_file_type || "sku_ean_master", ref_column: rule.ref_column || "",
      severity: rule.severity, threshold_pct: rule.threshold_pct,
    });
    setEditingRule(rule);
    setShowCreate(true);
    clearMessages();
  };

  const handleEvaluate = async () => {
    clearMessages();
    setEvaluating(true);
    try {
      const resp = await axios.post(`${API}/quality/rules/evaluate`);
      setEvalResults(resp.data);
      setSuccess(`Evaluated ${resp.data.summary.total} rules`);
      fetchRules();
    } catch (err) { setError(err.response?.data?.detail || "Evaluation failed"); }
    finally { setEvaluating(false); }
  };

  const getRuleTypeLabel = (key) => RULE_TYPES.find(t => t.key === key)?.label || key;
  const getFileLabel = (key) => FILE_TYPES.find(t => t.key === key)?.label || key;
  const getSeverityCfg = (key) => SEVERITIES.find(s => s.key === key) || SEVERITIES[1];

  if (loading) return <div className="flex items-center justify-center py-16"><Loader2 size={24} className="animate-spin text-slate-400" /></div>;

  return (
    <div className="space-y-6" data-testid="dq-rules-engine">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Custom Validation Rules</h2>
          <p className="text-sm text-slate-500">Define tenant-specific data quality rules</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleEvaluate} disabled={evaluating || rules.filter(r => r.is_active).length === 0}
            data-testid="evaluate-rules-btn"
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition flex items-center gap-2 disabled:opacity-50">
            {evaluating ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
            Run Rules
          </button>
          <button onClick={() => { setShowCreate(true); setEditingRule(null); setForm({ ...INIT_FORM }); clearMessages(); }}
            data-testid="create-rule-btn"
            className="px-4 py-2 bg-[#0176D3] hover:bg-[#0161B0] text-white text-sm font-medium rounded-lg transition flex items-center gap-2">
            <Plus size={14} /> New Rule
          </button>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="rules-error">
          <XCircle size={16} className="flex-shrink-0" /> {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 border border-green-100 p-3 rounded-lg" data-testid="rules-success">
          <CheckCircle size={16} className="flex-shrink-0" /> {success}
        </div>
      )}

      {/* Create / Edit Form */}
      {showCreate && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm" data-testid="rule-form">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="font-semibold text-slate-900">{editingRule ? "Edit Rule" : "Create New Rule"}</h3>
            <button onClick={() => { setShowCreate(false); setEditingRule(null); }} className="text-slate-400 hover:text-slate-600"><X size={18} /></button>
          </div>
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Name */}
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Rule Name</label>
                <input data-testid="rule-name-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
                  placeholder="e.g., Revenue must be positive" />
              </div>

              {/* File Type */}
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">File Type</label>
                <select data-testid="rule-file-type" value={form.file_type}
                  onChange={e => setForm({ ...form, file_type: e.target.value, column: "" })}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] bg-white">
                  {FILE_TYPES.map(ft => <option key={ft.key} value={ft.key}>{ft.label}</option>)}
                </select>
              </div>

              {/* Rule Type */}
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Rule Type</label>
                <select data-testid="rule-type-select" value={form.rule_type}
                  onChange={e => setForm({ ...form, rule_type: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] bg-white">
                  {RULE_TYPES.map(rt => <option key={rt.key} value={rt.key}>{rt.label}</option>)}
                </select>
                <p className="text-[11px] text-slate-400 mt-1">{RULE_TYPES.find(t => t.key === form.rule_type)?.desc}</p>
              </div>

              {/* Column */}
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                  Column {colLoading && <Loader2 size={10} className="inline animate-spin ml-1" />}
                </label>
                {columns.length > 0 ? (
                  <select data-testid="rule-column-select" value={form.column}
                    onChange={e => setForm({ ...form, column: e.target.value })}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] bg-white">
                    <option value="">Select column...</option>
                    {columns.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                ) : (
                  <input data-testid="rule-column-input" value={form.column}
                    onChange={e => setForm({ ...form, column: e.target.value })}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
                    placeholder="Column name (e.g., revenue)" />
                )}
              </div>

              {/* Threshold: operator + value */}
              {form.rule_type === "threshold" && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Operator</label>
                    <select data-testid="rule-operator" value={form.operator}
                      onChange={e => setForm({ ...form, operator: e.target.value })}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] bg-white">
                      {OPERATORS.map(op => <option key={op} value={op}>{op}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Value</label>
                    <input data-testid="rule-value" type="number" value={form.value}
                      onChange={e => setForm({ ...form, value: parseFloat(e.target.value) || 0 })}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]" />
                  </div>
                </>
              )}

              {/* Pattern: regex string */}
              {form.rule_type === "pattern" && (
                <div className="md:col-span-2">
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Regex Pattern</label>
                  <input data-testid="rule-pattern" value={form.value_str}
                    onChange={e => setForm({ ...form, value_str: e.target.value })}
                    className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
                    placeholder="e.g., ^STR-\d{4}$" />
                </div>
              )}

              {/* Range: min + max */}
              {form.rule_type === "range" && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Min Value</label>
                    <input data-testid="rule-min" type="number" value={form.min_value}
                      onChange={e => setForm({ ...form, min_value: parseFloat(e.target.value) || 0 })}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Max Value</label>
                    <input data-testid="rule-max" type="number" value={form.max_value}
                      onChange={e => setForm({ ...form, max_value: parseFloat(e.target.value) || 0 })}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]" />
                  </div>
                </>
              )}

              {/* Cross Reference: ref_file_type + ref_column */}
              {form.rule_type === "cross_reference" && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Reference File</label>
                    <select data-testid="rule-ref-file" value={form.ref_file_type}
                      onChange={e => setForm({ ...form, ref_file_type: e.target.value, ref_column: "" })}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] bg-white">
                      {FILE_TYPES.map(ft => <option key={ft.key} value={ft.key}>{ft.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Reference Column</label>
                    {refColumns.length > 0 ? (
                      <select data-testid="rule-ref-column" value={form.ref_column}
                        onChange={e => setForm({ ...form, ref_column: e.target.value })}
                        className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] bg-white">
                        <option value="">Select column...</option>
                        {refColumns.map(c => <option key={c} value={c}>{c}</option>)}
                      </select>
                    ) : (
                      <input data-testid="rule-ref-column-input" value={form.ref_column}
                        onChange={e => setForm({ ...form, ref_column: e.target.value })}
                        className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
                        placeholder="Reference column name" />
                    )}
                  </div>
                </>
              )}

              {/* Severity */}
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Severity</label>
                <select data-testid="rule-severity" value={form.severity}
                  onChange={e => setForm({ ...form, severity: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3] bg-white">
                  {SEVERITIES.map(s => <option key={s.key} value={s.key}>{s.label}</option>)}
                </select>
              </div>

              {/* Threshold % */}
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Pass Threshold (%)</label>
                <input data-testid="rule-threshold" type="number" min="0" max="100" value={form.threshold_pct}
                  onChange={e => setForm({ ...form, threshold_pct: parseFloat(e.target.value) || 0 })}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]" />
                <p className="text-[11px] text-slate-400 mt-1">Minimum % of records that must pass this rule</p>
              </div>

              {/* Description */}
              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Description (optional)</label>
                <input data-testid="rule-description" value={form.description}
                  onChange={e => setForm({ ...form, description: e.target.value })}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
                  placeholder="Explain what this rule validates..." />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button onClick={() => { setShowCreate(false); setEditingRule(null); }}
                className="px-4 py-2 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50">Cancel</button>
              <button onClick={handleCreate} disabled={actionLoading === "create"} data-testid="save-rule-btn"
                className="px-4 py-2 bg-[#0176D3] hover:bg-[#0161B0] text-white text-sm font-medium rounded-lg transition flex items-center gap-2 disabled:opacity-60">
                {actionLoading === "create" ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
                {editingRule ? "Update Rule" : "Create Rule"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Evaluation Results */}
      {evalResults && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm" data-testid="eval-results">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-slate-900">Evaluation Results</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {evalResults.summary.total} rules evaluated at {new Date(evalResults.summary.evaluated_at).toLocaleString()}
              </p>
            </div>
            <div className="flex gap-3 text-xs">
              <span className="flex items-center gap-1 text-green-600"><CheckCircle size={12} /> {evalResults.summary.passed} passed</span>
              <span className="flex items-center gap-1 text-amber-600"><AlertTriangle size={12} /> {evalResults.summary.warned} warned</span>
              <span className="flex items-center gap-1 text-red-600"><XCircle size={12} /> {evalResults.summary.failed} failed</span>
              {evalResults.summary.errors > 0 && (
                <span className="flex items-center gap-1 text-slate-500"><FileText size={12} /> {evalResults.summary.errors} skipped</span>
              )}
            </div>
          </div>
          <div className="divide-y divide-slate-50">
            {evalResults.results.map(r => (
              <div key={r.rule_id} className="px-6 py-3 flex items-start gap-3" data-testid={`eval-result-${r.rule_id}`}>
                <StatusIcon status={r.status} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-slate-800">{r.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${getSeverityCfg(r.severity).color}`}>
                      {r.severity}
                    </span>
                    <span className="text-[10px] text-slate-400">{getFileLabel(r.file_type)} / {r.column}</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{r.detail}</p>
                  {r.total > 0 && (
                    <div className="mt-1.5 flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden" style={{ maxWidth: 200 }}>
                        <div className="h-full rounded-full transition-all"
                          style={{ width: `${r.pass_pct}%`, background: r.status === "pass" ? "#2E844A" : r.status === "warn" ? "#DD7A01" : "#EA001E" }} />
                      </div>
                      <span className="text-[11px] font-medium text-slate-600">{r.pass_pct}%</span>
                      <span className="text-[10px] text-slate-400">({r.pass_count}/{r.total})</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rules List */}
      {rules.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-10 text-center" data-testid="no-rules">
          <Shield size={40} className="mx-auto text-slate-300 mb-3" />
          <p className="text-slate-500 text-sm">No custom rules defined yet</p>
          <p className="text-slate-400 text-xs mt-1">Create rules to enforce data quality standards specific to your business</p>
        </div>
      ) : (
        <div className="space-y-2">
          {rules.map(rule => {
            const sevCfg = getSeverityCfg(rule.severity);
            return (
              <div key={rule.rule_id} data-testid={`rule-card-${rule.rule_id}`}
                className={`bg-white rounded-xl border shadow-sm transition ${rule.is_active ? "border-slate-200" : "border-slate-100 opacity-60"}`}>
                <div className="p-4 flex items-center gap-3">
                  {/* Status dot */}
                  {rule.last_status ? (
                    <StatusIcon status={rule.last_status} size={16} />
                  ) : (
                    <div className="w-4 h-4 rounded-full bg-slate-200 flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                    </div>
                  )}

                  {/* Rule info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="font-medium text-slate-900 text-sm" data-testid={`rule-name-${rule.rule_id}`}>{rule.name}</h4>
                      {!rule.is_active && <span className="text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded font-medium uppercase">Disabled</span>}
                    </div>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1">
                      <span className="text-xs text-slate-500">{getRuleTypeLabel(rule.rule_type)}</span>
                      <span className="text-xs text-slate-400">{getFileLabel(rule.file_type)} / {rule.column}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${sevCfg.color}`}>{rule.severity}</span>
                      <span className="text-[10px] text-slate-400">Threshold: {rule.threshold_pct}%</span>
                      {rule.last_evaluated && (
                        <span className="text-[10px] text-slate-400">Last: {new Date(rule.last_evaluated).toLocaleString()}</span>
                      )}
                    </div>
                    {rule.description && <p className="text-xs text-slate-400 mt-0.5">{rule.description}</p>}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1">
                    <button onClick={() => handleEdit(rule)} data-testid={`edit-rule-${rule.rule_id}`}
                      className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition" title="Edit">
                      <Settings2 size={15} />
                    </button>
                    <button onClick={() => handleToggle(rule.rule_id)} disabled={!!actionLoading}
                      data-testid={`toggle-rule-${rule.rule_id}`}
                      className={`p-2 rounded-lg transition ${rule.is_active ? "text-green-500 hover:bg-green-50" : "text-slate-400 hover:bg-slate-50"}`}
                      title={rule.is_active ? "Disable" : "Enable"}>
                      {actionLoading === rule.rule_id ? <Loader2 size={15} className="animate-spin" /> :
                        rule.is_active ? <ToggleRight size={15} /> : <ToggleLeft size={15} />}
                    </button>
                    <button onClick={() => handleDelete(rule.rule_id)} disabled={!!actionLoading}
                      data-testid={`delete-rule-${rule.rule_id}`}
                      className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition" title="Delete">
                      {actionLoading === `del-${rule.rule_id}` ? <Loader2 size={15} className="animate-spin" /> : <Trash2 size={15} />}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default DataQualityRules;
