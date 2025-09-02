"""
Django-native API endpoints for Financial Stronghold.
Uses Django ORM instead of SQLAlchemy for all database operations.

Last updated: 2025-01-21 by AI Assistant
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from .auth import get_current_user, get_tenant_context, require_role
from .django_models import Account, Budget, Fee, Transaction, TenantType, User
from .services import DjangoTenantService

router = APIRouter(prefix="/financial", tags=["financial"])


# Account endpoints
@router.post("/accounts", status_code=status.HTTP_201_CREATED)
def create_account(
    payload: dict,
    tenant_context: dict = Depends(get_tenant_context),
):
    """Create a new account."""
    service = DjangoTenantService(Account)
    return service.create(
        payload, 
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"]
    )


@router.get("/accounts")
def list_accounts(
    tenant_context: dict = Depends(get_tenant_context),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
):
    """List all accounts for the tenant."""
    service = DjangoTenantService(Account)
    return service.get_all(
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"], 
        limit=limit, 
        offset=offset
    )


@router.get("/accounts/{account_id}")
def get_account(
    account_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
):
    """Get a specific account."""
    service = DjangoTenantService(Account)
    account = service.get_one(
        account_id, 
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"]
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.put("/accounts/{account_id}")
def update_account(
    account_id: UUID,
    payload: dict,
    tenant_context: dict = Depends(get_tenant_context),
):
    """Update an account."""
    service = DjangoTenantService(Account)
    account = service.update(
        account_id, 
        payload, 
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"]
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
):
    """Delete an account (requires admin role for organizations)."""
    # Check admin role for organizations
    if tenant_context["is_organization"]:
        # This will raise an exception if not admin/owner
        require_role(["owner", "admin"])(tenant_context)

    service = DjangoTenantService(Account)
    deleted = service.delete(
        account_id, 
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"]
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")


# Transaction endpoints
@router.post("/transactions", status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: dict,
    tenant_context: dict = Depends(get_tenant_context),
    current_user: Tuple[User, str, str] = Depends(get_current_user),
    auto_classify: bool = Query(True, description="Automatically classify the transaction"),
    auto_tag: bool = Query(True, description="Automatically create tags"),
):
    """Create a new transaction with automatic classification and tagging."""
    service = DjangoTenantService(Transaction)
    transaction = service.create(
        payload, 
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"]
    )

    # TODO: Implement auto-classification and tagging with Django ORM
    if auto_classify:
        pass  # Implement transaction classification

    if auto_tag:
        pass  # Implement auto-tagging

    return transaction


@router.get("/transactions")
def list_transactions(
    tenant_context: dict = Depends(get_tenant_context),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
):
    """List all transactions for the tenant."""
    service = DjangoTenantService(Transaction)
    return service.get_all(
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"], 
        limit=limit, 
        offset=offset
    )


@router.get("/transactions/{transaction_id}")
def get_transaction(
    transaction_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
):
    """Get a specific transaction."""
    service = DjangoTenantService(Transaction)
    transaction = service.get_one(
        transaction_id, 
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"]
    )
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction


@router.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: UUID,
    payload: dict,
    tenant_context: dict = Depends(get_tenant_context),
):
    """Update a transaction."""
    service = DjangoTenantService(Transaction)
    transaction = service.update(
        transaction_id, 
        payload, 
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"]
    )
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
):
    """Delete a transaction."""
    service = DjangoTenantService(Transaction)
    deleted = service.delete(
        transaction_id, 
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"]
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")


# Budget endpoints
@router.post("/budgets", status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: dict,
    tenant_context: dict = Depends(get_tenant_context),
):
    """Create a new budget."""
    service = DjangoTenantService(Budget)
    return service.create(
        payload, 
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"]
    )


@router.get("/budgets")
def list_budgets(
    tenant_context: dict = Depends(get_tenant_context),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
):
    """List all budgets for the tenant."""
    service = DjangoTenantService(Budget)
    return service.get_all(
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"], 
        limit=limit, 
        offset=offset
    )


@router.get("/budgets/{budget_id}")
def get_budget(
    budget_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
):
    """Get a specific budget."""
    service = DjangoTenantService(Budget)
    budget = service.get_one(
        budget_id, 
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"]
    )
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget


# Fee endpoints
@router.post("/fees", status_code=status.HTTP_201_CREATED)
def create_fee(
    payload: dict,
    tenant_context: dict = Depends(get_tenant_context),
):
    """Create a new fee."""
    service = DjangoTenantService(Fee)
    return service.create(
        payload, 
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"]
    )


@router.get("/fees")
def list_fees(
    tenant_context: dict = Depends(get_tenant_context),
    limit: Optional[int] = Query(None, ge=1, le=100),
    offset: Optional[int] = Query(None, ge=0),
):
    """List all fees for the tenant."""
    service = DjangoTenantService(Fee)
    return service.get_all(
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"], 
        limit=limit, 
        offset=offset
    )


@router.get("/fees/{fee_id}")
def get_fee(
    fee_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
):
    """Get a specific fee."""
    service = DjangoTenantService(Fee)
    fee = service.get_one(
        fee_id, 
        tenant_type=tenant_context["tenant_type"], 
        tenant_id=tenant_context["tenant_id"]
    )
    if not fee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fee not found")
    return fee