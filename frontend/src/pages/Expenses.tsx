import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Upload, CheckCircle, XCircle, FileText, AlertCircle, RefreshCw, DollarSign, Clock, CheckSquare, XOctagon } from "lucide-react";
import toast from "react-hot-toast";
import { api } from "../services/api";
import { ExpenseReport, Receipt } from "../types";
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Select, Skeleton, Badge, Dialog } from "../components/ui";
import { useAuth } from "../hooks/useAuth";

const Expenses: React.FC = () => {
  const { hasRole, user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  
  // Create Modal State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newReport, setNewReport] = useState({
    purpose: "",
    expense_date: "",
    department_id: "",
    cost_center_id: "",
    project_code: "",
    currency: "USD",
    justification: ""
  });

  // Submission Review Modal State
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [declarationChecked, setDeclarationChecked] = useState(false);

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

  const { data: departments = [] } = useQuery({
    queryKey: ["departments"],
    queryFn: async () => {
      const res = await api.get("/departments");
      return res.data;
    }
  });

  const { data: costCenters = [] } = useQuery({
    queryKey: ["cost_centres"],
    queryFn: async () => {
      const res = await api.get("/cost_centres");
      return res.data;
    }
  });

  const createReportMutation = useMutation({
    mutationFn: async (payload: any) => {
      const res = await api.post("/expenses", payload);
      return res.data;
    },
    onSuccess: (data) => {
      toast.success("Expense report created!");
      setIsCreateOpen(false);
      setNewReport({ purpose: "", expense_date: "", department_id: "", cost_center_id: "", project_code: "", currency: "USD", justification: "" });
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
      setIsReviewOpen(false);
      setDeclarationChecked(false);
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
      toast.success("Receipt verified amount updated");
      setEditingReceiptId(null);
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    }
  });

  const managerActionMutation = useMutation({
    mutationFn: async ({ reportId, action, comments }: { reportId: number, action: 'approve' | 'reject' | 'return', comments: string }) => {
      const res = await api.post(`/expenses/${reportId}/${action}`, { comments });
      return res.data;
    },
    onSuccess: () => {
      toast.success("Manager action recorded");
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    }
  });

  const financeActionMutation = useMutation({
    mutationFn: async ({ reportId, action }: { reportId: number, action: 'finance-verify' | 'pay' }) => {
      const res = await api.post(`/expenses/${reportId}/${action}`, { comments: "" });
      return res.data;
    },
    onSuccess: () => {
      toast.success("Finance action recorded");
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    }
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newReport.purpose.trim()) return;
    const payload: any = { 
      purpose: newReport.purpose, 
      currency: newReport.currency,
      justification: newReport.justification 
    };
    if (newReport.department_id) payload.department_id = parseInt(newReport.department_id);
    if (newReport.cost_center_id) payload.cost_center_id = parseInt(newReport.cost_center_id);
    if (newReport.project_code) payload.project_code = newReport.project_code;
    
    createReportMutation.mutate(payload);
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

  const isManager = hasRole("Manager");
  const isFinance = hasRole("Finance") || hasRole("Finance Manager");
  const isManagerOrAdmin = hasRole("Admin") || isManager || isFinance || hasRole("CFO");

  // Summary Metrics
  const summary = expenses.reduce((acc, r) => {
    acc[r.status] = (acc[r.status] || 0) + 1;
    if (r.status === "Approved" || r.status === "Closed" || r.status === "Payment Requested" || r.status === "Finance Verified") {
      acc.totalReimbursed += Number(r.total_amount || 0);
    }
    return acc;
  }, { totalReimbursed: 0 } as Record<string, number>);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            {isManager && !isFinance && !hasRole("Admin") ? "Team Reimbursements" : "My Reimbursements"}
          </h1>
          <p className="text-muted-foreground mt-1">Manage, verify, and track employee expense reports.</p>
        </div>
        {!isManagerOrAdmin && (
          <Button onClick={() => setIsCreateOpen(true)} className="flex items-center gap-2">
            <Plus className="w-4 h-4" /> New Reimbursement
          </Button>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card className="bg-muted/10 border-muted">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Draft</p>
              <h3 className="text-2xl font-bold">{summary["Draft"] || 0}</h3>
            </div>
            <FileText className="w-8 h-8 text-muted-foreground/40" />
          </CardContent>
        </Card>
        <Card className="bg-amber-500/10 border-amber-500/20">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-amber-700 uppercase tracking-wider">Pending</p>
              <h3 className="text-2xl font-bold text-amber-700">{summary["Pending Approval"] || 0}</h3>
            </div>
            <Clock className="w-8 h-8 text-amber-600/40" />
          </CardContent>
        </Card>
        <Card className="bg-blue-500/10 border-blue-500/20">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-blue-700 uppercase tracking-wider">Approved</p>
              <h3 className="text-2xl font-bold text-blue-700">{summary["Approved"] || 0}</h3>
            </div>
            <CheckSquare className="w-8 h-8 text-blue-600/40" />
          </CardContent>
        </Card>
        <Card className="bg-emerald-500/10 border-emerald-500/20">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">Paid / Closed</p>
              <h3 className="text-2xl font-bold text-emerald-700">{summary["Closed"] || 0}</h3>
            </div>
            <CheckCircle className="w-8 h-8 text-emerald-600/40" />
          </CardContent>
        </Card>
        <Card className="bg-rose-500/10 border-rose-500/20">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-rose-700 uppercase tracking-wider">Rejected</p>
              <h3 className="text-2xl font-bold text-rose-700">{(summary["Rejected"] || 0) + (summary["Returned for Correction"] || 0)}</h3>
            </div>
            <XOctagon className="w-8 h-8 text-rose-600/40" />
          </CardContent>
        </Card>
        <Card className="bg-primary/10 border-primary/20">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-primary uppercase tracking-wider">Total Value</p>
              <h3 className="text-2xl font-bold text-primary">${summary.totalReimbursed.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</h3>
            </div>
            <DollarSign className="w-8 h-8 text-primary/40" />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* Left Column: List of Reports */}
        <div className="lg:col-span-1 space-y-4">
          <Card className="h-[600px] flex flex-col">
            <CardHeader className="pb-3 shrink-0">
              <CardTitle className="text-lg">Reports List</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto pt-0">
              <div className="space-y-2">
                {expenses.length === 0 && <p className="text-sm text-muted-foreground text-center py-8">No reports found.</p>}
                {expenses.map(report => (
                  <div 
                    key={report.expense_report_id}
                    onClick={() => setSelectedReportId(report.expense_report_id)}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${selectedReportId === report.expense_report_id ? 'border-primary bg-primary/5 shadow-sm' : 'hover:bg-accent'}`}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <div className="font-medium text-sm truncate pr-2">{report.purpose}</div>
                      <Badge variant={
                        report.status === "Draft" ? "outline" : 
                        report.status === "Approved" || report.status === "Closed" ? "success" : 
                        report.status.includes("Pending") ? "warning" : "error"
                      }>{report.status}</Badge>
                    </div>
                    <div className="text-xs text-muted-foreground truncate mb-2">{report.justification || "No description"}</div>
                    <div className="flex justify-between items-center text-xs text-muted-foreground">
                      <span>{new Date(report.created_at).toLocaleDateString()}</span>
                      <span className="font-bold text-foreground">${Number(report.total_amount).toFixed(2)}</span>
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
              <Card className="h-full border-t-4 border-t-primary shadow-lg flex flex-col">
                <CardHeader className="flex flex-row justify-between items-start shrink-0">
                  <div>
                    <CardTitle className="text-2xl">{report.purpose}</CardTitle>
                    <div className="text-sm text-muted-foreground mt-1 flex flex-wrap gap-x-4 gap-y-1">
                      <span>Status: <strong className="text-foreground">{report.status}</strong></span>
                      <span>Created: {new Date(report.created_at).toLocaleDateString()}</span>
                      {report.department_id && <span>Dept ID: {report.department_id}</span>}
                      {report.project_code && <span>Project: {report.project_code}</span>}
                    </div>
                    {report.justification && (
                      <p className="mt-3 text-sm text-foreground/80 bg-muted/30 p-2 rounded">{report.justification}</p>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-3xl font-bold text-primary">
                      ${Number(report.total_amount).toFixed(2)}
                    </div>
                    <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Verified Total</div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6 flex-1 overflow-y-auto">
                  {/* Timeline */}
                  <div className="flex justify-between items-center mb-6 px-4">
                    {["Draft", "Pending Approval", "Finance Verified", "Payment Requested", "Closed"].map((s, i) => {
                      const statuses = ["Draft", "Pending Approval", "Finance Verified", "Payment Requested", "Closed"];
                      let currentIndex = statuses.indexOf(report.status);
                      if (report.status === "Approved") currentIndex = 1; // Approved -> waiting for finance
                      if (report.status === "Pending Finance Verification") currentIndex = 1;
                      
                      const isCompleted = i <= currentIndex;
                      const isRejected = report.status === "Rejected" || report.status === "Returned for Correction";
                      
                      return (
                        <div key={s} className="flex flex-col items-center w-1/5 relative">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold z-10 text-xs
                            ${isCompleted ? (isRejected && i === currentIndex ? 'bg-red-500 text-white' : 'bg-primary text-primary-foreground') : 'bg-muted text-muted-foreground'}`}>
                            {i + 1}
                          </div>
                          <span className="text-[10px] mt-2 text-center text-muted-foreground leading-tight font-medium uppercase">{s}</span>
                          {i < statuses.length - 1 && (
                            <div className={`absolute top-4 left-1/2 w-full h-1 -z-0 ${i < currentIndex ? 'bg-primary' : 'bg-muted'}`} />
                          )}
                        </div>
                      )
                    })}
                  </div>
                  
                  {report.duplicate_flag && (
                    <div className="bg-red-50 text-red-700 p-3 rounded-lg border border-red-200 flex items-center gap-2 mb-4">
                      <AlertCircle className="w-5 h-5" />
                      <strong>Warning:</strong> Duplicate receipts detected across other reports.
                    </div>
                  )}
                  {report.policy_flags && (
                    <div className="bg-amber-50 text-amber-700 p-3 rounded-lg border border-amber-200 flex items-center gap-2 mb-4">
                      <AlertCircle className="w-5 h-5" />
                      <strong>Policy Flag:</strong> {report.policy_flags}
                    </div>
                  )}

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
                          onClick={() => setIsReviewOpen(true)}
                          disabled={submitReportMutation.isPending || !report.receipts?.length}
                        >
                          Review & Submit
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  {/* Manager Review */}
                  {report.status === "Pending Manager Approval" && (hasRole("Manager") || hasRole("Admin")) && (
                    <div className="flex flex-col gap-3 p-4 bg-amber-500/10 rounded-xl border border-amber-500/20">
                      <h4 className="font-semibold text-amber-800 flex items-center gap-2"><CheckSquare className="w-4 h-4" /> Manager Review Required</h4>
                      <div className="flex gap-2">
                        <Button onClick={() => managerActionMutation.mutate({ reportId: report.expense_report_id, action: 'approve', comments: 'Looks good' })} className="bg-emerald-600 hover:bg-emerald-700 text-white">Approve Claim</Button>
                        <Button onClick={() => managerActionMutation.mutate({ reportId: report.expense_report_id, action: 'return', comments: 'Please clarify' })} variant="outline" className="bg-white">Return to Employee</Button>
                        <Button onClick={() => managerActionMutation.mutate({ reportId: report.expense_report_id, action: 'reject', comments: 'Rejected due to policy' })} variant="outline" className="bg-white text-red-600 hover:bg-red-50">Reject</Button>
                      </div>
                    </div>
                  )}

                  {/* Finance Review */}
                  {report.status === "Pending Finance Verification" && (hasRole("Finance") || hasRole("Admin")) && (
                    <div className="flex flex-col gap-3 p-4 bg-blue-500/10 rounded-xl border border-blue-500/20">
                       <h4 className="font-semibold text-blue-800 flex items-center gap-2"><CheckSquare className="w-4 h-4" /> Finance Verification</h4>
                      <Button onClick={() => financeActionMutation.mutate({ reportId: report.expense_report_id, action: 'finance-verify' })} className="w-max bg-blue-600 hover:bg-blue-700 text-white">Verify All Receipts</Button>
                    </div>
                  )}

                  {/* Payment */}
                  {report.status === "Payment Requested" && (hasRole("Finance Manager") || hasRole("CFO") || hasRole("Admin")) && (
                    <div className="flex flex-col gap-3 p-4 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
                       <h4 className="font-semibold text-emerald-800 flex items-center gap-2"><DollarSign className="w-4 h-4" /> Payment Authorization</h4>
                      <Button onClick={() => financeActionMutation.mutate({ reportId: report.expense_report_id, action: 'pay' })} className="w-max bg-emerald-600 hover:bg-emerald-700 text-white">Authorize Payment</Button>
                    </div>
                  )}

                  {/* Receipts List */}
                  <div className="mt-6">
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
                          <div key={receipt.receipt_id} className={`flex flex-col md:flex-row gap-4 p-4 border rounded-xl shadow-sm transition-all ${alert && report.status === "Draft" ? 'border-amber-300 bg-amber-50 dark:bg-amber-950/20' : 'bg-card hover:shadow-md'}`}>
                            {/* Preview */}
                            <div className="w-full md:w-24 h-24 shrink-0 rounded overflow-hidden bg-muted flex items-center justify-center border group relative cursor-pointer">
                               {receipt.image_path ? (
                                 <img src={`http://localhost:8000${receipt.image_path}`} alt="Receipt" className="object-cover w-full h-full opacity-80 group-hover:opacity-100 transition-opacity" />
                               ) : (
                                 <FileText className="w-8 h-8 text-muted-foreground/50" />
                               )}
                               <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                 <span className="text-white text-xs font-bold">View</span>
                               </div>
                            </div>
                            
                            {/* Details */}
                            <div className="flex-1 flex flex-col justify-center min-w-0">
                              <div className="font-medium flex items-center gap-2 text-base truncate">
                                {receipt.merchant_name || 'Unknown Merchant'}
                                {alert && report.status === "Draft" && <AlertCircle className="w-4 h-4 text-amber-500 shrink-0" title="Low OCR confidence, please verify amount" />}
                              </div>
                              <div className="text-sm text-muted-foreground flex flex-wrap items-center gap-x-3 gap-y-1 mt-1">
                                <span>Date: <strong className="text-foreground">{receipt.receipt_date || 'N/A'}</strong></span>
                                <span>Category: <strong className="text-foreground">{receipt.category || 'Uncategorized'}</strong></span>
                                <span className="flex items-center gap-1 bg-muted/50 px-2 py-0.5 rounded">
                                  OCR Confidence: <span className={lowConfidence ? "text-amber-600 font-semibold" : "text-green-600 font-medium"}>{receipt.ocr_confidence}%</span>
                                </span>
                              </div>
                              {report.status !== "Draft" && (
                                <div className="text-xs text-muted-foreground mt-2">
                                  OCR Extracted: ${Number(receipt.ocr_amount).toFixed(2)}
                                </div>
                              )}
                            </div>
                            
                            {/* Amount & Actions */}
                            <div className="flex items-center justify-end shrink-0 md:min-w-[150px]">
                              {editingReceiptId === receipt.receipt_id ? (
                                <div className="flex items-center gap-1 bg-muted p-1 rounded-lg">
                                  <div className="relative">
                                    <span className="absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground text-sm font-bold">$</span>
                                    <Input 
                                      type="number" 
                                      className="w-24 pl-6 pr-2 text-right font-bold h-9 bg-background" 
                                      value={editAmount}
                                      onChange={e => setEditAmount(e.target.value)}
                                      autoFocus
                                    />
                                  </div>
                                  <Button size="icon" variant="ghost" onClick={() => saveAmount(report.expense_report_id, receipt.receipt_id)} className="h-9 w-9 text-green-600 hover:text-green-700 hover:bg-green-100 rounded"><CheckCircle className="w-5 h-5" /></Button>
                                  <Button size="icon" variant="ghost" onClick={() => setEditingReceiptId(null)} className="h-9 w-9 text-red-600 hover:text-red-700 hover:bg-red-100 rounded"><XCircle className="w-5 h-5" /></Button>
                                </div>
                              ) : (
                                <div 
                                  className={`flex flex-col items-end cursor-pointer rounded-lg px-3 py-2 transition-colors border ${alert && report.status === "Draft" ? "border-amber-300 bg-amber-100/50 hover:bg-amber-200" : "border-transparent hover:bg-muted"}`}
                                  onClick={() => { if(report.status === "Draft") handleEditAmount(receipt); }}
                                  title={report.status === "Draft" ? "Click to correct amount" : ""}
                                >
                                  <span className="text-2xl font-bold text-foreground">
                                    ${Number(receipt.verified_amount).toFixed(2)}
                                  </span>
                                  {report.status === "Draft" && (
                                    <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider mt-1">
                                      {alert ? "Verify Amount" : "Click to Edit"}
                                    </span>
                                  )}
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
              <div className="text-center max-w-sm">
                <FileText className="w-16 h-16 mx-auto mb-4 opacity-40 text-primary" />
                <h3 className="text-lg font-semibold text-foreground mb-2">No Report Selected</h3>
                <p className="text-sm">Select a reimbursement report from the list to view its receipts, status, and policy flags, or create a new one.</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Reimbursement Modal */}
      <Dialog isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="New Expense Reimbursement">
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <Input 
            label="Business Purpose" 
            placeholder="e.g. Q3 Sales Offsite in NYC" 
            value={newReport.purpose}
            onChange={e => setNewReport({...newReport, purpose: e.target.value})}
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input 
              label="Expense Date" 
              type="date"
              value={newReport.expense_date}
              onChange={e => setNewReport({...newReport, expense_date: e.target.value})}
            />
            <Input 
              label="Currency" 
              value={newReport.currency}
              onChange={e => setNewReport({...newReport, currency: e.target.value})}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select 
              label="Department"
              value={newReport.department_id}
              onChange={e => setNewReport({...newReport, department_id: e.target.value})}
              options={[
                { label: "None", value: "" },
                ...departments.map((d: any) => ({ label: d.department_name, value: d.department_id.toString() }))
              ]}
            />
            <Select 
              label="Cost Center"
              value={newReport.cost_center_id}
              onChange={e => setNewReport({...newReport, cost_center_id: e.target.value})}
              options={[
                { label: "None", value: "" },
                ...costCenters.map((cc: any) => ({ label: cc.cost_center_name, value: cc.cost_center_id.toString() }))
              ]}
            />
          </div>
          <Input 
            label="Project Code" 
            placeholder="e.g. PRJ-2024-X"
            value={newReport.project_code}
            onChange={e => setNewReport({...newReport, project_code: e.target.value})}
          />
          <div>
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
              Description / Justification
            </label>
            <textarea
              className="w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all duration-200"
              rows={3}
              placeholder="Provide a detailed justification for this expense claim..."
              value={newReport.justification}
              onChange={e => setNewReport({...newReport, justification: e.target.value})}
            ></textarea>
          </div>
          <div className="pt-4 flex justify-end gap-2 border-t border-border">
            <Button type="button" variant="ghost" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={createReportMutation.isPending || !newReport.purpose}>Create Report</Button>
          </div>
        </form>
      </Dialog>

      {/* Review & Submit Modal */}
      <Dialog isOpen={isReviewOpen} onClose={() => setIsReviewOpen(false)} title="Review and Submit Claim">
        {selectedReportId && (() => {
          const report = expenses.find(r => r.expense_report_id === selectedReportId);
          if (!report) return null;
          
          const unverified = report.receipts?.filter(r => Number(r.verified_amount) === 0).length || 0;
          
          return (
            <div className="space-y-6">
              <div className="bg-muted/30 p-4 rounded-xl border">
                <h3 className="font-bold text-lg mb-2">{report.purpose}</h3>
                <div className="flex justify-between items-center text-sm border-t border-border pt-3 mt-3">
                  <span className="text-muted-foreground">Total Receipts:</span>
                  <span className="font-medium">{report.receipts?.length || 0}</span>
                </div>
                <div className="flex justify-between items-center text-sm mt-2">
                  <span className="text-muted-foreground">Calculated Claim Total:</span>
                  <span className="text-xl font-bold text-primary">${Number(report.total_amount).toFixed(2)}</span>
                </div>
              </div>
              
              {unverified > 0 && (
                <div className="bg-rose-50 text-rose-700 p-3 rounded-lg border border-rose-200 flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 mt-0.5 shrink-0" />
                  <div>
                    <strong>Action Required:</strong> You have {unverified} receipt(s) with an unverified or $0.00 amount. Please review and correct the amounts before submission.
                  </div>
                </div>
              )}

              <label className="flex items-start gap-3 p-4 border rounded-xl cursor-pointer hover:bg-muted/50 transition-colors">
                <input 
                  type="checkbox" 
                  className="mt-1 w-4 h-4 text-primary rounded border-border focus:ring-primary"
                  checked={declarationChecked}
                  onChange={e => setDeclarationChecked(e.target.checked)}
                />
                <span className="text-sm leading-relaxed text-muted-foreground">
                  <strong>Employee Declaration:</strong> I certify that these expenses were incurred for legitimate business purposes in accordance with company policy, and I have not previously claimed or been reimbursed for these expenses.
                </span>
              </label>

              <div className="flex justify-end gap-3 pt-4 border-t border-border">
                <Button variant="ghost" onClick={() => setIsReviewOpen(false)}>Back to Editing</Button>
                <Button 
                  onClick={() => submitReportMutation.mutate(report.expense_report_id)}
                  disabled={!declarationChecked || unverified > 0 || submitReportMutation.isPending}
                  className="font-bold shadow-md"
                >
                  Confirm & Submit
                </Button>
              </div>
            </div>
          );
        })()}
      </Dialog>
    </div>
  );
};

export default Expenses;
