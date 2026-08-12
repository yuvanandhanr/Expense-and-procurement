import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import { Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, Button } from "../components/ui";
import toast from "react-hot-toast";
import { Quotation } from "../types";

export const Quotations: React.FC = () => {
  const { user } = useAuth();
  const [quotes, setQuotes] = useState<Quotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedQuoteId, setExpandedQuoteId] = useState<number | null>(null);

  useEffect(() => {
    const fetchQuotes = async () => {
      try {
        const response = await api.get("/quotations");
        setQuotes(response.data);
      } catch (err) {
        console.error("Failed to load quotations:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchQuotes();
  }, []);

  const handleApprove = async (quote: any) => {
    try {
      await api.post(`/rfq/${quote.rfq_id}/select-vendor`, {
        selected_vendor_id: quote.vendor_id,
        selected_quotation_id: quote.quotation_id,
        reason: "Approved by Finance"
      });
      toast.success("Quotation approved and Purchase Order auto-generated!");
      // Refetch
      const response = await api.get("/quotations");
      setQuotes(response.data);
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
            <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              No bids or quotations recorded yet.
            </div>
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
