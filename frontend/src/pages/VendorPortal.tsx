import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import { Card, CardHeader, CardTitle, CardContent, Button, Badge, Skeleton, Dialog, Input } from "../components/ui";
import { formatDate } from "../utils/helpers";
import toast from "react-hot-toast";

export const VendorPortal: React.FC = () => {
  const { user } = useAuth();
  
  const [rfqs, setRfqs] = useState<any[]>([]);
  const [quotations, setQuotations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Submit Quotation states
  const [selectedRfq, setSelectedRfq] = useState<any | null>(null);
  const [price, setPrice] = useState("");
  const [timeline, setTimeline] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [rfqRes, quoteRes] = await Promise.all([
        api.get("/rfqs"),
        api.get("/quotations"),
      ]);
      // For demonstration, open RFQs are shown to the vendor
      setRfqs(rfqRes.data);
      setQuotations(quoteRes.data);
    } catch (err) {
      console.error("Failed to load vendor portal data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenBid = (rfq: any) => {
    setSelectedRfq(rfq);
    setPrice("");
    setTimeline("");
  };

  const handleSubmitBid = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!price || !timeline) {
      toast.error("Please enter a price proposal and delivery timeline.");
      return;
    }
    setIsSubmitting(true);
    try {
      await api.post("/quotations", {
        rfq_id: selectedRfq.rfq_id,
        total_price: parseFloat(price),
        delivery_timeline_days: parseInt(timeline),
        is_selected: false,
      });
      toast.success("Quotation submitted successfully!");
      setSelectedRfq(null);
      fetchData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to submit quotation bid.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Welcome Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-[10px] font-bold tracking-widest text-primary uppercase bg-primary/10 px-2.5 py-1 rounded-full border border-primary/20">
              Supplier Partner Workspace
            </span>
            <h1 className="text-3xl font-extrabold tracking-tight text-white mt-3">
              Welcome, {user?.first_name || "Supplier Partner"}
            </h1>
            <p className="text-slate-400 text-xs mt-1">
              Active Vendor Code: <span className="font-mono text-primary font-bold">{user?.employee_code}</span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="success">Active Status</Badge>
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-center min-w-[100px]">
              <span className="block text-[10px] text-slate-500 font-bold uppercase tracking-wider">Rating Index</span>
              <span className="text-lg font-extrabold text-white">95 / 100</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Active Bids / Open RFQs */}
        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Open Requests for Quotation (RFQs)</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 space-y-4">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            ) : rfqs.length === 0 ? (
              <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
                No active RFQs at the moment. Check back later.
              </div>
            ) : (
              <div className="divide-y divide-border">
                {rfqs.map((rfq) => (
                  <div key={rfq.rfq_id} className="p-4 hover:bg-accent/10 transition-colors flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold font-mono text-primary">#{rfq.rfq_number}</span>
                        <Badge variant="warning">Open for Bids</Badge>
                      </div>
                      <h4 className="text-sm font-bold text-foreground/90 mt-1">{rfq.title}</h4>
                      <span className="text-[10px] text-muted-foreground block mt-0.5">
                        Deadline: {formatDate(rfq.submission_deadline)}
                      </span>
                    </div>
                    <Button size="sm" onClick={() => handleOpenBid(rfq)}>
                      Submit Bid
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right: Submitted Quotation Statuses */}
        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Your Submitted Quotations</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 space-y-4">
                <Skeleton className="h-8 w-full" />
              </div>
            ) : quotations.length === 0 ? (
              <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
                You haven't submitted any bids yet.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-border bg-accent/40 text-[10px] font-bold text-muted-foreground uppercase">
                      <th className="p-4">Bid ID</th>
                      <th className="p-4">RFQ Ref</th>
                      <th className="p-4">Bid Price</th>
                      <th className="p-4">Timeline</th>
                      <th className="p-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {quotations.map((q) => (
                      <tr key={q.quotation_id} className="hover:bg-accent/10">
                        <td className="p-4 font-mono font-bold text-xs">#QT-{q.quotation_id}</td>
                        <td className="p-4 font-mono text-xs">#RFQ-{q.rfq_id}</td>
                        <td className="p-4 font-bold text-primary">${q.total_price?.toLocaleString()}</td>
                        <td className="p-4 text-xs">{q.delivery_timeline_days} days</td>
                        <td className="p-4">
                          <Badge variant={q.is_selected ? "success" : "neutral"}>
                            {q.is_selected ? "Accepted" : "Under Evaluation"}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Bid Submission Dialog */}
      {selectedRfq && (
        <Dialog isOpen={true} onClose={() => setSelectedRfq(null)} title={`Submit Bid for RFQ #${selectedRfq.rfq_number}`}>
          <form onSubmit={handleSubmitBid} className="space-y-4">
            <div className="bg-muted/40 p-3 rounded-lg border border-border text-xs">
              <span className="block font-semibold text-muted-foreground uppercase">RFQ Title</span>
              <span className="font-bold text-sm text-foreground/90">{selectedRfq.title}</span>
            </div>

            <Input
              id="price"
              type="number"
              label="Price Proposal ($)"
              placeholder="e.g. 5200"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
            />

            <Input
              id="timeline"
              type="number"
              label="Estimated Delivery / Completion (Days)"
              placeholder="e.g. 14"
              value={timeline}
              onChange={(e) => setTimeline(e.target.value)}
            />

            <div className="flex justify-end space-x-2 pt-4 border-t border-border">
              <Button variant="outline" type="button" onClick={() => setSelectedRfq(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Submitting Bid..." : "Submit Quotation Bid"}
              </Button>
            </div>
          </form>
        </Dialog>
      )}
    </div>
  );
};
export default VendorPortal;
