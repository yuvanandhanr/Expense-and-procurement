from typing import Optional, List
from datetime import timezone, datetime
from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class RequestForQuotation(Base):
    __tablename__ = "request_for_quotations"

    rfq_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rfq_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    pr_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("purchase_requisitions.pr_id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), default="Draft")
    submission_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closing_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.utcnow())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    # Relationships
    pr: Mapped[Optional["PurchaseRequisition"]] = relationship("PurchaseRequisition", lazy="selectin")
    creator: Mapped[Optional["User"]] = relationship("User")
    items: Mapped[List["RFQItem"]] = relationship("RFQItem", back_populates="rfq", cascade="all, delete-orphan")
    rfq_vendors: Mapped[List["RFQVendor"]] = relationship("RFQVendor", back_populates="rfq", cascade="all, delete-orphan")
    quotations: Mapped[List["VendorQuotation"]] = relationship("VendorQuotation", back_populates="rfq", cascade="all, delete-orphan")

    @property
    def pr_description(self) -> Optional[str]:
        return self.pr.description if self.pr else None

    @property
    def pr_justification(self) -> Optional[str]:
        return self.pr.justification if self.pr else None

    @property
    def pr_project_code(self) -> Optional[str]:
        return self.pr.project_code if self.pr else None

    @property
    def pr_priority(self) -> Optional[str]:
        return self.pr.priority if self.pr else None


class RFQItem(Base):
    __tablename__ = "rfq_items"

    rfq_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rfq_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("request_for_quotations.rfq_id", ondelete="CASCADE"))
    pr_item_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("pr_items.pr_item_id", ondelete="SET NULL"), nullable=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quantity: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    rfq: Mapped["RequestForQuotation"] = relationship("RequestForQuotation", back_populates="items")


class RFQVendor(Base):
    __tablename__ = "rfq_vendors"

    rfq_vendor_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rfq_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("request_for_quotations.rfq_id", ondelete="CASCADE"))
    vendor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="CASCADE"))
    invited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.utcnow())

    # Relationships
    rfq: Mapped["RequestForQuotation"] = relationship("RequestForQuotation", back_populates="rfq_vendors")
    vendor: Mapped["Vendor"] = relationship("Vendor")
