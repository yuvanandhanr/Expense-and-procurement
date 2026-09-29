from typing import Optional, List
from datetime import timezone, datetime, date
from decimal import Decimal
from sqlalchemy import BigInteger, String, Numeric, DateTime, Date, ForeignKey, Text, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class ExpenseReport(Base):
    __tablename__ = "expense_reports"

    expense_report_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"))
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("departments.department_id", ondelete="SET NULL"), nullable=True)
    cost_center_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("cost_centres.cost_center_id", ondelete="SET NULL"), nullable=True)
    project_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Draft") # Draft, Submitted, Pending Approval, Approved, Finance Verified, Payment Requested, Closed
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    duplicate_flag: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    policy_flags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    employee: Mapped["User"] = relationship("User", foreign_keys=[employee_id])
    department: Mapped[Optional["Department"]] = relationship("Department")
    cost_center: Mapped[Optional["CostCenter"]] = relationship("CostCenter")
    receipts: Mapped[List["Receipt"]] = relationship("Receipt", back_populates="expense_report", cascade="all, delete-orphan")
    approvals: Mapped[List["ExpenseApproval"]] = relationship("ExpenseApproval", back_populates="expense_report", cascade="all, delete-orphan")
    workflow_history: Mapped[List["ApprovalWorkflow"]] = relationship(
        "ApprovalWorkflow",
        primaryjoin="ExpenseReport.expense_report_id == foreign(ApprovalWorkflow.claim_id)",
        viewonly=True,
    )


class Receipt(Base):
    __tablename__ = "receipts"
    __table_args__ = (
        UniqueConstraint("expense_report_id", "content_hash", name="uq_receipt_report_content_hash"),
    )

    receipt_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    expense_report_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("expense_reports.expense_report_id", ondelete="CASCADE"))
    merchant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    receipt_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    receipt_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # Travel, Meals, Office Supplies, etc.
    ocr_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    verified_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    tax: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # SHA-256 of the uploaded bytes.  It is intentionally not exposed to clients.
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ocr_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True) # 0.00 to 100.00
    ocr_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    expense_report: Mapped["ExpenseReport"] = relationship("ExpenseReport", back_populates="receipts")


class ExpenseApproval(Base):
    __tablename__ = "expense_approvals"

    approval_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    expense_report_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("expense_reports.expense_report_id", ondelete="CASCADE"))
    approver_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # Pending, Approved, Rejected
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    expense_report: Mapped["ExpenseReport"] = relationship("ExpenseReport", back_populates="approvals")
    approver: Mapped[Optional["User"]] = relationship("User")
