import React from "react";
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
  if (!isOpen) return null;

  return (
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
                <div className="text-4xl font-bold text-violet-600 tracking-tight">${Number(receiptDetails.total_amount || 0).toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
                <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mt-1">Verified Total</div>
              </div>
            </div>
            
            {/* Progress Timeline */}
            <div className="py-8 px-4 w-full">
              <div className="flex items-center justify-between relative max-w-lg mx-auto">
                {/* Base Line */}
                <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-[2px] bg-muted z-0" />
                
                {["Draft", "Submitted", "Manager", "Finance", "Payment", "Closed"].map((step, idx) => {
                  let currentStepIdx = 1;
                  const s = (receiptDetails.status || "").toLowerCase();
                  const isRejectedOrReturned = s.includes("reject") || s.includes("return");

                  if (s.includes("draft")) currentStepIdx = 0;
                  else if (s.includes("manager")) currentStepIdx = 2;
                  else if (s.includes("finance")) currentStepIdx = 3;
                  else if (s.includes("payment")) currentStepIdx = 4;
                  else if (s.includes("closed") || s.includes("paid") || s.includes("approved")) currentStepIdx = 5;
                  
                  // If rejected, highlight all steps from current onwards in red
                  const isError = isRejectedOrReturned && idx >= currentStepIdx;
                  const isActive = idx === currentStepIdx && !isRejectedOrReturned;
                  const isCompleted = idx <= currentStepIdx && !isError;
                  
                  // Connecting line color
                  const lineActive = isCompleted && idx > 0;
                  const lineError = isError && idx > 0;

                  return (
                    <div key={idx} className="relative z-10 flex flex-col items-center gap-3">
                      {/* Connecting Line Segment (left of circle) */}
                      {idx > 0 && (
                        <div className={`absolute right-full top-4 -translate-y-1/2 h-[2px] w-[calc(100vw/6)] sm:w-24 ${lineError ? 'bg-red-400' : lineActive ? 'bg-violet-200' : 'bg-transparent'}`} style={{ zIndex: -1 }} />
                      )}

                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-sm ${
                        isError 
                          ? "bg-red-500 text-white ring-4 ring-red-500/20" 
                          : isActive 
                            ? "bg-blue-600 text-white ring-4 ring-blue-600/20 scale-110" 
                            : isCompleted 
                              ? "bg-violet-100 text-violet-700" 
                              : "bg-white text-muted-foreground border-2 border-muted"
                      }`}>
                        {idx + 1}
                      </div>
                      <span className={`text-[9px] uppercase tracking-wider font-bold ${isError ? "text-red-500" : isActive ? "text-blue-600" : isCompleted ? "text-violet-700" : "text-muted-foreground"}`}>{step}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Details & OCR */}
            <div className="space-y-6 pt-4">
              <div className="pl-4 border-l-2 border-violet-400">
                <p className="text-sm italic font-medium text-foreground">"{receiptDetails.justification}"</p>
              </div>

              <div className="flex gap-6 p-4 bg-white border border-border rounded-2xl text-sm font-semibold text-muted-foreground shadow-sm">
                <div className="flex items-center gap-2"><span className="text-violet-500 bg-violet-500/10 p-1.5 rounded-lg">🏢</span> Dept: {receiptDetails.department_id || "N/A"}</div>
                <div className="flex items-center gap-2"><span className="text-violet-500 bg-violet-500/10 p-1.5 rounded-lg">📁</span> Proj: {receiptDetails.project_code || receiptDetails.project_id || "N/A"}</div>
              </div>

              {/* ACTION BUTTONS (Placed above attached receipts) */}
              {isPendingForUser && (
                 <div className="flex items-center gap-3 pt-2 pb-2">
                   <Button 
                     variant="outline" 
                     className="border-green-600 text-green-700 bg-green-50 hover:bg-green-100 hover:text-green-800 hover:border-green-700 shadow-sm transition-colors" 
                     onClick={() => onAction("approve")}
                   >
                     Approve
                   </Button>
                   <Button 
                     variant="outline"
                     className="border-yellow-500 text-yellow-700 bg-yellow-50 hover:bg-yellow-100 hover:text-yellow-800 hover:border-yellow-600 shadow-sm transition-colors"
                     onClick={() => onAction("return")}
                   >
                     Return for Correction
                   </Button>
                   <Button 
                     variant="danger" 
                     className="shadow-sm transition-colors"
                     onClick={() => onAction("reject")}
                   >
                     Reject
                   </Button>
                 </div>
              )}

              {receiptDetails.receipts && receiptDetails.receipts.length > 0 && (
                <div className="space-y-4 pt-2">
                  <h4 className="text-sm font-bold text-foreground flex items-center gap-2">
                    <span className="text-blue-500">📄</span> Attached Receipts ({receiptDetails.receipts.length})
                  </h4>
                  {receiptDetails.receipts.map((receipt: any, idx: number) => {
                    
                    // Normalize OCR Confidence to 0-100%
                    let conf = receipt.ocr_confidence || 0;
                    if (conf <= 1 && conf > 0) conf = conf * 100;
                    conf = Math.min(100, Math.max(0, conf));
                    
                    const extractedAmount = (receipt.ocr_amount && Number(receipt.ocr_amount) > 0) 
                      ? `$${Number(receipt.ocr_amount).toFixed(2)}` 
                      : (receipt.total_amount && Number(receipt.total_amount) > 0) 
                        ? `$${Number(receipt.total_amount).toFixed(2)}`
                        : "Not detected";
                    
                    return (
                      <div key={idx} className="flex gap-6 p-5 bg-white border border-border rounded-2xl items-start hover:shadow-md transition-shadow shadow-sm">
                        <div className="w-32 h-32 bg-white rounded-xl flex items-center justify-center shrink-0 border border-border/80 overflow-hidden p-1 shadow-sm">
                          {receipt.file_url ? (
                             <a href={receipt.file_url} target="_blank" rel="noopener noreferrer" className="w-full h-full block">
                               <img src={receipt.file_url} alt="Receipt" className="w-full h-full object-cover rounded-lg hover:opacity-80 transition-opacity" />
                             </a>
                          ) : (
                             <span className="text-xs font-semibold text-muted-foreground flex flex-col items-center gap-2"><span className="text-2xl text-blue-400">🧾</span>No File</span>
                          )}
                        </div>
                        <div className="flex-1 text-xs space-y-2 pt-1">
                          <p className="font-bold text-base text-foreground">{receipt.merchant_name || "Unknown Merchant"}</p>
                          <p className="text-muted-foreground font-medium text-xs">Date: <span className="text-foreground">{formatDate(receipt.transaction_date || receipt.receipt_date)}</span> • Category: <span className="text-foreground">{receipt.category || "Uncategorized"}</span></p>
                          {conf > 0 && <p className="text-emerald-600 font-semibold text-[11px]">OCR Confidence: {conf.toFixed(2)}%</p>}
                          <p className="text-muted-foreground text-xs mt-1">OCR Extracted Amount: <span className="font-bold text-foreground">{extractedAmount}</span></p>
                        </div>
                        <div className="text-right pt-1">
                          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1">Receipt Total</div>
                          <div className="font-bold text-xl text-foreground">${Number(receipt.verified_amount || receipt.total_amount || 0).toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
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
        
        {/* Footer */}
        <div className="flex items-center pt-4 mt-4 bg-background">
          <Button variant="outline" onClick={onClose} className="border-none shadow-none text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-colors px-2">Close</Button>
        </div>
      </div>
    </Dialog>
  );
};
