import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { Vendor } from "../types";
import {Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, EmptyState} from "../components/ui";

export const Vendors: React.FC = () => {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVendors = async () => {
      try {
        const response = await api.get("/vendors");
        setVendors(response.data);
      } catch (err) {
        console.error("Failed to load vendors:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchVendors();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Vendor Management</h1>
        <p className="text-xs text-muted-foreground mt-1">Review onboarding partners, scoring metrics, and tax compliance certificates.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : vendors.length === 0 ? (
            <EmptyState title="No vendors registered." description="Data will appear here once available." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                    <th className="p-4">Vendor Code</th>
                    <th className="p-4">Company Name</th>
                    <th className="p-4">Email</th>
                    <th className="p-4">Compliance Status</th>
                    <th className="p-4">Rating Index</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {vendors.map((v: any) => (
                    <tr key={v.vendor_id} className="hover:bg-accent/20">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{v.vendor_code}</td>
                      <td className="p-4 font-semibold">{v.vendor_name}</td>
                      <td className="p-4">{v.email || "N/A"}</td>
                      <td className="p-4">
                        <Badge variant={v.status === "Active" ? "success" : "error"}>
                          {v.status === "Active" ? "Compliant" : "Non-Compliant"}
                        </Badge>
                      </td>
                      <td className="p-4 font-bold">{v.performance?.quality_score || "90"} / 100</td>
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
export default Vendors;
