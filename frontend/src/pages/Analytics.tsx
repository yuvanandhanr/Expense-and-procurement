import React, { useEffect, useState } from "react";
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
import { Activity, HardDrive, ShieldCheck, Server, AlertCircle } from "lucide-react";

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
  const [spendData, setSpendData] = useState<any>(null);
  const [vendorData, setVendorData] = useState<any>(null);
  const [budgetData, setBudgetData] = useState<any>(null);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const [spendRes, vendorRes, budgetRes, dashboardRes] = await Promise.all([
          api.get("/analytics/spend"),
          api.get("/analytics/vendors"),
          api.get("/analytics/budgets"),
          api.get("/dashboard"),
        ]);
        setSpendData(spendRes.data);
        setVendorData(vendorRes.data);
        setBudgetData(budgetRes.data);
        setDashboardData(dashboardRes.data);
      } catch (err) {
        console.error("Failed to load analytics trends:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
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
    // API returns month as "YYYY-MM"
    const match = spendData?.monthly_trends?.find((t: any) => parseInt(t.month.split("-")[1]) === i + 1);
    return match ? match.spend : 0;
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

  const deptLabels = spendData?.department_spend?.length ? spendData.department_spend.map((d: any) => d.department) : ["No Data"];
  const deptAmounts = spendData?.department_spend?.length ? spendData.department_spend.map((d: any) => d.spend) : [0];

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

  const isCFO = hasRole("CFO");
  const isCTO = hasRole("CTO");

  // --- CTO Operational Dashboard ---
  if (isCTO) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Operational / Technology Dashboard</h1>
          <p className="text-muted-foreground mt-1">System Health, API Performance, and Integration Volume.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-emerald-500/10 border-emerald-500/20">
            <CardContent className="p-4 flex flex-col gap-2">
              <div className="flex justify-between">
                <span className="text-xs font-bold text-emerald-700 uppercase">System Uptime</span>
                <Server className="w-5 h-5 text-emerald-600/50" />
              </div>
              <h3 className="text-2xl font-bold text-emerald-700">99.99%</h3>
            </CardContent>
          </Card>
          <Card className="bg-blue-500/10 border-blue-500/20">
            <CardContent className="p-4 flex flex-col gap-2">
              <div className="flex justify-between">
                <span className="text-xs font-bold text-blue-700 uppercase">API Health (Latency)</span>
                <Activity className="w-5 h-5 text-blue-600/50" />
              </div>
              <h3 className="text-2xl font-bold text-blue-700">42 ms</h3>
            </CardContent>
          </Card>
          <Card className="bg-amber-500/10 border-amber-500/20">
            <CardContent className="p-4 flex flex-col gap-2">
              <div className="flex justify-between">
                <span className="text-xs font-bold text-amber-700 uppercase">Integration Volume</span>
                <HardDrive className="w-5 h-5 text-amber-600/50" />
              </div>
              <h3 className="text-2xl font-bold text-amber-700">1.2M Req</h3>
            </CardContent>
          </Card>
          <Card className="bg-rose-500/10 border-rose-500/20">
            <CardContent className="p-4 flex flex-col gap-2">
              <div className="flex justify-between">
                <span className="text-xs font-bold text-rose-700 uppercase">Failed Jobs</span>
                <AlertCircle className="w-5 h-5 text-rose-600/50" />
              </div>
              <h3 className="text-2xl font-bold text-rose-700">3</h3>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
           <Card>
             <CardHeader><CardTitle>API Request Volume (24h)</CardTitle></CardHeader>
             <CardContent className="h-64 flex items-center justify-center bg-muted/20">
               {/* Mock Line Chart for API */}
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

  // --- CFO & Finance Manager Dashboard ---
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {isCFO ? "CFO Executive Dashboard" : "Financial Analytics"}
        </h1>
        <p className="text-xs text-muted-foreground mt-1">
          Historical spend trends, vendor score aggregations, and department budget performance.
        </p>
      </div>

      {isCFO && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-primary/10 border-primary/20">
             <CardContent className="p-6">
               <h3 className="text-sm font-bold text-primary uppercase tracking-wider mb-2">Total Budget Allocation</h3>
               <p className="text-4xl font-bold text-foreground">
                 ${(budgetData?.reduce((acc: number, b: any) => acc + (b.allocated || 0), 0) || 0).toLocaleString()}
               </p>
             </CardContent>
          </Card>
          <Card className="bg-amber-500/10 border-amber-500/20">
             <CardContent className="p-6">
               <h3 className="text-sm font-bold text-amber-700 uppercase tracking-wider mb-2">Pending Reimbursements</h3>
               <p className="text-4xl font-bold text-foreground">
                 ${(dashboardData?.widgets?.employee_reimbursements?.amount || 0).toLocaleString()}
               </p>
             </CardContent>
          </Card>
          <Card className="bg-emerald-500/10 border-emerald-500/20">
             <CardContent className="p-6">
               <h3 className="text-sm font-bold text-emerald-700 uppercase tracking-wider mb-2">Total Spend (YTD)</h3>
               <p className="text-4xl font-bold text-foreground">
                 ${(spendData?.yearly_trends?.reduce((acc: number, y: any) => acc + y.spend, 0) || 0).toLocaleString()}
               </p>
             </CardContent>
          </Card>
        </div>
      )}

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
                  <th className="p-4">PO Count</th>
                  <th className="p-4">Total Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {spendData?.vendor_spend?.length > 0 ? spendData.vendor_spend.map((v: any, idx: number) => (
                  <tr key={idx} className="hover:bg-accent/20">
                    <td className="p-4 font-bold">{v.vendor}</td>
                    <td className="p-4">-</td>
                    <td className="p-4 font-semibold">${v.spend?.toLocaleString()}</td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={3} className="p-4 text-center text-muted-foreground">No vendor spend data available.</td>
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
              <div className="text-center text-sm text-muted-foreground pt-4">No budget data available.</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
export default Analytics;
