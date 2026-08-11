import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { Asset, User } from "../types";
import { Card, CardContent, Badge, Skeleton, Button, Dialog } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import toast from "react-hot-toast";
import { ArrowRightLeft } from "lucide-react";

export const Assets: React.FC = () => {
  const { user } = useAuth();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  // Transfer Modal State
  const [transferAsset, setTransferAsset] = useState<Asset | null>(null);
  const [selectedUser, setSelectedUser] = useState("");
  const [transferNotes, setTransferNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isAdmin = user?.roles?.some(r => r.role_name === "Admin") || false;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [assetsRes, usersRes] = await Promise.all([
          api.get("/assets"),
          api.get("/users")
        ]);
        setAssets(assetsRes.data);
        setUsers(usersRes.data);
      } catch (err) {
        console.error("Failed to load data:", err);
      } finally {
        setLoading(false);
      }
    };
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
      
      // Reload assets
      const assetsRes = await api.get("/assets");
      setAssets(assetsRes.data);
    } catch (err) {
      toast.error("Failed to transfer asset.");
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Capital Assets Registry</h1>
        <p className="text-xs text-muted-foreground mt-1">Audit capital assets, serial numbers, and office locations.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : assets.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              No registered assets found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                    <th className="p-4">Asset Code</th>
                    <th className="p-4">Name</th>
                    <th className="p-4">Serial Number</th>
                    <th className="p-4">Category</th>
                    <th className="p-4">Assigned To</th>
                    <th className="p-4">Cost</th>
                    <th className="p-4">Status</th>
                    {isAdmin && <th className="p-4 text-right">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {assets.map((a) => (
                    <tr key={a.asset_id} className="hover:bg-accent/20">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{a.asset_code}</td>
                      <td className="p-4 font-semibold">{a.asset_name}</td>
                      <td className="p-4 font-mono text-xs">{a.serial_number || "N/A"}</td>
                      <td className="p-4">{a.category}</td>
                      <td className="p-4 text-xs font-semibold">{a.assigned_to_name || "Unassigned"}</td>
                      <td className="p-4 font-bold">${a.cost?.toLocaleString()}</td>
                      <td className="p-4">
                        <Badge variant={a.status === "Active" || a.status === "Assigned" ? "success" : "neutral"}>
                          {a.status}
                        </Badge>
                      </td>
                      {isAdmin && (
                        <td className="p-4 text-right">
                          <Button size="sm" variant="outline" onClick={() => setTransferAsset(a)}>
                            <ArrowRightLeft className="w-4 h-4 mr-1" /> Transfer
                          </Button>
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

      {/* Transfer Asset Dialog */}
      {transferAsset && (
        <Dialog isOpen={true} onClose={() => setTransferAsset(null)} title="Transfer Asset">
          <div className="space-y-4">
            <div className="bg-muted/40 p-3 rounded-lg border border-border text-xs">
              <span className="block font-semibold text-muted-foreground">Asset Details</span>
              <span className="font-bold text-sm text-foreground/90">{transferAsset.asset_name} ({transferAsset.asset_code})</span>
              <span className="block text-muted-foreground mt-1">Currently Assigned To: <span className="font-semibold text-foreground">{transferAsset.assigned_to_name}</span></span>
            </div>
            
            <div>
              <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">New Employee</label>
              <select 
                value={selectedUser} 
                onChange={e => setSelectedUser(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">-- Select Employee --</option>
                {users.map(u => (
                  <option key={u.user_id} value={u.user_id}>{u.first_name} {u.last_name} ({u.employee_code})</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Transfer Notes (Optional)</label>
              <textarea
                value={transferNotes}
                onChange={(e) => setTransferNotes(e.target.value)}
                placeholder="Reason for transfer, conditions, etc..."
                className="w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px]"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-4 border-t border-border">
              <Button variant="outline" type="button" onClick={() => setTransferAsset(null)}>
                Cancel
              </Button>
              <Button type="button" onClick={handleTransferSubmit} disabled={isSubmitting || !selectedUser}>
                {isSubmitting ? "Transferring..." : "Confirm Transfer"}
              </Button>
            </div>
          </div>
        </Dialog>
      )}
    </div>
  );
};
export default Assets;
