import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { Contract } from "../types";
import { Card, CardHeader, CardTitle, CardContent, Badge, Skeleton } from "../components/ui";
import { formatDate } from "../utils/helpers";

export const Contracts: React.FC = () => {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const response = await api.get("/contracts");
        setContracts(response.data);
      } catch (err) {
        console.error("Failed to load contracts:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchContracts();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Supplier Contracts</h1>
        <p className="text-xs text-muted-foreground mt-1">Review legal structures, pricing agreements, and expiration dates.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : contracts.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              No active vendor contracts found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                    <th className="p-4">Contract Number</th>
                    <th className="p-4">Title</th>
                    <th className="p-4">Start Date</th>
                    <th className="p-4">End Date</th>
                    <th className="p-4">Total Value</th>
                    <th className="p-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {contracts.map((c) => (
                    <tr key={c.contract_id} className="hover:bg-accent/20">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{c.contract_number}</td>
                      <td className="p-4 font-semibold">{c.title}</td>
                      <td className="p-4 text-xs text-muted-foreground">{formatDate(c.start_date)}</td>
                      <td className="p-4 text-xs text-muted-foreground">{formatDate(c.end_date)}</td>
                      <td className="p-4 font-bold">${c.total_value?.toLocaleString()}</td>
                      <td className="p-4">
                        <Badge variant={c.status === "Active" ? "success" : "neutral"}>
                          {c.status}
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
export default Contracts;
