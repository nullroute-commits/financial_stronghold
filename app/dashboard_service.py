"""Financial Dashboard Service for aggregating financial data."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Union

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.db.connection import get_db_session
from app.financial_models import Account, Budget, Transaction
from app.schemas import (
    AccountSummary,
    BudgetStatus,
    DashboardData,
    FinancialSummary,
    TenantInfo,
    TransactionRead,
    TransactionSummary,
)
from app.services import TenantService


class DashboardService:
    """Service for aggregating financial dashboard data."""

    def __init__(self, db: Session):
        self.db = db

    def get_account_summaries(self, tenant_type: str, tenant_id: Union[str, int]) -> List[AccountSummary]:
        """Get account summaries for the tenant."""
        account_service = TenantService(db=self.db, model=Account)
        accounts = account_service.get_all(tenant_type=tenant_type, tenant_id=tenant_id)
        
        return [
            AccountSummary(
                account_id=account.id,
                name=account.name,
                account_type=account.account_type,
                balance=account.balance,
                currency=account.currency,
                is_active=account.is_active,
            )
            for account in accounts
        ]

    def get_financial_summary(self, tenant_type: str, tenant_id: Union[str, int]) -> FinancialSummary:
        """Get overall financial summary for the tenant."""
        # Get all accounts
        account_service = TenantService(db=self.db, model=Account)
        accounts = account_service.get_all(tenant_type=tenant_type, tenant_id=tenant_id)
        
        # Calculate totals
        total_balance = sum(account.balance for account in accounts)
        total_accounts = len(accounts)
        active_accounts = len([account for account in accounts if account.is_active])
        
        # Get transaction stats
        transaction_service = TenantService(db=self.db, model=Transaction)
        all_transactions = transaction_service.get_all(tenant_type=tenant_type, tenant_id=tenant_id)
        total_transactions = len(all_transactions)
        
        # This month transactions
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_transactions = [
            t for t in all_transactions 
            if t.created_at >= month_start
        ]
        this_month_count = len(this_month_transactions)
        this_month_amount = sum(t.amount for t in this_month_transactions)
        
        # Get currency from first account or default to USD
        currency = accounts[0].currency if accounts else "USD"
        
        return FinancialSummary(
            total_balance=total_balance,
            total_accounts=total_accounts,
            active_accounts=active_accounts,
            total_transactions=total_transactions,
            this_month_transactions=this_month_count,
            this_month_amount=this_month_amount,
            currency=currency,
            last_updated=datetime.now(),
        )

    def get_transaction_summary(self, tenant_type: str, tenant_id: Union[str, int]) -> TransactionSummary:
        """Get transaction summary for the tenant."""
        transaction_service = TenantService(db=self.db, model=Transaction)
        all_transactions = transaction_service.get_all(tenant_type=tenant_type, tenant_id=tenant_id)
        
        if not all_transactions:
            return TransactionSummary(
                total_transactions=0,
                total_amount=Decimal("0.00"),
                avg_amount=Decimal("0.00"),
                currency="USD",
                recent_transactions=[],
            )
        
        total_transactions = len(all_transactions)
        total_amount = sum(t.amount for t in all_transactions)
        avg_amount = total_amount / total_transactions if total_transactions > 0 else Decimal("0.00")
        currency = all_transactions[0].currency if all_transactions else "USD"
        
        # Get recent transactions (last 5)
        recent_transactions = sorted(all_transactions, key=lambda t: t.created_at, reverse=True)[:5]
        recent_transaction_reads = [
            TransactionRead(
                id=t.id,
                amount=t.amount,
                currency=t.currency,
                description=t.description,
                transaction_type=t.transaction_type,
                reference_number=t.reference_number,
                account_id=t.account_id,
                to_account_id=t.to_account_id,
                status=t.status,
                category=t.category,
                tags=t.tags,
                tenant_type=t.tenant_type,
                tenant_id=t.tenant_id,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in recent_transactions
        ]
        
        return TransactionSummary(
            total_transactions=total_transactions,
            total_amount=total_amount,
            avg_amount=avg_amount,
            currency=currency,
            recent_transactions=recent_transaction_reads,
        )

    def get_budget_statuses(self, tenant_type: str, tenant_id: Union[str, int]) -> List[BudgetStatus]:
        """Get budget statuses for the tenant."""
        budget_service = TenantService(db=self.db, model=Budget)
        budgets = budget_service.get_all(tenant_type=tenant_type, tenant_id=tenant_id)
        
        budget_statuses = []
        for budget in budgets:
            remaining_amount = budget.total_amount - budget.spent_amount
            percentage_used = (budget.spent_amount / budget.total_amount * 100) if budget.total_amount > 0 else Decimal("0.00")
            is_over_budget = budget.spent_amount > budget.total_amount
            
            budget_statuses.append(
                BudgetStatus(
                    budget_id=budget.id,
                    name=budget.name,
                    total_amount=budget.total_amount,
                    spent_amount=budget.spent_amount,
                    remaining_amount=remaining_amount,
                    percentage_used=percentage_used,
                    is_over_budget=is_over_budget,
                    alert_threshold=budget.alert_threshold,
                    currency=budget.currency,
                )
            )
        
        return budget_statuses

    def get_complete_dashboard_data(self, tenant_type: str, tenant_id: Union[str, int]) -> DashboardData:
        """Get complete dashboard data for the tenant."""
        financial_summary = self.get_financial_summary(tenant_type, tenant_id)
        account_summaries = self.get_account_summaries(tenant_type, tenant_id)
        transaction_summary = self.get_transaction_summary(tenant_type, tenant_id)
        budget_statuses = self.get_budget_statuses(tenant_type, tenant_id)
        
        tenant_info = TenantInfo(tenant_type=tenant_type, tenant_id=str(tenant_id))
        
        return DashboardData(
            financial_summary=financial_summary,
            account_summaries=account_summaries,
            transaction_summary=transaction_summary,
            budget_statuses=budget_statuses,
            tenant_info=tenant_info,
        )