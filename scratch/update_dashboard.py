import re

with open("src/services/dashboard_service.py", "r") as f:
    content = f.read()

old_pending = """    async def _get_pending_approvals_count(self, manager_id: Optional[int] = None) -> int:
        # Return count of PRs in 'Pending Approval' status
        query = select(func.count(PurchaseRequisition.pr_id)).where(PurchaseRequisition.status == "Pending Approval")
        # If manager_id is passed, we can filter by requisition's manager or approval assignments if mapping exists
        result = await self.db.execute(query)
        return result.scalar() or 0"""

new_pending = """    async def _get_pending_approvals_count(self, manager_id: Optional[int] = None) -> int:
        from src.models.expense import ExpenseApproval
        from src.models.approval import ApprovalStep
        from src.models.auth import User
        count = 0
        if manager_id:
            user = await self.db.get(User, manager_id)
            if user:
                user_roles = [r.role_id for r in user.roles]
                
                # PR approvals
                pr_query = select(func.count(ApprovalStep.step_id)).where(
                    (ApprovalStep.approver_id == manager_id) |
                    (ApprovalStep.approver_id.is_(None) & ApprovalStep.approver_role_id.in_(user_roles)),
                    ApprovalStep.status == "Pending"
                )
                pr_res = await self.db.execute(pr_query)
                count += pr_res.scalar() or 0
                
                # Expense approvals
                exp_query = select(func.count(ExpenseApproval.approval_id)).where(
                    ExpenseApproval.approver_id == manager_id,
                    ExpenseApproval.status == "Pending"
                )
                exp_res = await self.db.execute(exp_query)
                count += exp_res.scalar() or 0
        return count"""

content = content.replace(old_pending, new_pending)

with open("src/services/dashboard_service.py", "w") as f:
    f.write(content)

