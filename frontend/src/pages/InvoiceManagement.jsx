import { useState, useEffect, useCallback } from "react";
import {
  FileText, Download, Plus, Loader2, AlertCircle, CheckCircle2,
  X, Clock, DollarSign, CreditCard, Eye, Trash2, Printer
} from "lucide-react";
import axios from "axios";
import { API } from "../App";

const STATUS_STYLES = {
  paid: "bg-emerald-50 text-emerald-700 border-emerald-200",
  unpaid: "bg-amber-50 text-amber-700 border-amber-200",
  overdue: "bg-red-50 text-red-700 border-red-200",
  cancelled: "bg-slate-100 text-slate-500 border-slate-200",
};

const InvoiceManagement = () => {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [description, setDescription] = useState("");
  const [customAmount, setCustomAmount] = useState("");
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(null);

  const fetchInvoices = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/invoices`);
      setInvoices(resp.data.invoices || []);
    } catch {
      setError("Failed to load invoices");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchInvoices(); }, [fetchInvoices]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError("");
    setSuccess("");
    try {
      const body = {};
      if (description) body.description = description;
      if (customAmount) body.custom_amount = parseFloat(customAmount);
      const resp = await axios.post(`${API}/invoices/generate`, body);
      setSuccess(`Invoice ${resp.data.invoice_number} generated`);
      setShowCreate(false);
      setDescription("");
      setCustomAmount("");
      fetchInvoices();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate invoice");
    } finally {
      setGenerating(false);
    }
  };

  const handleViewDetail = async (inv) => {
    setDetailLoading(inv.invoice_id);
    try {
      const resp = await axios.get(`${API}/invoices/${inv.invoice_id}`);
      setSelectedInvoice(resp.data);
    } catch {
      setError("Failed to load invoice details");
    } finally {
      setDetailLoading(null);
    }
  };

  const handleDownload = async (inv) => {
    try {
      const resp = await axios.get(`${API}/invoices/${inv.invoice_id}/download`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([resp.data], { type: "text/html" }));
      const w = window.open(url, "_blank");
      if (w) w.focus();
    } catch {
      setError("Failed to download invoice");
    }
  };

  const handleUpdateStatus = async (invoiceId, newStatus) => {
    setUpdatingStatus(invoiceId);
    try {
      await axios.put(`${API}/invoices/${invoiceId}/status`, { status: newStatus });
      fetchInvoices();
      if (selectedInvoice?.invoice_id === invoiceId) {
        setSelectedInvoice(prev => ({ ...prev, status: newStatus }));
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update status");
    } finally {
      setUpdatingStatus(null);
    }
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    setDeleting(true);
    try {
      await axios.delete(`${API}/invoices/${confirmDelete.invoice_id}`);
      setSuccess("Invoice deleted");
      setConfirmDelete(null);
      if (selectedInvoice?.invoice_id === confirmDelete.invoice_id) setSelectedInvoice(null);
      fetchInvoices();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete invoice");
    } finally {
      setDeleting(false);
    }
  };

  const formatCurrency = (amount, currency) => {
    if (currency === "INR") return `\u20b9${amount?.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
    if (currency === "USD") return `$${amount?.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
    return `${currency} ${amount?.toFixed(2)}`;
  };

  const formatDate = (iso) => {
    if (!iso) return "\u2014";
    return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  if (loading) return (
    <div className="flex items-center justify-center py-20" data-testid="invoice-loading">
      <Loader2 className="animate-spin text-slate-400" size={32} />
    </div>
  );

  return (
    <div data-testid="invoice-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-teal-100">
            <FileText size={22} className="text-teal-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900" data-testid="invoice-title">Invoices</h1>
            <p className="text-sm text-slate-500">Manage billing and download invoices</p>
          </div>
        </div>
        <button
          data-testid="generate-invoice-btn"
          onClick={() => { setShowCreate(true); setError(""); setSuccess(""); }}
          disabled={generating}
          className="px-4 py-2.5 text-sm font-medium text-white bg-teal-600 rounded-lg hover:bg-teal-700 transition flex items-center gap-2 disabled:opacity-60"
        >
          {generating ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
          Generate Invoice
        </button>
      </div>

      {/* Alerts */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="invoice-error">
          <AlertCircle size={16} className="flex-shrink-0" /> {error}
          <button onClick={() => setError("")} className="ml-auto"><X size={14} /></button>
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 border border-emerald-100 p-3 rounded-lg" data-testid="invoice-success">
          <CheckCircle2 size={16} className="flex-shrink-0" /> {success}
          <button onClick={() => setSuccess("")} className="ml-auto"><X size={14} /></button>
        </div>
      )}

      {/* Create Invoice Form */}
      {showCreate && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm" data-testid="create-invoice-form">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Generate New Invoice</h3>
          <div className="space-y-3 mb-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Description (optional)</label>
              <input data-testid="invoice-desc-input" type="text" value={description} onChange={e => setDescription(e.target.value)}
                placeholder="e.g. Monthly subscription - April 2026" maxLength={200}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Custom Amount (optional, uses plan price if blank)</label>
              <input data-testid="invoice-amount-input" type="number" value={customAmount} onChange={e => setCustomAmount(e.target.value)}
                placeholder="Leave blank for plan default" min="0" step="100"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500" />
            </div>
          </div>
          <div className="flex gap-3">
            <button data-testid="cancel-generate-btn" onClick={() => { setShowCreate(false); setDescription(""); setCustomAmount(""); }}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50">Cancel</button>
            <button data-testid="confirm-generate-btn" onClick={handleGenerate} disabled={generating}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-teal-600 rounded-lg hover:bg-teal-700 disabled:opacity-60 flex items-center justify-center gap-2">
              {generating ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
              {generating ? "Generating..." : "Generate Invoice"}
            </button>
          </div>
        </div>
      )}

      {/* Invoice List + Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* List */}
        <div className="lg:col-span-2 space-y-3">
          {invoices.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-10 text-center" data-testid="invoice-empty">
              <FileText size={40} className="text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500 text-sm">No invoices yet. Generate your first invoice.</p>
            </div>
          ) : invoices.map(inv => (
            <div key={inv.invoice_id}
              className={`bg-white rounded-xl border p-4 cursor-pointer transition hover:border-teal-300 ${selectedInvoice?.invoice_id === inv.invoice_id ? "border-teal-400 ring-1 ring-teal-200" : "border-slate-200"}`}
              onClick={() => handleViewDetail(inv)}
              data-testid={`invoice-item-${inv.invoice_id}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-slate-900" data-testid="invoice-item-number">{inv.invoice_number}</span>
                    <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${STATUS_STYLES[inv.status]}`}>{inv.status}</span>
                  </div>
                  <p className="text-xs text-slate-500 truncate">{inv.description}</p>
                  <div className="flex items-center gap-4 mt-1 text-xs text-slate-400">
                    <span><Clock size={11} className="inline mr-1" />{formatDate(inv.created_at)}</span>
                    <span>Due: {formatDate(inv.due_date)}</span>
                    <span className="capitalize">{inv.plan_label}</span>
                  </div>
                </div>
                <div className="text-right ml-4">
                  <p className="text-lg font-bold text-slate-900">{formatCurrency(inv.total, inv.currency)}</p>
                  <div className="flex items-center gap-1 mt-1">
                    <button onClick={(e) => { e.stopPropagation(); handleDownload(inv); }}
                      className="p-1.5 text-slate-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg" title="Download" data-testid={`download-inv-${inv.invoice_id}`}>
                      <Printer size={14} />
                    </button>
                    {inv.status === "unpaid" && (
                      <button onClick={(e) => { e.stopPropagation(); handleUpdateStatus(inv.invoice_id, "paid"); }}
                        disabled={updatingStatus === inv.invoice_id}
                        className="p-1.5 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg" title="Mark as Paid" data-testid={`pay-inv-${inv.invoice_id}`}>
                        {updatingStatus === inv.invoice_id ? <Loader2 size={14} className="animate-spin" /> : <CreditCard size={14} />}
                      </button>
                    )}
                    <button onClick={(e) => { e.stopPropagation(); setConfirmDelete(inv); }}
                      className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg" title="Delete" data-testid={`delete-inv-${inv.invoice_id}`}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Detail Panel */}
        <div className="lg:col-span-1">
          {selectedInvoice ? (
            <div className="bg-white rounded-xl border border-slate-200 p-5 sticky top-4" data-testid="invoice-detail-panel">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-900">Invoice Detail</h3>
                <button onClick={() => setSelectedInvoice(null)} className="text-slate-400 hover:text-slate-600"><X size={16} /></button>
              </div>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between"><span className="text-slate-500">Number</span><span className="font-medium">{selectedInvoice.invoice_number}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Status</span><span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${STATUS_STYLES[selectedInvoice.status]}`}>{selectedInvoice.status}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Company</span><span>{selectedInvoice.company_name}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Plan</span><span>{selectedInvoice.plan_label}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Period</span><span>{selectedInvoice.billing_period?.start} to {selectedInvoice.billing_period?.end}</span></div>
                <hr className="border-slate-100" />
                <div className="flex justify-between"><span className="text-slate-500">Subtotal</span><span>{formatCurrency(selectedInvoice.subtotal, selectedInvoice.currency)}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Tax ({Math.round((selectedInvoice.tax_rate || 0.18) * 100)}%)</span><span>{formatCurrency(selectedInvoice.tax_amount, selectedInvoice.currency)}</span></div>
                <div className="flex justify-between font-bold text-base"><span>Total</span><span className="text-teal-600">{formatCurrency(selectedInvoice.total, selectedInvoice.currency)}</span></div>
                <hr className="border-slate-100" />
                <p className="text-xs font-semibold text-slate-500 uppercase">Usage Metrics</p>
                {selectedInvoice.usage_metrics && (
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(selectedInvoice.usage_metrics).map(([k, v]) => (
                      <div key={k} className="bg-slate-50 p-2 rounded-lg text-center">
                        <p className="text-sm font-bold text-slate-900">{typeof v === "number" ? v.toLocaleString() : v}</p>
                        <p className="text-[10px] text-slate-500">{k.replace(/_/g, " ")}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="mt-4 flex gap-2">
                <button onClick={() => handleDownload(selectedInvoice)}
                  className="flex-1 px-3 py-2 text-xs font-medium text-teal-700 border border-teal-200 rounded-lg hover:bg-teal-50 flex items-center justify-center gap-1" data-testid="detail-download-btn">
                  <Printer size={12} /> Print / Download
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
              <Eye size={28} className="text-slate-300 mx-auto mb-2" />
              <p className="text-sm text-slate-400">Click an invoice to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Delete Modal */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" data-testid="delete-invoice-modal">
          <div className="bg-white rounded-xl p-6 w-full max-w-sm mx-4 shadow-2xl">
            <h3 className="text-base font-semibold text-slate-900 mb-2">Delete Invoice</h3>
            <p className="text-sm text-slate-500 mb-4">Delete <strong>{confirmDelete.invoice_number}</strong>? This cannot be undone.</p>
            <div className="flex gap-3">
              <button data-testid="cancel-delete-inv" onClick={() => setConfirmDelete(null)}
                className="flex-1 px-4 py-2.5 text-sm font-medium text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50">Cancel</button>
              <button data-testid="confirm-delete-inv" onClick={handleDelete} disabled={deleting}
                className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-60 flex items-center justify-center gap-2">
                {deleting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />} Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InvoiceManagement;
