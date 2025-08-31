"""Multi-tenancy extension for Financial Stronghold."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TenantInfo(BaseModel):
    """Base schema for tenant information."""

    tenant_type: str
    tenant_id: str


# Organization Schemas
class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationRead(OrganizationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Account Schemas
class AccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    account_type: str = Field(..., min_length=1, max_length=50)
    account_number: Optional[str] = Field(None, max_length=50)
    balance: Decimal = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    is_active: bool = True
    description: Optional[str] = None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    account_type: Optional[str] = Field(None, min_length=1, max_length=50)
    account_number: Optional[str] = Field(None, max_length=50)
    balance: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    is_active: Optional[bool] = None
    description: Optional[str] = None


class AccountRead(AccountBase, TenantInfo):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    description: Optional[str] = None
    transaction_type: str = Field(..., min_length=1, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    account_id: Optional[UUID] = None
    to_account_id: Optional[UUID] = None
    status: str = Field(default="completed", max_length=20)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    description: Optional[str] = None
    transaction_type: Optional[str] = Field(None, min_length=1, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    account_id: Optional[UUID] = None
    to_account_id: Optional[UUID] = None
    status: Optional[str] = Field(None, max_length=20)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = None


class TransactionRead(TransactionBase, TenantInfo):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Fee Schemas
class FeeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    fee_type: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    transaction_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    status: str = Field(default="active", max_length=20)
    frequency: Optional[str] = Field(None, max_length=20)


class FeeCreate(FeeBase):
    pass


class FeeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    fee_type: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    transaction_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    status: Optional[str] = Field(None, max_length=20)
    frequency: Optional[str] = Field(None, max_length=20)


class FeeRead(FeeBase, TenantInfo):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Budget Schemas
class BudgetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    total_amount: Decimal = Field(..., gt=0)
    spent_amount: Decimal = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    start_date: datetime
    end_date: datetime
    categories: Optional[str] = None
    is_active: bool = True
    alert_threshold: Optional[Decimal] = Field(None, ge=0, le=100)
    alert_enabled: bool = False


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    total_amount: Optional[Decimal] = Field(None, gt=0)
    spent_amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    categories: Optional[str] = None
    is_active: Optional[bool] = None
    alert_threshold: Optional[Decimal] = Field(None, ge=0, le=100)
    alert_enabled: Optional[bool] = None


class BudgetRead(BudgetBase, TenantInfo):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User Organization Link Schemas
class UserOrganizationLinkRead(BaseModel):
    user_id: UUID
    org_id: int
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class UserOrganizationLinkCreate(BaseModel):
    user_id: UUID
    role: str = "member"


class UserOrganizationLinkUpdate(BaseModel):
    role: str


# Dashboard Schemas
class AccountSummary(BaseModel):
    """Account summary for dashboard."""
    
    account_id: UUID
    name: str
    account_type: str
    balance: Decimal
    currency: str
    is_active: bool

    class Config:
        from_attributes = True


class TransactionSummary(BaseModel):
    """Transaction summary for dashboard."""
    
    total_transactions: int
    total_amount: Decimal
    avg_amount: Decimal
    currency: str
    recent_transactions: List['TransactionRead']

    class Config:
        from_attributes = True


class BudgetStatus(BaseModel):
    """Budget status for dashboard."""
    
    budget_id: UUID
    name: str
    total_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    percentage_used: Decimal
    is_over_budget: bool
    alert_threshold: Optional[Decimal]
    currency: str

    class Config:
        from_attributes = True


class FinancialSummary(BaseModel):
    """Complete financial summary for dashboard."""
    
    total_balance: Decimal
    total_accounts: int
    active_accounts: int
    total_transactions: int
    this_month_transactions: int
    this_month_amount: Decimal
    currency: str
    last_updated: datetime

    class Config:
        from_attributes = True


class DashboardData(BaseModel):
    """Complete dashboard data response."""
    
    financial_summary: FinancialSummary
    account_summaries: List[AccountSummary]
    transaction_summary: TransactionSummary
    budget_statuses: List[BudgetStatus]
    tenant_info: TenantInfo

    class Config:
        from_attributes = True
