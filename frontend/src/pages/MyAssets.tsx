import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import {Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, EmptyState, Dialog, Button} from "../components/ui";
import toast from "react-hot-toast";
import { isValidText } from "../utils/helpers";
import { Eye } from "lucide-react";

export const MyAssets: React.FC = () => {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"Assets" | "Incidents">("Assets");

  const [incidents, setIncidents] = useState<any[]>([]);
  const [isIncidentModalOpen, setIsIncidentModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<any>(null);
  const [selectedIncident, setSelectedIncident] = useState<any>(null);
  const [incidentDescription, setIncidentDescription] = useState("");
  const [incidentType, setIncidentType] = useState("Damage");
  const [imageUrl, setImageUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchAssets();
    fetchIncidents();
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

  const fetchIncidents = async () => {
    try {
      const response = await api.get("/asset-incidents");
      setIncidents(response.data);
    } catch (err) {
      console.error("Failed to load your incidents:", err);
    }
  };

  const openIncidentModal = (asset: any) => {
    setSelectedAsset(asset);
    setIncidentDescription("");
    setIncidentType("Damage");
    setImageUrl("");
    setIsIncidentModalOpen(true);
  };

  const openEditModal = (incident: any) => {
    setSelectedIncident(incident);
    setIncidentDescription(incident.description);
    setIncidentType(incident.incident_type);
    setImageUrl(incident.image_url || "");
    setIsEditModalOpen(true);
  };

  const openViewModal = (incident: any) => {
    setSelectedIncident(incident);
    setIsViewModalOpen(true);
  };

  const submitIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAsset || !incidentDescription) return;

    if (!isValidText(incidentDescription)) {
      toast.error("Please enter a valid description (letters or numbers required).");
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post("/asset-incidents", {
        asset_id: selectedAsset.asset_id,
        description: incidentDescription,
        incident_type: incidentType,
        image_url: imageUrl || null
      });
      toast.success("Incident reported successfully");
      setIsIncidentModalOpen(false);
      fetchAssets();
      fetchIncidents();
    } catch (err) {
      toast.error("Failed to report incident");
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitEditIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIncident || !incidentDescription) return;

    if (!isValidText(incidentDescription)) {
      toast.error("Please enter a valid description (letters or numbers required).");
      return;
    }

    setIsSubmitting(true);
    try {
      await api.put(`/asset-incidents/${selectedIncident.incident_id}`, {
        description: incidentDescription,
        incident_type: incidentType,
        image_url: imageUrl || null
      });
      toast.success("Incident updated and resubmitted successfully");
      setIsEditModalOpen(false);
      fetchAssets();
      fetchIncidents();
    } catch (err) {
      toast.error("Failed to update incident");
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

      <div className="flex items-center justify-between mb-4 mt-6">
        <div className="flex items-center space-x-2 bg-muted/40 p-1.5 rounded-xl w-fit border border-border/50">
          <button
            onClick={() => setActiveTab("Assets")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center space-x-1.5 ${
              activeTab === "Assets"
                ? "bg-primary text-primary-foreground shadow-sm font-bold"
                : "text-muted-foreground hover:text-foreground hover:bg-background/50"
            }`}
          >
            <span>My Assets</span>
            <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
              activeTab === "Assets" ? "bg-primary-foreground/20 text-primary-foreground font-bold" : "bg-muted text-muted-foreground"
            }`}>
              {assets.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab("Incidents")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center space-x-1.5 ${
              activeTab === "Incidents"
                ? "bg-primary text-primary-foreground shadow-sm font-bold"
                : "text-muted-foreground hover:text-foreground hover:bg-background/50"
            }`}
          >
            <span>My Asset Incidents</span>
            <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
              activeTab === "Incidents" ? "bg-primary-foreground/20 text-primary-foreground font-bold" : "bg-muted text-muted-foreground"
            }`}>
              {incidents.length}
            </span>
          </button>
        </div>
      </div>

      <div className="mt-4">
        {activeTab === "Assets" && (
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
                          <td className="p-4">
                            <Badge variant={a.status === "Assigned" ? "success" : "neutral"}>
                              {a.status}
                            </Badge>
                          </td>
                          <td className="p-4 text-right">
                            {["Damaged", "Reported", "Under Maintenance"].includes(a.status) ? (
                              <Button variant="outline" size="sm" disabled>
                                Reported
                              </Button>
                            ) : (
                              <Button variant="outline" size="sm" onClick={() => openIncidentModal(a)}>
                                Report Issue
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {activeTab === "Incidents" && (
        <Card>
          <CardContent className="p-0">
            {incidents.length === 0 ? (
              <EmptyState title="No incidents reported." description="You haven't reported any asset issues." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                      <th className="p-4">Incident ID</th>
                      <th className="p-4">Type</th>
                      <th className="p-4">Status</th>
                      <th className="p-4">Reported On</th>
                      <th className="p-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {incidents.map((inc: any) => (
                      <tr key={inc.incident_id} className="hover:bg-accent/20">
                        <td className="p-4 font-bold text-xs tracking-wider text-primary">#{inc.incident_id}</td>
                        <td className="p-4 text-xs font-semibold">{inc.incident_type}</td>
                        <td className="p-4">
                          <Badge variant={["Reported", "Pending Fulfillment", "Waiting for Procurement"].includes(inc.status) ? "info" : inc.status === "Returned for Correction" ? "warning" : inc.status === "Closed" ? "neutral" : "success"}>
                            {inc.status}
                          </Badge>
                        </td>
                        <td className="p-4 text-xs">{new Date(inc.created_at).toLocaleDateString()}</td>
                        <td className="p-4 text-right flex justify-end gap-2">
                          <Button variant="ghost" size="sm" onClick={() => openViewModal(inc)} title="View Details">
                            <Eye className="w-4 h-4" />
                          </Button>
                          {inc.status === "Returned for Correction" && (
                            <Button variant="outline" size="sm" onClick={() => openEditModal(inc)}>
                              Edit & Resubmit
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
        )}
      </div>

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

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Image URL (Optional)</label>
            <input 
              type="text"
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
              placeholder="https://example.com/image.png"
              value={imageUrl}
              onChange={e => setImageUrl(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">Provide a link to an image showing the issue.</p>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setIsIncidentModalOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting || !incidentDescription}>Submit Report</Button>
          </div>
        </form>
      </Dialog>

      <Dialog isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} title="Edit Asset Issue">
        <form onSubmit={submitEditIncident} className="space-y-4">
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
              value={incidentDescription}
              onChange={e => setIncidentDescription(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Image URL (Optional)</label>
            <input 
              type="text"
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
              placeholder="https://example.com/image.png"
              value={imageUrl}
              onChange={e => setImageUrl(e.target.value)}
            />
          </div>

            <div className="flex justify-end space-x-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsEditModalOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={isSubmitting || !incidentDescription}>Resubmit Report</Button>
            </div>
          </form>
        </Dialog>

        <Dialog isOpen={isViewModalOpen} onClose={() => setIsViewModalOpen(false)} title={`Asset Incident #${selectedIncident?.incident_id}`}>
          {selectedIncident && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4 pb-4 border-b border-border">
                 <div>
                   <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Type</p>
                   <p className="text-sm font-semibold">{selectedIncident.incident_type}</p>
                 </div>
                 <div>
                   <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Status</p>
                   <Badge variant={["Reported", "Pending Fulfillment", "Waiting for Procurement"].includes(selectedIncident.status) ? "info" : selectedIncident.status === "Returned for Correction" ? "warning" : selectedIncident.status === "Closed" ? "neutral" : "success"}>
                     {selectedIncident.status}
                   </Badge>
                 </div>
                 <div>
                   <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Reported On</p>
                   <p className="text-sm">{new Date(selectedIncident.created_at).toLocaleDateString()}</p>
                 </div>
                 {selectedIncident.updated_at && selectedIncident.status !== "Reported" && (
                   <div>
                     <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Last Updated</p>
                     <p className="text-sm">{new Date(selectedIncident.updated_at).toLocaleDateString()}</p>
                   </div>
                 )}
              </div>
              
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Description</p>
                <div className="bg-muted/40 p-3 rounded-lg border border-border text-sm min-h-[80px]">
                  {selectedIncident.description}
                </div>
              </div>

              {selectedIncident.image_url && (
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Image URL</p>
                  <a href={selectedIncident.image_url} target="_blank" rel="noreferrer" className="text-sm text-primary underline break-all">
                    {selectedIncident.image_url}
                  </a>
                </div>
              )}
              
              {selectedIncident.resolution && (
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Approver/Admin Notes (Resolution)</p>
                  <div className="bg-muted/40 p-3 rounded-lg border border-border text-sm min-h-[60px]">
                    {selectedIncident.resolution}
                  </div>
                </div>
              )}

              <div className="flex justify-end pt-2">
                <Button onClick={() => setIsViewModalOpen(false)}>Close</Button>
              </div>
            </div>
          )}
        </Dialog>
      </div>
  );
};
export default MyAssets;
