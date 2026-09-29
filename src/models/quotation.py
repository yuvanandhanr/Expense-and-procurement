from typing import Optional, List
from datetime import timezone, datetime
from decimal import Decimal
from sqlalchemy import BigInteger, String, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class VendorQuotation(Base):
    __tablename__ = "vendor_quotations"

    quotation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    quotation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    rfq_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("request_for_quotations.rfq_id", ondelete="CASCADE"))
    vendor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="CASCADE"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00)
    currency: Mapped[Optional[str]] = mapped_column(String(10), default="USD")
    lead_time_days: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    warranty_months: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    technical_proposal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    commercial_proposal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    technical_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    commercial_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), default="Submitted")
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    # Relationships
    rfq: Mapped["RequestForQuotation"] = relationship("RequestForQuotation", back_populates="quotations")
    vendor: Mapped["Vendor"] = relationship("Vendor")
    items: Mapped[List["QuotationItem"]] = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")


class QuotationItem(Base):
    __tablename__ = "quotation_items"

    quotation_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendor_quotations.quotation_id", ondelete="CASCADE"))
    rfq_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rfq_items.rfq_item_id", ondelete="CASCADE"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00)
    total_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Relationships
    quotation: Mapped["VendorQuotation"] = relationship("VendorQuotation", back_populates="items")
    rfq_item: Mapped["RFQItem"] = relationship("RFQItem")


class QuotationComparison(Base):
    __tablename__ = "quotation_comparison"

    comparison_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rfq_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("request_for_quotations.rfq_id", ondelete="CASCADE"))
    winner_technical_quotation_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("vendor_quotations.quotation_id", ondelete="SET NULL"), nullable=True)
    winner_commercial_quotation_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("vendor_quotations.quotation_id", ondelete="SET NULL"), nullable=True)
    final_selected_vendor_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="SET NULL"), nullable=True)
    final_selected_quotation_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("vendor_quotations.quotation_id", ondelete="SET NULL"), nullable=True)
    selection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    actioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    # Relationships
    rfq: Mapped["RequestForQuotation"] = relationship("RequestForQuotation")
    winner_technical: Mapped[Optional["VendorQuotation"]] = relationship("VendorQuotation", foreign_keys=[winner_technical_quotation_id])
    winner_commercial: Mapped[Optional["VendorQuotation"]] = relationship("VendorQuotation", foreign_keys=[winner_commercial_quotation_id])
    final_selected_vendor: Mapped[Optional["Vendor"]] = relationship("Vendor")
    final_selected_quotation: Mapped[Optional["VendorQuotation"]] = relationship("VendorQuotation", foreign_keys=[final_selected_quotation_id])
    approver: Mapped[Optional["User"]] = relationship("User")
