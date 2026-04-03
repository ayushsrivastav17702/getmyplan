import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";
import { useAuth } from "../context/AuthContext";
import {
  Users, UserPlus, Shield, Mail, Trash2, ChevronDown,
  CheckCircle, Clock, AlertCircle, Loader2, Copy, RefreshCw, FileText,
  Edit2, RotateCcw, Key, Upload, X
} from "lucide-react";

const ROLE_COLORS = {
  admin: "bg-red-100 text-red-700",
  super_admin: "bg-purple-100 text-purple-700",
  cxo: "bg-blue-100 text-blue-700",
  merchandiser: "bg-emerald-100 text-emerald-700",
  allocator: "bg-amber-100 text-amber-700",
  demand_planner: "bg-cyan-100 text-cyan-700",
  store_manager: "bg-orange-100 text-orange-700",
  viewer: "bg-slate-100 text-slate-600",
};

const UserManagement = () => {
  const { user, hasRole } = useAuth();
  const isAdmin = hasRole(["admin", "super_admin"]);

  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [activeTab, setActiveTab] = useState("users");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Invite form
  const [showInvite, setShowInvite] = useState(false);
  const [invEmail, setInvEmail] = useState("");
  const [invRole, setInvRole] = useState("viewer");
  const [invName, setInvName] = useState("");
  const [invLoading, setInvLoading] = useState(false);
  const [inviteToken, setInviteToken] = useState("");

  // Role change
  const [editingRole, setEditingRole] = useState(null);

  // Edit profile modal
  const [editUser, setEditUser] = useState(null);
  const [editName, setEditName] = useState("");

  // Password reset modal
  const [resetUser, setResetUser] = useState(null);
  const [newPassword, setNewPassword] = useState("");

  // Bulk import modal
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [bulkText, setBulkText] = useState("");

  // Bulk role update
  const [bulkRoleMode, setBulkRoleMode] = useState(false);
  const [selectedUsers, setSelectedUsers] = useState(new Set());
  const [bulkNewRole, setBulkNewRole] = useState("viewer");

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [usersR, rolesR, invR, logR] = await Promise.all([
        axios.get(`${API}/users/list`),
        axios.get(`${API}/users/roles`),
        axios.get(`${API}/users/invitations`),
        axios.get(`${API}/users/audit-log?limit=30`),
      ]);
      setUsers(usersR.data.users || []);
      setRoles(rolesR.data.roles || []);
      setInvitations(invR.data.invitations || []);
      setAuditLogs(logR.data.logs || []);
    } catch {
      setError("Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);
  useEffect(() => { if (success) { const t = setTimeout(() => setSuccess(""), 4000); return () => clearTimeout(t); } }, [success]);
  useEffect(() => { if (error) { const t = setTimeout(() => setError(""), 4000); return () => clearTimeout(t); } }, [error]);

  const handleInvite = async (e) => {
    e.preventDefault();
    setInvLoading(true); setError(""); setInviteToken("");
    try {
      const resp = await axios.post(`${API}/users/invite`, { email: invEmail, role: invRole, full_name: invName || null });
      setInviteToken(resp.data.invite_token);
      setSuccess(`Invitation sent to ${invEmail}`);
      setInvEmail(""); setInvName(""); fetchAll();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to send invite");
    } finally { setInvLoading(false); }
  };

  const handleRoleChange = async (email, newRole) => {
    try {
      await axios.put(`${API}/users/${encodeURIComponent(email)}/role`, { role: newRole });
      setSuccess(`${email} role updated to ${newRole}`);
      setEditingRole(null); fetchAll();
    } catch (err) { setError(err.response?.data?.detail || "Failed to update role"); }
  };

  const handleRemove = async (email) => {
    if (!window.confirm(`Remove ${email} from this tenant?`)) return;
    try {
      await axios.delete(`${API}/users/${encodeURIComponent(email)}`);
      setSuccess(`${email} removed`); fetchAll();
    } catch (err) { setError(err.response?.data?.detail || "Failed to remove user"); }
  };

  // USER-07: Reactivate
  const handleReactivate = async (email) => {
    try {
      await axios.post(`${API}/users/${encodeURIComponent(email)}/reactivate`);
      setSuccess(`${email} reactivated`); fetchAll();
    } catch (err) { setError(err.response?.data?.detail || "Failed to reactivate"); }
  };

  // USER-04: Update profile
  const handleUpdateProfile = async () => {
    if (!editUser) return;
    try {
      await axios.put(`${API}/users/${encodeURIComponent(editUser.email)}/profile`, { full_name: editName });
      setSuccess(`Profile updated for ${editUser.email}`);
      setEditUser(null); fetchAll();
    } catch (err) { setError(err.response?.data?.detail || "Failed to update profile"); }
  };

  // USER-16: Password reset
  const handlePasswordReset = async () => {
    if (!resetUser || !newPassword) return;
    try {
      await axios.post(`${API}/users/password-reset`, { email: resetUser.email, new_password: newPassword });
      setSuccess(`Password reset for ${resetUser.email}`);
      setResetUser(null); setNewPassword("");
    } catch (err) { setError(err.response?.data?.detail || "Failed to reset password"); }
  };

  // USER-08: Bulk import
  const handleBulkImport = async () => {
    try {
      const lines = bulkText.trim().split("\n").filter(Boolean);
      const items = lines.map(line => {
        const [email, role = "viewer", full_name = ""] = line.split(",").map(s => s.trim());
        return { email, role, full_name: full_name || null };
      });
      const resp = await axios.post(`${API}/users/bulk-import`, items);
      setSuccess(resp.data.message);
      setShowBulkImport(false); setBulkText(""); fetchAll();
    } catch (err) { setError(err.response?.data?.detail || "Bulk import failed"); }
  };

  // USER-09: Bulk role update
  const handleBulkRoleUpdate = async () => {
    if (selectedUsers.size === 0) return;
    try {
      const resp = await axios.put(`${API}/users/bulk-role-update`, { emails: [...selectedUsers], role: bulkNewRole });
      setSuccess(resp.data.message);
      setBulkRoleMode(false); setSelectedUsers(new Set()); fetchAll();
    } catch (err) { setError(err.response?.data?.detail || "Bulk update failed"); }
  };

  // USER-29: Resend invitation
  const handleResendInvite = async (email) => {
    try {
      const resp = await axios.post(`${API}/users/invitations/${encodeURIComponent(email)}/resend`);
      setSuccess(resp.data.message); fetchAll();
    } catch (err) { setError(err.response?.data?.detail || "Failed to resend"); }
  };

  // USER-30: Cancel invitation
  const handleCancelInvite = async (email) => {
    if (!window.confirm(`Cancel invitation for ${email}?`)) return;
    try {
      await axios.delete(`${API}/users/invitations/${encodeURIComponent(email)}`);
      setSuccess(`Invitation cancelled for ${email}`); fetchAll();
    } catch (err) { setError(err.response?.data?.detail || "Failed to cancel"); }
  };

  // USER-24: Delete custom role
  const handleDeleteRole = async (roleName) => {
    if (!window.confirm(`Delete custom role '${roleName}'?`)) return;
    try {
      await axios.delete(`${API}/users/roles/${encodeURIComponent(roleName)}`);
      setSuccess(`Role '${roleName}' deleted`); fetchAll();
    } catch (err) { setError(err.response?.data?.detail || "Failed to delete role"); }
  };

  if (!isAdmin) {
    return (
      <div className="text-center py-20">
        <Shield size={48} className="text-slate-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-slate-700">Access Denied</h2>
        <p className="text-sm text-slate-500 mt-2">You need Admin privileges to manage users.</p>
      </div>
    );
  }

  const tabs = [
    { key: "users", label: "Team Members", icon: Users, count: users.length },
    { key: "invitations", label: "Invitations", icon: Mail, count: invitations.length },
    { key: "roles", label: "Roles", icon: Shield, count: roles.length },
    { key: "audit", label: "Audit Log", icon: FileText, count: auditLogs.length },
  ];

  const SYSTEM_ROLES = new Set(["admin", "super_admin", "cxo", "merchandiser", "allocator", "demand_planner", "store_manager", "viewer"]);

  return (
    <div className="space-y-6" data-testid="user-management-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">User Management</h1>
          <p className="text-sm text-slate-500 mt-1">Manage team members, roles, and invitations</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchAll} data-testid="refresh-users" className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-500">
            <RefreshCw size={18} />
          </button>
          <button onClick={() => setShowBulkImport(true)} data-testid="bulk-import-btn"
            className="flex items-center gap-2 border border-slate-200 hover:bg-slate-50 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
            <Upload size={16} /> Bulk Import
          </button>
          <button onClick={() => setShowInvite(true)} data-testid="invite-user-btn"
            className="flex items-center gap-2 bg-[#0176D3] hover:bg-[#0161B0] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
            <UserPlus size={16} /> Invite User
          </button>
        </div>
      </div>

      {/* Alerts */}
      {success && (
        <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 p-3 rounded-lg" data-testid="success-alert">
          <CheckCircle size={16} /> {success}
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-100 p-3 rounded-lg" data-testid="error-alert">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* Invite Modal */}
      {showInvite && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" onClick={() => setShowInvite(false)}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6" data-testid="invite-modal" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Invite Team Member</h3>
            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Email</label>
                <input data-testid="invite-email" type="email" value={invEmail} onChange={e => setInvEmail(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]" placeholder="user@company.com" required />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Full Name (optional)</label>
                <input data-testid="invite-name" type="text" value={invName} onChange={e => setInvName(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]" placeholder="John Doe" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Role</label>
                <select data-testid="invite-role" value={invRole} onChange={e => setInvRole(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]">
                  {roles.map(r => <option key={r.role_name} value={r.role_name}>{r.display_name} - {r.description}</option>)}
                </select>
              </div>
              <div className="flex gap-2 pt-2">
                <button type="button" onClick={() => setShowInvite(false)} className="flex-1 border border-slate-200 rounded-lg py-2 text-sm text-slate-600 hover:bg-slate-50">Cancel</button>
                <button type="submit" data-testid="send-invite-btn" disabled={invLoading}
                  className="flex-1 bg-[#0176D3] hover:bg-[#0161B0] text-white rounded-lg py-2 text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-60">
                  {invLoading ? <Loader2 size={16} className="animate-spin" /> : <Mail size={16} />}
                  {invLoading ? "Sending..." : "Send Invite"}
                </button>
              </div>
            </form>
            {inviteToken && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs font-medium text-blue-700 mb-1">Invite Token (share with user)</p>
                <div className="flex items-center gap-2">
                  <code className="text-xs bg-white px-2 py-1 rounded flex-1 truncate">{inviteToken}</code>
                  <button onClick={() => { navigator.clipboard.writeText(inviteToken); setSuccess("Token copied!"); }} className="p-1 hover:bg-blue-100 rounded">
                    <Copy size={14} className="text-blue-600" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Edit Profile Modal */}
      {editUser && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" onClick={() => setEditUser(null)}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6" data-testid="edit-profile-modal" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Edit Profile — {editUser.email}</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Full Name</label>
                <input data-testid="edit-name-input" type="text" value={editName} onChange={e => setEditName(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]" />
              </div>
              <div className="flex gap-2 pt-2">
                <button onClick={() => setEditUser(null)} className="flex-1 border border-slate-200 rounded-lg py-2 text-sm text-slate-600">Cancel</button>
                <button data-testid="save-profile-btn" onClick={handleUpdateProfile}
                  className="flex-1 bg-[#0176D3] text-white rounded-lg py-2 text-sm font-medium">Save</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Password Reset Modal */}
      {resetUser && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" onClick={() => setResetUser(null)}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6" data-testid="password-reset-modal" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Reset Password — {resetUser.email}</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">New Password</label>
                <input data-testid="new-password-input" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0176D3]" placeholder="Min 8 characters" />
              </div>
              <div className="flex gap-2 pt-2">
                <button onClick={() => setResetUser(null)} className="flex-1 border border-slate-200 rounded-lg py-2 text-sm text-slate-600">Cancel</button>
                <button data-testid="confirm-reset-btn" onClick={handlePasswordReset} disabled={newPassword.length < 8}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-50">Reset Password</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Import Modal */}
      {showBulkImport && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" onClick={() => setShowBulkImport(false)}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6" data-testid="bulk-import-modal" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Bulk Import Users</h3>
            <p className="text-xs text-slate-500 mb-4">One user per line: email, role, name (comma-separated)</p>
            <textarea data-testid="bulk-import-text" value={bulkText} onChange={e => setBulkText(e.target.value)} rows={6}
              className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[#0176D3]"
              placeholder={"user1@company.com, viewer, John Doe\nuser2@company.com, merchandiser, Jane Smith"} />
            <div className="flex gap-2 pt-4">
              <button onClick={() => setShowBulkImport(false)} className="flex-1 border border-slate-200 rounded-lg py-2 text-sm text-slate-600">Cancel</button>
              <button data-testid="confirm-bulk-import" onClick={handleBulkImport} disabled={!bulkText.trim()}
                className="flex-1 bg-[#0176D3] text-white rounded-lg py-2 text-sm font-medium disabled:opacity-50">Import Users</button>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button key={tab.key} data-testid={`tab-${tab.key}`} onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
                activeTab === tab.key ? "border-[#0176D3] text-[#0176D3]" : "border-transparent text-slate-500 hover:text-slate-700"}`}>
              <Icon size={16} /> {tab.label}
              {tab.count > 0 && <span className="bg-slate-100 text-slate-600 text-xs px-1.5 py-0.5 rounded-full">{tab.count}</span>}
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16"><Loader2 size={32} className="animate-spin text-[#0176D3]" /></div>
      ) : (
        <>
          {/* USERS TAB */}
          {activeTab === "users" && (
            <div>
              {/* Bulk role update bar */}
              <div className="flex items-center justify-between mb-3">
                <button data-testid="toggle-bulk-role" onClick={() => { setBulkRoleMode(!bulkRoleMode); setSelectedUsers(new Set()); }}
                  className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${bulkRoleMode ? "bg-blue-50 border-blue-200 text-blue-700" : "border-slate-200 text-slate-500 hover:bg-slate-50"}`}>
                  {bulkRoleMode ? "Cancel Bulk Select" : "Bulk Role Update"}
                </button>
                {bulkRoleMode && selectedUsers.size > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">{selectedUsers.size} selected</span>
                    <select data-testid="bulk-role-select" value={bulkNewRole} onChange={e => setBulkNewRole(e.target.value)}
                      className="border border-slate-200 rounded px-2 py-1 text-xs">
                      {roles.map(r => <option key={r.role_name} value={r.role_name}>{r.display_name}</option>)}
                    </select>
                    <button data-testid="apply-bulk-role" onClick={handleBulkRoleUpdate}
                      className="bg-[#0176D3] text-white text-xs px-3 py-1.5 rounded-lg">Apply</button>
                  </div>
                )}
              </div>

              <div className="bg-white border border-slate-200 rounded-xl overflow-hidden" data-testid="users-table">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr>
                      {bulkRoleMode && <th className="px-3 py-3 w-8"></th>}
                      <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">User</th>
                      <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Role</th>
                      <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Joined</th>
                      <th className="text-right px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {users.map(u => (
                      <tr key={u.email} className="hover:bg-slate-50" data-testid={`user-row-${u.email}`}>
                        {bulkRoleMode && (
                          <td className="px-3 py-4">
                            {u.email !== user?.email && (
                              <input type="checkbox" checked={selectedUsers.has(u.email)}
                                onChange={() => { const s = new Set(selectedUsers); s.has(u.email) ? s.delete(u.email) : s.add(u.email); setSelectedUsers(s); }} />
                            )}
                          </td>
                        )}
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-[#0176D3] text-white flex items-center justify-center text-xs font-bold">
                              {(u.full_name || u.email)[0].toUpperCase()}
                            </div>
                            <div>
                              <p className="font-medium text-slate-800">{u.full_name || u.username}</p>
                              <p className="text-xs text-slate-400">{u.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          {editingRole === u.email ? (
                            <select data-testid={`role-select-${u.email}`} defaultValue={u.role}
                              onChange={e => handleRoleChange(u.email, e.target.value)} onBlur={() => setEditingRole(null)} autoFocus
                              className="border border-slate-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-[#0176D3]">
                              {roles.map(r => <option key={r.role_name} value={r.role_name}>{r.display_name}</option>)}
                            </select>
                          ) : (
                            <button onClick={() => u.email !== user?.email && setEditingRole(u.email)} disabled={u.email === user?.email}
                              className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${ROLE_COLORS[u.role] || ROLE_COLORS.viewer} ${u.email !== user?.email ? "cursor-pointer hover:opacity-80" : "cursor-default"}`}>
                              <Shield size={12} /> {u.role} {u.email !== user?.email && <ChevronDown size={12} />}
                            </button>
                          )}
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-500">{u.assigned_at ? new Date(u.assigned_at).toLocaleDateString() : "--"}</td>
                        <td className="px-6 py-4 text-right">
                          {u.email !== user?.email && (
                            <div className="flex items-center justify-end gap-1">
                              <button data-testid={`edit-user-${u.email}`} onClick={() => { setEditUser(u); setEditName(u.full_name || ""); }}
                                className="text-slate-400 hover:text-blue-500 p-1" title="Edit profile"><Edit2 size={15} /></button>
                              <button data-testid={`reset-pw-${u.email}`} onClick={() => setResetUser(u)}
                                className="text-slate-400 hover:text-amber-500 p-1" title="Reset password"><Key size={15} /></button>
                              <button data-testid={`remove-user-${u.email}`} onClick={() => handleRemove(u.email)}
                                className="text-slate-400 hover:text-red-500 p-1" title="Remove user"><Trash2 size={15} /></button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {users.length === 0 && <div className="py-12 text-center text-sm text-slate-400">No team members yet. Invite someone!</div>}
              </div>
            </div>
          )}

          {/* INVITATIONS TAB */}
          {activeTab === "invitations" && (
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden" data-testid="invitations-table">
              <table className="w-full text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Email</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Role</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Invited By</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Status</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Created</th>
                    <th className="text-right px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {invitations.map((inv, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-6 py-4 font-medium text-slate-800">{inv.email}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${ROLE_COLORS[inv.role] || ROLE_COLORS.viewer}`}>{inv.role}</span>
                      </td>
                      <td className="px-6 py-4 text-slate-500">{inv.invited_by}</td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-600"><Clock size={12} /> {inv.status}</span>
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-500">{inv.created_at ? new Date(inv.created_at).toLocaleDateString() : "--"}</td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button data-testid={`resend-invite-${inv.email}`} onClick={() => handleResendInvite(inv.email)}
                            className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1" title="Resend"><RotateCcw size={14} /></button>
                          <button data-testid={`cancel-invite-${inv.email}`} onClick={() => handleCancelInvite(inv.email)}
                            className="text-xs text-red-500 hover:text-red-700 px-2 py-1" title="Cancel"><X size={14} /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {invitations.length === 0 && <div className="py-12 text-center text-sm text-slate-400">No pending invitations.</div>}
            </div>
          )}

          {/* ROLES TAB */}
          {activeTab === "roles" && (
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden" data-testid="roles-table">
              <table className="w-full text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Role</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Description</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Type</th>
                    <th className="text-right px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {roles.map(r => (
                    <tr key={r.role_name} className="hover:bg-slate-50" data-testid={`role-row-${r.role_name}`}>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${ROLE_COLORS[r.role_name] || ROLE_COLORS.viewer}`}>{r.display_name}</span>
                      </td>
                      <td className="px-6 py-4 text-slate-500 text-xs">{r.description}</td>
                      <td className="px-6 py-4">
                        <span className={`text-xs px-2 py-0.5 rounded ${SYSTEM_ROLES.has(r.role_name) ? "bg-slate-100 text-slate-600" : "bg-blue-100 text-blue-700"}`}>
                          {SYSTEM_ROLES.has(r.role_name) ? "System" : "Custom"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        {!SYSTEM_ROLES.has(r.role_name) && (
                          <button data-testid={`delete-role-${r.role_name}`} onClick={() => handleDeleteRole(r.role_name)}
                            className="text-red-400 hover:text-red-600 text-xs">
                            <Trash2 size={14} />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* AUDIT LOG TAB */}
          {activeTab === "audit" && (
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden" data-testid="audit-log-table">
              <table className="w-full text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Time</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">User</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Action</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {auditLogs.map((log, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-6 py-4 text-xs text-slate-500 whitespace-nowrap">{log.created_at ? new Date(log.created_at).toLocaleString() : "--"}</td>
                      <td className="px-6 py-4 text-slate-700">{log.user_id}</td>
                      <td className="px-6 py-4"><span className="bg-slate-100 text-slate-700 text-xs px-2 py-1 rounded font-mono">{log.action}</span></td>
                      <td className="px-6 py-4 text-xs text-slate-500">{log.detail ? JSON.stringify(log.detail) : "--"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {auditLogs.length === 0 && <div className="py-12 text-center text-sm text-slate-400">No audit log entries yet.</div>}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default UserManagement;
