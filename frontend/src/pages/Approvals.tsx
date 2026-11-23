import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { ApprovalWorkflow } from "../types";
import { Button, Card, CardHeader, CardTitle, CardContent, Badge, StatusBadge, Skeleton, Dialog, Input, EmptyState } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import toast from "react-hot-toast";
import { formatDate, getErrorMessage, isValidText, resolveImageUrl, canViewAmount } from "../utils/helpers";
import { Check, X as XIcon, Eye, CheckCircle2, AlertTriangle } from "lucide-react";
import { ReimbursementDetailModal } from "../components/expenses/ReimbursementDetailModal";

type TabType = "Reimbursements" | "Requisitions" | "Asset Incidents";

export const Approvals: React.FC = () => {
  const { user, hasRole } = useAuth();
  const [workflows, setWorkflows] = useState<ApprovalWorkflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>("Reimbursements");
  const [statusFilter, setStatusFilter] = useState("All");

  useEffect(() => {
    setStatusFilter("All");
  }, [activeTab]);
  
  // Action state
  const [selectedWorkflow, setSelectedWorkflow] = useState<ApprovalWorkflow | null>(null);
  const [actionType, setActionType] = useState<"approve" | "reject" | "return" | "repair" | "replace" | null>(null);
  const [comment, setComment] = useState("");
  
  const [managerAssessment, setManagerAssessment] = useState("");
  const [managerComments, setManagerComments] = useState("");
  const [adminResolution, setAdminResolution] = useState("");
  const [adminComments, setAdminComments] = useState("");
  const [physicalInspectionDone, setPhysicalInspectionDone] = useState(true);

  // Requisition inventory check state
  const [inventoryCheck, setInventoryCheck] = useState<any>(null);
  const [loadingInvCheck, setLoadingInvCheck] = useState(false);
  const [initiateProcurementChoice, setInitiateProcurementChoice] = useState<boolean | null>(true);
  const [selectedAllocateAssetId, setSelectedAllocateAssetId] = useState<number | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [selectedReportDetails, setSelectedReportDetails] = useState<any>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  const handleOpenPrReview = async (wf: any, preferredAction: "approve" | "reject" | "return" = "approve") => {
    setSelectedWorkflow(wf);
    setActionType(preferredAction);
    setComment("");
    setPhysicalInspectionDone(true);
    setInventoryCheck(null);
    setInitiateProcurementChoice(true);
    setSelectedAllocateAssetId(null);

    if (wf.entity_type === "PurchaseRequisition") {
      setLoadingInvCheck(true);
      try {
        const res = await api.get(`/pr/${wf.entity_id}/inventory-check`);
        setInventoryCheck(res.data);
        if (res.data?.case === "A") {
          const firstAsset = res.data.items?.[0]?.available_assets?.[0];
          if (firstAsset) setSelectedAllocateAssetId(firstAsset.asset_id);
          setInitiateProcurementChoice(null);
        } else {
          setInitiateProcurementChoice(true);
        }
      } catch (err) {
        console.error("Failed to check inventory:", err);
      } finally {
        setLoadingInvCheck(false);
      }
    }
  };

  const handleViewDetails = async (reportId: number) => {
    setSelectedReportId(reportId);
    setLoadingDetails(true);
    try {
      const res = await api.get(`/expenses/${reportId}`);
      setSelectedReportDetails(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDetails(false);
    }
  };


  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const response = await api.get("/approvals");
      setWorkflows(response.data);
    } catch (err) {
      console.error("Failed to load approval workflows:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const handleAction = async () => {
    if (!selectedWorkflow || !actionType) return;
    
    if ((actionType === 'reject' || actionType === 'return') && !isValidText(comment)) {
      toast.error("Please enter a valid reason or instruction (letters or numbers required).");
      return;
    }

    setIsSubmitting(true);
    try {
      let endpoint = "";
      let payload: any = { comments: comment };
      

      if (selectedWorkflow.entity_type === "ExpenseReport") {
        endpoint = `/expenses/${selectedWorkflow.entity_id}/${actionType}`;
      } else if (selectedWorkflow.entity_type === "VendorInvoice") {
        endpoint = `/invoices/${selectedWorkflow.entity_id}/${actionType}`;
      } else if (selectedWorkflow.entity_type === "AssetIncident") {
        endpoint = `/asset-incidents/${selectedWorkflow.entity_id}/action`;
        let actStr = "Approve";
        if (actionType === "reject") actStr = "Reject";
        else if (actionType === "return") actStr = "Return for Correction";
        else if (actionType === "complete_procurement") actStr = "Complete Procurement Replacement";
        else if (actionType === "complete_repair") actStr = "Complete Repair";
        else if (actionType === "assign_replacement") actStr = "Assign Replacement";
        
        payload = { 
            action: actStr, 
            resolution: comment,
            manager_inspection_assessment: managerAssessment,
            manager_inspection_comments: managerComments,
            admin_inspection_resolution: adminResolution,
            admin_comments: adminComments
        };
      } else {
        endpoint = `/pr/${selectedWorkflow.entity_id}/${actionType}`;
        payload = {
          comments: comment,
          physical_inspection_done: physicalInspectionDone,
          initiate_procurement: initiateProcurementChoice,
          allocate_asset_id: selectedAllocateAssetId
        };
      }

      await api.post(endpoint, payload);
      toast.success(`Workflow successfully ${actionType}d!`);
      
      setSelectedWorkflow(null);
      setActionType(null);
      setComment("");
      
      setManagerAssessment("");
      setManagerComments("");
      setAdminResolution("");
      setAdminComments("");

      fetchWorkflows();
      
      // Redirect admin to asset inventory after processing an asset incident
      const userRoles = user?.roles?.map((r: any) => r.role_name) || [];
      const isAdmin = userRoles.includes("Admin") || userRoles.includes("SuperAdmin") || userRoles.includes("IT");
      if (isAdmin && selectedWorkflow.entity_type === "AssetIncident" && ["approve", "complete_repair", "assign_replacement", "complete_procurement"].includes(actionType)) {
          window.location.href = "/assets";
      }

    } catch (err: any) {
      toast.error(getErrorMessage(err, "Failed to process workflow action."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const getWorkflowsForTab = () => {
    return workflows.filter((wf: any) => {
      // Exclude 0.00 items from approval inbox for expenses and invoices
      const amt = Number(wf.amount || wf.total_amount || wf.estimated_cost || 0);
      if (wf.entity_type === "ExpenseReport" || wf.entity_type === "VendorInvoice") {
        if (amt <= 0) return false;
      }
      if (wf.status === "Draft") return false; // Exclude drafts from Approvals Inbox
      if (activeTab === "Requisitions") return wf.entity_type === "PurchaseRequisition";
      if (activeTab === "Reimbursements") return wf.entity_type === "ExpenseReport";
      if (activeTab === "Asset Incidents") return wf.entity_type === "AssetIncident";
      return false;
    });
  };

  const isSubmittedStatus = (status: string) => {
    if (!status) return false;
    return status.includes("Pending") || status === "Corrected Claim" || status === "Payment Requested" || status === "Approved for Payment" || status === "Finance Verified" || status === "Submitted" || status === "Under Review" || status === "Reported";
  };

  const isApprovedStatus = (status: string) => {
    if (!status) return false;
    if (status === "Approved for Payment") return false;
    return ["Approved", "Paid", "Closed", "Completed", "Active", "Success", "Verified"].includes(status) || status.includes("Approved") || status.includes("Resolved");
  };

  const getFilteredWorkflows = () => {
    return getWorkflowsForTab()
      .filter((r: any) => {
        if (statusFilter === "All") return true;
        if (statusFilter === "Submitted") return isSubmittedStatus(r.status);
        if (statusFilter === "Approved") return isApprovedStatus(r.status);
        if (statusFilter === "Rejected") return ["Rejected", "Cancelled", "Inactive", "Failed", "Error"].includes(r.status) || r.status.includes("Rejected");
        if (statusFilter === "Return for Correction") return r.status === "Returned for Correction" || r.status === "Returned";
        return r.status === statusFilter;
      })
      .sort((a: any, b: any) => {
        // Priority 1: Actionable by current user
        if (a.can_approve && !b.can_approve) return -1;
        if (!a.can_approve && b.can_approve) return 1;

        // Priority 2: "Payment Requested" or "Approved for Payment"
        const isPaymentPendingA = a.status === "Payment Requested" || a.status === "Approved for Payment";
        const isPaymentPendingB = b.status === "Payment Requested" || b.status === "Approved for Payment";
        if (isPaymentPendingA && !isPaymentPendingB) return -1;
        if (!isPaymentPendingA && isPaymentPendingB) return 1;

        const sA = (a.status || "").toLowerCase();
        const sB = (b.status || "").toLowerCase();
        const isPendingA = sA.includes("pending") || sA.includes("review");
        const isPendingB = sB.includes("pending") || sB.includes("review");
        
        // Priority 3: pending approval workflows come first
        if (isPendingA && !isPendingB) return -1;
        if (!isPendingA && isPendingB) return 1;
        
        // Sort according to time of creation (newest first)
        const timeA = new Date(a.created_at || a.submission_date || a.date || 0).getTime();
        const timeB = new Date(b.created_at || b.submission_date || b.date || 0).getTime();
        return timeB - timeA;
      });
  };

  const filteredWorkflows = getFilteredWorkflows();
  const currentTabWorkflows = getWorkflowsForTab();
  const subTabCounts: Record<string, number> = {
    All: currentTabWorkflows.length,
    Submitted: currentTabWorkflows.filter((r: any) => isSubmittedStatus(r.status)).length,
    Approved: currentTabWorkflows.filter((r: any) => isApprovedStatus(r.status)).length,
    Rejected: currentTabWorkflows.filter((r: any) => ["Rejected", "Cancelled", "Inactive", "Failed", "Error"].includes(r.status) || r.status.includes("Rejected")).length,
    "Return for Correction": currentTabWorkflows.filter((r: any) => r.status === "Returned for Correction" || r.status === "Returned").length,
  };

  // Incident Details Modal state
  const [selectedIncident, setSelectedIncident] = useState<any | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Approvals Inbox</h1>
        <p className="text-xs text-muted-foreground mt-1">Review and sign off on pending workflows.</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-border">
        {(["Reimbursements", "Requisitions", "Asset Incidents"] as TabType[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-semibold transition-colors border-b-2 ${
              activeTab === tab 
                ? "border-primary text-primary" 
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Filters & Controls */}
      <div className="flex items-center space-x-2 bg-muted/40 p-1.5 rounded-xl w-fit border border-border/50">
        {["All", "Submitted", "Approved", "Rejected", "Return for Correction"].map((status) => (
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
            <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
              statusFilter === status ? "bg-primary-foreground/20 text-primary-foreground font-bold" : "bg-muted text-muted-foreground"
            }`}>
              {subTabCounts[status] || 0}
            </span>
          </button>
        ))}
      </div>

      {/* Table/Cards View */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Skeleton className="h-40 w-full rounded-lg" />
          <Skeleton className="h-40 w-full rounded-lg" />
          <Skeleton className="h-40 w-full rounded-lg" />
        </div>
      ) : filteredWorkflows.length === 0 ? (
        <Card className="bg-transparent border-dashed">
          <CardContent className="py-12">
             <EmptyState title={`No pending ${activeTab.toLowerCase()}.`} description="You're all caught up!" />
          </CardContent>
        </Card>
      ) : activeTab === "Reimbursements" || activeTab === "Requisitions" ? (
        <div className="overflow-x-auto rounded-xl border border-border shadow-sm">
          <table className="w-full text-left text-sm text-foreground">
            <thead className="bg-muted text-muted-foreground uppercase text-xs font-bold tracking-wider">
              <tr>
                <th className="p-4">ID</th>
                <th className="p-4">Employee</th>
                <th className="p-4">Purpose</th>
                {canViewAmount(user) && <th className="p-4">Total Amount</th>}
                <th className="p-4">Status</th>
                <th className="p-4">Date Created</th>
                <th className="p-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border bg-card">
              {filteredWorkflows.map((wf) => (
                <tr key={wf.workflow_id} className="hover:bg-muted/50 transition-colors">
                  <td className="p-4 font-semibold">{activeTab === "Reimbursements" ? "EXP-" : "PR-"}{wf.entity_id}</td>
                  <td className="p-4 font-medium">
                    {wf.requestor_name && wf.requestor_name !== "Test User" 
                      ? wf.requestor_name 
                      : (wf.requestor_email ? wf.requestor_email.split('@')[0].split('.').map((s: string) => s.charAt(0).toUpperCase() + s.slice(1)).join(' ') : "Employee")} <span className="text-muted-foreground text-xs font-normal">({[(wf as any).requestor_department, (wf as any).requestor_role].filter(Boolean).join(" - ") || 'Employee'})</span>
                  </td>
                  <td className="p-4 font-medium max-w-[200px] truncate" title={wf.title}>{wf.title?.replace('Expense: ', '')}</td>
                  {canViewAmount(user) && (
                    <td className="p-4 font-bold tracking-tight">₹{Number(wf.amount || 0).toFixed(2)}</td>
                  )}
                  <td className="p-4">
                    <StatusBadge status={wf.status} />
                  </td>
                  <td className="p-4 text-xs text-muted-foreground">{new Date(wf.created_at || Date.now()).toLocaleDateString()}</td>
                  <td className="p-4 flex items-center gap-2">
                    {wf.can_approve ? (
                      <div className="flex items-center gap-1.5">
                        <Button 
                          size="sm" 
                          variant="primary"
                          onClick={() => {
                             if (activeTab === "Reimbursements") {
                               handleViewDetails(wf.entity_id);
                             } else {
                               handleOpenPrReview(wf, "approve");
                             }
                          }}
                          className="gap-1.5 bg-[#0f172a] text-white hover:bg-slate-800"
                        >
                          Review & Action
                        </Button>
                        {activeTab === "Requisitions" && (
                          <>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleOpenPrReview(wf, "return")}
                              className="text-amber-500 hover:text-amber-600 hover:bg-amber-500/10 px-2 text-xs"
                              title="Return for Correction"
                            >
                              Return
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleOpenPrReview(wf, "reject")}
                              className="text-rose-500 hover:text-rose-600 hover:bg-rose-500/10 px-2 text-xs"
                              title="Reject"
                            >
                              Reject
                            </Button>
                          </>
                        )}
                      </div>
                    ) : (
                      <Button 
                        size="sm" 
                        variant="view"
                        onClick={() => {
                          if (activeTab === "Reimbursements") {
                            handleViewDetails(wf.entity_id);
                          } else {
                            handleOpenPrReview(wf, "approve");
                          }
                        }}
                        className="gap-1.5"
                      >
                        <Eye className="w-3.5 h-3.5" /> View
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : activeTab === "Asset Incidents" ? (
        <div className="overflow-x-auto rounded-xl border border-border shadow-sm">
          <table className="w-full text-left text-sm text-foreground">
            <thead className="bg-muted text-muted-foreground uppercase text-xs font-bold tracking-wider">
              <tr>
                <th className="p-4">ID</th>
                <th className="p-4">Reported By</th>
                <th className="p-4">Issue</th>
                <th className="p-4">Reported Date</th>
                <th className="p-4">Status</th>
                <th className="p-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border bg-card">
              {filteredWorkflows.map((wf) => (
                <tr key={wf.workflow_id} className="hover:bg-muted/50 transition-colors">
                  <td className="p-4 font-semibold">INC-{wf.entity_id}</td>
                  <td className="p-4 font-medium">
                    {wf.requestor_name && wf.requestor_name !== "Test User" 
                      ? wf.requestor_name 
                      : (wf.requestor_email ? wf.requestor_email.split('@')[0].split('.').map((s: string) => s.charAt(0).toUpperCase() + s.slice(1)).join(' ') : "Employee")} <span className="text-muted-foreground text-xs font-normal">({[(wf as any).requestor_department, (wf as any).requestor_role].filter(Boolean).join(" - ") || 'Employee'})</span>
                  </td>
                  <td className="p-4 font-medium max-w-[250px] truncate" title={wf.title}>{wf.title}</td>
                  <td className="p-4 text-xs text-muted-foreground">{new Date(wf.created_at || Date.now()).toLocaleDateString()}</td>
                  <td className="p-4">
                    <StatusBadge status={wf.status} />
                  </td>
                  <td className="p-4 flex items-center gap-2">
                    {wf.can_approve ? (
                      <Button 
                        size="sm" 
                        variant="primary"
                        onClick={() => setSelectedIncident(wf)}
                        className="gap-1.5 bg-[#0f172a] text-white hover:bg-slate-800"
                      >
                        Need Approval
                      </Button>
                    ) : (
                      <Button 
                        size="sm" 
                        variant="view"
                        onClick={() => setSelectedIncident(wf)}
                        className="gap-1.5"
                      >
                        <Eye className="w-3.5 h-3.5" /> View
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredWorkflows.map(wf => (
            <Card key={wf.workflow_id} className="flex flex-col">
              <CardHeader className="pb-3 flex flex-col items-start gap-2">
                <div className="w-full flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-1">
                      {wf.entity_type === "AssetIncident" ? "ASSET INCIDENT" : wf.entity_type.replace(/([A-Z])/g, ' $1').trim()} #{wf.entity_id}
                    </span>
                    <CardTitle className="text-base">{wf.workflow_step || (wf.entity_type === 'AssetIncident' ? 'Incident Review' : `${wf.entity_type.replace(/([A-Z])/g, ' $1').trim()} Step`)}</CardTitle>
                  </div>
                  <StatusBadge status={wf.status} />
                </div>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col justify-between pt-0 space-y-4">
                <div className="text-sm space-y-3 mt-2">
                  <div>
                    <span className="font-semibold text-foreground text-base">{wf.title || "Untitled Request"}</span>
                  </div>
                  {wf.justification && (
                    <div>
                      <span className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Issue Description</span>
                      <p className="text-muted-foreground italic line-clamp-2">{wf.justification}</p>
                    </div>
                  )}
                  {wf.reason && (
                    <div>
                      <span className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Reason / Justification</span>
                      <p className="text-muted-foreground line-clamp-2">{wf.reason}</p>
                    </div>
                  )}
                  <div className="flex justify-between items-center bg-muted/40 p-2 rounded-lg border text-xs">
                    <span className="text-muted-foreground">Reported By:</span>
                    <span className="font-semibold">{wf.requestor_name || `User ${wf.requestor_id}`}</span>
                  </div>
                  <div className="flex justify-between items-center bg-muted/40 p-2 rounded-lg border text-xs">
                    <span className="text-muted-foreground">Submission Date:</span>
                    <span>{formatDate(wf.created_at)}</span>
                  </div>
                  {wf.manager_inspection_assessment && (
                    <div className="bg-primary/5 p-2.5 rounded-lg border border-primary/20 text-xs space-y-1">
                      <span className="font-bold text-primary block">Manager Assessment: {wf.manager_inspection_assessment}</span>
                      {wf.manager_inspection_comments && <p className="text-muted-foreground italic">"{wf.manager_inspection_comments}"</p>}
                    </div>
                  )}
                  {wf.admin_inspection_resolution && (
                    <div className="bg-emerald-500/5 p-2.5 rounded-lg border border-emerald-500/20 text-xs space-y-1">
                      <span className="font-bold text-emerald-600 block">Admin Resolution: {wf.admin_inspection_resolution}</span>
                      {wf.admin_comments && <p className="text-muted-foreground italic">"{wf.admin_comments}"</p>}
                    </div>
                  )}
                </div>
                
                {wf.entity_type === "AssetIncident" && (
                  <Button 
                    size="sm" 
                    variant="outline" 
                    className="w-full gap-1.5 text-xs font-semibold"
                    onClick={() => setSelectedIncident(wf)}
                  >
                    <Eye className="w-3.5 h-3.5" /> View Full Incident
                  </Button>
                )}

                {/* Approver Actions: Approve | Return for Correction | Reject */}
                {wf.can_approve && ["Submitted", "Reported", "Manager Approved"].includes(wf.status) && (
                  <div className="flex space-x-2 pt-4 border-t border-border">
                    <Button 
                      variant="success" 
                      className="flex-1 font-bold shadow-apple-sm text-xs"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("approve"); }}
                    >
                      <Check className="w-3.5 h-3.5 mr-1" />
                      <span>Approve</span>
                    </Button>
                    <Button 
                      variant="warning" 
                      className="flex-1 font-bold shadow-apple-sm border border-yellow-500 bg-yellow-500/10 text-yellow-600 hover:bg-yellow-500 hover:text-white transition-colors text-xs"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("return"); }}
                    >
                      <span>Return</span>
                    </Button>
                    <Button 
                      variant="danger" 
                      className="flex-1 font-bold shadow-apple-sm text-xs"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("reject"); }}
                    >
                      <XIcon className="w-3.5 h-3.5 mr-1" />
                      <span>Reject</span>
                    </Button>
                  </div>
                )}
                
                {wf.status === "Admin Approved" && wf.entity_type === "AssetIncident" && (
                  <div className="flex space-x-2 pt-4 border-t border-border">
                    {wf.admin_inspection_resolution === "Repair Required" ? (
                      <Button 
                        variant="success" 
                        className="flex-1 font-bold shadow-apple-sm text-xs"
                        onClick={() => { setSelectedWorkflow(wf); setActionType("complete_repair" as any); }}
                      >
                        <span>Complete Repair</span>
                      </Button>
                    ) : (
                      <>
                        <Button 
                          variant="info" 
                          className="flex-1 font-bold shadow-apple-sm text-xs"
                          onClick={() => { setSelectedWorkflow(wf); setActionType("assign_replacement" as any); }}
                        >
                          <span>Assign Replacement</span>
                        </Button>
                        <Button 
                          variant="outline" 
                          className="flex-1 font-bold shadow-apple-sm text-xs"
                          onClick={() => { setSelectedWorkflow(wf); setActionType("complete_procurement" as any); }}
                        >
                          <span>Trigger Procurement</span>
                        </Button>
                      </>
                    )}
                  </div>
                )}

                {wf.status === "Waiting for Procurement" && wf.entity_type === "AssetIncident" && (
                  <div className="flex space-x-2 pt-4 border-t border-border">
                    <Button 
                      variant="success" 
                      className="flex-1 font-bold shadow-apple-sm text-xs"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("assign_replacement" as any); }}
                    >
                      <span>Assign Received Asset</span>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Action Dialog */}
      <Dialog 
        isOpen={!!selectedWorkflow} 
        onClose={() => { 
          setSelectedWorkflow(null); 
          setActionType(null); 
          setComment(""); 
          setManagerAssessment("");
          setManagerComments("");
          setAdminResolution("");
          setAdminComments("");
        }}
        title={`${actionType === "approve" ? "Approve" : actionType === "reject" ? "Reject" : actionType === "return" ? "Return for Correction" : actionType === "complete_repair" ? "Complete Repair" : actionType === "assign_replacement" ? "Assign Replacement" : "Trigger Procurement"} ${selectedWorkflow?.entity_type} #${selectedWorkflow?.entity_id}`}
      >
        <div className="space-y-4">
          
          {["Submitted", "Reported"].includes(selectedWorkflow?.status || "") && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && (
            <div className="space-y-4 p-4 bg-muted/30 rounded-xl border border-border/50">
               <div>
                 <label className="block text-sm font-semibold mb-1">
                   Inspection / Resolution Assessment <span className="text-red-500">*</span>
                 </label>
                 <p className="text-xs text-muted-foreground mb-2">Record your physical inspection assessment with the employee before approving.</p>
                 <select 
                   className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" 
                   value={managerAssessment} 
                   onChange={(e) => setManagerAssessment(e.target.value)}
                   required
                 >
                   <option value="">Select Assessment Outcome</option>
                   <option value="No Action Required">No Action Required</option>
                   <option value="Repair Required">Repair Required</option>
                   <option value="Replacement Required">Replacement Required</option>
                   <option value="Further Inspection Required">Further Inspection Required</option>
                 </select>
               </div>
               <div>
                 <label className="block text-sm font-semibold mb-1">Manager Inspection Comments</label>
                 <Input 
                   value={managerComments} 
                   onChange={(e) => setManagerComments(e.target.value)} 
                   placeholder="Physical inspection findings, device condition, observations..." 
                 />
               </div>
            </div>
          )}

          {selectedWorkflow?.status === "Manager Approved" && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && (
            <div className="space-y-4 p-4 bg-muted/30 rounded-xl border border-border/50">
               <div>
                 <label className="block text-sm font-semibold mb-1">
                   Admin Inspection / Resolution <span className="text-red-500">*</span>
                 </label>
                 <p className="text-xs text-muted-foreground mb-2">Determine the final resolution following technical/inventory review.</p>
                 <select 
                   className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" 
                   value={adminResolution} 
                   onChange={(e) => setAdminResolution(e.target.value)}
                   required
                 >
                   <option value="">Select Resolution</option>
                   <option value="Repair Required">Repair Required</option>
                   <option value="Replacement Required">Replacement Required</option>
                   <option value="Further Inspection Required">Further Inspection Required</option>
                   <option value="No Replacement Required">No Replacement Required</option>
                 </select>
               </div>
               <div>
                 <label className="block text-sm font-semibold mb-1">Admin Comments / Resolution Notes</label>
                 <Input 
                   value={adminComments} 
                   onChange={(e) => setAdminComments(e.target.value)} 
                   placeholder="Technical findings, inventory availability, next steps..." 
                 />
               </div>
            </div>
          )}

          {/* Requisition Workflow Review UI */}
          {selectedWorkflow?.entity_type === "PurchaseRequisition" && (
            <div className="space-y-4">
              {/* Requisition Summary Card */}
              <div className="p-3.5 rounded-xl bg-muted/40 border border-border/60 text-xs space-y-1.5">
                <div className="flex justify-between items-center font-bold">
                  <span>PR #{selectedWorkflow.entity_id} — {selectedWorkflow.title}</span>
                  <StatusBadge status={selectedWorkflow.status} />
                </div>
                <div className="text-muted-foreground flex justify-between">
                  <span>Requestor: <strong className="text-foreground">{selectedWorkflow.requestor_name}</strong></span>
                  {canViewAmount(user) && (
                    <span>Estimated Total: <strong className="text-foreground">₹{Number(selectedWorkflow.amount || 0).toFixed(2)}</strong></span>
                  )}
                </div>
              </div>

              {/* Action Mode Selector */}
              <div className="flex rounded-lg bg-muted p-1 gap-1 text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setActionType("approve")}
                  className={`flex-1 py-1.5 px-3 rounded-md transition-all ${
                    actionType === "approve"
                      ? "bg-[#0071E3] text-white shadow-sm font-bold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Approve / Process
                </button>
                <button
                  type="button"
                  onClick={() => setActionType("return")}
                  className={`flex-1 py-1.5 px-3 rounded-md transition-all ${
                    actionType === "return"
                      ? "bg-amber-600 text-white shadow-sm font-bold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Return for Correction
                </button>
                <button
                  type="button"
                  onClick={() => setActionType("reject")}
                  className={`flex-1 py-1.5 px-3 rounded-md transition-all ${
                    actionType === "reject"
                      ? "bg-rose-600 text-white shadow-sm font-bold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Reject
                </button>
              </div>

              {actionType === "approve" && (
                <div className="space-y-3">
                  {/* Step 1: Manager Review */}
                  {(selectedWorkflow.status.includes("Manager") || hasRole("Manager")) && !selectedWorkflow.status.includes("Finance Manager") && !selectedWorkflow.status.includes("Admin") && (
                    <div className="space-y-3 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30">
                      <div className="flex items-center gap-2 text-xs font-bold text-amber-500">
                        <CheckCircle2 className="w-4 h-4" /> Manager Review & Physical Inspection
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Approving forwards the requisition to Admin for inventory verification.
                      </p>
                      <div className="flex items-center gap-2.5 pt-1">
                        <input
                          type="checkbox"
                          id="pr_physical_inspection_done"
                          checked={physicalInspectionDone}
                          onChange={(e) => setPhysicalInspectionDone(e.target.checked)}
                          className="w-4 h-4 rounded border-border text-primary focus:ring-primary cursor-pointer"
                        />
                        <label htmlFor="pr_physical_inspection_done" className="text-xs font-semibold cursor-pointer text-foreground select-none">
                          Physical inspection / requirement verification completed with employee
                        </label>
                      </div>
                    </div>
                  )}

                  {/* Step 2: Admin Inventory Verification */}
                  {(selectedWorkflow.status.includes("Admin") || hasRole("Admin")) && !selectedWorkflow.status.includes("Finance Manager") && (
                    <div className="space-y-3">
                      {loadingInvCheck ? (
                        <div className="p-4 rounded-xl border border-border/60 bg-muted/30 text-xs text-muted-foreground animate-pulse text-center">
                          Checking live inventory availability...
                        </div>
                      ) : inventoryCheck ? (
                        inventoryCheck.case === "A" ? (
                          /* Case A: Stock > 4 -> Direct Inventory Assignment */
                          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-2.5">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-emerald-500 flex items-center gap-1.5">
                                <CheckCircle2 className="w-4 h-4" /> Case A: Asset Availability &gt; 4
                              </span>
                              <Badge variant="success">
                                {inventoryCheck.available_count} Units Available
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground leading-relaxed">
                              Requested Asset: <strong className="text-foreground">{inventoryCheck.items?.[0]?.item_name || selectedWorkflow.title}</strong>.
                              Because inventory availability is <strong>more than 4 units</strong>, Admin approval will <strong>assign the requested asset directly to the employee</strong> and the requisition process will end here (no procurement / RFQ needed).
                            </p>
                          </div>
                        ) : (
                          /* Case B: Stock <= 4 or unavailable -> Prompt Admin */
                          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-3">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-amber-500 flex items-center gap-1.5">
                                <AlertTriangle className="w-4 h-4" /> Case B: Inventory Low or Unavailable (≤ 4 units)
                              </span>
                              <Badge variant="warning">
                                {inventoryCheck.available_count} Units Available
                              </Badge>
                            </div>
                            <div className="p-3 bg-background/80 rounded-lg border border-border/60 space-y-2">
                              <p className="text-xs font-semibold text-foreground">
                                Asset: {inventoryCheck.items?.[0]?.item_name || selectedWorkflow.title} (Available: {inventoryCheck.available_count})
                              </p>
                              <p className="text-xs text-muted-foreground">
                                Send a procurement request to the <strong>Finance Manager</strong>?
                              </p>
                              <div className="flex flex-col gap-2 pt-1">
                                <label className="flex items-center gap-2 cursor-pointer text-xs font-medium">
                                  <input
                                    type="radio"
                                    name="initiate_procurement"
                                    checked={initiateProcurementChoice === true}
                                    onChange={() => setInitiateProcurementChoice(true)}
                                    className="text-primary focus:ring-primary"
                                  />
                                  <span><strong>Yes</strong> — Forward procurement request to Finance Manager</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer text-xs font-medium">
                                  <input
                                    type="radio"
                                    name="initiate_procurement"
                                    checked={initiateProcurementChoice === false}
                                    onChange={() => setInitiateProcurementChoice(false)}
                                    className="text-primary focus:ring-primary"
                                  />
                                  <span><strong>No</strong> — Do not initiate procurement</span>
                                </label>
                              </div>
                            </div>
                          </div>
                        )
                      ) : null}
                    </div>
                  )}

                  {/* Step 3: Finance Manager Procurement Initiation */}
                  {(selectedWorkflow.status.includes("Finance Manager") || hasRole("Finance Manager")) && (
                    <div className="p-4 rounded-xl bg-teal-500/10 border border-teal-500/30 space-y-2.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-teal-500 flex items-center gap-1.5">
                          <CheckCircle2 className="w-4 h-4" /> Finance Manager: Procurement Initiation
                        </span>
                        <Badge variant="info">Procurement Forwarded by Admin</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        Admin verified inventory is low/unavailable and forwarded this purchase request for: <strong className="text-foreground">{selectedWorkflow.title}</strong>. Initiating approves the requisition for RFQ vendor bidding.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {actionType === "return" && (
                <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-muted-foreground space-y-1">
                  <div className="font-bold text-amber-500 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" /> Return for Correction
                  </div>
                  <p>Send the requisition back to the employee. Please provide mandatory instructions explaining what needs correction.</p>
                </div>
              )}

              {actionType === "reject" && (
                <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-muted-foreground space-y-1">
                  <div className="font-bold text-rose-500 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" /> Reject Requisition
                  </div>
                  <p>Requisition will be permanently rejected. Please provide a mandatory reason.</p>
                </div>
              )}
            </div>
          )}

          {actionType === "approve" && !["ExpenseReport", "VendorInvoice", "AssetIncident", "PurchaseRequisition"].includes(selectedWorkflow?.entity_type || "") && (
            <div className="flex items-center gap-2.5 p-3 rounded-xl bg-muted/40 border border-border/60">
              <input
                type="checkbox"
                id="pr_physical_inspection_done"
                checked={physicalInspectionDone}
                onChange={(e) => setPhysicalInspectionDone(e.target.checked)}
                className="w-4 h-4 rounded border-border text-primary focus:ring-primary cursor-pointer"
              />
              <label htmlFor="pr_physical_inspection_done" className="text-xs font-semibold cursor-pointer text-foreground select-none">
                Physical inspection / requirement verification completed with employee
              </label>
            </div>
          )}

          {(actionType === 'reject' || actionType === 'return' || actionType === 'approve' || actionType === 'complete_repair' || actionType === 'assign_replacement') && (
            <div>
              <label className="block text-sm font-semibold mb-1">
                {actionType === 'reject' ? 'Rejection Reason *' : actionType === 'return' ? 'Correction Instructions *' : 'Resolution / Notes'}
              </label>
              <Input 
                value={comment} 
                onChange={(e) => setComment(e.target.value)} 
                placeholder={(actionType === 'reject' || actionType === 'return') ? "Mandatory reason..." : "Optional notes..."} 
                required={actionType === 'reject' || actionType === 'return'}
              />
            </div>
          )}

          <div className="flex justify-end space-x-2 pt-3 border-t border-border">
            <Button variant="ghost" onClick={() => { 
              setSelectedWorkflow(null); 
              setActionType(null); 
              setManagerAssessment("");
              setManagerComments("");
              setAdminResolution("");
              setAdminComments("");
              setInventoryCheck(null);
            }}>
              Cancel
            </Button>
            <Button 
              variant={actionType === "approve" ? "success" : actionType === "reject" ? "danger" : actionType === "return" ? "warning" : "primary"} 
              onClick={handleAction} 
              disabled={
                isSubmitting || 
                ((actionType === "reject" || actionType === "return") && !comment.trim()) || 
                (["Submitted", "Reported"].includes(selectedWorkflow?.status || "") && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && !managerAssessment) ||
                (selectedWorkflow?.status === "Manager Approved" && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && !adminResolution) ||
                (selectedWorkflow?.entity_type === "PurchaseRequisition" && actionType === "approve" && selectedWorkflow?.status?.includes("Admin") && inventoryCheck?.case === "B" && initiateProcurementChoice === false)
              }
            >
              {isSubmitting ? "Processing..." : 
                selectedWorkflow?.entity_type === "PurchaseRequisition" && actionType === "approve" ? (
                  selectedWorkflow.status.includes("Admin") ? (
                    inventoryCheck?.case === "A" ? "Approve & Assign Asset Directly" :
                    initiateProcurementChoice === false ? "Procurement Declined" :
                    "Confirm & Forward to Finance Manager"
                  ) : selectedWorkflow.status.includes("Finance Manager") ? (
                    "Initiate Procurement Workflow"
                  ) : "Approve & Forward to Admin"
                ) : `Confirm ${actionType === "approve" ? "Approval" : actionType === "reject" ? "Rejection" : actionType === "return" ? "Return" : "Action"}`
              }
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Incident Details Inspection Modal */}
      {selectedIncident && (
        <Dialog 
          isOpen={!!selectedIncident} 
          onClose={() => setSelectedIncident(null)} 
          title={`Asset Incident #${selectedIncident.entity_id} - ${selectedIncident.title}`}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-muted/40 rounded-lg border">
                <span className="text-muted-foreground block">Asset Tag:</span>
                <span className="font-bold text-sm text-primary">{selectedIncident.asset_tag || "N/A"}</span>
              </div>
              <div className="p-3 bg-muted/40 rounded-lg border">
                <span className="text-muted-foreground block">Asset Model:</span>
                <span className="font-bold text-sm">{selectedIncident.asset_name || "N/A"}</span>
              </div>
              <div className="p-3 bg-muted/40 rounded-lg border">
                <span className="text-muted-foreground block">Incident Type:</span>
                <span className="font-semibold">{selectedIncident.incident_type || "N/A"}</span>
              </div>
              <div className="p-3 bg-muted/40 rounded-lg border">
                <span className="text-muted-foreground block">Status:</span>
                <StatusBadge status={selectedIncident.status} />
              </div>
              <div className="p-3 bg-muted/40 rounded-lg border">
                <span className="text-muted-foreground block">Reporter:</span>
                <span className="font-semibold">{selectedIncident.requestor_name}</span>
              </div>
              <div className="p-3 bg-muted/40 rounded-lg border">
                <span className="text-muted-foreground block">Reported Date:</span>
                <span>{formatDate(selectedIncident.created_at)}</span>
              </div>
            </div>

            <div className="p-3 bg-muted/30 rounded-lg border space-y-1">
              <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider block">Description</span>
              <p className="text-xs text-foreground leading-relaxed">{selectedIncident.justification || "None"}</p>
            </div>

            {selectedIncident.reason && (
              <div className="p-3 bg-muted/30 rounded-lg border space-y-1">
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider block">Reason / Justification</span>
                <p className="text-xs text-foreground leading-relaxed">{selectedIncident.reason}</p>
              </div>
            )}

            {selectedIncident.attachment_url && (() => {
              const url = resolveImageUrl(selectedIncident.attachment_url);
              return (
                <div className="p-3 bg-muted/30 rounded-lg border space-y-2">
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider block">Attachment / Photo Evidence</span>
                  <div className="max-h-48 overflow-hidden rounded-lg border bg-background flex flex-col items-center justify-center p-2">
                    <img
                      src={url}
                      alt="Damage Evidence"
                      className="max-h-40 object-contain rounded"
                      onError={(e: any) => { e.target.style.display = 'none'; }}
                    />
                    <a
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-primary underline block text-center mt-1"
                    >
                      Open Full Attachment
                    </a>
                  </div>
                </div>
              );
            })()}

            {selectedIncident.manager_inspection_assessment && (
              <div className="p-3 bg-primary/5 rounded-lg border border-primary/20 space-y-1 text-xs">
                <span className="font-bold text-primary block">Manager Physical Inspection Result:</span>
                <div className="font-semibold">{selectedIncident.manager_inspection_assessment}</div>
                {selectedIncident.manager_inspection_comments && (
                  <div className="text-muted-foreground italic">"{selectedIncident.manager_inspection_comments}"</div>
                )}
              </div>
            )}

            {selectedIncident.admin_inspection_resolution && (
              <div className="p-3 bg-emerald-500/5 rounded-lg border border-emerald-500/20 space-y-1 text-xs">
                <span className="font-bold text-emerald-600 block">Admin Inspection / Resolution:</span>
                <div className="font-semibold">{selectedIncident.admin_inspection_resolution}</div>
                {selectedIncident.admin_comments && (
                  <div className="text-muted-foreground italic">"{selectedIncident.admin_comments}"</div>
                )}
              </div>
            )}

            {selectedIncident.can_approve && ["Submitted", "Reported", "Manager Approved"].includes(selectedIncident.status) && (
              <div className="flex space-x-2 pt-4 border-t border-border">
                <Button 
                  variant="success" 
                  className="flex-1 font-bold shadow-apple-sm text-xs"
                  onClick={() => { setSelectedWorkflow(selectedIncident); setActionType("approve"); }}
                >
                  <Check className="w-3.5 h-3.5 mr-1" />
                  <span>Approve</span>
                </Button>
                <Button 
                  variant="warning" 
                  className="flex-1 font-bold shadow-apple-sm border border-yellow-500 bg-yellow-500/10 text-yellow-600 hover:bg-yellow-500 hover:text-white transition-colors text-xs"
                  onClick={() => { setSelectedWorkflow(selectedIncident); setActionType("return"); }}
                >
                  <span>Return</span>
                </Button>
                <Button 
                  variant="danger" 
                  className="flex-1 font-bold shadow-apple-sm text-xs"
                  onClick={() => { setSelectedWorkflow(selectedIncident); setActionType("reject"); }}
                >
                  <XIcon className="w-3.5 h-3.5 mr-1" />
                  <span>Reject</span>
                </Button>
              </div>
            )}
            
            {selectedIncident.status === "Admin Approved" && selectedIncident.entity_type === "AssetIncident" && (
              <div className="flex space-x-2 pt-4 border-t border-border">
                {selectedIncident.admin_inspection_resolution === "Repair Required" ? (
                  <Button 
                    variant="success" 
                    className="flex-1 font-bold shadow-apple-sm text-xs"
                    onClick={() => { setSelectedWorkflow(selectedIncident); setActionType("complete_repair" as any); }}
                  >
                    <span>Complete Repair</span>
                  </Button>
                ) : (
                  <>
                    <Button 
                      variant="info" 
                      className="flex-1 font-bold shadow-apple-sm text-xs"
                      onClick={() => { setSelectedWorkflow(selectedIncident); setActionType("assign_replacement" as any); }}
                    >
                      <span>Assign Replacement</span>
                    </Button>
                    <Button 
                      variant="outline" 
                      className="flex-1 font-bold shadow-apple-sm text-xs"
                      onClick={() => { setSelectedWorkflow(selectedIncident); setActionType("complete_procurement" as any); }}
                    >
                      <span>Trigger Procurement</span>
                    </Button>
                  </>
                )}
              </div>
            )}

            {selectedIncident.status === "Waiting for Procurement" && selectedIncident.entity_type === "AssetIncident" && (
              <div className="flex space-x-2 pt-4 border-t border-border">
                <Button 
                  variant="success" 
                  className="flex-1 font-bold shadow-apple-sm text-xs"
                  onClick={() => { setSelectedWorkflow(selectedIncident); setActionType("assign_replacement" as any); }}
                >
                  <span>Assign Received Asset</span>
                </Button>
              </div>
            )}

            <div className="flex justify-end pt-3 border-t">
              <Button variant="outline" onClick={() => setSelectedIncident(null)}>Close</Button>
            </div>
          </div>
        </Dialog>
      )}
      
      {/* Reimbursement Detail Modal */}
      {selectedReportId && (
        <ReimbursementDetailModal
          isOpen={!!selectedReportId}
          onClose={() => {
             setSelectedReportId(null);
             setSelectedReportDetails(null);
             fetchWorkflows();
          }}
          receiptDetails={selectedReportDetails}
          loading={loadingDetails}
          isPendingForUser={filteredWorkflows.find(w => w.entity_id === selectedReportId)?.can_approve || false}
          onAction={async (action) => {
             const wf = filteredWorkflows.find(w => w.entity_id === selectedReportId);
             if (wf) {
               setSelectedWorkflow(wf);
               setActionType(action === "approve" ? (wf.status === "Payment Requested" ? "pay" : "approve") : action);
               // Close this details modal so they can see the comment modal
               setSelectedReportId(null);
               setSelectedReportDetails(null);
             }
          }}
        />
      )}
    </div>
  );
};

export default Approvals;
