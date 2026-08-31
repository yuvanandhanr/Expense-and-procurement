import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import {Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, Button, EmptyState} from "../components/ui";
import toast from "react-hot-toast";
import { Quotation } from "../types";

export const Quotations: React.FC = () => {
  const { user } = useAuth();
  const [quotes, setQuotes] = useState<Quotation[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedRfqId, setExpandedRfqId] = useState<number | null>(null);

  const groupedQuotes = React.useMemo(() => {
    return quotes.reduce((acc: Record<number, Quotation[]>, q) => {
      if (!acc[q.rfq_id]) acc[q.rfq_id] = [];
      acc[q.rfq_id].push(q);
      return acc;
    }, {});
  }, [quotes]);

  const fetchData = async () => {
    try {
      const [quotesRes, poRes] = await Promise.all([
        api.get("/quotations"),
        api.get("/purchase-orders")
      ]);
      setQuotes(quotesRes.data);
      setPurchaseOrders(poRes.data);
    } catch (err) {
      console.error("Failed to load data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApprove = async (quote: any) => {
    try {
      await api.post(`/rfq/${quote.rfq_id}/select-vendor`, {
        selected_vendor_id: quote.vendor_id,
        selected_quotation_id: quote.quotation_id,
        reason: "Approved by Finance"
      });
      toast.success("Quotation approved and Purchase Order auto-generated!");
      // Refetch both quotes and POs to get the newly generated PO
      fetchData();
    } catch (err: any) {
      console.error(err);
      toast.error(err.response?.data?.detail || "Failed to approve quotation.");
    }
  };

  const isFinanceManager = user?.roles?.some(r => ["Finance Manager", "CFO", "Admin"].includes(r.role_name)) || false;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Quotations Repository</h1>
        <p className="text-xs text-muted-foreground mt-1">Review proposals submitted by invited suppliers.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : quotes.length === 0 ? (
            <EmptyState title="No bids or quotations recorded yet." description="Data will appear here once available." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                    <th className="p-4">RFQ ID</th>
                    <th className="p-4">Total Bids</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {Object.entries(groupedQuotes).map(([rfqIdStr, rfqQuotes]) => {
                    const rfqId = Number(rfqIdStr);
                    const isExpanded = expandedRfqId === rfqId;
                    const hasSelected = rfqQuotes.some(q => q.is_selected || q.status === "Selected");

                    return (
                      <React.Fragment key={rfqId}>
                        <tr className="hover:bg-accent/20 cursor-pointer" onClick={() => setExpandedRfqId(isExpanded ? null : rfqId)}>
                          <td className="p-4 font-bold text-xs tracking-wider text-primary">
                            <span className="mr-2 text-muted-foreground font-mono">
                              {isExpanded ? "▼" : "▶"}
                            </span>
                            #RFQ-{rfqId}
                          </td>
                          <td className="p-4 font-medium">{rfqQuotes.length} Bid{rfqQuotes.length !== 1 ? 's' : ''}</td>
                          <td className="p-4">
                            <Badge variant={hasSelected ? "success" : "neutral"}>
                              {hasSelected ? "Awarded" : "Under Review"}
                            </Badge>
                          </td>
                          <td className="p-4 text-right">
                            <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); setExpandedRfqId(isExpanded ? null : rfqId); }}>
                              {isExpanded ? "Close" : "Review Bids"}
                            </Button>
                          </td>
                        </tr>
                        {isExpanded && (
                          <tr className="bg-accent/5">
                            <td colSpan={4} className="p-4">
                              <div className="bg-background rounded-lg border border-border overflow-hidden">
                                <table className="w-full text-left text-xs border-collapse">
                                  <thead>
                                    <tr className="bg-accent/30 text-muted-foreground uppercase border-b border-border">
                                      <th className="p-3 pl-4">Vendor</th>
                                      <th className="p-3">Quotation Ref</th>
                                      <th className="p-3">Total Price</th>
                                      <th className="p-3">Timeline</th>
                                      <th className="p-3">Status</th>
                                      <th className="p-3 text-right">Action</th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-border">
                                    {rfqQuotes.map((q) => {
                                      // Display "Rejected" dynamically if another quote is selected but not saved to db yet, 
                                      // though the backend should handle setting it to Rejected now.
                                      let statusDisplay = q.status;
                                      let variant = "neutral";
                                      if (q.status === "Selected" || q.is_selected) {
                                        statusDisplay = "Selected";
                                        variant = "success";
                                      } else if (q.status === "Rejected") {
                                        variant = "destructive";
                                      } else if (hasSelected) {
                                        statusDisplay = "Rejected";
                                        variant = "destructive";
                                      }

                                      return (
                                        <React.Fragment key={q.quotation_id}>
                                          <tr className="hover:bg-accent/10">
                                            <td className="p-3 pl-4 font-medium">{(q as any).vendor?.vendor_name || `Vendor #${q.vendor_id}`}</td>
                                            <td className="p-3 font-mono text-muted-foreground">#QT-{q.quotation_id}</td>
                                            <td className="p-3 font-bold text-primary">${Number(q.total_amount).toLocaleString()}</td>
                                            <td className="p-3">{q.lead_time_days} days</td>
                                            <td className="p-3">
                                              <Badge variant={variant as any}>{statusDisplay}</Badge>
                                            </td>
                                            <td className="p-3 text-right">
                                              {isFinanceManager && !hasSelected && (
                                                <Button size="sm" onClick={() => handleApprove(q)}>Approve</Button>
                                              )}
                                            </td>
                                          </tr>
                                          
                                          {/* Auto-Generated Purchase Order Details if this quote is selected */}
                                          {(q.is_selected || q.status === "Selected") && (
                                            (() => {
                                              const linkedPo = purchaseOrders.find(
                                                po => po.rfq_id === q.rfq_id && po.vendor_id === q.vendor_id
                                              );
                                              if (!linkedPo) return null;
                                              return (
                                                <tr className="bg-primary/5">
                                                  <td colSpan={6} className="p-4 border-l-4 border-primary">
                                                    <div className="flex items-center justify-between mb-2">
                                                      <h4 className="font-bold text-sm text-foreground">Auto-Generated Purchase Order</h4>
                                                      <Badge variant="neutral">{linkedPo.status}</Badge>
                                                    </div>
                                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                                                      <div>
                                                        <p className="text-muted-foreground mb-1">PO Number</p>
                                                        <p className="font-mono font-bold text-primary">{linkedPo.po_number}</p>
                                                      </div>
                                                      <div>
                                                        <p className="text-muted-foreground mb-1">Grand Total</p>
                                                        <p className="font-bold">${linkedPo.grand_total?.toLocaleString()}</p>
                                                      </div>
                                                      <div>
                                                        <p className="text-muted-foreground mb-1">Delivery Date</p>
                                                        <p className="font-medium">{new Date(linkedPo.delivery_date || linkedPo.created_at).toLocaleDateString()}</p>
                                                      </div>
                                                      <div>
                                                        <p className="text-muted-foreground mb-1">Generated On</p>
                                                        <p className="font-medium">{new Date(linkedPo.created_at).toLocaleDateString()}</p>
                                                      </div>
                                                    </div>
                                                    <div className="mt-3 flex justify-end">
                                                      <Button variant="outline" size="sm" onClick={() => window.location.href='/purchase-orders'}>
                                                        View Full PO
                                                      </Button>
                                                    </div>
                                                  </td>
                                                </tr>
                                              );
                                            })()
                                          )}
                                        </React.Fragment>
                                      );
                                    })}
                                  </tbody>
                                </table>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
export default Quotations;
