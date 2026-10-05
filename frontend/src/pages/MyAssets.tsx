import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { Card, CardContent, Badge, Skeleton, EmptyState, Dialog, Button, Input } from "../components/ui";
import toast from "react-hot-toast";
import { isValidText } from "../utils/helpers";
import { Eye, Edit3, AlertCircle } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

export const MyAssets: React.FC = () => {
  const { user } = useAuth();
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"Assets" | "Incidents">("Assets");
  const [statusFilter, setStatusFilter] = useState("All");

  const [incidents, setIncidents] = useState<any[]>([]);
  const [isIncidentModalOpen, setIsIncidentModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  
  const [selectedAsset, setSelectedAsset] = useState<any>(null);
  const [selectedIncident, setSelectedIncident] = useState<any>(null);
  
  // Incident Form state
  const [incidentType, setIncidentType] = useState("Damaged");
  const [incidentDescription, setIncidentDescription] = useState("");
  const [incidentReason, setIncidentReason] = useState("");
  const [incidentComments, setIncidentComments] = useState("");
  const [incidentDate, setIncidentDate] = useState(new Date().toISOString().split("T")[0]);
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
    setIncidentType("Damaged");
    setIncidentDescription("");
    setIncidentReason("");
    setIncidentComments("");
    setIncidentDate(new Date().toISOString().split("T")[0]);
    setImageUrl("");
    setIsIncidentModalOpen(true);
  };

  const openEditModal = (incident: any) => {
    setSelectedIncident(incident);
    setIncidentType(incident.incident_type || "Damaged");
    setIncidentDescription(incident.description || "");
    setIncidentReason("");
    setIncidentComments("");
    setIncidentDate(incident.incident_date || new Date().toISOString().split("T")[0]);
    setImageUrl(incident.image_url || "");
    setIsEditModalOpen(true);
  };

  const openViewModal = (incident: any) => {
    setSelectedIncident(incident);
    setIsViewModalOpen(true);
  };

  const submitIncident = async (e: React.FormEvent, isDraft = false) => {
    e.preventDefault();
    if (!selectedAsset || !incidentDescription.trim()) {
      toast.error("Please provide a description of the issue.");
      return;
    }

    if (!isValidText(incidentDescription)) {
      toast.error("Please enter a valid description (letters or numbers required).");
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post("/asset-incidents", {
        asset_id: selectedAsset.asset_id,
        description: incidentDescription.trim(),
        incident_type: incidentType,
        reason: incidentReason.trim() || null,
        comments: incidentComments.trim() || null,
        incident_date: incidentDate || null,
        image_url: imageUrl.trim() || null,
        is_draft: isDraft,
        department_name: user?.department_name || null,
        employee_type: user?.employee_type || null
      });
      toast.success(isDraft ? "Incident draft saved successfully" : "Asset incident report submitted successfully");
      setIsIncidentModalOpen(false);
      fetchAssets();
      fetchIncidents();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to submit incident report");
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitEditIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIncident || !incidentDescription.trim()) {
      toast.error("Please provide a description of the issue.");
      return;
    }

    if (!isValidText(incidentDescription)) {
      toast.error("Please enter a valid description (letters or numbers required).");
      return;
    }

    setIsSubmitting(true);
    try {
      await api.put(`/asset-incidents/${selectedIncident.incident_id}`, {
        description: incidentDescription.trim(),
        incident_type: incidentType,
        reason: incidentReason.trim() || null,
        comments: incidentComments.trim() || null,
        incident_date: incidentDate || null,
        image_url: imageUrl.trim() || null
      });
      toast.success("Incident corrected and resubmitted successfully");
      setIsEditModalOpen(false);
      fetchAssets();
      fetchIncidents();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to resubmit incident");
    } finally {
      setIsSubmitting(false);
    }
  };

  const isSubmittedStatus = (status: string) => {
    const s = (status || "").toLowerCase();
    return s === "submitted" || s.includes("pending") || s.includes("reported") || s.includes("manager approved") || s.includes("admin approved") || s.includes("procurement") || s.includes("repair");
  };

  const isApprovedStatus = (status: string) => {
    const s = (status || "").toLowerCase();
    return s === "resolved / completed" || s === "completed" || s === "closed" || s === "resolved";
  };

  const subTabCounts: Record<string, number> = {
    All: incidents.length,
    Drafts: incidents.filter((i: any) => i.status === "Draft").length,
    Submitted: incidents.filter((i: any) => isSubmittedStatus(i.status)).length,
    Approved: incidents.filter((i: any) => isApprovedStatus(i.status)).length,
    Rejected: incidents.filter((i: any) => i.status === "Rejected").length,
    "Returned for Correction": incidents.filter((i: any) => i.status === "Returned for Correction").length,
  };

  const filteredIncidents = incidents.filter((i: any) => {
    if (statusFilter === "All") return true;
    if (statusFilter === "Drafts") return i.status === "Draft";
    if (statusFilter === "Submitted") return isSubmittedStatus(i.status);
    if (statusFilter === "Approved") return isApprovedStatus(i.status);
    if (statusFilter === "Rejected") return i.status === "Rejected";
    if (statusFilter === "Returned for Correction") return i.status === "Returned for Correction";
    return i.status === statusFilter;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">My Assets</h1>
        <p className="text-xs text-muted-foreground mt-1">View the assets and equipment assigned to you and report damaged or malfunctioning equipment.</p>
      </div>

      <div className="flex items-center justify-between mb-4 mt-6">
        <div className="flex items-center space-x-2 bg-card p-2 rounded-xl border border-border shadow-sm">
          <span className="text-xs font-semibold text-muted-foreground uppercase px-2">Section:</span>
          <button
            onClick={() => setActiveTab("Assets")}
            className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${activeTab === "Assets"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:bg-accent"
              }`}
          >
            My Assets
          </button>
          <button
            onClick={() => setActiveTab("Incidents")}
            className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${activeTab === "Incidents"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:bg-accent"
              }`}
          >
            My Asset Incidents
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
                  <Skeleton className="h-8 w-full" />
                </div>
              ) : assets.length === 0 ? (
                <EmptyState title="No assets assigned to you yet." description="Assets assigned to you by administrators will appear here." />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm border-collapse">
                    <thead>
                      <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                        <th className="p-4">Asset Tag</th>
                        <th className="p-4">Asset Name</th>
                        <th className="p-4">Category</th>
                        <th className="p-4">Serial Number</th>
                        <th className="p-4">Status</th>
                        <th className="p-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {assets.map((a: any) => (
                        <tr key={a.asset_id} className="hover:bg-accent/20">
                          <td className="p-4 font-bold text-xs tracking-wider text-primary">{a.serial_number || a.asset_code}</td>
                          <td className="p-4 font-semibold">{a.asset_name}</td>
                          <td className="p-4 text-xs text-muted-foreground">{a.category}</td>
                          <td className="p-4 font-mono text-xs text-muted-foreground">{a.serial_number || a.asset_code || "N/A"}</td>
                          <td className="p-4">
                            <Badge variant={a.status === "Assigned" ? "success" : a.status === "Under Maintenance" ? "warning" : "neutral"}>
                              {a.status}
                            </Badge>
                          </td>
                          <td className="p-4 text-right">
                            <Button variant="outline" size="sm" onClick={() => openIncidentModal(a)}>
                              Report
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
        )}

        {activeTab === "Incidents" && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center space-x-2 bg-muted/40 p-1.5 rounded-xl w-fit border border-border/50 gap-y-2">
            {["All", "Drafts", "Submitted", "Approved", "Rejected", "Returned for Correction"].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center space-x-1.5 ${
                  statusFilter === status
                    ? "bg-primary text-primary-foreground shadow-sm font-bold"
                    : "text-muted-foreground hover:text-foreground hover:bg-background/50"
                }`}
              >
                <span>{status}</span>
                <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                  statusFilter === status ? "bg-primary-foreground/20 text-primary-foreground font-bold" : "bg-muted text-muted-foreground"
                }`}>
                  {subTabCounts[status]}
                </span>
              </button>
            ))}
          </div>

          <Card>
            <CardContent className="p-0">
              {filteredIncidents.length === 0 ? (
                <EmptyState title="No asset incidents found." description={`There are no incidents matching "${statusFilter}".`} />
              ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                      <th className="p-4">Incident ID</th>
                      <th className="p-4">Asset Tag</th>
                      <th className="p-4">Asset Name</th>
                      <th className="p-4">Incident Type</th>
                      <th className="p-4">Description</th>
                      <th className="p-4">Submitted Date</th>
                      <th className="p-4">Status</th>
                      <th className="p-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {filteredIncidents.map((inc: any) => {
                      const assetTag = inc.asset?.asset_tag || inc.asset?.asset_number || `AST-${inc.asset_id}`;
                      const assetName = inc.asset?.model || "Asset";
                      return (
                        <tr key={inc.incident_id} className="hover:bg-accent/20">
                          <td className="p-4 font-bold text-xs tracking-wider text-primary">#{inc.incident_id}</td>
                          <td className="p-4 font-mono text-xs">{assetTag}</td>
                          <td className="p-4 font-semibold text-xs">{assetName}</td>
                          <td className="p-4 text-xs font-semibold">{inc.incident_type}</td>
                          <td className="p-4 text-xs max-w-[200px] truncate" title={inc.description}>{inc.description}</td>
                          <td className="p-4 text-xs text-muted-foreground">{new Date(inc.created_at || Date.now()).toLocaleDateString()}</td>
                          <td className="p-4">
                            <Badge variant={inc.status === "Resolved / Completed" ? "success" : inc.status === "Rejected" ? "danger" : inc.status === "Returned for Correction" ? "warning" : "info"}>
                              {inc.status}
                            </Badge>
                          </td>
                          <td className="p-4 text-right flex justify-end gap-2">
                            <Button variant="ghost" size="sm" onClick={() => openViewModal(inc)} title="View Complete Incident">
                              <Eye className="w-4 h-4" />
                            </Button>
                            {(inc.status === "Returned for Correction" || inc.status === "Draft") && (
                              <Button variant="outline" size="sm" onClick={() => openEditModal(inc)} className="gap-1">
                                <Edit3 className="w-3.5 h-3.5" /> {inc.status === "Draft" ? "Edit Draft" : "Edit & Resubmit"}
                              </Button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      )}
    </div>

      {/* Report Asset Incident Modal */}
      <Dialog isOpen={isIncidentModalOpen} onClose={() => setIsIncidentModalOpen(false)} title="Report Damaged / Malfunctioning Asset">
        <form onSubmit={(e) => submitIncident(e, false)} className="space-y-4">
          <div className="p-3 bg-muted/40 rounded-xl border border-border text-sm flex flex-col gap-1">
            <span className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Target Asset</span>
            <span className="font-bold text-foreground">{selectedAsset?.asset_name}</span>
            <span className="text-xs font-mono text-muted-foreground">Tag: {selectedAsset?.serial_number || selectedAsset?.asset_code} | Category: {selectedAsset?.category}</span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Incident Type <span className="text-red-500">*</span></label>
              <select 
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:ring-2 focus:ring-primary focus:outline-none"
                value={incidentType}
                onChange={e => setIncidentType(e.target.value)}
                required
              >
                <option value="Damaged">Damaged</option>
                <option value="Malfunctioning">Malfunctioning</option>
                <option value="Repair Required">Repair Required</option>
                <option value="Replacement Required">Replacement Required</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Date of Incident</label>
              <Input 
                type="date"
                value={incidentDate}
                onChange={e => setIncidentDate(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Description of the Issue / Damage <span className="text-red-500">*</span></label>
            <textarea 
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm min-h-[90px] focus:ring-2 focus:ring-primary focus:outline-none"
              placeholder="Describe what happened, error symptoms, or physical damage observed..."
              value={incidentDescription}
              onChange={e => setIncidentDescription(e.target.value)}
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Reason / Justification</label>
            <Input 
              placeholder="Why this repair or replacement is needed for your duties..."
              value={incidentReason}
              onChange={e => setIncidentReason(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Additional Comments</label>
            <Input 
              placeholder="Any additional notes or urgency details..."
              value={incidentComments}
              onChange={e => setIncidentComments(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Supporting Photo / Attachment URL</label>
            <Input 
              type="text"
              placeholder="https://example.com/asset-photo.jpg"
              value={imageUrl}
              onChange={e => setImageUrl(e.target.value)}
            />
          </div>

          <div className="flex justify-end space-x-2 pt-4 border-t border-border">
            <Button type="button" variant="outline" onClick={() => setIsIncidentModalOpen(false)}>Cancel</Button>
            <Button type="button" disabled={isSubmitting || !incidentDescription.trim()} variant="outline" onClick={(e) => submitIncident(e as any, true)}>Save Draft</Button>
            <Button type="submit" disabled={isSubmitting || !incidentDescription.trim()}>Submit Report</Button>
          </div>
        </form>
      </Dialog>

      {/* Edit & Resubmit Modal */}
      <Dialog isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} title="Correct & Resubmit Incident Report">
        <form onSubmit={submitEditIncident} className="space-y-4">
          {selectedIncident?.resolution && (
            <div className="p-3.5 bg-yellow-500/10 border border-yellow-500/30 rounded-xl text-xs space-y-1 text-foreground">
              <div className="flex items-center gap-1.5 font-bold text-yellow-600 dark:text-yellow-400">
                <AlertCircle className="w-4 h-4" />
                <span>Return for Correction Reason:</span>
              </div>
              <p className="text-muted-foreground">{selectedIncident.resolution}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Incident Type <span className="text-red-500">*</span></label>
              <select 
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:ring-2 focus:ring-primary focus:outline-none"
                value={incidentType}
                onChange={e => setIncidentType(e.target.value)}
                required
              >
                <option value="Damaged">Damaged</option>
                <option value="Malfunctioning">Malfunctioning</option>
                <option value="Repair Required">Repair Required</option>
                <option value="Replacement Required">Replacement Required</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Date of Incident</label>
              <Input 
                type="date"
                value={incidentDate}
                onChange={e => setIncidentDate(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Description of the Issue / Damage <span className="text-red-500">*</span></label>
            <textarea 
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm min-h-[90px] focus:ring-2 focus:ring-primary focus:outline-none"
              value={incidentDescription}
              onChange={e => setIncidentDescription(e.target.value)}
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">Supporting Photo / Attachment URL</label>
            <Input 
              type="text"
              placeholder="https://example.com/asset-photo.jpg"
              value={imageUrl}
              onChange={e => setImageUrl(e.target.value)}
            />
          </div>

          <div className="flex justify-end space-x-2 pt-4 border-t border-border">
            <Button type="button" variant="outline" onClick={() => setIsEditModalOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting || !incidentDescription.trim()}>Resubmit Report</Button>
          </div>
        </form>
      </Dialog>

      {/* View Incident Modal */}
      <Dialog isOpen={isViewModalOpen} onClose={() => setIsViewModalOpen(false)} title={`Asset Incident #${selectedIncident?.incident_id}`}>
        {selectedIncident && (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-4 pb-4 border-b border-border">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Asset Tag & Name</p>
                  <p className="text-sm font-semibold">{selectedIncident.asset?.asset_tag || `Asset #${selectedIncident.asset_id}`}</p>
                  <p className="text-xs text-muted-foreground">{selectedIncident.asset?.model || ""}</p>
                </div>
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Status</p>
                  <Badge variant={selectedIncident.status === "Resolved / Completed" ? "success" : selectedIncident.status === "Rejected" ? "danger" : selectedIncident.status === "Returned for Correction" ? "warning" : "info"}>
                    {selectedIncident.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Incident Type</p>
                  <p className="text-sm font-semibold">{selectedIncident.incident_type}</p>
                </div>
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Incident Date</p>
                  <p className="text-sm">{selectedIncident.incident_date || new Date(selectedIncident.created_at || Date.now()).toLocaleDateString()}</p>
                </div>
            </div>
            
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Description & Details</p>
              <div className="bg-muted/40 p-3.5 rounded-xl border border-border text-sm whitespace-pre-wrap">
                {selectedIncident.description}
              </div>
            </div>

            {selectedIncident.image_url && (
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Attachments / Photos</p>
                <a href={selectedIncident.image_url} target="_blank" rel="noreferrer" className="text-xs text-primary underline break-all">
                  {selectedIncident.image_url}
                </a>
              </div>
            )}

            {selectedIncident.manager_inspection_assessment && (
              <div className="p-3 bg-muted/30 rounded-xl border border-border text-xs space-y-1">
                <span className="font-bold text-foreground uppercase tracking-wider text-[10px]">Manager Inspection Assessment:</span>
                <p className="font-semibold text-primary">{selectedIncident.manager_inspection_assessment}</p>
                {selectedIncident.manager_inspection_comments && (
                  <p className="text-muted-foreground mt-1">Comments: {selectedIncident.manager_inspection_comments}</p>
                )}
              </div>
            )}

            {selectedIncident.admin_inspection_resolution && (
              <div className="p-3 bg-muted/30 rounded-xl border border-border text-xs space-y-1">
                <span className="font-bold text-foreground uppercase tracking-wider text-[10px]">Admin Inspection & Resolution:</span>
                <p className="font-semibold text-primary">{selectedIncident.admin_inspection_resolution}</p>
                {selectedIncident.admin_comments && (
                  <p className="text-muted-foreground mt-1">Notes: {selectedIncident.admin_comments}</p>
                )}
              </div>
            )}
            
            {selectedIncident.resolution && (
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">Resolution / Reason Notes</p>
                <div className="bg-muted/40 p-3 rounded-xl border border-border text-xs">
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

