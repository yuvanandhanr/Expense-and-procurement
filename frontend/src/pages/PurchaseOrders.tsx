import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { PurchaseOrder } from "../types";
import { Card, CardHeader, CardTitle, CardContent, Badge, StatusBadge, Skeleton, EmptyState, Button, Dialog, Input } from "../components/ui";
import { formatDate } from "../utils/helpers";
import toast from "react-hot-toast";

export const PurchaseOrders: React.FC = () => {
  const [pos, setPos] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedPo, setExpandedPo] = useState<number | null>(null);

  const [verifyDialogItem, setVerifyDialogItem] = useState<any | null>(null);
  const [productUniqueId, setProductUniqueId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchPOs = async () => {
    setLoading(true);
    try {
      const response = await api.get("/purchase-orders");
      setPos(response.data);
    } catch (err) {
      console.error("Failed to load POs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPOs();
  }, []);

  const toggleExpand = (po_id: number) => {
    setExpandedPo(expandedPo === po_id ? null : po_id);
  };

  const handleVerifyDelivery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productUniqueId) {
      toast.error("Please enter the Product Unique ID.");
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post(`/purchase-orders/${verifyDialogItem.po_id}/items/${verifyDialogItem.po_item_id}/verify-delivery`, {
        receiver_product_id: productUniqueId
      });
      toast.success("Delivery verified and Asset created successfully!");
      setVerifyDialogItem(null);
      fetchPOs();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to verify delivery.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Purchase Orders (POs)</h1>
        <p className="text-xs text-muted-foreground mt-1">Track binding contracts sent to suppliers and verify deliveries.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : pos.length === 0 ? (
            <EmptyState title="No Purchase Orders active." description="Data will appear here once available." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                    <th className="p-4 w-8 whitespace-nowrap"></th>
                    <th className="p-4 whitespace-nowrap">PO Number</th>
                    <th className="p-4 whitespace-nowrap">PR Reference</th>
                    <th className="p-4 whitespace-nowrap">Total Amount</th>
                    <th className="p-4 whitespace-nowrap">Status</th>
                    <th className="p-4 whitespace-nowrap">Date Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {pos.map((p) => (
                    <React.Fragment key={p.po_id}>
                      <tr className="hover:bg-accent/20 cursor-pointer" onClick={() => toggleExpand(p.po_id)}>
                        <td className="p-4 text-muted-foreground">
                          {expandedPo === p.po_id ? "▼" : "▶"}
                        </td>
                        <td className="p-4 font-bold text-xs tracking-wider text-primary whitespace-nowrap">{p.po_number}</td>
                        <td className="p-4 whitespace-nowrap">#PR-{p.pr_id}</td>
                        <td className="p-4 font-bold whitespace-nowrap">${p.total_amount?.toLocaleString()}</td>
                        <td className="p-4 whitespace-nowrap">
                          <StatusBadge status={p.status} />
                        </td>
                        <td className="p-4 text-xs text-muted-foreground whitespace-nowrap">{formatDate(p.created_at)}</td>
                      </tr>
                      
                      {/* Expanded Items Row */}
                      {expandedPo === p.po_id && (
                        <tr className="bg-muted/10">
                          <td colSpan={6} className="p-4 border-b border-border">
                            <div className="pl-8 py-2">
                              <h4 className="text-xs font-bold uppercase text-muted-foreground mb-3 tracking-wider">Order Items & Delivery Status</h4>
                              <div className="grid grid-cols-1 gap-3">
                                {p.items?.filter((item: any) => item.delivery_verification_status !== "Matched").map((item: any) => (
                                  <div key={item.po_item_id} className="bg-background border border-border p-3 rounded-lg flex items-center justify-between shadow-sm">
                                    <div>
                                      <span className="font-semibold text-sm block text-foreground/90">{item.item_name}</span>
                                      <span className="text-[10px] text-muted-foreground block mt-0.5">
                                        Qty: {item.quantity} | Total: ${item.total_price?.toLocaleString()}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                      <StatusBadge status={item.delivery_verification_status || "Pending"} />
                                      
                                      {item.delivery_verification_status === "Vendor Delivered" && (
                                        <Button size="sm" onClick={() => {
                                          setVerifyDialogItem({ ...item, po_id: p.po_id });
                                          setProductUniqueId("");
                                        }}>
                                          Verify Delivery
                                        </Button>
                                      )}
                                    </div>
                                  </div>
                                ))}
                                {(!p.items || p.items.filter((i: any) => i.delivery_verification_status !== "Matched").length === 0) && (
                                  <div className="text-xs text-muted-foreground">All items matched or no items available.</div>
                                )}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Verification Dialog */}
      {verifyDialogItem && (
        <Dialog isOpen={true} onClose={() => setVerifyDialogItem(null)} title="Verify Delivery">
          <form onSubmit={handleVerifyDelivery} className="space-y-4">
            <div className="bg-muted/40 p-3 rounded-lg border border-border text-xs mb-4">
              <span className="block font-semibold text-muted-foreground uppercase mb-1">Item to Verify</span>
              <span className="font-bold text-sm text-foreground/90">{verifyDialogItem.item_name}</span>
              <p className="mt-2 text-muted-foreground">Please enter the Unique Product ID (Serial Number / Asset Tag) found on the physical item. If it matches the vendor's record, it will be automatically added to your Asset Registry.</p>
            </div>

            <Input
              id="unique_id"
              type="text"
              label="Unique Product ID"
              placeholder="Enter ID..."
              value={productUniqueId}
              onChange={(e) => setProductUniqueId(e.target.value)}
            />

            <div className="flex justify-end space-x-2 pt-4 border-t border-border">
              <Button variant="close" size="sm" type="button" onClick={() => setVerifyDialogItem(null)}>Cancel</Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Verifying..." : "Verify & Claim"}
              </Button>
            </div>
          </form>
        </Dialog>
      )}
    </div>
  );
};
export default PurchaseOrders;
