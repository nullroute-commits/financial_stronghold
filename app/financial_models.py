"""Multi-tenancy extension for Financial Stronghold."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import Column, DateTime, String, Integer, Text, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.db.connection import Base
from app.core.models import BaseModel
from app.core.tenant import TenantMixin


class Account(BaseModel, TenantMixin):
    """Financial account model with tenant scoping."""

    __tablename__ = "accounts"

    name = Column(String(120), nullable=False)
    account_type = Column(String(50), nullable=False)  # checking, savings, credit, investment, etc.
    account_number = Column(String(50), nullable=True)
    balance = Column(Numeric(12, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="USD")
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Account(id={self.id}, name={self.name}, type={self.account_type}, balance={self.balance})>"


class Transaction(BaseModel, TenantMixin):
    """Financial transaction model with tenant scoping."""

    __tablename__ = "transactions"

    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    description = Column(Text, nullable=True)
    transaction_type = Column(String(50), nullable=False)  # debit, credit, transfer, etc.
    reference_number = Column(String(100), nullable=True)

    # Account association
    account_id = Column(UUID(as_uuid=True), nullable=True)

    # For transfers - could be to another account or external
    to_account_id = Column(UUID(as_uuid=True), nullable=True)

    # Status tracking
    status = Column(String(20), nullable=False, default="completed")  # pending, completed, failed, cancelled

    # Categorization
    category = Column(String(100), nullable=True)
    tags = Column(Text, nullable=True)  # JSON or comma-separated

    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, type={self.transaction_type}, status={self.status})>"


class Fee(BaseModel, TenantMixin):
    """Fee model for tracking various fees with tenant scoping."""

    __tablename__ = "fees"

    name = Column(String(120), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    fee_type = Column(String(50), nullable=False)  # monthly, transaction, overdraft, etc.
    description = Column(Text, nullable=True)

    # Optional association to transaction
    transaction_id = Column(UUID(as_uuid=True), nullable=True)

    # Optional association to account
    account_id = Column(UUID(as_uuid=True), nullable=True)

    # Status
    status = Column(String(20), nullable=False, default="active")  # active, waived, refunded

    # Frequency for recurring fees
    frequency = Column(String(20), nullable=True)  # monthly, yearly, per_transaction

    def __repr__(self):
        return f"<Fee(id={self.id}, name={self.name}, amount={self.amount}, type={self.fee_type})>"


class Budget(BaseModel, TenantMixin):
    """Budget tracking model with tenant scoping."""

    __tablename__ = "budgets"

    name = Column(String(120), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    spent_amount = Column(Numeric(12, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="USD")

    # Time period
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    # Categories this budget applies to
    categories = Column(Text, nullable=True)  # JSON or comma-separated

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Alert settings
    alert_threshold = Column(Numeric(5, 2), nullable=True)  # percentage (e.g., 80 for 80%)
    alert_enabled = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Budget(id={self.id}, name={self.name}, total={self.total_amount}, spent={self.spent_amount})>"
