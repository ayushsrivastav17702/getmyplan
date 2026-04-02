import { createContext, useContext, useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "../App";

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [tenantId, setTenantId] = useState(null);
  const [tenantInfo, setTenantInfo] = useState(null);
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Restore session from localStorage
  useEffect(() => {
    const stored = localStorage.getItem("merch_auth");
    if (stored) {
      try {
        const data = JSON.parse(stored);
        setUser(data.user);
        setToken(data.token);
        setTenantId(data.tenantId);
        setTenantInfo(data.tenantInfo);
        setPermissions(data.permissions || data.user?.permissions || []);
        axios.defaults.headers.common["Authorization"] = `Bearer ${data.token}`;
        axios.defaults.headers.common["X-Tenant-ID"] = data.tenantId;
      } catch (e) {
        localStorage.removeItem("merch_auth");
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email, password, selectedTenantId) => {
    const resp = await axios.post(`${API}/auth/login`, { email, password }, {
      headers: { "X-Tenant-ID": selectedTenantId },
    });
    const { access_token, user: userData } = resp.data;
    const userPerms = userData.permissions || [];

    // Fetch tenant info
    let tInfo = null;
    try {
      const tResp = await axios.get(`${API}/tenants/${selectedTenantId}/status`, {
        headers: { "X-Tenant-ID": selectedTenantId, Authorization: `Bearer ${access_token}` },
      });
      tInfo = tResp.data;
    } catch (e) {
      tInfo = { tenant_id: selectedTenantId, company_name: selectedTenantId };
    }

    setUser(userData);
    setToken(access_token);
    setTenantId(selectedTenantId);
    setTenantInfo(tInfo);
    setPermissions(userPerms);

    axios.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
    axios.defaults.headers.common["X-Tenant-ID"] = selectedTenantId;

    localStorage.setItem("merch_auth", JSON.stringify({
      user: userData,
      token: access_token,
      tenantId: selectedTenantId,
      tenantInfo: tInfo,
      permissions: userPerms,
    }));

    return userData;
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    setTenantId(null);
    setTenantInfo(null);
    setPermissions([]);
    delete axios.defaults.headers.common["Authorization"];
    delete axios.defaults.headers.common["X-Tenant-ID"];
    localStorage.removeItem("merch_auth");
  }, []);

  const hasPermission = useCallback((perm) => {
    if (!user) return false;
    const role = user.role;
    if (role === "admin" || role === "super_admin") return true;
    return permissions.includes(perm);
  }, [user, permissions]);

  const hasRole = useCallback((allowedRoles) => {
    if (!user) return false;
    if (typeof allowedRoles === "string") return user.role === allowedRoles;
    return allowedRoles.includes(user.role);
  }, [user]);

  const isAuthenticated = !!token && !!user;

  return (
    <AuthContext.Provider value={{
      user, token, tenantId, tenantInfo, permissions,
      loading, isAuthenticated,
      login, logout, hasPermission, hasRole,
    }}>
      {children}
    </AuthContext.Provider>
  );
};
