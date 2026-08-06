import { useAuth } from "./useAuth";

export const usePermissions = () => {
  const { user, hasRole, hasPermission, isAuthenticated } = useAuth();

  return {
    isVendor: hasRole("Vendor"),
    isAdmin: hasRole("Admin"),
    isManager: hasRole("Manager"),
    isFinance: hasRole("Finance"),
    isCEO: hasRole("CEO"),
    isCFO: hasRole("CFO"),
    isProcurement: hasRole("Procurement"),

    canManageVendors: hasPermission("manage_vendors") || hasRole("Admin"),
    canManageRFQs: hasPermission("manage_rfq") || hasRole("Admin"),
    canApprovePRs: hasPermission("approve_pr") || hasRole("Admin"),
    canApprovePOs: hasPermission("approve_po") || hasRole("Admin"),
    canViewAuditLogs: hasRole("Admin") || hasRole("CEO") || hasRole("CFO"),
    canAccessSettings: hasRole("Admin") || hasRole("CEO"),

    hasPermission,
    hasRole,
    isAuthenticated,
    user
  };
};
