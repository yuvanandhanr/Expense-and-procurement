from typing import Optional
from datetime import timezone, datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class PRAttachment(Base):
    __tablename__ = "pr_attachments"

    attachment_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    pr_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("purchase_requisitions.pr_id", ondelete="CASCADE"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    file_path: Mapped[str] = mapped_column(
        String(1024), nullable=False
    )
    file_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    file_size: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    uploaded_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=lambda: datetime.utcnow()
    )

    purchase_requisition = relationship("PurchaseRequisition", back_populates="attachments")
    uploader = relationship("User")
