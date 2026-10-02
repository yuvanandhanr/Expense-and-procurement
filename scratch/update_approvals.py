import os

filepath = 'src/pages/Approvals.tsx'
with open(filepath, 'r') as f:
    content = f.read()

content = content.replace('import { Check, X as XIcon } from "lucide-react";', 'import { Check, X as XIcon, Eye } from "lucide-react";\nimport { ReimbursementDetailModal } from "../components/expenses/ReimbursementDetailModal";')

content = content.replace('const [isSubmitting, setIsSubmitting] = useState(false);', 'const [isSubmitting, setIsSubmitting] = useState(false);\n  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);\n  const [selectedReportDetails, setSelectedReportDetails] = useState<any>(null);\n  const [loadingDetails, setLoadingDetails] = useState(false);\n\n  const handleViewDetails = async (reportId: number) => {\n    setSelectedReportId(reportId);\n    setLoadingDetails(true);\n    try {\n      const res = await api.get(`/expenses/${reportId}`);\n      setSelectedReportDetails(res.data);\n    } catch (err) {\n      console.error(err);\n    } finally {\n      setLoadingDetails(false);\n    }\n  };\n')

old_grid = '''      {/* Cards Grid */}
      {loading ? ('''
new_grid = '''      {/* Table/Cards View */}
      {loading ? ('''
content = content.replace(old_grid, new_grid)

old_empty = '''      ) : filteredWorkflows.length === 0 ? (
        <Card className="bg-transparent border-dashed">
          <CardContent className="py-12">
             <EmptyState title={`No pending ${activeTab.toLowerCase()}.`} description="You're all caught up!" />
          </CardContent>
        </Card>
      ) : ('''

new_empty = '''      ) : filteredWorkflows.length === 0 ? (
        <Card className="bg-transparent border-dashed">
          <CardContent className="py-12">
             <EmptyState title={`No pending ${activeTab.toLowerCase()}.`} description="You're all caught up!" />
          </CardContent>
        </Card>
      ) : activeTab === "Reimbursements" ? (
        <div className="overflow-x-auto rounded-xl border border-border shadow-sm">
          <table className="w-full text-left text-sm text-foreground">
            <thead className="bg-muted text-muted-foreground uppercase text-xs font-bold tracking-wider">
              <tr>
                <th className="p-4">Report ID</th>
                <th className="p-4">Purpose</th>
                <th className="p-4">Total Amount</th>
                <th className="p-4">Status</th>
                <th className="p-4">Date Created</th>
                <th className="p-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border bg-card">
              {filteredWorkflows.map((wf) => (
                <tr key={wf.workflow_id} className="hover:bg-muted/50 transition-colors">
                  <td className="p-4 font-semibold">EXP-{wf.entity_id}</td>
                  <td className="p-4 font-medium max-w-[200px] truncate" title={wf.title}>{wf.title?.replace('Expense: ', '')}</td>
                  <td className="p-4 font-bold tracking-tight">${Number(wf.amount || 0).toFixed(2)}</td>
                  <td className="p-4">
                    <StatusBadge status={wf.status} />
                  </td>
                  <td className="p-4 text-xs text-muted-foreground">{new Date(wf.created_at || Date.now()).toLocaleDateString()}</td>
                  <td className="p-4 flex items-center gap-2">
                    {wf.can_approve ? (
                      <Button 
                        size="sm" 
                        variant="primary"
                        onClick={() => handleViewDetails(wf.entity_id)}
                        className="gap-1.5 bg-[#0f172a] text-white hover:bg-slate-800"
                      >
                        Need Approval
                      </Button>
                    ) : (
                      <Button 
                        size="sm" 
                        variant="view"
                        onClick={() => handleViewDetails(wf.entity_id)}
                        className="gap-1.5"
                      >
                        <Eye className="w-3.5 h-3.5" /> View
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : ('''
content = content.replace(old_empty, new_empty)

old_end = '      </Dialog>\n    </div>\n  );'
new_end = '''      </Dialog>
      
      {/* Reimbursement Detail Modal */}
      {selectedReportId && (
        <ReimbursementDetailModal
          isOpen={!!selectedReportId}
          onClose={() => {
             setSelectedReportId(null);
             setSelectedReportDetails(null);
             fetchWorkflows();
          }}
          receiptDetails={selectedReportDetails}
          loading={loadingDetails}
          isPendingForUser={filteredWorkflows.find(w => w.entity_id === selectedReportId)?.can_approve || false}
          onAction={async (action) => {
             const wf = filteredWorkflows.find(w => w.entity_id === selectedReportId);
             if (wf) {
               setSelectedWorkflow(wf);
               setActionType(action === "approve" ? (wf.status === "Payment Requested" ? "pay" : "approve") : action);
               // Close this details modal so they can see the comment modal
               setSelectedReportId(null);
               setSelectedReportDetails(null);
             }
          }}
        />
      )}
    </div>
  );'''

content = content.replace(old_end, new_end)

with open(filepath, 'w') as f:
    f.write(content)
print('Updated Approvals.tsx')
