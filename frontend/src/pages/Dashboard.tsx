import React, { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import { Card, CardHeader, CardTitle, CardContent, Skeleton, Badge } from "../components/ui";
import {
  DollarSign,
  FileCheck,
  PackageCheck,
  TrendingDown,
  Percent,
  Clock,
  ClipboardList,
} from "lucide-react";

interface DashboardData {
  role: string;
  timestamp: string;
  widgets: Record<string, any>;
}

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
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
        <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">
          As of {data?.timestamp ? new Date(data.timestamp).toLocaleString() : new Date().toLocaleString()}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {widgets.spend_metrics && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Total Year Spend</span>
              <DollarSign className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${widgets.spend_metrics.total_spend?.toLocaleString() || "0"}</div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Across {widgets.spend_metrics.po_count || 0} Purchase Orders
              </p>
            </CardContent>
          </Card>
        )}

        {widgets.pending_approvals && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Pending Approvals</span>
              <FileCheck className="w-4 h-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{widgets.pending_approvals.count || 0}</div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Awaiting your signature
              </p>
            </CardContent>
          </Card>
        )}

        {widgets.budget_utilization && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Budget Limit Utilization</span>
              <Percent className="w-4 h-4 text-emerald-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(widgets.budget_utilization.utilization_rate || 0).toFixed(1)}%</div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Spent: ${widgets.budget_utilization.spent_amount?.toLocaleString() || 0}
              </p>
            </CardContent>
          </Card>
        )}

        {widgets.vendor_performance && (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Vendor Compliance</span>
              <Clock className="w-4 h-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{widgets.vendor_performance.avg_score || 92}/100</div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                On-time delivery performance rating
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
              <div className="text-2xl font-bold">{widgets.my_purchase_requests.count || 0}</div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Active requests this month
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Main Dashboard Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Activity Feed */}
        <Card className="lg:col-span-2">
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
                              {new Date(activity.timestamp).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
                No recent activity recorded.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right Column: Actions Quick Links */}
        <Card>
          <CardHeader>
            <CardTitle>Enterprise Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <a
              href="/prs"
              className="flex items-center justify-between p-3 rounded-lg border border-border bg-accent/20 hover:bg-accent hover:scale-[1.01] transition-all font-semibold text-xs uppercase tracking-wider"
            >
              <span>Submit Purchase Requisition</span>
              <span>&rarr;</span>
            </a>
            <a
              href="/reports"
              className="flex items-center justify-between p-3 rounded-lg border border-border bg-accent/20 hover:bg-accent hover:scale-[1.01] transition-all font-semibold text-xs uppercase tracking-wider"
            >
              <span>Export Spend Reports</span>
              <span>&rarr;</span>
            </a>
            <a
              href="/search"
              className="flex items-center justify-between p-3 rounded-lg border border-border bg-accent/20 hover:bg-accent hover:scale-[1.01] transition-all font-semibold text-xs uppercase tracking-wider"
            >
              <span>Global Audit Search</span>
              <span>&rarr;</span>
            </a>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
export default Dashboard;
