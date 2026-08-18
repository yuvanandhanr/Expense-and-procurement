import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { GRN } from "../types";
import {Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, EmptyState} from "../components/ui";
import { formatDate } from "../utils/helpers";

export const GRNs: React.FC = () => {
  const [grns, setGrns] = useState<GRN[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchGRNs = async () => {
      try {
        const response = await api.get("/grns");
        setGrns(response.data);
      } catch (err) {
        console.error("Failed to load GRNs:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchGRNs();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Goods Receipt Notes (GRN)</h1>
        <p className="text-xs text-muted-foreground mt-1">Audit accepted/rejected quantities during warehouse physical inspections.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : grns.length === 0 ? (
            <EmptyState title="No Goods Receipt Notes registered yet." description="Data will appear here once available." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                    <th className="p-4">GRN Number</th>
                    <th className="p-4">PO Reference</th>
                    <th className="p-4">Received Date</th>
                    <th className="p-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {grns.map((g) => (
                    <tr key={g.grn_id} className="hover:bg-accent/20">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{g.grn_number}</td>
                      <td className="p-4">#PO-{g.po_id}</td>
                      <td className="p-4 text-xs text-muted-foreground">{formatDate(g.received_date)}</td>
                      <td className="p-4">
                        <Badge variant={g.status === "Approved" ? "success" : "neutral"}>
                          {g.status}
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
export default GRNs;
