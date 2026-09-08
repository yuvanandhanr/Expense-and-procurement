import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { ApprovalWorkflow } from "../types";
import { Button, Card, CardHeader, CardTitle, CardContent, Badge, StatusBadge, Skeleton, Dialog, Input, EmptyState } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import toast from "react-hot-toast";
import { formatDate, getErrorMessage, isValidText } from "../utils/helpers";
import { Check, X as XIcon } from "lucide-react";

type TabType = "Requisitions" | "Expenses" | "Asset Incidents" | "Resignations";

export const Approvals: React.FC = () => {
  const { user } = useAuth();
  const [workflows, setWorkflows] = useState<ApprovalWorkflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>("Requisitions");
  
  // Action state
  const [selectedWorkflow, setSelectedWorkflow] = useState<ApprovalWorkflow | null>(null);
  const [actionType, setActionType] = useState<"approve" | "reject" | "return" | "repair" | "replace" | null>(null);
  const [comment, setComment] = useState("");
  const [physicalInspectionDone, setPhysicalInspectionDone] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

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
        else if (actionType === "repair") actStr = "Repair";
        else if (actionType === "replace") actStr = "Replace";
        else if (actionType === "assign_replacement") actStr = "Assign Replacement";
        payload = { action: actStr, resolution: comment, physical_inspection_done: physicalInspectionDone };
      } else {
        endpoint = `/pr/${selectedWorkflow.entity_id}/${actionType}`;
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

  const getFilteredWorkflows = () => {
    return workflows
      .filter((wf: any) => {
        // Exclude 0.00 items from approval inbox
        const amt = Number(wf.amount || wf.total_amount || wf.estimated_cost || 0);
        if (wf.entity_type === "ExpenseReport" || wf.entity_type === "PurchaseRequisition" || wf.entity_type === "VendorInvoice") {
          if (amt <= 0) return false;
        }
        if (activeTab === "Requisitions") return wf.entity_type === "PurchaseRequisition";
        if (activeTab === "Expenses") return wf.entity_type === "ExpenseReport";
        if (activeTab === "Asset Incidents") return wf.entity_type === "AssetIncident";
        if (activeTab === "Resignations") return wf.entity_type === "Resignation";
        return false;
      })
      .sort((a: any, b: any) => {
        const sA = (a.status || "").toLowerCase();
        const sB = (b.status || "").toLowerCase();
        const isPendingA = sA.includes("pending") || sA.includes("review");
        const isPendingB = sB.includes("pending") || sB.includes("review");
        
        // Priority: pending approval workflows come first
        if (isPendingA && !isPendingB) return -1;
        if (!isPendingA && isPendingB) return 1;
        
        // Sort according to time of creation (newest first)
        const timeA = new Date(a.created_at || a.submission_date || a.date || 0).getTime();
        const timeB = new Date(b.created_at || b.submission_date || b.date || 0).getTime();
        return timeB - timeA;
      });
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
        {(["Requisitions", "Expenses", "Asset Incidents", "Resignations"] as TabType[]).map((tab) => (
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
             <EmptyState title={`No pending ${activeTab.toLowerCase()}.`} description="You're all caught up!" />
          </CardContent>
        </Card>
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
                
                {((["Pending", "Under Review", "Reported"].includes(wf.status)) || (wf.status.toLowerCase().includes("pending") && wf.status !== "Approved" && wf.status !== "Pending Fulfillment")) && (
                  <div className="flex space-x-2 pt-4 border-t border-border">
                    <Button 
                      variant="success" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("approve"); }}
                    >
                      <Check className="w-4 h-4" />
                      <span>Approve</span>
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
        onClose={() => { setSelectedWorkflow(null); setActionType(null); setComment(""); setPhysicalInspectionDone(false); }}
        title={`${actionType ? actionType.charAt(0).toUpperCase() + actionType.slice(1) : ''} ${selectedWorkflow?.entity_type} #${selectedWorkflow?.entity_id}`}
      >
        <div className="space-y-4">
          {selectedWorkflow?.status === "Reported" && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && (
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
              Comments {(actionType === 'reject' || actionType === 'return' || selectedWorkflow?.entity_type === 'AssetIncident') && <span className="text-red-500">*</span>}
            </label>
            <Input 
              value={comment} 
              onChange={(e) => setComment(e.target.value)} 
              placeholder={(actionType === 'reject' || actionType === 'return' || selectedWorkflow?.entity_type === 'AssetIncident') ? "Resolution / Reason (required)..." : "Add a note..."} 
            />
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="ghost" onClick={() => { setSelectedWorkflow(null); setActionType(null); setPhysicalInspectionDone(false); }}>Cancel</Button>
            <Button 
              variant={actionType === "approve" ? "primary" : actionType === "reject" ? "danger" : actionType === "return" ? "warning" : "outline"} 
              onClick={handleAction} 
              disabled={isSubmitting || ((actionType === 'reject' || actionType === 'return' || selectedWorkflow?.entity_type === 'AssetIncident') && !comment.trim()) || (selectedWorkflow?.status === 'Reported' && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && !physicalInspectionDone)}
            >
              {isSubmitting ? "Processing..." : `Confirm ${actionType ? actionType.charAt(0).toUpperCase() + actionType.slice(1) : ''}`}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
};

export default Approvals;
