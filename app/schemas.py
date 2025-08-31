"""Multi-tenancy extension for Financial Stronghold."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
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


# Tagging and Analytics Schemas
class DataTagBase(BaseModel):
    """Base schema for data tags."""
    
    tag_type: str = Field(..., description="Type of tag (user, organization, role, category, custom)")
    tag_key: str = Field(..., min_length=1, max_length=100, description="Tag key (e.g., user_id, org_id, role_id)")
    tag_value: str = Field(..., min_length=1, max_length=255, description="Tag value (the actual ID or value)")
    resource_type: str = Field(..., min_length=1, max_length=100, description="Resource type being tagged")
    resource_id: UUID = Field(..., description="ID of the resource being tagged")
    tag_label: Optional[str] = Field(None, max_length=255, description="Human-readable label")
    tag_description: Optional[str] = Field(None, description="Tag description")
    tag_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code")
    is_active: bool = Field(default=True, description="Whether tag is active")
    priority: int = Field(default=0, description="Priority for ordering tags")
    tag_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DataTagCreate(DataTagBase):
    """Schema for creating a data tag."""
    pass


class DataTagUpdate(BaseModel):
    """Schema for updating a data tag."""
    
    tag_label: Optional[str] = Field(None, max_length=255)
    tag_description: Optional[str] = None
    tag_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    tag_metadata: Optional[Dict[str, Any]] = None


class DataTagRead(DataTagBase, TenantInfo):
    """Schema for reading a data tag."""
    
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TagFilterRequest(BaseModel):
    """Schema for tag filter requests."""
    
    tag_filters: Dict[str, str] = Field(..., description="Tag filters as key-value pairs")
    resource_types: List[str] = Field(default=["transaction", "account", "budget"], description="Resource types to analyze")
    period_start: Optional[datetime] = Field(None, description="Start of analysis period")
    period_end: Optional[datetime] = Field(None, description="End of analysis period")


class ResourceMetrics(BaseModel):
    """Schema for resource metrics."""
    
    resource_type: str
    total_count: int
    total_amount: Optional[float] = None
    average_amount: Optional[float] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency_breakdown: Optional[Dict[str, Dict[str, Union[int, float]]]] = None
    type_breakdown: Optional[Dict[str, Dict[str, Union[int, float]]]] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    active_count: Optional[int] = None
    total_balance: Optional[float] = None
    average_balance: Optional[float] = None
    total_budget_amount: Optional[float] = None
    total_spent_amount: Optional[float] = None
    total_remaining: Optional[float] = None
    utilization_percentage: Optional[float] = None
    over_budget_count: Optional[int] = None
    error: Optional[str] = None
    message: Optional[str] = None


class AnalyticsSummary(BaseModel):
    """Schema for analytics summary response."""
    
    tenant_info: TenantInfo
    tag_filters: Dict[str, str]
    resource_metrics: Dict[str, ResourceMetrics]
    generated_at: str


class AnalyticsViewBase(BaseModel):
    """Base schema for analytics views."""
    
    view_name: str = Field(..., min_length=1, max_length=100)
    view_description: Optional[str] = None
    tag_filters: Dict[str, str] = Field(..., description="Tag filters for the view")
    resource_types: List[str] = Field(..., description="Resource types included in the view")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    cache_ttl_seconds: int = Field(default=3600, ge=0, description="Cache TTL in seconds")
    auto_refresh: bool = Field(default=True, description="Whether to auto-refresh the view")


class AnalyticsViewCreate(AnalyticsViewBase):
    """Schema for creating an analytics view."""
    pass


class AnalyticsViewUpdate(BaseModel):
    """Schema for updating an analytics view."""
    
    view_name: Optional[str] = Field(None, min_length=1, max_length=100)
    view_description: Optional[str] = None
    tag_filters: Optional[Dict[str, str]] = None
    resource_types: Optional[List[str]] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    cache_ttl_seconds: Optional[int] = Field(None, ge=0)
    auto_refresh: Optional[bool] = None


class AnalyticsViewRead(AnalyticsViewBase, TenantInfo):
    """Schema for reading an analytics view."""
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    metrics: Dict[str, Any]
    last_computed: Optional[datetime]
    computation_status: str
    is_active: bool

    class Config:
        from_attributes = True


class TagHierarchyBase(BaseModel):
    """Base schema for tag hierarchies."""
    
    parent_tag_id: UUID
    child_tag_id: UUID
    relationship_type: str = Field(default="parent_child", max_length=50)
    hierarchy_level: int = Field(default=1, ge=1)
    is_active: bool = Field(default=True)


class TagHierarchyCreate(TagHierarchyBase):
    """Schema for creating a tag hierarchy."""
    pass


class TagHierarchyRead(TagHierarchyBase):
    """Schema for reading a tag hierarchy."""
    
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaggedResourceResponse(BaseModel):
    """Schema for tagged resource responses."""
    
    resource_ids: List[str]
    resource_count: int
    tag_filters: Dict[str, str]
    resource_type: str
