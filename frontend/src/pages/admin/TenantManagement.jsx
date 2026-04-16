import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "../../App";
import { useAuth } from "../../context/AuthContext";
import { toast } from "sonner";
import {
  Building2, Users, Plus, Shield, Trash2, LogIn, RefreshCw,
  Search, ChevronDown, Copy, Eye, EyeOff,
} from "lucide-react";

const PLANS = ["starter", "professional", "business", "enterprise"];
const ROLES = ["admin", "merchandiser", "viewer"];

export default function TenantManagement() {
  const navigate = useNavigate();
  const { startImpersonation } = useAuth();
  const [tenants, setTenants] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("tenants");
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [showAddUser, setShowAddUser] = useState(false);
  const [form, setForm] = useState({ tenant_id: "", company_name: "", admin_email: "", admin_name: "", plan: "professional" });
  const [userForm, setUserForm] = useState({ email: "", name: "", tenant_id: "", role: "viewer" });
  const [creds, setCreds] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [t, u] = await Promise.all([
        axios.get(`${API}/admin/platform/tenants`),
        axios.get(`${API}/admin/platform/users`),
      ]);
      setTenants(t.data.tenants || []);
      setUsers(u.data.users || []);
    } catch (e) {
      if (e.response?.status === 403) toast.error("Super Admin access required");
      else toast.error("Failed to load data");
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const createTenant = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post(`${API}/admin/platform/tenants`, form);
      toast.success(`Tenant '${form.tenant_id}' created`);
      setCreds({ email: form.admin_email, password: res.data.temp_password, tenant: form.tenant_id });
      setShowCreate(false);
      setForm({ tenant_id: "", company_name: "", admin_email: "", admin_name: "", plan: "professional" });
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to create tenant");
    }
  };

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

  const toggleStatus = async (tid, currentStatus) => {
    const newStatus = currentStatus === "active" ? "suspended" : "active";
    try {
      await axios.put(`${API}/admin/platform/tenants/${tid}/status`, { status: newStatus });
      toast.success(`Tenant ${newStatus}`);
      fetchData();
    } catch { toast.error("Failed to update status"); }
  };

  const impersonate = async (tid) => {
    try {
      const res = await axios.post(`${API}/admin/platform/impersonate/${tid}`);
      startImpersonation(res.data);
      toast.success(`Now viewing as ${res.data.company_name || tid}`);
      navigate("/dashboard");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to impersonate");
    }
  };

  const copyText = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  const filtered = tab === "tenants"
    ? tenants.filter(t => !search || t.tenant_id?.includes(search) || t.company_name?.toLowerCase().includes(search.toLowerCase()))
    : users.filter(u => !search || u.email?.includes(search) || u.tenant_id?.includes(search));

  return (
    <div data-testid="tenant-management" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Platform Admin</h1>
          <p className="text-sm text-gray-500 mt-1">{tenants.length} tenants, {users.length} users</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowAddUser(true)} className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium border border-gray-300 rounded-lg hover:bg-gray-50">
            <Users className="h-4 w-4" /> Add User
          </button>
          <button data-testid="create-tenant-btn" onClick={() => setShowCreate(true)} className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C]">
            <Plus className="h-4 w-4" /> New Tenant
          </button>
        </div>
      </div>

      {/* Credentials banner */}
      {creds && (
        <div data-testid="creds-banner" className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-4">
          <Shield className="h-5 w-5 text-emerald-600 shrink-0" />
          <div className="flex-1 text-sm">
            <p className="font-semibold text-emerald-800">Credentials for {creds.tenant}</p>
            <p className="text-emerald-700">Email: <code className="bg-emerald-100 px-1 rounded">{creds.email}</code> &nbsp; Password: <code className="bg-emerald-100 px-1 rounded">{creds.password}</code></p>
          </div>
          <button onClick={() => copyText(`Email: ${creds.email}\nPassword: ${creds.password}`)} className="p-1.5 hover:bg-emerald-100 rounded"><Copy className="h-4 w-4 text-emerald-600" /></button>
          <button onClick={() => setCreds(null)} className="p-1.5 hover:bg-emerald-100 rounded text-emerald-400">&times;</button>
        </div>
      )}

      {/* Tabs + Search */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
          <button onClick={() => setTab("tenants")} className={`px-4 py-1.5 rounded-md text-sm font-medium ${tab === "tenants" ? "bg-white shadow text-gray-900" : "text-gray-500"}`}>
            <Building2 className="h-4 w-4 inline mr-1.5" />Tenants
          </button>
          <button onClick={() => setTab("users")} className={`px-4 py-1.5 rounded-md text-sm font-medium ${tab === "users" ? "bg-white shadow text-gray-900" : "text-gray-500"}`}>
            <Users className="h-4 w-4 inline mr-1.5" />Users
          </button>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input type="text" placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)}
              className="pl-9 pr-3 py-1.5 border border-gray-300 rounded-lg text-sm w-52" />
          </div>
          <button onClick={fetchData} className="p-1.5 border border-gray-300 rounded-lg hover:bg-gray-50">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Tenants Table */}
      {tab === "tenants" && (
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-3 font-medium text-gray-600">Tenant</th>
                <th className="text-left p-3 font-medium text-gray-600">Company</th>
                <th className="text-left p-3 font-medium text-gray-600">Plan</th>
                <th className="text-left p-3 font-medium text-gray-600">Status</th>
                <th className="text-left p-3 font-medium text-gray-600">Users</th>
                <th className="text-left p-3 font-medium text-gray-600">Created</th>
                <th className="text-right p-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(t => (
                <tr key={t.tenant_id} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="p-3 font-medium text-gray-900">{t.tenant_id}</td>
                  <td className="p-3 text-gray-600">{t.company_name || "—"}</td>
                  <td className="p-3"><span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">{t.plan || "—"}</span></td>
                  <td className="p-3"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${t.status === "active" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>{t.status}</span></td>
                  <td className="p-3 text-gray-600">{t.user_count || 0}</td>
                  <td className="p-3 text-gray-400 text-xs">{t.created_at ? new Date(t.created_at).toLocaleDateString() : "—"}</td>
                  <td className="p-3 text-right">
                    <div className="flex justify-end gap-1">
                      <button onClick={() => impersonate(t.tenant_id)} title="Login As" className="p-1.5 hover:bg-blue-50 rounded text-blue-600"><LogIn className="h-4 w-4" /></button>
                      <button onClick={() => toggleStatus(t.tenant_id, t.status)} title={t.status === "active" ? "Suspend" : "Activate"}
                        className={`p-1.5 hover:bg-gray-100 rounded ${t.status === "active" ? "text-amber-500" : "text-emerald-500"}`}>
                        {t.status === "active" ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && <tr><td colSpan={7} className="p-8 text-center text-gray-400">No tenants found</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {/* Users Table */}
      {tab === "users" && (
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-3 font-medium text-gray-600">Email</th>
                <th className="text-left p-3 font-medium text-gray-600">Name</th>
                <th className="text-left p-3 font-medium text-gray-600">Tenant</th>
                <th className="text-left p-3 font-medium text-gray-600">Role</th>
                <th className="text-left p-3 font-medium text-gray-600">Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((u, i) => (
                <tr key={i} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="p-3 font-medium text-gray-900">{u.email}</td>
                  <td className="p-3 text-gray-600">{u.name || "—"}</td>
                  <td className="p-3"><span className="px-2 py-0.5 bg-gray-100 rounded text-xs">{u.tenant_id}</span></td>
                  <td className="p-3"><span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full text-xs font-medium">{u.role}</span></td>
                  <td className="p-3"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${u.active ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-500"}`}>{u.active ? "Active" : "Inactive"}</span></td>
                </tr>
              ))}
              {filtered.length === 0 && <tr><td colSpan={5} className="p-8 text-center text-gray-400">No users found</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Tenant Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowCreate(false)}>
          <form onSubmit={createTenant} onClick={e => e.stopPropagation()} className="bg-white rounded-xl p-6 w-full max-w-md shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-gray-900">Create New Tenant</h2>
            <input required placeholder="Tenant ID (e.g. acme_corp)" value={form.tenant_id} onChange={e => setForm({ ...form, tenant_id: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "") })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            <input required placeholder="Company Name" value={form.company_name} onChange={e => setForm({ ...form, company_name: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            <input required type="email" placeholder="Admin Email" value={form.admin_email} onChange={e => setForm({ ...form, admin_email: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            <input required placeholder="Admin Name" value={form.admin_name} onChange={e => setForm({ ...form, admin_name: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            <select value={form.plan} onChange={e => setForm({ ...form, plan: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
              {PLANS.map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
            </select>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50">Cancel</button>
              <button type="submit" className="px-4 py-2 text-sm bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C]">Create Tenant</button>
            </div>
          </form>
        </div>
      )}

      {/* Add User Modal */}
      {showAddUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowAddUser(false)}>
          <form onSubmit={createUser} onClick={e => e.stopPropagation()} className="bg-white rounded-xl p-6 w-full max-w-md shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-gray-900">Add User to Tenant</h2>
            <input required type="email" placeholder="Email" value={userForm.email} onChange={e => setUserForm({ ...userForm, email: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            <input required placeholder="Name" value={userForm.name} onChange={e => setUserForm({ ...userForm, name: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            <select required value={userForm.tenant_id} onChange={e => setUserForm({ ...userForm, tenant_id: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
              <option value="">Select Tenant</option>
              {tenants.map(t => <option key={t.tenant_id} value={t.tenant_id}>{t.tenant_id} — {t.company_name}</option>)}
            </select>
            <select value={userForm.role} onChange={e => setUserForm({ ...userForm, role: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
              {ROLES.map(r => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
            </select>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowAddUser(false)} className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50">Cancel</button>
              <button type="submit" className="px-4 py-2 text-sm bg-[#0B2545] text-white rounded-lg hover:bg-[#13315C]">Add User</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
