import React, { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Skeleton,
  Badge,
  HeroTimestamp,
} from "../components/ui";
import { formatDate } from "../utils/helpers";
import {
  Users,
  Briefcase,
  Package,
  FileSpreadsheet,
  AlertCircle,
  Clock,
  TrendingUp,
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

export const ProcurementDashboard: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  
  // We mock the API call here for the new dashboard, 
  // ideally this should fetch from a new backend endpoint
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await api.get("/dashboard");
        const dashData = response.data;
        
        setData({
          timestamp: dashData.timestamp,
          metrics: dashData.widgets?.procurement_metrics || {
            active_vendors: 0,
            pending_rfqs: 0,
            open_pos: 0,
            active_contracts: 0
          },
          vendor_scores: dashData.widgets?.vendor_performance || []
        });
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

  const role = user?.roles[0]?.role_name || "Manager";

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Procurement Cycle Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Supplier and Contract health overview for: <Badge variant="info" className="ml-1">{role}</Badge>
          </p>
        </div>
        <HeroTimestamp />
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Active Vendors</span>
            <Users className="w-4 h-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.metrics?.active_vendors || 0}</div>
            <p className="text-[10px] text-muted-foreground font-semibold mt-1">
              Registered & approved suppliers
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Open RFQs</span>
            <Briefcase className="w-4 h-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.metrics?.pending_rfqs || 0}</div>
            <p className="text-[10px] text-muted-foreground font-semibold mt-1">
              Awaiting supplier bids
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Active POs</span>
            <Package className="w-4 h-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.metrics?.open_pos || 0}</div>
            <p className="text-[10px] text-muted-foreground font-semibold mt-1">
              Currently processing
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Active Contracts</span>
            <FileSpreadsheet className="w-4 h-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.metrics?.active_contracts || 0}</div>
            <p className="text-[10px] text-muted-foreground font-semibold mt-1">
              Valid supplier agreements
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Top Vendor Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[250px] w-full">
                <Bar
                  data={{
                    labels: data?.vendor_scores?.map((v: any) => v.name) || [],
                    datasets: [
                      {
                        label: 'Performance Score (Out of 100)',
                        data: data?.vendor_scores?.map((v: any) => v.score) || [],
                        backgroundColor: 'rgba(16, 185, 129, 0.5)',
                        borderColor: 'rgba(16, 185, 129, 1)',
                        borderWidth: 1,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      y: { beginAtZero: true, max: 100 }
                    }
                  }}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <a
              href="/vendors"
              className="flex items-center justify-between p-3 rounded-lg border border-border bg-card hover:-translate-y-[1px] hover:border-violet/50 hover:shadow-sm transition-all group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-md bg-violet/10 text-violet flex items-center justify-center">
                  <Users className="w-4 h-4" />
                </div>
                <div>
                  <span className="block font-bold text-sm text-foreground group-hover:text-violet transition-colors">Manage Vendors</span>
                  <span className="block text-[10px] text-muted-foreground font-medium mt-0.5">Approve and onboard</span>
                </div>
              </div>
              <span className="text-muted-foreground group-hover:text-violet transition-colors">&rarr;</span>
            </a>
            <a
              href="/contracts"
              className="flex items-center justify-between p-3 rounded-lg border border-border bg-card hover:-translate-y-[1px] hover:border-cyan/50 hover:shadow-sm transition-all group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-md bg-cyan/10 text-cyan flex items-center justify-center">
                  <FileSpreadsheet className="w-4 h-4" />
                </div>
                <div>
                  <span className="block font-bold text-sm text-foreground group-hover:text-cyan transition-colors">Review Contracts</span>
                  <span className="block text-[10px] text-muted-foreground font-medium mt-0.5">Manage agreements</span>
                </div>
              </div>
              <span className="text-muted-foreground group-hover:text-cyan transition-colors">&rarr;</span>
            </a>
            <a
              href="/quotations"
              className="flex items-center justify-between p-3 rounded-lg border border-border bg-card hover:-translate-y-[1px] hover:border-lime/50 hover:shadow-sm transition-all group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-md bg-lime/10 text-lime flex items-center justify-center">
                  <Briefcase className="w-4 h-4" />
                </div>
                <div>
                  <span className="block font-bold text-sm text-foreground group-hover:text-lime transition-colors">Review Quotations</span>
                  <span className="block text-[10px] text-muted-foreground font-medium mt-0.5">Evaluate supplier bids</span>
                </div>
              </div>
              <span className="text-muted-foreground group-hover:text-lime transition-colors">&rarr;</span>
            </a>
            <a
              href="/pos"
              className="flex items-center justify-between p-3 rounded-lg border border-border bg-card hover:-translate-y-[1px] hover:border-violet/50 hover:shadow-sm transition-all group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-md bg-violet/10 text-violet flex items-center justify-center">
                  <Package className="w-4 h-4" />
                </div>
                <div>
                  <span className="block font-bold text-sm text-foreground group-hover:text-violet transition-colors">View Open POs</span>
                  <span className="block text-[10px] text-muted-foreground font-medium mt-0.5">Track fulfillments</span>
                </div>
              </div>
              <span className="text-muted-foreground group-hover:text-violet transition-colors">&rarr;</span>
            </a>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
export default ProcurementDashboard;
