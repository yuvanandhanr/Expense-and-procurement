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
UPLOAD_DIR = "uploads/receipts"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[ExpenseReportResponse])
async def list_expenses(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    # Simple role check: if Employee, show their own. If Manager/Finance, show all (or filtered).
    role_names = [r.role.role_name for r in current_user.roles]
    if "Admin" in role_names or "Finance" in role_names or "CFO" in role_names:
        reports = await repo.get_all_reports()
    elif "Manager" in role_names:
        # Simplification: just show all, in a real system we'd filter by department
        reports = await repo.get_all_reports()
    else:
        reports = await repo.get_all_reports(employee_id=current_user.user_id)
    return reports

@router.post("/", response_model=ExpenseReportResponse)
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
    return new_report

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
        
        receipt = Receipt(
            expense_report_id=report_id,
            merchant_name=ocr_result.get("merchant_name"),
            receipt_date=ocr_result.get("date"),
            ocr_amount=ocr_amount,
            verified_amount=verified_amount,
            image_path=f"/uploads/receipts/{unique_name}",
            file_name=file.filename,
            ocr_confidence=confidence,
            ocr_json=ocr_result
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
            
    # Transition status
    report.status = "Pending Approval"
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
    return {"status": "submitted", "total_amount": report.total_amount}
