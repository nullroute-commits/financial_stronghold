"""Multi-tenancy extension for Financial Stronghold."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.auth import get_current_user, get_tenant_context, require_role
from app.core.db.connection import get_db_session
from app.core.tenant import TenantType
from app.financial_models import Account, Budget, Fee, Transaction
from app.schemas import (
    AccountCreate,
    AccountRead,
    AccountSummary,
    AccountUpdate,
    AnalyticsSummary,
    AnalyticsViewCreate,
    AnalyticsViewRead,
    AnalyticsViewUpdate,
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    BudgetCreate,
    BudgetRead,
    BudgetStatus,
    BudgetUpdate,
    CategorySpendingInsight,
    ClassificationAnalyticsRequest,
    ClassificationAnalyticsResponse,
    ClassificationAmountAnalysis,
    ClassificationConfigRequest,
    ClassificationConfigResponse,
    ClassificationDistribution,
    DashboardData,
    DataTagCreate,
    DataTagRead,
    DataTagUpdate,
    FeeCreate,
    FeeRead,
    FeeUpdate,
    FinancialSummary,
    MonthlyBreakdownResponse,
    ResourceMetrics,
    SpendingInsights,
    TagFilterRequest,
    TaggedResourceResponse,
    TransactionClassificationRequest,
    TransactionClassificationResult,
    TransactionCreate,
    TransactionPatternsResponse,
    TransactionRead,
    TransactionSummary,
    TransactionUpdate,
)
from app.services import TenantService
from app.dashboard_service import DashboardService
from app.tagging_service import TaggingService, AnalyticsService

router = APIRouter(prefix="/financial", tags=["financial"])


# Account endpoints
@router.post("/accounts", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Create a new account."""
    service = TenantService(db=db, model=Account)
    return service.create(payload, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"])


@router.get("/accounts", response_model=List[AccountRead])
def list_accounts(
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
):
    """List all accounts for the tenant."""
    service = TenantService(db=db, model=Account)
    return service.get_all(
        tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"], limit=limit, offset=offset
    )


@router.get("/accounts/{account_id}", response_model=AccountRead)
def get_account(
    account_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get a specific account."""
    service = TenantService(db=db, model=Account)
    account = service.get_one(
        account_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.put("/accounts/{account_id}", response_model=AccountRead)
def update_account(
    account_id: UUID,
    payload: AccountUpdate,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Update an account."""
    service = TenantService(db=db, model=Account)
    account = service.update(
        account_id, payload, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Delete an account (requires admin role for organizations)."""
    # Check admin role for organizations
    if tenant_context["is_organization"]:
        # This will raise an exception if not admin/owner
        require_role(["owner", "admin"])(tenant_context)

    service = TenantService(db=db, model=Account)
    deleted = service.delete(
        account_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")


# Transaction endpoints
@router.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    tenant_context: dict = Depends(get_tenant_context),
    current_user: dict = Depends(get_current_user),
    auto_classify: bool = Query(True, description="Automatically classify the transaction"),
    auto_tag: bool = Query(True, description="Automatically create tags"),
    db: Session = Depends(get_db_session),
):
    """Create a new transaction with automatic classification and tagging."""
    service = TenantService(db=db, model=Transaction)
    transaction = service.create(payload, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"])
    
    if auto_classify:
        from app.transaction_classifier import TransactionClassifierService
        
        classifier = TransactionClassifierService(db=db)
        classifier.auto_classify_and_categorize(
            transaction=transaction,
            create_tags=auto_tag
        )
    
    if auto_tag:
        # Create standard tenant/user/role tags
        tagging_service = TaggingService(db=db)
        tagging_service.auto_tag_resource(
            resource_type="transaction",
            resource_id=transaction.id,
            tenant_type=tenant_context["tenant_type"],
            tenant_id=tenant_context["tenant_id"],
            user_id=current_user.get("user_id"),
        )
    
    # Refresh to get any new tags/classifications
    db.refresh(transaction)
    return transaction


@router.get("/transactions", response_model=List[TransactionRead])
def list_transactions(
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
):
    """List all transactions for the tenant."""
    service = TenantService(db=db, model=Transaction)
    return service.get_all(
        tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"], limit=limit, offset=offset
    )


@router.get("/transactions/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get a specific transaction."""
    service = TenantService(db=db, model=Transaction)
    transaction = service.get_one(
        transaction_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction


@router.put("/transactions/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: UUID,
    payload: TransactionUpdate,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Update a transaction."""
    service = TenantService(db=db, model=Transaction)
    transaction = service.update(
        transaction_id, payload, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Delete a transaction (requires admin role for organizations)."""
    # Check admin role for organizations
    if tenant_context["is_organization"]:
        # This will raise an exception if not admin/owner
        require_role(["owner", "admin"])(tenant_context)

    service = TenantService(db=db, model=Transaction)
    deleted = service.delete(
        transaction_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")


# Fee endpoints
@router.post("/fees", response_model=FeeRead, status_code=status.HTTP_201_CREATED)
def create_fee(
    payload: FeeCreate,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Create a new fee."""
    service = TenantService(db=db, model=Fee)
    return service.create(payload, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"])


@router.get("/fees", response_model=List[FeeRead])
def list_fees(
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
):
    """List all fees for the tenant."""
    service = TenantService(db=db, model=Fee)
    return service.get_all(
        tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"], limit=limit, offset=offset
    )


@router.get("/fees/{fee_id}", response_model=FeeRead)
def get_fee(
    fee_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get a specific fee."""
    service = TenantService(db=db, model=Fee)
    fee = service.get_one(
        fee_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )
    if not fee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee not found")
    return fee


@router.put("/fees/{fee_id}", response_model=FeeRead)
def update_fee(
    fee_id: UUID,
    payload: FeeUpdate,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Update a fee."""
    service = TenantService(db=db, model=Fee)
    fee = service.update(
        fee_id, payload, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )
    if not fee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee not found")
    return fee


@router.delete("/fees/{fee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fee(
    fee_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Delete a fee (requires admin role for organizations)."""
    # Check admin role for organizations
    if tenant_context["is_organization"]:
        # This will raise an exception if not admin/owner
        require_role(["owner", "admin"])(tenant_context)

    service = TenantService(db=db, model=Fee)
    deleted = service.delete(
        fee_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee not found")


# Budget endpoints
@router.post("/budgets", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreate,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Create a new budget."""
    service = TenantService(db=db, model=Budget)
    return service.create(payload, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"])


@router.get("/budgets", response_model=List[BudgetRead])
def list_budgets(
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
):
    """List all budgets for the tenant."""
    service = TenantService(db=db, model=Budget)
    return service.get_all(
        tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"], limit=limit, offset=offset
    )


@router.get("/budgets/{budget_id}", response_model=BudgetRead)
def get_budget(
    budget_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get a specific budget."""
    service = TenantService(db=db, model=Budget)
    budget = service.get_one(
        budget_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget


@router.put("/budgets/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: UUID,
    payload: BudgetUpdate,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Update a budget."""
    service = TenantService(db=db, model=Budget)
    budget = service.update(
        budget_id, payload, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Delete a budget (requires admin role for organizations)."""
    # Check admin role for organizations
    if tenant_context["is_organization"]:
        # This will raise an exception if not admin/owner
        require_role(["owner", "admin"])(tenant_context)

    service = TenantService(db=db, model=Budget)
    deleted = service.delete(
        budget_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")


# Dashboard endpoints
@router.get("/dashboard", response_model=DashboardData)
def get_dashboard_data(
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get complete dashboard data for the tenant."""
    dashboard_service = DashboardService(db=db)
    return dashboard_service.get_complete_dashboard_data(
        tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )


@router.get("/dashboard/summary", response_model=FinancialSummary)
def get_financial_summary(
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get financial summary for the tenant."""
    dashboard_service = DashboardService(db=db)
    return dashboard_service.get_financial_summary(
        tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )


@router.get("/dashboard/accounts", response_model=List[AccountSummary])
def get_account_summaries(
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get account summaries for the tenant."""
    dashboard_service = DashboardService(db=db)
    return dashboard_service.get_account_summaries(
        tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )


@router.get("/dashboard/transactions", response_model=TransactionSummary)
def get_transaction_summary(
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get transaction summary for the tenant."""
    dashboard_service = DashboardService(db=db)
    return dashboard_service.get_transaction_summary(
        tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )


@router.get("/dashboard/budgets", response_model=List[BudgetStatus])
def get_budget_statuses(
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get budget statuses for the tenant."""
    dashboard_service = DashboardService(db=db)
    return dashboard_service.get_budget_statuses(
        tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
    )


# Tagging endpoints
@router.post("/tags", response_model=DataTagRead, status_code=status.HTTP_201_CREATED)
def create_tag(
    payload: DataTagCreate,
    tenant_context: dict = Depends(get_tenant_context),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Create a new data tag."""
    tagging_service = TaggingService(db=db)
    
    # Use the appropriate create method based on tag type
    if payload.tag_type == "user" and payload.tag_key == "user_id":
        return tagging_service.create_user_tag(
            user_id=payload.tag_value,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            tenant_type=tenant_context["tenant_type"],
            tenant_id=tenant_context["tenant_id"],
            label=payload.tag_label,
            metadata=payload.tag_metadata,
        )
    elif payload.tag_type == "organization" and payload.tag_key == "org_id":
        return tagging_service.create_organization_tag(
            org_id=payload.tag_value,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            tenant_type=tenant_context["tenant_type"],
            tenant_id=tenant_context["tenant_id"],
            label=payload.tag_label,
            metadata=payload.tag_metadata,
        )
    elif payload.tag_type == "role" and payload.tag_key == "role_id":
        return tagging_service.create_role_tag(
            role_id=payload.tag_value,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            tenant_type=tenant_context["tenant_type"],
            tenant_id=tenant_context["tenant_id"],
            label=payload.tag_label,
            metadata=payload.tag_metadata,
        )
    else:
        # Generic tag creation
        from app.tagging_models import TagType as TagTypeEnum
        return tagging_service._create_tag(
            tag_type=TagTypeEnum(payload.tag_type),
            tag_key=payload.tag_key,
            tag_value=payload.tag_value,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            tenant_type=tenant_context["tenant_type"],
            tenant_id=tenant_context["tenant_id"],
            label=payload.tag_label,
            metadata=payload.tag_metadata,
        )


@router.get("/tags/resource/{resource_type}/{resource_id}", response_model=List[DataTagRead])
def get_resource_tags(
    resource_type: str,
    resource_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get all tags for a specific resource."""
    tagging_service = TaggingService(db=db)
    return tagging_service.get_resource_tags(
        resource_type=resource_type,
        resource_id=resource_id,
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"],
    )


@router.post("/tags/auto/{resource_type}/{resource_id}", response_model=List[DataTagRead])
def auto_tag_resource(
    resource_type: str,
    resource_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Automatically create standard tags for a resource."""
    tagging_service = TaggingService(db=db)
    return tagging_service.auto_tag_resource(
        resource_type=resource_type,
        resource_id=resource_id,
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"],
        user_id=current_user.get("user_id"),
    )


@router.post("/tags/query", response_model=TaggedResourceResponse)
def query_tagged_resources(
    tag_filters: dict,
    resource_type: str,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Query resources by tag filters."""
    tagging_service = TaggingService(db=db)
    resource_ids = tagging_service.get_tagged_resources(
        tag_filters=tag_filters,
        resource_type=resource_type,
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"],
    )
    
    return TaggedResourceResponse(
        resource_ids=resource_ids,
        resource_count=len(resource_ids),
        tag_filters=tag_filters,
        resource_type=resource_type,
    )


# Analytics endpoints
@router.post("/analytics/compute", response_model=ResourceMetrics)
def compute_tag_metrics(
    request: TagFilterRequest,
    resource_type: str,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Compute metrics for resources matching tag filters."""
    analytics_service = AnalyticsService(db=db)
    metrics = analytics_service.compute_tag_metrics(
        tag_filters=request.tag_filters,
        resource_type=resource_type,
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"],
        period_start=request.period_start,
        period_end=request.period_end,
    )
    
    return ResourceMetrics(**metrics)


@router.post("/analytics/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    request: TagFilterRequest,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get comprehensive analytics summary across all resource types."""
    analytics_service = AnalyticsService(db=db)
    summary = analytics_service.get_analytics_summary(
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"],
        tag_filters=request.tag_filters,
    )
    
    # Convert to proper schema format
    resource_metrics = {}
    for resource_type, metrics in summary["resource_metrics"].items():
        resource_metrics[resource_type] = ResourceMetrics(**metrics)
    
    return AnalyticsSummary(
        tenant_info=summary["tenant_info"],
        tag_filters=summary["tag_filters"],
        resource_metrics=resource_metrics,
        generated_at=summary["generated_at"],
    )


@router.post("/analytics/views", response_model=AnalyticsViewRead, status_code=status.HTTP_201_CREATED)
def create_analytics_view(
    payload: AnalyticsViewCreate,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Create a saved analytics view."""
    analytics_service = AnalyticsService(db=db)
    return analytics_service.create_analytics_view(
        view_name=payload.view_name,
        tag_filters=payload.tag_filters,
        resource_types=payload.resource_types,
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"],
        description=payload.view_description,
        period_start=payload.period_start,
        period_end=payload.period_end,
    )


@router.get("/analytics/views", response_model=List[AnalyticsViewRead])
def list_analytics_views(
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
):
    """List analytics views for the tenant."""
    from app.tagging_models import AnalyticsView
    from app.core.tenant import TenantType
    
    query = db.query(AnalyticsView).filter(
        AnalyticsView.tenant_type == TenantType(tenant_context["tenant_type"]),
        AnalyticsView.tenant_id == tenant_context["tenant_id"],
        AnalyticsView.is_active == True,
    ).order_by(AnalyticsView.created_at.desc())
    
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    
    return query.all()


@router.get("/analytics/views/{view_id}", response_model=AnalyticsViewRead)
def get_analytics_view(
    view_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get a specific analytics view."""
    from app.tagging_models import AnalyticsView
    from app.core.tenant import TenantType
    
    view = db.query(AnalyticsView).filter(
        AnalyticsView.id == view_id,
        AnalyticsView.tenant_type == TenantType(tenant_context["tenant_type"]),
        AnalyticsView.tenant_id == tenant_context["tenant_id"],
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="Analytics view not found")
    
    return view


@router.post("/analytics/views/{view_id}/refresh", response_model=AnalyticsViewRead)
def refresh_analytics_view(
    view_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Refresh an analytics view with current data."""
    analytics_service = AnalyticsService(db=db)
    
    # Verify view belongs to tenant
    from app.tagging_models import AnalyticsView
    from app.core.tenant import TenantType
    
    view = db.query(AnalyticsView).filter(
        AnalyticsView.id == view_id,
        AnalyticsView.tenant_type == TenantType(tenant_context["tenant_type"]),
        AnalyticsView.tenant_id == tenant_context["tenant_id"],
    ).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="Analytics view not found")
    
    try:
        return analytics_service.refresh_analytics_view(view_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh view: {str(e)}")


# Enhanced Dashboard with Analytics
@router.get("/dashboard/analytics", response_model=AnalyticsSummary)
def get_dashboard_analytics(
    tenant_context: dict = Depends(get_tenant_context),
    user_id: Optional[str] = Query(None, description="Filter by user_id"),
    org_id: Optional[str] = Query(None, description="Filter by org_id"),
    role_id: Optional[str] = Query(None, description="Filter by role_id"),
    db: Session = Depends(get_db_session),
):
    """Get dashboard with tag-based analytics filtering."""
    analytics_service = AnalyticsService(db=db)
    
    # Build tag filters from query parameters
    tag_filters = {}
    if user_id:
        tag_filters["user_id"] = user_id
    if org_id:
        tag_filters["org_id"] = org_id
    if role_id:
        tag_filters["role_id"] = role_id
    
    summary = analytics_service.get_analytics_summary(
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"],
        tag_filters=tag_filters,
    )
    
    # Convert to proper schema format
    resource_metrics = {}
    for resource_type, metrics in summary["resource_metrics"].items():
        resource_metrics[resource_type] = ResourceMetrics(**metrics)
    
    return AnalyticsSummary(
        tenant_info=summary["tenant_info"],
        tag_filters=summary["tag_filters"],
        resource_metrics=resource_metrics,
        generated_at=summary["generated_at"],
    )


# Transaction Classification and Analytics Endpoints
@router.post("/transactions/classify", response_model=List[TransactionClassificationResult])
def classify_transactions(
    request: TransactionClassificationRequest,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Classify transactions automatically."""
    from app.transaction_classifier import TransactionClassifierService
    
    classifier = TransactionClassifierService(db=db)
    results = []
    
    # Get transactions to classify
    if request.transaction_ids:
        transactions = db.query(Transaction).filter(
            and_(
                Transaction.id.in_(request.transaction_ids),
                Transaction.tenant_type == TenantType(tenant_context["tenant_type"]),
                Transaction.tenant_id == tenant_context["tenant_id"]
            )
        ).all()
    else:
        # Classify all transactions for the tenant
        transactions = db.query(Transaction).filter(
            and_(
                Transaction.tenant_type == TenantType(tenant_context["tenant_type"]),
                Transaction.tenant_id == tenant_context["tenant_id"]
            )
        ).all()
    
    for transaction in transactions:
        # Check if already classified (unless forcing reclassification)
        existing_tags = classifier.tagging_service.get_resource_tags(
            resource_type="transaction",
            resource_id=transaction.id,
            tenant_type=tenant_context["tenant_type"],
            tenant_id=tenant_context["tenant_id"]
        )
        
        existing_classification = None
        existing_category = None
        
        for tag in existing_tags:
            if tag.tag_key == "classification":
                existing_classification = tag.tag_value
            elif tag.tag_key == "category":
                existing_category = tag.tag_value
        
        # Skip if already classified and not forcing reclassification
        if existing_classification and existing_category and not request.force_reclassify:
            results.append(TransactionClassificationResult(
                transaction_id=transaction.id,
                classification=existing_classification,
                category=existing_category,
                auto_generated=False,
                confidence=0.95
            ))
            continue
        
        # Classify the transaction
        classification_result = classifier.auto_classify_and_categorize(
            transaction=transaction,
            create_tags=request.auto_tag
        )
        
        results.append(TransactionClassificationResult(
            transaction_id=transaction.id,
            classification=classification_result["classification"],
            category=classification_result["category"],
            auto_generated=True,
            confidence=0.85,
            previous_classification=existing_classification,
            previous_category=existing_category
        ))
    
    return results


@router.post("/analytics/classification", response_model=ClassificationAnalyticsResponse)
def get_classification_analytics(
    request: ClassificationAnalyticsRequest,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get comprehensive classification and categorization analytics."""
    from app.transaction_analytics import TransactionAnalyticsService
    
    analytics_service = TransactionAnalyticsService(db=db)
    
    if request.analysis_type in ["classification", "all"]:
        classification_analytics = analytics_service.get_classification_analytics(
            tenant_type=tenant_context["tenant_type"],
            tenant_id=tenant_context["tenant_id"],
            period_start=request.period_start,
            period_end=request.period_end
        )
        
        # Convert to schema format
        distribution = ClassificationDistribution(**classification_analytics["distribution"])
        
        amount_analysis = {}
        for classification, data in classification_analytics["amount_analysis"].items():
            amount_analysis[classification] = ClassificationAmountAnalysis(**data)
        
        return ClassificationAnalyticsResponse(
            distribution=distribution,
            amount_analysis=amount_analysis,
            period_start=classification_analytics["period_start"],
            period_end=classification_analytics["period_end"],
            analysis_type="classification"
        )
    
    elif request.analysis_type == "category":
        category_analytics = analytics_service.get_category_analytics(
            tenant_type=tenant_context["tenant_type"],
            tenant_id=tenant_context["tenant_id"],
            period_start=request.period_start,
            period_end=request.period_end
        )
        
        # Convert to schema format
        distribution = ClassificationDistribution(
            classifications={},
            categories={cat: data["count"] for cat, data in category_analytics["category_analysis"].items()},
            total_classified=0,
            total_categorized=sum(data["count"] for data in category_analytics["category_analysis"].values())
        )
        
        amount_analysis = {}
        for category, data in category_analytics["category_analysis"].items():
            amount_analysis[category] = ClassificationAmountAnalysis(**data)
        
        # Convert spending insights
        spending_insights = None
        if "spending_insights" in category_analytics:
            insights_data = category_analytics["spending_insights"]
            spending_insights = SpendingInsights(
                top_spending_categories=[
                    CategorySpendingInsight(**cat_data) 
                    for cat_data in insights_data["top_spending_categories"]
                ],
                total_spending=insights_data["total_spending"],
                categories_with_spending=insights_data["categories_with_spending"],
                average_transaction_amount=insights_data["average_transaction_amount"]
            )
        
        return ClassificationAnalyticsResponse(
            distribution=distribution,
            amount_analysis=amount_analysis,
            spending_insights=spending_insights,
            period_start=category_analytics["period_start"],
            period_end=category_analytics["period_end"],
            analysis_type="category"
        )


@router.post("/analytics/anomalies", response_model=AnomalyDetectionResponse)
def detect_transaction_anomalies(
    request: AnomalyDetectionRequest,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Detect anomalies in transaction patterns."""
    from app.transaction_analytics import TransactionAnalyticsService
    
    analytics_service = TransactionAnalyticsService(db=db)
    
    anomaly_data = analytics_service.get_anomaly_detection(
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"],
        sensitivity=request.sensitivity
    )
    
    # Convert to schema format
    anomalies = [TransactionAnomaly(**anomaly) for anomaly in anomaly_data["anomalies"]]
    
    return AnomalyDetectionResponse(
        anomalies=anomalies,
        sensitivity=anomaly_data["sensitivity"],
        analysis_period=anomaly_data["analysis_period"],
        total_anomalies=anomaly_data["total_anomalies"]
    )


@router.get("/analytics/monthly-breakdown", response_model=MonthlyBreakdownResponse)
def get_monthly_breakdown(
    tenant_context: dict = Depends(get_tenant_context),
    months: int = Query(12, ge=1, le=24, description="Number of months to analyze"),
    db: Session = Depends(get_db_session),
):
    """Get monthly breakdown of transaction classifications and categories."""
    from app.transaction_analytics import TransactionAnalyticsService
    
    analytics_service = TransactionAnalyticsService(db=db)
    
    breakdown_data = analytics_service.get_monthly_breakdown(
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"],
        months=months
    )
    
    # Convert to schema format
    monthly_breakdown = {}
    for month, data in breakdown_data["monthly_breakdown"].items():
        classifications = {}
        for classification, analysis in data["classifications"].items():
            classifications[classification] = ClassificationAmountAnalysis(**analysis)
            
        categories = {}
        for category, analysis in data["categories"].items():
            categories[category] = ClassificationAmountAnalysis(**analysis)
        
        monthly_breakdown[month] = MonthlyBreakdownData(
            classifications=classifications,
            categories=categories,
            period=data["period"]
        )
    
    return MonthlyBreakdownResponse(
        monthly_breakdown=monthly_breakdown,
        analysis_period=breakdown_data["analysis_period"]
    )


@router.get("/analytics/patterns", response_model=TransactionPatternsResponse)
def get_transaction_patterns(
    tenant_context: dict = Depends(get_tenant_context),
    pattern_type: str = Query("all", description="Pattern type: 'classification', 'category', or 'all'"),
    db: Session = Depends(get_db_session),
):
    """Analyze transaction patterns for insights."""
    from app.transaction_analytics import TransactionAnalyticsService
    
    analytics_service = TransactionAnalyticsService(db=db)
    
    patterns_data = analytics_service.get_transaction_patterns(
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"],
        pattern_type=pattern_type
    )
    
    # Convert to schema format
    response_data = {}
    
    if "classification_patterns" in patterns_data:
        classification_patterns = {}
        for classification, pattern_data in patterns_data["classification_patterns"].items():
            classification_patterns[classification] = TransactionPatternAnalysis(**pattern_data)
        response_data["classification_patterns"] = classification_patterns
    
    if "category_patterns" in patterns_data:
        category_patterns = {}
        for category, pattern_data in patterns_data["category_patterns"].items():
            category_patterns[category] = TransactionPatternAnalysis(**pattern_data)
        response_data["category_patterns"] = category_patterns
    
    if "cross_analysis" in patterns_data:
        response_data["cross_analysis"] = patterns_data["cross_analysis"]
    
    return TransactionPatternsResponse(**response_data)


@router.get("/classification/config", response_model=ClassificationConfigResponse)
def get_classification_config(
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Get current classification configuration patterns."""
    from app.transaction_classifier import TransactionClassifierService
    
    classifier = TransactionClassifierService(db=db)
    
    return ClassificationConfigResponse(
        classification_patterns=classifier.get_classification_patterns(),
        category_patterns=classifier.get_category_patterns(),
        updated_at=datetime.now(timezone.utc).isoformat()
    )


@router.post("/classification/config", response_model=ClassificationConfigResponse)
def update_classification_config(
    request: ClassificationConfigRequest,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
):
    """Update classification configuration patterns."""
    from app.transaction_classifier import TransactionClassifierService, TransactionClassification, TransactionCategory
    
    classifier = TransactionClassifierService(db=db)
    
    # Add new classification patterns
    if request.classification_patterns:
        for classification_name, patterns in request.classification_patterns.items():
            try:
                classification = TransactionClassification(classification_name)
                for pattern in patterns:
                    classifier.add_classification_pattern(classification, pattern)
            except ValueError:
                continue  # Skip invalid classification names
    
    # Add new category patterns
    if request.category_patterns:
        for category_name, patterns in request.category_patterns.items():
            try:
                category = TransactionCategory(category_name)
                for pattern in patterns:
                    classifier.add_category_pattern(category, pattern)
            except ValueError:
                continue  # Skip invalid category names
    
    return ClassificationConfigResponse(
        classification_patterns=classifier.get_classification_patterns(),
        category_patterns=classifier.get_category_patterns(),
        updated_at=datetime.now(timezone.utc).isoformat()
    )
