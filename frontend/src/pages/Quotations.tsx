import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { Quotation, RFQ } from "../types";
import { useAuth } from "../hooks/useAuth";
import { Card, CardHeader, CardTitle, CardContent, Badge, StatusBadge, Skeleton, Button, EmptyState } from "../components/ui";
import { Check, Eye } from "lucide-react";
import toast from "react-hot-toast";

export const Quotations: React.FC = () => {
  const { user } = useAuth();
  const [rfqs, setRfqs] = useState<RFQ[]>([]);
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedRfq, setExpandedRfq] = useState<number | null>(null);

  const isFinanceManager = user?.roles?.some(r => r.role_name === "Finance Manager" || r.role_name === "CFO" || r.role_name === "Admin");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [rfqRes, quoteRes, poRes] = await Promise.all([
        api.get("/rfq"),
        api.get("/quotations"),
        api.get("/purchase-orders").catch(() => ({ data: [] }))
      ]);
      setRfqs(rfqRes.data);
      setQuotations(quoteRes.data);
      setPurchaseOrders(poRes.data);
      if (Array.isArray(rfqRes?.data) && rfqRes.data.length > 0 && expandedRfq === null) {
        setExpandedRfq(rfqRes.data[0]?.rfq_id || null);
      }
    } catch (err) {
      console.error("Failed to load quotations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApprove = async (quote: Quotation) => {
    try {
      await api.post(`/quotations/${quote.quotation_id}/approve`);
      toast.success("Quotation selected! Purchase Order auto-generated.");
      fetchData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to select quotation.");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Quotations Inbox</h1>
        <p className="text-xs text-muted-foreground mt-1">Review vendor bids for open RFQs, evaluate delivery timelines, and award purchase orders.</p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {loading ? (
          <Skeleton className="h-64 w-full" />
        ) : rfqs.length === 0 ? (
          <EmptyState title="No RFQs available." description="Create RFQs to receive vendor quotation proposals." />
        ) : (
          rfqs.map((rfq) => {
            const rfqQuotes = quotations.filter(q => q.rfq_id === rfq.rfq_id);
            const isExpanded = expandedRfq === rfq.rfq_id;
            const hasSelected = rfqQuotes.some(q => q.status === "Selected" || q.is_selected);

            return (
              <Card key={rfq.rfq_id} className="overflow-hidden border border-border">
                <div 
                  className="p-4 bg-muted/20 hover:bg-muted/30 cursor-pointer flex items-center justify-between transition-colors"
                  onClick={() => setExpandedRfq(isExpanded ? null : rfq.rfq_id)}
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-muted-foreground font-mono">{isExpanded ? "▼" : "▶"}</span>
                    <div>
                      <h3 className="font-bold text-base text-foreground">{rfq.title}</h3>
                      <p className="text-xs text-muted-foreground font-mono">RFQ #{rfq.rfq_number}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="text-xs text-muted-foreground">{rfqQuotes.length} Proposals Submitted</span>
                    <StatusBadge status={hasSelected ? "Awarded" : rfq.status} />
                  </div>
                </div>

                {isExpanded && (
                  <div className="p-0 border-t border-border">
                    {rfqQuotes.length === 0 ? (
                      <div className="p-6 text-center text-xs text-muted-foreground">
                        No vendor quotations submitted for this RFQ yet.
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead>
                            <tr className="border-b border-border bg-muted/40 font-semibold text-muted-foreground uppercase">
                              <th className="p-3 pl-4 whitespace-nowrap">Vendor</th>
                              <th className="p-3 whitespace-nowrap">Quotation Ref</th>
                              <th className="p-3 whitespace-nowrap">Total Price</th>
                              <th className="p-3 whitespace-nowrap">Timeline</th>
                              <th className="p-3 whitespace-nowrap">Status</th>
                              <th className="p-3 text-right whitespace-nowrap">Action</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border">
                            {rfqQuotes.map((q) => {
                              let statusDisplay = q.status;
                              if (q.status === "Selected" || q.is_selected) {
                                statusDisplay = "Selected";
                              } else if (q.status === "Rejected" || hasSelected) {
                                statusDisplay = "Rejected";
                              }

                              return (
                                <tr key={q.quotation_id} className="hover:bg-accent/10">
                                  <td className="p-3 pl-4 font-medium whitespace-nowrap">{(q as any).vendor?.vendor_name || `Vendor #${q.vendor_id}`}</td>
                                  <td className="p-3 font-mono text-muted-foreground whitespace-nowrap">#QT-{q.quotation_id}</td>
                                  <td className="p-3 font-bold text-primary whitespace-nowrap">${Number(q.total_amount).toLocaleString()}</td>
                                  <td className="p-3 whitespace-nowrap">{q.lead_time_days} days</td>
                                  <td className="p-3 whitespace-nowrap">
                                    <StatusBadge status={statusDisplay} />
                                  </td>
                                  <td className="p-3 text-right whitespace-nowrap">
                                    {isFinanceManager && !hasSelected && (
                                      <Button size="sm" variant="success" onClick={() => handleApprove(q)} className="gap-1 font-bold shadow-apple-sm">
                                        <Check className="w-3.5 h-3.5" /> Select Quote
                                      </Button>
                                    )}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
};
export default Quotations;
