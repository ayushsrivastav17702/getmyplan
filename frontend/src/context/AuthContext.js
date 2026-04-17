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
  const [mfaChallenge, setMfaChallenge] = useState(null); // { mfa_token, mfa_methods, email }
  const [mfaEnforced, setMfaEnforced] = useState(false);
  const [impersonation, setImpersonation] = useState(() => {
    try { return JSON.parse(localStorage.getItem("merch_impersonation")); } catch { return null; }
  });
  const interceptorId = useRef(null);

  // Setup 401 response interceptor
  useEffect(() => {
    interceptorId.current = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        const status = error.response?.status;
        const detail = error.response?.data?.detail || "";
        if (status === 401 || (status === 403 && detail.includes("not found or inactive"))) {
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
    // CRITICAL: If returning from OAuth callback, skip restore — AuthCallback will handle it
    if (window.location.hash?.includes("session_id=")) {
      setLoading(false);
      return;
    }
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
        setMfaEnforced(data.mfaEnforced || false);
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
    setMfaChallenge(null);
    // Clear any stale auth headers before login
    delete axios.defaults.headers.common["Authorization"];
    delete axios.defaults.headers.common["X-Tenant-ID"];
    const resp = await axios.post(`${API}/auth/login`, { email, password });

    // MFA challenge — don't issue token yet
    if (resp.data.mfa_required) {
      setMfaChallenge({
        mfa_token: resp.data.mfa_token,
        mfa_methods: resp.data.mfa_methods || ["totp", "email_otp"],
        email,
      });
      return { mfa_required: true };
    }

    return _handleLoginSuccess(resp.data);
  }, []);

  const _handleLoginSuccess = useCallback((data) => {
    const { access_token, user: userData, trial_info, plan_info, tenant_id: resolvedTenantId, must_change_password, mfa_enforced } = data;
    const tid = resolvedTenantId || userData.tenant_id;
    const userPerms = userData.permissions || [];
    const trialData = trial_info || null;
    const planData = plan_info || null;

    // Set auth headers immediately so subsequent calls work
    axios.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
    axios.defaults.headers.common["X-Tenant-ID"] = tid;

    const mustChangePw = !!must_change_password;
    const mfaEnf = !!mfa_enforced;

    setUser(userData);
    setToken(access_token);
    setTenantId(tid);
    setPermissions(userPerms);
    setTrialInfo(trialData);
    setPlanInfo(planData);
    setMustChangePassword(mustChangePw);
    setMfaEnforced(mfaEnf);
    setMfaChallenge(null);

    // Fetch tenant info + branding in background
    Promise.all([
      axios.get(`${API}/tenants/${tid}/status`).catch(() => ({ data: { tenant_id: tid, company_name: tid } })),
      axios.get(`${API}/tenants/${tid}/branding`).catch(() => ({ data: null })),
    ]).then(([tResp, bResp]) => {
      setTenantInfo(tResp.data);
      setBranding(bResp.data);
      localStorage.setItem("merch_auth", JSON.stringify({
        user: userData, token: access_token, tenantId: tid,
        tenantInfo: tResp.data, branding: bResp.data,
        permissions: userPerms, trialInfo: trialData, planInfo: planData,
        mustChangePassword: mustChangePw, mfaEnforced: mfaEnf,
      }));
    });

    // Set initial localStorage immediately so page doesn't flash
    localStorage.setItem("merch_auth", JSON.stringify({
      user: userData, token: access_token, tenantId: tid,
      tenantInfo: null, branding: null,
      permissions: userPerms, trialInfo: trialData, planInfo: planData,
      mustChangePassword: mustChangePw, mfaEnforced: mfaEnf,
    }));

    return userData;
  }, []);

  const completeMfaLogin = useCallback((data) => {
    return _handleLoginSuccess(data);
  }, [_handleLoginSuccess]);

  const cancelMfa = useCallback(() => {
    setMfaChallenge(null);
  }, []);

  const startImpersonation = useCallback((data) => {
    // Save current super admin session
    const currentSession = localStorage.getItem("merch_auth");
    const impInfo = {
      originalSession: currentSession,
      impersonatedBy: data.impersonated_by,
      targetTenant: data.tenant_id,
      companyName: data.company_name,
    };
    localStorage.setItem("merch_impersonation", JSON.stringify(impInfo));
    setImpersonation(impInfo);

    // Set new impersonated session
    const { access_token, user: userData, tenant_id: tid } = data;
    const userPerms = userData.permissions || [];

    axios.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
    axios.defaults.headers.common["X-Tenant-ID"] = tid;

    setUser(userData);
    setToken(access_token);
    setTenantId(tid);
    setPermissions(userPerms);
    setTrialInfo(null);
    setPlanInfo(null);
    setMustChangePassword(false);
    setMfaEnforced(false);

    localStorage.setItem("merch_auth", JSON.stringify({
      user: userData, token: access_token, tenantId: tid,
      tenantInfo: null, branding: null,
      permissions: userPerms, trialInfo: null, planInfo: null,
      mustChangePassword: false, mfaEnforced: false,
    }));

    // Fetch tenant info in background
    Promise.all([
      axios.get(`${API}/tenants/${tid}/status`).catch(() => ({ data: { tenant_id: tid, company_name: tid } })),
      axios.get(`${API}/tenants/${tid}/branding`).catch(() => ({ data: null })),
    ]).then(([tResp, bResp]) => {
      setTenantInfo(tResp.data);
      setBranding(bResp.data);
    });
  }, []);

  const stopImpersonation = useCallback(() => {
    if (!impersonation?.originalSession) return;
    // Log impersonation end (fire-and-forget)
    axios.post(`${API}/admin/platform/impersonate/end`).catch(() => {});
    try {
      const original = JSON.parse(impersonation.originalSession);
      setUser(original.user);
      setToken(original.token);
      setTenantId(original.tenantId);
      setTenantInfo(original.tenantInfo);
      setBranding(original.branding || null);
      setPermissions(original.permissions || original.user?.permissions || []);
      setTrialInfo(original.trialInfo || null);
      setPlanInfo(original.planInfo || null);
      setMfaEnforced(original.mfaEnforced || false);
      axios.defaults.headers.common["Authorization"] = `Bearer ${original.token}`;
      axios.defaults.headers.common["X-Tenant-ID"] = original.tenantId;
      localStorage.setItem("merch_auth", impersonation.originalSession);
    } catch {
      // Fallback: full logout
    }
    localStorage.removeItem("merch_impersonation");
    setImpersonation(null);
  }, [impersonation]);

  const isImpersonating = !!impersonation;

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
    setMfaChallenge(null);
    setMfaEnforced(false);
    setImpersonation(null);
    delete axios.defaults.headers.common["Authorization"];
    delete axios.defaults.headers.common["X-Tenant-ID"];
    localStorage.removeItem("merch_auth");
    localStorage.removeItem("merch_impersonation");
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
      mfaChallenge, mfaEnforced, completeMfaLogin, cancelMfa,
      isImpersonating, impersonation, startImpersonation, stopImpersonation,
      login, logout, hasPermission, hasRole, clearSessionExpired, clearMustChangePassword,
    }}>
      {children}
    </AuthContext.Provider>
  );
};
