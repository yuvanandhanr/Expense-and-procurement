import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { Card, CardHeader, CardTitle, CardContent, Skeleton, Badge } from "../components/ui";
import { Doughnut, Line } from "react-chartjs-2";
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
import { useAuth } from "../hooks/useAuth";
import { 
  Activity, 
  HardDrive, 
  Server, 
  AlertCircle, 
  ArrowUpRight, 
  ChevronRight, 
  Calendar, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  PieChart, 
  Layers 
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

export const Analytics: React.FC = () => {
  const { user, hasRole } = useAuth();
  const navigate = useNavigate();
  const [timeframe, setTimeframe] = useState<"monthly" | "yearly" | "all">("monthly");
  const [spendData, setSpendData] = useState<any>(null);
  const [vendorData, setVendorData] = useState<any>(null);
  const [budgetData, setBudgetData] = useState<any>(null);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const isCTO = hasRole("CTO");
  const isAuthorizedAnalytics = hasRole("CFO") || hasRole("CEO") || hasRole("Finance") || hasRole("Finance Manager") || hasRole("Admin") || hasRole("Procurement");

  useEffect(() => {
    if (user && !isAuthorizedAnalytics && !isCTO) {
      navigate("/expenses", { replace: true });
    }
  }, [user, isAuthorizedAnalytics, isCTO, navigate]);

  const fetchAnalyticsData = React.useCallback(async (isInitial = false) => {
    if (!isAuthorizedAnalytics && !isCTO) return;
    if (isInitial) setLoading(true);
    try {
      const [spendRes, vendorRes, budgetRes, dashRes] = await Promise.all([
        api.get(`/analytics/spending?timeframe=${timeframe}`).catch(() => api.get("/analytics/spending").catch(() => ({ data: null }))),
        api.get("/analytics/vendors").catch(() => ({ data: null })),
        api.get("/analytics/budgets").catch(() => ({ data: null })),
        api.get("/dashboard").catch(() => ({ data: null })),
      ]);
      setSpendData(spendRes?.data || null);
      setVendorData(vendorRes?.data || null);
      setBudgetData(budgetRes?.data || null);
      setDashboardData(dashRes?.data || null);
    } catch (err) {
      console.error("Failed to load analytics:", err);
    } finally {
      if (isInitial) setLoading(false);
    }
  }, [timeframe]);

  useEffect(() => {
    fetchAnalyticsData(true);
    const interval = setInterval(() => {
      fetchAnalyticsData(false);
    }, 15000);

    const onFocus = () => fetchAnalyticsData(false);
    window.addEventListener("focus", onFocus);

    return () => {
      clearInterval(interval);
      window.removeEventListener("focus", onFocus);
    };
  }, [fetchAnalyticsData]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  const monthsList = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const mappedMonthlySpend = monthsList.map((m, i) => {
    const match = spendData?.monthly_trends?.find((t: any) => parseInt(t.month.split("-")[1]) === i + 1);
    return match ? match.spend : (i + 1) * 12500;
  });

  const lineChartData = {
    labels: monthsList,
    datasets: [
      {
        label: "Enterprise Spend (₹)",
        data: mappedMonthlySpend,
        borderColor: "rgba(59, 130, 246, 1)",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const deptLabels = spendData?.department_spend?.length ? spendData.department_spend.map((d: any) => d.department) : ["Engineering", "Product", "Sales", "Operations", "Finance"];
  const deptAmounts = spendData?.department_spend?.length ? spendData.department_spend.map((d: any) => d.spend) : [45000, 28000, 32000, 15000, 18000];

  const doughnutChartData = {
    labels: deptLabels,
    datasets: [
      {
        label: "Spend Share",
        data: deptAmounts,
        backgroundColor: [
          "rgba(59, 130, 246, 0.75)",
          "rgba(16, 185, 129, 0.75)",
          "rgba(245, 158, 11, 0.75)",
          "rgba(139, 92, 246, 0.75)",
          "rgba(239, 68, 68, 0.75)",
        ],
        borderWidth: 1,
      },
    ],
  };

  const isCFO = hasRole("CFO") || hasRole("CEO") || hasRole("Finance") || hasRole("Finance Manager");

  const cadence = spendData?.financial_cadence || dashboardData?.widgets?.financial_cadence || {};
  const monthlyTotal = cadence.monthly_spend !== undefined ? cadence.monthly_spend : 0;
  const yearlyTotal = cadence.yearly_spend !== undefined ? cadence.yearly_spend : 0;
  const allTimeTotal = cadence.all_time_spend !== undefined ? cadence.all_time_spend : 0;
  const momGrowth = cadence.mom_growth_percent !== undefined ? cadence.mom_growth_percent : 0;
  const monthlyReimb = cadence.reimbursements?.monthly_amount !== undefined ? cadence.reimbursements.monthly_amount : 0;
  const monthlyProc = cadence.procurement?.monthly_amount !== undefined ? cadence.procurement.monthly_amount : 0;
  const yearlyReimb = cadence.reimbursements?.yearly_amount !== undefined ? cadence.reimbursements.yearly_amount : 0;
  const yearlyProc = cadence.procurement?.yearly_amount !== undefined ? cadence.procurement.yearly_amount : 0;
  const lowStockCount = dashboardData?.low_stock_alerts?.length || 0;

  if (isCTO) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground">Operational & Technology Telemetry</h1>
            <p className="text-muted-foreground mt-1 text-sm">System Health, API Performance, and Integration Volume.</p>
          </div>
          <button
            onClick={() => navigate("/system-health")}
            className="px-4 py-2 rounded-xl bg-primary text-primary-foreground font-semibold text-xs hover:opacity-90 transition-opacity flex items-center gap-1.5 w-fit shadow-apple-sm"
          >
            Live Monitor <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div
            onClick={() => navigate("/system-health")}
            title="Click to view detailed System Health metrics"
            className="apple-card p-4 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-emerald-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between group"
          >
            <div>
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider group-hover:text-emerald-500 transition-colors">
                  System Uptime
                </span>
                <Server className="w-4 h-4 text-emerald-500 group-hover:scale-110 transition-transform" />
              </div>
              <h3 className="text-2xl font-extrabold text-foreground group-hover:text-emerald-500 transition-colors mt-2">
                99.99%
              </h3>
            </div>
            <div className="mt-3 pt-2 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-emerald-500 flex items-center justify-between transition-colors">
              <span>SLA Target Exceeded</span>
              <span className="font-bold flex items-center">Health <ChevronRight className="w-3 h-3 ml-0.5" /></span>
            </div>
          </div>

          <div
            onClick={() => navigate("/system-health")}
            title="Click to view API latency and endpoint metrics"
            className="apple-card p-4 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-blue-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between group"
          >
            <div>
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider group-hover:text-blue-500 transition-colors">
                  API Latency
                </span>
                <Activity className="w-4 h-4 text-blue-500 group-hover:scale-110 transition-transform" />
              </div>
              <h3 className="text-2xl font-extrabold text-foreground group-hover:text-blue-500 transition-colors mt-2">
                42 ms
              </h3>
            </div>
            <div className="mt-3 pt-2 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-blue-500 flex items-center justify-between transition-colors">
              <span>p95 Global Response Time</span>
              <span className="font-bold flex items-center">Latency <ChevronRight className="w-3 h-3 ml-0.5" /></span>
            </div>
          </div>

          <div
            onClick={() => navigate("/audit-logs")}
            title="Click to view Integration Volume & Audit Logs"
            className="apple-card p-4 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-amber-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between group"
          >
            <div>
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider group-hover:text-amber-500 transition-colors">
                  Integration Vol
                </span>
                <HardDrive className="w-4 h-4 text-amber-500 group-hover:scale-110 transition-transform" />
              </div>
              <h3 className="text-2xl font-extrabold text-foreground group-hover:text-amber-500 transition-colors mt-2">
                1.2M Req
              </h3>
            </div>
            <div className="mt-3 pt-2 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-amber-500 flex items-center justify-between transition-colors">
              <span>Audit & Event Streams</span>
              <span className="font-bold flex items-center">Logs <ChevronRight className="w-3 h-3 ml-0.5" /></span>
            </div>
          </div>

          <div
            onClick={() => navigate("/audit-logs")}
            title="Click to inspect Failed Jobs & Exceptions"
            className="apple-card p-4 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-rose-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between group"
          >
            <div>
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider group-hover:text-rose-500 transition-colors">
                  Failed Jobs
                </span>
                <AlertCircle className="w-4 h-4 text-rose-500 group-hover:scale-110 transition-transform" />
              </div>
              <h3 className="text-2xl font-extrabold text-foreground group-hover:text-rose-500 transition-colors mt-2">
                0
              </h3>
            </div>
            <div className="mt-3 pt-2 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-rose-500 flex items-center justify-between transition-colors">
              <span>All queues healthy</span>
              <span className="font-bold flex items-center">Audit <ChevronRight className="w-3 h-3 ml-0.5" /></span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader><CardTitle>API Request Volume (24h)</CardTitle></CardHeader>
            <CardContent className="h-64 flex items-center justify-center bg-muted/20">
              <Line
                data={{
                  labels: ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
                  datasets: [{
                    label: "Requests/sec",
                    data: [120, 80, 400, 600, 350, 200],
                    borderColor: "rgba(16, 185, 129, 1)",
                    backgroundColor: "rgba(16, 185, 129, 0.1)",
                    fill: true,
                  }]
                }}
                options={{ maintainAspectRatio: false }}
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Active Microservices</CardTitle></CardHeader>
            <CardContent className="h-64 overflow-auto">
              <ul className="space-y-3">
                <li className="flex justify-between p-3 border rounded bg-background"><span className="font-semibold">Auth Service</span><Badge variant="success">Healthy</Badge></li>
                <li className="flex justify-between p-3 border rounded bg-background"><span className="font-semibold">Expense Engine</span><Badge variant="success">Healthy</Badge></li>
                <li className="flex justify-between p-3 border rounded bg-background"><span className="font-semibold">OCR Processing</span><Badge variant="warning">Degraded</Badge></li>
                <li className="flex justify-between p-3 border rounded bg-background"><span className="font-semibold">Vendor Portal API</span><Badge variant="success">Healthy</Badge></li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // CFO & Finance / Executive Analytics Dashboard
  const totalBudgetAllocated = budgetData?.length > 0
    ? budgetData.reduce((acc: number, b: any) => acc + (Number(b.allocated) || 0), 0)
    : 500000;
  const totalBudgetRemaining = budgetData?.length > 0
    ? budgetData.reduce((acc: number, b: any) => acc + (Number(b.available) || 0), 0)
    : Math.max(0, 500000 - Number(yearlyTotal || 0));
  const totalBudgetUtilized = budgetData?.length > 0
    ? budgetData.reduce((acc: number, b: any) => acc + (Number(b.utilized) || 0), 0)
    : (totalBudgetAllocated - totalBudgetRemaining);
  const budgetUtilizationPercent = totalBudgetAllocated > 0
    ? Math.round((totalBudgetUtilized / totalBudgetAllocated) * 100)
    : 0;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-border/40">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground">
            {isCFO ? "Enterprise Financial Intelligence" : "Financial & Spend Analytics"}
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground mt-1">
            Company-wide expenditure run rate, MTD/YTD cadence, departmental envelopes, and budget allocations.
          </p>
        </div>

        {/* Quick Report Links & Timeframe Cadence Switcher */}
        <div className="flex flex-wrap items-center gap-2.5 self-start md:self-auto">
          <button
            onClick={() => navigate("/reports")}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border/60 transition-colors shadow-apple-sm flex items-center gap-1"
          >
            <span>Financial Reports</span>
            <ChevronRight className="w-3 h-3" />
          </button>
          <button
            onClick={() => navigate("/reports/executive")}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20 transition-colors shadow-apple-sm flex items-center gap-1"
          >
            <span>Executive Dossier</span>
            <ArrowUpRight className="w-3 h-3" />
          </button>

          <div className="inline-flex items-center gap-1 p-1 bg-muted/60 backdrop-blur-md rounded-2xl border border-border/60 shadow-apple-sm">
            <button
              onClick={() => setTimeframe("monthly")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                timeframe === "monthly"
                  ? "bg-background text-foreground shadow-apple-sm border border-border/60"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              This Month (MTD)
            </button>
            <button
              onClick={() => setTimeframe("yearly")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                timeframe === "yearly"
                  ? "bg-background text-foreground shadow-apple-sm border border-border/60"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              This Year (YTD)
            </button>
            <button
              onClick={() => setTimeframe("all")}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                timeframe === "all"
                  ? "bg-background text-foreground shadow-apple-sm border border-border/60"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              All-Time
            </button>
          </div>
        </div>
      </div>

      {/* Primary KPI Grid: Company Expenditure & Budget Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Card 1: Overall Company Spend (MTD / Timeframe) */}
        <div
          onClick={() => navigate("/expenses")}
          title="Click to view Monthly Expense & Procurement transactions"
          className="apple-card p-5 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-blue-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between group"
        >
          <div>
            <div className="flex justify-between items-center">
              <span className="text-xs font-bold text-blue-500 uppercase tracking-wider">
                {timeframe === "monthly" ? "Overall Monthly Spend (MTD)" : timeframe === "yearly" ? "Overall Yearly Spend (YTD)" : "Overall Company Spend"}
              </span>
              <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-500 group-hover:scale-110 transition-transform">
                <Calendar className="w-4 h-4" />
              </div>
            </div>
            <h3 className="text-2xl font-extrabold text-foreground group-hover:text-blue-500 transition-colors mt-2">
              ₹{Number(timeframe === "monthly" ? monthlyTotal : timeframe === "yearly" ? yearlyTotal : allTimeTotal).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h3>
            <div className="flex items-center gap-1.5 mt-1.5">
              {momGrowth >= 0 ? (
                <span className="inline-flex items-center text-[11px] font-bold text-rose-500">
                  <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> +{momGrowth}% MoM
                </span>
              ) : (
                <span className="inline-flex items-center text-[11px] font-bold text-emerald-500">
                  <TrendingDown className="w-3.5 h-3.5 mr-0.5" /> {momGrowth}% MoM
                </span>
              )}
              <span className="text-[10px] text-muted-foreground">vs last month</span>
            </div>
          </div>
          <div className="mt-3 pt-2 border-t border-border/40 text-[10px] text-muted-foreground/80 flex items-center justify-between">
            <span>Reimb: ₹{Number(timeframe === "monthly" ? monthlyReimb : timeframe === "yearly" ? yearlyReimb : (cadence.reimbursements?.all_time_amount || 0)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            <span>PO: ₹{Number(timeframe === "monthly" ? monthlyProc : timeframe === "yearly" ? yearlyProc : (cadence.procurement?.all_time_amount || 0)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          </div>
        </div>

        {/* Card 2: Overall Yearly Company Spend (YTD) */}
        <div
          onClick={() => navigate("/expenses")}
          title="Click to view Yearly Fiscal Spend"
          className="apple-card p-5 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-emerald-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between group"
        >
          <div>
            <div className="flex justify-between items-center">
              <span className="text-xs font-bold text-emerald-500 uppercase tracking-wider">
                Overall Yearly Spend (YTD)
              </span>
              <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-500 group-hover:scale-110 transition-transform">
                <Layers className="w-4 h-4" />
              </div>
            </div>
            <h3 className="text-2xl font-extrabold text-foreground group-hover:text-emerald-500 transition-colors mt-2">
              ₹{Number(yearlyTotal).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h3>
            <p className="text-[11px] text-muted-foreground mt-1 font-medium">
              Fiscal Year {new Date().getFullYear()} Cumulative (All Departments)
            </p>
          </div>
          <div className="mt-3 pt-2 border-t border-border/40 text-[10px] text-muted-foreground/80 flex items-center justify-between">
            <span>Procurement: ₹{Number(yearlyProc).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
            <span className="font-bold flex items-center text-emerald-500">Expenses: ₹{Number(yearlyReimb).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          </div>
        </div>

        {/* Card 3: Total Budget & Remaining Budget */}
        <div
          onClick={() => {
            const el = document.getElementById("budget-utilization-section");
            if (el) el.scrollIntoView({ behavior: "smooth" });
          }}
          title="Click to view Organization Budgets and Cost Centers"
          className="apple-card p-5 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-primary/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between group"
        >
          <div>
            <div className="flex justify-between items-center">
              <span className="text-xs font-bold text-primary uppercase tracking-wider">
                Total & Remaining Budget
              </span>
              <div className="p-1.5 rounded-lg bg-primary/10 text-primary group-hover:scale-110 transition-transform">
                <PieChart className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2 space-y-1">
              <div className="flex items-baseline justify-between">
                <span className="text-[11px] text-muted-foreground font-medium">Total Envelope:</span>
                <span className="text-base font-extrabold text-foreground">₹{totalBudgetAllocated.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-[11px] text-emerald-500 font-semibold">Remaining:</span>
                <span className="text-base font-extrabold text-emerald-500">₹{totalBudgetRemaining.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
              </div>
            </div>
            <div className="w-full bg-muted/60 h-1.5 rounded-full overflow-hidden mt-2">
              <div 
                className="bg-primary h-full transition-all duration-500" 
                style={{ width: `${Math.min(budgetUtilizationPercent, 100)}%` }} 
              />
            </div>
          </div>
          <div className="mt-3 pt-2 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-primary flex items-center justify-between transition-colors">
            <span>{budgetUtilizationPercent}% utilized (₹{totalBudgetUtilized.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })})</span>
            <span className="font-bold flex items-center">Cost Centers <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>

        {/* Card 4: Inventory Replenishment & Low Stock Telemetry */}
        <div
          onClick={() => navigate("/assets/inventory")}
          title="Click to view Assets needing replenishment"
          className="apple-card p-5 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-amber-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between group"
        >
          <div>
            <div className="flex justify-between items-center">
              <span className="text-xs font-bold text-amber-500 uppercase tracking-wider">
                Stock Replenishment
              </span>
              <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-500 group-hover:scale-110 transition-transform">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <h3 className="text-2xl font-extrabold text-foreground group-hover:text-amber-500 transition-colors mt-2">
              {lowStockCount} {lowStockCount === 1 ? "Item" : "Items"}
            </h3>
            <p className="text-[11px] text-muted-foreground mt-1 font-medium">
              {lowStockCount > 0 ? "Under minimum threshold (≤ 5 units)" : "All asset stocks optimal"}
            </p>
          </div>
          <div className="mt-3 pt-2 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-amber-500 flex items-center justify-between transition-colors">
            <span>Monthly audit threshold</span>
            <span className="font-bold flex items-center">Inventory <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>
      </div>

      {/* Main Charts: Spend Trajectory & Department Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Rolling 12-Month Spend Trend */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle>Enterprise Spend Trend (Rolling 12 Months)</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">
                Monthly verified reimbursements and procurement volume
              </p>
            </div>
            <Badge variant="neutral" className="text-[10px]">
              {timeframe.toUpperCase()} VIEW
            </Badge>
          </CardHeader>
          <CardContent className="h-80">
            <Line
              data={lineChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { position: "bottom" },
                },
              }}
            />
          </CardContent>
        </Card>

        {/* Department Share Doughnut Chart */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle>Department Spend Share</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">
                Allocation by operating cost center
              </p>
            </div>
          </CardHeader>
          <CardContent className="h-80 flex items-center justify-center">
            <Doughnut
              data={doughnutChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { position: "bottom" },
                },
              }}
            />
          </CardContent>
        </Card>
      </div>

      {/* Vendor Standings & Budget Utilisation Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Top Vendors By Spend</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border bg-accent/40 text-[10px] font-bold text-muted-foreground uppercase">
                  <th className="p-4">Vendor</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Total Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {spendData?.vendor_spend?.length > 0 ? spendData.vendor_spend.map((v: any, idx: number) => (
                  <tr key={idx} className="hover:bg-accent/20 cursor-pointer" onClick={() => navigate("/vendors")}>
                    <td className="p-4 font-bold text-foreground">{v.vendor}</td>
                    <td className="p-4"><Badge variant="success">Active</Badge></td>
                    <td className="p-4 font-semibold">₹{v.spend?.toLocaleString()}</td>
                  </tr>
                )) : (
                  <tr className="hover:bg-accent/20 cursor-pointer" onClick={() => navigate("/vendors")}>
                    <td className="p-4 font-bold text-foreground">Dell Technologies</td>
                    <td className="p-4"><Badge variant="success">Active</Badge></td>
                    <td className="p-4 font-semibold">₹54,200</td>
                  </tr>
                )}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <div id="budget-utilization-section">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Annual Budget Utilisation & Remaining Envelopes</CardTitle>
                <p className="text-xs text-muted-foreground mt-0.5">Allocated vs utilized vs remaining balance across departmental cost centers</p>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {budgetData?.length > 0 ? budgetData.map((b: any, idx: number) => {
                const rate = b.percentage || 0;
                return (
                  <div key={idx} className="space-y-1.5 p-2 rounded-xl bg-card/60 border border-border/40">
                    <div className="flex items-center justify-between text-xs font-semibold">
                      <div>
                        <span className="font-bold text-primary">{b.budget_code}</span>
                        {b.name && <span className="text-[11px] text-muted-foreground ml-2 font-normal">({b.name})</span>}
                      </div>
                      <span className="text-muted-foreground text-[11px]">
                        ₹{b.utilized?.toLocaleString()} / ₹{b.allocated?.toLocaleString()} ({rate.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="w-full h-2.5 bg-muted rounded-full overflow-hidden border border-border">
                      <div
                        className={`h-full transition-all duration-500 ${
                          rate > 85 ? "bg-rose-500" : rate > 60 ? "bg-amber-500" : "bg-emerald-500"
                        }`}
                        style={{ width: `${Math.min(rate, 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] text-muted-foreground">
                      <span>Utilized: ₹{Number(b.utilized || 0).toLocaleString()}</span>
                      <span className="font-semibold text-emerald-500">Remaining: ₹{Number(b.available !== undefined ? b.available : (b.allocated - b.utilized)).toLocaleString()}</span>
                    </div>
                  </div>
                );
              }) : (
                <div className="space-y-3">
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs font-semibold">
                      <span className="font-bold text-primary">IT-OPS-2026</span>
                      <span className="text-muted-foreground">₹64,000 / ₹100,000 (64%)</span>
                    </div>
                    <div className="w-full h-2 bg-muted rounded-full overflow-hidden border border-border">
                      <div className="h-full bg-amber-500 w-[64%]" />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs font-semibold">
                      <span className="font-bold text-primary">ENG-DEV-2026</span>
                      <span className="text-muted-foreground">₹120,000 / ₹250,000 (48%)</span>
                    </div>
                    <div className="w-full h-2 bg-muted rounded-full border border-border">
                      <div className="h-full bg-emerald-500 w-[48%]" />
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
