import re

with open('frontend/src/pages/Expenses.tsx', 'r') as f:
    content = f.read()

# 1. Add manager action state
state_code = """  // Manager Action Modal State
  const [managerAction, setManagerAction] = useState<{isOpen: boolean, action: 'return' | 'reject' | null, reportId: number | null}>({isOpen: false, action: null, reportId: null});
  const [managerComments, setManagerComments] = useState("");
  
  // Edit Details State
  const [isEditDetailsOpen, setIsEditDetailsOpen] = useState(false);
  const [editDetails, setEditDetails] = useState({ purpose: "", justification: "", department_id: "", cost_center_id: "", project_code: "" });

"""
content = content.replace("  const [editingReceiptId, setEditingReceiptId] = useState<number | null>(null);", state_code + "  const [editingReceiptId, setEditingReceiptId] = useState<number | null>(null);")

# 2. Add updateReportMutation
mutation_code = """  const updateReportMutation = useMutation({
    mutationFn: async ({ reportId, payload }: { reportId: number, payload: any }) => {
      const res = await api.put(`/expenses/${reportId}`, payload);
      return res.data;
    },
    onSuccess: () => {
      toast.success("Expense report updated");
      setIsEditDetailsOpen(false);
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to update report");
    }
  });

"""
content = content.replace("  const updateReceiptMutation = useMutation({", mutation_code + "  const updateReceiptMutation = useMutation({")


# 3. Change report.status === "Draft" to allow Returned for Correction
# There are multiple places.

content = content.replace('report.status === "Draft" ? "neutral" :', 'report.status === "Draft" || report.status === "Returned for Correction" ? "neutral" :')

content = content.replace('report.status === "Draft" && (', '(report.status === "Draft" || report.status === "Returned for Correction") && (')

# For the receipt edit condition:
content = content.replace('if(report.status === "Draft") handleEditAmount(receipt);', 'if(report.status === "Draft" || report.status === "Returned for Correction") handleEditAmount(receipt);')
content = content.replace('title={report.status === "Draft" ? "Click to correct amount" : ""}', 'title={report.status === "Draft" || report.status === "Returned for Correction" ? "Click to correct amount" : ""}')
content = content.replace('alert && report.status === "Draft" ?', 'alert && (report.status === "Draft" || report.status === "Returned for Correction") ?')

# 4. Manager action buttons
old_manager_buttons = """<Button onClick={() => managerActionMutation.mutate({ reportId: report.expense_report_id, action: 'return', comments: 'Please clarify' })} variant="outline" className="bg-white text-black">Return to Employee</Button>
                        <Button onClick={() => managerActionMutation.mutate({ reportId: report.expense_report_id, action: 'reject', comments: 'Rejected due to policy' })} variant="outline" className="bg-white text-red-600 hover:bg-red-50">Reject</Button>"""

new_manager_buttons = """<Button onClick={() => setManagerAction({isOpen: true, action: 'return', reportId: report.expense_report_id})} variant="outline" className="bg-white text-black">Return to Employee</Button>
                        <Button onClick={() => setManagerAction({isOpen: true, action: 'reject', reportId: report.expense_report_id})} variant="outline" className="bg-white text-red-600 hover:bg-red-50">Reject</Button>"""

content = content.replace(old_manager_buttons, new_manager_buttons)


# 5. Add "Edit Details" button next to "Review & Submit"
old_submit_btn = """<Button 
                          size="lg" 
                          className="w-full sm:w-auto font-semibold shadow-md"
                          onClick={() => setIsReviewOpen(true)}
                          disabled={submitReportMutation.isPending || !report.receipts?.length}
                        >
                          Review & Submit
                        </Button>"""

new_submit_btn = """<Button 
                          size="lg" 
                          variant="outline"
                          className="w-full sm:w-auto font-semibold"
                          onClick={() => {
                            setEditDetails({
                              purpose: report.purpose,
                              justification: report.justification || "",
                              department_id: report.department_id ? report.department_id.toString() : "",
                              cost_center_id: report.cost_center_id ? report.cost_center_id.toString() : "",
                              project_code: report.project_code || ""
                            });
                            setIsEditDetailsOpen(true);
                          }}
                        >
                          Edit Details
                        </Button>
                        <Button 
                          size="lg" 
                          className="w-full sm:w-auto font-semibold shadow-md"
                          onClick={() => setIsReviewOpen(true)}
                          disabled={submitReportMutation.isPending || !report.receipts?.length}
                        >
                          Review & Submit
                        </Button>"""

content = content.replace(old_submit_btn, new_submit_btn)

# 6. Add modals at the end before </div>\n  );\n};\n
modals_code = """
      {/* Manager Action Modal */}
      <Dialog isOpen={managerAction.isOpen} onClose={() => setManagerAction({isOpen: false, action: null, reportId: null})} title={managerAction.action === 'return' ? "Return to Employee" : "Reject Expense Claim"}>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">Please provide a justification for this action. This will be visible to the employee.</p>
          <textarea
            className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background focus:ring-2 focus:ring-primary focus:border-transparent"
            rows={4}
            placeholder="Enter your justification..."
            value={managerComments}
            onChange={e => setManagerComments(e.target.value)}
          />
          <div className="flex justify-end gap-2 pt-4 border-t border-border">
            <Button variant="ghost" onClick={() => setManagerAction({isOpen: false, action: null, reportId: null})}>Cancel</Button>
            <Button 
              disabled={!managerComments.trim() || managerActionMutation.isPending}
              onClick={() => {
                if(managerAction.reportId && managerAction.action) {
                  managerActionMutation.mutate({ reportId: managerAction.reportId, action: managerAction.action, comments: managerAction.comments });
                  setManagerAction({isOpen: false, action: null, reportId: null});
                  setManagerComments("");
                }
              }}
              className={managerAction.action === 'reject' ? "bg-red-600 hover:bg-red-700 text-white" : ""}
            >
              {managerAction.action === 'return' ? "Return" : "Reject"}
            </Button>
          </div>
        </div>
      </Dialog>
      
      {/* Edit Details Modal */}
      <Dialog isOpen={isEditDetailsOpen} onClose={() => setIsEditDetailsOpen(false)} title="Edit Report Details">
        <form onSubmit={(e) => {
          e.preventDefault();
          if (selectedReportId) {
            updateReportMutation.mutate({ reportId: selectedReportId, payload: editDetails });
          }
        }} className="space-y-4">
          <Input 
            label="Business Purpose *" 
            value={editDetails.purpose}
            onChange={e => setEditDetails({...editDetails, purpose: e.target.value})}
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Select 
              label="Department"
              value={editDetails.department_id}
              onChange={e => setEditDetails({...editDetails, department_id: e.target.value})}
              options={[
                { label: "None", value: "" },
                ...departments.map((d: any) => ({ label: d.department_name, value: d.department_id.toString() }))
              ]}
            />
            <Select 
              label="Cost Center"
              value={editDetails.cost_center_id}
              onChange={e => setEditDetails({...editDetails, cost_center_id: e.target.value})}
              options={[
                { label: "None", value: "" },
                ...costCenters.map((cc: any) => ({ label: cc.cost_center_name, value: cc.cost_center_id.toString() }))
              ]}
            />
          </div>
          <Input 
            label="Project Code" 
            value={editDetails.project_code}
            onChange={e => setEditDetails({...editDetails, project_code: e.target.value})}
          />
          <div>
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
              Description / Justification <span className="text-red-500">*</span>
            </label>
            <textarea
              className="w-full px-3 py-2 text-sm rounded-lg bg-background border border-border focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all duration-200"
              rows={3}
              value={editDetails.justification}
              onChange={e => setEditDetails({...editDetails, justification: e.target.value})}
              required
            ></textarea>
          </div>
          <div className="pt-4 flex justify-end gap-2 border-t border-border">
            <Button type="button" variant="ghost" onClick={() => setIsEditDetailsOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={updateReportMutation.isPending || !editDetails.purpose.trim() || !editDetails.justification.trim()}>Save Changes</Button>
          </div>
        </form>
      </Dialog>
"""

content = content.replace("    </div>\n  );\n};\n\nexport default Expenses;", modals_code + "    </div>\n  );\n};\n\nexport default Expenses;")


with open('frontend/src/pages/Expenses.tsx', 'w') as f:
    f.write(content)

print("Done FE Expenses")
