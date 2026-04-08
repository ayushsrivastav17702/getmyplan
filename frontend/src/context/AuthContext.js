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
  const [planInfo, setPlanInfo] = useState(null);
  const [mustChangePassword, setMustChangePassword] = useState(false);
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
            setPlanInfo(null);
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
        setPlanInfo(data.planInfo || null);
        axios.defaults.headers.common["Authorization"] = `Bearer ${data.token}`;
        axios.defaults.headers.common["X-Tenant-ID"] = data.tenantId;
      } catch (e) {
        localStorage.removeItem("merch_auth");
      }
    }
    setLoading(false);
  }, []);

  const clearSessionExpired = useCallback(() => setSessionExpired(false), []);

  const login = useCallback(async (email, password) => {
    setSessionExpired(false);
    // Clear any stale auth headers before login
    delete axios.defaults.headers.common["Authorization"];
    delete axios.defaults.headers.common["X-Tenant-ID"];
    const resp = await axios.post(`${API}/auth/login`, { email, password });
    const { access_token, user: userData, trial_info, plan_info, tenant_id: resolvedTenantId, must_change_password } = resp.data;
    const tid = resolvedTenantId || userData.tenant_id;
    const userPerms = userData.permissions || [];
    const trialData = trial_info || null;
    const planData = plan_info || null;

    // Set auth headers immediately so subsequent calls work
    axios.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
    axios.defaults.headers.common["X-Tenant-ID"] = tid;

    // Fetch tenant info + branding
    let tInfo = null;
    let brandData = null;
    try {
      const [tResp, bResp] = await Promise.all([
        axios.get(`${API}/tenants/${tid}/status`),
        axios.get(`${API}/tenants/${tid}/branding`).catch(() => ({ data: null })),
      ]);
      tInfo = tResp.data;
      brandData = bResp.data;
    } catch (e) {
      tInfo = { tenant_id: tid, company_name: tid };
    }

    const mustChangePw = !!must_change_password;

    setUser(userData);
    setToken(access_token);
    setTenantId(tid);
    setTenantInfo(tInfo);
    setBranding(brandData);
    setPermissions(userPerms);
    setTrialInfo(trialData);
    setPlanInfo(planData);
    setMustChangePassword(mustChangePw);

    localStorage.setItem("merch_auth", JSON.stringify({
      user: userData,
      token: access_token,
      tenantId: tid,
      tenantInfo: tInfo,
      branding: brandData,
      permissions: userPerms,
      trialInfo: trialData,
      planInfo: planData,
      mustChangePassword: mustChangePw,
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
    setPlanInfo(null);
    setMustChangePassword(false);
    delete axios.defaults.headers.common["Authorization"];
    delete axios.defaults.headers.common["X-Tenant-ID"];
    localStorage.removeItem("merch_auth");
  }, []);

  const clearMustChangePassword = useCallback(() => {
    setMustChangePassword(false);
    const stored = localStorage.getItem("merch_auth");
    if (stored) {
      try {
        const data = JSON.parse(stored);
        data.mustChangePassword = false;
        localStorage.setItem("merch_auth", JSON.stringify(data));
      } catch {}
    }
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
      user, token, tenantId, tenantInfo, branding, permissions, trialInfo, planInfo,
      mustChangePassword, loading, isAuthenticated, sessionExpired,
      login, logout, hasPermission, hasRole, clearSessionExpired, clearMustChangePassword,
    }}>
      {children}
    </AuthContext.Provider>
  );
};
