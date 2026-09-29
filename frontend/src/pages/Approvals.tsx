import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { ApprovalWorkflow } from "../types";
import { Button, Card, CardHeader, CardTitle, CardContent, Badge, StatusBadge, Skeleton, Dialog, Input, EmptyState } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import toast from "react-hot-toast";
import { formatDate, getErrorMessage, isValidText } from "../utils/helpers";
import { Check, X as XIcon, Eye } from "lucide-react";
import { ReimbursementDetailModal } from "../components/expenses/ReimbursementDetailModal";

type TabType = "Reimbursements" | "Requisitions" | "Asset Incidents" | "Resignations";

export const Approvals: React.FC = () => {
  const { user } = useAuth();
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

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [selectedReportDetails, setSelectedReportDetails] = useState<any>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

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
    
    if ((actionType === 'reject' || actionType === 'return' || selectedWorkflow.entity_type === 'AssetIncident') && !isValidText(comment)) {
      toast.error("Please enter a valid comment (letters or numbers required).");
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
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Failed to process workflow action."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const getWorkflowsForTab = () => {
    return workflows.filter((wf: any) => {
      // Exclude 0.00 items from approval inbox
      const amt = Number(wf.amount || wf.total_amount || wf.estimated_cost || 0);
      if (wf.entity_type === "ExpenseReport" || wf.entity_type === "PurchaseRequisition" || wf.entity_type === "VendorInvoice") {
        if (amt <= 0) return false;
      }
      if (wf.status === "Draft") return false; // Exclude drafts from Approvals Inbox
      if (activeTab === "Requisitions") return wf.entity_type === "PurchaseRequisition";
      if (activeTab === "Reimbursements") return wf.entity_type === "ExpenseReport";
      if (activeTab === "Asset Incidents") return wf.entity_type === "AssetIncident";
      if (activeTab === "Resignations") return wf.entity_type === "Resignation";
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

  const currentTabWorkflows = getWorkflowsForTab();
  const subTabCounts: Record<string, number> = {
    All: currentTabWorkflows.length,
    Submitted: currentTabWorkflows.filter((r: any) => isSubmittedStatus(r.status)).length,
    Approved: currentTabWorkflows.filter((r: any) => isApprovedStatus(r.status)).length,
    Rejected: currentTabWorkflows.filter((r: any) => ["Rejected", "Cancelled", "Inactive", "Failed", "Error"].includes(r.status) || r.status.includes("Rejected")).length,
    "Return for Correction": currentTabWorkflows.filter((r: any) => r.status === "Returned for Correction" || r.status === "Returned").length,
  };

  const filteredWorkflows = getFilteredWorkflows();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Approvals Inbox</h1>
        <p className="text-xs text-muted-foreground mt-1">Review and sign off on pending workflows.</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-border">
        {(["Reimbursements", "Requisitions", "Asset Incidents", "Resignations"] as TabType[]).map((tab) => (
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
      ) : activeTab === "Reimbursements" ? (
        <div className="overflow-x-auto rounded-xl border border-border shadow-sm">
          <table className="w-full text-left text-sm text-foreground">
            <thead className="bg-muted text-muted-foreground uppercase text-xs font-bold tracking-wider">
              <tr>
                <th className="p-4">Report ID</th>
                <th className="p-4">Purpose</th>
                <th className="p-4">Total Amount</th>
                <th className="p-4">Status</th>
                <th className="p-4">Date Created</th>
                <th className="p-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border bg-card">
              {filteredWorkflows.map((wf) => (
                <tr key={wf.workflow_id} className="hover:bg-muted/50 transition-colors">
                  <td className="p-4 font-semibold">EXP-{wf.entity_id}</td>
                  <td className="p-4 font-medium max-w-[200px] truncate" title={wf.title}>{wf.title?.replace('Expense: ', '')}</td>
                  <td className="p-4 font-bold tracking-tight">${Number(wf.amount || 0).toFixed(2)}</td>
                  <td className="p-4">
                    <StatusBadge status={wf.status} />
                  </td>
                  <td className="p-4 text-xs text-muted-foreground">{new Date(wf.created_at || Date.now()).toLocaleDateString()}</td>
                  <td className="p-4 flex items-center gap-2">
                    {wf.can_approve ? (
                      <Button 
                        size="sm" 
                        variant="primary"
                        onClick={() => handleViewDetails(wf.entity_id)}
                        className="gap-1.5 bg-[#0f172a] text-white hover:bg-slate-800"
                      >
                        Need Approval
                      </Button>
                    ) : (
                      <Button 
                        size="sm" 
                        variant="view"
                        onClick={() => handleViewDetails(wf.entity_id)}
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
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-1">
                    {wf.entity_type === "AssetIncident" ? "ASSET INCIDENT" : wf.entity_type.replace(/([A-Z])/g, ' $1').trim()} #{wf.entity_id}
                  </span>
                  <CardTitle className="text-base">{wf.workflow_step || (wf.entity_type === 'AssetIncident' ? 'Request for Repair/Replacement' : `${wf.entity_type.replace(/([A-Z])/g, ' $1').trim()} Step`)}</CardTitle>
                </div>
                <StatusBadge status={wf.status} />
              </CardHeader>
              <CardContent className="flex-1 flex flex-col justify-between pt-0 space-y-4">
                <div className="text-sm space-y-3 mt-2">
                  <div>
                    <span className="font-semibold text-foreground text-base">{wf.title || "Untitled Request"}</span>
                  </div>
                  {wf.justification && (
                    <div>
                      <span className="block text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Justification / Reason</span>
                      <p className="text-muted-foreground italic line-clamp-2">{wf.justification}</p>
                    </div>
                  )}
                  <div className="flex justify-between items-center bg-muted/40 p-2 rounded-lg border">
                    <span className="text-muted-foreground text-xs">Requested By:</span>
                    <span className="font-semibold text-xs">{wf.requestor_name || `User ${wf.requester_id}`}</span>
                  </div>
                  <div className="flex justify-between items-center bg-muted/40 p-2 rounded-lg border">
                    <span className="text-muted-foreground text-xs">Requested Date:</span>
                    <span className="text-xs">{formatDate(wf.created_at)}</span>
                  </div>
                  {(wf.status === "Approved" && wf.updated_at) && (
                    <div className="flex justify-between items-center bg-muted/40 p-2 rounded-lg border">
                      <span className="text-muted-foreground text-xs">Approved Date:</span>
                      <span className="text-xs">{formatDate(wf.updated_at)}</span>
                    </div>
                  )}
                </div>
                
                {((["Pending", "Under Review", "Reported", "Payment Requested"].includes(wf.status)) || (wf.status.toLowerCase().includes("pending") && wf.status !== "Approved" && wf.status !== "Pending Fulfillment")) && (
                  <div className="flex space-x-2 pt-4 border-t border-border">
                    <Button 
                      variant="success" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType(wf.status === "Payment Requested" ? "pay" : "approve"); }}
                    >
                      <Check className="w-4 h-4" />
                      <span>{wf.status === "Payment Requested" ? "Authorize Payment" : "Approve"}</span>
                    </Button>
                    <Button 
                      variant="warning" 
                      className="flex-1 font-bold shadow-apple-sm border border-yellow-500 bg-yellow-500/10 text-yellow-600 hover:bg-yellow-500 hover:text-white transition-colors"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("return"); }}
                    >
                      <span>Return</span>
                    </Button>
                    <Button 
                      variant="danger" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("reject"); }}
                    >
                      <XIcon className="w-4 h-4" />
                      <span>Reject</span>
                    </Button>
                  </div>
                )}
                
                {wf.status === "Pending Fulfillment" && wf.entity_type === "AssetIncident" && (
                  <div className="flex space-x-2 pt-4 border-t border-border">
                    <Button 
                      variant="warning" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("repair"); }}
                    >
                      <span>Repair</span>
                    </Button>
                    <Button 
                      variant="info" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("replace"); }}
                    >
                      <span>Replace</span>
                    </Button>
                  </div>
                )}

                {wf.status === "Waiting for Procurement" && wf.entity_type === "AssetIncident" && (
                  <div className="flex space-x-2 pt-4 border-t border-border">
                    <Button 
                      variant="success" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("assign_replacement"); }}
                    >
                      <span>Assign Replacement</span>
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
        onClose={() => { setSelectedWorkflow(null); setActionType(null); setComment(""); 
      setManagerAssessment("");
      setManagerComments("");
      setAdminResolution("");
      setAdminComments("");
 }}
        title={`${actionType ? actionType.charAt(0).toUpperCase() + actionType.slice(1) : ''} ${selectedWorkflow?.entity_type} #${selectedWorkflow?.entity_id}`}
      >
        <div className="space-y-4">
          
          
          {selectedWorkflow?.status === "Submitted" && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && (
            <div className="space-y-4 p-3 bg-muted/30 rounded-xl border border-border/50">
               <div>
                 <label className="block text-sm font-medium mb-1">Inspection / Resolution Assessment <span className="text-red-500">*</span></label>
                 <select className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" value={managerAssessment} onChange={(e) => setManagerAssessment(e.target.value)}>
                   <option value="">Select an option</option>
                   <option value="No Action Required">No Action Required</option>
                   <option value="Repair Required">Repair Required</option>
                   <option value="Replacement Required">Replacement Required</option>
                   <option value="Further Inspection Required">Further Inspection Required</option>
                 </select>
               </div>
               <div>
                 <label className="block text-sm font-medium mb-1">Manager Inspection Comments</label>
                 <Input value={managerComments} onChange={(e) => setManagerComments(e.target.value)} placeholder="Notes..." />
               </div>
            </div>
          )}
          {selectedWorkflow?.status === "Manager Approved" && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && (
            <div className="space-y-4 p-3 bg-muted/30 rounded-xl border border-border/50">
               <div>
                 <label className="block text-sm font-medium mb-1">Admin Inspection / Resolution <span className="text-red-500">*</span></label>
                 <select className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" value={adminResolution} onChange={(e) => setAdminResolution(e.target.value)}>
                   <option value="">Select an option</option>
                   <option value="Repair Required">Repair Required</option>
                   <option value="Replacement Required">Replacement Required</option>
                   <option value="Further Inspection Required">Further Inspection Required</option>
                   <option value="No Replacement Required">No Replacement Required</option>
                 </select>
               </div>
               <div>
                 <label className="block text-sm font-medium mb-1">Admin Comments / Resolution Notes</label>
                 <Input value={adminComments} onChange={(e) => setAdminComments(e.target.value)} placeholder="Notes..." />
               </div>
            </div>
          )}
          {(actionType === 'reject' || actionType === 'return' || selectedWorkflow?.entity_type === 'AssetIncident') && (
            <div>
              <label className="block text-sm font-medium mb-1">
                Comments {(actionType === 'reject' || actionType === 'return') && <span className="text-red-500">*</span>}
              </label>
              <Input 
                value={comment} 
                onChange={(e) => setComment(e.target.value)} 
                placeholder={(actionType === 'reject' || actionType === 'return') ? "Resolution / Reason (required)..." : "Add a note..."} 
              />
            </div>
          )}

          <div className="flex justify-end space-x-2">
            <Button variant="ghost" onClick={() => { setSelectedWorkflow(null); setActionType(null); 
      setManagerAssessment("");
      setManagerComments("");
      setAdminResolution("");
      setAdminComments("");
 }}>Cancel</Button>
            <Button 
              variant={actionType === "approve" ? "primary" : actionType === "reject" ? "danger" : actionType === "return" ? "warning" : "outline"} 
              onClick={handleAction} 
              disabled={isSubmitting || ((actionType === "reject" || actionType === "return") && !comment.trim()) || (selectedWorkflow?.status === "Submitted" && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && !managerAssessment) || (selectedWorkflow?.status === "Manager Approved" && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && !adminResolution)}
            >
              {isSubmitting ? "Processing..." : `Confirm ${actionType ? actionType.charAt(0).toUpperCase() + actionType.slice(1) : ''}`}
            </Button>
          </div>
        </div>
      </Dialog>
      
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
