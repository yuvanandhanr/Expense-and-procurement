import React, { useState } from "react";
import { Building, Briefcase, FileText } from "lucide-react";
import { Dialog, StatusBadge, Button } from "../ui";
import { formatDate } from "../../utils/helpers";

interface ReimbursementDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  receiptDetails: any; // The detailed report data from /api/expenses/{id}
  isPendingForUser: boolean;
  onAction: (action: "approve" | "reject" | "return") => void;
  loading?: boolean;
}

export const ReimbursementDetailModal: React.FC<ReimbursementDetailModalProps> = ({
  isOpen,
  onClose,
  receiptDetails,
  isPendingForUser,
  onAction,
  loading = false,
}) => {
  const [previewReceipt, setPreviewReceipt] = useState<string | null>(null);

  if (!isOpen) return null;

  return (
    <>
    <Dialog 
      isOpen={isOpen} 
      onClose={onClose}
      title={receiptDetails?.title || receiptDetails?.purpose || "Reimbursement Details"}
      maxWidthClass="max-w-3xl"
    >
      <div className="space-y-6">
        {loading ? (
          <div className="p-12 flex items-center justify-center flex-col gap-4 text-muted-foreground">
             <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
             <p className="font-semibold text-sm">Loading reimbursement details...</p>
          </div>
        ) : receiptDetails ? (
          <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
              <div>
                <StatusBadge status={receiptDetails.status} />
                <span className="text-sm font-medium text-muted-foreground ml-3">Created: {formatDate(receiptDetails.created_at || receiptDetails.submission_date || receiptDetails.date)}</span>
              </div>
              <div className="text-right">
                <div className="text-4xl font-bold text-blue-600 tracking-tight">₹{Number(receiptDetails.total_amount || 0).toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
                <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mt-1">Verified Total</div>
              </div>
            </div>
            
            {/* Progress Timeline */}
            <div className="pt-8 pb-4 px-4 w-full">
              <div className="flex items-center justify-between relative max-w-lg mx-auto w-full">
                {(() => {
                  const roles = receiptDetails.employee?.roles?.map((r: any) => (r.role_name || "").toLowerCase()) || [];
                  const desig = (receiptDetails.requestor_designation || "").toLowerCase();
                  
                  const isRole = (role: string) => desig.includes(role) || roles.some((r: string) => r.includes(role));
                  
                  let steps = ["Draft", "Submitted", "Manager", "Finance", "Payment", "Approved"];
                  
                  if (isRole("ceo") || isRole("admin") || isRole("cfo") || isRole("finance manager")) {
                    steps = ["Draft", "Submitted", "CFO", "Payment", "Approved"];
                  } else if (isRole("manager")) {
                    steps = ["Draft", "Submitted", "Finance", "Payment", "Approved"];
                  }
                  
                  return steps.map((step, idx, arr) => {
                  let currentStepIdx = 1;
                  const s = (receiptDetails.status || "").toLowerCase();
                  const isRejectedOrReturned = s.includes("reject") || s.includes("return");

                  if (s.includes("draft")) currentStepIdx = steps.indexOf("Draft");
                  else if (s.includes("manager approval")) currentStepIdx = steps.indexOf("Manager");
                  else if (s.includes("finance manager approval") || s.includes("finance approval")) {
                    currentStepIdx = steps.indexOf("Finance");
                    if (currentStepIdx === -1) currentStepIdx = steps.indexOf("CFO");
                  }
                  else if (s.includes("cfo approval")) currentStepIdx = steps.indexOf("CFO");
                  else if (s.includes("payment")) currentStepIdx = steps.indexOf("Payment");
                  else if (s.includes("closed") || s.includes("paid") || s.includes("approved")) currentStepIdx = steps.indexOf("Approved");
                  
                  if (currentStepIdx === -1) {
                    if (isRejectedOrReturned) currentStepIdx = 1;
                  }
                  
                  // If rejected, highlight all steps from current onwards in red
                  const isError = isRejectedOrReturned && idx >= currentStepIdx;
                  const isActive = idx === currentStepIdx && !isRejectedOrReturned;
                  const isCompleted = idx <= currentStepIdx && !isError;
                  
                  // Connecting line logic
                  const lineCompleted = isCompleted && idx < currentStepIdx;
                  const lineError = isError;

                  return (
                    <React.Fragment key={idx}>
                      <div className="relative z-10 flex flex-col items-center gap-3 shrink-0">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-sm ${
                          isError 
                            ? "bg-red-500 text-white ring-4 ring-red-500/20" 
                            : isActive 
                              ? "bg-card text-blue-600 border-2 border-blue-600 ring-4 ring-blue-600/20 scale-110" 
                              : isCompleted 
                              ? "bg-blue-500 text-white shadow-md shadow-blue-500/20" 
                                : "bg-card text-muted-foreground border-2 border-muted"
                        }`}>
                          {idx + 1}
                        </div>
                        <span className={`absolute top-11 text-[9px] uppercase tracking-wider font-bold whitespace-nowrap ${isError ? "text-red-500" : isActive ? "text-blue-600" : isCompleted ? "text-blue-500" : "text-muted-foreground"}`}>{step}</span>
                      </div>
                      
                      {/* Connecting Line Segment */}
                      {idx < arr.length - 1 && (
                        <div className={`flex-1 h-[2px] mx-1 ${lineError ? 'bg-red-400' : lineCompleted ? 'bg-blue-400' : 'bg-slate-200'}`} />
                      )}
                    </React.Fragment>
                  );
                });
              })()}
              </div>
              <div className="h-6"></div> {/* Spacer for absolute text */}
            </div>

            {/* Details & OCR */}
            <div className="space-y-6 pt-4">
              <div className="pl-4 py-1 border-l-4 border-blue-500" style={{ boxShadow: '-6px 0px 8px -4px rgba(59,130,246,0.3)' }}>
                <p className="text-sm italic font-medium text-foreground">"{receiptDetails.justification}"</p>
              </div>

              <div className="flex gap-6 p-4 bg-card border border-border rounded-2xl text-sm font-semibold text-foreground shadow-sm">
                <div className="flex items-center gap-2.5">
                  <div className="bg-blue-100 p-1.5 rounded-lg text-blue-600">
                    <Building className="w-4 h-4" />
                  </div>
                  Dept: {receiptDetails.department_id || "N/A"}
                </div>
                <div className="flex items-center gap-2.5">
                  <div className="bg-blue-100 p-1.5 rounded-lg text-blue-600">
                    <Briefcase className="w-4 h-4" />
                  </div>
                  Proj: {receiptDetails.project_code || receiptDetails.project_id || "N/A"}
                </div>
              </div>

              {/* ACTION BUTTONS (Placed above attached receipts) */}
              {isPendingForUser && (
                 <div className="flex items-center gap-3 pt-2 pb-2 justify-start">
                    <Button variant="approve" onClick={() => onAction("approve")}>
                      {(receiptDetails.status === "Payment Requested" || receiptDetails.status === "Approved for Payment") ? "Authorize Payment" : "Approve"}
                    </Button>
                    {receiptDetails.status !== "Payment Requested" && receiptDetails.status !== "Approved for Payment" && (
                      <>
                        <Button variant="return" onClick={() => onAction("return")}>
                          Return for Correction
                        </Button>
                        <Button variant="reject" onClick={() => onAction("reject")}>
                          Reject
                        </Button>
                      </>
                    )}
                  </div>
              )}

              {receiptDetails.receipts && receiptDetails.receipts.length > 0 && (
                <div className="space-y-4 pt-2">
                  <h4 className="text-sm font-bold text-foreground flex items-center gap-2">
                    <span className="text-blue-500">📄</span> Attached Receipts ({receiptDetails.receipts.length})
                  </h4>
                  {receiptDetails.receipts.map((receipt: any, idx: number) => {
                    
                    const conf = receipt.ocr_confidence != null ? Number(receipt.ocr_confidence) : null;
                    
                    const extractedAmount = (receipt.ocr_amount && Number(receipt.ocr_amount) > 0) 
                      ? `₹${Number(receipt.ocr_amount).toFixed(2)}` 
                      : (receipt.total_amount && Number(receipt.total_amount) > 0) 
                        ? `₹${Number(receipt.total_amount).toFixed(2)}`
                        : "Not detected";
                    
                    const rawUrl = receipt.file_url || receipt.image_path;
                    let finalUrl = null;
                    if (rawUrl) {
                       if (rawUrl.startsWith('http') || rawUrl.startsWith('data:')) {
                          finalUrl = rawUrl;
                       } else {
                          const basePath = import.meta.env.VITE_API_URL || '/api/v1';
                          const cleanPath = rawUrl.startsWith('/uploads') ? rawUrl.replace('/uploads', '') : (rawUrl.startsWith('/') ? rawUrl : `/${rawUrl}`);
                          finalUrl = `${basePath}/uploads${cleanPath}`;
                       }
                    }
                    
                    return (
                      <div key={idx} className="flex gap-6 p-5 bg-card border border-border rounded-2xl items-start hover:shadow-md transition-shadow shadow-sm">
                        <div className="w-32 h-32 bg-card rounded-xl flex items-center justify-center shrink-0 border border-border/80 overflow-hidden p-1 shadow-sm">
                          {finalUrl ? (
                             <button 
                               onClick={() => setPreviewReceipt(finalUrl)} 
                               className="w-full h-full block bg-muted/20 cursor-pointer flex items-center justify-center relative group"
                             >
                               {finalUrl.toLowerCase().endsWith('.pdf') ? (
                                 <div className="flex flex-col items-center justify-center gap-2 text-red-500 group-hover:scale-105 transition-transform">
                                   <FileText className="w-12 h-12" />
                                   <span className="text-[10px] font-bold">PDF</span>
                                 </div>
                               ) : (
                                 <img 
                                   src={finalUrl} 
                                   alt="Receipt" 
                                   className="w-full h-full object-cover rounded-lg hover:opacity-80 transition-opacity" 
                                   onError={(e) => {
                                     (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM5NDkzYjgiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cmVjdCB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHg9IjMiIHk9IjMiIHJ4PSIyIiByeT0iMiIvPjxjaXJjbGUgY3g9IjkuIiBjeT0iOSIgcj0iMiIvPjxwYXRoIGQ9Im0yMSAxNS0zLjA4Ni0zLjA4NmEtMiAyIDAgMCAwLTIuODI4IDBsLTUuNzg2IDUuNzg2Ii8+PC9zdmc+'; // fallback icon
                                     (e.target as HTMLImageElement).className = "w-10 h-10 object-contain mx-auto mt-10 opacity-50";
                                   }}
                                 />
                               )}
                             </button>
                          ) : (
                             <span className="text-xs font-semibold text-muted-foreground flex flex-col items-center gap-2"><FileText className="w-8 h-8 text-muted-foreground/50" />No File</span>
                          )}
                        </div>
                        <div className="flex-1 text-xs space-y-2 pt-1">
                          <p className="font-bold text-base text-foreground">{receipt.merchant_name || "Unknown Merchant"}</p>
                          <p className="text-muted-foreground font-medium text-xs">Date: <span className="text-foreground">{formatDate(receipt.transaction_date || receipt.receipt_date)}</span> • Category: <span className="text-foreground">{receipt.category || "Uncategorized"}</span></p>
                          {conf !== null && conf > 0 ? (
                            <p className="text-emerald-600 font-semibold text-[11px]">OCR Confidence: {conf.toFixed(2)}%</p>
                          ) : (
                            <p className="text-muted-foreground font-semibold text-[11px]">OCR Confidence: Not available</p>
                          )}
                          <p className="text-muted-foreground text-xs mt-1">OCR Extracted Amount: <span className="font-bold text-foreground">{extractedAmount}</span></p>
                        </div>
                        <div className="text-right pt-1">
                          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1">Receipt Total</div>
                          <div className="font-bold text-xl text-foreground">₹{Number(receipt.verified_amount || receipt.total_amount || 0).toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-muted-foreground">Failed to load reimbursement details.</div>
        )}
      </div>
    </Dialog>

    {/* Receipt Preview Overlay */}
    {previewReceipt && (
      <div 
        className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" 
        onClick={() => setPreviewReceipt(null)}
      >
        <div className="relative max-w-4xl max-h-[95vh] bg-card p-2 rounded-xl shadow-2xl flex flex-col" onClick={e => e.stopPropagation()}>
           <button 
             onClick={() => setPreviewReceipt(null)} 
             className="absolute -top-4 -right-4 w-10 h-10 bg-card rounded-full flex items-center justify-center text-foreground font-bold shadow-md hover:bg-muted transition-colors z-10 text-xl"
           >
             ✕
           </button>
           <div className="flex-1 overflow-auto rounded-lg bg-muted/10 flex items-center justify-center p-4">
             {previewReceipt.toLowerCase().endsWith('.pdf') ? (
               <iframe src={previewReceipt} className="w-full h-[85vh] rounded-lg border-none" title="PDF Preview" />
             ) : (
               <img 
                 src={previewReceipt} 
                 className="max-w-full max-h-[90vh] object-contain rounded-lg shadow-sm" 
                 alt="Preview" 
                 onError={(e) => {
                   (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM5NDkzYjgiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cmVjdCB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHg9IjMiIHk9IjMiIHJ4PSIyIiByeT0iMiIvPjxjaXJjbGUgY3g9IjkuIiBjeT0iOSIgcj0iMiIvPjxwYXRoIGQ9Im0yMSAxNS0zLjA4Ni0zLjA4NmEtMiAyIDAgMCAwLTIuODI4IDBsLTUuNzg2IDUuNzg2Ii8+PC9zdmc+';
                   (e.target as HTMLImageElement).className = "max-w-xs max-h-xs object-contain mx-auto opacity-50";
                 }}
               />
             )}
           </div>
        </div>
      </div>
    )}
    </>
  );
};

