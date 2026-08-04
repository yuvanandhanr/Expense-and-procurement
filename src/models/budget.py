from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class BudgetAllocation(Base):
    __tablename__ = "budget_allocations"

    allocation_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    budget_code_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("budget_codes.budget_code_id", ondelete="CASCADE"), nullable=False
    )
    allocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    spent_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), default=0.00
    )
    reserved_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), default=0.00
    )
    fiscal_year: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(20), default="Active"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    budget_code = relationship("BudgetCode")


class BudgetReservation(Base):
    __tablename__ = "budget_reservations"

    reservation_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    pr_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("purchase_requisitions.pr_id", ondelete="CASCADE"), nullable=False
    )
    budget_code_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("budget_codes.budget_code_id", ondelete="CASCADE"), nullable=False
    )
    reserved_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(50), default="Reserved"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    released_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    purchase_requisition = relationship("PurchaseRequisition", back_populates="reservations")
    budget_code = relationship("BudgetCode")
