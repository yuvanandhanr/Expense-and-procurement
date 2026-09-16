import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { ApprovalWorkflow } from "../types";
import { Button, Card, CardHeader, CardTitle, CardContent, StatusBadge, Skeleton, Dialog, Input, EmptyState } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import toast from "react-hot-toast";
import { formatDate, getErrorMessage, isValidText } from "../utils/helpers";
import { Check, X as XIcon } from "lucide-react";

type TabType = "Reimbursements" | "Requisitions" | "Asset Incidents" | "Resignations";
type StatusSubTab = "All" | "Submitted" | "Approved" | "Rejected";

export const Approvals: React.FC = () => {
  const { user } = useAuth();
  const [workflows, setWorkflows] = useState<ApprovalWorkflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>("Reimbursements");
  const [statusSubTab, setStatusSubTab] = useState<StatusSubTab>("All");
  
  // Action state
  const [selectedWorkflow, setSelectedWorkflow] = useState<ApprovalWorkflow | null>(null);
  const [actionType, setActionType] = useState<"approve" | "reject" | "return" | "repair" | "replace" | null>(null);
  const [comment, setComment] = useState("");
  const [physicalInspectionDone, setPhysicalInspectionDone] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [allocateAssetId, setAllocateAssetId] = useState("");
  
  // Preview state
  const [previewWorkflow, setPreviewWorkflow] = useState<any>(null);
  const [receiptDetails, setReceiptDetails] = useState<any>(null);
  const [loadingReceipt, setLoadingReceipt] = useState(false);

  const handleViewReceipt = async (wf: any) => {
    setPreviewWorkflow(wf);
    setLoadingReceipt(true);
    try {
      const response = await api.get(`/expenses/${wf.entity_id}`);
      setReceiptDetails(response.data);
    } catch (err) {
      console.error("Failed to fetch receipt details:", err);
      toast.error("Could not load receipt details.");
    } finally {
      setLoadingReceipt(false);
    }
  };

  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const response = await api.get("/approvals");
      if (Array.isArray(response.data)) {
        setWorkflows(response.data);
      } else {
        setWorkflows([]);
      }
    } catch (err) {
      console.error("Failed to load approval workflows:", err);
      setWorkflows([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const handleAction = async () => {
    if (!selectedWorkflow || !actionType) return;
    
    if ((actionType === "reject" || actionType === "return" || selectedWorkflow.entity_type === "AssetIncident") && !isValidText(comment)) {
      toast.error("Please enter a valid comment (letters or numbers required).");
      return;
    }

    setIsSubmitting(true);
    try {
      let endpoint = "";
      let payload: any = { comments: comment };
      
      if (selectedWorkflow.entity_type === "ExpenseReport" || selectedWorkflow.entity_type === "Expense") {
        endpoint = `/expenses/${selectedWorkflow.entity_id}/${actionType}`;
      } else if (selectedWorkflow.entity_type === "VendorInvoice") {
        endpoint = `/invoices/${selectedWorkflow.entity_id}/${actionType}`;
      } else if (selectedWorkflow.entity_type === "AssetIncident") {
        endpoint = `/asset-incidents/${selectedWorkflow.entity_id}/action`;
        let actStr = "Approve";
        if (actionType === "reject") actStr = "Reject";
        else if (actionType === "return") actStr = "Return for Correction";
        else if (actionType === "repair") actStr = "Repair";
        else if (actionType === "replace") actStr = "Replace";
        else if (actionType === "assign_replacement") actStr = "Assign Replacement";
        payload = { action: actStr, resolution: comment, physical_inspection_done: physicalInspectionDone };
      } else {
        endpoint = `/pr/${selectedWorkflow.entity_id}/${actionType}`;
        payload = { comments: comment, physical_inspection_done: physicalInspectionDone };
      }
      
      await api.post(endpoint, payload);
      toast.success(`Workflow successfully ${actionType}d!`);
      
      setSelectedWorkflow(null);
      setActionType(null);
      setComment("");
      setPhysicalInspectionDone(false);
      fetchWorkflows();
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Failed to process workflow action."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAdminAction = async (type: "allocate" | "procure") => {
    if (!selectedWorkflow) return;
    setIsSubmitting(true);
    try {
      if (type === "allocate") {
        if (!allocateAssetId) {
          toast.error("Please provide an Asset ID to allocate.");
          setIsSubmitting(false);
          return;
        }
        await api.post(`/pr/${selectedWorkflow.entity_id}/allocate-inventory`, { asset_id: parseInt(allocateAssetId) });
        toast.success("Asset allocated from inventory successfully!");
      } else {
        await api.post(`/pr/${selectedWorkflow.entity_id}/initiate-procurement`);
        toast.success("Procurement initiated. Escalated to CFO.");
      }
      setSelectedWorkflow(null);
      setAllocateAssetId("");
      fetchWorkflows();
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Failed to process admin action."));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Helper status checkers
  const isApprovedWf = (wf: any) => {
    const s = String(wf?.status || "").toLowerCase();
    return s.includes("approved") || s === "pass" || s === "completed" || s === "fulfilled";
  };

  const isRejectedWf = (wf: any) => {
    const s = String(wf?.status || "").toLowerCase();
    return s.includes("reject") || s.includes("denied") || s.includes("correction") || s.includes("returned");
  };

  const isSubmittedWf = (wf: any) => {
    return !isApprovedWf(wf) && !isRejectedWf(wf);
  };

  // Base list of workflows for the selected category
  const baseCategoryWorkflows = (Array.isArray(workflows) ? workflows : []).filter((wf: any) => {
    if (!wf || typeof wf !== "object") return false;
    
    const rawAmt = wf.total_amount ?? wf.amount ?? wf.estimated_cost;
    if (rawAmt !== undefined && rawAmt !== null) {
      const amt = Number(rawAmt);
      if (!isNaN(amt) && amt <= 0 && (wf.entity_type === "ExpenseReport" || wf.entity_type === "PurchaseRequisition" || wf.entity_type === "VendorInvoice")) {
        return false;
      }
    }

    if (activeTab === "Requisitions") return wf.entity_type === "PurchaseRequisition";
    if (activeTab === "Reimbursements") return wf.entity_type === "ExpenseReport" || wf.entity_type === "Expense";
    if (activeTab === "Asset Incidents") return wf.entity_type === "AssetIncident";
    if (activeTab === "Resignations") return wf.entity_type === "Resignation";
    return false;
  });

  // Calculate counts for sub-tabs
  const subTabCounts = {
    All: baseCategoryWorkflows.length,
    Submitted: baseCategoryWorkflows.filter(isSubmittedWf).length,
    Approved: baseCategoryWorkflows.filter(isApprovedWf).length,
    Rejected: baseCategoryWorkflows.filter(isRejectedWf).length,
  };

  // Filter category workflows by current status sub-tab
  const filteredWorkflows = baseCategoryWorkflows
    .filter((wf: any) => {
      if (statusSubTab === "Submitted") return isSubmittedWf(wf);
      if (statusSubTab === "Approved") return isApprovedWf(wf);
      if (statusSubTab === "Rejected") return isRejectedWf(wf);
      return true; // "All"
    })
    .sort((a: any, b: any) => {
      const sA = String(a?.status || "").toLowerCase();
      const sB = String(b?.status || "").toLowerCase();
      const isPendingA = sA.includes("pending") || sA.includes("review");
      const isPendingB = sB.includes("pending") || sB.includes("review");
      
      // Priority: pending approval workflows come first
      if (isPendingA && !isPendingB) return -1;
      if (!isPendingA && isPendingB) return 1;
      
      // Sort according to time of creation (newest first)
      const timeA = new Date(a?.created_at || a?.submission_date || a?.date || 0).getTime();
      const timeB = new Date(b?.created_at || b?.submission_date || b?.date || 0).getTime();
      return timeB - timeA;
    });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Approvals Inbox</h1>
        <p className="text-xs text-muted-foreground mt-1">Review and sign off on pending workflows.</p>
      </div>

      {/* Primary Category Tabs */}
      <div className="flex space-x-2 border-b border-border">
        {(["Reimbursements", "Requisitions", "Asset Incidents", "Resignations"] as TabType[]).map((tab) => (
          <button
            key={tab}
            onClick={() => {
              setActiveTab(tab);
              setStatusSubTab("All"); // Reset subtab on category change
            }}
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

      {/* Status Sub-Tabs (All, Submitted, Approved, Rejected) */}
      <div className="flex items-center space-x-2 bg-muted/40 p-1.5 rounded-xl w-fit border border-border/50">
        {(["All", "Submitted", "Approved", "Rejected"] as StatusSubTab[]).map((subTab) => (
          <button
            key={subTab}
            onClick={() => setStatusSubTab(subTab)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center space-x-1.5 ${
              statusSubTab === subTab
                ? "bg-primary text-primary-foreground shadow-sm font-bold"
                : "text-muted-foreground hover:text-foreground hover:bg-background/50"
            }`}
          >
            <span>{subTab}</span>
            <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
              statusSubTab === subTab ? "bg-primary-foreground/20 text-primary-foreground font-bold" : "bg-muted text-muted-foreground"
            }`}>
              {subTabCounts[subTab]}
            </span>
          </button>
        ))}
      </div>

      {/* Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Skeleton className="h-40 w-full rounded-lg" />
          <Skeleton className="h-40 w-full rounded-lg" />
          <Skeleton className="h-40 w-full rounded-lg" />
        </div>
      ) : filteredWorkflows.length === 0 ? (
        <Card className="bg-transparent border-dashed">
          <CardContent className="py-12">
             <EmptyState title={`No ${statusSubTab === "All" ? "" : statusSubTab.toLowerCase() + " "}${activeTab.toLowerCase()}.`} description="You are all caught up!" />
          </CardContent>
        </Card>
      ) : activeTab === "Reimbursements" ? (
        <div className="bg-white rounded-xl shadow-sm border border-border overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border/80 text-xs text-muted-foreground uppercase tracking-wider bg-muted/20">
                <th className="px-6 py-4 font-semibold">Report ID</th>
                <th className="px-6 py-4 font-semibold">Purpose</th>
                <th className="px-6 py-4 font-semibold">Total Amount</th>
                <th className="px-6 py-4 font-semibold">Status</th>
                <th className="px-6 py-4 font-semibold">Created By</th>
                <th className="px-6 py-4 font-semibold text-center">Receipt</th>
                <th className="px-6 py-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50 text-sm">
              {filteredWorkflows.map(wf => {
                const titleStr = typeof wf.title === "string" ? wf.title : "Untitled Request";
                const descStr = typeof wf.description === "string" ? wf.description : (typeof wf.justification === "string" ? wf.justification : "");
                const requesterStr = wf.requestor_name || wf.requester_name || wf.submitted_by || "Employee";
                const rawAmt = wf.total_amount ?? wf.amount ?? wf.estimated_cost;
                const amtNum = rawAmt !== undefined && rawAmt !== null ? Number(rawAmt) : null;
                const statusStr = String(wf.status || "");
                
                const isApproved = isApprovedWf(wf);
                const isRejected = isRejectedWf(wf);
                const isPendingStatus = !isApproved && !isRejected && ((["Pending", "Under Review", "Reported"].includes(statusStr)) || (statusStr.toLowerCase().includes("pending") && statusStr !== "Approved" && statusStr !== "Pending Fulfillment"));

                return (
                  <tr key={wf.workflow_id || wf.entity_id} className="hover:bg-muted/10 transition-colors">
                    <td className="px-6 py-4 font-semibold text-primary">#{wf.entity_id || wf.workflow_id}</td>
                    <td className="px-6 py-4">
                      <div className="font-semibold text-foreground">{titleStr}</div>
                      {descStr && <div className="text-xs text-muted-foreground mt-1 line-clamp-1">{descStr}</div>}
                    </td>
                    <td className="px-6 py-4 font-bold">
                      {amtNum !== null && !isNaN(amtNum) ? `$${amtNum.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "-"}
                    </td>
                    <td className="px-6 py-4"><StatusBadge status={statusStr} /></td>
                    <td className="px-6 py-4">
                      <div className="text-xs font-semibold">{requesterStr}</div>
                      <div className="text-[10px] text-muted-foreground">{formatDate(wf.created_at || wf.submission_date || wf.date)}</div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <Button variant="outline" size="sm" onClick={() => handleViewReceipt(wf)} className="text-xs shadow-sm">View Receipt</Button>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {isPendingStatus ? (
                        <div className="flex justify-end gap-2">
                          <Button variant="success" size="sm" onClick={() => { setSelectedWorkflow(wf); setActionType("approve"); }} className="px-3 shadow-sm text-xs"><Check className="w-3.5 h-3.5 mr-1" /> Approve</Button>
                          <Button variant="warning" size="sm" onClick={() => { setSelectedWorkflow(wf); setActionType("return"); }} className="px-3 shadow-sm text-xs bg-amber-500/10 text-amber-600 border border-amber-500/30 hover:bg-amber-500 hover:text-white">Return</Button>
                          <Button variant="danger" size="sm" onClick={() => { setSelectedWorkflow(wf); setActionType("reject"); }} className="px-3 shadow-sm text-xs"><XIcon className="w-3.5 h-3.5 mr-1" /> Reject</Button>
                        </div>
                      ) : (
                        <span className="text-muted-foreground text-xs italic">No actions available</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredWorkflows.map(wf => {
            const entityTypeStr = String(wf.entity_type || "");
            
            let formattedTitle = "Purchase Requisition";
            if (entityTypeStr === "ExpenseReport" || entityTypeStr === "Expense") formattedTitle = "Expense Reimbursement";
            else if (entityTypeStr === "AssetIncident") formattedTitle = "Asset Incident";
            else if (entityTypeStr === "Resignation") formattedTitle = "Resignation";
            else if (entityTypeStr === "PurchaseRequisition") formattedTitle = "Purchase Requisition";
            else formattedTitle = entityTypeStr.replace(/([A-Z])/g, " $1").trim();

            const headerTag = entityTypeStr === "ExpenseReport" ? "EXPENSE REIMBURSEMENT" : formattedTitle.toUpperCase();

            const titleStr = typeof wf.title === "string" ? wf.title : "Untitled Request";
            const descStr = typeof wf.description === "string" ? wf.description : (typeof wf.justification === "string" ? wf.justification : "");
            const requesterStr = wf.requestor_name || wf.requester_name || wf.submitted_by || "Employee";
            const rawAmt = wf.total_amount ?? wf.amount ?? wf.estimated_cost;
            const amtNum = rawAmt !== undefined && rawAmt !== null ? Number(rawAmt) : null;
            const statusStr = String(wf.status || "");
            
            const isApproved = isApprovedWf(wf);
            const isRejected = isRejectedWf(wf);
            const isPendingStatus = !isApproved && !isRejected && ((["Pending", "Under Review", "Reported"].includes(statusStr)) || (statusStr.toLowerCase().includes("pending") && statusStr !== "Approved" && statusStr !== "Pending Fulfillment"));

            return (
              <Card key={wf.workflow_id || wf.entity_id} className="flex flex-col border border-border/80 shadow-sm hover:shadow-md transition-shadow">
                <CardHeader className="pb-3 flex flex-col items-start gap-2">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-0.5">
                      {headerTag} #{wf.entity_id || wf.workflow_id}
                    </span>
                    <CardTitle className="text-base font-bold">{formattedTitle}</CardTitle>
                  </div>
                  <StatusBadge status={statusStr} />
                </CardHeader>
                <CardContent className="flex-1 flex flex-col justify-between pt-0 space-y-4">
                  <div className="text-sm space-y-3 mt-1">
                    <div>
                      <span className="font-semibold text-foreground text-base">{titleStr}</span>
                    </div>
                    
                    {descStr && (
                      <div className="space-y-0.5 bg-muted/20 p-2.5 rounded-lg border border-border/40">
                        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">Reason</span>
                        <p className="text-foreground text-xs leading-relaxed font-normal line-clamp-3">{descStr}</p>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-3 text-xs pt-2 border-t border-border/50">
                      <div>
                        <span className="text-muted-foreground font-medium block text-[11px] mb-0.5">Submitted By</span>
                        <span className="font-semibold text-foreground text-xs block truncate">{requesterStr}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground font-medium block text-[11px] mb-0.5">Date</span>
                        <span className="font-semibold text-foreground text-xs block">{formatDate(wf.created_at || wf.submission_date || wf.date)}</span>
                      </div>
                    </div>

                    {amtNum !== null && !isNaN(amtNum) && (
                      <div className="flex justify-between items-center bg-muted/40 p-2 rounded-lg border border-border/50">
                        <span className="text-muted-foreground text-xs font-medium">Total Amount:</span>
                        <span className="font-bold text-foreground">${amtNum.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                      </div>
                    )}

                    {isApproved && (
                      <div className="flex justify-between items-center bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/20 text-xs">
                        <span className="text-emerald-700 dark:text-emerald-400 font-semibold">Approved Date:</span>
                        <span className="font-bold text-emerald-800 dark:text-emerald-300">{formatDate(wf.updated_at || wf.actioned_at || wf.created_at)}</span>
                      </div>
                    )}

                    {isRejected && (
                      <div className="flex justify-between items-center bg-rose-500/10 p-2 rounded-lg border border-rose-500/20 text-xs">
                        <span className="text-rose-700 dark:text-rose-400 font-semibold">
                          {statusStr.toLowerCase().includes("return") ? "Returned Date:" : "Rejected Date:"}
                        </span>
                        <span className="font-bold text-rose-800 dark:text-rose-300">{formatDate(wf.updated_at || wf.actioned_at || wf.created_at)}</span>
                      </div>
                    )}
                  </div>
                  
                  {isPendingStatus && (
                    <div className="flex items-center gap-2 pt-3 border-t border-border">
                      <Button 
                        variant="success" 
                        size="sm"
                        className="flex-1 py-1.5 px-2 text-xs font-semibold shadow-apple-sm flex items-center justify-center gap-1"
                        onClick={() => { setSelectedWorkflow(wf); setActionType("approve"); }}
                      >
                        <Check className="w-3.5 h-3.5 shrink-0" />
                        <span>Approve</span>
                      </Button>
                      <Button 
                        variant="warning" 
                        size="sm"
                        className="flex-1 py-1.5 px-2 text-xs font-semibold shadow-apple-sm border border-amber-500/30 bg-amber-500/10 text-amber-600 hover:bg-amber-500 hover:text-white transition-all flex items-center justify-center gap-1"
                        onClick={() => { setSelectedWorkflow(wf); setActionType("return"); }}
                      >
                        <span>Return</span>
                      </Button>
                      <Button 
                        variant="danger" 
                        size="sm"
                        className="flex-1 py-1.5 px-2 text-xs font-semibold shadow-apple-sm flex items-center justify-center gap-1"
                        onClick={() => { setSelectedWorkflow(wf); setActionType("reject"); }}
                      >
                        <XIcon className="w-3.5 h-3.5 shrink-0" />
                        <span>Reject</span>
                      </Button>
                    </div>
                  )}
                  
                  {statusStr === "Pending Admin Approval" && entityTypeStr === "PurchaseRequisition" && user?.roles?.some(r => r.role_name === "Admin") && (
                    <div className="mt-4 p-4 border border-border bg-muted/20 rounded-lg space-y-4">
                      <h4 className="font-bold text-sm">Inventory Check & Allocation</h4>
                      <div className="space-y-2">
                        <label className="text-xs font-semibold text-muted-foreground uppercase">Allocate from Available Inventory</label>
                        <div className="flex gap-2">
                          <Input 
                            id="allocate-asset-id"
                            placeholder="Enter Asset ID..." 
                            value={allocateAssetId}
                            onChange={(e) => setAllocateAssetId(e.target.value)}
                          />
                          <Button onClick={() => { setSelectedWorkflow(wf); handleAdminAction("allocate"); }} variant="primary" disabled={isSubmitting}>Allocate Asset</Button>
                        </div>
                      </div>
                      <div className="pt-2 border-t border-border">
                        <p className="text-xs text-muted-foreground mb-2">If no suitable asset is found in inventory, initiate a new purchase.</p>
                        <Button onClick={() => { setSelectedWorkflow(wf); handleAdminAction("procure"); }} variant="outline" className="w-full" disabled={isSubmitting}>Initiate Procurement (Route to CFO)</Button>
                      </div>
                    </div>
                  )}
                  
                  {statusStr === "Pending Fulfillment" && entityTypeStr === "AssetIncident" && (
                    <div className="flex items-center gap-2 pt-3 border-t border-border">
                      <Button 
                        variant="warning" 
                        size="sm"
                        className="flex-1 py-1.5 px-2 text-xs font-semibold shadow-apple-sm"
                        onClick={() => { setSelectedWorkflow(wf); setActionType("repair"); }}
                      >
                        <span>Repair</span>
                      </Button>
                      <Button 
                        variant="info" 
                        size="sm"
                        className="flex-1 py-1.5 px-2 text-xs font-semibold shadow-apple-sm"
                        onClick={() => { setSelectedWorkflow(wf); setActionType("replace"); }}
                      >
                        <span>Replace</span>
                      </Button>
                    </div>
                  )}

                  {statusStr === "Waiting for Procurement" && entityTypeStr === "AssetIncident" && (
                    <div className="flex items-center gap-2 pt-3 border-t border-border">
                      <Button 
                        variant="success" 
                        size="sm"
                        className="flex-1 py-1.5 px-2 text-xs font-semibold shadow-apple-sm"
                        onClick={() => { setSelectedWorkflow(wf); setActionType("assign_replacement"); }}
                      >
                        <span>Assign Replacement</span>
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Action Dialog */}
      <Dialog 
        isOpen={!!selectedWorkflow} 
        onClose={() => { setSelectedWorkflow(null); setActionType(null); setComment(""); setPhysicalInspectionDone(false); }}
        title={`${actionType ? actionType.charAt(0).toUpperCase() + actionType.slice(1) : ""} ${selectedWorkflow?.entity_type || ""} #${selectedWorkflow?.entity_id || ""}`}
      >
        <div className="space-y-4">
          {((selectedWorkflow?.status === "Reported" && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident") ||
            (selectedWorkflow?.status === "Pending Manager Approval" && selectedWorkflow?.entity_type === "PurchaseRequisition" && actionType === "approve")) && (
            <div className="flex items-center space-x-2 p-3 bg-muted/30 rounded-xl border border-border/50">
              <input 
                type="checkbox" 
                id="physicalInspection"
                checked={physicalInspectionDone}
                onChange={(e) => setPhysicalInspectionDone(e.target.checked)}
                className="w-4 h-4 text-primary rounded border-border focus:ring-primary cursor-pointer"
              />
              <label htmlFor="physicalInspection" className="text-sm font-semibold text-foreground cursor-pointer select-none">
                Physical Inspection Completed <span className="text-red-500">*</span>
              </label>
            </div>
          )}
          <div>
            <label className="block text-sm font-medium mb-1">
              Comments {(actionType === "reject" || actionType === "return" || selectedWorkflow?.entity_type === "AssetIncident") && <span className="text-red-500">*</span>}
            </label>
            <Input 
              value={comment} 
              onChange={(e) => setComment(e.target.value)} 
              placeholder={(actionType === "reject" || actionType === "return" || selectedWorkflow?.entity_type === "AssetIncident") ? "Resolution / Reason (required)..." : "Add a note..."} 
            />
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="ghost" onClick={() => { setSelectedWorkflow(null); setActionType(null); setPhysicalInspectionDone(false); }}>Cancel</Button>
            <Button 
              variant={actionType === "approve" ? "primary" : actionType === "reject" ? "danger" : actionType === "return" ? "warning" : "outline"} 
              onClick={handleAction} 
              disabled={isSubmitting || ((actionType === "reject" || actionType === "return" || selectedWorkflow?.entity_type === "AssetIncident") && !comment.trim()) || (selectedWorkflow?.status === "Reported" && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && !physicalInspectionDone)}
            >
              {isSubmitting ? "Processing..." : `Confirm ${actionType ? actionType.charAt(0).toUpperCase() + actionType.slice(1) : ""}`}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Receipt Preview Dialog */}
      <Dialog 
        isOpen={!!previewWorkflow} 
        onClose={() => { setPreviewWorkflow(null); setReceiptDetails(null); }}
        title={`Receipt Preview - Reimbursement #${previewWorkflow?.entity_id}`}
      >
        <div className="space-y-4">
          {loadingReceipt ? (
            <div className="p-8 text-center text-muted-foreground">Loading receipt data...</div>
          ) : receiptDetails ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center bg-muted/20 p-4 rounded-xl border border-border">
                <div>
                  <h3 className="font-bold text-lg">{receiptDetails.merchant_name || receiptDetails.purpose || "Expense"}</h3>
                  <p className="text-sm text-muted-foreground">{formatDate(receiptDetails.transaction_date || receiptDetails.created_at)}</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-primary">${Number(receiptDetails.total_amount).toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
                  <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Verified Total</div>
                </div>
              </div>
              
              <div className="bg-muted/10 p-4 rounded-xl border border-border text-sm space-y-2">
                <p><span className="font-semibold">Reason:</span> {receiptDetails.justification}</p>
                {receiptDetails.department_id && <p><span className="font-semibold">Dept ID:</span> {receiptDetails.department_id}</p>}
                {receiptDetails.project_id && <p><span className="font-semibold">Project ID:</span> {receiptDetails.project_id}</p>}
              </div>

              {receiptDetails.receipts && receiptDetails.receipts.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Attached Receipts ({receiptDetails.receipts.length})</h4>
                  {receiptDetails.receipts.map((receipt: any, idx: number) => (
                    <div key={idx} className="flex gap-4 p-3 border border-border rounded-lg items-center">
                      <div className="w-16 h-16 bg-muted rounded flex items-center justify-center shrink-0">
                        {receipt.file_url ? (
                           <img src={receipt.file_url} alt="Receipt" className="w-full h-full object-cover rounded" />
                        ) : (
                           <span className="text-xs text-muted-foreground">No File</span>
                        )}
                      </div>
                      <div className="flex-1 text-xs space-y-1">
                        <p className="font-semibold text-sm">{receipt.merchant_name}</p>
                        <p className="text-muted-foreground">Date: {formatDate(receipt.transaction_date)} • Category: {receipt.category}</p>
                        {receipt.ocr_confidence && <p className="text-emerald-600">OCR Confidence: {(receipt.ocr_confidence * 100).toFixed(2)}%</p>}
                        {receipt.total_amount && <p className="font-medium text-foreground">OCR Extracted: ${Number(receipt.total_amount).toFixed(2)}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 text-center text-muted-foreground">Failed to load receipt data.</div>
          )}
          <div className="flex justify-end pt-2 border-t border-border">
            <Button variant="outline" onClick={() => setPreviewWorkflow(null)}>Close</Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
};

export default Approvals;
