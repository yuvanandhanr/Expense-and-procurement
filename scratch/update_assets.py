import re

def main():
    path = "/Users/a.chaitnasree/Expense-and-procurement/frontend/src/pages/Assets.tsx"
    with open(path, "r") as f:
        content = f.read()

    # 1. Update imports
    content = content.replace('import { ArrowRightLeft, Filter, Plus, Search } from "lucide-react";', 'import { ArrowRightLeft, Filter, Plus, Search, Edit2 } from "lucide-react";')
    
    # 2. Update states
    content = content.replace('const [isAddAssetOpen, setIsAddAssetOpen] = useState(false);', 'const [isAssetModalOpen, setIsAssetModalOpen] = useState(false);\n  const [editingAssetId, setEditingAssetId] = useState<number | null>(null);')
    content = content.replace('const [newAsset, setNewAsset] = useState({ name: "", category: "Hardware", cost: "", status: "Active" });', 'const [newAsset, setNewAsset] = useState({ name: "", category: "Hardware", cost: "", status: "Unassigned" });')
    
    # 3. Replace handleAddAsset with openAddModal, openEditModal, handleSaveAsset
    old_handleAdd = """  const handleAddAsset = async () => {
    if (!newAsset.name || !newAsset.cost) return;
    setIsSubmitting(true);
    try {
      await api.post(`/assets`, {
        asset_number: `AST-${Math.floor(Math.random() * 1000000)}`,
        asset_tag: `TAG-${Math.floor(Math.random() * 1000000)}`,
        model: newAsset.name,
        category_id: null,
        status: newAsset.status
      });
      toast.success("Asset added successfully!");
      setIsAddAssetOpen(false);
      setNewAsset({ name: "", category: "Hardware", cost: "", status: "Active" });
      fetchData();
    } catch (err) {
      toast.error("Failed to add asset.");
    } finally {
      setIsSubmitting(false);
    }
  };"""
    
    new_handleAdd = """  const openAddModal = () => {
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
  };"""
    content = content.replace(old_handleAdd, new_handleAdd)
    
    # 4. Update button to open add modal
    content = content.replace('onClick={() => setIsAddAssetOpen(true)}', 'onClick={openAddModal}')
    
    # 5. Fix status filter
    content = content.replace('<option value="Damaged">Damaged</option>', '<option value="Out of Service">Out of Service</option>')
    
    # 6. Fix table Badge
    old_badge = """                        <Badge 
                          variant={
                            ["Damaged", "Reported", "Under Maintenance", "Disposed", "Lost"].includes(a.status) ? "error" : 
                            a.status === "Active" ? "success" : 
                            a.status === "Assigned" ? "warning" : 
                            "neutral"
                          }
                        >"""
    new_badge = """                        <Badge 
                          variant={
                            ["Damaged", "Reported", "Under Maintenance", "Disposed", "Lost", "Out of Service"].includes(a.status) ? "error" : 
                            a.status === "Active" || a.status === "Unassigned" ? "success" : 
                            a.status === "Assigned" ? "warning" : 
                            "neutral"
                          }
                        >"""
    content = content.replace(old_badge, new_badge)
    
    # 7. Update table Actions
    old_actions = """                          {["Damaged", "Reported", "Under Maintenance", "Disposed"].includes(a.status) ? (
                            <Button size="sm" variant="ghost" disabled>
                              Unavailable
                            </Button>
                          ) : (
                            <Button size="sm" variant="outline" onClick={() => setTransferAsset(a)}>
                              <ArrowRightLeft className="w-3.5 h-3.5 mr-1.5" /> {a.assigned_to_name ? "Transfer" : "Assign"}
                            </Button>
                          )}"""
    
    new_actions = """                          {["Damaged", "Reported", "Under Maintenance", "Disposed", "Out of Service"].includes(a.status) ? (
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
                          )}"""
    content = content.replace(old_actions, new_actions)
    
    # 8. Update Add Asset Dialog
    old_dialog = """      <Dialog isOpen={isAddAssetOpen} onClose={() => setIsAddAssetOpen(false)} title="Add New Asset">"""
    new_dialog = """      <Dialog isOpen={isAssetModalOpen} onClose={() => setIsAssetModalOpen(false)} title={editingAssetId ? "Edit Asset" : "Add New Asset"}>"""
    content = content.replace(old_dialog, new_dialog)
    
    old_dialog_cancel = """<Button variant="ghost" onClick={() => setIsAddAssetOpen(false)}>Cancel</Button>"""
    new_dialog_cancel = """<Button variant="ghost" onClick={() => setIsAssetModalOpen(false)}>Cancel</Button>"""
    content = content.replace(old_dialog_cancel, new_dialog_cancel)
    
    old_dialog_save = """<Button variant="primary" onClick={handleAddAsset} disabled={isSubmitting || !newAsset.name || !newAsset.cost}>
              {isSubmitting ? "Saving..." : "Save Asset"}
            </Button>"""
    new_dialog_save = """<Button variant="primary" onClick={handleSaveAsset} disabled={isSubmitting || !newAsset.name || !newAsset.category || !newAsset.cost || Number(newAsset.cost) <= 0}>
              {isSubmitting ? "Saving..." : "Save Asset"}
            </Button>"""
    content = content.replace(old_dialog_save, new_dialog_save)
    
    # Update dropdown options
    old_dropdown = """<Select 
            label="Initial Status" 
            value={newAsset.status}
            onChange={(e) => setNewAsset({...newAsset, status: e.target.value})}
            options={[
              { label: "Active (Unassigned)", value: "Active" },
              { label: "In Repair", value: "Repair" }
            ]}
          />"""
    new_dropdown = """<Select 
            label="Status" 
            value={newAsset.status}
            onChange={(e) => setNewAsset({...newAsset, status: e.target.value})}
            options={[
              { label: "Unassigned", value: "Unassigned" },
              { label: "Assigned", value: "Assigned" },
              { label: "Out of Service", value: "Out of Service" }
            ]}
          />"""
    content = content.replace(old_dropdown, new_dropdown)
    
    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()
