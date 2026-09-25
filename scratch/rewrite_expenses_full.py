import re

with open('frontend/src/pages/Expenses.tsx', 'r') as f:
    content = f.read()

# 1. Imports
content = content.replace(
    'import { Card, CardHeader, CardTitle, CardContent, Button, Input, Select, Skeleton, Badge, Dialog } from "../components/ui";',
    'import { Card, CardHeader, CardTitle, CardContent, Button, Input, Select, Skeleton, Badge, Dialog, HeroTimestamp, EmptyState } from "../components/ui";'
)
content = content.replace(
    'import { Plus, Upload, CheckCircle, XCircle, FileText, AlertCircle, RefreshCw, DollarSign, Clock, CheckSquare, XOctagon, Trash2 } from "lucide-react";',
    'import { Plus, Upload, CheckCircle, XCircle, FileText, AlertCircle, RefreshCw, DollarSign, Clock, CheckSquare, XOctagon, Trash2, ClipboardList } from "lucide-react";'
)

# 2. Add statusFilter state
if 'const [statusFilter, setStatusFilter] = useState("All");' not in content:
    content = content.replace(
        'const [selectedReportId, setSelectedReportId] = useState<number | null>(null);',
        'const [selectedReportId, setSelectedReportId] = useState<number | null>(null);\n  const [statusFilter, setStatusFilter] = useState("All");'
    )


# Read the parts of the return statement.
# We will construct a completely new return statement.

new_return = """
  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase();
    if (s === "approved" || s === "closed" || s === "payment requested" || s === "finance verified") return <Badge variant="success">{status}</Badge>;
    if (s === "pending" || s.includes("pending") || s === "corrected claim") return <Badge variant="warning">{status}</Badge>;
    if (s === "rejected" || s === "returned for correction") return <Badge variant="error">{status}</Badge>;
    return <Badge variant="neutral">{status}</Badge>;
  };

  const filteredExpenses = expenses.filter((r: any) => {
    if (statusFilter === "All") return true;
    if (statusFilter === "Draft") return r.status === "Draft";
    if (statusFilter === "Submitted") return r.status.includes("Pending") || r.status === "Corrected Claim";
    if (statusFilter === "Approved") return r.status === "Approved" || r.status === "Closed" || r.status === "Payment Requested" || r.status === "Finance Verified";
    if (statusFilter === "Rejected") return r.status === "Rejected" || r.status === "Returned for Correction";
    return r.status === statusFilter;
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            {isManager && !isFinance && !hasRole("Admin") ? "Team Reimbursements" : "Employee Reimbursements"}
          </h1>
          <p className="text-xs text-muted-foreground mt-1">Manage, verify, and track employee expense reports.</p>
        </div>
        <div className="flex items-center space-x-4">
          <HeroTimestamp />
          {!isManagerOrAdmin && (
            <Button onClick={() => setIsCreateOpen(true)} className="font-bold text-xs uppercase tracking-wider">
              New Reimbursement
            </Button>
          )}
        </div>
      </div>

      {/* Filters & Controls */}
      <div className="flex items-center space-x-2 bg-card p-3 rounded-lg border border-border">
        <span className="text-xs font-semibold text-muted-foreground uppercase px-2">Filter State:</span>
        {["All", "Draft", "Submitted", "Approved", "Rejected"].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-3 py-1 text-xs font-bold rounded-full transition-all ${
              statusFilter === status
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent"
            }`}
          >
            {status}
          </button>
        ))}
      </div>

      {/* Table List */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : filteredExpenses.length === 0 ? (
            <EmptyState
              icon={<ClipboardList className="w-8 h-8" />}
              title="No Reimbursements found."
              description="There are no expense reports matching this filter."
              actionLabel={!isManagerOrAdmin ? "Create new reimbursement" : undefined}
              onAction={!isManagerOrAdmin ? () => setIsCreateOpen(true) : undefined}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border bg-accent/40 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    <th className="p-4">Report ID</th>
                    <th className="p-4">Purpose</th>
                    <th className="p-4">Total Amount</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Date Created</th>
                    <th className="p-4">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-sm">
                  {filteredExpenses.map((report: any) => (
                    <tr key={report.expense_report_id} className="hover:bg-accent/20 transition-colors">
                      <td className="p-4 font-bold text-xs tracking-wider text-primary">{report.expense_report_id}</td>
                      <td className="p-4">
                        <div className="font-semibold">{report.purpose}</div>
                        <div className="text-xs text-muted-foreground truncate max-w-[200px]">{report.justification}</div>
                      </td>
                      <td className="p-4 font-bold text-foreground">
                        ${Number(report.total_amount).toFixed(2)}
                      </td>
                      <td className="p-4">
                        {getStatusBadge(report.status)}
                      </td>
                      <td className="p-4 text-xs text-muted-foreground">{new Date(report.created_at).toLocaleDateString()}</td>
                      <td className="p-4 flex items-center gap-2">
                        {report.status === "Draft" && (
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-8 w-8 text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded shrink-0"
                            title="Delete Draft Report"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (window.confirm("Are you sure you want to delete this draft expense report?")) {
                                deleteReportMutation.mutate(report.expense_report_id);
                              }
                            }}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                        <Button size="sm" onClick={() => setSelectedReportId(report.expense_report_id)}>
                          Review
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
"""

# Now we extract everything below `{/* Create Reimbursement Modal */}` up to `{/* Review & Submit Modal */}` from the original file
# We'll use the existing modals, but we'll modify the "Review Dialog" which was the right column.

create_modal_idx = content.find('{/* Create Reimbursement Modal */}')
review_modal_idx = content.find('{/* Review & Submit Modal */}')
manager_modal_idx = content.find('{/* Manager Action Modal */}')

create_modal = content[create_modal_idx:review_modal_idx]

# We need the full right column logic. It was inside `<div className="lg:col-span-2">` which is between `<div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">` and the modals.

right_col_start = content.find('{/* Right Column: Report Details & Receipts */}')
right_col_end = content.find('{/* Create Reimbursement Modal */}')

right_col = content[right_col_start:right_col_end]
# We will wrap this right_col inside a Dialog.
# First, let's clean up the right_col. It has `if (!report) return null; return ( <Card ... )`
# We want to change the `<Card ...>` into `<Dialog isOpen={true} onClose={() => setSelectedReportId(null)} title={report.purpose}>`

right_col = right_col.replace('className="lg:col-span-2"', '')
right_col = right_col.replace('{selectedReportId ? (() => {', '{selectedReportId && (() => {')
right_col = right_col.replace('return (', 'return (\n<Dialog isOpen={true} onClose={() => setSelectedReportId(null)} title={report.purpose}>')
right_col = right_col.replace('</Card>', '</Dialog>')
# Remove the <Card> and <CardHeader> tags, replace with div
right_col = right_col.replace('<Card className="h-full border-t-4 border-t-primary shadow-lg flex flex-col">', '<div>')
right_col = right_col.replace('<CardHeader className="flex flex-row justify-between items-start shrink-0">', '<div className="flex flex-row justify-between items-start shrink-0">')
right_col = right_col.replace('<CardTitle className="text-2xl">{report.purpose}</CardTitle>', '')
right_col = right_col.replace('</CardHeader>', '</div>')
right_col = right_col.replace('<CardContent className="space-y-6 flex-1 overflow-y-auto">', '<div className="space-y-6 flex-1 overflow-y-auto max-h-[70vh]">')
right_col = right_col.replace('</CardContent>', '</div>')
right_col = right_col.replace('})() : (', '})()}\n{/*')
right_col = right_col.replace('</div>\n          )}', '*/}')

# Get the rest of the modals
rest_of_modals = content[review_modal_idx:]

# Combine everything
idx_start_return = content.find('return (\n    <div className="space-y-6">')
final_content = content[:idx_start_return] + new_return + "\n" + create_modal + "\n" + right_col + "\n" + rest_of_modals

# One more fix: The return statement closes with </div>.
final_content += "\n"

with open('frontend/src/pages/Expenses.tsx', 'w') as f:
    f.write(final_content)

print("Done rewrite")
