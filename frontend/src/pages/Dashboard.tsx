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

  const cadence = data?.widgets?.financial_cadence || {};
  const monthlySpend = cadence.monthly_spend || 0;
  const yearlySpend = cadence.yearly_spend || 0;
  const totalExpenseSpend = safeExpenses.reduce((sum: number, e: any) => sum + (Number(e?.total_amount) || 0), 0);
  const lowStockAlerts = data?.widgets?.low_stock_alerts;

  const pendingApprovalsCount = isApprover 
    ? safeApprovals.filter((a: any) => {
        const amt = Number(a?.amount || a?.total_amount || a?.estimated_cost || 0);
        if (a?.entity_type === "ExpenseReport" || a?.entity_type === "PurchaseRequisition" || a?.entity_type === "VendorInvoice") {
          if (amt <= 0) return false;
        }
        return a?.status === "Pending" || a?.status === "Under Review" || a?.status?.toLowerCase().includes("pending");
      }).length
    : safeExpenses.filter((e: any) => (Number(e?.total_amount || 0) > 0) && e?.status?.includes("Pending")).length + 
      safePrs.filter((p: any) => (Number(p?.total_estimated_amount || p?.estimated_cost || 0) > 0) && (p?.status?.includes("Pending") || p?.status === "Submitted")).length;
  
  const assignedAssetsCount = safeMyAssetsList.length || (Array.isArray(data?.widgets?.my_assets) ? data.widgets.my_assets.length : 0);

  // Real-time recent lists
  const recentPRs = [...safePrs].sort((a: any, b: any) => {
    const isPendingA = (a.status?.toLowerCase().includes("pending") || a.status === "Submitted") && (Number(a.total_estimated_amount || a.estimated_cost || 0) > 0);
    const isPendingB = (b.status?.toLowerCase().includes("pending") || b.status === "Submitted") && (Number(b.total_estimated_amount || b.estimated_cost || 0) > 0);
    if (isPendingA && !isPendingB) return -1;
    if (!isPendingA && isPendingB) return 1;
    const timeA = new Date(a.created_at || 0).getTime();
    const timeB = new Date(b.created_at || 0).getTime();
    return timeB - timeA;
  }).slice(0, 5);

  const recentExpenseList = [...safeExpenses].sort((a: any, b: any) => {
    const isPendingA = (a.status?.toLowerCase().includes("pending") || a.status?.toLowerCase().includes("corrected")) && (Number(a.total_amount || 0) > 0);
    const isPendingB = (b.status?.toLowerCase().includes("pending") || b.status?.toLowerCase().includes("corrected")) && (Number(b.total_amount || 0) > 0);
    if (isPendingA && !isPendingB) return -1;
    if (!isPendingA && isPendingB) return 1;
    const timeA = new Date(a.created_at || a.submission_date || a.date || 0).getTime();
    const timeB = new Date(b.created_at || b.submission_date || b.date || 0).getTime();
    return timeB - timeA;
  }).slice(0, 5);

  // Chart data for 12 months rolling
  const monthsList = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const monthlyProcTrends = data?.widgets?.monthly_procurement || [];
  const chartData = {
    labels: monthsList,
    datasets: [
      {
        label: "Procurement Spend (₹)",
        data: monthsList.map((_, i) => {
          const mStr = `${new Date().getFullYear()}-${String(i + 1).padStart(2, "0")}`;
          const match = monthlyProcTrends.find((t: any) => t.month === mStr);
          return match ? match.spend : 0;
        }),
        backgroundColor: "rgba(59, 130, 246, 0.75)",
        borderRadius: 6,
      }
    ]
  };

  return (
    <div className="space-y-7 animate-fade-in">
      {/* Hero Header & Timeframe Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground">
              Good day, {user?.first_name || "Team Member"}
            </h1>
            <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping mr-0.5" /> Live Sync
            </span>
          </div>
          <p className="text-xs md:text-sm text-muted-foreground mt-1">
            Enterprise spend intelligence & approval pipeline updating in real time.
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

      {/* Apple Metrics Overview Bento Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Card 1: Differentiated Monthly vs. Yearly Spend */}
        <div
          onClick={() => navigate("/analytics")}
          title="Click to view full Spend Analytics"
          className="apple-card p-5 rounded-2xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-primary/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                {timeframe === "monthly" ? "Monthly Spend (MTD)" : timeframe === "yearly" ? "Yearly Spend (YTD)" : "Total Spend"}
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
                ₹{timeframe === "monthly"
                  ? (monthlySpend || totalExpenseSpend).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                  : timeframe === "yearly"
                  ? (yearlySpend || totalExpenseSpend).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                  : totalExpenseSpend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className="flex items-center gap-1.5 mt-1.5 text-[11px] font-semibold text-primary">
                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-primary/10">
                  {timeframe === "monthly" ? (cadence.current_month_name || "Current Month") : (cadence.current_fiscal_year || "Current FY")}
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
              {timeframe === "monthly" ? `Claims: ₹${cadence.reimbursements?.monthly_amount || 0} | POs: ₹${cadence.procurement?.monthly_amount || 0}` : `YTD Claims + Open POs`}
            </span>
            <span className="font-bold flex items-center">Analytics <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>

        {/* Card 2: Pending Approvals */}
        <div
          onClick={() => navigate(isApprover ? "/approvals" : "/expenses")}
          title="Click to review Pending Approvals & Claims"
          className="apple-card p-5 rounded-2xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-amber-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                {isApprover ? "Pending Approvals" : "Pending Claims"}
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
                  {pendingApprovalsCount > 0 ? "Action Required" : "All Caught Up"}
                </span>
                <span className="text-muted-foreground text-[10px]">in approval inbox</span>
              </div>
            </div>
          </div>
          <div className="mt-3.5 pt-2.5 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-amber-500 flex items-center justify-between transition-colors">
            <span>Awaiting verification & signoff</span>
            <span className="font-bold flex items-center">Open Queue <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>

        {/* Card 3: Annual Budget Utilization / Velocity */}
        <div
          onClick={() => navigate("/analytics")}
          title="Click to view Budget & Velocity telemetry"
          className="apple-card p-5 rounded-2xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-cyan-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                {isFinanceOrAdmin ? "Annual Budget Burn" : "Approval Velocity"}
              </span>
              <div className="flex items-center gap-1.5">
                <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-[#30B0C7] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                <div className="w-8 h-8 rounded-xl bg-[#30B0C7]/10 flex items-center justify-center text-[#30B0C7] group-hover:scale-110 transition-transform">
                  <TrendingUp className="w-4 h-4" />
                </div>
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-extrabold tracking-tight text-foreground group-hover:text-[#30B0C7] transition-colors">
                {isFinanceOrAdmin ? "42.8%" : "1.4 days"}
              </div>
              <div className="flex items-center gap-1.5 mt-1.5 text-[11px] font-semibold text-[#30B0C7]">
                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-[#30B0C7]/10">
                  {isFinanceOrAdmin ? "Within Healthy Cap" : "Fast Turnaround"}
                </span>
              </div>
            </div>
          </div>
          <div className="mt-3.5 pt-2.5 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-[#30B0C7] flex items-center justify-between transition-colors">
            <span>{isFinanceOrAdmin ? "Fiscal year envelope" : "Average signoff timeline"}</span>
            <span className="font-bold flex items-center">Budgets <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>

        {/* Card 4: Active Assets & Low Stock Pulse */}
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
          
          {/* Spend Trend Chart (Rolling 12 Months) */}
          {isFinanceOrAdmin && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-base">Procurement & Expense Trajectory ({new Date().getFullYear()})</CardTitle>
                  <p className="text-xs text-muted-foreground">Monthly expenditure run rate across all department cost centers.</p>
                </div>
                <Badge variant="neutral">Monthly Cadence</Badge>
              </CardHeader>
              <CardContent className="h-64">
                <Bar 
                  data={chartData} 
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                      y: { grid: { color: "rgba(150, 150, 150, 0.1)" } },
                      x: { grid: { display: false } }
                    }
                  }} 
                />
              </CardContent>
            </Card>
          )}

          {/* Recent Requisitions Table */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-6 h-6 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <FileText className="w-3.5 h-3.5" />
                </div>
                <CardTitle>Recent Requisitions</CardTitle>
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
                        <td colSpan={4} className="py-6 text-center text-muted-foreground">No active requisitions.</td>
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
                <CardTitle>Recent Expense Claims</CardTitle>
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
                <CardTitle>My Assets</CardTitle>
              </div>
              <Button size="sm" variant="ghost" onClick={() => navigate("/my-assets")} className="text-xs">
                Manage
              </Button>
            </CardHeader>
            <CardContent className="space-y-3.5">
              {safeMyAssetsList.length === 0 ? (
                <div className="py-8 text-center text-xs text-muted-foreground">No assets currently assigned.</div>
              ) : (
                safeMyAssetsList.map((asset: any, idx: number) => (
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
                <CardTitle className="text-sm">Periodic Governance</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="p-3 rounded-lg bg-background border border-border/60 space-y-1">
                <span className="font-bold text-primary block">Monthly Checklist</span>
                <p className="text-muted-foreground text-[11px]">
                  Expense claim cutoff, batch payout releases, and low-stock replenishment review.
                </p>
              </div>
              <div className="p-3 rounded-lg bg-background border border-border/60 space-y-1">
                <span className="font-bold text-emerald-600 block">Annual Checklist</span>
                <p className="text-muted-foreground text-[11px]">
                  Fiscal budget renewal, vendor compliance review, asset wall-to-wall audit & depreciation.
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

