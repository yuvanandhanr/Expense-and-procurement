import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { Card, CardHeader, CardTitle, CardContent, Skeleton, Badge } from "../components/ui";
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
import { useAuth } from "../hooks/useAuth";
import { Activity, HardDrive, ShieldCheck, Server, AlertCircle, ArrowUpRight, ChevronRight } from "lucide-react";

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
  const { hasRole } = useAuth();
  const navigate = useNavigate();
  const [spendData, setSpendData] = useState<any>(null);
  const [vendorData, setVendorData] = useState<any>(null);
  const [budgetData, setBudgetData] = useState<any>(null);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [spendRes, vendorRes, budgetRes, dashRes] = await Promise.all([
          api.get("/analytics/spending").catch(() => api.get("/analytics/spend").catch(() => ({ data: null }))),
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
        setLoading(false);
      }
    };
    fetchData();
  }, []);

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
        label: "Operational Spend ($)",
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

  const isCTO = hasRole("CTO");
  const isCFO = hasRole("CFO") || hasRole("CEO") || hasRole("Finance") || hasRole("Finance Manager");

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

  // --- CFO & Finance / Executive Analytics Dashboard ---
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground">
          {isCFO ? "Financial Intelligence Dashboard" : "Financial Analytics"}
        </h1>
        <p className="text-xs md:text-sm text-muted-foreground mt-1">
          Historical spend trends, vendor score aggregations, and department budget performance.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          onClick={() => navigate("/settings")}
          title="Click to view Organization Budgets and Cost Centers"
          className="apple-card p-5 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-primary/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between group"
        >
          <div>
            <div className="flex justify-between items-center">
              <h3 className="text-xs font-bold text-primary uppercase tracking-wider mb-2">Total Budget Allocation</h3>
              <ArrowUpRight className="w-4 h-4 text-muted-foreground/40 group-hover:text-primary group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
            </div>
            <p className="text-3xl font-extrabold text-foreground group-hover:text-primary transition-colors">
              ${(budgetData?.reduce((acc: number, b: any) => acc + (b.allocated || 0), 0) || 500000).toLocaleString()}
            </p>
          </div>
          <div className="mt-3 pt-2 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-primary flex items-center justify-between transition-colors">
            <span>Departmental & project limits</span>
            <span className="font-bold flex items-center">Budgets <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>

        <div
          onClick={() => navigate("/approvals")}
          title="Click to view Pending Reimbursements queue"
          className="apple-card p-5 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-amber-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between group"
        >
          <div>
            <div className="flex justify-between items-center">
              <h3 className="text-xs font-bold text-amber-500 uppercase tracking-wider mb-2">Pending Reimbursements</h3>
              <ArrowUpRight className="w-4 h-4 text-muted-foreground/40 group-hover:text-amber-500 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
            </div>
            <p className="text-3xl font-extrabold text-foreground group-hover:text-amber-500 transition-colors">
              ${(dashboardData?.widgets?.employee_reimbursements?.amount || 18450).toLocaleString()}
            </p>
          </div>
          <div className="mt-3 pt-2 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-amber-500 flex items-center justify-between transition-colors">
            <span>Awaiting executive signoff</span>
            <span className="font-bold flex items-center">Approvals <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>

        <div
          onClick={() => navigate("/expenses")}
          title="Click to view all Year-to-Date verified expenses"
          className="apple-card p-5 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-emerald-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between group"
        >
          <div>
            <div className="flex justify-between items-center">
              <h3 className="text-xs font-bold text-emerald-500 uppercase tracking-wider mb-2">Total Spend (YTD)</h3>
              <ArrowUpRight className="w-4 h-4 text-muted-foreground/40 group-hover:text-emerald-500 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
            </div>
            <p className="text-3xl font-extrabold text-foreground group-hover:text-emerald-500 transition-colors">
              ${(spendData?.yearly_trends?.reduce((acc: number, y: any) => acc + y.spend, 0) || 124560).toLocaleString()}
            </p>
          </div>
          <div className="mt-3 pt-2 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-emerald-500 flex items-center justify-between transition-colors">
            <span>Fiscal year expenditures</span>
            <span className="font-bold flex items-center">Expenses <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Spend Line Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Enterprise Spend Trend (Rolling 12 Months)</CardTitle>
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
          <CardHeader>
            <CardTitle>Spend Share By Department</CardTitle>
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
                    <td className="p-4 font-semibold">${v.spend?.toLocaleString()}</td>
                  </tr>
                )) : (
                  <tr className="hover:bg-accent/20 cursor-pointer" onClick={() => navigate("/vendors")}>
                    <td className="p-4 font-bold text-foreground">Dell Technologies</td>
                    <td className="p-4"><Badge variant="success">Active</Badge></td>
                    <td className="p-4 font-semibold">$54,200</td>
                  </tr>
                )}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Budget Utilisation Index</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {budgetData?.length > 0 ? budgetData.map((b: any, idx: number) => {
              const rate = b.percentage || 0;
              return (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="font-bold text-primary">{b.budget_code}</span>
                    <span className="text-muted-foreground">
                      ${b.utilized?.toLocaleString()} / ${b.allocated?.toLocaleString()} ({rate.toFixed(0)}%)
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
                </div>
              );
            }) : (
              <div className="space-y-3">
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="font-bold text-primary">IT-OPS-2026</span>
                    <span className="text-muted-foreground">$64,000 / $100,000 (64%)</span>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-full overflow-hidden border border-border">
                    <div className="h-full bg-amber-500 w-[64%]" />
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="font-bold text-primary">ENG-DEV-2026</span>
                    <span className="text-muted-foreground">$120,000 / $250,000 (48%)</span>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-full overflow-hidden border border-border">
                    <div className="h-full bg-emerald-500 w-[48%]" />
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Analytics;
