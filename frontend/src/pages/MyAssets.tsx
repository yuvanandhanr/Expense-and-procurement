import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import {Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, EmptyState} from "../components/ui";

export const MyAssets: React.FC = () => {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const response = await api.get("/assets/my-assets");
        setAssets(response.data);
      } catch (err) {
        console.error("Failed to load your assets:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAssets();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">My Assets</h1>
        <p className="text-xs text-muted-foreground mt-1">View the assets and equipment assigned to you.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : assets.length === 0 ? (
            <EmptyState title="No assets assigned to you yet." description="Data will appear here once available." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                    <th className="p-4">Asset ID</th>
                    <th className="p-4">Serial / Unique ID</th>
                    <th className="p-4">Product Name</th>
                    <th className="p-4">Category</th>
                    <th className="p-4">Vendor</th>
                    <th className="p-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {assets.map((a: any) => (
                    <tr key={a.asset_id} className="hover:bg-accent/20">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{a.asset_code}</td>
                      <td className="p-4 font-mono text-xs">{a.serial_number || "N/A"}</td>
                      <td className="p-4 font-semibold">{a.asset_name}</td>
                      <td className="p-4 text-xs text-muted-foreground">{a.category}</td>
                      <td className="p-4 text-xs">{a.vendor_name}</td>
                      <td className="p-4">
                        <Badge variant={a.status === "Assigned" ? "success" : "neutral"}>
                          {a.status}
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
export default MyAssets;
