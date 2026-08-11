import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Upload, CheckCircle, XCircle, FileText, AlertCircle, RefreshCw } from "lucide-react";
import toast from "react-hot-toast";
import { api } from "../services/api";
import { ExpenseReport, Receipt } from "../types";
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Skeleton, Badge } from "../components/ui";
import { useAuth } from "../hooks/useAuth";

const Expenses: React.FC = () => {
  const { hasRole } = useAuth();
  const queryClient = useQueryClient();
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [newPurpose, setNewPurpose] = useState("");
  const [uploading, setUploading] = useState(false);
  const [editingReceiptId, setEditingReceiptId] = useState<number | null>(null);
  const [editAmount, setEditAmount] = useState<string>("");

  const { data: expenses = [], isLoading } = useQuery<ExpenseReport[]>({
    queryKey: ["expenses"],
    queryFn: async () => {
      const res = await api.get("/expenses");
      return res.data;
    }
  });

  const createReportMutation = useMutation({
    mutationFn: async (purpose: string) => {
      const res = await api.post("/expenses", { purpose, currency: "USD" });
      return res.data;
    },
    onSuccess: (data) => {
      toast.success("Expense report created!");
      setNewPurpose("");
      setSelectedReportId(data.expense_report_id);
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    },
    onError: () => {
      toast.error("Failed to create expense report");
    }
  });

  const uploadReceiptsMutation = useMutation({
    mutationFn: async ({ reportId, files }: { reportId: number; files: FileList }) => {
      const formData = new FormData();
      for (let i = 0; i < files.length; i++) {
        formData.append("files", files[i]);
      }
      const res = await api.post(`/expenses/${reportId}/receipts/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      return res.data;
    },
    onSuccess: () => {
      toast.success("Receipts uploaded & OCR completed");
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    },
    onError: () => toast.error("Failed to upload receipts")
  });

  const submitReportMutation = useMutation({
    mutationFn: async (reportId: number) => {
      const res = await api.post(`/expenses/${reportId}/submit`);
      return res.data;
    },
    onSuccess: () => {
      toast.success("Report submitted for approval");
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to submit report");
    }
  });
  
  const updateReceiptMutation = useMutation({
    mutationFn: async ({ reportId, receiptId, verified_amount }: { reportId: number, receiptId: number, verified_amount: number }) => {
      const res = await api.put(`/expenses/${reportId}/receipts/${receiptId}`, { verified_amount });
      return res.data;
    },
    onSuccess: () => {
      toast.success("Receipt updated");
      setEditingReceiptId(null);
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    }
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPurpose.trim()) return;
    createReportMutation.mutate(newPurpose);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, reportId: number) => {
    if (e.target.files && e.target.files.length > 0) {
      setUploading(true);
      await uploadReceiptsMutation.mutateAsync({ reportId, files: e.target.files });
      setUploading(false);
      e.target.value = ''; // Reset
    }
  };
  
  const handleEditAmount = (receipt: Receipt) => {
      setEditingReceiptId(receipt.receipt_id);
      setEditAmount(receipt.verified_amount.toString());
  }
  
  const saveAmount = (reportId: number, receiptId: number) => {
      updateReceiptMutation.mutate({
          reportId,
          receiptId,
          verified_amount: parseFloat(editAmount) || 0
      })
  }

  if (isLoading) return <Skeleton className="w-full h-[600px] rounded-xl" />;

  const isManagerOrAdmin = hasRole("Admin") || hasRole("Manager") || hasRole("Finance") || hasRole("CFO");

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Employee Reimbursement</h1>
          <p className="text-muted-foreground mt-1">Manage and track your expense reports and receipts.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: List of Reports */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">My Reports</CardTitle>
            </CardHeader>
            <CardContent>
              {!isManagerOrAdmin && (
                <form onSubmit={handleCreate} className="flex gap-2 mb-4">
                  <Input 
                    placeholder="E.g., Client Visit NY" 
                    value={newPurpose} 
                    onChange={e => setNewPurpose(e.target.value)}
                  />
                  <Button type="submit" disabled={createReportMutation.isPending}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </form>
              )}
              <div className="space-y-2">
                {expenses.length === 0 && <p className="text-sm text-muted-foreground">No reports found.</p>}
                {expenses.map(report => (
                  <div 
                    key={report.expense_report_id}
                    onClick={() => setSelectedReportId(report.expense_report_id)}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${selectedReportId === report.expense_report_id ? 'border-primary bg-primary/5' : 'hover:bg-accent'}`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="font-medium text-sm truncate pr-2">{report.purpose}</div>
                      <Badge variant={
                        report.status === "Draft" ? "outline" : 
                        report.status === "Approved" ? "default" : "secondary"
                      }>{report.status}</Badge>
                    </div>
                    <div className="flex justify-between items-center mt-2 text-xs text-muted-foreground">
                      <span>{new Date(report.created_at).toLocaleDateString()}</span>
                      <span className="font-semibold text-foreground">${Number(report.total_amount).toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Report Details & Receipts */}
        <div className="lg:col-span-2">
          {selectedReportId ? (() => {
            const report = expenses.find(r => r.expense_report_id === selectedReportId);
            if (!report) return null;
            return (
              <Card className="h-full border-t-4 border-t-primary shadow-lg">
                <CardHeader className="flex flex-row justify-between items-start">
                  <div>
                    <CardTitle className="text-2xl">{report.purpose}</CardTitle>
                    <div className="text-sm text-muted-foreground mt-1 flex gap-4">
                      <span>Status: <strong>{report.status}</strong></span>
                      <span>Created: {new Date(report.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-primary">
                      ${Number(report.total_amount).toFixed(2)}
                    </div>
                    <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Grand Total</div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  
                  {/* Actions */}
                  {report.status === "Draft" && (
                    <div className="flex flex-col sm:flex-row gap-4 p-4 bg-muted/30 rounded-xl border border-dashed border-primary/20">
                      <div className="flex-1">
                        <label htmlFor="receipt-upload" className="flex flex-col items-center justify-center w-full h-24 border-2 border-dashed rounded-lg cursor-pointer bg-background hover:bg-muted/50 border-primary/30 transition-colors">
                          <div className="flex flex-col items-center justify-center pt-5 pb-6">
                            {uploading ? (
                              <RefreshCw className="w-6 h-6 text-primary animate-spin mb-2" />
                            ) : (
                              <Upload className="w-6 h-6 text-primary mb-2" />
                            )}
                            <p className="text-sm text-muted-foreground">
                              {uploading ? "Extracting OCR..." : "Click to upload multiple receipts"}
                            </p>
                          </div>
                          <input id="receipt-upload" type="file" multiple accept="image/*,.pdf" className="hidden" onChange={(e) => handleFileUpload(e, report.expense_report_id)} disabled={uploading} />
                        </label>
                      </div>
                      <div className="flex items-center">
                        <Button 
                          size="lg" 
                          className="w-full sm:w-auto font-semibold shadow-md"
                          onClick={() => submitReportMutation.mutate(report.expense_report_id)}
                          disabled={submitReportMutation.isPending || !report.receipts?.length}
                        >
                          Submit Report
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Receipts List */}
                  <div>
                    <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                      <FileText className="w-5 h-5 text-muted-foreground" />
                      Attached Receipts ({report.receipts?.length || 0})
                    </h3>
                    
                    <div className="space-y-3">
                      {report.receipts?.length === 0 && (
                        <div className="p-8 text-center text-muted-foreground border rounded-lg bg-muted/10">
                          No receipts added yet. Upload receipts to build your report.
                        </div>
                      )}
                      {report.receipts?.map(receipt => {
                        const lowConfidence = receipt.ocr_confidence && receipt.ocr_confidence < 50;
                        const needsVerification = Number(receipt.verified_amount) === 0;
                        const alert = lowConfidence || needsVerification;

                        return (
                          <div key={receipt.receipt_id} className={`flex flex-col sm:flex-row gap-4 p-4 border rounded-xl shadow-sm transition-all ${alert && report.status === "Draft" ? 'border-amber-300 bg-amber-50 dark:bg-amber-950/20' : 'bg-card hover:shadow-md'}`}>
                            {/* Preview */}
                            <div className="w-16 h-16 shrink-0 rounded overflow-hidden bg-muted flex items-center justify-center border">
                               <FileText className="w-8 h-8 text-muted-foreground/50" />
                            </div>
                            
                            {/* Details */}
                            <div className="flex-1 flex flex-col justify-center">
                              <div className="font-medium flex items-center gap-2">
                                {receipt.merchant_name || 'Unknown Merchant'}
                                {alert && report.status === "Draft" && <AlertCircle className="w-4 h-4 text-amber-500" title="Low OCR confidence, please verify amount" />}
                              </div>
                              <div className="text-sm text-muted-foreground flex items-center gap-3 mt-1">
                                <span>{receipt.receipt_date || 'Unknown Date'}</span>
                                <span className="flex items-center gap-1">
                                  OCR Confidence: <span className={lowConfidence ? "text-amber-600 font-semibold" : "text-green-600"}>{receipt.ocr_confidence}%</span>
                                </span>
                              </div>
                            </div>
                            
                            {/* Amount & Actions */}
                            <div className="flex items-center justify-end min-w-[120px]">
                              {editingReceiptId === receipt.receipt_id ? (
                                <div className="flex items-center gap-2">
                                  <Input 
                                    type="number" 
                                    className="w-24 text-right font-bold h-9" 
                                    value={editAmount}
                                    onChange={e => setEditAmount(e.target.value)}
                                    autoFocus
                                  />
                                  <Button size="icon" variant="ghost" onClick={() => saveAmount(report.expense_report_id, receipt.receipt_id)} className="h-8 w-8 text-green-600 hover:text-green-700 hover:bg-green-100"><CheckCircle className="w-4 h-4" /></Button>
                                  <Button size="icon" variant="ghost" onClick={() => setEditingReceiptId(null)} className="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-100"><XCircle className="w-4 h-4" /></Button>
                                </div>
                              ) : (
                                <div 
                                  className={`text-xl font-bold text-right cursor-pointer rounded px-2 py-1 transition-colors ${alert && report.status === "Draft" ? "text-amber-600 bg-amber-100/50 hover:bg-amber-200" : "text-foreground hover:bg-muted"}`}
                                  onClick={() => { if(report.status === "Draft") handleEditAmount(receipt); }}
                                  title={report.status === "Draft" ? "Click to edit" : ""}
                                >
                                  ${Number(receipt.verified_amount).toFixed(2)}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })() : (
            <div className="h-full flex items-center justify-center p-12 border rounded-xl bg-muted/10 text-muted-foreground">
              <div className="text-center">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Select a report to view details or create a new one.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Expenses;
