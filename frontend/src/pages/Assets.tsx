import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { Asset, User } from "../types";
import { Card, CardContent, Badge, Skeleton, Button, Dialog, EmptyState, Input, Select } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import toast from "react-hot-toast";
import { ArrowRightLeft, Filter, Plus, Search, Edit2, Layers, CheckCircle2, AlertCircle, Package } from "lucide-react";

export const Assets: React.FC = () => {
  const { user } = useAuth();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  // Category mapping
  const categoryToId: Record<string, number> = {
    "Laptop": 1,
    "Monitor": 2,
    "Hardware": 3,
    "Software": 4,
    "Furniture": 5
  };

  // Filter State
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [activeTab, setActiveTab] = useState<string>("All");

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
  const canViewCost = user?.roles?.some(r => ["Admin", "CEO", "CFO"].includes(r.role_name)) || false;

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
          cost: Number(newAsset.cost),
          category_id: categoryToId[newAsset.category] || null
        });
        toast.success("Asset updated successfully!");
      } else {
        await api.post(`/assets`, {
          asset_number: `AST-${Math.floor(Math.random() * 1000000)}`,
          asset_tag: `TAG-${Math.floor(Math.random() * 1000000)}`,
          model: newAsset.name,
          category_id: categoryToId[newAsset.category] || null,
          cost: Number(newAsset.cost),
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


  const isAssignedAsset = (a: Asset) => (a.assigned_to_name && a.assigned_to_name !== "Unassigned") || a.status === "Assigned" || a.status === "Transferred";
  const isOutOfServiceAsset = (a: Asset) => ["Out of Service", "Retired", "Damaged", "Disposed", "Lost", "Under Maintenance", "Reported"].includes(a.status);
  const isUnassignedAsset = (a: Asset) => !isAssignedAsset(a) && !isOutOfServiceAsset(a);

  const counts = {
    all: assets.length,
    assigned: assets.filter(isAssignedAsset).length,
    unassigned: assets.filter(isUnassignedAsset).length,
    outOfService: assets.filter(isOutOfServiceAsset).length,
  };

  const filteredAssets = assets.filter(a => {
    const matchesSearch = a.asset_code.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          a.asset_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    let matchesTab = true;
    if (activeTab === "Assigned") {
      matchesTab = isAssignedAsset(a);
    } else if (activeTab === "Unassigned") {
      matchesTab = isUnassignedAsset(a);
    } else if (activeTab === "Out of Service") {
      matchesTab = isOutOfServiceAsset(a);
    }

    const matchesStatus = statusFilter === "All" || a.status === statusFilter;
    return matchesSearch && matchesTab && matchesStatus;
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


      {/* Metric Category Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <button
          onClick={() => setActiveTab("All")}
          className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
            activeTab === "All"
              ? "bg-primary/10 border-primary shadow-sm text-primary ring-1 ring-primary"
              : "bg-card border-border hover:bg-accent/40 text-muted-foreground"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider">All Assets</span>
            <Layers className="w-4 h-4 text-primary" />
          </div>
          <div className="text-2xl font-bold mt-2 text-foreground">{counts.all}</div>
          <div className="text-[11px] text-muted-foreground mt-0.5">Master Inventory List</div>
        </button>

        <button
          onClick={() => setActiveTab("Assigned")}
          className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
            activeTab === "Assigned"
              ? "bg-amber-500/10 border-amber-500 shadow-sm text-amber-500 ring-1 ring-amber-500"
              : "bg-card border-border hover:bg-accent/40 text-muted-foreground"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-500">Assigned</span>
            <CheckCircle2 className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold mt-2 text-foreground">{counts.assigned}</div>
          <div className="text-[11px] text-muted-foreground mt-0.5">Allocated to Employees</div>
        </button>

        <button
          onClick={() => setActiveTab("Unassigned")}
          className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
            activeTab === "Unassigned"
              ? "bg-emerald-500/10 border-emerald-500 shadow-sm text-emerald-500 ring-1 ring-emerald-500"
              : "bg-card border-border hover:bg-accent/40 text-muted-foreground"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-500">Unassigned</span>
            <Package className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold mt-2 text-foreground">{counts.unassigned}</div>
          <div className="text-[11px] text-muted-foreground mt-0.5">Available for Assignment</div>
        </button>

        <button
          onClick={() => setActiveTab("Out of Service")}
          className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
            activeTab === "Out of Service"
              ? "bg-rose-500/10 border-rose-500 shadow-sm text-rose-500 ring-1 ring-rose-500"
              : "bg-card border-border hover:bg-accent/40 text-muted-foreground"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-rose-500">Out of Service</span>
            <AlertCircle className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-bold mt-2 text-foreground">{counts.outOfService}</div>
          <div className="text-[11px] text-muted-foreground mt-0.5">Maintenance & Retired</div>
        </button>
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
                    {canViewCost && <th className="p-4">Cost</th>}
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
                      {canViewCost && <td className="p-4 font-mono">${a.cost?.toLocaleString()}</td>}
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
                          ) : ((a.assigned_to_name && a.assigned_to_name !== "Unassigned") || a.status === "Assigned" || a.status === "Transferred") ? (
                            <div className="flex justify-end items-center gap-2">
                              <Button size="sm" variant="ghost" disabled className="text-amber-400 opacity-80 cursor-not-allowed bg-amber-500/10 border border-amber-500/20">
                                Transferred
                              </Button>
                            </div>
                          ) : (
                            <div className="flex justify-end items-center gap-2">
                              <Button size="sm" variant="ghost" onClick={() => openEditModal(a)}>
                                <Edit2 className="w-3.5 h-3.5" />
                              </Button>
                              <Button size="sm" variant="outline" onClick={() => setTransferAsset(a)}>
                                <ArrowRightLeft className="w-3.5 h-3.5 mr-1.5" /> Assign
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
                ...users.filter(u => !u.roles?.some(r => r.role_name.toLowerCase().includes('vendor'))).map(u => ({ value: u.user_id.toString(), label: `${u.first_name} ${u.last_name} (${u.roles && u.roles.length > 0 ? u.roles.map(r => r.role_name).join(', ') : 'Employee'})` }))
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
