import React, { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import { Card, CardHeader, CardTitle, CardContent, Skeleton, Badge, HeroTimestamp, EmptyState } from "../components/ui";
import { formatDate } from "../utils/helpers";
import {
  DollarSign,
  FileCheck,
  PackageCheck,
  TrendingDown,
  Percent,
  Clock,
  ClipboardList,
  CreditCard,
  Building,
  Activity,
} from "lucide-react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface DashboardData {
  role: string;
  timestamp: string;
  widgets: Record<string, any>;
}

export const Dashboard: React.FC = () => {
  const { user, hasRole } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await api.get("/dashboard");
        setData(response.data);
      } catch (err) {
        console.error("Failed to load dashboard metrics:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-6 w-32" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  // Fallback default widgets structure if API returns empty
  const role = data?.role || "Employee";
  const widgets = data?.widgets || {};

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Workspace Overview</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Tailored dashboard view for role: <Badge variant="info" className="ml-1">{role}</Badge>
          </p>
        </div>
        <HeroTimestamp staticDate={data?.timestamp} />
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {widgets.pending_approvals !== undefined && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Pending Approvals</span>
              <FileCheck className="w-4 h-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{widgets.pending_approvals || 0}</div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Awaiting sign-off
              </p>
            </CardContent>
          </Card>
        )}

        {widgets.department_spend && widgets.department_spend.length > 0 && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Dept Spend</span>
              <DollarSign className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${widgets.department_spend.reduce((acc: number, cur: any) => acc + (cur.spend || 0), 0).toLocaleString()}
              </div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Across {widgets.department_spend.length} Departments
              </p>
            </CardContent>
          </Card>
        )}

        {widgets.budget_utilization && widgets.budget_utilization.length > 0 && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Avg Budget Util</span>
              <Percent className="w-4 h-4 text-emerald-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(widgets.budget_utilization.reduce((acc: number, cur: any) => acc + (cur.percentage || 0), 0) / widgets.budget_utilization.length).toFixed(1)}%
              </div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Across active budgets
              </p>
            </CardContent>
          </Card>
        )}

        {widgets.vendor_performance && widgets.vendor_performance.length > 0 && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Avg Vendor Score</span>
              <Clock className="w-4 h-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(widgets.vendor_performance.reduce((acc: number, cur: any) => acc + (cur.score || 0), 0) / widgets.vendor_performance.length).toFixed(1)}/100
              </div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Performance rating
              </p>
            </CardContent>
          </Card>
        )}

        {widgets.my_purchase_requests && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">My Requisitions</span>
              <ClipboardList className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {Object.values(widgets.my_purchase_requests).reduce((acc: any, cur: any) => acc + cur, 0) as number}
              </div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Active requests
              </p>
            </CardContent>
          </Card>
        )}

        {widgets.employee_reimbursements && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Emp Reimbursements</span>
              <CreditCard className="w-4 h-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${widgets.employee_reimbursements.amount?.toLocaleString() || "0"}</div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Across {widgets.employee_reimbursements.count || 0} claims
              </p>
            </CardContent>
          </Card>
        )}

        {widgets.vendor_invoices && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Vendor Invoices</span>
              <Building className="w-4 h-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${widgets.vendor_invoices.amount?.toLocaleString() || "0"}</div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Across {widgets.vendor_invoices.count || 0} bills
              </p>
            </CardContent>
          </Card>
        )}

        {widgets.my_reimbursements && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Total Reimbursed</span>
              <FileCheck className="w-4 h-4 text-indigo-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${widgets.my_reimbursements.amount?.toLocaleString() || "0"}</div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                {widgets.my_reimbursements.count || 0} approved claims
              </p>
            </CardContent>
          </Card>
        )}

        {widgets.purchase_orders && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Total PO Spend</span>
              <DollarSign className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${Object.values(widgets.purchase_orders.amounts).reduce((a: any, b: any) => a + b, 0).toLocaleString()}
              </div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Across all orders
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Main Dashboard Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Charts & Feeds */}
        <div className="lg:col-span-2 space-y-6">
          
          {widgets.my_monthly_trend && widgets.my_monthly_trend.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>My Spending Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[250px] w-full">
                  <Bar
                    data={{
                      labels: widgets.my_monthly_trend.map((d: any) => d.month),
                      datasets: [
                        {
                          label: 'Reimbursed Amount ($)',
                          data: widgets.my_monthly_trend.map((d: any) => d.spend),
                          backgroundColor: 'rgba(99, 102, 241, 0.5)',
                          borderColor: 'rgba(99, 102, 241, 1)',
                          borderWidth: 1,
                        },
                      ],
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: { beginAtZero: true }
                      }
                    }}
                  />
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Recent Bounded Workflow Activity</CardTitle>
            </CardHeader>
            <CardContent>
              {widgets.recent_activities && widgets.recent_activities.length > 0 ? (
                <div className="flow-root">
                  <ul className="-mb-8">
                    {widgets.recent_activities.map((activity: any, idx: number) => (
                      <li key={idx}>
                        <div className="relative pb-8">
                          {idx !== widgets.recent_activities.length - 1 && (
                            <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-border" aria-hidden="true" />
                          )}
                          <div className="relative flex space-x-3">
                            <div>
                              <span className="h-8 w-8 rounded-full bg-accent border border-border flex items-center justify-center">
                                <span className="text-[10px] font-bold">{idx + 1}</span>
                              </span>
                            </div>
                            <div className="flex-1 min-w-0 pt-1.5 flex justify-between space-x-4">
                              <div>
                                <p className="text-xs font-semibold text-foreground/90">{activity.description}</p>
                              </div>
                              <div className="text-right text-[10px] font-bold text-muted-foreground uppercase tracking-wider whitespace-nowrap">
                                {formatDate(activity.timestamp)}
                              </div>
                            </div>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <EmptyState
                  icon={<Activity className="w-8 h-8" />}
                  title="No recent activity recorded."
                  description="Your workflow events will appear here once you participate in the cycle."
                  actionLabel="Start a new request"
                  actionHref="/prs"
                />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Actions Quick Links */}
        <Card>
          <CardHeader>
            <CardTitle>Enterprise Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!hasRole("Vendor Portal") && !hasRole("Vendor") && (
              <a
                href="/prs"
                className="flex items-center justify-between p-3 rounded-lg border border-border bg-card hover:-translate-y-[1px] hover:border-violet/50 hover:shadow-sm transition-all group"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-md bg-violet/10 text-violet flex items-center justify-center">
                    <ClipboardList className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="block font-bold text-sm text-foreground group-hover:text-violet transition-colors">Submit Purchase Requisition</span>
                    <span className="block text-[10px] text-muted-foreground font-medium mt-0.5">Start a new department request</span>
                  </div>
                </div>
                <span className="text-muted-foreground group-hover:text-violet transition-colors">&rarr;</span>
              </a>
            )}
            {(hasRole("Finance") || hasRole("CFO") || hasRole("CEO") || hasRole("Admin")) && (
              <a
                href="/reports"
                className="flex items-center justify-between p-3 rounded-lg border border-border bg-card hover:-translate-y-[1px] hover:border-cyan/50 hover:shadow-sm transition-all group"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-md bg-cyan/10 text-cyan flex items-center justify-center">
                    <FileCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="block font-bold text-sm text-foreground group-hover:text-cyan transition-colors">Export Spend Reports</span>
                    <span className="block text-[10px] text-muted-foreground font-medium mt-0.5">Download financial data</span>
                  </div>
                </div>
                <span className="text-muted-foreground group-hover:text-cyan transition-colors">&rarr;</span>
              </a>
            )}
            <a
              href="/search"
              className="flex items-center justify-between p-3 rounded-lg border border-border bg-card hover:-translate-y-[1px] hover:border-lime/50 hover:shadow-sm transition-all group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-md bg-lime/10 text-lime flex items-center justify-center">
                  <PackageCheck className="w-4 h-4" />
                </div>
                <div>
                  <span className="block font-bold text-sm text-foreground group-hover:text-lime transition-colors">Global Audit Search</span>
                  <span className="block text-[10px] text-muted-foreground font-medium mt-0.5">Find any record instantly</span>
                </div>
              </div>
              <span className="text-muted-foreground group-hover:text-lime transition-colors">&rarr;</span>
            </a>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
export default Dashboard;
