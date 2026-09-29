"""
Base Model Definition.

Contains the SQLAlchemy declarative base and the standard abstract model containing
primary key (UUID) and auditing timestamps.
"""

import uuid
from datetime import timezone, datetime
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Declarative Base for all project entities.
    """
    pass


class AuditedModel(Base):
    """
    Abstract base model carrying UUID primary key and standard auditing details.
    
    Automatically tracks creation and last update timestamps in UTC.
    """
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the record"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp representing when the record was created"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp representing when the record was last updated"
    )
