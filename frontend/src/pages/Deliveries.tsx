import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { Delivery } from "../types";
import { Card, CardHeader, CardTitle, CardContent, Badge, Skeleton } from "../components/ui";
import { formatDate } from "../utils/helpers";

export const Deliveries: React.FC = () => {
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDeliveries = async () => {
      try {
        const response = await api.get("/deliveries");
        setDeliveries(response.data);
      } catch (err) {
        console.error("Failed to load deliveries:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDeliveries();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Product Shipments & Deliveries</h1>
        <p className="text-xs text-muted-foreground mt-1">Track incoming goods shipment dates and recipient employees.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : deliveries.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              No delivery shipments tracked yet.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                    <th className="p-4">Delivery Number</th>
                    <th className="p-4">PO Reference</th>
                    <th className="p-4">Delivered Date</th>
                    <th className="p-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {deliveries.map((d) => (
                    <tr key={d.delivery_id} className="hover:bg-accent/20">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{d.delivery_number}</td>
                      <td className="p-4">#PO-{d.po_id}</td>
                      <td className="p-4 text-xs text-muted-foreground">{formatDate(d.delivered_date)}</td>
                      <td className="p-4">
                        <Badge variant={d.status === "Delivered" ? "success" : "neutral"}>
                          {d.status}
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
export default Deliveries;
