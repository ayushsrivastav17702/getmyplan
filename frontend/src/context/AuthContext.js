import { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { API } from "../App";

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [tenantId, setTenantId] = useState(null);
  const [tenantInfo, setTenantInfo] = useState(null);
  const [branding, setBranding] = useState(null);
  const [permissions, setPermissions] = useState([]);
  const [trialInfo, setTrialInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);
  const interceptorId = useRef(null);

  // Setup 401 response interceptor
  useEffect(() => {
    interceptorId.current = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Don't intercept login requests themselves
          const url = error.config?.url || "";
          if (!url.includes("/auth/login")) {
            setSessionExpired(true);
            setUser(null);
            setToken(null);
            setTenantId(null);
            setTenantInfo(null);
            setBranding(null);
            setPermissions([]);
            setTrialInfo(null);
            delete axios.defaults.headers.common["Authorization"];
            delete axios.defaults.headers.common["X-Tenant-ID"];
            localStorage.removeItem("merch_auth");
          }
        }
        return Promise.reject(error);
      }
    );
    return () => {
      if (interceptorId.current !== null) {
        axios.interceptors.response.eject(interceptorId.current);
      }
    };
  }, []);

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
        setBranding(data.branding || null);
        setPermissions(data.permissions || data.user?.permissions || []);
        setTrialInfo(data.trialInfo || null);
        axios.defaults.headers.common["Authorization"] = `Bearer ${data.token}`;
        axios.defaults.headers.common["X-Tenant-ID"] = data.tenantId;
      } catch (e) {
        localStorage.removeItem("merch_auth");
      }
    }
    setLoading(false);
  }, []);

  const clearSessionExpired = useCallback(() => setSessionExpired(false), []);

  const login = useCallback(async (email, password, selectedTenantId) => {
    setSessionExpired(false);
    const resp = await axios.post(`${API}/auth/login`, { email, password }, {
      headers: { "X-Tenant-ID": selectedTenantId },
    });
    const { access_token, user: userData, trial_info } = resp.data;
    const userPerms = userData.permissions || [];
    const trialData = trial_info || null;

    // Fetch tenant info + branding
    let tInfo = null;
    let brandData = null;
    try {
      const [tResp, bResp] = await Promise.all([
        axios.get(`${API}/tenants/${selectedTenantId}/status`, {
          headers: { "X-Tenant-ID": selectedTenantId, Authorization: `Bearer ${access_token}` },
        }),
        axios.get(`${API}/tenants/${selectedTenantId}/branding`, {
          headers: { "X-Tenant-ID": selectedTenantId, Authorization: `Bearer ${access_token}` },
        }).catch(() => ({ data: null })),
      ]);
      tInfo = tResp.data;
      brandData = bResp.data;
    } catch (e) {
      tInfo = { tenant_id: selectedTenantId, company_name: selectedTenantId };
    }

    setUser(userData);
    setToken(access_token);
    setTenantId(selectedTenantId);
    setTenantInfo(tInfo);
    setBranding(brandData);
    setPermissions(userPerms);
    setTrialInfo(trialData);

    axios.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
    axios.defaults.headers.common["X-Tenant-ID"] = selectedTenantId;

    localStorage.setItem("merch_auth", JSON.stringify({
      user: userData,
      token: access_token,
      tenantId: selectedTenantId,
      tenantInfo: tInfo,
      branding: brandData,
      permissions: userPerms,
      trialInfo: trialData,
    }));

    return userData;
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    setTenantId(null);
    setTenantInfo(null);
    setBranding(null);
    setPermissions([]);
    setTrialInfo(null);
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
      user, token, tenantId, tenantInfo, branding, permissions, trialInfo,
      loading, isAuthenticated, sessionExpired,
      login, logout, hasPermission, hasRole, clearSessionExpired,
    }}>
      {children}
    </AuthContext.Provider>
  );
};
