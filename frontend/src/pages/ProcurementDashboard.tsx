import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
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
  ArrowUpRight,
  ChevronRight,
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
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  const fetchLiveData = React.useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const [dashRes, vendorRes, rfqRes, poRes, contractRes, invoiceRes] = await Promise.all([
        api.get("/dashboard").catch(() => ({ data: null })),
        api.get("/vendors").catch(() => ({ data: [] })),
        api.get("/rfq").catch(() => ({ data: [] })),
        api.get("/purchase-orders").catch(() => ({ data: [] })),
        api.get("/contracts").catch(() => ({ data: [] })),
        api.get("/invoices").catch(() => ({ data: [] }))
      ]);

      const dashData = dashRes?.data || {};
      const vendors = Array.isArray(vendorRes?.data) ? vendorRes.data : [];
      const rfqs = Array.isArray(rfqRes?.data) ? rfqRes.data : [];
      const pos = Array.isArray(poRes?.data) ? poRes.data : [];
      const contracts = Array.isArray(contractRes?.data) ? contractRes.data : [];
      const invoices = Array.isArray(invoiceRes?.data) ? invoiceRes.data : [];

      setData({
        timestamp: dashData.timestamp || new Date().toISOString(),
        metrics: {
          active_vendors: vendors.filter((v: any) => v?.status === "Active" || !v?.status).length || vendors.length,
          pending_rfqs: rfqs.filter((r: any) => r?.status !== "Closed").length || rfqs.length,
          open_pos: pos.filter((p: any) => p?.status !== "Completed" && p?.status !== "Cancelled").length || pos.length,
          active_contracts: contracts.filter((c: any) => c?.status === "Active" || !c?.status).length || contracts.length,
          pending_invoices: invoices.filter((i: any) => i?.status !== "Paid" && i?.status !== "Approved").length || invoices.length
        },
        vendor_scores: Array.isArray(dashData.widgets?.vendor_performance) ? dashData.widgets.vendor_performance : []
      });
    } catch (err) {
      console.error("Failed to load real-time procurement metrics:", err);
    } finally {
      if (isInitial) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLiveData(true);
    const interval = setInterval(() => {
      fetchLiveData(false);
    }, 10000);

    const onFocus = () => fetchLiveData(false);
    window.addEventListener("focus", onFocus);

    return () => {
      clearInterval(interval);
      window.removeEventListener("focus", onFocus);
    };
  }, [fetchLiveData]);

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

  const role = user?.roles?.[0]?.role_name || "Manager";

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold tracking-tight">Procurement Cycle Dashboard</h1>
            <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping mr-0.5" /> Live Sync
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Supplier and Contract health overview for: <Badge variant="info" className="ml-1">{role}</Badge>
          </p>
        </div>
        <HeroTimestamp />
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {/* Card 1: Active Vendors */}
        <div
          onClick={() => navigate("/vendors")}
          title="Click to view Vendors Directory & Scores"
          className="apple-card p-5 rounded-2xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-blue-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider group-hover:text-blue-500 transition-colors">
                Active Vendors
              </span>
              <div className="flex items-center gap-1.5">
                <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-blue-500 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                <div className="w-8 h-8 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-500 group-hover:scale-110 transition-transform">
                  <Users className="w-4 h-4" />
                </div>
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-foreground group-hover:text-blue-500 transition-colors">
                {data?.metrics?.active_vendors || 0}
              </div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Registered & approved suppliers
              </p>
            </div>
          </div>
          <div className="mt-3.5 pt-2.5 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-blue-500 flex items-center justify-between transition-colors">
            <span>Directory & performance</span>
            <span className="font-bold flex items-center">Vendors <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>

        {/* Card 2: Open RFQs */}
        <div
          onClick={() => navigate("/rfqs")}
          title="Click to view Requests for Quotation (RFQs)"
          className="apple-card p-5 rounded-2xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-amber-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider group-hover:text-amber-500 transition-colors">
                Open RFQs
              </span>
              <div className="flex items-center gap-1.5">
                <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-amber-500 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                <div className="w-8 h-8 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-500 group-hover:scale-110 transition-transform">
                  <Briefcase className="w-4 h-4" />
                </div>
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-foreground group-hover:text-amber-500 transition-colors">
                {data?.metrics?.pending_rfqs || 0}
              </div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Awaiting supplier bids
              </p>
            </div>
          </div>
          <div className="mt-3.5 pt-2.5 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-amber-500 flex items-center justify-between transition-colors">
            <span>Active tenders & quotes</span>
            <span className="font-bold flex items-center">RFQs <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>

        {/* Card 3: Active POs */}
        <div
          onClick={() => navigate("/pos")}
          title="Click to view Purchase Orders"
          className="apple-card p-5 rounded-2xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-emerald-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider group-hover:text-emerald-500 transition-colors">
                Active POs
              </span>
              <div className="flex items-center gap-1.5">
                <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-emerald-500 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                <div className="w-8 h-8 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-500 group-hover:scale-110 transition-transform">
                  <Package className="w-4 h-4" />
                </div>
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-foreground group-hover:text-emerald-500 transition-colors">
                {data?.metrics?.open_pos || 0}
              </div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Currently processing
              </p>
            </div>
          </div>
          <div className="mt-3.5 pt-2.5 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-emerald-500 flex items-center justify-between transition-colors">
            <span>Fulfillment & deliveries</span>
            <span className="font-bold flex items-center">Orders <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>

        {/* Card 4: Active Contracts */}
        <div
          onClick={() => navigate("/contracts")}
          title="Click to view Contracts Registry"
          className="apple-card p-5 rounded-2xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-purple-500/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider group-hover:text-purple-500 transition-colors">
                Active Contracts
              </span>
              <div className="flex items-center gap-1.5">
                <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-purple-500 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                <div className="w-8 h-8 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-500 group-hover:scale-110 transition-transform">
                  <FileSpreadsheet className="w-4 h-4" />
                </div>
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-foreground group-hover:text-purple-500 transition-colors">
                {data?.metrics?.active_contracts || 0}
              </div>
              <p className="text-[10px] text-muted-foreground font-semibold mt-1">
                Valid supplier agreements
              </p>
            </div>
          </div>
          <div className="mt-3.5 pt-2.5 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-purple-500 flex items-center justify-between transition-colors">
            <span>Terms & SLA compliance</span>
            <span className="font-bold flex items-center">Contracts <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>
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
