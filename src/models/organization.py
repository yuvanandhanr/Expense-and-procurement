from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


class Department(Base):
    """
    SQLAlchemy Model for the public.departments table.
    """
    __tablename__ = "departments"

    department_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for departments"
    )
    department_name: Mapped[str] = mapped_column(
        String, nullable=False, comment="Name of the department"
    )
    department_code: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, comment="Unique department identifier code"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Detailed description of the department"
    )
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=True, comment="Department status"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="department", foreign_keys="[User.department_id]"
    )
    cost_centers: Mapped[List["CostCenter"]] = relationship(
        "CostCenter", back_populates="department", cascade="all, delete-orphan"
    )
    budget_codes: Mapped[List["BudgetCode"]] = relationship(
        "BudgetCode", back_populates="department"
    )


class Designation(Base):
    """
    SQLAlchemy Model for the public.designations table.
    """
    __tablename__ = "designations"

    designation_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for designations"
    )
    designation_name: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, comment="Name of the designation"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Description of the designation"
    )
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=True, comment="Status of the designation"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="designation_rel"
    )


class CostCenter(Base):
    """
    SQLAlchemy Model for the public.cost_centres table.
    """
    __tablename__ = "cost_centres"

    cost_center_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for cost centers"
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("departments.department_id"), nullable=True, comment="Parent department reference"
    )
    cost_center_name: Mapped[str] = mapped_column(
        String, nullable=False, comment="Name of the cost center"
    )
    budget_limit: Mapped[float] = mapped_column(
        Numeric(precision=15, scale=2), nullable=False, comment="Assigned budget limit"
    )
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=True, comment="Cost center status"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )

    # Relationships
    department: Mapped[Optional[Department]] = relationship(
        "Department", back_populates="cost_centers"
    )
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="cost_center", foreign_keys="[User.cost_center_id]"
    )
    budget_codes: Mapped[List["BudgetCode"]] = relationship(
        "BudgetCode", back_populates="cost_center"
    )


class BudgetCode(Base):
    """
    SQLAlchemy Model for the public.budget_codes table.
    """
    __tablename__ = "budget_codes"

    budget_code_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for budget codes"
    )
    budget_code: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, comment="Budget code string identifier"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Detailed description of budget usage"
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("departments.department_id"), nullable=True, comment="Associated department"
    )
    cost_center_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("cost_centres.cost_center_id"), nullable=True, comment="Associated cost center"
    )
    annual_budget: Mapped[float] = mapped_column(
        Numeric(precision=15, scale=2), default=0.00, nullable=True, comment="Total annual allocated budget"
    )
    available_budget: Mapped[float] = mapped_column(
        Numeric(precision=15, scale=2), default=0.00, nullable=True, comment="Remaining available budget"
    )
    fiscal_year: Mapped[str] = mapped_column(
        String, nullable=False, comment="Fiscal year (e.g. FY2026)"
    )
    status: Mapped[str] = mapped_column(
        String, default="Active", nullable=True, comment="Status (Active/Inactive)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )

    # Relationships
    department: Mapped[Optional[Department]] = relationship(
        "Department", back_populates="budget_codes"
    )
    cost_center: Mapped[Optional[CostCenter]] = relationship(
        "CostCenter", back_populates="budget_codes"
    )


class OrgSettings(Base):
    """
    SQLAlchemy Model for the public.organization_settings table.
    """
    __tablename__ = "organization_settings"

    settings_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Primary key for settings"
    )
    org_name: Mapped[str] = mapped_column(
        String, nullable=False, comment="Registered name of the organization"
    )
    currency: Mapped[str] = mapped_column(
        String, default="USD", nullable=True, comment="Primary operating currency"
    )
    timezone: Mapped[str] = mapped_column(
        String, default="UTC", nullable=True, comment="Primary operating timezone"
    )
    fiscal_year_start: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Start date of fiscal year"
    )
    fiscal_year_end: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="End date of fiscal year"
    )
    approval_thresholds: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="Threshold configuration mapping roles to approval limits"
    )
    password_policy: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="Password validation constraints policy"
    )
    session_timeout_minutes: Mapped[int] = mapped_column(
        BigInteger, default=30, nullable=True, comment="Inactivity duration threshold before logout"
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, comment="URL referencing organization logo image"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )
