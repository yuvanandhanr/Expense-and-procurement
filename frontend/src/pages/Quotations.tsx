import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { Quotation } from "../types";
import { Card, CardHeader, CardTitle, CardContent, Badge, Skeleton } from "../components/ui";

export const Quotations: React.FC = () => {
  const [quotes, setQuotes] = useState<Quotation[]>([]);
  const [loading, setLoading] = useState(true);

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
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {quotes.map((q) => (
                    <tr key={q.quotation_id} className="hover:bg-accent/20">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">#QT-{q.quotation_id}</td>
                      <td className="p-4">#RFQ-{q.rfq_id}</td>
                      <td className="p-4 font-bold">${q.total_price?.toLocaleString()}</td>
                      <td className="p-4">{q.delivery_timeline_days} days</td>
                      <td className="p-4">
                        <Badge variant={q.is_selected ? "success" : "neutral"}>
                          {q.is_selected ? "Selected" : "Under Review"}
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
  );
};
export default Quotations;
