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
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter State
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [activeMainCategory, setActiveMainCategory] = useState<string>("All");
  const [activeSubCategory, setActiveSubCategory] = useState<string>("All");


  // Add Asset State
  const [isAssetModalOpen, setIsAssetModalOpen] = useState(false);
  const [editingAssetId, setEditingAssetId] = useState<number | null>(null);
  const [newAsset, setNewAsset] = useState({ name: "", category_id: "", cost: "", status: "Unassigned" });

  const MAIN_CATEGORIES = [
    "All",
    "Hardware",
    "Network",
    "Server & Storage",
    "Software",
    "Software Licenses",
    "Cloud",
    "Security",
    "Communication",
    "Office",
    "Vehicle"
  ];
  
  const SUB_CATEGORIES: Record<string, string[]> = {
    "Hardware": ["All", "Laptop", "Desktop", "Monitor", "Mobile", "Tablet", "Printer", "Other Peripherals"],
    "Network": ["All", "Router", "Switch", "Firewall", "Access Point", "Network Equipment"],
    "Server & Storage": ["All", "Server", "NAS", "Storage", "Backup"],
    "Software": ["All", "Operating System", "Application", "Database", "Development Software"],
    "Software Licenses": ["All", "Subscription", "Enterprise License", "User License"],
    "Cloud": ["All", "VM", "Storage", "Database", "Cloud Service", "SaaS"],
    "Security": ["All", "Security Device", "Certificate", "Security Key", "Security Software"],
    "Communication": ["All", "IP Phone", "Headset", "Webcam", "Conference Equipment"],
    "Office": ["All", "Desk", "Chair", "Projector", "UPS"],
    "Vehicle": ["All", "Car", "Bike", "Other"]
  };


  // Transfer Modal State
  const [transferAsset, setTransferAsset] = useState<Asset | null>(null);
  const [selectedUser, setSelectedUser] = useState("");
  const [transferNotes, setTransferNotes] = useState("");
  const [assigneeSearchQuery, setAssigneeSearchQuery] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isAdmin = user?.roles?.some(r => r.role_name === "Admin") || false;
  const canViewAll = user?.roles?.some(r => ["Admin", "CFO", "Finance Manager"].includes(r.role_name)) || false;
  const canViewCost = user?.roles?.some(r => ["Admin", "CFO"].includes(r.role_name)) || false;

  const fetchData = async () => {
    setLoading(true);
    try {
      // According to requirements, Admin, CFO, Finance Manager can see the global registry
      const endpoint = "/assets";
      const assetsRes = await api.get(endpoint);
      setAssets(assetsRes.data);

      const catRes = await api.get("/assets/categories");
      setCategories(catRes.data);
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
    setNewAsset({ name: "", category_id: "", cost: "", status: "Unassigned" });
    setEditingAssetId(null);
    setIsAssetModalOpen(true);
  }

  const openEditModal = (asset: any) => {
    // Find category ID from category name
    const cat = categories.find(c => c.name === asset.category);
    setNewAsset({ 
      name: asset.asset_name || "", 
      category_id: cat?.id?.toString() || "", 
      cost: asset.cost?.toString() || "", 
      status: asset.status || "Unassigned" 
    });
    setEditingAssetId(asset.asset_id);
    setIsAssetModalOpen(true);
  }

  const handleSaveAsset = async () => {
    if (!newAsset.name || !newAsset.category_id || !newAsset.cost || Number(newAsset.cost) <= 0) return;
    setIsSubmitting(true);
    try {
      if (editingAssetId) {
        await api.put(`/assets/${editingAssetId}`, {
          model: newAsset.name,
          status: newAsset.status,
          cost: Number(newAsset.cost),
          category_id: Number(newAsset.category_id)
        });
        toast.success("Asset updated successfully!");
      } else {
        await api.post(`/assets`, {
          asset_number: `AST-${Math.floor(Math.random() * 1000000)}`,
          asset_tag: `TAG-${Math.floor(Math.random() * 1000000)}`,
          model: newAsset.name,
          category_id: Number(newAsset.category_id),
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

  const filteredAssigneeUsers = users
    .filter(u => !u.roles?.some(r => r.role_name.toLowerCase().includes("vendor")))
    .filter(u => {
      if (!assigneeSearchQuery.trim()) return true;
      const q = assigneeSearchQuery.toLowerCase();
      const nameMatch = `${u.first_name} ${u.last_name}`.toLowerCase().includes(q);
      const roleMatch = u.roles?.some(r => r.role_name.toLowerCase().includes(q)) || false;
      return nameMatch || roleMatch;
    });

  const getMainCategoryCount = (mainCat: string) => {
    if (mainCat === "All") return assets.length;
    const allowedSubcats = SUB_CATEGORIES[mainCat] || [];
    return assets.filter(a => allowedSubcats.includes(a.category)).length;
  };

  const getSubCategoryCount = (subCat: string, mainCat: string) => {
    if (subCat === "All") return getMainCategoryCount(mainCat);
    return assets.filter(a => a.category === subCat).length;
  };

  const handleMainCategoryChange = (mainCat: string) => {
    setActiveMainCategory(mainCat);
    setActiveSubCategory("All");
  };

  // We only count based on the current category filter so the counts are accurate for the current view
  const categoryFilteredAssets = assets.filter(a => {
    if (activeMainCategory === "All") return true;
    if (activeSubCategory !== "All") {
      return a.category === activeSubCategory;
    } else {
      const allowedSubcats = SUB_CATEGORIES[activeMainCategory] || [];
      return allowedSubcats.includes(a.category);
    }
  });

  const counts = {
    "All Assets": categoryFilteredAssets.length,
    "Assigned": categoryFilteredAssets.filter(isAssignedAsset).length,
    "Unassigned": categoryFilteredAssets.filter(isUnassignedAsset).length,
    "Out of Service": categoryFilteredAssets.filter(isOutOfServiceAsset).length,
  };

  const filteredAssets = assets.filter(a => {
    const matchesSearch = a.asset_code.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          a.asset_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    let matchesCategory = true;
    if (activeMainCategory !== "All") {
      if (activeSubCategory !== "All") {
        matchesCategory = a.category === activeSubCategory;
      } else {
        const allowedSubcats = SUB_CATEGORIES[activeMainCategory] || [];
        matchesCategory = allowedSubcats.includes(a.category);
      }
    }

    let matchesStatus = true;
    if (statusFilter === "Assigned") matchesStatus = isAssignedAsset(a);
    else if (statusFilter === "Unassigned") matchesStatus = isUnassignedAsset(a);
    else if (statusFilter === "Out of Service") matchesStatus = isOutOfServiceAsset(a);
    
    return matchesSearch && matchesCategory && matchesStatus;
  });


  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">ASSET INVENTORY</h1>
          <p className="text-xs text-muted-foreground mt-1">Global inventory of hardware, software, licenses, and equipment.</p>
        </div>
        
        {isAdmin && (
          <Button onClick={openAddModal} className="flex items-center space-x-2">
            <Plus className="w-4 h-4" />
            <span>Add Asset</span>
          </Button>
        )}
      </div>

      
      {/* Filters (Categories) */}
      <div className="space-y-4">
        {/* Main Category Filters */}
        <div className="flex flex-wrap items-center gap-2 bg-muted/40 p-1.5 rounded-xl w-full border border-border/50">
          {MAIN_CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => handleMainCategoryChange(cat)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center space-x-1.5 ${
                activeMainCategory === cat
                  ? "bg-primary text-primary-foreground shadow-sm font-bold"
                  : "text-muted-foreground hover:text-foreground hover:bg-background/50"
              }`}
            >
              <span>{cat}</span>
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                activeMainCategory === cat
                  ? "bg-primary-foreground/20 text-primary-foreground font-bold"
                  : "bg-muted text-muted-foreground"
              }`}>
                {getMainCategoryCount(cat)}
              </span>
            </button>
          ))}
        </div>

        {/* Sub Category Filters */}
        {activeMainCategory !== "All" && SUB_CATEGORIES[activeMainCategory] && (
          <div className="flex flex-wrap items-center gap-2 bg-muted/40 p-1.5 rounded-xl w-fit border border-border/50">
            {SUB_CATEGORIES[activeMainCategory].map((subCat) => (
              <button
                key={subCat}
                onClick={() => setActiveSubCategory(subCat)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center space-x-1.5 ${
                  activeSubCategory === subCat
                    ? "bg-primary text-primary-foreground shadow-sm font-bold"
                    : "text-muted-foreground hover:text-foreground hover:bg-background/50"
                }`}
              >
                <span>{subCat}</span>
                <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                  activeSubCategory === subCat
                    ? "bg-primary-foreground/20 text-primary-foreground font-bold"
                    : "bg-muted text-muted-foreground"
                }`}>
                  {getSubCategoryCount(subCat, activeMainCategory)}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="flex-1 space-y-4">
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
                  <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="w-40 text-sm">
                    <option value="All">All Statuses</option>
                    <option value="Assigned">Assigned</option>
                    <option value="Unassigned">Unassigned</option>
                    <option value="Out of Service">Out of Service</option>
                  </Select>
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
                                  <Button size="sm" variant="outline" onClick={() => { setTransferAsset(a); setAssigneeSearchQuery(""); }}>
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
        </div>
      {/* Add / Edit Asset Modal */}
      <Dialog open={isAssetModalOpen} onClose={() => setIsAssetModalOpen(false)} title={editingAssetId ? "Edit Asset" : "Add Asset"} description="Fill in the asset details below.">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Asset Model / Name</label>
            <Input value={newAsset.name} onChange={e => setNewAsset({ ...newAsset, name: e.target.value })} placeholder="e.g., MacBook Pro M3" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Category</label>
            <Select value={newAsset.category_id} onChange={e => setNewAsset({ ...newAsset, category_id: e.target.value })}>
              <option value="">Select a category</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </Select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Cost ($)</label>
            <Input type="number" value={newAsset.cost} onChange={e => setNewAsset({ ...newAsset, cost: e.target.value })} placeholder="0.00" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Status</label>
            <Select value={newAsset.status} onChange={e => setNewAsset({ ...newAsset, status: e.target.value })}>
              <option value="Unassigned">Unassigned</option>
              <option value="Out of Service">Out of Service</option>
              <option value="Retired">Retired</option>
            </Select>
          </div>
        </div>
        <div className="flex justify-end space-x-2 mt-6">
          <Button variant="outline" onClick={() => setIsAssetModalOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveAsset} disabled={isSubmitting}>{editingAssetId ? "Save Changes" : "Create Asset"}</Button>
        </div>
      </Dialog>

      {/* Transfer Asset Modal */}
      <Dialog open={!!transferAsset} onClose={() => setTransferAsset(null)} title="Assign Asset" description={`Assign ${transferAsset?.asset_name} (${transferAsset?.asset_code}) to an employee.`}>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Search Employee</label>
            <div className="relative mb-2">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search by name or role..."
                value={assigneeSearchQuery}
                onChange={e => setAssigneeSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm rounded-lg border border-border bg-background outline-none"
              />
            </div>
            <div className="border border-border rounded-lg max-h-48 overflow-y-auto bg-card">
              {filteredAssigneeUsers.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">No employees found.</div>
              ) : (
                filteredAssigneeUsers.map(u => (
                  <div
                    key={u.user_id}
                    className={`flex items-center justify-between p-3 border-b border-border last:border-b-0 cursor-pointer hover:bg-accent transition-colors ${selectedUser === u.user_id?.toString() ? "bg-primary/10 border-l-2 border-l-primary" : ""}`}
                    onClick={() => setSelectedUser(u.user_id?.toString() || "")}
                  >
                    <div>
                      <div className="font-semibold text-sm">{u.first_name} {u.last_name}</div>
                      <div className="text-xs text-muted-foreground">{u.email}</div>
                    </div>
                    <div className="flex flex-wrap gap-1 justify-end max-w-[120px]">
                      {u.roles?.slice(0, 2).map(r => (
                        <Badge key={r.role_id} variant="neutral" className="text-[10px] py-0">{r.role_name}</Badge>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Transfer Notes (Optional)</label>
            <Input value={transferNotes} onChange={e => setTransferNotes(e.target.value)} placeholder="e.g., Replacement for old laptop" />
          </div>
        </div>
        <div className="flex justify-end space-x-2 mt-6">
          <Button variant="outline" onClick={() => setTransferAsset(null)}>Cancel</Button>
          <Button onClick={handleTransferSubmit} disabled={isSubmitting || !selectedUser}>Assign to Employee</Button>
        </div>
      </Dialog>
    </div>
  );
};

export default Assets;