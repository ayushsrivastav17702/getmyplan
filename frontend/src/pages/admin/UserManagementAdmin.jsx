import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../../App";
import { toast } from "sonner";
import {
  Users, Plus, RefreshCw, Search, Shield, Copy,
  KeyRound, UserX, UserCheck, ChevronDown,
} from "lucide-react";

const ROLES = ["super_admin", "admin", "merchandiser", "store_manager", "viewer"];

export default function UserManagementAdmin() {
  const [users, setUsers] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterTenant, setFilterTenant] = useState("");
  const [filterRole, setFilterRole] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [showAddUser, setShowAddUser] = useState(false);
  const [userForm, setUserForm] = useState({ email: "", name: "", tenant_id: "", role: "viewer" });
  const [creds, setCreds] = useState(null);
  const [editingRole, setEditingRole] = useState(null); // { email, tenant_id, role }

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [u, t] = await Promise.all([
        axios.get(`${API}/admin/platform/users`),
        axios.get(`${API}/admin/platform/tenants`),
      ]);
      setUsers(u.data.users || []);
      setTenants(t.data.tenants || []);
    } catch (e) {
      if (e.response?.status === 403) toast.error("Super Admin access required");
      else toast.error("Failed to load data");
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const createUser = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post(`${API}/admin/platform/users`, userForm);
      toast.success(`User '${userForm.email}' created`);
      setCreds({ email: userForm.email, password: res.data.temp_password, tenant: userForm.tenant_id });
      setShowAddUser(false);
      setUserForm({ email: "", name: "", tenant_id: "", role: "viewer" });
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to create user");
    }
  };

  const updateRole = async (email, tenant_id, newRole) => {
    try {
      await axios.put(`${API}/admin/platform/users/${encodeURIComponent(email)}/role`, { tenant_id, role: newRole });
      toast.success(`Role updated to ${newRole}`);
      setEditingRole(null);
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to update role");
    }
  };

  const toggleStatus = async (email, tenant_id, currentActive) => {
    try {
      await axios.put(`${API}/admin/platform/users/${encodeURIComponent(email)}/status`, { tenant_id, is_active: !currentActive });
      toast.success(currentActive ? "User deactivated" : "User activated");
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to update status");
    }
  };

  const resetPassword = async (email) => {
    try {
      const res = await axios.post(`${API}/admin/platform/users/${encodeURIComponent(email)}/reset-password`);
      setCreds({ email, password: res.data.temp_password, tenant: "—" });
      toast.success("Password reset successfully");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to reset password");
    }
  };

  const copyText = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  const filtered = users.filter(u => {
    if (filterTenant && u.tenant_id !== filterTenant) return false;
    if (filterRole && u.role !== filterRole) return false;
    if (filterStatus === "active" && !u.is_active) return false;
    if (filterStatus === "inactive" && u.is_active) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!u.email?.toLowerCase().includes(q) && !u.full_name?.toLowerCase().includes(q) && !u.tenant_id?.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const stats = {
    total: users.length,
    active: users.filter(u => u.is_active).length,
    inactive: users.filter(u => !u.is_active).length,
    tenantCount: new Set(users.map(u => u.tenant_id)).size,
  };

  return (
    <div data-testid="user-management-admin" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 data-testid="page-title" className="text-2xl font-bold text-gray-900">User Management</h1>
          <p className="text-sm text-gray-500 mt-1">
            {stats.total} users across {stats.tenantCount} tenants &middot; {stats.active} active, {stats.inactive} inactive
          </p>
        </div>
        <button
          data-testid="add-user-btn"
          onClick={() => setShowAddUser(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C] transition-colors"
        >
          <Plus className="h-4 w-4" /> Add User
        </button>
      </div>

      {/* Credentials banner */}
      {creds && (
        <div data-testid="creds-banner" className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-4">
          <Shield className="h-5 w-5 text-emerald-600 shrink-0" />
          <div className="flex-1 text-sm">
            <p className="font-semibold text-emerald-800">Credentials for {creds.email}</p>
            <p className="text-emerald-700">
              Email: <code className="bg-emerald-100 px-1 rounded">{creds.email}</code> &nbsp;
              Password: <code className="bg-emerald-100 px-1 rounded">{creds.password}</code>
            </p>
          </div>
          <button onClick={() => copyText(`Email: ${creds.email}\nPassword: ${creds.password}`)} className="p-1.5 hover:bg-emerald-100 rounded">
            <Copy className="h-4 w-4 text-emerald-600" />
          </button>
          <button onClick={() => setCreds(null)} className="p-1.5 hover:bg-emerald-100 rounded text-emerald-400 text-lg">&times;</button>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            data-testid="search-input"
            type="text"
            placeholder="Search email, name, or tenant..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>
        <select
          data-testid="filter-tenant"
          value={filterTenant}
          onChange={e => setFilterTenant(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
        >
          <option value="">All Tenants</option>
          {tenants.map(t => <option key={t.tenant_id} value={t.tenant_id}>{t.tenant_id}</option>)}
        </select>
        <select
          data-testid="filter-role"
          value={filterRole}
          onChange={e => setFilterRole(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
        >
          <option value="">All Roles</option>
          {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <select
          data-testid="filter-status"
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        <button
          data-testid="refresh-btn"
          onClick={fetchData}
          className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
        <span className="text-xs text-gray-400 ml-auto">{filtered.length} of {users.length} shown</span>
      </div>

      {/* Users Table */}
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <table data-testid="users-table" className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-3 font-medium text-gray-600">User</th>
              <th className="text-left p-3 font-medium text-gray-600">Tenant</th>
              <th className="text-left p-3 font-medium text-gray-600">Role</th>
              <th className="text-left p-3 font-medium text-gray-600">Status</th>
              <th className="text-left p-3 font-medium text-gray-600">MFA</th>
              <th className="text-left p-3 font-medium text-gray-600">Last Login</th>
              <th className="text-right p-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((u, i) => {
              const isEditing = editingRole?.email === u.email && editingRole?.tenant_id === u.tenant_id;
              const isActive = u.is_active !== false && u.active !== false;
              return (
                <tr key={`${u.email}-${u.tenant_id}-${i}`} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="p-3">
                    <div className="font-medium text-gray-900">{u.email}</div>
                    <div className="text-xs text-gray-400">{u.full_name || u.name || "—"}</div>
                  </td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 bg-gray-100 rounded text-xs font-medium">{u.tenant_id}</span>
                  </td>
                  <td className="p-3">
                    {isEditing ? (
                      <select
                        data-testid={`role-select-${u.email}`}
                        autoFocus
                        value={editingRole.role}
                        onChange={e => setEditingRole({ ...editingRole, role: e.target.value })}
                        onBlur={() => {
                          if (editingRole.role !== u.role) updateRole(u.email, u.tenant_id, editingRole.role);
                          else setEditingRole(null);
                        }}
                        className="border border-indigo-300 rounded px-2 py-0.5 text-xs bg-white focus:ring-1 focus:ring-indigo-400"
                      >
                        {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                      </select>
                    ) : (
                      <button
                        data-testid={`role-badge-${u.email}`}
                        onClick={() => setEditingRole({ email: u.email, tenant_id: u.tenant_id, role: u.role })}
                        className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full text-xs font-medium hover:bg-indigo-100 cursor-pointer transition-colors"
                        title="Click to change role"
                      >
                        {u.role}
                      </button>
                    )}
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${isActive ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-600"}`}>
                      {isActive ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`text-xs ${u.mfa_enabled ? "text-emerald-600 font-medium" : "text-gray-400"}`}>
                      {u.mfa_enabled ? "Enabled" : "Off"}
                    </span>
                  </td>
                  <td className="p-3 text-xs text-gray-400">
                    {u.last_login ? new Date(u.last_login).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "Never"}
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex justify-end gap-1">
                      <button
                        data-testid={`toggle-status-${u.email}`}
                        onClick={() => toggleStatus(u.email, u.tenant_id, isActive)}
                        title={isActive ? "Deactivate" : "Activate"}
                        className={`p-1.5 rounded hover:bg-gray-100 ${isActive ? "text-amber-500" : "text-emerald-500"}`}
                      >
                        {isActive ? <UserX className="h-4 w-4" /> : <UserCheck className="h-4 w-4" />}
                      </button>
                      <button
                        data-testid={`reset-password-${u.email}`}
                        onClick={() => resetPassword(u.email)}
                        title="Reset Password"
                        className="p-1.5 rounded hover:bg-gray-100 text-gray-500"
                      >
                        <KeyRound className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr><td colSpan={7} className="p-8 text-center text-gray-400">
                {loading ? "Loading users..." : "No users match the current filters"}
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Add User Modal */}
      {showAddUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowAddUser(false)}>
          <form data-testid="add-user-modal" onSubmit={createUser} onClick={e => e.stopPropagation()} className="bg-white rounded-xl p-6 w-full max-w-md shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-gray-900">Add User to Tenant</h2>
            <input required type="email" placeholder="Email" value={userForm.email} onChange={e => setUserForm({ ...userForm, email: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" data-testid="user-email-input" />
            <input required placeholder="Full Name" value={userForm.name} onChange={e => setUserForm({ ...userForm, name: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" data-testid="user-name-input" />
            <select required value={userForm.tenant_id} onChange={e => setUserForm({ ...userForm, tenant_id: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" data-testid="user-tenant-select">
              <option value="">Select Tenant</option>
              {tenants.map(t => <option key={t.tenant_id} value={t.tenant_id}>{t.tenant_id} — {t.company_name}</option>)}
            </select>
            <select value={userForm.role} onChange={e => setUserForm({ ...userForm, role: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" data-testid="user-role-select">
              {ROLES.map(r => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
            </select>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowAddUser(false)} className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50">Cancel</button>
              <button data-testid="submit-add-user" type="submit" className="px-4 py-2 text-sm bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C]">Add User</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
