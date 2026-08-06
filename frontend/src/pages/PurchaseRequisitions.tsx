import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { PurchaseRequisition } from "../types";
import { Button, Input, Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, Dialog } from "../components/ui";
import toast from "react-hot-toast";
import { formatDate, getErrorMessage } from "../utils/helpers";

export const PurchaseRequisitions: React.FC = () => {
  const [prs, setPrs] = useState<PurchaseRequisition[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState("All");

  // Form states
  const [title, setTitle] = useState("");
  const [estimatedCost, setEstimatedCost] = useState("");
  const [priority, setPriority] = useState("Medium");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchPRs = async () => {
    setLoading(true);
    try {
      const response = await api.get("/pr");
      setPrs(response.data);
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
      await api.post("/pr", {
        title,
        justification: description || "No justification provided",
        priority,
        department_id: 1,
        items: [
          {
            category: "Standard",
            item_name: title,
            quantity: 1,
            unit_price: parseFloat(estimatedCost)
          }
        ]
      });
      toast.success("Purchase Requisition created successfully!");
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

  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase();
    if (s === "approved" || s === "completed") return <Badge variant="success">{status}</Badge>;
    if (s === "pending" || s === "under_review" || s === "submitted") return <Badge variant="warning">{status}</Badge>;
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
        <Button onClick={() => setIsCreateOpen(true)} className="font-bold text-xs uppercase tracking-wider">
          New Requisition
        </Button>
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
            <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              No Requisitions found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    <th className="p-4">PR Number</th>
                    <th className="p-4">Title</th>
                    <th className="p-4">Estimated Cost</th>
                    <th className="p-4">Priority</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Date Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-sm">
                  {filteredPrs.map((pr) => (
                    <tr key={pr.pr_id} className="hover:bg-accent/20 transition-colors">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{pr.pr_number}</td>
                      <td className="p-4 font-semibold">{pr.title}</td>
                      <td className="p-4 font-bold">${pr.total_estimated_amount?.toLocaleString()}</td>
                      <td className="p-4">
                        <Badge variant={pr.priority === "High" ? "error" : pr.priority === "Medium" ? "warning" : "neutral"}>
                          {pr.priority}
                        </Badge>
                      </td>
                      <td className="p-4">{getStatusBadge(pr.status)}</td>
                      <td className="p-4 text-xs text-muted-foreground">{formatDate(pr.created_at)}</td>
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
    </div>
  );
};
export default PurchaseRequisitions;
