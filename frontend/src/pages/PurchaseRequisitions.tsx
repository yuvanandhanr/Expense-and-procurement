import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { PurchaseRequisition } from "../types";
import { Button, Input, Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, Dialog, HeroTimestamp, EmptyState } from "../components/ui";
import { ClipboardList } from "lucide-react";
import toast from "react-hot-toast";
import { formatDate, getErrorMessage } from "../utils/helpers";
import { useAuth } from "../hooks/useAuth";

export const PurchaseRequisitions: React.FC = () => {
  const { user } = useAuth();
  const [prs, setPrs] = useState<PurchaseRequisition[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState("All");
  const [selectedPr, setSelectedPr] = useState<PurchaseRequisition | null>(null);
  const [comment, setComment] = useState("");

  // Form states
  const [title, setTitle] = useState("");
  const [estimatedCost, setEstimatedCost] = useState("");
  const [priority, setPriority] = useState("Medium");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchPRs = async () => {
    setLoading(true);
    try {
      const [response, poRes] = await Promise.all([
        api.get("/pr"),
        api.get("/purchase-orders").catch(() => ({ data: [] })) // In case the user doesn't have PO access
      ]);
      setPrs(response.data);
      setPurchaseOrders(poRes.data);
    } catch (err) {
      console.error("Failed to load PRs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPRs();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !estimatedCost) {
      toast.error("Title and estimated cost are required.");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await api.post("/pr", {
        title,
        justification: description || "No justification provided",
        priority,
        department_id: 123,
        items: [
          {
            category: "Standard",
            item_name: title,
            quantity: 1,
            unit_price: parseFloat(estimatedCost)
          }
        ]
      });
      
      // Auto-submit the PR to trigger the workflow
      if (res.data && res.data.pr_id) {
        await api.post(`/pr/${res.data.pr_id}/submit`);
      }
      
      toast.success("Purchase Requisition created and submitted successfully!");
      setIsCreateOpen(false);
      // Reset form
      setTitle("");
      setEstimatedCost("");
      setPriority("Medium");
      setDescription("");
      fetchPRs();
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Failed to create PR."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAction = async (action: "approve" | "reject" | "cancel") => {
    if (!selectedPr) return;
    setIsSubmitting(true);
    try {
      if (action === "cancel") {
        await api.post(`/pr/${selectedPr.pr_id}/cancel`);
        toast.success(`Purchase Requisition successfully cancelled!`);
      } else {
        await api.post(`/pr/${selectedPr.pr_id}/${action}`, {
          comments: comment,
        });
        toast.success(`Purchase Requisition successfully ${action}d!`);
      }
      setSelectedPr(null);
      setComment("");
      fetchPRs();
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Failed to process workflow action."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async (prId: number) => {
    try {
      await api.post(`/pr/${prId}/submit`);
      toast.success("Purchase Requisition submitted successfully!");
      fetchPRs();
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Failed to submit PR."));
    }
  };

  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase();
    if (s === "approved" || s === "completed") return <Badge variant="success">{status}</Badge>;
    if (s === "pending" || s === "under review" || s === "submitted" || s.includes("pending")) return <Badge variant="warning">{status}</Badge>;
    if (s === "rejected" || s === "cancelled") return <Badge variant="error">{status}</Badge>;
    return <Badge variant="neutral">{status}</Badge>;
  };

  const filteredPrs = prs.filter((pr) => {
    if (statusFilter === "All") return true;
    return pr.status.toLowerCase() === statusFilter.toLowerCase();
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Purchase Requisitions</h1>
          <p className="text-xs text-muted-foreground mt-1">Submit and track department purchase requests.</p>
        </div>
        <div className="flex items-center space-x-4">
          <HeroTimestamp />
          <Button onClick={() => setIsCreateOpen(true)} className="font-bold text-xs uppercase tracking-wider">
            New Requisition
          </Button>
        </div>
      </div>

      {/* Filters & Controls */}
      <div className="flex items-center space-x-2 bg-card p-3 rounded-lg border border-border">
        <span className="text-xs font-semibold text-muted-foreground uppercase px-2">Filter State:</span>
        {["All", "Draft", "Submitted", "Approved", "Rejected"].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-3 py-1 text-xs font-bold rounded-full transition-all ${
              statusFilter === status
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent"
            }`}
          >
            {status}
          </button>
        ))}
      </div>

      {/* PR Table List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : filteredPrs.length === 0 ? (
            <EmptyState
              icon={<ClipboardList className="w-8 h-8" />}
              title="No Requisitions found."
              description="You have not submitted any purchase requests yet."
              actionLabel="Create new requisition"
              onAction={() => setIsCreateOpen(true)}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    <th className="p-4">PR Number</th>
                    <th className="p-4">Requestor Name</th>
                    <th className="p-4">Title</th>
                    <th className="p-4">Estimated Cost</th>
                    <th className="p-4">Priority</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Date Created</th>
                    <th className="p-4">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-sm">
                  {filteredPrs.map((pr) => (
                    <tr key={pr.pr_id} className="hover:bg-accent/20 transition-colors">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{pr.pr_number}</td>
                      <td className="p-4">{pr.requestor_name || "Unknown"}</td>
                      <td className="p-4 font-semibold">{pr.title}</td>
                      <td className="p-4 font-bold">${pr.total_estimated_amount?.toLocaleString()}</td>
                      <td className="p-4">
                        <Badge variant={pr.priority === "High" ? "error" : pr.priority === "Medium" ? "warning" : "neutral"}>
                          {pr.priority}
                        </Badge>
                      </td>
                      <td className="p-4">{getStatusBadge(pr.status)}</td>
                      <td className="p-4 text-xs text-muted-foreground">{formatDate(pr.created_at)}</td>
                      <td className="p-4">
                        {pr.status === "Draft" && (
                          <Button size="sm" variant="outline" onClick={() => handleSubmit(pr.pr_id)}>
                            Submit
                          </Button>
                        )}
                        {(["Pending", "Under Review", "Submitted", "Pending Manager Approval", "Pending Finance Approval", "Pending CFO Approval", "Approved", "Completed"].includes(pr.status)) && (
                          <Button size="sm" onClick={() => setSelectedPr(pr)}>
                            {["Approved", "Completed"].includes(pr.status) ? "View" : "Review"}
                          </Button>
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

      {/* Creation Modal */}
      <Dialog isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Create Purchase Requisition">
        <form onSubmit={handleCreate} className="space-y-4">
          <Input
            id="title"
            label="Requisition Title"
            placeholder="e.g. Office Server Upgrades"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <Input
            id="cost"
            type="number"
            label="Estimated Cost (USD)"
            placeholder="e.g. 5000"
            value={estimatedCost}
            onChange={(e) => setEstimatedCost(e.target.value)}
          />
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">Priority Level</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">Justification / Details</label>
            <textarea
              placeholder="Provide context for approval"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px]"
            />
          </div>
          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Submitting..." : "Submit Requisition"}
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Review Dialog */}
      {selectedPr && (
        <Dialog isOpen={true} onClose={() => setSelectedPr(null)} title={`Review PR #${selectedPr.pr_number}`}>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 bg-muted/40 p-3 rounded-lg border border-border text-xs">
              <div>
                <span className="block text-muted-foreground font-semibold uppercase">Requisition Title</span>
                <span className="font-bold text-sm uppercase tracking-wider text-foreground">{selectedPr.title}</span>
              </div>
              <div>
                <span className="block text-muted-foreground font-semibold uppercase">Estimated Cost</span>
                <span className="font-bold text-sm tracking-wider text-foreground">${selectedPr.total_estimated_amount?.toLocaleString()}</span>
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

            {/* Delivery Verification Section */}
            {purchaseOrders.filter(po => po.pr_id === selectedPr.pr_id).map(po => (
              <div key={po.po_id} className="mt-4 pt-4 border-t border-border">
                <h4 className="text-xs font-bold uppercase text-muted-foreground mb-3 tracking-wider">PO #{po.po_number} Deliveries</h4>
                <div className="space-y-3">
                  {po.items?.map((item: any) => (
                    <div key={item.po_item_id} className="bg-background border border-border p-3 rounded-lg shadow-sm">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-semibold text-sm">{item.item_name}</span>
                        <Badge variant={
                          item.delivery_verification_status === "Matched" ? "success" : 
                          item.delivery_verification_status === "Returned / Cancelled" ? "danger" : 
                          item.delivery_verification_status === "Vendor Delivered" ? "warning" : "neutral"
                        }>
                          {item.delivery_verification_status || "Pending"}
                        </Badge>
                      </div>
                      
                      {item.delivery_verification_status === "Vendor Delivered" && (
                        <div className="flex items-center gap-2 mt-2 pt-2 border-t border-border">
                          <Input
                            id={`verify-${item.po_item_id}`}
                            type="text"
                            placeholder="Enter received Unique ID..."
                            value={(window as any)[`verify_${item.po_item_id}`] || ""}
                            onChange={(e) => {
                              (window as any)[`verify_${item.po_item_id}`] = e.target.value;
                              // Force re-render just to update input (hacky but works for this demo scope)
                              setComment(comment + " "); 
                              setTimeout(() => setComment(comment.trim()), 0);
                            }}
                          />
                          <Button size="sm" onClick={async () => {
                            const val = (window as any)[`verify_${item.po_item_id}`];
                            if (!val) { toast.error("Enter the product unique ID"); return; }
                            try {
                              await api.post(`/purchase-orders/${po.po_id}/items/${item.po_item_id}/verify-delivery`, {
                                receiver_product_id: val
                              });
                              toast.success("Verification processed!");
                              fetchPRs();
                              const poRes = await api.get("/purchase-orders");
                              setPurchaseOrders(poRes.data);
                            } catch (e: any) {
                              toast.error(e.response?.data?.detail || "Failed to verify");
                            }
                          }}>Verify</Button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}

            <div className="flex justify-end space-x-2 pt-4 border-t border-border">
              <Button variant="outline" onClick={() => setSelectedPr(null)}>
                Close
              </Button>
              {(!["Approved", "Completed", "Cancelled", "Rejected"].includes(selectedPr.status)) && (
                selectedPr.requestor_id === user?.user_id || selectedPr.requested_by === user?.user_id ? (
                  <Button variant="danger" disabled={isSubmitting} onClick={() => handleAction("cancel")}>
                    Cancel Request
                  </Button>
                ) : (
                  <>
                    <Button variant="danger" disabled={isSubmitting} onClick={() => handleAction("reject")}>
                      Reject
                    </Button>
                    <Button disabled={isSubmitting} onClick={() => handleAction("approve")}>
                      Approve
                    </Button>
                  </>
                )
              )}
            </div>
          </div>
        </Dialog>
      )}
    </div>
  );
};
export default PurchaseRequisitions;
