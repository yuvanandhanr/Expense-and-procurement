import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { ApprovalWorkflow } from "../types";
import { Button, Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, Dialog, Input } from "../components/ui";
import toast from "react-hot-toast";

export const Approvals: React.FC = () => {
  const [workflows, setWorkflows] = useState<ApprovalWorkflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedWorkflow, setSelectedWorkflow] = useState<ApprovalWorkflow | null>(null);
  
  // Action state
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

  const handleAction = async (action: "approve" | "reject" | "delegate") => {
    if (!selectedWorkflow) return;
    setIsSubmitting(true);
    try {
      await api.post(`/approvals/${selectedWorkflow.workflow_id}/action`, {
        action,
        comment,
      });
      toast.success(`Workflow successfully ${action}d!`);
      setSelectedWorkflow(null);
      setComment("");
      fetchWorkflows();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to process workflow action.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Approvals Inbox</h1>
        <p className="text-xs text-muted-foreground mt-1">Review and sign off on requisitions and operational workflows.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : workflows.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              No pending approvals found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    <th className="p-4">Workflow ID</th>
                    <th className="p-4">Entity Type</th>
                    <th className="p-4">Entity ID</th>
                    <th className="p-4">Current Step Sequence</th>
                    <th className="p-4">Workflow Status</th>
                    <th className="p-4">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-sm">
                  {workflows.map((wf) => (
                    <tr key={wf.workflow_id} className="hover:bg-accent/20 transition-colors">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">#WF-{wf.workflow_id}</td>
                      <td className="p-4 font-bold text-xs">{wf.entity_type}</td>
                      <td className="p-4 font-bold text-xs">#{wf.entity_id}</td>
                      <td className="p-4">Step {wf.current_step_sequence}</td>
                      <td className="p-4">
                        <Badge variant={wf.status === "Approved" ? "success" : wf.status === "Pending" ? "warning" : "error"}>
                          {wf.status}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <Button size="sm" onClick={() => setSelectedWorkflow(wf)}>
                          Review
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

      {/* Review Dialog */}
      {selectedWorkflow && (
        <Dialog isOpen={true} onClose={() => setSelectedWorkflow(null)} title={`Review Workflow #WF-${selectedWorkflow.workflow_id}`}>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 bg-muted/40 p-3 rounded-lg border border-border text-xs">
              <div>
                <span className="block text-muted-foreground font-semibold uppercase">Target Entity</span>
                <span className="font-bold text-sm uppercase tracking-wider text-foreground">{selectedWorkflow.entity_type}</span>
              </div>
              <div>
                <span className="block text-muted-foreground font-semibold uppercase">Entity ID</span>
                <span className="font-bold text-sm tracking-wider text-foreground">#{selectedWorkflow.entity_id}</span>
              </div>
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">Comments / Decision Notes</label>
              <textarea
                placeholder="Include details explaining your decision (required if rejecting)"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px]"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-4 border-t border-border">
              <Button variant="outline" onClick={() => setSelectedWorkflow(null)}>
                Close
              </Button>
              <Button variant="danger" disabled={isSubmitting} onClick={() => handleAction("reject")}>
                Reject
              </Button>
              <Button disabled={isSubmitting} onClick={() => handleAction("approve")}>
                Approve
              </Button>
            </div>
          </div>
        </Dialog>
      )}
    </div>
  );
};
export default Approvals;
