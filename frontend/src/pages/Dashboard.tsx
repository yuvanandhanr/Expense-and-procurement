import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import { Card, CardHeader, CardTitle, CardContent, Skeleton, Badge, HeroTimestamp, StatusBadge, Button } from "../components/ui";
import { formatDate } from "../utils/helpers";
import { Bar, Doughnut, Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { 
  HardDrive, Receipt, FileText, CheckCircle, Clock, AlertCircle, 
  TrendingUp, IndianRupee, ShieldCheck, ArrowUpRight, ChevronRight, 
  Calendar, Layers, AlertTriangle, Sparkles 
} from "lucide-react";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

export const Dashboard: React.FC = () => {
  const { user, hasRole } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [expenses, setExpenses] = useState<any[]>([]);
  const [prs, setPrs] = useState<any[]>([]);
  const [approvals, setApprovals] = useState<any[]>([]);
  const [myAssetsList, setMyAssetsList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState<"monthly" | "yearly" | "all">("monthly");

  const isApprover = hasRole("Manager") || hasRole("Finance") || hasRole("Finance Manager") || hasRole("CFO") || hasRole("Admin") || hasRole("CEO");
  const isFinanceOrAdmin = hasRole("Finance") || hasRole("Finance Manager") || hasRole("CFO") || hasRole("Admin") || hasRole("CEO");

  const fetchAllLiveData = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const [dashRes, expRes, prRes, appRes, astRes] = await Promise.all([
        api.get("/dashboard").catch(() => ({ data: null })),
        api.get("/expenses").catch(() => ({ data: [] })),
        api.get("/pr").catch(() => ({ data: [] })),
        api.get("/approvals").catch(() => ({ data: [] })),
        api.get("/assets/my-assets").catch(() => ({ data: [] }))
      ]);

      if (dashRes?.data) setData(dashRes.data);
      if (expRes?.data) setExpenses(expRes.data);
      if (prRes?.data) setPrs(prRes.data);
      if (appRes?.data) setApprovals(appRes.data);
      if (astRes?.data) setMyAssetsList(astRes.data);
    } catch (err) {
      console.error("Failed to load real-time dashboard data:", err);
    } finally {
      if (isInitial) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllLiveData(true);
    const interval = setInterval(() => {
      fetchAllLiveData(false);
    }, 10000);

    const onFocus = () => fetchAllLiveData(false);
    window.addEventListener("focus", onFocus);

    return () => {
      clearInterval(interval);
      window.removeEventListener("focus", onFocus);
    };
  }, [fetchAllLiveData]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-64 w-full lg:col-span-2" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  // Real-time calculated live aggregates
  const safeExpenses = Array.isArray(expenses) ? expenses : [];
  const safePrs = Array.isArray(prs) ? prs : [];
  const safeApprovals = Array.isArray(approvals) ? approvals : [];
  const safeMyAssetsList = Array.isArray(myAssetsList) ? myAssetsList : [];

  // Strict personal filtering: Every user on My Dashboard sees only their own requests & claims
  const userFilteredExpenses = safeExpenses.filter((e: any) => !user || e.employee_id === user.user_id);

  const userFilteredPrs = safePrs.filter((p: any) => !user || p.requestor_id === user.user_id);

  const userFilteredAssets = safeMyAssetsList.filter(
    (a: any) => !user || a.assigned_employee_id === user.user_id || !a.assigned_employee_id
  );

  const cadence = data?.widgets?.financial_cadence || {};
  const monthlySpend = cadence.monthly_spend;
  const yearlySpend = cadence.yearly_spend;
  const allTimeSpend = cadence.all_time_spend;
  const lowStockAlerts = data?.widgets?.low_stock_alerts;

  // Real-time fallback financial calculations strictly using approved financial statuses
  const APPROVED_STATUSES = ["Approved", "Finance Verified", "Paid", "Approved for Payment", "Payment Requested"];
  const approvedExpenses = userFilteredExpenses.filter((e: any) => 
    APPROVED_STATUSES.includes(e?.status)
  );

  const approvedPrs = safePrs.filter((p: any) => 
    ["Approved", "Ordered", "Received", "Closed"].includes(p?.status)
  );

  const now = new Date();
  const currentMonthStart = new Date(now.getFullYear(), now.getMonth(), 1);
  const currentYearStart = new Date(now.getFullYear(), 0, 1);

  const fallbackMtd = approvedExpenses
    .filter((e: any) => new Date(e?.created_at || e?.submission_date || e?.date || 0) >= currentMonthStart)
    .reduce((sum: number, e: any) => sum + (Number(e?.total_amount) || 0), 0);

  const fallbackYtd = approvedExpenses
    .filter((e: any) => new Date(e?.created_at || e?.submission_date || e?.date || 0) >= currentYearStart)
    .reduce((sum: number, e: any) => sum + (Number(e?.total_amount) || 0), 0);

  const fallbackAllTime = approvedExpenses
    .reduce((sum: number, e: any) => sum + (Number(e?.total_amount) || 0), 0);

  const fallbackMtdPr = approvedPrs
    .filter((p: any) => new Date(p?.created_at || 0) >= currentMonthStart)
    .reduce((sum: number, p: any) => sum + (Number(p?.total_estimated_amount || p?.estimated_cost) || 0), 0);

  const fallbackYtdPr = approvedPrs
    .filter((p: any) => new Date(p?.created_at || 0) >= currentYearStart)
    .reduce((sum: number, p: any) => sum + (Number(p?.total_estimated_amount || p?.estimated_cost) || 0), 0);

  const fallbackAllTimePr = approvedPrs
    .reduce((sum: number, p: any) => sum + (Number(p?.total_estimated_amount || p?.estimated_cost) || 0), 0);

  const getDisplayedSpend = () => {
    if (timeframe === "monthly") {
      return cadence.reimbursements?.monthly_amount !== undefined 
        ? Number(cadence.reimbursements.monthly_amount) 
        : (monthlySpend !== undefined ? Number(monthlySpend) : fallbackMtd);
    }
    if (timeframe === "yearly") {
      return cadence.reimbursements?.yearly_amount !== undefined 
        ? Number(cadence.reimbursements.yearly_amount) 
        : (yearlySpend !== undefined ? Number(yearlySpend) : fallbackYtd);
    }
    // "all"
    return cadence.reimbursements?.all_time_amount !== undefined 
      ? Number(cadence.reimbursements.all_time_amount) 
      : (allTimeSpend !== undefined ? Number(allTimeSpend) : fallbackAllTime);
  };

  const pendingApprovalsCount = isApprover 
    ? safeApprovals.filter((a: any) => {
        const amt = Number(a?.amount || a?.total_amount || a?.estimated_cost || 0);
        if (a?.entity_type === "ExpenseReport" || a?.entity_type === "PurchaseRequisition" || a?.entity_type === "VendorInvoice") {
          if (amt <= 0) return false;
        }
        return a?.status === "Pending" || a?.status === "Under Review" || a?.status?.toLowerCase().includes("pending");
      }).length
    : userFilteredExpenses.filter((e: any) => (Number(e?.total_amount || 0) > 0) && (e?.status?.includes("Pending") || e?.status === "Submitted")).length + 
      userFilteredPrs.filter((p: any) => (Number(p?.total_estimated_amount || p?.estimated_cost || 0) > 0) && (p?.status?.includes("Pending") || p?.status === "Submitted")).length;
  
  const assignedAssetsCount = userFilteredAssets.length || (Array.isArray(data?.widgets?.my_assets) ? data.widgets.my_assets.length : 0);

  // Real-time recent lists
  const recentPRs = [...userFilteredPrs].sort((a: any, b: any) => {
    const isPendingA = (a.status?.toLowerCase().includes("pending") || a.status === "Submitted") && (Number(a.total_estimated_amount || a.estimated_cost || 0) > 0);
    const isPendingB = (b.status?.toLowerCase().includes("pending") || b.status === "Submitted") && (Number(b.total_estimated_amount || b.estimated_cost || 0) > 0);
    if (isPendingA && !isPendingB) return -1;
    if (!isPendingA && isPendingB) return 1;
    const timeA = new Date(a.created_at || 0).getTime();
    const timeB = new Date(b.created_at || 0).getTime();
    return timeB - timeA;
  }).slice(0, 5);

  const recentExpenseList = [...userFilteredExpenses].sort((a: any, b: any) => {
    const isPendingA = (a.status?.toLowerCase().includes("pending") || a.status?.toLowerCase().includes("corrected")) && (Number(a.total_amount || 0) > 0);
    const isPendingB = (b.status?.toLowerCase().includes("pending") || b.status?.toLowerCase().includes("corrected")) && (Number(b.total_amount || 0) > 0);
    if (isPendingA && !isPendingB) return -1;
    if (!isPendingA && isPendingB) return 1;
    const timeA = new Date(a.created_at || a.submission_date || a.date || 0).getTime();
    const timeB = new Date(b.created_at || b.submission_date || b.date || 0).getTime();
    return timeB - timeA;
  }).slice(0, 5);

  return (
    <div className="space-y-7 animate-fade-in">
      {/* Hero Header & Timeframe Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground">
              My Dashboard
            </h1>
            <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping mr-0.5" /> Live Sync
            </span>
          </div>
          <p className="text-xs md:text-sm text-muted-foreground mt-1">
            Welcome back, <span className="font-semibold text-foreground">{user?.first_name ? `${user.first_name} ${user.last_name || ""}`.trim() : "Team Member"}</span> &bull; Your personal expenditure, claims, and assigned assets.
          </p>
        </div>

        {/* Timeframe Cadence Selector */}
        <div className="flex items-center gap-3">
          <div className="flex items-center space-x-1 bg-muted/60 p-1 rounded-xl border border-border/60 shadow-sm">
            <button
              onClick={() => setTimeframe("monthly")}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-1.5 ${
                timeframe === "monthly"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>This Month (MTD)</span>
            </button>
            <button
              onClick={() => setTimeframe("yearly")}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all flex items-center gap-1.5 ${
                timeframe === "yearly"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>This Year (YTD)</span>
            </button>
            <button
              onClick={() => setTimeframe("all")}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                timeframe === "all"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              All Time
            </button>
          </div>
          <HeroTimestamp />
        </div>
      </div>

      {/* Management Financial Overview Link (CEO, CFO, Finance Manager, Admin) */}
      {isFinanceOrAdmin && (
        <div 
          onClick={() => navigate("/analytics")}
          className="p-4 rounded-2xl bg-gradient-to-r from-blue-500/10 via-indigo-500/10 to-blue-500/10 border border-blue-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 cursor-pointer hover:bg-blue-500/15 transition-all group shadow-apple-sm"
        >
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 text-blue-500 flex items-center justify-center font-bold group-hover:scale-105 transition-transform">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-black uppercase tracking-widest bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/30">
                  Company-Wide Overview
                </span>
                <span className="text-xs font-bold text-foreground">
                  Financial Analytics
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                View organization-wide expenditure (MTD/YTD), total & remaining budgets, and departmental summaries under Financial Operations.
              </p>
            </div>
          </div>
          <Button size="sm" className="gap-1 font-bold bg-blue-600 hover:bg-blue-700 text-white shrink-0">
            <span>Open Financial Analytics</span> <ChevronRight className="w-3.5 h-3.5" />
          </Button>
        </div>
      )}

      {/* Low Stock Replenishment Alert Banner (if applicable for Admin/Finance/IT) */}
      {lowStockAlerts?.has_low_stock && isFinanceOrAdmin && (
        <div 
          onClick={() => navigate("/assets")}
          className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between cursor-pointer hover:bg-amber-500/15 transition-colors group shadow-apple-sm"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-500 flex items-center justify-center font-bold">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-amber-600 dark:text-amber-400">
                Low Stock Inventory Replenishment Alert ({lowStockAlerts.low_stock_count} item{lowStockAlerts.low_stock_count > 1 ? 's' : ''} &le; 5 units)
              </h4>
              <p className="text-xs text-muted-foreground mt-0.5">
                {lowStockAlerts.items.map((i: any) => `${i.category} (${i.available_stock} left)`).join(", ")} &mdash; Review inventory and push procurement to Finance Manager.
              </p>
            </div>
          </div>
          <Button size="sm" variant="warning" className="gap-1 font-bold">
            <span>Check Inventory</span> <ChevronRight className="w-3.5 h-3.5" />
          </Button>
        </div>
      )}

      {/* Apple Metrics Overview Bento Grid - 3 Columns strictly personal */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        
        {/* Card 1: Differentiated Personal Monthly vs. Yearly vs. All Time Spend */}
        <div
          onClick={() => navigate("/expenses")}
          title="Click to view your Expense Claims"
          className="apple-card p-5 rounded-2xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-primary/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                {timeframe === "monthly" ? "My Monthly Spend (MTD)" : timeframe === "yearly" ? "My Yearly Spend (YTD)" : "My Total Spend (All Time)"}
              </span>
              <div className="flex items-center gap-1.5">
                <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-primary group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                  <IndianRupee className="w-4 h-4" />
                </div>
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-extrabold tracking-tight text-foreground group-hover:text-primary transition-colors">
                ₹{getDisplayedSpend().toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className="flex items-center gap-1.5 mt-1.5 text-[11px] font-semibold text-primary">
                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-primary/10">
                  {timeframe === "monthly" 
                    ? (cadence.current_month_name || "Current Month") 
                    : timeframe === "yearly" 
                    ? (cadence.current_fiscal_year || `FY ${now.getFullYear()}`) 
                    : "All Time"}
                </span>
                {cadence.mom_growth_percent !== undefined && timeframe === "monthly" && (
                  <span className={`text-[10px] font-bold ${cadence.mom_growth_percent >= 0 ? 'text-amber-500' : 'text-emerald-500'}`}>
                    {cadence.mom_growth_percent >= 0 ? `+${cadence.mom_growth_percent}% MoM` : `${cadence.mom_growth_percent}% MoM`}
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="mt-3.5 pt-2.5 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-primary flex items-center justify-between transition-colors">
            <span>
              {timeframe === "monthly"
                ? `My Monthly Claims: ₹${(cadence.reimbursements?.monthly_amount !== undefined ? cadence.reimbursements.monthly_amount : fallbackMtd).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : timeframe === "yearly"
                ? `My YTD Claims: ₹${(cadence.reimbursements?.yearly_amount !== undefined ? cadence.reimbursements.yearly_amount : fallbackYtd).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : `My All-Time Claims: ₹${(cadence.reimbursements?.all_time_amount !== undefined ? cadence.reimbursements.all_time_amount : fallbackAllTime).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
              }
            </span>
            <span className="font-bold flex items-center">
              My Expenses <ChevronRight className="w-3 h-3 ml-0.5" />
            </span>
          </div>
        </div>

        {/* Card 2: Pending Approvals / My Pending Claims */}
        <div
          onClick={() => {
            if (isApprover) {
              navigate("/approvals");
            } else {
              navigate("/expenses?status=pending");
            }
          }}
          title={isApprover ? "Click to review Pending Approvals" : "Click to review your Pending Claims"}
          className="apple-card p-5 rounded-2xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-amber-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                {isApprover ? "Pending Approvals" : "My Pending Claims"}
              </span>
              <div className="flex items-center gap-1.5">
                <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-amber-500 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                <div className="w-8 h-8 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-500 group-hover:scale-110 transition-transform">
                  <Clock className="w-4 h-4" />
                </div>
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-extrabold tracking-tight text-foreground group-hover:text-amber-500 transition-colors">
                {pendingApprovalsCount}
              </div>
              <div className="flex items-center gap-1.5 mt-1.5 text-[11px] font-semibold text-amber-500">
                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-amber-500/10">
                  {pendingApprovalsCount > 0 ? (isApprover ? "Action Required" : "Awaiting Review") : "All Caught Up"}
                </span>
                <span className="text-muted-foreground text-[10px]">
                  {isApprover ? "in approval inbox" : "awaiting approval"}
                </span>
              </div>
            </div>
          </div>
          <div className="mt-3.5 pt-2.5 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-amber-500 flex items-center justify-between transition-colors">
            <span>{isApprover ? "Awaiting verification & signoff" : "Awaiting manager/finance approval"}</span>
            <span className="font-bold flex items-center">{isApprover ? "Open Queue" : "My Claims"} <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>

        {/* Card 3: Active Assigned Assets */}
        <div
          onClick={() => navigate("/my-assets")}
          title="Click to view and manage Assigned Assets"
          className="apple-card p-5 rounded-2xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-purple-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                Assigned Assets
              </span>
              <div className="flex items-center gap-1.5">
                <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-purple-500 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                <div className="w-8 h-8 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-500 group-hover:scale-110 transition-transform">
                  <HardDrive className="w-4 h-4" />
                </div>
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-extrabold tracking-tight text-foreground group-hover:text-purple-500 transition-colors">
                {assignedAssetsCount}
              </div>
              <div className="flex items-center gap-1.5 mt-1.5 text-[11px] font-semibold text-purple-500">
                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-purple-500/10">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-500 mr-1.5" /> Verified Registry
                </span>
              </div>
            </div>
          </div>
          <div className="mt-3.5 pt-2.5 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-purple-500 flex items-center justify-between transition-colors">
            <span>Hardware & software licenses</span>
            <span className="font-bold flex items-center">My Assets <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>
      </div>

      {/* Main Content Split: Requisitions, Expenses, Trends & Assets */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Left 2 Columns: Requisitions & Recent Expenses */}
        <div className="xl:col-span-2 space-y-6">

          {/* Recent Requisitions Table */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-6 h-6 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <FileText className="w-3.5 h-3.5" />
                </div>
                <CardTitle>My Requisitions</CardTitle>
              </div>
              <Button size="sm" variant="ghost" onClick={() => navigate("/prs")} className="text-xs">
                View All
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-border/50 bg-muted/30 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                      <th className="py-3.5 px-5 whitespace-nowrap">Req #</th>
                      <th className="py-3.5 px-5">Description</th>
                      <th className="py-3.5 px-5 text-right whitespace-nowrap">Amount</th>
                      <th className="py-3.5 px-5 text-center whitespace-nowrap">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    {recentPRs.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="py-6 text-center text-muted-foreground">
                          No requisitions submitted yet.
                        </td>
                      </tr>
                    ) : (
                      recentPRs.map((req: any, idx: number) => (
                        <tr key={idx} className="hover:bg-muted/30 transition-colors">
                          <td className="py-3.5 px-5 font-bold text-primary whitespace-nowrap">{req.pr_number || req.id}</td>
                          <td className="py-3.5 px-5 font-medium">{req.title}</td>
                          <td className="py-3.5 px-5 text-right font-mono font-semibold whitespace-nowrap">₹{(Number(req.total_estimated_amount) || Number(req.amount) || 0).toLocaleString()}</td>
                          <td className="py-3.5 px-5 text-center whitespace-nowrap">
                            <StatusBadge status={req.status} />
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Recent Expenses */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-6 h-6 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <Receipt className="w-3.5 h-3.5" />
                </div>
                <CardTitle>My Expense Claims</CardTitle>
              </div>
              <Button size="sm" variant="ghost" onClick={() => navigate("/expenses")} className="text-xs">
                View Ledger
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentExpenseList.length === 0 ? (
                  <div className="py-6 text-center text-xs text-muted-foreground">No recent expenses found.</div>
                ) : (
                  recentExpenseList.map((exp: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-3.5 rounded-xl border border-border/60 bg-card/60 backdrop-blur-sm hover:border-primary/40 transition-all duration-200 shadow-apple-sm">
                      <div className="flex items-center space-x-3.5">
                        <div className={`p-2 rounded-xl ${
                          ["Approved", "Finance Verified", "Payment Requested"].includes(exp.status) ? 'bg-emerald-500/15 text-emerald-500' : 
                          exp.status === 'Rejected' ? 'bg-rose-500/15 text-rose-500' : 'bg-amber-500/15 text-amber-500'
                        }`}>
                          {["Approved", "Finance Verified", "Payment Requested"].includes(exp.status) ? <CheckCircle className="w-4 h-4" /> : 
                           exp.status === 'Rejected' ? <AlertCircle className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
                        </div>
                        <div>
                          <p className="font-bold text-xs text-foreground">{exp.purpose || exp.title}</p>
                          <p className="text-[11px] text-muted-foreground mt-0.5">{formatDate(exp.created_at || exp.date)}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-mono font-bold text-xs text-foreground">₹{(Number(exp.total_amount) || Number(exp.amount) || 0).toFixed(2)}</p>
                        <div className="mt-1">
                          <StatusBadge status={exp.status} />
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: My Assigned Assets & Governance Cadence */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-6 h-6 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <HardDrive className="w-3.5 h-3.5" />
                </div>
                <CardTitle>My Assigned Assets</CardTitle>
              </div>
              <Button size="sm" variant="ghost" onClick={() => navigate("/my-assets")} className="text-xs">
                Manage
              </Button>
            </CardHeader>
            <CardContent className="space-y-3.5">
              {userFilteredAssets.length === 0 ? (
                <div className="py-8 text-center text-xs text-muted-foreground">No assets currently assigned.</div>
              ) : (
                userFilteredAssets.map((asset: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-xl border border-border/60 bg-card/60 backdrop-blur-sm shadow-apple-sm flex flex-col space-y-2.5 relative overflow-hidden group hover:border-primary/40 transition-all duration-200">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-primary bg-primary/10 px-2.5 py-0.5 rounded-full">
                        {asset.tag || asset.asset_tag || "ASSET"}
                      </span>
                      <span className="flex items-center text-[11px] font-semibold text-emerald-500">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5" />
                        {asset.status || "Assigned"}
                      </span>
                    </div>
                    <h3 className="font-bold text-xs text-foreground pt-1">{asset.name || asset.asset_name}</h3>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Operational Cadence Card */}
          <Card className="bg-gradient-to-br from-primary/5 via-card to-card border-primary/20">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                <CardTitle className="text-sm">{!isFinanceOrAdmin ? "Employee Reminders" : "Periodic Governance"}</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="p-3 rounded-lg bg-background border border-border/60 space-y-1">
                <span className="font-bold text-primary block">Monthly Checklist</span>
                <p className="text-muted-foreground text-[11px]">
                  {!isFinanceOrAdmin
                    ? "Submit expense receipts before month-end cutoff and verify your claim statuses."
                    : "Expense claim cutoff, batch payout releases, and low-stock replenishment review."}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-background border border-border/60 space-y-1">
                <span className="font-bold text-emerald-600 block">{!isFinanceOrAdmin ? "Equipment Care" : "Annual Checklist"}</span>
                <p className="text-muted-foreground text-[11px]">
                  {!isFinanceOrAdmin
                    ? "Keep assigned equipment updated and report any damaged assets promptly under My Assets."
                    : "Fiscal budget renewal, vendor compliance review, asset wall-to-wall audit & depreciation."}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

