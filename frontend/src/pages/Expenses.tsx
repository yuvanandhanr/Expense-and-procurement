import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Upload, CheckCircle, XCircle, FileText, AlertCircle, RefreshCw, DollarSign, Clock, CheckSquare, XOctagon, Trash2, ClipboardList, Building, Briefcase, Eye } from "lucide-react";
import toast from "react-hot-toast";
import { api } from "../services/api";
import { Card, CardHeader, CardTitle, CardContent, Button, Input, Select, Skeleton, Badge, StatusBadge, Dialog, HeroTimestamp, EmptyState } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { isValidText } from "../utils/helpers";

const Expenses: React.FC = () => {
  const { hasRole, user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState("All");

  // Create Modal State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newReport, setNewReport] = useState({
    purpose: "",
    submission_date: new Date().toISOString().slice(0, 10),
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
  // Manager Action Modal State
  const [managerAction, setManagerAction] = useState<{ isOpen: boolean, action: 'return' | 'reject' | null, reportId: number | null }>({ isOpen: false, action: null, reportId: null });
  const [managerComments, setManagerComments] = useState("");

  // Edit Details State
  const [isEditDetailsOpen, setIsEditDetailsOpen] = useState(false);
  const [editDetails, setEditDetails] = useState({ purpose: "", justification: "", department_id: "", cost_center_id: "", project_code: "" });
  const [previewReceiptUrl, setPreviewReceiptUrl] = useState<string | null>(null);

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
      setNewReport({ purpose: "", submission_date: new Date().toISOString().slice(0, 10), department_id: "", cost_center_id: "", project_code: "", currency: "USD", justification: "" });
      setSelectedReportId(data.expense_report_id);
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to create expense report");
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
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || err.message || "Failed to upload receipt (Duplicate or Invalid file)");
    }
  });

  const deleteReceiptMutation = useMutation({
    mutationFn: async ({ reportId, receiptId }: { reportId: number; receiptId: number }) => {
      const res = await api.delete(`/expenses/${reportId}/receipts/${receiptId}`);
      return res.data;
    },
    onSuccess: () => {
      toast.success("Receipt deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to delete receipt");
    }
  });

  const deleteReportMutation = useMutation({
    mutationFn: async (reportId: number) => {
      const res = await api.delete(`/expenses/${reportId}`);
      return res.data;
    },
    onSuccess: () => {
      toast.success("Draft expense report deleted");
      if (selectedReportId) setSelectedReportId(null);
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to delete draft report");
    }
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

  const updateReportMutation = useMutation({
    mutationFn: async ({ reportId, payload }: { reportId: number, payload: any }) => {
      const res = await api.put(`/expenses/${reportId}`, payload);
      return res.data;
    },
    onSuccess: () => {
      toast.success("Expense report updated");
      setIsEditDetailsOpen(false);
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : "Failed to update report. Please check your inputs.");
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
    if (!newReport.purpose.trim() || !isValidText(newReport.purpose)) {
      toast.error("Business purpose is required and must contain letters or numbers.");
      return;
    }
    if (!newReport.justification.trim() || !isValidText(newReport.justification)) {
      toast.error("Description / Justification is required and must contain letters or numbers.");
      return;
    }
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
      const report = expenses.find(item => item.expense_report_id === reportId);
      const selectedNames = new Set<string>();
      for (const file of Array.from(e.target.files)) {
        const normalizedName = file.name.trim().toLowerCase();
        if (selectedNames.has(normalizedName) || report?.receipts?.some(receipt => receipt.file_name.trim().toLowerCase() === normalizedName)) {
          toast.error("This receipt is already attached to the reimbursement. Choose a different file.");
          e.target.value = "";
          return;
        }
        selectedNames.add(normalizedName);
      }
      setUploading(true);
      try {
        await uploadReceiptsMutation.mutateAsync({ reportId, files: e.target.files });
      } finally {
        setUploading(false);
        e.target.value = ''; // Reset, including after a rejected duplicate.
      }
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
  const isOwner = (report: any) => user?.user_id === report.employee_id;

  // Summary Metrics
  const summary = expenses.reduce((acc, r) => {
    acc[r.status] = (acc[r.status] || 0) + 1;
    if (r.status === "Approved" || r.status === "Closed" || r.status === "Payment Requested" || r.status === "Finance Verified") {
      acc.totalReimbursed += Number(r.total_amount || 0);
    }
    return acc;
  }, { totalReimbursed: 0 } as Record<string, number>);


  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase();
    if (s === "approved" || s === "closed" || s === "payment requested" || s === "finance verified") return <Badge variant="success">{status}</Badge>;
    if (s === "pending" || s.includes("pending") || s === "corrected claim") return <Badge variant="warning">{status}</Badge>;
    if (s === "rejected" || s === "returned for correction") return <Badge variant="error">{status}</Badge>;
    return <Badge variant="neutral">{status}</Badge>;
  };

  const subTabCounts: Record<string, number> = {
    All: expenses.length,
    Draft: expenses.filter((r: any) => r.status === "Draft").length,
    Submitted: expenses.filter((r: any) => r.status.includes("Pending") || r.status === "Corrected Claim" || r.status === "Payment Requested" || r.status === "Finance Verified").length,
    Approved: expenses.filter((r: any) => r.status === "Approved" || r.status === "Closed").length,
    Rejected: expenses.filter((r: any) => r.status === "Rejected" || r.status === "Returned for Correction").length,
  };

  const filteredExpenses = expenses.filter((r: any) => {
    if (statusFilter === "All") return true;
    if (statusFilter === "Draft") return r.status === "Draft";
    if (statusFilter === "Submitted") return r.status.includes("Pending") || r.status === "Corrected Claim" || r.status === "Payment Requested" || r.status === "Finance Verified";
    if (statusFilter === "Approved") return r.status === "Approved" || r.status === "Closed";
    if (statusFilter === "Rejected") return r.status === "Rejected" || r.status === "Returned for Correction";
    return r.status === statusFilter;
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            My Reimbursements
          </h1>
          <p className="text-xs text-muted-foreground mt-1">Manage, verify, and track employee expense reports.</p>
        </div>
        <div className="flex items-center space-x-4">
          <HeroTimestamp />
          <Button onClick={() => setIsCreateOpen(true)} className="font-bold text-xs uppercase tracking-wider">
            New Reimbursement
          </Button>
        </div>
      </div>

      {/* Filters & Controls */}
      <div className="flex items-center space-x-2 bg-muted/40 p-1.5 rounded-xl w-fit border border-border/50">
        {["All", "Draft", "Submitted", "Approved", "Rejected"].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center space-x-1.5 ${
              statusFilter === status
                ? "bg-primary text-primary-foreground shadow-sm font-bold"
                : "text-muted-foreground hover:text-foreground hover:bg-background/50"
            }`}
          >
            <span>{status}</span>
            <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
              statusFilter === status ? "bg-primary-foreground/20 text-primary-foreground font-bold" : "bg-muted text-muted-foreground"
            }`}>
              {subTabCounts[status]}
            </span>
          </button>
        ))}
      </div>

      {/* Table List */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : filteredExpenses.length === 0 ? (
            <EmptyState
              icon={<FileText className="w-10 h-10" />}
              title="No Reimbursements Found"
              description={`There are no expense reports matching "${statusFilter}".`}
              actionLabel={(!isFinance && !hasRole("CFO")) ? "Create new reimbursement" : undefined}
              onAction={(!isFinance && !hasRole("CFO")) ? () => setIsCreateOpen(true) : undefined}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    <th className="p-4">Report ID</th>
                    <th className="p-4">Purpose</th>
                    <th className="p-4">Total Amount</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Date Created</th>
                    <th className="p-4">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-sm">
                  {filteredExpenses.map((report: any) => (
                    <tr key={report.expense_report_id} className="hover:bg-accent/20 transition-colors">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{report.expense_report_id}</td>
                      <td className="p-4">
                        <div className="font-semibold">{report.purpose}</div>
                        <div className="text-xs text-muted-foreground truncate max-w-[200px]">{report.justification}</div>
                      </td>
                      <td className="p-4 font-bold text-foreground">
                        ${Number(report.total_amount).toFixed(2)}
                      </td>
                      <td className="p-4">
                        {getStatusBadge(report.status)}
                      </td>
                      <td className="p-4 text-xs text-muted-foreground">{new Date(report.created_at).toLocaleDateString()}</td>
                      <td className="p-4 flex items-center gap-2">
                        {report.status === "Draft" && (
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-8 w-8 text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded shrink-0"
                            title="Delete Draft Report"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (window.confirm("Are you sure you want to delete this draft expense report?")) {
                                deleteReportMutation.mutate(report.expense_report_id);
                              }
                            }}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                        <Button 
                          size="sm" 
                          variant={["Approved", "Closed", "Rejected", "Returned for Correction"].includes(report.status) ? "secondary" : "primary"}
                          onClick={() => setSelectedReportId(report.expense_report_id)}
                          className="gap-1.5"
                        >
                          {(() => {
                            if (["Approved", "Closed", "Rejected", "Returned for Correction"].includes(report.status)) return <><Eye className="w-3.5 h-3.5" /> View</>;
                            if (report.status === "Draft") return "Edit Draft";
                            return "View Details";
                          })()}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Reimbursement Modal */}
      <Dialog isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="New Expense Reimbursement">
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <Input
            label="Business Purpose *"
            placeholder="e.g. Q3 Sales Offsite in NYC"
            value={newReport.purpose}
            onChange={e => setNewReport({ ...newReport, purpose: e.target.value.replace(/[^a-zA-Z0-9\s.,-]/g, '') })}
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Date of Submission"
              type="date"
              value={newReport.submission_date}
              readOnly
            />
            <Input
              label="Currency *"
              value={newReport.currency}
              onChange={e => setNewReport({ ...newReport, currency: e.target.value })}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Department"
              value={newReport.department_id}
              onChange={e => setNewReport({ ...newReport, department_id: e.target.value })}
              options={[
                { label: "None", value: "" },
                ...departments.map((d: any) => ({ label: d.department_name, value: d.department_id.toString() }))
              ]}
            />
            <Select
              label="Cost Center"
              value={newReport.cost_center_id}
              onChange={e => setNewReport({ ...newReport, cost_center_id: e.target.value })}
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
            onChange={e => setNewReport({ ...newReport, project_code: e.target.value.replace(/[^a-zA-Z0-9\s-]/g, '') })}
          />
          <div>
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
              Description / Justification <span className="text-red-500">*</span>
            </label>
            <textarea
              className="w-full px-3 py-2 text-sm rounded-lg bg-background dark:bg-black dark:text-white border border-border focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all duration-200"
              rows={3}
              placeholder="Provide a detailed justification for this expense claim..."
              value={newReport.justification}
              onChange={e => setNewReport({ ...newReport, justification: e.target.value.replace(/[^a-zA-Z0-9\s.,!?-]/g, '') })}
              required
            ></textarea>
          </div>
          <div className="pt-4 flex justify-end gap-2 border-t border-border">
            <Button type="button" variant="ghost" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={createReportMutation.isPending || !newReport.purpose.trim() || !newReport.justification.trim()}>Create Report</Button>
          </div>
        </form>
      </Dialog>


      {/* Right Column: Report Details & Receipts */}
      {selectedReportId && (() => {
        const report = expenses.find(r => Number(r.expense_report_id) === Number(selectedReportId));
        if (!report) return null;

        const isRejected = report.status === "Rejected";
        const isReturned = report.status === "Returned for Correction";
        const isApproved = report.status === "Approved" || report.status === "Closed";

        const isPendingManager = report.status === "Pending Manager Approval" || report.status === "Pending Approval" || report.status === "Corrected Claim";
        const isPendingFinance = report.status === "Pending Finance Manager Approval" || report.status === "Pending Finance Approval" || report.status === "Pending Finance Verification";


        const steps = [
          { name: "Draft", key: "draft" },
          { name: "Manager Approval", key: "manager" },
          { name: "Finance Approval", key: "finance" },
          { name: "Completed", key: "completed" }
        ];

        let currentStepIdx = 0;
        if (isPendingManager) currentStepIdx = 1;
        else if (isPendingFinance || report.status === "Payment Requested") currentStepIdx = 2;
        else if (isApproved) currentStepIdx = 3;

        return (
          <Dialog isOpen={true} onClose={() => setSelectedReportId(null)} title={report.purpose || "Untitled Expense"} maxWidthClass="max-w-2xl">
            <div className="flex flex-col space-y-8 mt-4">
              {/* Header Section */}
              <div className="flex items-center justify-between px-2">
                <div className="flex items-center gap-4">
                  <Badge variant={
                    report.status === 'Approved' || report.status === 'Closed' ? 'success' :
                      (report.status.includes('Rejected') || report.status.includes('Returned')) ? 'error' :
                        (report.status.includes('Pending') || report.status.includes('Review')) ? 'info' :
                          'neutral'
                  }>{report.status}</Badge>
                  <span className="text-sm text-muted-foreground font-medium">
                    Created: {new Date(report.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-black text-purple-600 dark:text-purple-400">
                    ${Number(report.total_amount).toFixed(2)}
                  </div>
                  <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mt-1">Verified Total</div>
                </div>
              </div>

              {/* Compact Progress Bar */}
              <div className="flex justify-between items-center px-8 py-6 relative">
                <div className="absolute top-1/2 left-10 right-10 h-0.5 bg-muted -z-10 -translate-y-1/2 rounded-full" />
                {(() => {
                  const requestorRoles = report.employee?.roles?.map((r: any) => r.role_name) || [];
                  const routesToCfo = requestorRoles.includes("Admin") || requestorRoles.includes("CEO") || requestorRoles.includes("Finance Manager") || requestorRoles.includes("Finance");
                  const routesToFinanceManager = requestorRoles.includes("CFO") || (requestorRoles.includes("Manager") && !routesToCfo);

                  let steps = ["Draft", "Submitted", "Manager", "Finance", "Payment", "Closed"];
                  if (routesToCfo) {
                    steps = ["Draft", "Submitted", "CFO", "Payment", "Closed"];
                  } else if (routesToFinanceManager) {
                    steps = ["Draft", "Submitted", "Finance Manager", "Payment", "Closed"];
                  }
                    
                  let currentIndex = 0;
                  if (report.status === "Draft") currentIndex = 0;
                  else if (report.status === "Corrected Claim") currentIndex = 1;
                  else if (report.status === "Pending Manager Approval") currentIndex = steps.indexOf("Manager") !== -1 ? steps.indexOf("Manager") : 1;
                  else if (report.status === "Pending Finance Approval" || report.status === "Pending Finance Manager Approval" || report.status === "Pending CFO Approval") {
                      if (steps.includes("CFO")) currentIndex = steps.indexOf("CFO");
                      else if (steps.includes("Finance Manager")) currentIndex = steps.indexOf("Finance Manager");
                      else currentIndex = steps.indexOf("Finance");
                  }
                  else if (report.status === "Payment Requested") currentIndex = steps.indexOf("Payment");
                  else if (report.status === "Closed" || report.status === "Approved") currentIndex = steps.indexOf("Closed");
                  else currentIndex = 1;

                  return steps.map((s, i) => {
                    const isCompleted = i < currentIndex;
                    const isRejected = report.status.includes("Reject") || report.status.includes("Return");
                    const isActive = i === currentIndex;

                    return (
                      <div key={s} className="flex flex-col items-center gap-2.5 relative group">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold z-10 transition-all shadow-sm
                            ${isCompleted
                            ? (isRejected && isActive ? 'bg-red-500 text-white shadow-red-500/20' : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-purple-500/20')
                            : (isActive ? 'border-2 border-blue-500 bg-background text-blue-500' : 'bg-muted border border-border text-muted-foreground')}`}
                        >
                          {i + 1}
                        </div>
                        <span className={`text-[10px] font-bold uppercase tracking-wider text-center w-20 leading-tight
                            ${isActive ? 'text-foreground' : 'text-muted-foreground'}`}>
                          {s}
                        </span>
                        {i < currentIndex && (
                          <div className="absolute top-3 left-6 w-[calc(100%+30px)] h-0.5 bg-gradient-to-r from-purple-500 to-pink-500 -z-10" />
                        )}
                      </div>
                    )
                  });
                })()}
              </div>

              {report.justification && (
                <div className="text-sm text-foreground/90 italic border-l-2 border-purple-500/50 pl-4 py-2 bg-muted/10 rounded-r-md mx-2">
                  "{report.justification}"
                </div>
              )}

              <div className="flex flex-wrap gap-6 text-sm text-muted-foreground font-medium bg-muted/20 p-4 rounded-xl border border-border/50 mx-2">
                {report.department_id && <span className="flex items-center gap-2"><Building className="w-4 h-4 text-purple-500/70" /> Dept: {report.department_id}</span>}
                {report.project_code && <span className="flex items-center gap-2"><Briefcase className="w-4 h-4 text-pink-500/70" /> Proj: {report.project_code}</span>}
              </div>

              {report.duplicate_flag && (
                <div className="bg-red-500/10 text-red-500 text-sm p-4 rounded-xl border border-red-500/20 flex items-center gap-3 mx-2">
                  <AlertCircle className="w-5 h-5 shrink-0" />
                  <span><strong>Warning:</strong> Duplicate receipts detected across other reports.</span>
                </div>
              )}
              {report.policy_flags && (
                <div className="bg-amber-500/10 text-amber-500 text-sm p-4 rounded-xl border border-amber-500/20 flex items-center gap-3 mx-2">
                  <AlertCircle className="w-5 h-5 shrink-0" />
                  <span><strong>Policy Flag:</strong> {report.policy_flags}</span>
                </div>
              )}

              {/* Unified Action Area */}
              {(report.status === "Draft" || (report.status === "Returned for Correction" && isOwner(report))) && (
                <div className="flex flex-col gap-6 pt-2">
                  <div className="p-6 bg-transparent rounded-xl border border-[#3E3E4A] border-dashed">
                    <div className="flex items-start gap-3 mb-4">
                      <Upload className="w-5 h-5 text-[#A78BFA]" />
                      <div>
                        <h4 className="text-sm font-semibold text-foreground">Upload Receipts</h4>
                        <p className="text-xs text-muted-foreground mt-1">Upload multiple receipts to build your report.</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-0 w-full mb-4">
                      <label className="cursor-pointer bg-[#2A2A35] hover:bg-[#333338] border border-[#3E3E4A] border-r-0 rounded-l-md px-4 py-2.5 text-sm font-medium text-[#A78BFA] transition-colors">
                        Choose File
                        <input id="receipt-upload" type="file" multiple accept="image/*,.pdf" className="hidden" onChange={(e) => handleFileUpload(e, report.expense_report_id)} disabled={uploading} />
                      </label>
                      <div className="flex-1 bg-[#23232C] border border-[#3E3E4A] rounded-r-md px-4 py-2.5 text-sm text-muted-foreground flex items-center">
                        {uploading ? "Extracting OCR..." : "No file chosen"}
                        {uploading && <RefreshCw className="w-4 h-4 text-[#A78BFA] animate-spin ml-auto" />}
                      </div>
                    </div>

                    <p className="text-xs text-muted-foreground">Accepted formats: JPG, PNG, PDF (Max size: 10MB each)</p>
                  </div>

                  <div className="flex justify-end gap-4 w-full">
                    <Button
                      size="default"
                      variant="outline"
                      className="text-sm font-semibold h-10 px-6 border-[#3E3E4A] hover:bg-[#2A2A35] rounded-md text-foreground"
                      onClick={() => {
                        setEditDetails({
                          purpose: report.purpose,
                          justification: report.justification || "",
                          department_id: report.department_id ? report.department_id.toString() : "",
                          cost_center_id: report.cost_center_id ? report.cost_center_id.toString() : "",
                          project_code: report.project_code || ""
                        });
                        setIsEditDetailsOpen(true);
                      }}
                    >
                      Edit Details
                    </Button>
                    <Button
                      size="default"
                      variant="primary"
                      className="text-sm font-bold h-10 px-6 bg-gradient-to-r from-[#A78BFA] to-[#F472B6] hover:opacity-90 border-0 rounded-md text-white shadow-none"
                      onClick={() => setIsReviewOpen(true)}
                      disabled={submitReportMutation.isPending || !report.receipts?.length}
                    >
                      Review & Submit
                    </Button>
                  </div>
                </div>
              )}
              {!isOwner(report) && report.status === "Draft" && (
                <div className="text-muted-foreground italic text-sm text-center p-4 bg-muted/30 rounded-xl mx-2">Draft report - Waiting for submission</div>
              )}


            {/* Receipts List */}
            <div className="mt-6 space-y-3">
              <h3 className="font-bold text-sm text-foreground flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
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
                    <div key={receipt.receipt_id} className={`flex flex-col md:flex-row gap-4 p-4 rounded-2xl border transition-all duration-200 shadow-apple-sm ${alert && (report.status === "Draft" || report.status === "Returned for Correction") ? 'border-amber-500/40 bg-amber-500/10' : 'apple-card'}`}>
                      {/* Apple Thumbnail Preview */}
                      <div
                        className="w-16 h-16 sm:w-20 sm:h-20 bg-muted/60 rounded-xl border border-border flex items-center justify-center overflow-hidden shrink-0 group relative shadow-inner cursor-pointer"
                        onClick={() => {
                            const fullUrl = receipt.image_path.startsWith('http') ? receipt.image_path : `${import.meta.env.VITE_API_URL.replace('/api/v1', '')}${receipt.image_path}`;
                            setPreviewReceiptUrl(fullUrl);
                        }}
                      >
                        {receipt.image_path ? (
                          <>
                            <img src={receipt.image_path.startsWith('http') ? receipt.image_path : `${import.meta.env.VITE_API_URL.replace('/api/v1', '')}${receipt.image_path}`} alt="Receipt" className="object-cover w-full h-full opacity-80 group-hover:opacity-100 transition-opacity" />
                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                              <Eye className="w-5 h-5 text-white" />
                            </div>
                          </>
                        ) : (
                          <FileText className="w-6 h-6 sm:w-8 sm:h-8 text-muted-foreground/50" />
                        )}
                      </div>

                      {/* Details */}
                      <div className="flex-1 flex flex-col justify-center min-w-0">
                        <div className="font-bold flex items-center gap-2 text-sm text-foreground truncate">
                          {receipt.merchant_name || 'QuickBite Restaurant'}
                          {alert && report.status === "Draft" && <span title="Low OCR confidence, please verify amount"><AlertCircle className="w-4 h-4 text-amber-500 shrink-0" /></span>}
                        </div>
                        <div className="text-xs text-muted-foreground flex flex-wrap items-center gap-x-3 gap-y-1 mt-1">
                          <span>Date: <strong className="text-foreground">{receipt.receipt_date || 'N/A'}</strong></span>
                          <span>Category: <strong className="text-foreground">{receipt.category || 'Uncategorized'}</strong></span>
                          <span className="flex items-center gap-1 bg-muted/50 px-2 py-0.5 rounded">
                            OCR Confidence: <span className={lowConfidence ? "text-amber-600 font-semibold" : "text-green-600 font-medium"}>{receipt.ocr_confidence}%</span>
                          </span>
                        </div>
                        {report.status !== "Draft" && (
                          <div className="text-[11px] text-muted-foreground mt-1.5 font-medium">
                            OCR Extracted: ${Number(receipt.ocr_amount).toFixed(2)}
                          </div>
                        )}
                      </div>

                      {/* Amount & Actions */}
                      <div className="flex items-center justify-end shrink-0 md:min-w-[160px] gap-2">
                        {editingReceiptId === receipt.receipt_id ? (
                          <div className="flex items-center gap-1.5 bg-muted/80 p-1.5 rounded-xl border border-border">
                            <div className="relative">
                              <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground text-xs font-bold">$</span>
                              <Input
                                type="number"
                                className="w-24 pl-6 pr-2 text-right font-bold h-8 text-xs bg-background rounded-lg"
                                value={editAmount}
                                onChange={e => setEditAmount(e.target.value)}
                                autoFocus
                              />
                            </div>
                            <Button size="sm" variant="primary" onClick={() => saveAmount(report.expense_report_id, receipt.receipt_id)} className="h-8 px-2.5 rounded-lg"><CheckCircle className="w-4 h-4" /></Button>
                            <Button size="sm" variant="ghost" onClick={() => setEditingReceiptId(null)} className="h-8 px-2 rounded-lg text-rose-500"><XCircle className="w-4 h-4" /></Button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <div
                              className={`flex flex-col items-end cursor-pointer rounded-xl px-3 py-1.5 transition-colors border ${alert && (report.status === "Draft" || report.status === "Returned for Correction") ? "border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20" : "border-transparent hover:bg-muted/60"}`}
                              onClick={() => { if (report.status === "Draft" || (report.status === "Returned for Correction" && isOwner(report))) handleEditAmount(receipt); }}
                              title={report.status === "Draft" || (report.status === "Returned for Correction" && isOwner(report)) ? "Click to correct amount" : ""}
                            >
                              <span className="text-xl font-extrabold text-foreground tracking-tight">
                                ${Number(receipt.verified_amount).toFixed(2)}
                              </span>
                              {(report.status === "Draft" || (report.status === "Returned for Correction" && isOwner(report))) && (
                                <span className="text-[9px] text-muted-foreground uppercase font-bold tracking-wider mt-0.5">
                                  {alert ? "Verify Amount" : "Click to Edit"}
                                </span>
                              )}
                            </div>

                            {report.status === "Draft" && (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-9 w-9 text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded"
                                title="Delete Receipt / OCR"
                                onClick={() => {
                                  if (window.confirm("Are you sure you want to delete this receipt?")) {
                                    deleteReceiptMutation.mutate({ reportId: report.expense_report_id, receiptId: receipt.receipt_id });
                                  }
                                }}
                                disabled={deleteReceiptMutation.isPending}
                              >
                                <Trash2 className="w-4.5 h-4.5" />
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </Dialog>
      );
    })()}


{/* Review & Submit Modal */ }
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

{/* Manager Action Modal */ }
<Dialog isOpen={managerAction.isOpen} onClose={() => setManagerAction({ isOpen: false, action: null, reportId: null })} title={managerAction.action === 'return' ? "Return to Employee" : "Reject Expense Claim"}>
  <div className="space-y-4">
    <p className="text-sm text-muted-foreground">Please provide a justification for this action. This will be visible to the employee.</p>
    <textarea
      className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background dark:bg-black dark:text-white focus:ring-2 focus:ring-primary focus:border-transparent"
      rows={4}
      placeholder="Enter your justification..."
      value={managerComments}
      onChange={e => setManagerComments(e.target.value)}
    />
    <div className="flex justify-end gap-2 pt-4 border-t border-border">
      <Button variant="ghost" onClick={() => setManagerAction({ isOpen: false, action: null, reportId: null })}>Cancel</Button>
      <Button
        disabled={!managerComments.trim() || managerActionMutation.isPending}
        onClick={() => {
          if (!isValidText(managerComments)) {
            toast.error("Please enter a valid justification (letters or numbers required).");
            return;
          }
          if (managerAction.reportId && managerAction.action) {
            managerActionMutation.mutate({ reportId: managerAction.reportId, action: managerAction.action, comments: managerComments });
            setManagerAction({ isOpen: false, action: null, reportId: null });
            setManagerComments("");
          }
        }}
        className={managerAction.action === 'reject' ? "bg-red-600 hover:bg-red-700 text-white" : ""}
      >
        {managerAction.action === 'return' ? "Return" : "Reject"}
      </Button>
    </div>
  </div>
</Dialog>

{/* Edit Details Modal */ }
<Dialog isOpen={isEditDetailsOpen} onClose={() => setIsEditDetailsOpen(false)} title="Edit Report Details">
  <form onSubmit={(e) => {
    e.preventDefault();
    if (selectedReportId) {
      const payload: any = {
        purpose: editDetails.purpose,
        justification: editDetails.justification,
        project_code: editDetails.project_code || null
      };
      if (editDetails.department_id) payload.department_id = parseInt(editDetails.department_id);
      else payload.department_id = null;
      if (editDetails.cost_center_id) payload.cost_center_id = parseInt(editDetails.cost_center_id);
      else payload.cost_center_id = null;

      updateReportMutation.mutate({ reportId: selectedReportId, payload });
    }
  }} className="space-y-4">
    <Input
      label="Business Purpose *"
      value={editDetails.purpose}
      onChange={e => setEditDetails({ ...editDetails, purpose: e.target.value.replace(/[^a-zA-Z0-9\s.,-]/g, '') })}
      required
    />
    <div className="grid grid-cols-2 gap-4">
      <Select
        label="Department"
        value={editDetails.department_id}
        onChange={e => setEditDetails({ ...editDetails, department_id: e.target.value })}
        options={[
          { label: "None", value: "" },
          ...departments.map((d: any) => ({ label: d.department_name, value: d.department_id.toString() }))
        ]}
      />
      <Select
        label="Cost Center"
        value={editDetails.cost_center_id}
        onChange={e => setEditDetails({ ...editDetails, cost_center_id: e.target.value })}
        options={[
          { label: "None", value: "" },
          ...costCenters.map((cc: any) => ({ label: cc.cost_center_name, value: cc.cost_center_id.toString() }))
        ]}
      />
    </div>
    <Input
      label="Project Code"
      value={editDetails.project_code}
      onChange={e => setEditDetails({ ...editDetails, project_code: e.target.value.replace(/[^a-zA-Z0-9\s-]/g, '') })}
    />
    <div>
      <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
        Description / Justification <span className="text-red-500">*</span>
      </label>
      <textarea
        className="w-full px-3 py-2 text-sm rounded-lg bg-background dark:bg-black dark:text-white border border-border focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all duration-200"
        rows={3}
        value={editDetails.justification}
        onChange={e => setEditDetails({ ...editDetails, justification: e.target.value.replace(/[^a-zA-Z0-9\s.,!?-]/g, '') })}
        required
      ></textarea>
    </div>
    <div className="pt-4 flex justify-end gap-2 border-t border-border">
      <Button type="button" variant="ghost" onClick={() => setIsEditDetailsOpen(false)}>Cancel</Button>
      <Button type="submit" disabled={updateReportMutation.isPending || !editDetails.purpose.trim() || !editDetails.justification.trim()}>Save Changes</Button>
    </div>
  </form>
</Dialog>
      <Dialog isOpen={!!previewReceiptUrl} onClose={() => setPreviewReceiptUrl(null)} title="Receipt Preview" maxWidthClass="max-w-4xl">
        <div className="flex items-center justify-center bg-black/10 dark:bg-black/50 rounded-xl overflow-hidden p-2 min-h-[50vh]">
          {previewReceiptUrl && (
            <img src={previewReceiptUrl} alt="Receipt Preview" className="max-w-full max-h-[80vh] object-contain rounded-lg" />
          )}
        </div>
      </Dialog>
    </div>
  );
};

export default Expenses;
