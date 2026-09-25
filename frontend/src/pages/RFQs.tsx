import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { RFQ } from "../types";
import { Card, CardHeader, CardTitle, CardContent, Badge, StatusBadge, Skeleton, Button, EmptyState } from "../components/ui";
import { formatDate } from "../utils/helpers";

export const RFQs: React.FC = () => {
  const [rfqs, setRfqs] = useState<RFQ[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRFQs = async () => {
      try {
        const response = await api.get("/rfq");
        setRfqs(response.data);
      } catch (err) {
        console.error("Failed to load RFQs:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchRFQs();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Request for Quotation (RFQs)</h1>
        <p className="text-xs text-muted-foreground mt-1">Initiate and view vendor bidding cycles.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : rfqs.length === 0 ? (
            <EmptyState title="No active RFQ sessions found." description="Data will appear here once available." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                    <th className="p-4 whitespace-nowrap">RFQ Number</th>
                    <th className="p-4">Title</th>
                    <th className="p-4 whitespace-nowrap">Submission Deadline</th>
                    <th className="p-4 whitespace-nowrap">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {rfqs.map((r) => (
                    <tr key={r.rfq_id} className="hover:bg-accent/20">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary whitespace-nowrap">{r.rfq_number}</td>
                      <td className="p-4 font-semibold">{r.title}</td>
                      <td className="p-4 text-xs text-muted-foreground whitespace-nowrap">{formatDate(r.submission_deadline)}</td>
                      <td className="p-4 whitespace-nowrap">
                        <StatusBadge status={r.status} />
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
export default RFQs;
