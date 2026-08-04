from typing import Optional, List
from datetime import datetime
from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class Delivery(Base):
    __tablename__ = "deliveries"

    delivery_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    po_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("purchase_orders.po_id", ondelete="CASCADE"))
    vendor_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="CASCADE"))
    delivery_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expected_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), default="Pending") # Pending, Scheduled, In Transit, Delivered, Partially Delivered, Rejected, Returned, Completed
    delivery_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    po: Mapped["PurchaseOrder"] = relationship("PurchaseOrder")
    vendor: Mapped["Vendor"] = relationship("Vendor")
    items: Mapped[List["DeliveryItem"]] = relationship("DeliveryItem", back_populates="delivery", cascade="all, delete-orphan")


class DeliveryItem(Base):
    __tablename__ = "delivery_items"

    delivery_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("deliveries.delivery_id", ondelete="CASCADE"))
    po_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("purchase_order_items.po_item_id", ondelete="CASCADE"))
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_shipped: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    delivery: Mapped["Delivery"] = relationship("Delivery", back_populates="items")
    po_item: Mapped["PurchaseOrderItem"] = relationship("PurchaseOrderItem")
