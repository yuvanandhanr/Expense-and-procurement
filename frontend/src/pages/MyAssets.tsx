import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import {Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, EmptyState, Dialog, Button} from "../components/ui";
import toast from "react-hot-toast";

export const MyAssets: React.FC = () => {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [isIncidentModalOpen, setIsIncidentModalOpen] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<any>(null);
  const [incidentDescription, setIncidentDescription] = useState("");
  const [incidentType, setIncidentType] = useState("Damage");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchAssets();
  }, []);

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

  const openIncidentModal = (asset: any) => {
    setSelectedAsset(asset);
    setIncidentDescription("");
    setIncidentType("Damage");
    setIsIncidentModalOpen(true);
  };

  const submitIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAsset || !incidentDescription) return;

    setIsSubmitting(true);
    try {
      await api.post("/asset-incidents", {
        asset_id: selectedAsset.asset_id,
        description: incidentDescription,
        incident_type: incidentType
      });
      toast.success("Incident reported successfully");
      setIsIncidentModalOpen(false);
      fetchAssets();
    } catch (err) {
      toast.error("Failed to report incident");
    } finally {
      setIsSubmitting(false);
    }
  };

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
                    <th className="p-4 text-right">Actions</th>
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
                      <td className="p-4 text-right">
                        <Button variant="outline" size="sm" onClick={() => openIncidentModal(a)}>
                          Report Issue
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog isOpen={isIncidentModalOpen} onClose={() => setIsIncidentModalOpen(false)} title="Report Asset Issue">
        <form onSubmit={submitIncident} className="space-y-4">
          <div className="p-3 bg-accent/30 rounded-md border text-sm">
            Reporting issue for: <span className="font-bold">{selectedAsset?.asset_name}</span> ({selectedAsset?.asset_code})
          </div>
          
          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Issue Type</label>
            <select 
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
              value={incidentType}
              onChange={e => setIncidentType(e.target.value)}
            >
              <option value="Damage">Hardware Damage</option>
              <option value="Loss">Lost or Stolen</option>
              <option value="Malfunction">Software / System Malfunction</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Description</label>
            <textarea 
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm min-h-[100px]"
              placeholder="Please describe exactly what happened..."
              value={incidentDescription}
              onChange={e => setIncidentDescription(e.target.value)}
              required
            />
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setIsIncidentModalOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting || !incidentDescription}>Submit Report</Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
};
export default MyAssets;
