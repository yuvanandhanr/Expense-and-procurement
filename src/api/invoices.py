from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import os
import uuid
from decimal import Decimal
from fastapi.responses import FileResponse

from src.database.dependency import get_db_session
from src.auth.dependencies import get_current_user
from src.models.auth import User, Role
from src.models.invoice import VendorInvoice, InvoiceDocument, InvoiceApproval
from src.schemas.invoice import InvoiceSchema, InvoiceUpdate
from src.services.ocr import OCRService
from src.models.approval import ApprovalWorkflow, ApprovalStep

router = APIRouter(prefix="/invoices", tags=["Invoices"])

async def get_role_by_name(session: AsyncSession, role_name: str) -> Optional[Role]:
    stmt = select(Role).where(Role.role_name == role_name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_role_if_not_exists(session: AsyncSession, role_name: str) -> Role:
    role = await get_role_by_name(session, role_name)
    if not role:
        role = Role(role_name=role_name, status=True)
        session.add(role)
        await session.flush()
    return role

@router.get("", response_model=List[InvoiceSchema])
async def get_invoices(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.orm import selectinload
    stmt = select(VendorInvoice).options(
        selectinload(VendorInvoice.items),
        selectinload(VendorInvoice.documents),
        selectinload(VendorInvoice.approvals)
    ).order_by(VendorInvoice.created_at.desc())
    
    # RBAC: Strict data isolation
    is_manager_or_admin = False
    is_vendor = False
    
    if current_user.roles:
        for role in current_user.roles:
            if role.role_name in ["Manager", "Finance Manager", "CFO", "Admin"]:
                is_manager_or_admin = True
            elif role.role_name == "Vendor Portal":
                is_vendor = True

    if is_vendor and not is_manager_or_admin:
        from src.models.vendor import Vendor
        vendor_stmt = select(Vendor.vendor_id).where(Vendor.email == current_user.email)
        vendor_result = await session.execute(vendor_stmt)
        vendor_id = vendor_result.scalar_one_or_none()
        if vendor_id:
            # Vendors see only their vendor invoices (not internal employee reimbursements)
            stmt = stmt.where(
                (VendorInvoice.vendor_id == vendor_id) & 
                (VendorInvoice.employee_id.is_(None))
            )
        else:
            stmt = stmt.where(VendorInvoice.invoice_id == -1) # return none
            
    elif not is_manager_or_admin:
        # Employees see only their own reimbursements/invoices
        stmt = stmt.where(VendorInvoice.employee_id == current_user.user_id)
        
    result = await session.execute(stmt)
    return result.scalars().all()

@router.post("/upload-batch", response_model=List[InvoiceSchema])
async def upload_invoice_batch(
    files: List[UploadFile] = File(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    saved_invoices = []
    
    for file in files:
        if not file.content_type.startswith("image/"):
            continue

        content = await file.read()
        ocr_result = OCRService.process_invoice_image(content)
        grand_total = ocr_result.get("total", Decimal("0.00"))
        cause = ocr_result.get("cause", "General Expense")
        invoice_date_str = ocr_result.get("date")
        
        from datetime import date
        try:
            if invoice_date_str:
                invoice_date = date.fromisoformat(invoice_date_str)
            else:
                invoice_date = date.today()
        except Exception:
            invoice_date = date.today()
        
        invoice_number = f"INV-{uuid.uuid4().hex[:6].upper()}"
        
        invoice = VendorInvoice(
            invoice_number=invoice_number,
            vendor_id=1,
            employee_id=current_user.user_id,
            cause=cause,
            invoice_date=invoice_date,
            subtotal=grand_total,
            grand_total=grand_total,
            status="Pending Approval"
        )
        
        session.add(invoice)
        await session.flush()
        
        # Save file to disk
        upload_dir = "/app/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{invoice.invoice_id}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(content)
            
        doc = InvoiceDocument(
            invoice_id=invoice.invoice_id,
            file_name=file.filename,
            file_path=file_path
        )
        session.add(doc)
        
        approval_role_name = None
        if grand_total > 10000:
            approval_role_name = "CFO"
        elif grand_total > 5000:
            approval_role_name = "Finance Manager"
        elif grand_total > 500:
            approval_role_name = "Manager"

        if approval_role_name:
            role = await create_role_if_not_exists(session, approval_role_name)
            from src.models.invoice import InvoiceApproval
            approval = InvoiceApproval(
                invoice_id=invoice.invoice_id,
                status="Pending",
                comments=f"Automated routing to {approval_role_name} due to amount {grand_total}"
            )
            session.add(approval)
        else:
            invoice.status = "Approved"

        await session.commit()
        
        from sqlalchemy.orm import selectinload
        stmt = select(VendorInvoice).options(
            selectinload(VendorInvoice.items),
            selectinload(VendorInvoice.documents),
            selectinload(VendorInvoice.approvals)
        ).where(VendorInvoice.invoice_id == invoice.invoice_id)
        
        result = await session.execute(stmt)
        final_invoice = result.scalar_one()
        saved_invoices.append(final_invoice)
        
    return saved_invoices

@router.post("/upload", response_model=InvoiceSchema)
async def upload_invoice(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported for OCR.")

    # Read image
    content = await file.read()
    
    # Process OCR
    grand_total = OCRService.process_invoice_image(content)
    
    # Generate mock vendor (or prompt user to select, but for now we default to a generic one or vendor_id 1)
    # Ideally, OCR could find vendor name too, but we keep it simple as requested.
    invoice_number = f"INV-{uuid.uuid4().hex[:6].upper()}"
    
    # Create Invoice record
    invoice = VendorInvoice(
        invoice_number=invoice_number,
        vendor_id=1, # Default vendor for demo purposes
        invoice_date=None, # Will default to now in DB if nullable, wait it's not nullable!
    )
    # Actually invoice_date is not nullable in model, we must provide it.
    from datetime import date
    invoice.invoice_date = date.today()
    invoice.subtotal = grand_total
    invoice.grand_total = grand_total
    invoice.status = "Pending Approval"
    
    session.add(invoice)
    await session.flush()
    
    # Determine Approval Routing
    approval_role_name = None
    if grand_total > 10000:
        approval_role_name = "CFO"
    elif grand_total > 5000:
        approval_role_name = "Finance Manager"
    elif grand_total > 500:
        approval_role_name = "Manager"

    if approval_role_name:
        # Get or create role
        role = await create_role_if_not_exists(session, approval_role_name)
        
        # We can reuse the ApprovalWorkflow but it usually ties to pr_id. 
        # For invoices, maybe there is an InvoiceApproval? Let's check models.
        # Yes, invoice.py has InvoiceApproval!
        from src.models.invoice import InvoiceApproval
        
        approval = InvoiceApproval(
            invoice_id=invoice.invoice_id,
            status="Pending",
            comments=f"Automated routing to {approval_role_name} due to amount {grand_total}"
        )
        session.add(approval)
    else:
        invoice.status = "Approved"

    await session.commit()
    
    from sqlalchemy.orm import selectinload
    stmt = select(VendorInvoice).options(
        selectinload(VendorInvoice.items),
        selectinload(VendorInvoice.documents),
        selectinload(VendorInvoice.approvals)
    ).where(VendorInvoice.invoice_id == invoice.invoice_id)
    
    result = await session.execute(stmt)
    final_invoice = result.scalar_one()
    
    return final_invoice


@router.patch("/{invoice_id}", response_model=InvoiceSchema)
async def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.orm import selectinload
    stmt = select(VendorInvoice).options(
        selectinload(VendorInvoice.items),
        selectinload(VendorInvoice.documents),
        selectinload(VendorInvoice.approvals)
    ).where(VendorInvoice.invoice_id == invoice_id)
    
    result = await session.execute(stmt)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    if invoice.employee_id != current_user.user_id and not any(r.role_name in ["Admin", "Manager", "Finance Manager", "CFO"] for r in current_user.roles):
        raise HTTPException(status_code=403, detail="Not authorized to update this invoice")
        
    if data.cause is not None:
        invoice.cause = data.cause
        
    if data.status is not None:
        invoice.status = data.status
        
    await session.commit()
    return invoice

@router.get("/{invoice_id}/document")
async def get_invoice_document(
    invoice_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(InvoiceDocument).where(InvoiceDocument.invoice_id == invoice_id)
    result = await session.execute(stmt)
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found for this invoice")
        
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File does not exist on disk")
        
    return FileResponse(path=doc.file_path, filename=doc.file_name)


@router.post("/{invoice_id}/{action}", response_model=InvoiceSchema)
async def approve_reject_invoice(
    invoice_id: int,
    action: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be approve or reject")
        
    user_roles = [r.role_name for r in current_user.roles]
    if not any(role in ["Manager", "Finance Manager", "CFO", "Admin"] for role in user_roles):
        raise HTTPException(status_code=403, detail="Not authorized to approve/reject invoices")

    from sqlalchemy.orm import selectinload
    stmt = select(VendorInvoice).options(
        selectinload(VendorInvoice.items),
        selectinload(VendorInvoice.documents),
        selectinload(VendorInvoice.approvals)
    ).where(VendorInvoice.invoice_id == invoice_id)
    
    result = await session.execute(stmt)
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    new_status = "Approved" if action == "approve" else "Rejected"
    invoice.status = new_status
    
    for approval in invoice.approvals:
        if approval.status == "Pending":
            approval.status = new_status
            approval.approver_id = current_user.user_id
            approval.comments = f"{new_status} by {current_user.first_name}"
            
    await session.commit()
    
    # Reload to return fresh object
    result = await session.execute(stmt)
    return result.scalar_one()

