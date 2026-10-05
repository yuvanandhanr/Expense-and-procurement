import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import { Report } from "../types";
import {Button, Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, Input, EmptyState} from "../components/ui";
import { formatDate } from "../utils/helpers";
import { Sparkles, ChevronRight } from "lucide-react";
import toast from "react-hot-toast";

export const Reports: React.FC = () => {
  const { hasRole } = useAuth();
  const navigate = useNavigate();
  const isFinanceOrAdmin = hasRole("Admin") || hasRole("CEO") || hasRole("CFO") || hasRole("Finance Manager") || hasRole("Finance");

  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Export states
  const [name, setName] = useState("");
  const [reportType, setReportType] = useState("PR");
  const [fileType, setFileType] = useState("CSV");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const response = await api.get("/reports");
      setReports(response.data);
    } catch (err) {
      console.error("Failed to load reports history:", err);
    } finally {
      if (false) setLoading(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleExport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) {
      toast.error("Please provide a report name.");
      return;
    }
    setIsSubmitting(true);
    try {
      await api.post("/reports/generate", {
        name,
        report_type: reportType,
        file_type: fileType,
      });
      toast.success("Export generated successfully!");
      setName("");
      fetchReports();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to generate report export.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  const handleDownloadReport = async (rep: any) => {
    setDownloadingId(rep.report_id);
    try {
      const response = await api.get(`/reports/${rep.report_id}/download`, {
        responseType: "blob",
      });
      const ext = rep.file_type?.toLowerCase() === "pdf" ? "pdf" : (rep.file_type?.toLowerCase() === "excel" ? "xlsx" : "csv");
      const filename = rep.name ? (rep.name.includes(".") ? rep.name : `${rep.name}.${ext}`) : `Report_${rep.report_id}.${ext}`;
      const mime = ext === "pdf" ? "application/pdf" : (ext === "xlsx" ? "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" : "text/csv");
      
      const blob = new Blob([response.data], { type: mime });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success(`Downloaded ${filename} directly to your disk!`);
    } catch (err: any) {
      console.error("Report download failed:", err);
      // Fallback to /files/download/ endpoint
      try {
        const response = await api.get(`/files/download/${rep.report_id}`, {
          responseType: "blob",
        });
        const ext = rep.file_type?.toLowerCase() === "pdf" ? "pdf" : (rep.file_type?.toLowerCase() === "excel" ? "xlsx" : "csv");
        const filename = rep.name ? (rep.name.includes(".") ? rep.name : `${rep.name}.${ext}`) : `Report_${rep.report_id}.${ext}`;
        const blob = new Blob([response.data]);
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        toast.success(`Downloaded ${filename} directly to your disk!`);
      } catch (fallbackErr: any) {
        toast.error(err.response?.data?.detail || "Failed to download file from server.");
      }
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Exports & Reports</h1>
          <p className="text-xs text-muted-foreground mt-1">Export transaction data, requisitions, invoices, and audit logs.</p>
        </div>
        {isFinanceOrAdmin && (
          <Button
            onClick={() => navigate("/reports/executive")}
            className="bg-sky-500 hover:bg-sky-600 text-white font-bold text-xs flex items-center gap-1.5 shadow-apple-sm"
          >
            <Sparkles className="w-4 h-4" /> Dataeko Executive Dossier Generator <ChevronRight className="w-3.5 h-3.5" />
          </Button>
        )}
      </div>

      {/* Dataeko Executive Banner for CFO / Finance */}
      {isFinanceOrAdmin && (
        <div
          onClick={() => navigate("/reports/executive")}
          className="p-4 rounded-2xl bg-gradient-to-r from-[#0F172A] to-[#1E293B] text-white border border-sky-500/30 flex items-center justify-between cursor-pointer hover:border-sky-400/60 transition-all shadow-md group"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/20 text-sky-400 flex items-center justify-center font-bold">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded bg-sky-500/30 text-sky-300">
                  Dataeko AI
                </span>
                <span className="text-xs font-bold text-slate-300">Executive Financial & Performance Report</span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Generate 5-year longitudinal historical archive or custom date range PDF with multi-level cascading parameters.
              </p>
            </div>
          </div>
          <Button size="sm" className="bg-sky-500 hover:bg-sky-600 text-white font-bold text-xs gap-1">
            <span>Open Builder</span> <ChevronRight className="w-3.5 h-3.5" />
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Export Request Card */}
        <Card className="lg:col-span-1 h-fit">
          <CardHeader>
            <CardTitle>Request Export Run</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleExport} className="space-y-4">
              <Input
                id="name"
                label="Report Export Filename"
                placeholder="e.g. Q3_Purchase_Summary"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />

              <div className="space-y-1">
                <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">Report Source Domain</label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="PR">My Requisitions</option>
                  <option value="PO">Purchase Orders</option>
                  <option value="Vendor">Vendor Catalog</option>
                  <option value="Invoice">Invoices & Match Status</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">Format Target</label>
                <select
                  value={fileType}
                  onChange={(e) => setFileType(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="CSV">Comma Separated Values (.csv)</option>
                  <option value="Excel">Microsoft Excel (.xlsx)</option>
                  <option value="PDF">Portable Document Format (.pdf)</option>
                </select>
              </div>

              <Button type="submit" className="w-full font-bold text-xs uppercase py-3 mt-4" disabled={isSubmitting}>
                {isSubmitting ? "Exporting Data..." : "Run Export Pipeline"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Right: Reports History List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Generated Export Log</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 space-y-4">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            ) : reports.length === 0 ? (
              <EmptyState title="No reports generated yet." description="Data will appear here once available." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                      <th className="p-4">Report Name</th>
                      <th className="p-4">Source</th>
                      <th className="p-4">Format</th>
                      <th className="p-4">Status</th>
                      <th className="p-4">Date</th>
                      <th className="p-4">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {reports.map((rep) => (
                      <tr key={rep.report_id} className="hover:bg-accent/20">
                        <td className="p-4 font-bold">{rep.name}</td>
                        <td className="p-4 text-xs font-bold uppercase">{rep.report_type}</td>
                        <td className="p-4 text-xs font-bold uppercase">{rep.file_type}</td>
                        <td className="p-4">
                          <Badge variant={rep.status === "Completed" ? "success" : "neutral"}>
                            {rep.status}
                          </Badge>
                        </td>
                        <td className="p-4 text-xs text-muted-foreground">
                          {formatDate(rep.created_at)}
                        </td>
                        <td className="p-4">
                          {rep.status === "Completed" && (
                            <button
                              type="button"
                              onClick={() => handleDownloadReport(rep)}
                              disabled={downloadingId === rep.report_id}
                              className="text-xs font-bold text-sky-500 hover:text-sky-600 hover:underline uppercase tracking-wider cursor-pointer bg-transparent border-none p-0 inline-flex items-center gap-1"
                            >
                              {downloadingId === rep.report_id ? "Downloading..." : "Download"}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
export default Reports;
