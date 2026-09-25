import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import {Card, CardHeader, CardTitle, CardContent, Button, Badge, Skeleton, Dialog, Input, EmptyState} from "../components/ui";
import { formatDate, isValidText } from "../utils/helpers";
import toast from "react-hot-toast";

export const VendorPortal: React.FC = () => {
  const { user } = useAuth();
  
  const [rfqs, setRfqs] = useState<any[]>([]);
  const [quotations, setQuotations] = useState<any[]>([]);
  const [vendorProfile, setVendorProfile] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Submit Quotation states
  const [selectedRfq, setSelectedRfq] = useState<any | null>(null);
  const [timeline, setTimeline] = useState("");
  const [itemPrices, setItemPrices] = useState<Record<number, { unit_price: string, tax_amount: string }>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [rfqRes, quoteRes, vendorRes] = await Promise.all([
        api.get("/rfq"),
        api.get("/quotations"),
        api.get("/vendors/me").catch(() => ({ data: null }))
      ]);
      setRfqs(rfqRes.data);
      setQuotations(quoteRes.data);
      if (vendorRes.data) setVendorProfile(vendorRes.data);
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
    setTimeline("");
    const initialPrices: Record<number, { unit_price: string, tax_amount: string }> = {};
    if (rfq.items) {
      rfq.items.forEach((item: any) => {
        initialPrices[item.rfq_item_id] = { unit_price: "", tax_amount: "0" };
      });
    }
    setItemPrices(initialPrices);
  };

  const handleSubmitBid = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!timeline || !isValidText(timeline)) {
      toast.error("Please enter a valid delivery timeline (letters or numbers required).");
      return;
    }
    
    const itemsPayload: any[] = [];
    if (selectedRfq.items) {
      for (const item of selectedRfq.items) {
        const pricing = itemPrices[item.rfq_item_id];
        if (!pricing || !pricing.unit_price) {
          toast.error(`Please enter a unit price for ${item.item_name}`);
          return;
        }
        itemsPayload.push({
          rfq_item_id: item.rfq_item_id,
          unit_price: parseFloat(pricing.unit_price),
          tax_amount: parseFloat(pricing.tax_amount || "0"),
          discount_amount: 0
        });
      }
    }

    setIsSubmitting(true);
    try {
      await api.post("/quotations", {
        rfq_id: selectedRfq.rfq_id,
        vendor_id: vendorProfile?.vendor_id || 0, 
        lead_time_days: parseInt(timeline),
        items: itemsPayload
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
              Welcome, {vendorProfile?.vendor_name || user?.first_name || "Supplier Partner"}
            </h1>
            <p className="text-slate-400 text-xs mt-1">
              Active Vendor Code: <span className="font-mono text-primary font-bold">{vendorProfile?.vendor_code || user?.employee_code}</span>
            </p>
          </div>
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <Badge variant="success">Active Status</Badge>
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-center min-w-[100px]">
              <span className="block text-[10px] text-slate-500 font-bold uppercase tracking-wider">Quality Score</span>
              <span className="text-lg font-extrabold text-white">{vendorProfile?.performance?.quality_score || "100.00"}</span>
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
            ) : rfqs.filter(rfq => !quotations.some(q => q.rfq_id === rfq.rfq_id)).length === 0 ? (
              <EmptyState title="No active RFQs at the moment. Check back later." description="Data will appear here once available." />
            ) : (
              <div className="divide-y divide-border">
                {rfqs.filter(rfq => !quotations.some(q => q.rfq_id === rfq.rfq_id)).map((rfq) => (
                  <div key={rfq.rfq_id} className="p-4 hover:bg-accent/10 transition-colors flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold font-mono text-primary">#{rfq.rfq_number}</span>
                        <Badge variant="warning">Open for Bids</Badge>
                        {rfq.pr_id && <Badge variant="neutral">PR #{rfq.pr_id}</Badge>}
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
                        <td className="p-4 font-bold text-primary">${q.total_amount?.toLocaleString()}</td>
                        <td className="p-4 text-xs">{q.lead_time_days} days</td>
                        <td className="p-4">
                          <Badge 
                            variant={
                              (q.is_selected || q.status === "Selected") ? "success" : 
                              (q.status === "Rejected") ? "destructive" : "neutral"
                            }
                          >
                            {(q.is_selected || q.status === "Selected") ? "Pending PO" : 
                             (q.status === "Rejected") ? "Bid Lost" : "Under Evaluation"}
                          </Badge>
                          {(q.is_selected || q.status === "Selected") && (
                            <div className="text-[10px] text-primary mt-1 font-semibold">
                              Awaiting PO Generation
                            </div>
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
      </div>



      {/* Bid Submission Dialog */}
      {selectedRfq && (
        <Dialog isOpen={true} onClose={() => setSelectedRfq(null)} title={`Submit Bid for RFQ #${selectedRfq.rfq_number}`}>
          <form onSubmit={handleSubmitBid} className="space-y-4">
            <div className="bg-muted/40 p-3 rounded-lg border border-border text-xs">
              <span className="block font-semibold text-muted-foreground uppercase">RFQ Title</span>
              <span className="font-bold text-sm text-foreground/90">{selectedRfq.title}</span>
            </div>


            {selectedRfq.items && selectedRfq.items.length > 0 && (
              <div className="bg-background rounded-lg border border-border mt-4">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-border bg-accent/40 text-[10px] font-bold text-muted-foreground uppercase">
                      <th className="p-3">Item Name</th>
                      <th className="p-3">Qty</th>
                      <th className="p-3">Unit Price ($)</th>
                      <th className="p-3">Tax ($)</th>
                      <th className="p-3">Total ($)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {selectedRfq.items.map((item: any) => {
                      const pricing = itemPrices[item.rfq_item_id] || { unit_price: "0", tax_amount: "0" };
                      const unit = parseFloat(pricing.unit_price || "0");
                      const tax = parseFloat(pricing.tax_amount || "0");
                      const lineTotal = (unit * item.quantity) + tax;
                      
                      return (
                        <tr key={item.rfq_item_id}>
                          <td className="p-3">
                            <div className="font-semibold text-xs text-foreground/90">{item.item_name}</div>
                            {item.specification && <div className="text-[10px] text-muted-foreground">{item.specification}</div>}
                          </td>
                          <td className="p-3 font-mono text-xs">{item.quantity}</td>
                          <td className="p-3">
                            <input
                              type="number"
                              min="0"
                              step="0.01"
                              className="w-24 px-2 py-1.5 text-xs border border-primary/40 rounded-md bg-muted/50 text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all shadow-sm"
                              placeholder="0.00"
                              value={pricing.unit_price}
                              onChange={(e) => setItemPrices({
                                ...itemPrices,
                                [item.rfq_item_id]: { ...pricing, unit_price: e.target.value }
                              })}
                            />
                          </td>
                          <td className="p-3">
                            <input
                              type="number"
                              min="0"
                              step="0.01"
                              className="w-20 px-2 py-1.5 text-xs border border-primary/40 rounded-md bg-muted/50 text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all shadow-sm"
                              placeholder="0.00"
                              value={pricing.tax_amount}
                              onChange={(e) => setItemPrices({
                                ...itemPrices,
                                [item.rfq_item_id]: { ...pricing, tax_amount: e.target.value }
                              })}
                            />
                          </td>
                          <td className="p-3 font-bold text-primary text-xs">
                            ${lineTotal.toFixed(2)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                <div className="p-3 bg-muted/20 flex justify-end font-bold text-sm">
                  Grand Total: $<span className="text-primary ml-1">
                    {selectedRfq.items.reduce((acc: number, item: any) => {
                      const pricing = itemPrices[item.rfq_item_id] || { unit_price: "0", tax_amount: "0" };
                      return acc + (parseFloat(pricing.unit_price || "0") * item.quantity) + parseFloat(pricing.tax_amount || "0");
                    }, 0).toFixed(2)}
                  </span>
                </div>
              </div>
            )}

            <Input
              id="timeline"
              type="number"
              label="Estimated Delivery / Completion (Days)"
              placeholder="e.g. 14"
              value={timeline}
              onChange={(e) => setTimeline(e.target.value)}
            />

            <div className="flex justify-end space-x-2 pt-3 mt-2 border-t border-border">
              <Button variant="close" type="button" onClick={() => setSelectedRfq(null)}>Cancel</Button>
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
