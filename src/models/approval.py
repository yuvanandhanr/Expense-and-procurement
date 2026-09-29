from typing import Optional, List
from datetime import timezone, datetime
from decimal import Decimal
from sqlalchemy import BigInteger, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class ApprovalMatrix(Base):
    __tablename__ = "approval_matrix"

    matrix_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="Primary key for matrix rule"
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("departments.department_id", ondelete="SET NULL"), nullable=True
    )
    cost_center_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("cost_centres.cost_center_id", ondelete="SET NULL"), nullable=True
    )
    purchase_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    min_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=0.00
    )
    max_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=99999999.99
    )
    approval_level: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("roles.role_id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.utcnow()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow()
    )

    department = relationship("Department")
    cost_center = relationship("CostCenter")
    role = relationship("Role")


class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"

    workflow_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    pr_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("purchase_requisitions.pr_id", ondelete="CASCADE"), nullable=True
    )
    claim_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("expense_reports.expense_report_id", ondelete="CASCADE"), nullable=True
    )
    po_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("purchase_orders.po_id", ondelete="CASCADE"), nullable=True
    )
    invoice_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("vendor_invoices.invoice_id", ondelete="CASCADE"), nullable=True
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(50), default="Under Review"
    )

    __table_args__ = (
        CheckConstraint(
            """
            (
                (CASE WHEN claim_id IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN pr_id IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN po_id IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN invoice_id IS NOT NULL THEN 1 ELSE 0 END)
            ) = 1
            """,
            name="check_exclusive_workflow_ownership"
        ),
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.utcnow()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow()
    )

    purchase_requisition = relationship(
        "PurchaseRequisition", 
        back_populates="workflows"
    )
    steps: Mapped[List["ApprovalStep"]] = relationship(
        "ApprovalStep", back_populates="workflow", cascade="all, delete-orphan"
    )


class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    step_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    workflow_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("approval_workflows.workflow_id", ondelete="CASCADE"), nullable=True
    )
    step_number: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    approver_role_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("roles.role_id", ondelete="SET NULL"), nullable=True
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(50), default="Pending"
    )
    actioned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    workflow = relationship("ApprovalWorkflow", back_populates="steps")
    approver_role = relationship("Role")
    approver = relationship("User")
    history_records = relationship(
        "ApprovalHistory", back_populates="step", cascade="all, delete-orphan"
    )


class WorkflowHistory(Base):
    __tablename__ = "workflow_history"

    history_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    pr_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("purchase_requisitions.pr_id", ondelete="CASCADE"), nullable=True
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    performed_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    from_status: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    to_status: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    comments: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.utcnow()
    )

    purchase_requisition = relationship("PurchaseRequisition", back_populates="history")
    user = relationship("User")


class ApprovalHistory(Base):
    __tablename__ = "approval_history"

    history_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    step_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("approval_steps.step_id", ondelete="CASCADE"), nullable=True
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    performed_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    comments: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.utcnow()
    )

    step = relationship("ApprovalStep", back_populates="history_records")
    user = relationship("User")


class ApprovalComment(Base):
    __tablename__ = "approval_comments"

    comment_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    pr_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("purchase_requisitions.pr_id", ondelete="CASCADE"), nullable=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    parent_comment_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("approval_comments.comment_id", ondelete="CASCADE"), nullable=True
    )
    is_internal: Mapped[Optional[bool]] = mapped_column(
        Boolean, default=False
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.utcnow()
    )

    purchase_requisition = relationship("PurchaseRequisition", back_populates="comments")
    user = relationship("User")
    parent = relationship("ApprovalComment", remote_side=[comment_id])
    replies: Mapped[List["ApprovalComment"]] = relationship(
        "ApprovalComment", cascade="all, delete-orphan"
    )
