import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { Invoice } from "../types";
import { Card, CardHeader, CardTitle, CardContent, Badge, Skeleton } from "../components/ui";

export const Invoices: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInvoices = async () => {
      try {
        const response = await api.get("/invoices");
        setInvoices(response.data);
      } catch (err) {
        console.error("Failed to load invoices:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchInvoices();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Accounts Payable Invoices</h1>
        <p className="text-xs text-muted-foreground mt-1">Review incoming vendor billings, matching status logs, and due dates.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : invoices.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              No invoices uploaded.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                    <th className="p-4">Invoice Number</th>
                    <th className="p-4">PO Reference</th>
                    <th className="p-4">Amount</th>
                    <th className="p-4">Due Date</th>
                    <th className="p-4">3-Way Match</th>
                    <th className="p-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {invoices.map((inv) => (
                    <tr key={inv.invoice_id} className="hover:bg-accent/20">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{inv.invoice_number}</td>
                      <td className="p-4">#PO-{inv.po_id}</td>
                      <td className="p-4 font-bold">${inv.amount?.toLocaleString()}</td>
                      <td className="p-4 text-xs text-muted-foreground">{new Date(inv.due_date).toLocaleDateString()}</td>
                      <td className="p-4">
                        <Badge variant={inv.matching_status === "Matched" ? "success" : "warning"}>
                          {inv.matching_status}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <Badge variant={inv.status === "Paid" ? "success" : "neutral"}>
                          {inv.status}
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
export default Invoices;
