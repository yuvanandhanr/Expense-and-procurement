with open('src/services/dashboard_service.py', 'r') as f:
    content = f.read()

# Need to import ExpenseReport
if 'from src.models.expense import ExpenseReport' not in content:
    old_import = 'from src.models.invoice import VendorInvoice'
    new_import = 'from src.models.invoice import VendorInvoice\nfrom src.models.expense import ExpenseReport'
    content = content.replace(old_import, new_import)

old_recent = """    async def _get_employee_recent_expenses(self, user_id: int) -> List[Dict[str, Any]]:
        query = select(VendorInvoice).where(
            VendorInvoice.employee_id == user_id
        ).order_by(desc(VendorInvoice.created_at)).limit(5)
        result = await self.db.execute(query)
        expenses = result.scalars().all()
        return [
            {
                "id": exp.invoice_id,
                "title": exp.description or exp.invoice_number,
                "amount": float(exp.grand_total or 0.0),
                "date": exp.created_at.isoformat() if exp.created_at else None,
                "status": exp.status
            }
            for exp in expenses
        ]"""

new_recent = """    async def _get_employee_recent_expenses(self, user_id: int) -> List[Dict[str, Any]]:
        query = select(ExpenseReport).where(
            ExpenseReport.employee_id == user_id,
            ExpenseReport.status.in_(["Approved", "Finance Verified", "Payment Requested", "Closed"])
        ).order_by(desc(ExpenseReport.created_at)).limit(5)
        result = await self.db.execute(query)
        expenses = result.scalars().all()
        return [
            {
                "id": exp.expense_report_id,
                "title": exp.purpose,
                "amount": float(exp.total_amount or 0.0),
                "date": exp.created_at.isoformat() if exp.created_at else None,
                "status": exp.status
            }
            for exp in expenses
        ]"""

content = content.replace(old_recent, new_recent)

with open('src/services/dashboard_service.py', 'w') as f:
    f.write(content)

print("Done Dashboard backend")
