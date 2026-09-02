import re

with open('frontend/src/pages/Expenses.tsx', 'r') as f:
    content = f.read()

# 1. Error handling in updateReportMutation
old_error = """    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to update report");
    }"""
new_error = """    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : "Failed to update report. Please check your inputs.");
    }"""
content = content.replace(old_error, new_error)

# 2. Add isOwner check 
old_isowner = """  const isFinance = hasRole("Finance") || hasRole("Finance Manager");
  const isManagerOrAdmin = hasRole("Admin") || isManager || isFinance || hasRole("CFO");"""

new_isowner = """  const isFinance = hasRole("Finance") || hasRole("Finance Manager");
  const isManagerOrAdmin = hasRole("Admin") || isManager || isFinance || hasRole("CFO");
  const isOwner = (report: any) => user?.user_id === report.employee_id;"""
content = content.replace(old_isowner, new_isowner)

# 3. Edit Details Form payload building
old_form = """        <form onSubmit={(e) => {
          e.preventDefault();
          if (selectedReportId) {
            updateReportMutation.mutate({ reportId: selectedReportId, payload: editDetails });
          }
        }} className="space-y-4">"""
new_form = """        <form onSubmit={(e) => {
          e.preventDefault();
          if (selectedReportId) {
            const payload: any = { 
              purpose: editDetails.purpose,
              justification: editDetails.justification,
              project_code: editDetails.project_code || null
            };
            if (editDetails.department_id) payload.department_id = parseInt(editDetails.department_id);
            else payload.department_id = null;
            if (editDetails.cost_center_id) payload.cost_center_id = parseInt(editDetails.cost_center_id);
            else payload.cost_center_id = null;
            
            updateReportMutation.mutate({ reportId: selectedReportId, payload });
          }
        }} className="space-y-4">"""
content = content.replace(old_form, new_form)

# 4. Hide Delete Button for Returned Claims (and receipt delete)
# Report delete:
old_report_del = """                        {(report.status === "Draft" || report.status === "Returned for Correction") && (
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-6 w-6 text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded shrink-0"
                            title="Delete Draft Report"
                            onClick={(e) => {"""
new_report_del = """                        {report.status === "Draft" && (
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-6 w-6 text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded shrink-0"
                            title="Delete Draft Report"
                            onClick={(e) => {"""
content = content.replace(old_report_del, new_report_del)

# Receipt delete
old_receipt_del = """                                  {(report.status === "Draft" || report.status === "Returned for Correction") && (
                                    <Button
                                      size="icon"
                                      variant="ghost"
                                      className="h-9 w-9 text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded"
                                      title="Delete Receipt / OCR"
                                      onClick={() => {"""
new_receipt_del = """                                  {report.status === "Draft" && (
                                    <Button
                                      size="icon"
                                      variant="ghost"
                                      className="h-9 w-9 text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded"
                                      title="Delete Receipt / OCR"
                                      onClick={() => {"""
content = content.replace(old_receipt_del, new_receipt_del)


# 5. Add "Corrected Claim" logic
# Badge color
old_badge = 'report.status.includes("Pending") ? "warning" : "error"'
new_badge = 'report.status.includes("Pending") || report.status === "Corrected Claim" ? "warning" : "error"'
content = content.replace(old_badge, new_badge)

# Timeline array
old_timeline_statuses = 'const statuses = ["Draft", "Pending Approval", "Finance Verified", "Payment Requested", "Closed"];'
new_timeline_statuses = 'const statuses = ["Draft", "Pending Approval", "Finance Verified", "Payment Requested", "Closed"];'
content = content.replace(old_timeline_statuses, new_timeline_statuses)

# Timeline index
old_timeline_idx = 'if (report.status === "Pending Finance Verification") currentIndex = 1;'
new_timeline_idx = 'if (report.status === "Pending Finance Verification") currentIndex = 1;\n                      if (report.status === "Corrected Claim") currentIndex = 1;'
content = content.replace(old_timeline_idx, new_timeline_idx)


# Manager Review Condition
old_manager_review = '{(report.status === "Pending Manager Approval" || report.status === "Pending Finance Manager Approval") && (hasRole("Manager") || hasRole("Finance Manager") || hasRole("CFO") || hasRole("Admin")) && ('
new_manager_review = '{(report.status === "Pending Manager Approval" || report.status === "Pending Finance Manager Approval" || report.status === "Corrected Claim") && (hasRole("Manager") || hasRole("Finance Manager") || hasRole("CFO") || hasRole("Admin")) && ('
content = content.replace(old_manager_review, new_manager_review)


# 6. isOwner checks for Edit UI
# Upload/Edit Details/Submit Container:
old_edit_container = '{(report.status === "Draft" || report.status === "Returned for Correction") && ('
new_edit_container = '{(report.status === "Draft" || (report.status === "Returned for Correction" && isOwner(report))) && ('
content = content.replace(old_edit_container, new_edit_container)

# Receipt edit amount trigger
old_receipt_edit = 'onClick={() => { if(report.status === "Draft" || report.status === "Returned for Correction") handleEditAmount(receipt); }}'
new_receipt_edit = 'onClick={() => { if(report.status === "Draft" || (report.status === "Returned for Correction" && isOwner(report))) handleEditAmount(receipt); }}'
content = content.replace(old_receipt_edit, new_receipt_edit)

old_receipt_title = 'title={report.status === "Draft" || report.status === "Returned for Correction" ? "Click to correct amount" : ""}'
new_receipt_title = 'title={report.status === "Draft" || (report.status === "Returned for Correction" && isOwner(report)) ? "Click to correct amount" : ""}'
content = content.replace(old_receipt_title, new_receipt_title)

old_receipt_alert = '{(report.status === "Draft" || report.status === "Returned for Correction") && ('
new_receipt_alert = '{(report.status === "Draft" || (report.status === "Returned for Correction" && isOwner(report))) && ('
# Actually this might replace the edit_container too, so let's be careful.
# I already replaced edit_container which had the same exact string. Let's see if there are other occurrences.
# In the receipt amount block:
# {(report.status === "Draft" || report.status === "Returned for Correction") && (
#   <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider mt-1">
#     {alert ? "Verify Amount" : "Click to Edit"}
#   </span>
# )}
content = content.replace('{(report.status === "Draft" || report.status === "Returned for Correction") && (\n                                      <span className="text-[10px]', '{(report.status === "Draft" || (report.status === "Returned for Correction" && isOwner(report))) && (\n                                      <span className="text-[10px]')


with open('frontend/src/pages/Expenses.tsx', 'w') as f:
    f.write(content)

print("Done Expenses.tsx")
