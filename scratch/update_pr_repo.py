import re

with open("src/repositories/purchase_requisition.py", "r") as f:
    content = f.read()

new_method = """    async def list_accessible_prs(self, user) -> List[PurchaseRequisition]:
        from src.models.approval import ApprovalWorkflow, ApprovalStep, ApprovalHistory
        from src.models.auth import User as UserModel
        from sqlalchemy import select, or_
        from sqlalchemy.orm import selectinload

        user_roles = [r.role_id for r in user.roles]
        
        stmt = (
            select(self.model)
            .outerjoin(UserModel, self.model.requestor_id == UserModel.user_id)
            .outerjoin(ApprovalWorkflow, ApprovalWorkflow.pr_id == self.model.pr_id)
            .outerjoin(ApprovalStep, ApprovalStep.workflow_id == ApprovalWorkflow.workflow_id)
            .outerjoin(ApprovalHistory, ApprovalHistory.step_id == ApprovalStep.step_id)
            .options(
                selectinload(self.model.items),
                selectinload(self.model.requestor)
            )
        )
        
        conditions = [self.model.requestor_id == user.user_id]
        
        # If manager, can see direct reports
        if any(r.role_name == "Manager" for r in user.roles):
            conditions.append((UserModel.manager_id == user.user_id) & (self.model.status != "Draft"))
            
        # In approval step or history
        conditions.append((ApprovalStep.approver_id == user.user_id) & (self.model.status != "Draft"))
        conditions.append((ApprovalStep.approver_id.is_(None)) & (ApprovalStep.approver_role_id.in_(user_roles)) & (self.model.status != "Draft"))
        conditions.append((ApprovalHistory.performed_by == user.user_id) & (self.model.status != "Draft"))
        
        stmt = stmt.where(or_(*conditions)).order_by(self.model.created_at.desc())
        result = await self.session.execute(stmt)
        
        # Deduplicate
        seen = set()
        prs = []
        for pr in result.scalars().all():
            if pr.pr_id not in seen:
                seen.add(pr.pr_id)
                prs.append(pr)
        return prs
"""

if "def list_accessible_prs" not in content:
    content += "\n" + new_method

with open("src/repositories/purchase_requisition.py", "w") as f:
    f.write(content)

