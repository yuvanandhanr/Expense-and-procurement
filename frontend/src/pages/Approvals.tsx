import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { ApprovalWorkflow } from "../types";
import { Button, Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, Dialog, Input, EmptyState } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import toast from "react-hot-toast";
import { formatDate } from "../utils/helpers";
import { Check, X as XIcon } from "lucide-react";

type TabType = "Requisitions" | "Expenses" | "Asset Incidents" | "Resignations";

export const Approvals: React.FC = () => {
  const { user } = useAuth();
  const [workflows, setWorkflows] = useState<ApprovalWorkflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>("Requisitions");
  
  // Action state
  const [selectedWorkflow, setSelectedWorkflow] = useState<ApprovalWorkflow | null>(null);
  const [actionType, setActionType] = useState<"approve" | "reject" | null>(null);
  const [comment, setComment] = useState("");
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
    setIsSubmitting(true);
    try {
      let endpoint = "";
      if (selectedWorkflow.entity_type === "ExpenseReport") {
        endpoint = `/expenses/${selectedWorkflow.entity_id}/${actionType}`;
      } else if (selectedWorkflow.entity_type === "VendorInvoice") {
        endpoint = `/invoices/${selectedWorkflow.entity_id}/${actionType}`;
      } else {
        endpoint = `/pr/${selectedWorkflow.entity_id}/${actionType}`;
      }
      
      const payload = selectedWorkflow.entity_type === "ExpenseReport" ? { comments: comment } : { action: actionType, comment };
      
      await api.post(endpoint, payload);
      toast.success(`Workflow successfully ${actionType}d!`);
      
      setSelectedWorkflow(null);
      setActionType(null);
      setComment("");
      fetchWorkflows();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to process workflow action.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getFilteredWorkflows = () => {
    return workflows.filter(wf => {
      if (activeTab === "Requisitions") return wf.entity_type === "PurchaseRequisition";
      if (activeTab === "Expenses") return wf.entity_type === "ExpenseReport";
      if (activeTab === "Asset Incidents") return wf.entity_type === "AssetIncident";
      if (activeTab === "Resignations") return wf.entity_type === "Resignation";
      return false;
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
                ? "border-violet text-violet" 
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
              <CardHeader className="pb-3 flex flex-row items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-1">
                    {wf.entity_type} #{wf.entity_id}
                  </span>
                  <CardTitle className="text-base">{wf.workflow_step} Step</CardTitle>
                </div>
                <Badge variant={wf.status === "Pending" ? "warning" : "neutral"}>{wf.status}</Badge>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col justify-between pt-0 space-y-4">
                <div className="text-sm space-y-2 mt-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Requested By:</span>
                    <span className="font-semibold">User {wf.requester_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Date:</span>
                    <span>{formatDate(wf.created_at)}</span>
                  </div>
                </div>
                
                <div className="flex space-x-2 pt-4 border-t border-border">
                  <Button 
                    variant="primary" 
                    className="flex-1 flex items-center justify-center space-x-2"
                    onClick={() => { setSelectedWorkflow(wf); setActionType("approve"); }}
                  >
                    <Check className="w-4 h-4" />
                    <span>Approve</span>
                  </Button>
                  <Button 
                    variant="danger" 
                    className="flex-1 flex items-center justify-center space-x-2 bg-pink hover:bg-pink/90 text-white shadow-sm"
                    onClick={() => { setSelectedWorkflow(wf); setActionType("reject"); }}
                  >
                    <XIcon className="w-4 h-4" />
                    <span>Reject</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Action Dialog */}
      <Dialog 
        isOpen={!!selectedWorkflow} 
        onClose={() => { setSelectedWorkflow(null); setActionType(null); setComment(""); }}
        title={`${actionType === 'approve' ? 'Approve' : 'Reject'} ${selectedWorkflow?.entity_type} #${selectedWorkflow?.entity_id}`}
      >
        <div className="space-y-4">
          <Input 
            label="Comments (Optional)" 
            value={comment} 
            onChange={(e) => setComment(e.target.value)} 
            placeholder="Add a note..." 
          />
          <div className="flex justify-end space-x-2">
            <Button variant="ghost" onClick={() => { setSelectedWorkflow(null); setActionType(null); }}>Cancel</Button>
            <Button 
              variant={actionType === "approve" ? "primary" : "danger"} 
              onClick={handleAction} 
              disabled={isSubmitting}
            >
              {isSubmitting ? "Processing..." : `Confirm ${actionType}`}
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
};

export default Approvals;
