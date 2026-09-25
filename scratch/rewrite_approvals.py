with open("/Users/a.chaitnasree/Expense-and-procurement/frontend/src/pages/Approvals.tsx", "r") as f:
    content = f.read()

# Replace physicalInspectionDone with specific ones
new_state = """
  const [managerAssessment, setManagerAssessment] = useState("");
  const [managerComments, setManagerComments] = useState("");
  const [adminResolution, setAdminResolution] = useState("");
  const [adminComments, setAdminComments] = useState("");
"""
content = content.replace('const [physicalInspectionDone, setPhysicalInspectionDone] = useState(false);', new_state)

new_action = """
      if (selectedWorkflow.entity_type === "ExpenseReport") {
        endpoint = `/expenses/${selectedWorkflow.entity_id}/${actionType}`;
      } else if (selectedWorkflow.entity_type === "VendorInvoice") {
        endpoint = `/invoices/${selectedWorkflow.entity_id}/${actionType}`;
      } else if (selectedWorkflow.entity_type === "AssetIncident") {
        endpoint = `/asset-incidents/${selectedWorkflow.entity_id}/action`;
        let actStr = "Approve";
        if (actionType === "reject") actStr = "Reject";
        else if (actionType === "return") actStr = "Return for Correction";
        else if (actionType === "complete_procurement") actStr = "Complete Procurement Replacement";
        else if (actionType === "complete_repair") actStr = "Complete Repair";
        else if (actionType === "assign_replacement") actStr = "Assign Replacement";
        
        payload = { 
            action: actStr, 
            resolution: comment,
            manager_inspection_assessment: managerAssessment,
            manager_inspection_comments: managerComments,
            admin_inspection_resolution: adminResolution,
            admin_comments: adminComments
        };
      } else {
        endpoint = `/pr/${selectedWorkflow.entity_id}/${actionType}`;
      }
"""
import re
content = re.sub(r'      if \(selectedWorkflow\.entity_type === "ExpenseReport"\).*?endpoint = `/pr/\${selectedWorkflow.entity_id}/\${actionType}`;\n      }', new_action, content, flags=re.DOTALL)

clear_state = """
      setManagerAssessment("");
      setManagerComments("");
      setAdminResolution("");
      setAdminComments("");
"""
content = content.replace('setPhysicalInspectionDone(false);', clear_state)

# Replace buttons in CardContent
new_buttons = """
                {((["Pending", "Under Review", "Submitted"].includes(wf.status)) || (wf.status.toLowerCase().includes("pending") && !["Approved", "Manager Approved", "Admin Approved", "Waiting for Procurement", "Replacement Assigned"].includes(wf.status))) && (
                  <div className="flex space-x-2 pt-4 border-t border-border">
                    <Button 
                      variant="success" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("approve"); }}
                    >
                      <Check className="w-4 h-4" />
                      <span>Approve</span>
                    </Button>
                    <Button 
                      variant="warning" 
                      className="flex-1 font-bold shadow-apple-sm border border-yellow-500 bg-yellow-500/10 text-yellow-600 hover:bg-yellow-500 hover:text-white transition-colors"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("return"); }}
                    >
                      <span>Return</span>
                    </Button>
                    <Button 
                      variant="danger" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("reject"); }}
                    >
                      <XIcon className="w-4 h-4" />
                      <span>Reject</span>
                    </Button>
                  </div>
                )}
                
                {wf.status === "Manager Approved" && wf.entity_type === "AssetIncident" && (
                  <div className="flex space-x-2 pt-4 border-t border-border">
                    <Button 
                      variant="success" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("approve"); }}
                    >
                      <span>Review & Resolve</span>
                    </Button>
                    <Button 
                      variant="warning" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("return"); }}
                    >
                      <span>Return</span>
                    </Button>
                    <Button 
                      variant="danger" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("reject"); }}
                    >
                      <span>Reject</span>
                    </Button>
                  </div>
                )}

                {wf.status === "Admin Approved" && wf.entity_type === "AssetIncident" && (
                  <div className="flex space-x-2 pt-4 border-t border-border">
                    <Button 
                      variant="success" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("assign_replacement"); }}
                    >
                      <span>Assign Replacement</span>
                    </Button>
                  </div>
                )}
                
                {wf.status === "Repair" && wf.entity_type === "AssetIncident" && (
                  <div className="flex space-x-2 pt-4 border-t border-border">
                    <Button 
                      variant="success" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("complete_repair"); }}
                    >
                      <span>Complete Repair</span>
                    </Button>
                  </div>
                )}

                {wf.status === "Waiting for Procurement" && wf.entity_type === "AssetIncident" && (
                  <div className="flex space-x-2 pt-4 border-t border-border">
                    <Button 
                      variant="success" 
                      className="flex-1 font-bold shadow-apple-sm"
                      onClick={() => { setSelectedWorkflow(wf); setActionType("complete_procurement"); }}
                    >
                      <span>Complete Procurement Replacement</span>
                    </Button>
                  </div>
                )}
"""
content = re.sub(r'\{(\(\[\"Pending\", \"Under Review\", \"Reported\"\].*?) \)\}', new_buttons, content, flags=re.DOTALL)


# Modals
new_dialog_content = """
          {selectedWorkflow?.status === "Submitted" && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && (
            <div className="space-y-4 p-3 bg-muted/30 rounded-xl border border-border/50">
               <div>
                 <label className="block text-sm font-medium mb-1">Inspection / Resolution Assessment <span className="text-red-500">*</span></label>
                 <select className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" value={managerAssessment} onChange={(e) => setManagerAssessment(e.target.value)}>
                   <option value="">Select an option</option>
                   <option value="No Action Required">No Action Required</option>
                   <option value="Repair Required">Repair Required</option>
                   <option value="Replacement Required">Replacement Required</option>
                   <option value="Further Inspection Required">Further Inspection Required</option>
                 </select>
               </div>
               <div>
                 <label className="block text-sm font-medium mb-1">Manager Inspection Comments</label>
                 <Input value={managerComments} onChange={(e) => setManagerComments(e.target.value)} placeholder="Notes..." />
               </div>
            </div>
          )}
          {selectedWorkflow?.status === "Manager Approved" && actionType === "approve" && selectedWorkflow?.entity_type === "AssetIncident" && (
            <div className="space-y-4 p-3 bg-muted/30 rounded-xl border border-border/50">
               <div>
                 <label className="block text-sm font-medium mb-1">Admin Inspection / Resolution <span className="text-red-500">*</span></label>
                 <select className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" value={adminResolution} onChange={(e) => setAdminResolution(e.target.value)}>
                   <option value="">Select an option</option>
                   <option value="Repair Required">Repair Required</option>
                   <option value="Replacement Required">Replacement Required</option>
                   <option value="Further Inspection Required">Further Inspection Required</option>
                   <option value="No Replacement Required">No Replacement Required</option>
                 </select>
               </div>
               <div>
                 <label className="block text-sm font-medium mb-1">Admin Comments / Resolution Notes</label>
                 <Input value={adminComments} onChange={(e) => setAdminComments(e.target.value)} placeholder="Notes..." />
               </div>
            </div>
          )}
          {(actionType === 'reject' || actionType === 'return' || selectedWorkflow?.entity_type === 'AssetIncident') && (
            <div>
              <label className="block text-sm font-medium mb-1">
                Comments {(actionType === 'reject' || actionType === 'return') && <span className="text-red-500">*</span>}
              </label>
              <Input 
                value={comment} 
                onChange={(e) => setComment(e.target.value)} 
                placeholder={(actionType === 'reject' || actionType === 'return') ? "Resolution / Reason (required)..." : "Add a note..."} 
              />
            </div>
          )}
"""

content = re.sub(r'\{selectedWorkflow\?\.status === \"Reported\".*?<\/div>\n          \)\}', '', content, flags=re.DOTALL)
content = re.sub(r'<div>\n\s*<label className=\"block text-sm font-medium mb-1\">\n\s*Comments.*?\n\s*<\/label>.*?<\/div>', new_dialog_content, content, flags=re.DOTALL)

with open("/Users/a.chaitnasree/Expense-and-procurement/frontend/src/pages/Approvals.tsx", "w") as f:
    f.write(content)
