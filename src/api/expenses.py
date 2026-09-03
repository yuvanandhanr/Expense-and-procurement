from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
import os
import uuid
import hashlib
import logging
from decimal import Decimal
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from src.database.dependency import get_db_session
from src.schemas.expense import ExpenseReportCreate, ExpenseReportUpdate, ExpenseReportResponse, ReceiptResponse, ReceiptUpdate
from src.repositories.expense import ExpenseRepository
from src.models.expense import ExpenseReport, Receipt
from src.services.ocr import OCRService
from src.api.auth import get_current_user
from src.models.auth import User
from src.services.approval_service import ApprovalService

router = APIRouter(prefix="/expenses", tags=["Employee Expenses"])
logger = logging.getLogger(__name__)

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


def _roles(user: User) -> set[str]:
    return {role.role_name for role in user.roles}


def _log_action(user: User, action: str, record_id: int | str, *, level: int = logging.INFO) -> None:
    """Log operational events without receipt contents, OCR text, or other sensitive data."""
    logger.log(
        level,
        "expense_action timestamp=%s user_id=%s action=%s record_id=%s",
        datetime.utcnow().isoformat(timespec="seconds") + "Z",
        user.user_id,
        action,
        record_id,
    )


def _can_access_report(report: ExpenseReport, user: User) -> bool:
    roles = _roles(user)
    if bool(roles & {"Admin", "Finance", "Finance Manager", "CFO", "CEO", "Manager"}):
        return True
    if report.employee_id == user.user_id:
        return True
    return False


def _can_act_on_pending_report(report: ExpenseReport, user: User, explicit_approval: object | None) -> bool:
    """Whether a user may approve / reject / return a report awaiting review.

    An explicit expense-approval assignment wins. Otherwise, any manager-level
    approval role (Admin, Manager, Finance Manager, CFO) may act on a report they
    are allowed to access, matching the controls presented in the UI.
    """
    if explicit_approval is not None:
        return True
    if not _can_access_report(report, user):
        return False
    return bool(_roles(user) & {"Admin", "Manager", "Finance Manager", "CFO", "CEO"})


async def _get_accessible_report(repo: ExpenseRepository, report_id: int, user: User) -> ExpenseReport:
    report = await repo.get_report_by_id(report_id)
    if not report or not _can_access_report(report, user):
        # Do not disclose the existence of another user's private draft.
        _log_action(user, "expense_access_denied", report_id, level=logging.WARNING)
        raise HTTPException(status_code=404, detail="Expense report not found")
    return report


async def _get_owned_editable_report(repo: ExpenseRepository, report_id: int, user: User) -> ExpenseReport:
    report = await _get_accessible_report(repo, report_id, user)
    if report.status not in ("Draft", "Returned for Correction"):
        raise HTTPException(status_code=400, detail="Report is not in an editable state")
    roles = _roles(user)
    if report.employee_id != user.user_id and not bool(roles & {"Admin", "Manager"}):
        _log_action(user, "expense_draft_access_denied", report_id, level=logging.WARNING)
        raise HTTPException(status_code=403, detail="Not authorized to edit this report")
    return report


def _remove_uploaded_file(image_path: str) -> None:
    """Best-effort cleanup of a file stored below the receipt upload directory."""
    filename = os.path.basename(image_path)
    path = os.path.join(UPLOAD_DIR, filename)
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        logger.exception("Unable to remove receipt file during cleanup")


def _present_report(report: ExpenseReport) -> ExpenseReport:
    """Keep pre-constraint legacy data from breaking read responses before migration runs."""
    if not report.justification or not report.justification.strip():
        report.justification = "Legacy report: description unavailable"
    return report

@router.get("", response_model=List[ExpenseReportResponse])
async def list_expenses(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    role_names = [r.role_name for r in current_user.roles]
    if any(r in role_names for r in ["Admin", "Finance", "Finance Manager", "CFO", "CEO", "Manager"]):
        reports = await repo.get_all_reports()
    else:
        reports = await repo.get_all_reports(employee_id=current_user.user_id)
    return [_present_report(report) for report in reports if _can_access_report(report, current_user)]

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
    _log_action(current_user, "expense_draft_created", new_report.expense_report_id)
    loaded_report = await repo.get_report_by_id(new_report.expense_report_id)
    return loaded_report

@router.get("/{report_id}", response_model=ExpenseReportResponse)
async def get_expense_report(
    report_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    report = await _get_accessible_report(repo, report_id, current_user)
    return _present_report(report)

@router.post("/{report_id}/receipts/upload", response_model=List[ReceiptResponse])
async def upload_receipts(
    report_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    report = await _get_owned_editable_report(repo, report_id, current_user)

    # Read and validate the whole batch before writing anything. This avoids a
    # partially uploaded request if one file is a duplicate.
    uploads: list[tuple[UploadFile, bytes, str]] = []
    batch_hashes: set[str] = set()
    for file in files:
        content = await file.read()
        content_hash = hashlib.sha256(content).hexdigest()
        if content_hash in batch_hashes or await repo.get_receipt_by_content_hash(report_id, content_hash):
            _log_action(current_user, "receipt_duplicate_detected", report_id, level=logging.WARNING)
            raise HTTPException(status_code=409, detail="Duplicate receipt detected in this reimbursement report.")
        batch_hashes.add(content_hash)
        uploads.append((file, content, content_hash))

    created_receipts = []
    total_added = Decimal("0.00")

    written_paths: list[str] = []
    try:
      for file, content, content_hash in uploads:
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin"
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, unique_name)
        
        async with aiofiles.open(filepath, 'wb') as out_file:
            await out_file.write(content)
        written_paths.append(filepath)
            
        # Run OCR
        ocr_result = OCRService.process_receipt_image(content)
        
        # Determine verified amount (fallback to 0 if low confidence)
        confidence = ocr_result.get("confidence", Decimal("0.00"))
        ocr_amount = ocr_result.get("total_amount", Decimal("0.00"))
        parsed_date = parse_ocr_date(ocr_result.get("date"))
        merchant = ocr_result.get("merchant_name")
        
        # Keep the OCR-based comparison as a second line of defence for legacy
        # receipts uploaded before content hashes were available.
        for existing in report.receipts:
            if existing.file_name == file.filename:
                raise HTTPException(
                    status_code=400,
                    detail=f"Duplicate receipt error: File '{file.filename}' has already been uploaded to this report."
                )
            if (
                merchant 
                and merchant != "Unknown Merchant" 
                and merchant != "Unknown"
                and existing.merchant_name == merchant
                and parsed_date is not None
                and existing.receipt_date == parsed_date
                and ocr_amount > Decimal("0.00")
                and (existing.ocr_amount == ocr_amount or existing.verified_amount == ocr_amount)
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"Duplicate receipt error: Receipt from '{merchant}' dated {parsed_date} for ${ocr_amount} already exists on this report."
                )

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
            merchant_name=merchant,
            receipt_date=parsed_date,
            category=ocr_result.get("category"),
            ocr_amount=ocr_amount,
            verified_amount=verified_amount,
            image_path=f"/uploads/receipts/{unique_name}",
            file_name=file.filename,
            content_hash=content_hash,
            ocr_confidence=confidence,
            ocr_json=safe_ocr_result
        )
        await repo.add_receipt(receipt)
        _log_action(current_user, "receipt_uploaded_ocr_completed", receipt.receipt_id)
        created_receipts.append(receipt)
        total_added += verified_amount
        
      # Update total report amount
      report.total_amount += total_added
      await repo.update_report(report)
      await db.commit()
      return created_receipts
    except HTTPException:
      await db.rollback()
      for path in written_paths:
          _remove_uploaded_file(path)
      raise
    except IntegrityError:
      await db.rollback()
      for path in written_paths:
          _remove_uploaded_file(path)
      _log_action(current_user, "receipt_duplicate_detected", report_id, level=logging.WARNING)
      raise HTTPException(status_code=409, detail="Duplicate receipt detected in this reimbursement report.")
    except Exception:
      await db.rollback()
      for path in written_paths:
          _remove_uploaded_file(path)
      _log_action(current_user, "receipt_upload_failed", report_id, level=logging.ERROR)
      logger.exception("Receipt upload/OCR failed")
      raise HTTPException(status_code=500, detail="Unable to upload and process receipt")

@router.delete("/{report_id}")
async def delete_expense_report(
    report_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    report = await _get_owned_editable_report(repo, report_id, current_user)
    image_paths = [receipt.image_path for receipt in report.receipts]
    await repo.delete_report(report)
    await db.commit()
    for image_path in image_paths:
        _remove_uploaded_file(image_path)
    _log_action(current_user, "expense_draft_deleted", report_id)
    return {"status": "success", "message": "Draft report deleted successfully"}

@router.put("/{report_id}", response_model=ExpenseReportResponse)
async def update_expense_report(
    report_id: int,
    payload: ExpenseReportUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    repo = ExpenseRepository(db)
    report = await _get_owned_editable_report(repo, report_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(report, field, value)
    await repo.update_report(report)
    await db.commit()
    _log_action(current_user, "expense_draft_updated", report_id)
    return report

@router.put("/{report_id}/receipts/{receipt_id}", response_model=ReceiptResponse)
async def update_receipt(
    report_id: int,
    receipt_id: int,
    payload: ReceiptUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    report = await _get_owned_editable_report(repo, report_id, current_user)
        
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
    _log_action(current_user, "receipt_verified_updated", receipt_id)
    return receipt
    
@router.delete("/{report_id}/receipts/{receipt_id}")
async def delete_receipt(
    report_id: int,
    receipt_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    repo = ExpenseRepository(db)
    report = await _get_owned_editable_report(repo, report_id, current_user)
        
    receipt = await repo.get_receipt_by_id(receipt_id)
    if not receipt or receipt.expense_report_id != report_id:
        raise HTTPException(status_code=404, detail="Receipt not found")
        
    report.total_amount -= receipt.verified_amount
    await repo.delete_receipt(receipt)
    await repo.update_report(report)
    await db.commit()
    _remove_uploaded_file(receipt.image_path)
    _log_action(current_user, "receipt_ocr_deleted", receipt_id)
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
    report = await _get_owned_editable_report(repo, report_id, current_user)
    if not report.receipts:
        _log_action(current_user, "expense_submission_validation_failed", report_id, level=logging.WARNING)
        raise HTTPException(status_code=400, detail="Add at least one receipt before submitting the report.")
    if not report.justification or not report.justification.strip():
        _log_action(current_user, "expense_submission_validation_failed", report_id, level=logging.WARNING)
        raise HTTPException(status_code=400, detail="Description / Justification is required")

    # Validate that all receipts have been verified (no 0.00 amounts unless it's a legit 0 receipt)
    for r in report.receipts:
        if r.verified_amount == Decimal("0.00") and r.ocr_confidence and r.ocr_confidence < Decimal("50.00"):
            _log_action(current_user, "expense_submission_validation_failed", report_id, level=logging.WARNING)
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
                _log_action(current_user, "receipt_duplicate_detected_across_reports", report_id, level=logging.WARNING)
                
        if r.verified_amount > Decimal("100.00") and not r.category:
            policy_issues.append(f"Receipt {r.file_name} > $100 requires a category")
            
    report.duplicate_flag = duplicates_found
    report.policy_flags = ", ".join(policy_issues) if policy_issues else None
    
    is_manager = any(r.role_name == "Manager" for r in current_user.roles)
    if is_manager and policy_issues and not report.justification:
        _log_action(current_user, "expense_submission_validation_failed", report_id, level=logging.WARNING)
        raise HTTPException(status_code=400, detail="Policy violations found. Manager claims require justification.")
    # Transition status
    report.status = "Corrected Claim" if report.status == "Returned for Correction" else "Pending Manager Approval"
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
    except Exception:
        # If approval flow fails, we should probably revert status
        report.status = "Draft"
        await repo.update_report(report)
        await db.rollback()
        _log_action(current_user, "expense_submission_failed", report_id, level=logging.ERROR)
        logger.exception("Expense approval flow initialization failed")
        raise HTTPException(status_code=500, detail="Failed to initialize approval flow")

    await db.commit()
    _log_action(current_user, "expense_submitted", report_id)
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
        
    valid_statuses = [
        "Pending Manager Approval",
        "Pending Finance Manager Approval",
        "Pending Finance Approval",
        "Pending Finance Verification",
        "Pending Approval",
        "Corrected Claim"
    ]
    if report.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Report is not pending approval")
        
    query = select(ExpenseApproval).where(
        ExpenseApproval.expense_report_id == report_id,
        ExpenseApproval.approver_id == current_user.user_id,
        ExpenseApproval.status == "Pending"
    )
    result = await db.execute(query)
    approval = result.scalar_one_or_none()
    
    if not _can_act_on_pending_report(report, current_user, approval):
        _log_action(current_user, "expense_approval_denied", report_id, level=logging.WARNING)
        raise HTTPException(status_code=403, detail="Not authorized to approve this report")
        
    if approval:
        approval.status = "Approved"
        approval.comments = payload.comments
        approval.actioned_at = datetime.utcnow()
    else:
        # If acted on by manager/admin without explicit single-user assignment
        unassigned_query = select(ExpenseApproval).where(
            ExpenseApproval.expense_report_id == report_id,
            ExpenseApproval.status == "Pending"
        )
        unassigned_res = await db.execute(unassigned_query)
        unassigned = unassigned_res.scalar_one_or_none()
        if unassigned:
            unassigned.status = "Approved"
            unassigned.approver_id = current_user.user_id
            unassigned.comments = payload.comments
            unassigned.actioned_at = datetime.utcnow()
        
    roles = _roles(current_user)
    if report.status in ["Pending Manager Approval", "Corrected Claim", "Pending Approval"]:
        report.status = "Pending Finance Manager Approval"
        
        # Find a Finance Manager for next step
        fm_query = select(User).join(User.roles).where(Role.role_name.in_(["Finance Manager", "Finance", "CFO"]), User.status == "Active")
        fm_result = await db.execute(fm_query)
        finance_manager = fm_result.scalars().first()
        
        fm_approval = ExpenseApproval(
            expense_report_id=report.expense_report_id,
            approver_id=finance_manager.user_id if finance_manager else None,
            status="Pending"
        )
        db.add(fm_approval)
    else:
        # Final approval by Finance Manager / Finance / CFO / Admin
        report.status = "Approved"
        report.payment_status = "Payment Authorized"
        
    await repo.update_report(report)
    await db.commit()
    _log_action(current_user, "expense_approved", report_id)
    return {"status": "Approved", "new_report_status": report.status}

@router.post("/{report_id}/reject")
async def reject_expense(
    report_id: int,
    payload: ExpenseActionPayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if not payload.comments or not payload.comments.strip():
        raise HTTPException(status_code=400, detail="Justification is required for rejecting a claim")
        
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
    if not _can_act_on_pending_report(report, current_user, approval):
        _log_action(current_user, "expense_rejection_denied", report_id, level=logging.WARNING)
        raise HTTPException(status_code=403, detail="Not authorized to reject this report")
    if approval:
        approval.status = "Rejected"
        approval.comments = payload.comments
        approval.actioned_at = datetime.utcnow()
    else:
        unassigned_query = select(ExpenseApproval).where(
            ExpenseApproval.expense_report_id == report_id,
            ExpenseApproval.status == "Pending"
        )
        unassigned_res = await db.execute(unassigned_query)
        unassigned = unassigned_res.scalar_one_or_none()
        if unassigned:
            unassigned.status = "Rejected"
            unassigned.approver_id = current_user.user_id
            unassigned.comments = payload.comments
            unassigned.actioned_at = datetime.utcnow()
        
    report.status = "Rejected"
    await repo.update_report(report)
    await db.commit()
    _log_action(current_user, "expense_rejected", report_id)
    return {"status": "Rejected"}

@router.post("/{report_id}/return")
async def return_expense(
    report_id: int,
    payload: ExpenseActionPayload,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if not payload.comments or not payload.comments.strip():
        raise HTTPException(status_code=400, detail="Justification is required for returning a claim")
        
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
    if not _can_act_on_pending_report(report, current_user, approval):
        _log_action(current_user, "expense_return_denied", report_id, level=logging.WARNING)
        raise HTTPException(status_code=403, detail="Not authorized to return this report")
    if approval:
        approval.status = "Returned"
        approval.comments = payload.comments
        approval.actioned_at = datetime.utcnow()
    else:
        unassigned_query = select(ExpenseApproval).where(
            ExpenseApproval.expense_report_id == report_id,
            ExpenseApproval.status == "Pending"
        )
        unassigned_res = await db.execute(unassigned_query)
        unassigned = unassigned_res.scalar_one_or_none()
        if unassigned:
            unassigned.status = "Returned"
            unassigned.approver_id = current_user.user_id
            unassigned.comments = payload.comments
            unassigned.actioned_at = datetime.utcnow()
        
    report.status = "Returned for Correction"
    await repo.update_report(report)
    await db.commit()
    _log_action(current_user, "expense_returned", report_id)
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
    if not _roles(current_user) & {"Finance Manager", "Finance", "CFO", "Admin", "CEO"}:
        _log_action(current_user, "expense_payment_denied", report_id, level=logging.WARNING)
        raise HTTPException(status_code=403, detail="Not authorized to authorize payment")
        
    report.status = "Closed"
    report.payment_status = "Paid"
    report.payment_reference = f"PAY-EXP-{report_id}-{uuid.uuid4().hex[:6]}"
    await repo.update_report(report)
    await db.commit()
    _log_action(current_user, "expense_paid", report_id)
    return {"status": "Paid", "reference": report.payment_reference, "payment_reference": report.payment_reference}
