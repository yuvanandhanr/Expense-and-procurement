import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import {Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, Button, Dialog, Input, EmptyState} from "../components/ui";
import { formatDate } from "../utils/helpers";
import toast from "react-hot-toast";

export const DeliveredItems: React.FC = () => {
  const [purchaseOrders, setPurchaseOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedPo, setExpandedPo] = useState<number | null>(null);
  
  const [deliveryDialogItem, setDeliveryDialogItem] = useState<any | null>(null);
  const [productUniqueId, setProductUniqueId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const poRes = await api.get("/purchase-orders");
      setPurchaseOrders(poRes.data);
    } catch (err) {
      console.error("Failed to load purchase orders:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleMarkDelivered = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productUniqueId) {
      toast.error("Please enter the Product Unique ID.");
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post(`/purchase-orders/${deliveryDialogItem.po_id}/items/${deliveryDialogItem.po_item_id}/vendor-deliver`, {
        vendor_product_id: productUniqueId
      });
      toast.success("Item marked as delivered!");
      setDeliveryDialogItem(null);
      fetchData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to mark item as delivered.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleExpand = (po_id: number) => {
    setExpandedPo(expandedPo === po_id ? null : po_id);
  };

  return (
    <div className="space-y-6 font-sans">
      <Card>
        <CardHeader>
          <CardTitle>Assigned Purchase Orders (Delivered Items)</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : purchaseOrders.length === 0 ? (
            <EmptyState title="No active Purchase Orders at the moment." description="Data will appear here once available." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-[10px] font-bold text-muted-foreground uppercase">
                    <th className="p-4 w-8"></th>
                    <th className="p-4">PO Number</th>
                    <th className="p-4">RFQ Ref</th>
                    <th className="p-4">Amount</th>
                    <th className="p-4">Date</th>
                    <th className="p-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {purchaseOrders.map((po) => (
                    <React.Fragment key={po.po_id}>
                      <tr className="hover:bg-accent/10 cursor-pointer" onClick={() => toggleExpand(po.po_id)}>
                        <td className="p-4 text-muted-foreground">
                          {expandedPo === po.po_id ? "▼" : "▶"}
                        </td>
                        <td className="p-4 font-mono font-bold text-xs">{po.po_number}</td>
                        <td className="p-4 font-mono text-xs">{po.rfq_id ? `#RFQ-${po.rfq_id}` : "N/A"}</td>
                        <td className="p-4 font-bold text-primary">${po.grand_total?.toLocaleString()}</td>
                        <td className="p-4 text-xs">{formatDate(po.created_at)}</td>
                        <td className="p-4">
                          <Badge variant="neutral">{po.status}</Badge>
                        </td>
                      </tr>
                      {expandedPo === po.po_id && (
                        <tr className="bg-muted/10">
                          <td colSpan={6} className="p-4 border-b border-border">
                            <div className="pl-8 py-2">
                              <h4 className="text-xs font-bold uppercase text-muted-foreground mb-3 tracking-wider">Purchase Order Items</h4>
                              <div className="grid grid-cols-1 gap-3">
                                {po.items?.map((item: any) => (
                                  <div key={item.po_item_id} className="bg-background border border-border p-3 rounded-lg flex items-center justify-between shadow-sm">
                                    <div>
                                      <span className="font-semibold text-sm block text-foreground/90">{item.item_name}</span>
                                      <span className="text-[10px] text-muted-foreground block mt-0.5">
                                        Qty: {item.quantity} | Total: ${item.total_price?.toLocaleString()}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                      <Badge variant={
                                        item.delivery_verification_status === "Matched" ? "success" : 
                                        item.delivery_verification_status === "Returned / Cancelled" ? "danger" : 
                                        item.delivery_verification_status === "Vendor Delivered" ? "warning" : "neutral"
                                      }>
                                        {item.delivery_verification_status || "Pending"}
                                      </Badge>
                                      {(!item.delivery_verification_status || item.delivery_verification_status === "Pending") && (
                                        <Button size="sm" onClick={() => {
                                          setDeliveryDialogItem(item);
                                          setProductUniqueId("");
                                        }}>
                                          Mark as Delivered
                                        </Button>
                                      )}
                                    </div>
                                  </div>
                                ))}
                                {(!po.items || po.items.length === 0) && (
                                  <div className="text-xs text-muted-foreground">No items found for this PO.</div>
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

      {deliveryDialogItem && (
        <Dialog isOpen={true} onClose={() => setDeliveryDialogItem(null)} title="Mark Item as Delivered">
          <form onSubmit={handleMarkDelivered} className="space-y-4">
            <div className="bg-muted/40 p-3 rounded-lg border border-border text-xs mb-4">
              <span className="block font-semibold text-muted-foreground uppercase mb-1">Item to Deliver</span>
              <span className="font-bold text-sm text-foreground/90">{deliveryDialogItem.item_name}</span>
            </div>

            <Input
              id="unique_id"
              type="text"
              label="Product Unique ID"
              placeholder="Enter serial number or tracking ID..."
              value={productUniqueId}
              onChange={(e) => setProductUniqueId(e.target.value)}
            />

            <div className="flex justify-end space-x-2 pt-4 border-t border-border">
              <Button variant="close" size="sm" type="button" onClick={() => setDeliveryDialogItem(null)}>Cancel</Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Submitting..." : "Confirm Delivery"}
              </Button>
            </div>
          </form>
        </Dialog>
      )}
    </div>
  );
};
export default DeliveredItems;
