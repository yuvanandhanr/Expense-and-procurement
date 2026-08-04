from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, String, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class ThreeWayMatching(Base):
    __tablename__ = "three_way_matching"

    matching_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vendor_invoices.invoice_id", ondelete="CASCADE"))
    po_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("purchase_orders.po_id", ondelete="SET NULL"), nullable=True)
    grn_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("goods_receipts.grn_id", ondelete="SET NULL"), nullable=True)
    item_match_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    quantity_match_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    price_match_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tax_match_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    currency_match_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    total_amount_match_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    variance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    match_result: Mapped[str] = mapped_column(String(50), nullable=False) # Matched, Matched with Variance, Mismatch, Rejected, Manual Review Required
    inspected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    invoice: Mapped["VendorInvoice"] = relationship("VendorInvoice")
    po: Mapped[Optional["PurchaseOrder"]] = relationship("PurchaseOrder")
    grn: Mapped[Optional["GoodsReceipt"]] = relationship("GoodsReceipt")
