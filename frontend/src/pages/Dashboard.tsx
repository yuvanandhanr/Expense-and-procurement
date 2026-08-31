import React, { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import { Card, CardHeader, CardTitle, CardContent, Skeleton, Badge, HeroTimestamp } from "../components/ui";
import { formatDate } from "../utils/helpers";
import { HardDrive, Receipt, FileText, CheckCircle, Clock, AlertCircle } from "lucide-react";

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // We mock some employee data if the API doesn't return exactly what we need for the specific prompt UI.
  // The backend currently provides `widgets`. We will assume or supplement it to fulfill the requirements.

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

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Welcome back, {user?.first_name || "Employee"}</h1>
          <p className="text-sm text-muted-foreground mt-1">Here is an overview of your active requests and assets.</p>
        </div>
        <HeroTimestamp />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Left Column: Requisitions (Status Table) & Expenses (List) */}
        <div className="xl:col-span-2 space-y-6">
          
          {/* My Requisitions - Status Table */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-primary" />
                <CardTitle>My Requisitions</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-border bg-accent/30 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                      <th className="p-4">Req #</th>
                      <th className="p-4">Description</th>
                      <th className="p-4 text-right">Amount</th>
                      <th className="p-4 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {myRequisitions.map((req: any, idx: number) => (
                      <tr key={idx} className="hover:bg-accent/10 transition-colors">
                        <td className="p-4 font-semibold text-primary">{req.id}</td>
                        <td className="p-4">{req.title}</td>
                        <td className="p-4 text-right font-mono">${req.amount.toLocaleString()}</td>
                        <td className="p-4 text-center">
                          <Badge 
                            variant={req.status === "Approved" ? "success" : req.status === "Pending" ? "warning" : "neutral"}
                          >
                            {req.status}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Recent Expenses - List */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center space-x-2">
                <Receipt className="w-5 h-5 text-primary" />
                <CardTitle>Recent Expenses</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentExpenses.map((exp: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-lg border border-border bg-card-2 hover:border-primary/30 transition-colors">
                    <div className="flex items-center space-x-4">
                      <div className={`p-2 rounded-full ${
                        exp.status === 'Approved' ? 'bg-lime/20 text-lime' : 
                        exp.status === 'Rejected' ? 'bg-destructive/20 text-destructive' : 'bg-amber-500/20 text-amber-500'
                      }`}>
                        {exp.status === 'Approved' ? <CheckCircle className="w-4 h-4" /> : 
                         exp.status === 'Rejected' ? <AlertCircle className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
                      </div>
                      <div>
                        <p className="font-semibold text-sm">{exp.title}</p>
                        <p className="text-xs text-muted-foreground">{formatDate(exp.date)}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-mono font-bold">${exp.amount.toFixed(2)}</p>
                      <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">{exp.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: My Assets */}
        <div className="space-y-6">
          <Card className="h-full">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <HardDrive className="w-5 h-5 text-primary" />
                <CardTitle>My Assets</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {myAssets.map((asset: any, idx: number) => (
                <div key={idx} className="p-4 rounded-lg border border-border bg-gradient-to-br from-card to-card-2 shadow-sm flex flex-col space-y-3 relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                    <HardDrive className="w-16 h-16" />
                  </div>
                  <div className="z-10">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                      {asset.tag}
                    </span>
                    <h3 className="font-bold text-sm mt-2">{asset.name}</h3>
                  </div>
                  <div className="z-10 flex items-center justify-between text-xs font-semibold text-muted-foreground pt-2 border-t border-border/50">
                    <span>Status:</span>
                    <span className="flex items-center text-lime">
                      <span className="w-1.5 h-1.5 rounded-full bg-lime mr-1.5 animate-pulse" />
                      {asset.status}
                    </span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
