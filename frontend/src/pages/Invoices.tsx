import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { Invoice } from "../types";
import { useAuth } from "../hooks/useAuth";
import { Card, CardHeader, CardTitle, CardContent, Badge, StatusBadge, Skeleton, Button, Dialog, EmptyState } from "../components/ui";
import { formatDate } from "../utils/helpers";
import toast from "react-hot-toast";
import { FileText, CheckCircle, XCircle, AlertTriangle, Upload, Eye, Check, X } from "lucide-react";

export const Invoices: React.FC = () => {
  const { user, hasRole } = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  
  // 3-Way Match Review State
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Upload State
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [availablePOs, setAvailablePOs] = useState<any[]>([]);
  const [selectedPO, setSelectedPO] = useState<string>("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const isManager = user?.roles?.some(r => ["Manager", "Finance Manager", "CFO", "Admin"].includes(r.role_name)) || false;
  const isVendor = user?.roles?.some(r => ["Vendor", "Vendor Portal"].includes(r.role_name)) || false;
  const isFinance = user?.roles?.some(r => ["Finance", "Finance Manager", "CFO", "Admin"].includes(r.role_name)) || false;

  const isEmployeeOnly = user?.roles?.some(r => r.role_name === "Employee") && !isManager && !isFinance && !isVendor;

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

  const handleApproveReject = async (invoiceId: number, action: "approve" | "reject") => {
    setIsSubmitting(true);
    try {
      await api.post(`/invoices/${invoiceId}/${action}`);
      toast.success(`Invoice ${action}d successfully!`);
      setSelectedInvoice(null);
      fetchInvoices();
    } catch (err) {
      toast.error(`Failed to ${action} invoice.`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenUploadModal = async () => {
    try {
      const res = await api.get("/purchase-orders");
      setAvailablePOs(res.data);
      setIsUploadModalOpen(true);
    } catch (err) {
      toast.error("Failed to load purchase orders.");
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPO || !uploadFile) {
      toast.error("Please select a PO and choose a file.");
      return;
    }

    const formData = new FormData();
    formData.append("po_id", selectedPO);
    formData.append("file", uploadFile);

    setIsSubmitting(true);
    try {
      await api.post("/invoices/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      toast.success("Invoice uploaded and 3-way matching triggered!");
      setIsUploadModalOpen(false);
      setSelectedPO("");
      setUploadFile(null);
      fetchInvoices();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to upload invoice.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isEmployeeOnly) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <EmptyState 
          icon={<XCircle className="w-16 h-16 text-destructive/50" />} 
          title="Access Denied" 
          description="Vendor Invoices are restricted to Finance and Vendor operations." 
        />
      </div>
    );
  }

  // Mock details for the 3-Way match layout based on the invoice
  const generateMatchDetails = (invoice: Invoice) => {
    const isDiscrepancy = invoice.matching_status === "Discrepancy";
    // If discrepancy, make PO amount higher or GRN quantity lower to simulate it
    const poAmount = isDiscrepancy ? invoice.amount + 500 : invoice.amount;
    const grnReceived = isDiscrepancy ? "Partial (Short Shipment)" : "Full";
    
    return {
      po: { number: invoice.po_id ? `PO-${invoice.po_id}` : 'Unlinked', amount: poAmount },
      grn: { number: invoice.po_id ? `GRN-${invoice.po_id}` : 'Unlinked', status: invoice.po_id ? grnReceived : 'N/A' },
      inv: { number: invoice.invoice_number, grand_total: invoice.grand_total }
    };
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Vendor Invoices (3-Way Match)</h1>
          <p className="text-xs text-muted-foreground mt-1">Review vendor billings against POs and GRNs.</p>
        </div>
        <div>
          {(hasRole("Admin") || hasRole("Vendor") || hasRole("Vendor Portal")) && (
            <Button onClick={handleOpenUploadModal} className="gap-1.5 shadow-apple-glow">
              <Upload className="w-4 h-4" /> Upload Invoice
            </Button>
          )}
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full rounded-lg" />
              <Skeleton className="h-8 w-full rounded-lg" />
            </div>
          ) : invoices.length === 0 ? (
            <EmptyState title="No invoices found." description="Upload or sync invoices to see them here." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/30 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                    <th className="p-4 whitespace-nowrap">Invoice #</th>
                    <th className="p-4 whitespace-nowrap">Vendor</th>
                    <th className="p-4 whitespace-nowrap">Date</th>
                    <th className="p-4 whitespace-nowrap">Amount</th>
                    <th className="p-4 whitespace-nowrap">Status</th>
                    <th className="p-4 whitespace-nowrap">Match Status</th>
                    <th className="p-4 text-right whitespace-nowrap">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-sm">
                  {invoices.map((inv) => (
                    <tr key={inv.invoice_id} className="hover:bg-accent/10 transition-colors">
                      <td className="p-4 font-semibold text-primary whitespace-nowrap">{inv.invoice_number}</td>
                      <td className="p-4 whitespace-nowrap">{inv.vendor_name || `Vendor #${inv.vendor_id}`}</td>
                      <td className="p-4 text-muted-foreground whitespace-nowrap">{formatDate(inv.invoice_date)}</td>
                      <td className="p-4 font-mono font-semibold whitespace-nowrap">${Number(inv.grand_total || 0).toLocaleString('en-US')}</td>
                      <td className="p-4 whitespace-nowrap">
                        <StatusBadge status={inv.status} />
                      </td>
                      <td className="p-4 whitespace-nowrap">
                        <StatusBadge status={inv.matching_status} />
                      </td>
                      <td className="p-4 text-right whitespace-nowrap">
                        <Button 
                          size="sm" 
                          variant="primary" 
                          onClick={() => setSelectedInvoice(inv)}
                          className="gap-1.5 shadow-apple-sm"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Review 3-Way Match</span>
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

      {/* Upload Invoice Dialog */}
      <Dialog
        isOpen={isUploadModalOpen}
        onClose={() => !isSubmitting && setIsUploadModalOpen(false)}
        title="Upload Invoice"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Link to Purchase Order (Optional)</label>
            <select
              className="w-full bg-background border border-input rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              value={selectedPO}
              onChange={(e) => setSelectedPO(e.target.value)}
              disabled={isSubmitting}
            >
              <option value="">-- No PO Linked --</option>
              {availablePOs.map((po) => (
                <option key={po.po_id} value={po.po_id}>
                  {po.po_number} - ${Number(po.total_amount).toLocaleString()}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Invoice Document</label>
            <input
              type="file"
              accept="image/*,.pdf"
              className="w-full bg-background border border-input rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) setUploadFile(file);
              }}
              disabled={isSubmitting}
            />
          </div>

          <div className="flex justify-end space-x-3 pt-3 mt-2 border-t border-border">
            <Button variant="close" onClick={() => setIsUploadModalOpen(false)} disabled={isSubmitting}>Cancel</Button>
            <Button variant="primary" onClick={handleUploadSubmit} disabled={isSubmitting || !uploadFile}>
              {isSubmitting ? "Uploading..." : "Submit Invoice"}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* 3-Way Match Review Dialog */}
      <Dialog
        isOpen={!!selectedInvoice}
        onClose={() => !isSubmitting && setSelectedInvoice(null)}
        title="3-Way Match Review"
      >
        {selectedInvoice && (
          <div className="space-y-6">
            <div className="grid grid-cols-3 gap-4">
              {/* Purchase Order Column */}
              <div className="bg-card-2 border border-border rounded-lg p-4 space-y-3">
                <div className="flex items-center space-x-2 text-muted-foreground border-b border-border pb-2">
                  <FileText className="w-4 h-4" />
                  <span className="font-bold text-xs uppercase tracking-wider">Purchase Order</span>
                </div>
                <div className="space-y-1 text-sm">
                  <p><span className="text-muted-foreground">PO Number:</span> {generateMatchDetails(selectedInvoice).po.number}</p>
                  <p><span className="text-muted-foreground">Amount:</span> <span className="font-mono font-semibold">${generateMatchDetails(selectedInvoice).po.amount.toLocaleString()}</span></p>
                </div>
              </div>

              {/* Goods Receipt Column */}
              <div className="bg-card-2 border border-border rounded-lg p-4 space-y-3">
                <div className="flex items-center space-x-2 text-muted-foreground border-b border-border pb-2">
                  <CheckCircle className="w-4 h-4" />
                  <span className="font-bold text-xs uppercase tracking-wider">Goods Receipt</span>
                </div>
                <div className="space-y-1 text-sm">
                  <p><span className="text-muted-foreground">GRN Number:</span> {generateMatchDetails(selectedInvoice).grn.number}</p>
                  <p>
                    <span className="text-muted-foreground">Status:</span> 
                    <span className={`ml-1 font-semibold ${generateMatchDetails(selectedInvoice).grn.status.includes("Short") ? "text-destructive" : "text-lime"}`}>
                      {generateMatchDetails(selectedInvoice).grn.status}
                    </span>
                  </p>
                </div>
              </div>

              {/* Vendor Invoice Column */}
              <div className={`bg-card-2 border rounded-lg p-4 space-y-3 ${selectedInvoice.matching_status === 'Discrepancy' ? 'border-destructive/50 bg-destructive/5' : 'border-border'}`}>
                <div className="flex items-center space-x-2 text-muted-foreground border-b border-border pb-2">
                  <FileText className="w-4 h-4" />
                  <span className="font-bold text-xs uppercase tracking-wider">Vendor Invoice</span>
                </div>
                <div className="space-y-1 text-sm">
                  <p><span className="text-muted-foreground">Inv Number:</span> {generateMatchDetails(selectedInvoice).inv.number}</p>
                  <p>
                    <span className="text-muted-foreground">Amount:</span> 
                    <span className={`ml-1 font-mono font-semibold ${selectedInvoice.matching_status === 'Discrepancy' ? 'text-destructive' : ''}`}>
                      ${Number(generateMatchDetails(selectedInvoice).inv.grand_total || 0).toLocaleString('en-US')}
                    </span>
                  </p>
                </div>
              </div>
            </div>

            {selectedInvoice.matching_status === "Discrepancy" && (
              <div className="flex items-start space-x-3 bg-destructive/10 text-destructive p-4 rounded-lg border border-destructive/20">
                <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-sm">Discrepancy Detected</h4>
                  <p className="text-xs mt-1">
                    The billed amount exceeds the PO limit or the GRN indicates a short shipment. Please review carefully before approving.
                  </p>
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-3 pt-3 mt-2 border-t border-border">
              <Button variant="close" onClick={() => setSelectedInvoice(null)} disabled={isSubmitting}>Cancel</Button>
              <Button 
                variant="danger" 
                onClick={() => handleApproveReject(selectedInvoice.invoice_id, "reject")}
                disabled={isSubmitting}
                className="gap-1.5 font-bold"
              >
                <X className="w-4 h-4" /> Reject Invoice
              </Button>
              <Button 
                variant="success" 
                onClick={() => handleApproveReject(selectedInvoice.invoice_id, "approve")}
                disabled={isSubmitting}
                className="gap-1.5 font-bold shadow-apple-sm"
              >
                <Check className="w-4 h-4" /> Approve & Authorize
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
};

export default Invoices;
