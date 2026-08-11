from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import BigInteger, String, Text, Numeric, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class VendorInvoice(Base):
    __tablename__ = "vendor_invoices"

    invoice_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="CASCADE"))
    po_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("purchase_orders.po_id", ondelete="SET NULL"), nullable=True)
    grn_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("goods_receipts.grn_id", ondelete="SET NULL"), nullable=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), default="USD")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    taxes: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    discount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(50), default="Draft") # Draft, Submitted, Validated, Approved, Rejected, Paid, Cancelled
    employee_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    cause: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    asset_serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("vendor_id", "invoice_number", name="unique_vendor_invoice"),
    )

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor")
    po: Mapped[Optional["PurchaseOrder"]] = relationship("PurchaseOrder")
    grn: Mapped[Optional["GoodsReceipt"]] = relationship("GoodsReceipt")
    employee: Mapped[Optional["User"]] = relationship("User")
    items: Mapped[List["InvoiceItem"]] = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    documents: Mapped[List["InvoiceDocument"]] = relationship("InvoiceDocument", back_populates="invoice", cascade="all, delete-orphan")
    approvals: Mapped[List["InvoiceApproval"]] = relationship("InvoiceApproval", back_populates="invoice", cascade="all, delete-orphan")

    @property
    def vendor_name(self) -> str:
        if self.vendor:
            return self.vendor.vendor_name
        return "Unknown"


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    invoice_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendor_invoices.invoice_id", ondelete="CASCADE"))
    po_item_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("purchase_order_items.po_item_id", ondelete="SET NULL"), nullable=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(BigInteger, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Relationship
    invoice: Mapped["VendorInvoice"] = relationship("VendorInvoice", back_populates="items")
    po_item: Mapped[Optional["PurchaseOrderItem"]] = relationship("PurchaseOrderItem")


class InvoiceDocument(Base):
    __tablename__ = "invoice_documents"

    document_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendor_invoices.invoice_id", ondelete="CASCADE"))
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    invoice: Mapped["VendorInvoice"] = relationship("VendorInvoice", back_populates="documents")


class InvoiceApproval(Base):
    __tablename__ = "invoice_approval"

    approval_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendor_invoices.invoice_id", ondelete="CASCADE"))
    approver_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # Approved, Rejected
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    invoice: Mapped["VendorInvoice"] = relationship("VendorInvoice", back_populates="approvals")
    approver: Mapped[Optional["User"]] = relationship("User")
