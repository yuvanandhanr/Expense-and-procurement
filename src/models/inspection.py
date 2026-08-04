from typing import Optional, List
from datetime import datetime
from sqlalchemy import BigInteger, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class InspectionReport(Base):
    __tablename__ = "inspection_reports"

    inspection_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("deliveries.delivery_id", ondelete="CASCADE"))
    inspected_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    inspection_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False) # Accepted, Accepted with Remarks, Rejected, Partial Acceptance, Replacement Requested
    inspection_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    damage_check_passed: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    specification_check_passed: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    quantity_verified: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    delivery: Mapped["Delivery"] = relationship("Delivery")
    inspector: Mapped[Optional["User"]] = relationship("User")
    items: Mapped[List["InspectionItem"]] = relationship("InspectionItem", back_populates="report", cascade="all, delete-orphan")


class InspectionItem(Base):
    __tablename__ = "inspection_items"

    inspection_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    inspection_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("inspection_reports.inspection_id", ondelete="CASCADE"))
    delivery_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("delivery_items.delivery_item_id", ondelete="CASCADE"))
    quantity_inspected: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity_accepted: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity_rejected: Mapped[int] = mapped_column(BigInteger, nullable=False)
    serial_numbers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    license_keys: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    report: Mapped["InspectionReport"] = relationship("InspectionReport", back_populates="items")
    delivery_item: Mapped["DeliveryItem"] = relationship("DeliveryItem")
