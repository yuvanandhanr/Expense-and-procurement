import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { Card, CardHeader, CardTitle, CardContent, Skeleton } from "../components/ui";
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
  const [spendData, setSpendData] = useState<any>(null);
  const [vendorData, setVendorData] = useState<any>(null);
  const [budgetData, setBudgetData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const [spendRes, vendorRes, budgetRes] = await Promise.all([
          api.get("/analytics/spend"),
          api.get("/analytics/vendors"),
          api.get("/analytics/budgets"),
        ]);
        setSpendData(spendRes.data);
        setVendorData(vendorRes.data);
        setBudgetData(budgetRes.data);
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

  // Formatting Line chart for monthly spend trends
  const lineChartData = {
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    datasets: [
      {
        label: "Operational Spend ($)",
        data: spendData?.monthly_trend || [12000, 19000, 3000, 5000, 2000, 3000, 20000, 14000, 9000, 12000, 25000, 18000],
        borderColor: "rgba(59, 130, 246, 1)",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        tension: 0.4,
        fill: true,
      },
    ],
  };

  // Formatting Doughnut chart for department distribution
  const doughnutChartData = {
    labels: spendData?.departments?.map((d: any) => d.name) || ["Engineering", "Sales", "HR", "Marketing", "Legal"],
    datasets: [
      {
        label: "Spend Share",
        data: spendData?.departments?.map((d: any) => d.total) || [45000, 25000, 10000, 15000, 8000],
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Business Intelligence & Analytics</h1>
        <p className="text-xs text-muted-foreground mt-1">
          Historical spend trends, vendor score aggregations, and department budget performance.
        </p>
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
                  legend: {
                    position: "bottom",
                  },
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
                  legend: {
                    position: "bottom",
                  },
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
                {(vendorData?.top_vendors || [
                  { name: "Acme Corp", pos: 12, total: 85000 },
                  { name: "Global Logistics", pos: 8, total: 42000 },
                  { name: "Apex Technologies", pos: 5, total: 31000 },
                ]).map((v: any, idx: number) => (
                  <tr key={idx} className="hover:bg-accent/20">
                    <td className="p-4 font-bold">{v.name}</td>
                    <td className="p-4">{v.pos}</td>
                    <td className="p-4 font-semibold">${v.total?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Budget Utilisation Index</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {(budgetData?.allocations || [
              { code: "DEPT-ENG-2026", spent: 45000, limit: 100000 },
              { code: "DEPT-SLS-2026", spent: 25000, limit: 50000 },
              { code: "DEPT-MKT-2026", spent: 15000, limit: 20000 },
            ]).map((b: any, idx: number) => {
              const rate = (b.spent / b.limit) * 100;
              return (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="font-bold text-primary">{b.code}</span>
                    <span className="text-muted-foreground">
                      ${b.spent?.toLocaleString()} / ${b.limit?.toLocaleString()} ({rate.toFixed(0)}%)
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
            })}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
export default Analytics;
