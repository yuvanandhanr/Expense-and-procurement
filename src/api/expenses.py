from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from typing import List, Any
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
import os
import uuid
from decimal import Decimal
from datetime import datetime

from src.database.dependency import get_db_session
from src.schemas.expense import ExpenseReportCreate, ExpenseReportUpdate, ExpenseReportResponse, ReceiptResponse, ReceiptUpdate
from src.repositories.expense import ExpenseRepository
from src.models.expense import ExpenseReport, Receipt
from src.services.ocr import OCRService
from src.api.auth import get_current_user
from src.models.auth import User
from src.services.approval_service import ApprovalService

router = APIRouter(prefix="/expenses", tags=["Employee Expenses"])

# Helper for file uploads
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "receipts")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def parse_ocr_date(date_str: str):
    if not date_str:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    return None

@router.get("", response_model=List[ExpenseReportResponse])
async def list_expenses(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    # Simple role check: if Employee, show their own. If Manager, show their department. If Finance/CFO/Admin, show all.
    role_names = [r.role_name for r in current_user.roles]
    if "Admin" in role_names or "Finance" in role_names or "Finance Manager" in role_names or "CFO" in role_names:
        reports = await repo.get_all_reports()
    elif "Manager" in role_names:
        reports = await repo.get_all_reports(department_id=current_user.department_id)
    else:
        reports = await repo.get_all_reports(employee_id=current_user.user_id)
    return reports

@router.post("", response_model=ExpenseReportResponse)
async def create_expense_report(
    payload: ExpenseReportCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    new_report = ExpenseReport(
        employee_id=current_user.user_id,
        purpose=payload.purpose,
        justification=payload.justification,
        department_id=payload.department_id,
        cost_center_id=payload.cost_center_id,
        project_code=payload.project_code,
        currency=payload.currency,
        status="Draft",
        total_amount=Decimal("0.00")
    )
    await repo.create_report(new_report)
    loaded_report = await repo.get_report_by_id(new_report.expense_report_id)
    return loaded_report

@router.get("/{report_id}", response_model=ExpenseReportResponse)
async def get_expense_report(
    report_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    report = await repo.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Expense report not found")
    return report

@router.post("/{report_id}/receipts/upload", response_model=List[ReceiptResponse])
async def upload_receipts(
    report_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    report = await repo.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Expense report not found")
        
    if report.status != "Draft":
        raise HTTPException(status_code=400, detail="Cannot add receipts to non-draft report")

    created_receipts = []
    total_added = Decimal("0.00")

    for file in files:
        ext = file.filename.split(".")[-1]
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, unique_name)
        
        content = await file.read()
        async with aiofiles.open(filepath, 'wb') as out_file:
            await out_file.write(content)
            
        # Run OCR
        ocr_result = OCRService.process_receipt_image(content)
        
        # Determine verified amount (fallback to 0 if low confidence)
        confidence = ocr_result.get("confidence", Decimal("0.00"))
        ocr_amount = ocr_result.get("total_amount", Decimal("0.00"))
        
        # If low confidence, employee must manually verify. Default to 0.00 so report cannot be submitted blindly.
        verified_amount = ocr_amount if confidence > Decimal("50.00") else Decimal("0.00")
        
        # Convert Decimal values to float for JSON serialization
        import decimal
        safe_ocr_result = {
            k: float(v) if isinstance(v, decimal.Decimal) else v
            for k, v in ocr_result.items()
        }
        
        receipt = Receipt(
            expense_report_id=report_id,
            merchant_name=ocr_result.get("merchant_name"),
            receipt_date=parse_ocr_date(ocr_result.get("date")),
            ocr_amount=ocr_amount,
            verified_amount=verified_amount,
            image_path=f"/uploads/receipts/{unique_name}",
            file_name=file.filename,
            ocr_confidence=confidence,
            ocr_json=safe_ocr_result
        )
        await repo.add_receipt(receipt)
        created_receipts.append(receipt)
        total_added += verified_amount
        
    # Update total report amount
    report.total_amount += total_added
    await repo.update_report(report)
    await db.commit()
    
    # Reload receipts
    return created_receipts

@router.put("/{report_id}/receipts/{receipt_id}", response_model=ReceiptResponse)
async def update_receipt(
    report_id: int,
    receipt_id: int,
    payload: ReceiptUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    report = await repo.get_report_by_id(report_id)
    if not report or report.status != "Draft":
        raise HTTPException(status_code=400, detail="Report not found or not in draft state")
        
    receipt = await repo.get_receipt_by_id(receipt_id)
    if not receipt or receipt.expense_report_id != report_id:
        raise HTTPException(status_code=404, detail="Receipt not found")
        
    # Subtract old amount, add new amount
    report.total_amount -= receipt.verified_amount
    
    receipt.merchant_name = payload.merchant_name if payload.merchant_name is not None else receipt.merchant_name
    receipt.receipt_date = payload.receipt_date if payload.receipt_date is not None else receipt.receipt_date
    receipt.category = payload.category if payload.category is not None else receipt.category
    receipt.verified_amount = payload.verified_amount if payload.verified_amount is not None else receipt.verified_amount
    receipt.tax = payload.tax if payload.tax is not None else receipt.tax
    receipt.currency = payload.currency if payload.currency is not None else receipt.currency
    
    report.total_amount += receipt.verified_amount
    
    await repo.update_receipt(receipt)
    await repo.update_report(report)
    await db.commit()
    return receipt
    
@router.delete("/{report_id}/receipts/{receipt_id}")
async def delete_receipt(
    report_id: int,
    receipt_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    report = await repo.get_report_by_id(report_id)
    if not report or report.status != "Draft":
        raise HTTPException(status_code=400, detail="Report not found or not in draft state")
        
    receipt = await repo.get_receipt_by_id(receipt_id)
    if not receipt or receipt.expense_report_id != report_id:
        raise HTTPException(status_code=404, detail="Receipt not found")
        
    report.total_amount -= receipt.verified_amount
    await repo.delete_receipt(receipt)
    await repo.update_report(report)
    await db.commit()
    return {"status": "success"}

from pydantic import BaseModel

class ExpenseActionPayload(BaseModel):
    comments: str = ""

@router.post("/{report_id}/submit")
async def submit_report(
    report_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    report = await repo.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if report.status != "Draft":
        raise HTTPException(status_code=400, detail="Report is already submitted")
        
    # Validate that all receipts have been verified (no 0.00 amounts unless it's a legit 0 receipt)
    for r in report.receipts:
        if r.verified_amount == Decimal("0.00") and r.ocr_confidence and r.ocr_confidence < Decimal("50.00"):
            raise HTTPException(status_code=400, detail=f"Receipt {r.file_name} requires manual verification of the amount.")
            
    # Duplicate and Policy Checks
    duplicates_found = False
    policy_issues = []
    
    if report.total_amount > Decimal("500.00") and not report.justification:
        policy_issues.append("High amount requires justification")
        
    from sqlalchemy import select
    for r in report.receipts:
        if r.merchant_name and r.receipt_date:
            query_dup = select(Receipt).join(ExpenseReport).where(
                ExpenseReport.employee_id == report.employee_id,
                ExpenseReport.expense_report_id != report.expense_report_id,
                ExpenseReport.status != "Rejected",
                Receipt.merchant_name == r.merchant_name,
                Receipt.receipt_date == r.receipt_date,
                Receipt.verified_amount == r.verified_amount
            )
            result_dup = await db.execute(query_dup)
            if result_dup.scalars().first():
                duplicates_found = True
                
        if r.verified_amount > Decimal("100.00") and not r.category:
            policy_issues.append(f"Receipt {r.file_name} > $100 requires a category")
            
    report.duplicate_flag = duplicates_found
    report.policy_flags = ", ".join(policy_issues) if policy_issues else None
    
    is_manager = any(r.role_name == "Manager" for r in current_user.roles)
    if is_manager and policy_issues and not report.justification:
        raise HTTPException(status_code=400, detail="Policy violations found. Manager claims require justification.")
    # Transition status
    report.status = "Pending Manager Approval"
    await repo.update_report(report)
    
    # Trigger approval engine based on total_amount
    try:
        approval_service = ApprovalService(db)
        await approval_service.initialize_approval_flow(
            document_type="ExpenseReport",
            document_id=report.expense_report_id,
            amount=report.total_amount,
            department_id=report.department_id
        )
    except Exception as e:
        # If approval flow fails, we should probably revert status
        report.status = "Draft"
        await repo.update_report(report)
        raise HTTPException(status_code=500, detail=f"Failed to initialize approval flow: {str(e)}")

    await db.commit()
    return {"status": "submitted", "total_amount": report.total_amount, "duplicates": duplicates_found, "policies": report.policy_flags}

@router.post("/{report_id}/approve")
async def approve_expense(
    report_id: int,
    payload: ExpenseActionPayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    from src.models.expense import ExpenseApproval
    from src.models.auth import Role, User
    from sqlalchemy import select
    
    repo = ExpenseRepository(db)
    report = await repo.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if report.status not in ["Pending Manager Approval", "Pending Finance Manager Approval"]:
        raise HTTPException(status_code=400, detail="Report is not pending approval")
        
    query = select(ExpenseApproval).where(
        ExpenseApproval.expense_report_id == report_id,
        ExpenseApproval.approver_id == current_user.user_id,
        ExpenseApproval.status == "Pending"
    )
    result = await db.execute(query)
    approval = result.scalar_one_or_none()
    
    if not approval and not any(r.role_name == "Admin" for r in current_user.roles):
        raise HTTPException(status_code=403, detail="Not authorized to approve this report")
        
    if approval:
        approval.status = "Approved"
        approval.comments = payload.comments
        approval.actioned_at = datetime.utcnow()
        
    if report.status == "Pending Manager Approval":
        if report.total_amount > Decimal("1000.00"):
            report.status = "Pending Finance Manager Approval"
            
            # Find a Finance Manager
            fm_query = select(User).join(User.roles).where(Role.role_name == "Finance Manager", User.status == "Active")
            fm_result = await db.execute(fm_query)
            finance_manager = fm_result.scalars().first()
            
            fm_approval = ExpenseApproval(
                expense_report_id=report.expense_report_id,
                approver_id=finance_manager.user_id if finance_manager else None,
                status="Pending"
            )
            db.add(fm_approval)
        else:
            report.status = "Payment Requested"
            report.payment_status = "Pending Payment"
    elif report.status == "Pending Finance Manager Approval":
        report.status = "Payment Requested"
        report.payment_status = "Pending Payment"
        
    await repo.update_report(report)
    await db.commit()
    return {"status": "Approved"}

@router.post("/{report_id}/reject")
async def reject_expense(
    report_id: int,
    payload: ExpenseActionPayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    from src.models.expense import ExpenseApproval
    from sqlalchemy import select
    
    repo = ExpenseRepository(db)
    report = await repo.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    query = select(ExpenseApproval).where(
        ExpenseApproval.expense_report_id == report_id,
        ExpenseApproval.approver_id == current_user.user_id,
        ExpenseApproval.status == "Pending"
    )
    result = await db.execute(query)
    approval = result.scalar_one_or_none()
    
    if approval:
        approval.status = "Rejected"
        approval.comments = payload.comments
        approval.actioned_at = datetime.utcnow()
        
    report.status = "Rejected"
    await repo.update_report(report)
    await db.commit()
    return {"status": "Rejected"}

@router.post("/{report_id}/return")
async def return_expense(
    report_id: int,
    payload: ExpenseActionPayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    from src.models.expense import ExpenseApproval
    from sqlalchemy import select
    
    repo = ExpenseRepository(db)
    report = await repo.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    query = select(ExpenseApproval).where(
        ExpenseApproval.expense_report_id == report_id,
        ExpenseApproval.approver_id == current_user.user_id,
        ExpenseApproval.status == "Pending"
    )
    result = await db.execute(query)
    approval = result.scalar_one_or_none()
    
    if approval:
        approval.status = "Returned"
        approval.comments = payload.comments
        approval.actioned_at = datetime.utcnow()
        
    report.status = "Returned for Correction"
    await repo.update_report(report)
    await db.commit()
    return {"status": "Returned"}

@router.post("/{report_id}/pay")
async def pay_expense(
    report_id: int,
    payload: ExpenseActionPayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    report = await repo.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if report.status != "Payment Requested":
        raise HTTPException(status_code=400, detail="Report is not requesting payment")
        
    report.status = "Closed"
    report.payment_status = "Paid"
    report.payment_reference = f"PAY-EXP-{report_id}-{uuid.uuid4().hex[:6]}"
    await repo.update_report(report)
    await db.commit()
    return {"status": "Paid", "payment_reference": report.payment_reference}
