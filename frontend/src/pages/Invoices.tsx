import React, { useEffect, useState, useRef } from "react";
import { api } from "../services/api";
import { Invoice } from "../types";
import { useAuth } from "../hooks/useAuth";
import { Card, CardHeader, CardTitle, CardContent, Badge, Skeleton, Button, Dialog, Input } from "../components/ui";
import { formatDate, getErrorMessage } from "../utils/helpers";
import toast from "react-hot-toast";
import { FileText, Edit2, CheckCircle, XCircle } from "lucide-react";

export const Invoices: React.FC = () => {
  const { user } = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Modals state
  const [editingInvoice, setEditingInvoice] = useState<Invoice | null>(null);
  const [editCause, setEditCause] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const [viewingDoc, setViewingDoc] = useState<string | null>(null);
  
  // Upload modal state
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [serialNumber, setSerialNumber] = useState("");

  const isManager = user?.roles?.some(r => ["Manager", "Finance Manager", "CFO", "Admin"].includes(r.role_name)) || false;

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      const response = await api.get("/invoices");
      setInvoices(response.data);
    } catch (err) {
      console.error("Failed to load invoices:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, []);

  const handleFilesSelected = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFiles(event.target.files);
      setIsUploadOpen(true);
    }
  };

  const handleUploadSubmit = async () => {
    if (!selectedFiles || selectedFiles.length === 0) return;

    const formData = new FormData();
    Array.from(selectedFiles).forEach((file) => {
      formData.append("files", file);
    });
    
    if (serialNumber) {
      formData.append("asset_serial_number", serialNumber);
    }

    setUploading(true);
    try {
      await api.post("/invoices/upload-batch", formData);
      toast.success(`${selectedFiles.length} invoice(s) uploaded and processed successfully!`);
      setIsUploadOpen(false);
      setSelectedFiles(null);
      setSerialNumber("");
      fetchInvoices();
    } catch (err) {
      console.error("Failed to upload invoices:", err);
      toast.error(getErrorMessage(err, "Error uploading invoices. Make sure they are images."));
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleUpdateCause = async () => {
    if (!editingInvoice) return;
    setIsSubmitting(true);
    try {
      await api.patch(`/invoices/${editingInvoice.invoice_id}`, { cause: editCause });
      toast.success("Invoice description updated!");
      setEditingInvoice(null);
      fetchInvoices();
    } catch (err) {
      toast.error("Failed to update description.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApproveReject = async (invoiceId: number, action: "approve" | "reject") => {
    try {
      await api.post(`/invoices/${invoiceId}/${action}`);
      toast.success(`Invoice ${action}d successfully!`);
      fetchInvoices();
    } catch (err) {
      toast.error(`Failed to ${action} invoice.`);
    }
  };

  const handleViewBill = async (invoiceId: number) => {
    try {
      const response = await api.get(`/invoices/${invoiceId}/document`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      setViewingDoc(url);
    } catch (err) {
      toast.error("Failed to load document or document not found.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Vendor Invoices
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Review and manage incoming vendor billings.
          </p>
        </div>
        <div>
          <input 
            type="file" 
            accept="image/*" 
            multiple
            className="hidden" 
            ref={fileInputRef} 
            onChange={handleFilesSelected} 
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 text-sm font-semibold disabled:opacity-50"
          >
            {uploading ? "Processing OCR..." : "Upload Invoices"}
          </button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
            </div>
          ) : invoices.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              No invoices uploaded.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase">
                    <th className="p-4">Invoice Number</th>
                    <th className="p-4">Vendor Name</th>
                    <th className="p-4">Cause / Description</th>
                    <th className="p-4">Amount</th>
                    <th className="p-4">Invoice Date</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {invoices.map((inv: any) => (
                    <tr key={inv.invoice_id} className="hover:bg-accent/20 transition-colors">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{inv.invoice_number}</td>
                      <td className="p-4 font-semibold text-xs text-muted-foreground">{inv.vendor_name || "Unknown"}</td>
                      <td className="p-4 text-xs font-medium truncate max-w-[200px]" title={inv.cause}>{inv.cause || "N/A"}</td>
                      <td className="p-4 font-bold">${inv.grand_total?.toLocaleString() || inv.amount?.toLocaleString() || '0.00'}</td>
                      <td className="p-4 text-xs text-muted-foreground">{formatDate(inv.invoice_date)}</td>
                      <td className="p-4">
                        <Badge variant={inv.status === "Approved" ? "success" : inv.status === "Pending Approval" ? "warning" : inv.status === "Rejected" ? "error" : "neutral"}>
                          {inv.status}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center justify-end space-x-2">
                          <Button size="sm" variant="outline" onClick={() => handleViewBill(inv.invoice_id)} title="View Bill">
                            <FileText className="w-4 h-4 mr-1" /> View Bill
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={() => {
                              setEditingInvoice(inv);
                              setEditCause(inv.cause || "");
                            }}
                            title="Add/Edit Description"
                          >
                            <Edit2 className="w-4 h-4 mr-1" /> Add Desc
                          </Button>
                          {isManager && inv.status === "Pending Approval" && (
                            <>
                              <Button size="sm" variant="outline" className="text-emerald-500 hover:text-emerald-600 hover:bg-emerald-50" onClick={() => handleApproveReject(inv.invoice_id, "approve")} title="Approve">
                                <CheckCircle className="w-4 h-4 mr-1" /> Approve
                              </Button>
                              <Button size="sm" variant="outline" className="text-rose-500 hover:text-rose-600 hover:bg-rose-50" onClick={() => handleApproveReject(inv.invoice_id, "reject")} title="Reject">
                                <XCircle className="w-4 h-4 mr-1" /> Reject
                              </Button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Description Dialog */}
      {editingInvoice && (
        <Dialog isOpen={true} onClose={() => setEditingInvoice(null)} title="Edit Invoice Description">
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Description / Cause</label>
              <textarea
                value={editCause}
                onChange={(e) => setEditCause(e.target.value)}
                placeholder="Explain the reason for this expense..."
                className="w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring min-h-[100px]"
              />
            </div>
            <div className="flex justify-end space-x-2 pt-4">
              <Button variant="outline" onClick={() => setEditingInvoice(null)}>Cancel</Button>
              <Button onClick={handleUpdateCause} disabled={isSubmitting}>Save</Button>
            </div>
          </div>
        </Dialog>
      )}

      {/* View Document Dialog */}
      {viewingDoc && (
        <Dialog isOpen={true} onClose={() => {
          window.URL.revokeObjectURL(viewingDoc);
          setViewingDoc(null);
        }} title="Invoice Bill Document">
          <div className="flex items-center justify-center p-4 bg-muted/30 rounded-lg overflow-auto max-h-[70vh]">
            <img src={viewingDoc} alt="Invoice Document" className="max-w-full h-auto rounded shadow-sm border border-border" />
          </div>
          <div className="flex justify-end mt-4">
            <Button variant="outline" onClick={() => {
              window.URL.revokeObjectURL(viewingDoc);
              setViewingDoc(null);
            }}>Close</Button>
          </div>
        </Dialog>
      )}

      {/* Upload Invoice Dialog */}
      {isUploadOpen && (
        <Dialog isOpen={true} onClose={() => { setIsUploadOpen(false); setSelectedFiles(null); }} title="Upload Invoice Details">
          <div className="space-y-4">
            <div className="bg-muted/40 p-3 rounded-lg border border-border text-xs">
              <span className="block font-semibold text-muted-foreground uppercase">Selected Files</span>
              <span className="font-bold text-sm text-foreground/90">{selectedFiles ? selectedFiles.length : 0} file(s) selected</span>
            </div>
            
            <Input
              id="serial_number"
              type="text"
              label="Asset Serial Number / Unique ID (Optional)"
              placeholder="e.g. SN-12345678"
              value={serialNumber}
              onChange={(e) => setSerialNumber(e.target.value)}
            />
            <p className="text-[10px] text-muted-foreground">If this invoice is for an asset (e.g. IT Equipment, Hardware), enter the product serial number here to register it automatically upon approval.</p>

            <div className="flex justify-end space-x-2 pt-4 border-t border-border">
              <Button variant="outline" type="button" onClick={() => { setIsUploadOpen(false); setSelectedFiles(null); }}>
                Cancel
              </Button>
              <Button type="button" onClick={handleUploadSubmit} disabled={uploading}>
                {uploading ? "Uploading..." : "Submit Upload"}
              </Button>
            </div>
          </div>
        </Dialog>
      )}
    </div>
  );
};
export default Invoices;
