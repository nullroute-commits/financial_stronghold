"""Multi-tenancy extension for Financial Stronghold."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, get_tenant_context, require_role
from app.core.db.connection import get_db_session
from app.financial_models import Account, Budget, Fee, Transaction
from app.schemas import (
    AccountCreate,
    AccountRead,
    AccountUpdate,
    BudgetCreate,
    BudgetRead,
    BudgetUpdate,
    FeeCreate,
    FeeRead,
    FeeUpdate,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from app.services import TenantService

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
    db: Session = Depends(get_db_session),
):
    """Create a new transaction."""
    service = TenantService(db=db, model=Transaction)
    return service.create(payload, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"])


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
