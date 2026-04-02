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
        // Set default headers
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

    // Set default headers for all subsequent requests
    axios.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
    axios.defaults.headers.common["X-Tenant-ID"] = selectedTenantId;

    // Persist
    localStorage.setItem("merch_auth", JSON.stringify({
      user: userData,
      token: access_token,
      tenantId: selectedTenantId,
      tenantInfo: tInfo,
    }));

    return userData;
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    setTenantId(null);
    setTenantInfo(null);
    delete axios.defaults.headers.common["Authorization"];
    delete axios.defaults.headers.common["X-Tenant-ID"];
    localStorage.removeItem("merch_auth");
  }, []);

  const isAuthenticated = !!token && !!user;

  return (
    <AuthContext.Provider value={{
      user, token, tenantId, tenantInfo,
      loading, isAuthenticated,
      login, logout,
    }}>
      {children}
    </AuthContext.Provider>
  );
};
