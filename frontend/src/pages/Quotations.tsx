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
  const [expandedQuoteId, setExpandedQuoteId] = useState<number | null>(null);

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
    } catch (err) {
      console.error(err);
      toast.error("Failed to approve quotation.");
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
                    <th className="p-4">Quotation ID</th>
                    <th className="p-4">RFQ ID</th>
                    <th className="p-4">Total Price</th>
                    <th className="p-4">Timeline (Days)</th>
                    <th className="p-4">Matching Status</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {quotes.map((q) => (
                    <React.Fragment key={q.quotation_id}>
                      <tr className="hover:bg-accent/20">
                        <td className="p-4 font-bold text-xs tracking-wider text-primary">
                          <button
                            type="button"
                            className="mr-2 text-muted-foreground hover:text-foreground font-mono"
                            onClick={() => setExpandedQuoteId(expandedQuoteId === q.quotation_id ? null : q.quotation_id)}
                          >
                            {expandedQuoteId === q.quotation_id ? "▼" : "▶"}
                          </button>
                          #QT-{q.quotation_id}
                        </td>
                        <td className="p-4">#RFQ-{q.rfq_id}</td>
                        <td className="p-4 font-bold">${q.total_amount?.toLocaleString()}</td>
                        <td className="p-4">{q.lead_time_days} days</td>
                        <td className="p-4">
                          <Badge variant={q.is_selected || q.status === "Selected" ? "success" : "neutral"}>
                            {q.is_selected || q.status === "Selected" ? "Selected" : "Under Review"}
                          </Badge>
                        </td>
                        <td className="p-4 text-right">
                          {isFinanceManager && (!q.is_selected && q.status !== "Selected") && (
                            <Button size="sm" onClick={() => handleApprove(q)}>Approve & Gen PO</Button>
                          )}
                        </td>
                      </tr>
                      {expandedQuoteId === q.quotation_id && q.items && q.items.length > 0 && (
                        <tr className="bg-accent/5">
                          <td colSpan={6} className="p-4">
                            <div className="bg-background rounded-lg border border-border overflow-hidden">
                              <table className="w-full text-left text-xs border-collapse">
                                <thead>
                                  <tr className="bg-accent/30 text-muted-foreground uppercase border-b border-border">
                                    <th className="p-2 pl-4">Item Ref</th>
                                    <th className="p-2">Unit Price</th>
                                    <th className="p-2">Tax</th>
                                    <th className="p-2 font-bold text-primary">Total Price</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                  {q.items.map((item) => (
                                    <tr key={item.quotation_item_id} className="hover:bg-accent/10">
                                      <td className="p-2 pl-4 font-mono text-muted-foreground">#Item-{item.rfq_item_id}</td>
                                      <td className="p-2">${Number(item.unit_price).toFixed(2)}</td>
                                      <td className="p-2">${Number(item.tax_amount || 0).toFixed(2)}</td>
                                      <td className="p-2 font-bold text-primary">${Number(item.total_price || 0).toFixed(2)}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                            
                            {/* Embed Auto-Generated Purchase Order Details if this quote is selected */}
                            {(q.is_selected || q.status === "Selected") && (
                              (() => {
                                const linkedPo = purchaseOrders.find(
                                  po => po.rfq_id === q.rfq_id && po.vendor_id === q.vendor_id
                                );
                                if (!linkedPo) return null;
                                return (
                                  <div className="mt-4 p-4 bg-primary/5 border-l-4 border-primary rounded-r-lg">
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
                                  </div>
                                );
                              })()
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
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
