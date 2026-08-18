from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, String, Text, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    payment_request_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("vendor_invoices.invoice_id", ondelete="CASCADE"), nullable=True)
    expense_report_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("expense_reports.expense_report_id", ondelete="CASCADE"), nullable=True)
    po_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("purchase_orders.po_id", ondelete="SET NULL"), nullable=True)
    request_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(10), default="USD")
    status: Mapped[Optional[str]] = mapped_column(String(50), default="Pending") # Pending, Hold, Approved, Paid, Rejected
    payment_readiness_passed: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    invoice: Mapped[Optional["VendorInvoice"]] = relationship("VendorInvoice")
    expense_report: Mapped[Optional["ExpenseReport"]] = relationship("ExpenseReport")
    po: Mapped[Optional["PurchaseOrder"]] = relationship("PurchaseOrder")
    approvals: Mapped[List["PaymentApproval"]] = relationship("PaymentApproval", back_populates="payment_request", cascade="all, delete-orphan")


class PaymentApproval(Base):
    __tablename__ = "payment_approvals"

    approval_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    payment_request_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("payment_requests.payment_request_id", ondelete="CASCADE"))
    approver_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # Approved, Rejected, Hold
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    payment_request: Mapped["PaymentRequest"] = relationship("PaymentRequest", back_populates="approvals")
    approver: Mapped[Optional["User"]] = relationship("User")
