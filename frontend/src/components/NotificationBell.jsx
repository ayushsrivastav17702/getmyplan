import { useState, useEffect, useRef, useCallback } from "react";
import { Bell, X, CheckCheck, AlertTriangle, AlertCircle, Info, Trash2 } from "lucide-react";
import axios from "axios";
import { API } from "../App";

const SEVERITY_CONFIG = {
  critical: { icon: AlertCircle, color: "text-red-600", bg: "bg-red-50", border: "border-red-200", dot: "bg-red-500" },
  warning: { icon: AlertTriangle, color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200", dot: "bg-amber-500" },
  info: { icon: Info, color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-200", dot: "bg-blue-500" },
};

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef(null);

  const fetchUnreadCount = useCallback(async () => {
    try {
      // Tight 2s timeout: this runs on every page load and MUST NOT block the
      // UI if the endpoint is slow. If it takes longer than 2s we fail open
      // with 0 unread — a stale badge is far less bad than a hanging header.
      const resp = await axios.get(`${API}/notifications/unread-count`, { timeout: 2000 });
      setUnreadCount(resp.data.unread_count);
    } catch {
      // Fail open: 0 unread, keep rendering the rest of the app.
      setUnreadCount(0);
    }
  }, []);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await axios.get(`${API}/notifications`, { params: { limit: 30 } });
      setNotifications(resp.data.notifications || []);
      setUnreadCount(resp.data.unread_count || 0);
    } catch {
      // silent
    }
    setLoading(false);
  }, []);

  // Poll unread count every 30s (pause when tab is hidden to avoid stale connections)
  useEffect(() => {
    fetchUnreadCount();
    let interval = setInterval(fetchUnreadCount, 30000);
    const handleVisibility = () => {
      clearInterval(interval);
      if (!document.hidden) {
        fetchUnreadCount();
        interval = setInterval(fetchUnreadCount, 30000);
      }
    };
    document.addEventListener("visibilitychange", handleVisibility);
    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [fetchUnreadCount]);

  // Fetch full list when panel opens
  useEffect(() => {
    if (open) fetchNotifications();
  }, [open, fetchNotifications]);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const markAllRead = async () => {
    try {
      await axios.put(`${API}/notifications/mark-all-read`);
      setUnreadCount(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    } catch {
      // silent
    }
  };

  const clearOld = async () => {
    try {
      await axios.delete(`${API}/notifications/clear`, { params: { days: 7 } });
      fetchNotifications();
    } catch {
      // silent
    }
  };

  const formatTime = (iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    const now = new Date();
    const diff = (now - d) / 1000;
    if (diff < 60) return "Just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={() => setOpen(!open)}
        data-testid="notification-bell"
        className="relative p-2 rounded-lg hover:bg-slate-100 transition"
      >
        <Bell size={20} className="text-slate-600" />
        {unreadCount > 0 && (
          <span
            data-testid="notification-badge"
            className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1"
          >
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div
          data-testid="notification-panel"
          className="absolute right-0 top-full mt-2 w-96 bg-white rounded-xl shadow-xl border border-gray-200 z-50 overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllRead}
                  data-testid="mark-all-read-btn"
                  className="text-[11px] text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                >
                  <CheckCheck size={12} /> Mark all read
                </button>
              )}
              <button
                onClick={clearOld}
                className="text-[11px] text-gray-400 hover:text-gray-600 flex items-center gap-1"
                title="Clear notifications older than 7 days"
              >
                <Trash2 size={12} />
              </button>
              <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X size={14} />
              </button>
            </div>
          </div>

          {/* List */}
          <div className="max-h-96 overflow-y-auto">
            {loading && notifications.length === 0 && (
              <div className="p-6 text-center text-sm text-gray-400">Loading...</div>
            )}
            {!loading && notifications.length === 0 && (
              <div className="p-6 text-center">
                <Bell size={24} className="text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No notifications yet</p>
              </div>
            )}
            {notifications.map((n, i) => {
              const config = SEVERITY_CONFIG[n.severity] || SEVERITY_CONFIG.info;
              const Icon = config.icon;
              return (
                <div
                  key={`${n.type}-${n.created_at}-${i}`}
                  data-testid={`notification-item-${i}`}
                  className={`px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition ${!n.read ? "bg-blue-50/30" : ""}`}
                >
                  <div className="flex gap-3">
                    <div className={`w-8 h-8 rounded-lg ${config.bg} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                      <Icon size={14} className={config.color} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-semibold text-gray-900">{n.title}</span>
                        {!n.read && <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />}
                      </div>
                      <p className="text-xs text-gray-600 line-clamp-2">{n.message}</p>
                      <span className="text-[10px] text-gray-400 mt-1 block">{formatTime(n.created_at)}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
