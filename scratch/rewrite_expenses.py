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

# 3. Replace summary cards and 2-column layout with the new layout
# The layout starts at: return ( <div className="space-y-6"> <div className="flex justify-between items-center">
# And ends at: {/* Create Reimbursement Modal */}

# We need to extract the return statement body up to the first modal.
layout_start_idx = content.find('return (')
first_modal_idx = content.find('{/* Create Reimbursement Modal */}')

if layout_start_idx != -1 and first_modal_idx != -1:
    old_layout = content[layout_start_idx:first_modal_idx]
    
    new_layout = """return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            {isManager && !isFinance && !hasRole("Admin") ? "Team Reimbursements" : "My Reimbursements"}
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
        {["All", "Draft", "Pending", "Approved", "Paid", "Rejected"].map((status) => (
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
          ) : expenses.filter((r: any) => {
              if (statusFilter === "All") return true;
              if (statusFilter === "Paid") return r.status === "Closed";
              if (statusFilter === "Pending") return r.status.includes("Pending") || r.status === "Corrected Claim";
              if (statusFilter === "Rejected") return r.status === "Rejected" || r.status === "Returned for Correction";
              return r.status === statusFilter;
          }).length === 0 ? (
            <EmptyState
              icon={<ClipboardList className="w-8 h-8" />}
              title="No Reimbursements found."
              description="There are no expense reports matching this filter."
              actionLabel="Create new reimbursement"
              onAction={() => setIsCreateOpen(true)}
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
                  {expenses.filter((r: any) => {
                      if (statusFilter === "All") return true;
                      if (statusFilter === "Paid") return r.status === "Closed";
                      if (statusFilter === "Pending") return r.status.includes("Pending") || r.status === "Corrected Claim";
                      if (statusFilter === "Rejected") return r.status === "Rejected" || r.status === "Returned for Correction";
                      return r.status === statusFilter;
                  }).map((report: any) => (
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
                        <Badge variant={
                          report.status === "Draft" || (report.status === "Returned for Correction" && isOwner(report)) ? "neutral" : 
                          report.status === "Approved" || report.status === "Closed" ? "success" : 
                          report.status.includes("Pending") || report.status === "Corrected Claim" ? "warning" : "error"
                        }>{report.status}</Badge>
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
    content = content.replace(old_layout, new_layout)


# 4. We need to wrap the right column details (from old UI) inside a Dialog if selectedReportId is set.
# The review modal logic should completely replace the old `isReviewOpen` modal and use `selectedReportId`.

# Actually, replacing large chunks with regex is risky. Let me just write out the full file contents. 
# It's cleaner and guarantees no parsing errors.
