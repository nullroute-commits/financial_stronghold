"""Multi-tenancy extension for Financial Stronghold."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
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
