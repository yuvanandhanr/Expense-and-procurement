import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { PurchaseRequisition } from "../types";
import { Button, Input, Card, CardHeader, CardTitle, CardContent, Badge, StatusBadge, Skeleton, Dialog, HeroTimestamp, EmptyState } from "../components/ui";
import { ClipboardList, Plus, Eye, Send, Check, X, Ban } from "lucide-react";
import toast from "react-hot-toast";
import { formatDate, getErrorMessage, isValidText } from "../utils/helpers";
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
  const [specification, setSpecification] = useState("");
  const [justification, setJustification] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [physicalInspectionDone, setPhysicalInspectionDone] = useState(false);
  const [allocateAssetId, setAllocateAssetId] = useState("");

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

  const handleCreate = async (e: React.FormEvent, isDraft: boolean = false) => {
    e.preventDefault();
    if (!title || !justification) {
      toast.error("Please fill in the required fields (Title and Justification).");
      return;
    }

    if (!isValidText(title) || !isValidText(justification)) {
      toast.error("Title and justification must contain letters or numbers.");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await api.post("/pr", {
        title,
        justification: justification,
        department_id: user?.department_id || null,
        department_name: user?.department_name || null,
        employee_type: user?.employee_type || null,
        items: [
          {
            category: "Standard",
            item_name: title,
            specification: specification,
            quantity: 1,
            unit_price: 0
          }
        ]
      });

      if (!isDraft) {
        // Auto-submit the PR to trigger the workflow
        if (res.data && res.data.pr_id) {
          await api.post(`/pr/${res.data.pr_id}/submit`);
        }
        toast.success("My Requisition created and submitted successfully!");
      } else {
        toast.success("My Requisition saved as draft!");
      }

      setIsCreateOpen(false);
      // Reset form
      setTitle("");
      setSpecification("");
      setJustification("");
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
      if (action === "cancel" || action === "reject") {
        if (!comment.trim() || !isValidText(comment)) {
          toast.error(`Please provide a valid reason for ${action === "cancel" ? "cancellation" : "rejection"} (letters or numbers required).`);
          setIsSubmitting(false);
          return;
        }
        await api.post(`/pr/${selectedPr.pr_id}/${action}`, { comments: comment });
        toast.success(`My Requisition successfully ${action === "cancel" ? "cancelled" : "rejected"}!`);
      } else {
        await api.post(`/pr/${selectedPr.pr_id}/${action}`, {
          comments: comment,
          physical_inspection_done: physicalInspectionDone
        });
        toast.success(`My Requisition successfully ${action}d!`);
      }
      setSelectedPr(null);
      setComment("");
      setPhysicalInspectionDone(false);
      setAllocateAssetId("");
      fetchPRs();
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Failed to process workflow action."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAdminAction = async (type: "allocate" | "procure") => {
    if (!selectedPr) return;
    setIsSubmitting(true);
    try {
      if (type === "allocate") {
        if (!allocateAssetId) {
          toast.error("Please provide an Asset ID to allocate.");
          setIsSubmitting(false);
          return;
        }
        await api.post(`/pr/${selectedPr.pr_id}/allocate-inventory`, { asset_id: parseInt(allocateAssetId) });
        toast.success("Asset allocated from inventory successfully!");
      } else {
        await api.post(`/pr/${selectedPr.pr_id}/initiate-procurement`);
        toast.success("Procurement initiated. Escalated to CFO.");
      }
      setSelectedPr(null);
      setComment("");
      setAllocateAssetId("");
      fetchPRs();
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Failed to process Admin action."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async (prId: number) => {
    try {
      await api.post(`/pr/${prId}/submit`);
      toast.success("My Requisition submitted successfully!");
      fetchPRs();
    } catch (err: any) {
      toast.error(getErrorMessage(err, "Failed to submit PR."));
    }
  };

  const getStatusBadge = (status: string) => {
    return <StatusBadge status={status} />;
  };

  const subTabCounts: Record<string, number> = {
    All: prs.length,
    Draft: prs.filter((pr) => pr.status === "Draft").length,
    Submitted: prs.filter((pr) => {
      const s = pr.status.toLowerCase();
      return s.includes("pending") || s === "submitted" || s === "under review";
    }).length,
    Approved: prs.filter((pr) => pr.status === "Approved" || pr.status === "Completed").length,
    Rejected: prs.filter((pr) => pr.status === "Rejected" || pr.status === "Cancelled").length,
    "Return for Correction": prs.filter((pr) => pr.status === "Returned for Correction").length,
  };

  const filteredPrs = prs.filter((pr) => {
    if (statusFilter === "All") return true;
    if (statusFilter === "Submitted") {
      const s = pr.status.toLowerCase();
      return s.includes("pending") || s === "submitted" || s === "under review";
    }
    if (statusFilter === "Return for Correction") return pr.status === "Returned for Correction";
    return pr.status.toLowerCase() === statusFilter.toLowerCase();
  });

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Requisitions</h1>
          <p className="text-xs text-muted-foreground mt-1">Submit and track department purchase requests.</p>
        </div>
        <div className="flex items-center space-x-4">
          <HeroTimestamp />
          <Button onClick={() => setIsCreateOpen(true)} className="font-bold text-xs uppercase tracking-wider gap-1.5 shadow-apple-glow">
            <Plus className="w-4 h-4" /> New Requisition
          </Button>
        </div>
      </div>

      {/* Filters & Controls */}
      <div className="flex flex-wrap items-center space-x-2 bg-muted/40 p-1.5 rounded-xl w-fit border border-border/50 gap-y-2">
        {["All", "Draft", "Submitted", "Approved", "Rejected", "Return for Correction"].map((status) => (
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
                    <th className="p-4 whitespace-nowrap">PR Number</th>
                    <th className="p-4 whitespace-nowrap">Requestor Name</th>
                    <th className="p-4">Title</th>
                    <th className="p-4 whitespace-nowrap">Estimated Cost</th>
                    <th className="p-4 whitespace-nowrap">Priority</th>
                    <th className="p-4 whitespace-nowrap">Status</th>
                    <th className="p-4 whitespace-nowrap">Date Created</th>
                    <th className="p-4 whitespace-nowrap">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-sm">
                  {filteredPrs.map((pr) => (
                    <tr key={pr.pr_id} className="hover:bg-accent/20 transition-colors">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary whitespace-nowrap">{pr.pr_number}</td>
                      <td className="p-4 whitespace-nowrap">{pr.requestor_name || "Unknown"}</td>
                      <td className="p-4 font-semibold">{pr.title}</td>
                      <td className="p-4 font-bold whitespace-nowrap">{pr.total_estimated_amount > 0 ? `₹${pr.total_estimated_amount?.toLocaleString()}` : "TBD"}</td>
                      <td className="p-4 whitespace-nowrap">
                        <Badge variant={pr.priority === "High" ? "error" : pr.priority === "Medium" ? "warning" : "neutral"}>
                          {pr.priority || "Standard"}
                        </Badge>
                      </td>
                      <td className="p-4 whitespace-nowrap">
                        <StatusBadge status={pr.status} />
                      </td>
                      <td className="p-4 text-xs text-muted-foreground whitespace-nowrap">{formatDate(pr.created_at)}</td>
                      <td className="p-4 whitespace-nowrap">
                        {pr.status === "Draft" ? (
                          <Button size="sm" variant="outline" onClick={() => handleSubmit(pr.pr_id)} className="gap-1.5">
                            <Send className="w-3.5 h-3.5" /> Submit
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant={["Approved", "Completed", "Rejected", "Cancelled"].includes(pr.status) ? "view" : "primary"}
                            onClick={() => setSelectedPr(pr)}
                            className="gap-1.5 shadow-apple-sm"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            {["Approved", "Completed", "Rejected", "Cancelled"].includes(pr.status) ? "View" : 
                             (pr.requestor_id === user?.user_id ? "View Details" : "Review")}
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
      <Dialog isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Create My Requisition">
        <form onSubmit={(e) => handleCreate(e, false)} className="space-y-4">
          <Input
            id="title"
            label="What do you need?"
            placeholder="e.g. MacBook Pro M3"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">Requirements / Specifications</label>
            <textarea
              placeholder="e.g. 16GB RAM, 512GB SSD"
              value={specification}
              onChange={(e) => setSpecification(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring min-h-[60px]"
            />
          </div>
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">Why do you need it? (Business Reason) <span className="text-red-500">*</span></label>
            <textarea
              placeholder="Provide context for approval and actual problem being solved..."
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px]"
              required
            />
          </div>
          <div className="flex justify-end space-x-2 pt-3">
            <Button variant="close" type="button"  onClick={() => setIsCreateOpen(false)}>Cancel</Button>
            <Button type="button" variant="secondary" disabled={isSubmitting} onClick={(e) => handleCreate(e, true)}>
              {isSubmitting ? "Saving..." : "Save as Draft"}
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
          <div className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-muted/30 p-4 rounded-xl border border-border/60">
                <span className="block text-[10px] text-muted-foreground font-bold uppercase tracking-widest mb-1.5">What do you need?</span>
                <span className="font-bold text-base text-foreground leading-tight">{selectedPr.title}</span>
              </div>
              <div className="bg-muted/30 p-4 rounded-xl border border-border/60">
                <span className="block text-[10px] text-muted-foreground font-bold uppercase tracking-widest mb-1.5">Requirements / Specifications</span>
                <span className="font-medium text-sm text-foreground">
                  {selectedPr.items && selectedPr.items.length > 0 && (selectedPr.items[0] as any).specification 
                    ? (selectedPr.items[0] as any).specification 
                    : "None provided."}
                </span>
              </div>
              <div className="bg-muted/30 p-4 rounded-xl border border-border/60 md:col-span-2">
                <span className="block text-[10px] text-muted-foreground font-bold uppercase tracking-widest mb-1.5">Business Justification</span>
                <span className="font-medium text-sm text-foreground leading-relaxed">{selectedPr.justification || "None provided."}</span>
              </div>
            </div>

            {/* Actionable Sections (Hidden in View Mode) */}
            {(!["Approved", "Completed", "Cancelled", "Rejected"].includes(selectedPr.status)) && (
              <>
                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    {selectedPr.requestor_id === user?.user_id || selectedPr.requested_by === user?.user_id ? "Reason for Cancellation *" : "Comments / Decision Notes"}
                  </label>
                  <textarea
                    placeholder={selectedPr.requestor_id === user?.user_id || selectedPr.requested_by === user?.user_id ? "Provide a reason for canceling this request..." : "Include details explaining your decision (required if rejecting)"}
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px]"
                  />
                </div>

                {/* Delivery Verification Section */}
                {purchaseOrders.filter(po => po.pr_id === selectedPr.pr_id).map(po => (
                  <div key={po.po_id} className="mt-4 pt-3 mt-2 border-t border-border">
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

                {selectedPr.requestor_id !== user?.user_id && user?.roles?.some(r => r.role_name === "Manager") && selectedPr.status === "Pending Manager Approval" && (
                  <div className="flex items-center space-x-2 bg-muted/30 p-3 rounded-lg border border-border mt-4">
                    <input
                      type="checkbox"
                      id="physical_inspection"
                      checked={physicalInspectionDone}
                      onChange={(e) => setPhysicalInspectionDone(e.target.checked)}
                      className="w-4 h-4 text-primary rounded border-border focus:ring-primary"
                    />
                    <label htmlFor="physical_inspection" className="text-sm font-semibold">
                      Physical Inspection Completed <span className="text-red-500">*</span>
                    </label>
                  </div>
                )}

                {selectedPr.requestor_id !== user?.user_id && user?.roles?.some(r => r.role_name === "Admin") && (selectedPr.status === "Pending Admin Approval" || selectedPr.status === "Under Review") && (
                  <div className="mt-4 p-4 border border-border bg-muted/20 rounded-lg space-y-4">
                    <h4 className="font-bold text-sm">Asset Inventory Check & Resolution</h4>
                    
                    <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs space-y-1">
                      <span className="font-bold text-amber-600 block">Inventory Assessment Rule:</span>
                      <p className="text-muted-foreground">
                        If available stock &gt; 5, allocate an existing asset to close this requisition. If stock &le; 5 or unavailable, you can push the requirement to Finance Manager to start vendor RFQ procurement.
                      </p>
                    </div>

                    <div className="space-y-2">
                      <label className="text-xs font-semibold text-muted-foreground uppercase">Option A: Allocate from Available Inventory (Stock &gt; 0)</label>
                      <div className="flex gap-2">
                        <Input 
                          id="allocate-asset-id"
                          placeholder="Enter Available Asset ID..." 
                          value={allocateAssetId}
                          onChange={(e) => setAllocateAssetId(e.target.value)}
                        />
                        <Button onClick={() => handleAdminAction("allocate")} variant="primary" disabled={isSubmitting}>
                          Allocate Asset
                        </Button>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-border space-y-2">
                      <label className="text-xs font-semibold text-muted-foreground uppercase">Option B: Low Stock / No Stock (Stock &le; 5)</label>
                      <p className="text-xs text-muted-foreground">Push this requirement to the Finance Manager to initiate RFQ and vendor quotation bidding.</p>
                      <Button onClick={() => handleAdminAction("procure")} variant="warning" className="w-full font-bold" disabled={isSubmitting}>
                        Push to Finance Manager (Start RFQ Procurement)
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}

            <div className="flex justify-end space-x-2 pt-3 border-t border-border mt-2">
              <Button variant="close" onClick={() => setSelectedPr(null)}>Close</Button>
              {(!["Approved", "Completed", "Cancelled", "Rejected"].includes(selectedPr.status)) && (
                selectedPr.requestor_id === user?.user_id || selectedPr.requested_by === user?.user_id ? (
                  <Button variant="danger" disabled={isSubmitting} onClick={() => handleAction("cancel")} className="gap-1.5 font-bold">
                    <Ban className="w-4 h-4" /> Cancel Request
                  </Button>
                ) : (
                  <>
                    <Button variant="danger" disabled={isSubmitting} onClick={() => handleAction("reject")} className="gap-1.5 font-bold">
                      <X className="w-4 h-4" /> Reject
                    </Button>
                    <Button variant="success" disabled={isSubmitting} onClick={() => handleAction("approve")} className="gap-1.5 font-bold shadow-apple-sm">
                      <Check className="w-4 h-4" /> Approve Requisition
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
