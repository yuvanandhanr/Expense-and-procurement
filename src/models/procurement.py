from typing import Optional
from datetime import timezone, datetime
from sqlalchemy import BigInteger, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class ProcurementClosure(Base):
    __tablename__ = "procurement_closure"

    closure_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    po_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("purchase_orders.po_id", ondelete="CASCADE"), unique=True)
    closed_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.utcnow())
    po_completed: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    grn_completed: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    invoice_approved: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    payment_approved: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    assets_registered: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    audit_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    po: Mapped["PurchaseOrder"] = relationship("PurchaseOrder")
    closer: Mapped[Optional["User"]] = relationship("User")
