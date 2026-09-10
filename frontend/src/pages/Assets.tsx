import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { Asset, User } from "../types";
import { Card, CardContent, Badge, Skeleton, Button, Dialog, EmptyState, Input, Select } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import toast from "react-hot-toast";
import { ArrowRightLeft, Filter, Plus, Search, Edit2 } from "lucide-react";

export const Assets: React.FC = () => {
  const { user } = useAuth();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter State
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");

  // Add Asset State
  const [isAssetModalOpen, setIsAssetModalOpen] = useState(false);
  const [editingAssetId, setEditingAssetId] = useState<number | null>(null);
  const [newAsset, setNewAsset] = useState({ name: "", category: "Hardware", cost: "", status: "Unassigned" });

  // Transfer Modal State
  const [transferAsset, setTransferAsset] = useState<Asset | null>(null);
  const [selectedUser, setSelectedUser] = useState("");
  const [transferNotes, setTransferNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isAdmin = user?.roles?.some(r => r.role_name === "Admin") || false;
  const canViewAll = user?.roles?.some(r => ["Admin", "CEO", "CFO", "Finance Manager"].includes(r.role_name)) || false;

  const fetchData = async () => {
    setLoading(true);
    try {
      const endpoint = canViewAll ? "/assets" : "/assets/my-assets";
      const assetsRes = await api.get(endpoint);
      setAssets(assetsRes.data);
    } catch (err) {
      console.error("Failed to load assets:", err);
    }
    
    if (isAdmin) {
      try {
        const usersRes = await api.get("/users");
        setUsers(usersRes.data);
      } catch (err) {
        console.error("Failed to load users:", err);
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleTransferSubmit = async () => {
    if (!transferAsset || !selectedUser) return;
    setIsSubmitting(true);
    try {
      await api.post(`/assets/${transferAsset.asset_id}/transfer`, {
        new_employee_id: parseInt(selectedUser),
        notes: transferNotes
      });
      toast.success("Asset transferred successfully!");
      setTransferAsset(null);
      setSelectedUser("");
      setTransferNotes("");
      fetchData();
    } catch (err) {
      toast.error("Failed to transfer asset.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const openAddModal = () => {
    setNewAsset({ name: "", category: "Hardware", cost: "", status: "Unassigned" });
    setEditingAssetId(null);
    setIsAssetModalOpen(true);
  }

  const openEditModal = (asset: any) => {
    setNewAsset({ 
      name: asset.asset_name || "", 
      category: asset.category || "Hardware", 
      cost: asset.cost?.toString() || "", 
      status: asset.status || "Unassigned" 
    });
    setEditingAssetId(asset.asset_id);
    setIsAssetModalOpen(true);
  }

  const handleSaveAsset = async () => {
    if (!newAsset.name || !newAsset.category || !newAsset.cost || Number(newAsset.cost) <= 0) return;
    setIsSubmitting(true);
    try {
      if (editingAssetId) {
        await api.put(`/assets/${editingAssetId}`, {
          model: newAsset.name,
          status: newAsset.status,
          cost: Number(newAsset.cost)
        });
        toast.success("Asset updated successfully!");
      } else {
        await api.post(`/assets`, {
          asset_number: `AST-${Math.floor(Math.random() * 1000000)}`,
          asset_tag: `TAG-${Math.floor(Math.random() * 1000000)}`,
          model: newAsset.name,
          category_id: null,
          status: newAsset.status
        });
        toast.success("Asset added successfully!");
      }
      setIsAssetModalOpen(false);
      fetchData();
    } catch (err) {
      toast.error(editingAssetId ? "Failed to update asset." : "Failed to add asset.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredAssets = assets.filter(a => {
    const matchesSearch = a.asset_code.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          a.asset_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "All" || a.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Global Asset Inventory</h1>
          <p className="text-xs text-muted-foreground mt-1">Audit capital assets, serial numbers, and assignments.</p>
        </div>
        
        {isAdmin && (
          <Button onClick={openAddModal} className="flex items-center space-x-2">
            <Plus className="w-4 h-4" />
            <span>Add Asset</span>
          </Button>
        )}
      </div>

      <Card>
        <CardContent className="p-0">
          {/* Filters Bar */}
          <div className="p-4 border-b border-border bg-accent/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="relative max-w-sm w-full">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input 
                type="text" 
                placeholder="Search by tag or name..." 
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm rounded-lg border border-border bg-background focus:ring-2 focus:ring-violet outline-none"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-muted-foreground" />
              <select 
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                className="px-3 py-2 text-sm rounded-lg border border-border bg-background outline-none focus:ring-2 focus:ring-violet"
              >
                <option value="All">All Statuses</option>
                <option value="Active">Active</option>
                <option value="Assigned">Assigned</option>
                <option value="Retired">Retired</option>
                <option value="Out of Service">Out of Service</option>
              </select>
            </div>
          </div>

          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full rounded-lg" />
              <Skeleton className="h-8 w-full rounded-lg" />
            </div>
          ) : filteredAssets.length === 0 ? (
            <EmptyState title="No registered assets found." description="Adjust your filters or add a new asset." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/30 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                    <th className="p-4">Asset Tag</th>
                    <th className="p-4">Name</th>
                    <th className="p-4">Category</th>
                    {canViewAll && <th className="p-4">Assigned To</th>}
                    {canViewAll && <th className="p-4">Cost</th>}
                    <th className="p-4">Status</th>
                    {isAdmin && <th className="p-4 text-right">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredAssets.map((a) => (
                    <tr key={a.asset_id} className="hover:bg-accent/10 transition-colors">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{a.asset_code}</td>
                      <td className="p-4 font-semibold">{a.asset_name}</td>
                      <td className="p-4 text-muted-foreground">{a.category}</td>
                      {canViewAll && <td className="p-4 text-xs font-semibold">{a.assigned_to_name || "Unassigned"}</td>}
                      {canViewAll && <td className="p-4 font-mono">${a.cost?.toLocaleString()}</td>}
                      <td className="p-4">
                        <Badge 
                          variant={
                            ["Damaged", "Reported", "Under Maintenance", "Disposed", "Lost", "Out of Service"].includes(a.status) ? "error" : 
                            a.status === "Active" || a.status === "Unassigned" ? "success" : 
                            a.status === "Assigned" ? "warning" : 
                            "neutral"
                          }
                        >
                          {a.status}
                        </Badge>
                      </td>
                      {isAdmin && (
                        <td className="p-4 text-right">
                          {["Damaged", "Reported", "Under Maintenance", "Disposed", "Out of Service"].includes(a.status) ? (
                            <Button size="sm" variant="ghost" disabled>
                              Unavailable
                            </Button>
                          ) : (
                            <div className="flex justify-end items-center gap-2">
                              {(!a.assigned_to_name || a.assigned_to_name === "Unassigned") && (
                                <Button size="sm" variant="ghost" onClick={() => openEditModal(a)}>
                                  <Edit2 className="w-3.5 h-3.5" />
                                </Button>
                              )}
                              <Button size="sm" variant="outline" onClick={() => setTransferAsset(a)}>
                                <ArrowRightLeft className="w-3.5 h-3.5 mr-1.5" /> {a.assigned_to_name && a.assigned_to_name !== "Unassigned" ? "Transfer" : "Assign"}
                              </Button>
                            </div>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Asset Dialog */}
      <Dialog isOpen={isAssetModalOpen} onClose={() => setIsAssetModalOpen(false)} title={editingAssetId ? "Edit Asset" : "Add New Asset"}>
        <div className="space-y-4">
          <Input 
            label="Asset Name" 
            placeholder="e.g. MacBook Pro M3" 
            value={newAsset.name} 
            onChange={(e) => setNewAsset({...newAsset, name: e.target.value})} 
          />
          <Select 
            label="Category" 
            value={newAsset.category}
            onChange={(e) => setNewAsset({...newAsset, category: e.target.value})}
            options={[
              { label: "Hardware", value: "Hardware" },
              { label: "Software", value: "Software" },
              { label: "Furniture", value: "Furniture" }
            ]}
          />
          <Input 
            label="Cost ($)" 
            type="number" 
            placeholder="0.00" 
            value={newAsset.cost} 
            onChange={(e) => setNewAsset({...newAsset, cost: e.target.value})} 
          />
          <Select 
            label="Status" 
            value={newAsset.status}
            onChange={(e) => setNewAsset({...newAsset, status: e.target.value})}
            options={[
              { label: "Unassigned", value: "Unassigned" },
              { label: "Assigned", value: "Assigned" },
              { label: "Out of Service", value: "Out of Service" }
            ]}
          />
          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="ghost" onClick={() => setIsAssetModalOpen(false)}>Cancel</Button>
            <Button variant="primary" onClick={handleSaveAsset} disabled={isSubmitting || !newAsset.name || !newAsset.category || !newAsset.cost || Number(newAsset.cost) <= 0}>
              {isSubmitting ? "Saving..." : "Save Asset"}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Transfer Asset Dialog */}
      <Dialog isOpen={!!transferAsset} onClose={() => setTransferAsset(null)} title={transferAsset?.assigned_to_name && transferAsset.assigned_to_name !== "Unassigned" ? "Transfer Asset" : "Assign Asset"}>
        {transferAsset && (
          <div className="space-y-4">
            <div className="bg-muted/40 p-3 rounded-lg border border-border text-xs">
              <span className="block font-semibold text-muted-foreground">Asset Details</span>
              <span className="font-bold text-sm text-foreground/90">{transferAsset.asset_name} ({transferAsset.asset_code})</span>
              <span className="block text-muted-foreground mt-1">Currently Assigned To: <span className="font-semibold text-foreground">{transferAsset.assigned_to_name || "Unassigned"}</span></span>
            </div>
            
            <Select 
              label="New Assignee"
              value={selectedUser}
              onChange={e => setSelectedUser(e.target.value)}
              options={[
                { value: "", label: "Select an employee..." },
                ...users.map(u => ({ value: u.user_id.toString(), label: `${u.first_name} ${u.last_name} (${u.roles && u.roles.length > 0 ? u.roles.map(r => r.role_name).join(', ') : 'Employee'})` }))
              ]}
            />

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Transfer Notes / Reason</label>
              <textarea 
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm min-h-[80px]"
                value={transferNotes}
                onChange={e => setTransferNotes(e.target.value)}
                placeholder="Optional notes regarding this assignment..."
              />
            </div>
            
            <div className="flex justify-end space-x-3 pt-4 border-t border-border mt-4">
              <Button variant="ghost" onClick={() => setTransferAsset(null)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleTransferSubmit} disabled={isSubmitting || !selectedUser}>
                {isSubmitting ? "Processing..." : (transferAsset?.assigned_to_name && transferAsset.assigned_to_name !== "Unassigned" ? "Transfer Asset" : "Assign Asset")}
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
};

export default Assets;
