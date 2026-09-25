import re

with open("src/services/approval_service.py", "r") as f:
    content = f.read()

old_query = """        query = (
            select(ApprovalWorkflow, PurchaseRequisition, UserModel)
            .join(PurchaseRequisition, ApprovalWorkflow.pr_id == PurchaseRequisition.pr_id)
            .join(UserModel, PurchaseRequisition.requestor_id == UserModel.user_id)"""

new_query = """        from sqlalchemy.orm import selectinload
        query = (
            select(ApprovalWorkflow, PurchaseRequisition, UserModel)
            .options(selectinload(UserModel.roles))
            .join(PurchaseRequisition, ApprovalWorkflow.pr_id == PurchaseRequisition.pr_id)
            .join(UserModel, PurchaseRequisition.requestor_id == UserModel.user_id)"""

content = content.replace(old_query, new_query)

with open("src/services/approval_service.py", "w") as f:
    f.write(content)
