import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import { Card, CardHeader, CardTitle, CardContent, Button, Badge, Skeleton, Dialog, Input, EmptyState, StatusBadge } from "../components/ui";
import { formatDate, isValidText, canViewAmount } from "../utils/helpers";
import toast from "react-hot-toast";
import { Eye, Package, Send, CheckCircle2, ShoppingBag } from "lucide-react";

export const VendorPortal: React.FC = () => {
  const { user } = useAuth();
  
  const [rfqs, setRfqs] = useState<any[]>([]);
  const [quotations, setQuotations] = useState<any[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<any[]>([]);
  const [vendorProfile, setVendorProfile] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Submit Quotation states
  const [selectedRfq, setSelectedRfq] = useState<any | null>(null);
  const [viewRfq, setViewRfq] = useState<any | null>(null);
  const [timeline, setTimeline] = useState("");
  const [itemPrices, setItemPrices] = useState<Record<number, { unit_price: string, tax_amount: string }>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Vendor Delivery Dispatch states
  const [dispatchItem, setDispatchItem] = useState<any | null>(null);
  const [vendorProductId, setVendorProductId] = useState("");
  const [isDispatching, setIsDispatching] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [rfqRes, quoteRes, vendorRes, poRes] = await Promise.all([
        api.get("/rfq"),
        api.get("/quotations"),
        api.get("/vendors/me").catch(() => ({ data: null })),
        api.get("/purchase-orders").catch(() => ({ data: [] }))
      ]);
      setRfqs(rfqRes.data || []);
      setQuotations(quoteRes.data || []);
      if (vendorRes.data) setVendorProfile(vendorRes.data);
      setPurchaseOrders(poRes.data || []);
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
      toast.error("Please enter a valid delivery timeline (number of days).");
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

  const handleDispatchItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vendorProductId.trim()) {
      toast.error("Please enter the Product Unique ID / Serial Tag.");
      return;
    }
    setIsDispatching(true);
    try {
      await api.post(`/purchase-orders/${dispatchItem.po_id}/items/${dispatchItem.po_item_id}/deliver`, {
        vendor_product_id: vendorProductId.trim()
      });
      toast.success("Item dispatched and delivery status updated!");
      setDispatchItem(null);
      setVendorProductId("");
      fetchData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to record dispatch.");
    } finally {
      setIsDispatching(false);
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
              <EmptyState title="No active RFQs at the moment. Check back later." description="Newly published RFQs and Requisitions will appear here." />
            ) : (
              <div className="divide-y divide-border">
                {rfqs.filter(rfq => !quotations.some(q => q.rfq_id === rfq.rfq_id)).map((rfq) => {
                  const reqRef = rfq.pr_number || rfq.requisition_ref || (rfq.pr_id ? `PR-${rfq.pr_id}` : null);
                  return (
                    <div key={rfq.rfq_id} className="p-4 hover:bg-accent/10 transition-colors flex items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-bold font-mono text-primary">#{rfq.rfq_number}</span>
                          <Badge variant="warning">Open for Bids</Badge>
                          {reqRef && <Badge variant="neutral">REF: {reqRef}</Badge>}
                        </div>
                        <h4 className="text-sm font-bold text-foreground/90 mt-1">{rfq.title}</h4>
                        <span className="text-[10px] text-muted-foreground block mt-0.5">
                          Deadline: {formatDate(rfq.submission_deadline)}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Button size="sm" variant="outline" onClick={() => setViewRfq(rfq)}>
                          <Eye className="w-3.5 h-3.5 mr-1" /> View Details
                        </Button>
                        <Button size="sm" onClick={() => handleOpenBid(rfq)}>
                          Submit Bid
                        </Button>
                      </div>
                    </div>
                  );
                })}
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
                      {canViewAmount(user) && <th className="p-4">Bid Price</th>}
                      <th className="p-4">Timeline</th>
                      <th className="p-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {quotations.map((q) => (
                      <tr key={q.quotation_id} className="hover:bg-accent/10">
                        <td className="p-4 font-mono font-bold text-xs">#QT-{q.quotation_id}</td>
                        <td className="p-4 font-mono text-xs">#RFQ-{q.rfq_id}</td>
                        {canViewAmount(user) && (
                          <td className="p-4 font-bold text-primary">₹{q.total_amount?.toLocaleString()}</td>
                        )}
                        <td className="p-4 text-xs">{q.lead_time_days} days</td>
                        <td className="p-4">
                          <Badge 
                            variant={
                              (q.is_selected || q.status === "Selected") ? "success" : 
                              (q.status === "Rejected") ? "destructive" : "neutral"
                            }
                          >
                            {(q.is_selected || q.status === "Selected") ? "Winning Bid" : 
                             (q.status === "Rejected") ? "Bid Lost" : "Under Evaluation"}
                          </Badge>
                          {(q.is_selected || q.status === "Selected") && (
                            <div className="text-[10px] text-primary mt-1 font-semibold flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3 text-emerald-500" /> Confirmed / PO Issued
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

      {/* Awarded Purchase Orders Section (Requirement 3: PO Accessible to Specific Winning Vendor) */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <ShoppingBag className="w-5 h-5 text-primary" />
              Awarded Purchase Orders (POs)
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">
              Official binding Purchase Orders generated from your winning quotations.
            </p>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : purchaseOrders.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground">
              No Purchase Orders issued yet. Win an RFQ bid to receive purchase orders.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-[10px] font-bold text-muted-foreground uppercase">
                    <th className="p-4">PO Number</th>
                    <th className="p-4">Requisition REF</th>
                    <th className="p-4">Date Issued</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Items & Delivery Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {purchaseOrders.map((po) => {
                    const reqRef = po.pr_number || po.requisition_ref || (po.pr_id ? `PR-${po.pr_id}` : "—");
                    return (
                      <tr key={po.po_id} className="hover:bg-accent/10">
                        <td className="p-4 font-mono font-bold text-xs text-primary">{po.po_number}</td>
                        <td className="p-4 font-mono text-xs">{reqRef}</td>
                        <td className="p-4 text-xs text-muted-foreground">{formatDate(po.created_at)}</td>
                        <td className="p-4">
                          <StatusBadge status={po.status || "Issued"} />
                        </td>
                        <td className="p-4">
                          <div className="space-y-2">
                            {po.items && po.items.map((item: any) => (
                              <div key={item.po_item_id} className="flex items-center justify-between gap-3 text-xs bg-muted/40 p-2 rounded-lg border border-border/60">
                                <div>
                                  <span className="font-semibold">{item.item_name}</span>
                                  <span className="text-muted-foreground ml-2">(Qty: {item.quantity})</span>
                                  {item.vendor_delivery_id && (
                                    <span className="block text-[10px] font-mono text-emerald-600 dark:text-emerald-400">
                                      Dispatched UID: {item.vendor_delivery_id}
                                    </span>
                                  )}
                                </div>
                                <div>
                                  {item.delivery_verification_status === "Matched" ? (
                                    <Badge variant="success">Delivered & Matched</Badge>
                                  ) : item.delivery_verification_status === "Vendor Delivered" ? (
                                    <Badge variant="warning">In Transit / Verification</Badge>
                                  ) : (
                                    <Button 
                                      size="sm" 
                                      variant="outline"
                                      onClick={() => {
                                        setDispatchItem({ ...item, po_id: po.po_id });
                                        setVendorProductId("");
                                      }}
                                    >
                                      <Package className="w-3.5 h-3.5 mr-1" /> Dispatch Item
                                    </Button>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* View Requisition Details Dialog (Requirement 1: Vendors can view requisition details) */}
      {viewRfq && (
        <Dialog isOpen={true} onClose={() => setViewRfq(null)} title={`Requisition Details: ${viewRfq.title}`}>
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-3 bg-muted/40 p-3 rounded-xl border border-border">
              <div>
                <span className="block text-[10px] font-bold uppercase text-muted-foreground">RFQ Number</span>
                <span className="font-mono font-bold text-primary">{viewRfq.rfq_number}</span>
              </div>
              <div>
                <span className="block text-[10px] font-bold uppercase text-muted-foreground">Requisition REF</span>
                <span className="font-mono font-bold text-foreground">
                  {viewRfq.pr_number || viewRfq.requisition_ref || (viewRfq.pr_id ? `PR-${viewRfq.pr_id}` : "N/A")}
                </span>
              </div>
              <div className="col-span-2">
                <span className="block text-[10px] font-bold uppercase text-muted-foreground">Description</span>
                <span className="text-foreground">{viewRfq.description || viewRfq.pr_description || "Standard Requisition"}</span>
              </div>
            </div>

            <div>
              <h4 className="font-bold text-xs uppercase tracking-wider text-muted-foreground mb-2">Required Items</h4>
              <div className="border border-border rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-muted/60 text-muted-foreground font-bold">
                    <tr>
                      <th className="p-3">Item Name</th>
                      <th className="p-3">Specification</th>
                      <th className="p-3 text-right">Required Quantity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {viewRfq.items && viewRfq.items.map((item: any) => (
                      <tr key={item.rfq_item_id}>
                        <td className="p-3 font-semibold">{item.item_name}</td>
                        <td className="p-3 text-muted-foreground">{item.specification || "Standard Spec"}</td>
                        <td className="p-3 text-right font-mono font-bold">{item.quantity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-border">
              <Button variant="close" onClick={() => setViewRfq(null)}>Close</Button>
              <Button onClick={() => {
                const targetRfq = viewRfq;
                setViewRfq(null);
                handleOpenBid(targetRfq);
              }}>
                Submit Quotation Bid
              </Button>
            </div>
          </div>
        </Dialog>
      )}

      {/* Bid Submission Dialog */}
      {selectedRfq && (
        <Dialog isOpen={true} onClose={() => setSelectedRfq(null)} title={`Submit Bid for RFQ #${selectedRfq.rfq_number}`}>
          <form onSubmit={handleSubmitBid} className="space-y-4">
            <div className="bg-muted/40 p-3 rounded-lg border border-border text-xs">
              <span className="block font-semibold text-muted-foreground uppercase">Requisition REF</span>
              <span className="font-mono font-bold text-primary block mb-1">
                {selectedRfq.pr_number || selectedRfq.requisition_ref || (selectedRfq.pr_id ? `PR-${selectedRfq.pr_id}` : "N/A")}
              </span>
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
                      <th className="p-3">Unit Price (₹)</th>
                      <th className="p-3">Tax (₹)</th>
                      <th className="p-3">Total (₹)</th>
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
                            ₹{lineTotal.toFixed(2)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                <div className="p-3 bg-muted/20 flex justify-end font-bold text-sm">
                  Grand Total: ₹<span className="text-primary ml-1">
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

      {/* Dispatch Item Dialog */}
      {dispatchItem && (
        <Dialog isOpen={true} onClose={() => setDispatchItem(null)} title="Dispatch / Deliver Item">
          <form onSubmit={handleDispatchItem} className="space-y-4">
            <div className="bg-muted/40 p-3 rounded-lg border border-border text-xs mb-2">
              <span className="block font-semibold text-muted-foreground uppercase">Item to Dispatch</span>
              <span className="font-bold text-sm text-foreground/90">{dispatchItem.item_name} (Qty: {dispatchItem.quantity})</span>
              <p className="mt-1 text-muted-foreground">
                Enter the physical Product Unique ID (Serial Tag / Asset UID) you are dispatching to the client. This will be verified upon delivery.
              </p>
            </div>

            <Input
              id="vendor_product_id"
              label="Product Unique ID / Serial Tag"
              placeholder="e.g. UID-DELL-8821"
              value={vendorProductId}
              onChange={(e) => setVendorProductId(e.target.value)}
              required
            />

            <div className="flex justify-end space-x-2 pt-3 border-t border-border">
              <Button variant="close" type="button" onClick={() => setDispatchItem(null)}>Cancel</Button>
              <Button type="submit" disabled={isDispatching}>
                {isDispatching ? "Recording Dispatch..." : "Confirm Dispatch"}
              </Button>
            </div>
          </form>
        </Dialog>
      )}
    </div>
  );
};
export default VendorPortal;
