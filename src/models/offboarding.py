from typing import Optional, List
from datetime import timezone, datetime
from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base

class OffboardingTask(Base):
    __tablename__ = "offboarding_tasks"

    task_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("assets.asset_id", ondelete="SET NULL"), nullable=True)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False) # e.g., "Retrieve Asset", "Revoke Access"
    status: Mapped[str] = mapped_column(String(50), default="Pending") # Pending, Cleared
    cleared_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    cleared_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())
    
    employee = relationship("User", foreign_keys=[employee_id])
    asset = relationship("Asset", foreign_keys=[asset_id])
    clearer = relationship("User", foreign_keys=[cleared_by])
