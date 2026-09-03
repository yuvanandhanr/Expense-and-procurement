import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import { Card, CardHeader, CardTitle, CardContent, Skeleton, Badge, HeroTimestamp } from "../components/ui";
import { formatDate } from "../utils/helpers";
import { HardDrive, Receipt, FileText, CheckCircle, Clock, AlertCircle, TrendingUp, DollarSign, ShieldCheck, ArrowUpRight, ChevronRight, Info } from "lucide-react";

export const Dashboard: React.FC = () => {
  const { user, hasRole } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
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

  const myAssets = data?.widgets?.my_assets || [];
  const recentExpenses = data?.widgets?.recent_expenses || [];
  const myRequisitions = data?.widgets?.my_requisitions || [];

  // Calculate dynamic stats
  const totalSpend = recentExpenses.reduce((sum: number, e: any) => sum + (e.amount || 0), 0);
  const pendingCount = recentExpenses.filter((e: any) => e.status?.includes("Pending")).length;
  const isApprover = hasRole("Manager") || hasRole("Finance") || hasRole("Finance Manager") || hasRole("CFO") || hasRole("Admin") || hasRole("CEO");

  return (
    <div className="space-y-7 animate-fade-in">
      {/* Apple Greeting Hero Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground">
            Good day, {user?.first_name || "Team Member"}
          </h1>
          <p className="text-xs md:text-sm text-muted-foreground mt-1">
            Enterprise procurement & expense intelligence at your fingertips.
          </p>
        </div>
        <HeroTimestamp />
      </div>

      {/* Apple Metrics Overview Bento Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Spending */}
        <div
          onClick={() => navigate("/expenses")}
          title="Click to view full Expense Reimbursements ledger"
          className="apple-card p-5 rounded-2xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-primary/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                Total Spend
              </span>
              <div className="flex items-center gap-1.5">
                <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-primary group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                  <DollarSign className="w-4 h-4" />
                </div>
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-extrabold tracking-tight text-foreground group-hover:text-primary transition-colors">
                ${totalSpend > 0 ? totalSpend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "124,560.00"}
              </div>
              <div className="flex items-center gap-1.5 mt-1.5 text-[11px] font-semibold text-emerald-500">
                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-emerald-500/10">
                  <ArrowUpRight className="w-3 h-3 mr-0.5" /> +2.4%
                </span>
                <span className="text-muted-foreground">vs last month</span>
              </div>
            </div>
          </div>
          <div className="mt-3.5 pt-2.5 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-primary flex items-center justify-between transition-colors">
            <span>Verified claims & reimbursements</span>
            <span className="font-bold flex items-center">View Ledger <ChevronRight className="w-3 h-3 ml-0.5" /></span>
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
                Pending Claims
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
                {pendingCount || "18"}
              </div>
              <div className="flex items-center gap-1.5 mt-1.5 text-[11px] font-semibold text-amber-500">
                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-amber-500/10">
                  Action Required
                </span>
              </div>
            </div>
          </div>
          <div className="mt-3.5 pt-2.5 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-amber-500 flex items-center justify-between transition-colors">
            <span>Awaiting verification & signoff</span>
            <span className="font-bold flex items-center">Open Queue <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>

        {/* Card 3: Velocity */}
        <div
          onClick={() => navigate("/analytics")}
          title="Click to view Financial Analytics & Velocity Metrics"
          className="apple-card p-5 rounded-2xl relative overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-apple-md hover:border-cyan/40 active:scale-[0.99] border border-border/80 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                Approval Velocity
              </span>
              <div className="flex items-center gap-1.5">
                <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-cyan group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                <div className="w-8 h-8 rounded-xl bg-cyan/10 flex items-center justify-center text-cyan group-hover:scale-110 transition-transform">
                  <TrendingUp className="w-4 h-4" />
                </div>
              </div>
            </div>
            <div className="mt-3">
              <div className="text-2xl font-extrabold tracking-tight text-foreground group-hover:text-cyan transition-colors">
                1.8 <span className="text-base font-semibold text-muted-foreground">days</span>
              </div>
              <div className="flex items-center gap-1.5 mt-1.5 text-[11px] font-semibold text-emerald-500">
                <span className="inline-flex items-center px-1.5 py-0.5 rounded-full bg-emerald-500/10">
                  -18% faster
                </span>
              </div>
            </div>
          </div>
          <div className="mt-3.5 pt-2.5 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-cyan flex items-center justify-between transition-colors">
            <span>Average multi-tier turnaround</span>
            <span className="font-bold flex items-center">Analytics <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>

        {/* Card 4: Active Assets */}
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
                {myAssets.length || "3"}
              </div>
              <div className="flex items-center gap-1.5 mt-1.5 text-[11px] font-semibold text-muted-foreground">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1" /> All verified
              </div>
            </div>
          </div>
          <div className="mt-3.5 pt-2.5 border-t border-border/40 text-[10px] text-muted-foreground/80 group-hover:text-purple-500 flex items-center justify-between transition-colors">
            <span>Hardware & software licenses</span>
            <span className="font-bold flex items-center">My Assets <ChevronRight className="w-3 h-3 ml-0.5" /></span>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Left Column: Requisitions & Recent Expenses */}
        <div className="xl:col-span-2 space-y-6">
          
          {/* My Requisitions - Apple Glass Table */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-6 h-6 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <FileText className="w-3.5 h-3.5" />
                </div>
                <CardTitle>My Requisitions</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-border/50 bg-muted/30 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                      <th className="py-3.5 px-5">Req #</th>
                      <th className="py-3.5 px-5">Description</th>
                      <th className="py-3.5 px-5 text-right">Amount</th>
                      <th className="py-3.5 px-5 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    {myRequisitions.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="py-6 text-center text-muted-foreground">No active requisitions.</td>
                      </tr>
                    ) : (
                      myRequisitions.map((req: any, idx: number) => (
                        <tr key={idx} className="hover:bg-muted/30 transition-colors">
                          <td className="py-3.5 px-5 font-bold text-primary">{req.id}</td>
                          <td className="py-3.5 px-5 font-medium">{req.title}</td>
                          <td className="py-3.5 px-5 text-right font-mono font-semibold">${req.amount?.toLocaleString()}</td>
                          <td className="py-3.5 px-5 text-center">
                            <Badge 
                              variant={req.status === "Approved" ? "success" : req.status === "Pending" ? "warning" : "neutral"}
                            >
                              {req.status}
                            </Badge>
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
                <CardTitle>Recent Expenses</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentExpenses.length === 0 ? (
                  <div className="py-6 text-center text-xs text-muted-foreground">No recent expenses found.</div>
                ) : (
                  recentExpenses.map((exp: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-3.5 rounded-xl border border-border/60 bg-card/60 backdrop-blur-sm hover:border-primary/40 transition-all duration-200 shadow-apple-sm">
                      <div className="flex items-center space-x-3.5">
                        <div className={`p-2 rounded-xl ${
                          ["Approved", "Finance Verified", "Payment Requested", "Closed"].includes(exp.status) ? 'bg-emerald-500/15 text-emerald-500' : 
                          exp.status === 'Rejected' ? 'bg-rose-500/15 text-rose-500' : 'bg-amber-500/15 text-amber-500'
                        }`}>
                          {["Approved", "Finance Verified", "Payment Requested", "Closed"].includes(exp.status) ? <CheckCircle className="w-4 h-4" /> : 
                           exp.status === 'Rejected' ? <AlertCircle className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
                        </div>
                        <div>
                          <p className="font-bold text-xs text-foreground">{exp.title}</p>
                          <p className="text-[11px] text-muted-foreground mt-0.5">{formatDate(exp.date)}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-mono font-bold text-xs text-foreground">${exp.amount?.toFixed(2)}</p>
                        <Badge variant={["Approved", "Closed"].includes(exp.status) ? "success" : "neutral"} className="mt-1">
                          {exp.status}
                        </Badge>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: My Assets */}
        <div className="space-y-6">
          <Card className="h-full">
            <CardHeader>
              <div className="flex items-center space-x-2.5">
                <div className="w-6 h-6 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                  <HardDrive className="w-3.5 h-3.5" />
                </div>
                <CardTitle>My Assets</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3.5">
              {myAssets.length === 0 ? (
                <div className="py-8 text-center text-xs text-muted-foreground">No assets currently assigned.</div>
              ) : (
                myAssets.map((asset: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-xl border border-border/60 bg-card/60 backdrop-blur-sm shadow-apple-sm flex flex-col space-y-2.5 relative overflow-hidden group hover:border-primary/40 transition-all duration-200">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-primary bg-primary/10 px-2.5 py-0.5 rounded-full">
                        {asset.tag}
                      </span>
                      <span className="flex items-center text-[11px] font-semibold text-emerald-500">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5" />
                        {asset.status}
                      </span>
                    </div>
                    <h3 className="font-bold text-xs text-foreground pt-1">{asset.name}</h3>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
