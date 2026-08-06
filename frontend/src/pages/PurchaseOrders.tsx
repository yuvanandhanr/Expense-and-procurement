import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { PurchaseOrder } from "../types";
import { Card, CardHeader, CardTitle, CardContent, Badge, Skeleton } from "../components/ui";
import { formatDate } from "../utils/helpers";

export const PurchaseOrders: React.FC = () => {
  const [pos, setPos] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPOs = async () => {
      try {
        const response = await api.get("/purchase_orders");
        setPos(response.data);
      } catch (err) {
        console.error("Failed to load POs:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchPOs();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Purchase Orders (POs)</h1>
        <p className="text-xs text-muted-foreground mt-1">Track binding contracts sent to suppliers.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : pos.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              No Purchase Orders active.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                    <th className="p-4">PO Number</th>
                    <th className="p-4">PR Reference</th>
                    <th className="p-4">Total Amount</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Date Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {pos.map((p) => (
                    <tr key={p.po_id} className="hover:bg-accent/20">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{p.po_number}</td>
                      <td className="p-4">#PR-{p.pr_id}</td>
                      <td className="p-4 font-bold">${p.total_amount?.toLocaleString()}</td>
                      <td className="p-4">
                        <Badge variant={p.status === "Approved" ? "success" : "neutral"}>
                          {p.status}
                        </Badge>
                      </td>
                      <td className="p-4 text-xs text-muted-foreground">{formatDate(p.created_at)}</td>
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
export default PurchaseOrders;
