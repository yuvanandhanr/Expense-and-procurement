import re

with open("src/api/approvals_inbox.py", "r") as f:
    content = f.read()

# Fix AssetIncident query
old_asset_q = """        stmt = (
            select(AssetIncident, Asset, UserModel)
            .join(Asset, AssetIncident.asset_id == Asset.asset_id)
            .join(UserModel, AssetIncident.reporter_id == UserModel.user_id)
            .where(AssetIncident.status != "Draft")
        )"""
new_asset_q = """        from sqlalchemy.orm import selectinload
        stmt = (
            select(AssetIncident, Asset, UserModel)
            .options(selectinload(UserModel.roles))
            .join(Asset, AssetIncident.asset_id == Asset.asset_id)
            .join(UserModel, AssetIncident.reporter_id == UserModel.user_id)
            .where(AssetIncident.status != "Draft")
        )"""

content = content.replace(old_asset_q, new_asset_q)

# Fix ExpenseReport query
old_exp_q = """        stmt = (
            select(ExpenseReport, UserModel)
            .join(UserModel, ExpenseReport.employee_id == UserModel.user_id)
            .join(ExpenseApproval, (ExpenseApproval.expense_report_id == ExpenseReport.expense_report_id))
            .where(
                ExpenseReport.employee_id != current_user.user_id,
                ExpenseReport.status != "Draft",
                ExpenseApproval.approver_id == current_user.user_id,
                ExpenseApproval.status == "Pending"
            )
        )"""
new_exp_q = """        from sqlalchemy.orm import selectinload
        stmt = (
            select(ExpenseReport, UserModel)
            .options(selectinload(UserModel.roles))
            .join(UserModel, ExpenseReport.employee_id == UserModel.user_id)
            .join(ExpenseApproval, (ExpenseApproval.expense_report_id == ExpenseReport.expense_report_id))
            .where(
                ExpenseReport.employee_id != current_user.user_id,
                ExpenseReport.status != "Draft",
                ExpenseApproval.approver_id == current_user.user_id,
                ExpenseApproval.status == "Pending"
            )
        )"""

content = content.replace(old_exp_q, new_exp_q)

with open("src/api/approvals_inbox.py", "w") as f:
    f.write(content)
