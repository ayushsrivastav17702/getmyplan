import { useState, useEffect, useCallback } from "react";
import {
  Database, Download, Upload, Trash2, Plus, Loader2,
  AlertCircle, CheckCircle2, Clock, HardDrive, FileArchive,
  RefreshCw, X, Shield, ChevronDown
} from "lucide-react";
import axios from "axios";
import { API } from "../App";

const BackupRestore = () => {
  const [backups, setBackups] = useState([]);
  const [maxBackups, setMaxBackups] = useState(5);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [restoring, setRestoring] = useState(null);
  const [downloading, setDownloading] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [backupName, setBackupName] = useState("");
  const [backupDesc, setBackupDesc] = useState("");
  const [confirmRestore, setConfirmRestore] = useState(null);
  const [restoreMode, setRestoreMode] = useState("merge");
  const [confirmDelete, setConfirmDelete] = useState(null);

  const fetchBackups = useCallback(async () => {
    try {
      const resp = await axios.get(`${API}/backup/list`);
      setBackups(resp.data.backups || []);
      setMaxBackups(resp.data.max_backups || 5);
    } catch {
      setError("Failed to load backups");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchBackups(); }, [fetchBackups]);

  const handleCreate = async () => {
    setCreating(true);
    setError("");
    setSuccess("");
    try {
      const resp = await axios.post(`${API}/backup/create`, {
        name: backupName || undefined,
        description: backupDesc || undefined,
      });
      setSuccess(`Backup "${resp.data.name}" created — ${resp.data.total_docs.toLocaleString()} documents, ${resp.data.size_mb} MB`);
      setShowCreate(false);
      setBackupName("");
      setBackupDesc("");
      fetchBackups();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create backup");
    } finally {
      setCreating(false);
    }
  };

  const handleDownload = async (backup) => {
    setDownloading(backup.backup_id);
    try {
      const resp = await axios.get(`${API}/backup/${backup.backup_id}/download`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `${backup.name.replace(/\s+/g, "_")}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setError("Failed to download backup");
    } finally {
      setDownloading(null);
    }
  };

  const handleRestore = async () => {
    if (!confirmRestore) return;
    setRestoring(confirmRestore.backup_id);
    setError("");
    setSuccess("");
    try {
      const resp = await axios.post(`${API}/backup/${confirmRestore.backup_id}/restore`, {
        mode: restoreMode,
      });
      const d = resp.data;
      setSuccess(`Restored ${d.total_docs_restored.toLocaleString()} documents across ${d.restored_collections} collections (${restoreMode} mode)`);
      setConfirmRestore(null);
    } catch (err) {
      setError(err.response?.data?.detail || "Restore failed");
    } finally {
      setRestoring(null);
    }
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    setDeleting(confirmDelete.backup_id);
    setError("");
    try {
      await axios.delete(`${API}/backup/${confirmDelete.backup_id}`);
      setSuccess("Backup deleted");
      setConfirmDelete(null);
      fetchBackups();
    } catch {
      setError("Failed to delete backup");
    } finally {
      setDeleting(null);
    }
  };

  const formatDate = (iso) => {
    if (!iso) return "—";
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
  };

  if (loading) return (
    <div className="flex items-center justify-center py-20" data-testid="backup-loading">
      <Loader2 className="animate-spin text-slate-400" size={32} />
    </div>
  );

  return (
    <div data-testid="backup-restore-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-100">
            <Database size={22} className="text-indigo-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900" data-testid="backup-title">Backup & Restore</h1>
            <p className="text-sm text-slate-500">Create snapshots of your workspace data. Retains last {maxBackups} backups.</p>
          </div>
        </div>
        <button
          data-testid="create-backup-btn"
          onClick={() => { setShowCreate(true); setError(""); setSuccess(""); }}
          disabled={creating}
          className="px-4 py-2.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition flex items-center gap-2 disabled:opacity-60"
        >
          {creating ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
          Create Backup
        </button>
      </div>

      {/* Alerts */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="backup-error">
          <AlertCircle size={16} className="flex-shrink-0" /> {error}
          <button onClick={() => setError("")} className="ml-auto"><X size={14} /></button>
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 border border-emerald-100 p-3 rounded-lg" data-testid="backup-success">
          <CheckCircle2 size={16} className="flex-shrink-0" /> {success}
          <button onClick={() => setSuccess("")} className="ml-auto"><X size={14} /></button>
        </div>
      )}

      {/* Create Backup Modal */}
      {showCreate && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm" data-testid="create-backup-form">
          <h3 className="text-base font-semibold text-slate-900 mb-4">New Backup</h3>
          <div className="space-y-3 mb-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Name (optional)</label>
              <input
                data-testid="backup-name-input"
                type="text"
                value={backupName}
                onChange={e => setBackupName(e.target.value)}
                placeholder="e.g. Pre-migration snapshot"
                maxLength={100}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Description (optional)</label>
              <input
                data-testid="backup-desc-input"
                type="text"
                value={backupDesc}
                onChange={e => setBackupDesc(e.target.value)}
                placeholder="Why are you creating this backup?"
                maxLength={500}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 mb-4">
            <strong>Includes:</strong> All workspace data — sales, inventory, configs, user accounts, analytics, forecasts, and more.
          </div>
          <div className="flex gap-3">
            <button
              data-testid="cancel-create-btn"
              onClick={() => { setShowCreate(false); setBackupName(""); setBackupDesc(""); }}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              data-testid="confirm-create-btn"
              onClick={handleCreate}
              disabled={creating}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {creating ? <Loader2 size={14} className="animate-spin" /> : <HardDrive size={14} />}
              {creating ? "Creating..." : "Create Backup"}
            </button>
          </div>
        </div>
      )}

      {/* Backup List */}
      {backups.length === 0 && !showCreate ? (
        <div className="bg-white rounded-xl border border-slate-200 p-10 text-center" data-testid="backup-empty">
          <FileArchive size={40} className="text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 text-sm">No backups yet. Create your first backup to get started.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {backups.map((b) => (
            <div key={b.backup_id} className="bg-white rounded-xl border border-slate-200 p-4 hover:border-slate-300 transition" data-testid={`backup-item-${b.backup_id}`}>
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-semibold text-slate-900 truncate" data-testid="backup-item-name">{b.name}</h3>
                    <span className="px-2 py-0.5 text-xs font-medium bg-indigo-50 text-indigo-600 rounded-full">{b.size_mb} MB</span>
                  </div>
                  {b.description && <p className="text-xs text-slate-500 mb-1 truncate">{b.description}</p>}
                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <span className="flex items-center gap-1"><Clock size={12} /> {formatDate(b.created_at)}</span>
                    <span>{b.total_docs.toLocaleString()} docs</span>
                    <span>{b.collections_count} collections</span>
                    <span>by {b.created_by}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <button
                    data-testid={`download-btn-${b.backup_id}`}
                    onClick={() => handleDownload(b)}
                    disabled={downloading === b.backup_id}
                    className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition disabled:opacity-50"
                    title="Download ZIP"
                  >
                    {downloading === b.backup_id ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
                  </button>
                  <button
                    data-testid={`restore-btn-${b.backup_id}`}
                    onClick={() => { setConfirmRestore(b); setRestoreMode("merge"); setError(""); setSuccess(""); }}
                    disabled={restoring === b.backup_id}
                    className="p-2 text-slate-500 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition disabled:opacity-50"
                    title="Restore"
                  >
                    {restoring === b.backup_id ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
                  </button>
                  <button
                    data-testid={`delete-btn-${b.backup_id}`}
                    onClick={() => { setConfirmDelete(b); setError(""); }}
                    disabled={deleting === b.backup_id}
                    className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition disabled:opacity-50"
                    title="Delete"
                  >
                    {deleting === b.backup_id ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Restore Confirmation Modal */}
      {confirmRestore && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" data-testid="restore-modal">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4 shadow-2xl">
            <h3 className="text-base font-semibold text-slate-900 mb-2 flex items-center gap-2">
              <RefreshCw size={18} className="text-amber-600" /> Restore Backup
            </h3>
            <p className="text-sm text-slate-500 mb-4">
              Restoring from: <strong>{confirmRestore.name}</strong>
            </p>
            <div className="space-y-2 mb-4">
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">Restore Mode</label>
              <div className="space-y-2">
                <label className="flex items-start gap-3 p-3 border rounded-lg cursor-pointer hover:bg-slate-50 transition" data-testid="restore-mode-merge">
                  <input type="radio" name="mode" value="merge" checked={restoreMode === "merge"} onChange={() => setRestoreMode("merge")} className="mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-slate-900">Merge</p>
                    <p className="text-xs text-slate-500">Add backup data alongside existing data. Won't overwrite existing records.</p>
                  </div>
                </label>
                <label className="flex items-start gap-3 p-3 border rounded-lg cursor-pointer hover:bg-slate-50 transition" data-testid="restore-mode-overwrite">
                  <input type="radio" name="mode" value="overwrite" checked={restoreMode === "overwrite"} onChange={() => setRestoreMode("overwrite")} className="mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-700">Overwrite</p>
                    <p className="text-xs text-slate-500">Replace all current data with backup data. <strong className="text-red-600">This cannot be undone.</strong></p>
                  </div>
                </label>
              </div>
            </div>
            {restoreMode === "overwrite" && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 mb-4" data-testid="restore-overwrite-warning">
                <strong>Warning:</strong> Overwrite will permanently delete current data and replace it with the backup snapshot.
              </div>
            )}
            <div className="flex gap-3">
              <button
                data-testid="cancel-restore-btn"
                onClick={() => setConfirmRestore(null)}
                className="flex-1 px-4 py-2.5 text-sm font-medium text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                data-testid="confirm-restore-btn"
                onClick={handleRestore}
                disabled={restoring}
                className={`flex-1 px-4 py-2.5 text-sm font-medium text-white rounded-lg flex items-center justify-center gap-2 disabled:opacity-60 ${
                  restoreMode === "overwrite" ? "bg-red-600 hover:bg-red-700" : "bg-amber-600 hover:bg-amber-700"
                }`}
              >
                {restoring ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                {restoring ? "Restoring..." : `Restore (${restoreMode})`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" data-testid="delete-modal">
          <div className="bg-white rounded-xl p-6 w-full max-w-sm mx-4 shadow-2xl">
            <h3 className="text-base font-semibold text-slate-900 mb-2">Delete Backup</h3>
            <p className="text-sm text-slate-500 mb-4">
              Are you sure you want to delete <strong>{confirmDelete.name}</strong>? This cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                data-testid="cancel-delete-btn"
                onClick={() => setConfirmDelete(null)}
                className="flex-1 px-4 py-2.5 text-sm font-medium text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                data-testid="confirm-delete-btn"
                onClick={handleDelete}
                disabled={deleting}
                className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-60 flex items-center justify-center gap-2"
              >
                {deleting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BackupRestore;
