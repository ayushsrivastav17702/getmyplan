import { useAuth } from "../context/AuthContext";

/**
 * Conditionally render children based on user permissions.
 * Usage: <PermissionGate permission="analytics.gap.view">...</PermissionGate>
 *        <PermissionGate roles={["admin","merchandiser"]}>...</PermissionGate>
 */
const PermissionGate = ({ children, permission, roles, fallback = null }) => {
  const { hasPermission, hasRole } = useAuth();

  if (permission && !hasPermission(permission)) return fallback;
  if (roles && !hasRole(roles)) return fallback;

  return children;
};

export default PermissionGate;
