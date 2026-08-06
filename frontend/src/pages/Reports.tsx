import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { Report } from "../types";
import { Button, Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, Input } from "../components/ui";
import { formatDate } from "../utils/helpers";
import toast from "react-hot-toast";

export const Reports: React.FC = () => {
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Exports & Reports</h1>
        <p className="text-xs text-muted-foreground mt-1">Export transaction data, requisitions, invoices, and audit logs.</p>
      </div>

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
                  <option value="PR">Purchase Requisitions</option>
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
              <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
                No reports generated yet.
              </div>
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
                            <a
                              href={`/api/v1/files/download/${rep.report_id}`}
                              className="text-xs font-bold text-primary hover:underline uppercase tracking-wider"
                              target="_blank"
                              rel="noreferrer"
                            >
                              Download
                            </a>
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
