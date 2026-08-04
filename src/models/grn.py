from typing import Optional, List
from datetime import datetime
from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"

    grn_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    grn_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    po_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("purchase_orders.po_id", ondelete="SET NULL"), nullable=True)
    vendor_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("vendors.vendor_id", ondelete="SET NULL"), nullable=True)
    delivery_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("deliveries.delivery_id", ondelete="SET NULL"), nullable=True)
    inspection_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("inspection_reports.inspection_id", ondelete="SET NULL"), nullable=True)
    warehouse: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    received_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    received_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[Optional[str]] = mapped_column(String(50), default="Pending") # Pending, Partial, Completed, Rejected
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    po: Mapped[Optional["PurchaseOrder"]] = relationship("PurchaseOrder")
    vendor: Mapped[Optional["Vendor"]] = relationship("Vendor")
    delivery: Mapped[Optional["Delivery"]] = relationship("Delivery")
    inspection: Mapped[Optional["InspectionReport"]] = relationship("InspectionReport")
    receiver: Mapped[Optional["User"]] = relationship("User")
    items: Mapped[List["GoodsReceiptItem"]] = relationship("GoodsReceiptItem", back_populates="goods_receipt", cascade="all, delete-orphan")


class GoodsReceiptItem(Base):
    __tablename__ = "goods_receipt_items"

    grn_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    grn_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("goods_receipts.grn_id", ondelete="CASCADE"))
    delivery_item_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("delivery_items.delivery_item_id", ondelete="SET NULL"), nullable=True)
    quantity_received: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity_rejected: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    goods_receipt: Mapped["GoodsReceipt"] = relationship("GoodsReceipt", back_populates="items")
    delivery_item: Mapped[Optional["DeliveryItem"]] = relationship("DeliveryItem")
