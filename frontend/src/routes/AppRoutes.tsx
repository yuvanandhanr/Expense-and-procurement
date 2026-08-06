import React, { Suspense, lazy } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { DashboardLayout } from "../layouts/DashboardLayout";
import { Skeleton } from "../components/ui";

// Lazy-loaded pages
const Login = lazy(() => import("../pages/Login"));
const Dashboard = lazy(() => import("../pages/Dashboard"));
const PurchaseRequisitions = lazy(() => import("../pages/PurchaseRequisitions"));
const Approvals = lazy(() => import("../pages/Approvals"));
const Vendors = lazy(() => import("../pages/Vendors"));
const RFQs = lazy(() => import("../pages/RFQs"));
const Quotations = lazy(() => import("../pages/Quotations"));
const PurchaseOrders = lazy(() => import("../pages/PurchaseOrders"));
const Contracts = lazy(() => import("../pages/Contracts"));
const Deliveries = lazy(() => import("../pages/Deliveries"));
const GRNs = lazy(() => import("../pages/GRNs"));
const Assets = lazy(() => import("../pages/Assets"));
const Invoices = lazy(() => import("../pages/Invoices"));
const Analytics = lazy(() => import("../pages/Analytics"));
const Reports = lazy(() => import("../pages/Reports"));
const AuditLogs = lazy(() => import("../pages/AuditLogs"));
const SystemHealth = lazy(() => import("../pages/SystemHealth"));
const Settings = lazy(() => import("../pages/Settings"));
const GlobalSearch = lazy(() => import("../pages/GlobalSearch"));
const VendorPortal = lazy(() => import("../pages/VendorPortal"));
const Users = lazy(() => import("../pages/Users"));

// Protected Route Guard
const ProtectedRoute: React.FC<{ children: React.ReactNode; requiredRole?: string; requiredPermission?: string }> = ({
  children,
  requiredRole,
  requiredPermission,
}) => {
  const { isAuthenticated, isLoading, hasRole, hasPermission } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md space-y-4">
          <Skeleton className="h-8 w-2/3 mx-auto" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Cross-role redirect guards
  if (hasRole("Vendor") && requiredRole !== "Vendor") {
    return <Navigate to="/vendor-portal" replace />;
  }

  if (!hasRole("Vendor") && requiredRole === "Vendor") {
    return <Navigate to="/" replace />;
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return <Navigate to="/" replace />;
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <Navigate to="/" replace />;
  }

  return <DashboardLayout>{children}</DashboardLayout>;
};

export const AppRoutes: React.FC = () => {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-background">
          <div className="flex flex-col items-center space-y-4">
            <div className="w-12 h-12 rounded-full border-4 border-primary border-t-transparent animate-spin" />
            <span className="text-sm font-semibold tracking-wider text-muted-foreground uppercase">
              Loading workspace...
            </span>
          </div>
        </div>
      }
    >
      <Routes>
        {/* Auth routes */}
        <Route path="/login" element={<Login />} />

        {/* Operational protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/search"
          element={
            <ProtectedRoute>
              <GlobalSearch />
            </ProtectedRoute>
          }
        />
        <Route
          path="/prs"
          element={
            <ProtectedRoute>
              <PurchaseRequisitions />
            </ProtectedRoute>
          }
        />
        <Route
          path="/approvals"
          element={
            <ProtectedRoute>
              <Approvals />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendors"
          element={
            <ProtectedRoute requiredPermission="manage_vendors">
              <Vendors />
            </ProtectedRoute>
          }
        />
        <Route
          path="/rfqs"
          element={
            <ProtectedRoute requiredPermission="manage_rfq">
              <RFQs />
            </ProtectedRoute>
          }
        />
        <Route
          path="/quotations"
          element={
            <ProtectedRoute requiredPermission="manage_rfq">
              <Quotations />
            </ProtectedRoute>
          }
        />
        <Route
          path="/pos"
          element={
            <ProtectedRoute>
              <PurchaseOrders />
            </ProtectedRoute>
          }
        />
        <Route
          path="/contracts"
          element={
            <ProtectedRoute>
              <Contracts />
            </ProtectedRoute>
          }
        />
        <Route
          path="/deliveries"
          element={
            <ProtectedRoute>
              <Deliveries />
            </ProtectedRoute>
          }
        />
        <Route
          path="/grns"
          element={
            <ProtectedRoute>
              <GRNs />
            </ProtectedRoute>
          }
        />
        <Route
          path="/assets"
          element={
            <ProtectedRoute>
              <Assets />
            </ProtectedRoute>
          }
        />
        <Route
          path="/invoices"
          element={
            <ProtectedRoute>
              <Invoices />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <Analytics />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reports"
          element={
            <ProtectedRoute>
              <Reports />
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit-logs"
          element={
            <ProtectedRoute requiredRole="Admin">
              <AuditLogs />
            </ProtectedRoute>
          }
        />
        <Route
          path="/users"
          element={
            <ProtectedRoute requiredRole="Admin">
              <Users />
            </ProtectedRoute>
          }
        />
        <Route
          path="/monitoring"
          element={
            <ProtectedRoute requiredRole="Admin">
              <SystemHealth />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute requiredRole="Admin">
              <Settings />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendor-portal"
          element={
            <ProtectedRoute requiredRole="Vendor">
              <VendorPortal />
            </ProtectedRoute>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
};
export default AppRoutes;
