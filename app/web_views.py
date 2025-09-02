"""
Django views for the Financial Stronghold web interface.
Provides HTML views that integrate with the existing FastAPI backend.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import transaction
from django.urls import reverse
from decimal import Decimal
from datetime import datetime
import logging

from app.core.db.connection import get_db_session
from app.dashboard_service import DashboardService
from app.services import TenantService
from app.financial_models import Account, Transaction, Budget
from app.django_models import User

logger = logging.getLogger(__name__)


def get_tenant_context_from_user(user):
    """Get tenant context for the current user."""
    if user.is_authenticated:
        return {"tenant_type": "user", "tenant_id": str(user.id), "is_organization": False}
    return None


@login_required
def dashboard_home(request):
    """Main dashboard view with financial overview."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("login")

            dashboard_service = DashboardService(db=db)

            # Get dashboard data
            financial_summary = dashboard_service.get_financial_summary(
                tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            account_summaries = dashboard_service.get_account_summaries(
                tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            transaction_summary = dashboard_service.get_transaction_summary(
                tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            budget_statuses = dashboard_service.get_budget_statuses(
                tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            context = {
                "financial_summary": financial_summary,
                "account_summaries": account_summaries[:4],  # Show top 4 accounts
                "transaction_summary": transaction_summary,
                "budget_statuses": budget_statuses[:3],  # Show top 3 budgets
                "recent_transactions": (
                    transaction_summary.recent_transactions[:5] if transaction_summary.recent_transactions else []
                ),
            }

            return render(request, "dashboard/home.html", context)

    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        messages.error(request, "Error loading dashboard data")
        return render(
            request,
            "dashboard/home.html",
            {
                "financial_summary": None,
                "account_summaries": [],
                "transaction_summary": None,
                "budget_statuses": [],
                "recent_transactions": [],
            },
        )


@login_required
def accounts_list(request):
    """List all accounts for the current user."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("dashboard:home")

            service = TenantService(db=db, model=Account)
            accounts = service.get_all(tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"])

            # Calculate totals
            total_balance = sum(account.balance for account in accounts)
            active_accounts = [acc for acc in accounts if acc.is_active]

            context = {
                "accounts": accounts,
                "total_balance": total_balance,
                "total_accounts": len(accounts),
                "active_accounts": len(active_accounts),
            }

            return render(request, "accounts/list.html", context)

    except Exception as e:
        logger.error(f"Error loading accounts: {str(e)}")
        messages.error(request, "Error loading accounts")
        return render(request, "accounts/list.html", {"accounts": []})


@login_required
def account_detail(request, account_id):
    """Show account details and recent transactions."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("accounts:list")

            # Get account
            service = TenantService(db=db, model=Account)
            account = service.get_one(
                account_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            if not account:
                messages.error(request, "Account not found")
                return redirect("accounts:list")

            # Get recent transactions for this account
            transaction_service = TenantService(db=db, model=Transaction)
            account_transactions = transaction_service.get_transactions_for_account(
                account_id=account.id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            # Sort by date (newest first)
            account_transactions.sort(key=lambda x: x.created_at, reverse=True)

            # Paginate
            paginator = Paginator(account_transactions, 20)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)

            context = {
                "account": account,
                "transactions": page_obj,
                "transaction_count": len(account_transactions),
            }

            return render(request, "accounts/detail.html", context)

    except Exception as e:
        logger.error(f"Error loading account detail: {str(e)}")
        messages.error(request, "Error loading account details")
        return redirect("accounts:list")


@login_required
def transactions_list(request):
    """List all transactions for the current user."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("dashboard:home")

            service = TenantService(db=db, model=Transaction)
            transactions = service.get_all(
                tenant_type=tenant_context["tenant_type"],
                tenant_id=tenant_context["tenant_id"],
                order_by=[("created_at", "desc")],
            )

            # Paginate
            paginator = Paginator(transactions, 25)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)

            # Calculate summary stats
            total_amount = sum(t.amount for t in transactions)
            transaction_count = len(transactions)

            context = {
                "transactions": page_obj,
                "total_amount": total_amount,
                "transaction_count": transaction_count,
            }

            return render(request, "transactions/list.html", context)

    except Exception as e:
        logger.error(f"Error loading transactions: {str(e)}")
        messages.error(request, "Error loading transactions")
        return render(request, "transactions/list.html", {"transactions": None})


@login_required
def transaction_detail(request, transaction_id):
    """Show transaction details."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("transactions:list")

            service = TenantService(db=db, model=Transaction)
            transaction_obj = service.get_one(
                transaction_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            if not transaction_obj:
                messages.error(request, "Transaction not found")
                return redirect("transactions:list")

            # Get related accounts
            account_service = TenantService(db=db, model=Account)
            from_account = None
            to_account = None

            if transaction_obj.account_id:
                from_account = account_service.get_one(
                    transaction_obj.account_id,
                    tenant_type=tenant_context["tenant_type"],
                    tenant_id=tenant_context["tenant_id"],
                )

            if transaction_obj.to_account_id:
                to_account = account_service.get_one(
                    transaction_obj.to_account_id,
                    tenant_type=tenant_context["tenant_type"],
                    tenant_id=tenant_context["tenant_id"],
                )

            context = {
                "transaction": transaction_obj,
                "from_account": from_account,
                "to_account": to_account,
            }

            return render(request, "transactions/detail.html", context)

    except Exception as e:
        logger.error(f"Error loading transaction detail: {str(e)}")
        messages.error(request, "Error loading transaction details")
        return redirect("transactions:list")


@login_required
def budgets_list(request):
    """List all budgets for the current user."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("dashboard:home")

            service = TenantService(db=db, model=Budget)
            budgets = service.get_all(tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"])

            # Calculate budget statistics
            total_budget = sum(budget.total_amount for budget in budgets)
            total_spent = sum(budget.spent_amount for budget in budgets)
            budgets_over = len([b for b in budgets if b.spent_amount > b.total_amount])

            context = {
                "budgets": budgets,
                "total_budget": total_budget,
                "total_spent": total_spent,
                "budgets_over": budgets_over,
                "utilization_percentage": (total_spent / total_budget * 100) if total_budget > 0 else 0,
            }

            return render(request, "budgets/list.html", context)

    except Exception as e:
        logger.error(f"Error loading budgets: {str(e)}")
        messages.error(request, "Error loading budgets")
        return render(request, "budgets/list.html", {"budgets": []})


@login_required
def budget_detail(request, budget_id):
    """Show budget details and spending breakdown."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("budgets:list")

            service = TenantService(db=db, model=Budget)
            budget = service.get_one(
                budget_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            if not budget:
                messages.error(request, "Budget not found")
                return redirect("budgets:list")

            # Calculate budget metrics
            remaining_amount = budget.total_amount - budget.spent_amount
            percentage_used = (budget.spent_amount / budget.total_amount * 100) if budget.total_amount > 0 else 0
            is_over_budget = budget.spent_amount > budget.total_amount

            context = {
                "budget": budget,
                "remaining_amount": remaining_amount,
                "percentage_used": percentage_used,
                "is_over_budget": is_over_budget,
            }

            return render(request, "budgets/detail.html", context)

    except Exception as e:
        logger.error(f"Error loading budget detail: {str(e)}")
        messages.error(request, "Error loading budget details")
        return redirect("budgets:list")


# Fee Management Views
@login_required
def fees_list(request):
    """List all fees for the current user."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("dashboard:home")

            from app.financial_models import Fee

            service = TenantService(db=db, model=Fee)
            fees = service.get_all(tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"])

            # Calculate totals
            total_fees = sum(fee.amount for fee in fees)
            active_fees = [fee for fee in fees if fee.is_active]

            context = {
                "fees": fees,
                "total_fees": total_fees,
                "total_count": len(fees),
                "active_count": len(active_fees),
            }

            return render(request, "fees/list.html", context)

    except Exception as e:
        logger.error(f"Error loading fees: {str(e)}")
        messages.error(request, "Error loading fees")
        return render(request, "fees/list.html", {"fees": []})


@login_required
def fee_detail(request, fee_id):
    """Show fee details."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("fees:list")

            from app.financial_models import Fee

            service = TenantService(db=db, model=Fee)
            fee = service.get_one(
                fee_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            if not fee:
                messages.error(request, "Fee not found")
                return redirect("fees:list")

            context = {
                "fee": fee,
            }

            return render(request, "fees/detail.html", context)

    except Exception as e:
        logger.error(f"Error loading fee detail: {str(e)}")
        messages.error(request, "Error loading fee details")
        return redirect("fees:list")


@login_required
@require_http_methods(["GET", "POST"])
def fee_create(request):
    """Create a new fee."""
    if request.method == "GET":
        return render(request, "fees/create.html")

    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("fees:list")

            # Extract form data
            fee_data = {
                "name": request.POST.get("name"),
                "description": request.POST.get("description"),
                "amount": Decimal(request.POST.get("amount")),
                "fee_type": request.POST.get("fee_type"),
                "is_active": request.POST.get("is_active") == "on",
                "due_date": request.POST.get("due_date") or None,
            }

            from app.financial_models import Fee
            from app.schemas import FeeCreate

            service = TenantService(db=db, model=Fee)

            # Create the fee
            fee_create = FeeCreate(**fee_data)
            fee = service.create(
                fee_create, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            messages.success(request, f"Fee '{fee.name}' created successfully")
            return redirect("fees:detail", fee_id=fee.id)

    except Exception as e:
        logger.error(f"Error creating fee: {str(e)}")
        messages.error(request, f"Error creating fee: {str(e)}")
        return render(request, "fees/create.html")


@login_required
@require_http_methods(["GET", "POST"])
def fee_edit(request, fee_id):
    """Edit an existing fee."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("fees:list")

            from app.financial_models import Fee

            service = TenantService(db=db, model=Fee)
            fee = service.get_one(
                fee_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            if not fee:
                messages.error(request, "Fee not found")
                return redirect("fees:list")

            if request.method == "GET":
                context = {"fee": fee}
                return render(request, "fees/edit.html", context)

            # Handle POST - update fee
            fee_data = {
                "name": request.POST.get("name"),
                "description": request.POST.get("description"),
                "amount": Decimal(request.POST.get("amount")),
                "fee_type": request.POST.get("fee_type"),
                "is_active": request.POST.get("is_active") == "on",
                "due_date": request.POST.get("due_date") or None,
            }

            from app.schemas import FeeUpdate

            fee_update = FeeUpdate(**fee_data)
            updated_fee = service.update(
                fee_id, fee_update, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            messages.success(request, f"Fee '{updated_fee.name}' updated successfully")
            return redirect("fees:detail", fee_id=updated_fee.id)

    except Exception as e:
        logger.error(f"Error updating fee: {str(e)}")
        messages.error(request, f"Error updating fee: {str(e)}")
        return redirect("fees:list")


# Enhanced Transaction Management Views
@login_required
@require_http_methods(["GET", "POST"])
def transaction_create(request):
    """Create a new transaction."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("transactions:list")

            if request.method == "GET":
                # Get available accounts for the user
                service = TenantService(db=db, model=Account)
                accounts = service.get_all(
                    tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
                )
                context = {"accounts": accounts}
                return render(request, "transactions/create.html", context)

            # Handle POST - create transaction
            transaction_data = {
                "account_id": request.POST.get("account_id"),
                "to_account_id": request.POST.get("to_account_id") or None,
                "amount": Decimal(request.POST.get("amount")),
                "currency": request.POST.get("currency", "USD"),
                "description": request.POST.get("description"),
                "transaction_type": request.POST.get("transaction_type"),
                "category": request.POST.get("category"),
                "tags": request.POST.get("tags", "").split(",") if request.POST.get("tags") else [],
            }

            from app.schemas import TransactionCreate

            service = TenantService(db=db, model=Transaction)

            transaction_create = TransactionCreate(**transaction_data)
            transaction = service.create(
                transaction_create, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            messages.success(request, f"Transaction created successfully")
            return redirect("transactions:detail", transaction_id=transaction.id)

    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        messages.error(request, f"Error creating transaction: {str(e)}")
        return redirect("transactions:create")


@login_required
@require_http_methods(["GET", "POST"])
def transaction_edit(request, transaction_id):
    """Edit an existing transaction."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("transactions:list")

            service = TenantService(db=db, model=Transaction)
            transaction_obj = service.get_one(
                transaction_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            if not transaction_obj:
                messages.error(request, "Transaction not found")
                return redirect("transactions:list")

            if request.method == "GET":
                # Get available accounts
                account_service = TenantService(db=db, model=Account)
                accounts = account_service.get_all(
                    tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
                )
                context = {"transaction": transaction_obj, "accounts": accounts}
                return render(request, "transactions/edit.html", context)

            # Handle POST - update transaction
            transaction_data = {
                "account_id": request.POST.get("account_id"),
                "to_account_id": request.POST.get("to_account_id") or None,
                "amount": Decimal(request.POST.get("amount")),
                "currency": request.POST.get("currency", "USD"),
                "description": request.POST.get("description"),
                "transaction_type": request.POST.get("transaction_type"),
                "category": request.POST.get("category"),
                "tags": request.POST.get("tags", "").split(",") if request.POST.get("tags") else [],
            }

            from app.schemas import TransactionUpdate

            transaction_update = TransactionUpdate(**transaction_data)
            updated_transaction = service.update(
                transaction_id,
                transaction_update,
                tenant_type=tenant_context["tenant_type"],
                tenant_id=tenant_context["tenant_id"],
            )

            messages.success(request, f"Transaction updated successfully")
            return redirect("transactions:detail", transaction_id=updated_transaction.id)

    except Exception as e:
        logger.error(f"Error updating transaction: {str(e)}")
        messages.error(request, f"Error updating transaction: {str(e)}")
        return redirect("transactions:list")


# Enhanced Budget Management Views
@login_required
@require_http_methods(["GET", "POST"])
def budget_create(request):
    """Create a new budget."""
    if request.method == "GET":
        return render(request, "budgets/create.html")

    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("budgets:list")

            # Extract form data
            budget_data = {
                "name": request.POST.get("name"),
                "description": request.POST.get("description"),
                "category": request.POST.get("category"),
                "total_amount": Decimal(request.POST.get("total_amount")),
                "spent_amount": Decimal(request.POST.get("spent_amount", "0")),
                "currency": request.POST.get("currency", "USD"),
                "start_date": request.POST.get("start_date"),
                "end_date": request.POST.get("end_date"),
                "is_active": request.POST.get("is_active") == "on",
            }

            from app.schemas import BudgetCreate

            service = TenantService(db=db, model=Budget)

            budget_create = BudgetCreate(**budget_data)
            budget = service.create(
                budget_create, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            messages.success(request, f"Budget '{budget.name}' created successfully")
            return redirect("budgets:detail", budget_id=budget.id)

    except Exception as e:
        logger.error(f"Error creating budget: {str(e)}")
        messages.error(request, f"Error creating budget: {str(e)}")
        return render(request, "budgets/create.html")


@login_required
@require_http_methods(["GET", "POST"])
def budget_edit(request, budget_id):
    """Edit an existing budget."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("budgets:list")

            service = TenantService(db=db, model=Budget)
            budget = service.get_one(
                budget_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            if not budget:
                messages.error(request, "Budget not found")
                return redirect("budgets:list")

            if request.method == "GET":
                context = {"budget": budget}
                return render(request, "budgets/edit.html", context)

            # Handle POST - update budget
            budget_data = {
                "name": request.POST.get("name"),
                "description": request.POST.get("description"),
                "category": request.POST.get("category"),
                "total_amount": Decimal(request.POST.get("total_amount")),
                "spent_amount": Decimal(request.POST.get("spent_amount", "0")),
                "currency": request.POST.get("currency", "USD"),
                "start_date": request.POST.get("start_date"),
                "end_date": request.POST.get("end_date"),
                "is_active": request.POST.get("is_active") == "on",
            }

            from app.schemas import BudgetUpdate

            budget_update = BudgetUpdate(**budget_data)
            updated_budget = service.update(
                budget_id,
                budget_update,
                tenant_type=tenant_context["tenant_type"],
                tenant_id=tenant_context["tenant_id"],
            )

            messages.success(request, f"Budget '{updated_budget.name}' updated successfully")
            return redirect("budgets:detail", budget_id=updated_budget.id)

    except Exception as e:
        logger.error(f"Error updating budget: {str(e)}")
        messages.error(request, f"Error updating budget: {str(e)}")
        return redirect("budgets:list")


# Enhanced Account Management Views
@login_required
@require_http_methods(["GET", "POST"])
def account_create(request):
    """Create a new account."""
    if request.method == "GET":
        return render(request, "accounts/create.html")

    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("accounts:list")

            # Extract form data
            account_data = {
                "name": request.POST.get("name"),
                "account_type": request.POST.get("account_type"),
                "balance": Decimal(request.POST.get("balance", "0")),
                "currency": request.POST.get("currency", "USD"),
                "description": request.POST.get("description"),
                "is_active": request.POST.get("is_active") == "on",
            }

            from app.schemas import AccountCreate

            service = TenantService(db=db, model=Account)

            account_create = AccountCreate(**account_data)
            account = service.create(
                account_create, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            messages.success(request, f"Account '{account.name}' created successfully")
            return redirect("accounts:detail", account_id=account.id)

    except Exception as e:
        logger.error(f"Error creating account: {str(e)}")
        messages.error(request, f"Error creating account: {str(e)}")
        return render(request, "accounts/create.html")


@login_required
@require_http_methods(["GET", "POST"])
def account_edit(request, account_id):
    """Edit an existing account."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("accounts:list")

            service = TenantService(db=db, model=Account)
            account = service.get_one(
                account_id, tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            if not account:
                messages.error(request, "Account not found")
                return redirect("accounts:list")

            if request.method == "GET":
                context = {"account": account}
                return render(request, "accounts/edit.html", context)

            # Handle POST - update account
            account_data = {
                "name": request.POST.get("name"),
                "account_type": request.POST.get("account_type"),
                "balance": Decimal(request.POST.get("balance", "0")),
                "currency": request.POST.get("currency", "USD"),
                "description": request.POST.get("description"),
                "is_active": request.POST.get("is_active") == "on",
            }

            from app.schemas import AccountUpdate

            account_update = AccountUpdate(**account_data)
            updated_account = service.update(
                account_id,
                account_update,
                tenant_type=tenant_context["tenant_type"],
                tenant_id=tenant_context["tenant_id"],
            )

            messages.success(request, f"Account '{updated_account.name}' updated successfully")
            return redirect("accounts:detail", account_id=updated_account.id)

    except Exception as e:
        logger.error(f"Error updating account: {str(e)}")
        messages.error(request, f"Error updating account: {str(e)}")
        return redirect("accounts:list")


# Analytics and Reporting Views
@login_required
def analytics_dashboard(request):
    """Analytics dashboard with comprehensive financial insights."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("dashboard:home")

            # Get analytics data using the analytics service
            from app.tagging_service import AnalyticsService

            analytics_service = AnalyticsService(db=db)

            # Get summary analytics
            analytics_summary = analytics_service.get_analytics_summary(
                tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            # Get dashboard data for additional context
            dashboard_service = DashboardService(db=db)
            dashboard_data = dashboard_service.get_complete_dashboard_data(
                tenant_type=tenant_context["tenant_type"], tenant_id=tenant_context["tenant_id"]
            )

            context = {
                "analytics_summary": analytics_summary,
                "dashboard_data": dashboard_data,
                "financial_summary": dashboard_data.financial_summary,
                "account_summaries": dashboard_data.account_summaries,
                "transaction_summary": dashboard_data.transaction_summary,
                "budget_statuses": dashboard_data.budget_statuses,
            }

            return render(request, "analytics/dashboard.html", context)

    except Exception as e:
        logger.error(f"Error loading analytics dashboard: {str(e)}")
        messages.error(request, "Error loading analytics data")
        return render(request, "analytics/dashboard.html", {})


# Tagging System Views
@login_required
def tags_list(request):
    """List all tags for the current user."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("dashboard:home")

            from app.tagging_service import TaggingService
            tagging_service = TaggingService(db=db)
            
            # Get all tags for the tenant
            tags = tagging_service.get_tenant_tags(
                tenant_type=tenant_context["tenant_type"],
                tenant_id=tenant_context["tenant_id"]
            )

            # Group tags by type
            tag_groups = {}
            for tag in tags:
                tag_type = tag.tag_type
                if tag_type not in tag_groups:
                    tag_groups[tag_type] = []
                tag_groups[tag_type].append(tag)

            context = {
                "tag_groups": tag_groups,
                "total_tags": len(tags),
                "tag_types": list(tag_groups.keys()),
            }

            return render(request, "tags/list.html", context)

    except Exception as e:
        logger.error(f"Error loading tags: {str(e)}")
        messages.error(request, "Error loading tags")
        return render(request, "tags/list.html", {"tag_groups": {}, "total_tags": 0, "tag_types": []})


@login_required
@require_http_methods(["GET", "POST"])
def tag_create(request):
    """Create a new tag."""
    if request.method == "GET":
        return render(request, "tags/create.html")

    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("tags:list")

            from app.tagging_service import TaggingService
            from app.schemas import DataTagCreate

            tagging_service = TaggingService(db=db)

            # Extract form data
            tag_data = {
                "tag_type": request.POST.get("tag_type"),
                "tag_key": request.POST.get("tag_key"),
                "tag_value": request.POST.get("tag_value"),
                "resource_type": request.POST.get("resource_type"),
                "resource_id": request.POST.get("resource_id"),
                "tag_label": request.POST.get("tag_label"),
                "tag_metadata": request.POST.get("tag_metadata", "{}"),
            }

            # Create the tag
            tag_create = DataTagCreate(**tag_data)
            tag = tagging_service._create_tag(
                tag_type=tag_create.tag_type,
                tag_key=tag_create.tag_key,
                tag_value=tag_create.tag_value,
                resource_type=tag_create.resource_type,
                resource_id=tag_create.resource_id,
                tenant_type=tenant_context["tenant_type"],
                tenant_id=tenant_context["tenant_id"],
                label=tag_create.tag_label,
                metadata=tag_create.tag_metadata,
            )

            messages.success(request, f"Tag '{tag.tag_label}' created successfully")
            return redirect("tags:list")

    except Exception as e:
        logger.error(f"Error creating tag: {str(e)}")
        messages.error(request, f"Error creating tag: {str(e)}")
        return render(request, "tags/create.html")


@login_required
def tag_detail(request, tag_id):
    """Show tag details and associated resources."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("tags:list")

            from app.tagging_service import TaggingService
            tagging_service = TaggingService(db=db)

            # Get tag details
            tag = tagging_service.get_tag_by_id(tag_id)
            if not tag:
                messages.error(request, "Tag not found")
                return redirect("tags:list")

            # Get resources with this tag
            tagged_resources = tagging_service.get_tagged_resources(
                tag_filters={tag.tag_key: tag.tag_value},
                resource_type=tag.resource_type,
                tenant_type=tenant_context["tenant_type"],
                tenant_id=tenant_context["tenant_id"],
            )

            context = {
                "tag": tag,
                "tagged_resources": tagged_resources,
                "resource_count": len(tagged_resources),
            }

            return render(request, "tags/detail.html", context)

    except Exception as e:
        logger.error(f"Error loading tag detail: {str(e)}")
        messages.error(request, "Error loading tag details")
        return redirect("tags:list")


# Transaction Classification Views
@login_required
def classification_dashboard(request):
    """Transaction classification dashboard."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("dashboard:home")

            from app.transaction_classifier import TransactionClassifierService
            classifier = TransactionClassifierService(db=db)

            # Get classification statistics
            classification_stats = classifier.get_classification_statistics(
                tenant_type=tenant_context["tenant_type"],
                tenant_id=tenant_context["tenant_id"]
            )

            # Get recent classifications
            recent_classifications = classifier.get_recent_classifications(
                tenant_type=tenant_context["tenant_type"],
                tenant_id=tenant_context["tenant_id"],
                limit=10
            )

            context = {
                "classification_stats": classification_stats,
                "recent_classifications": recent_classifications,
            }

            return render(request, "classification/dashboard.html", context)

    except Exception as e:
        logger.error(f"Error loading classification dashboard: {str(e)}")
        messages.error(request, "Error loading classification data")
        return render(request, "classification/dashboard.html", {})


@login_required
@require_http_methods(["GET", "POST"])
def classify_transactions(request):
    """Classify transactions manually or automatically."""
    if request.method == "GET":
        return render(request, "classification/classify.html")

    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("classification:dashboard")

            from app.transaction_classifier import TransactionClassifierService
            from app.schemas import TransactionClassificationRequest

            classifier = TransactionClassifierService(db=db)

            # Extract form data
            classification_data = {
                "transaction_ids": request.POST.getlist("transaction_ids"),
                "auto_tag": request.POST.get("auto_tag") == "on",
                "force_reclassify": request.POST.get("force_reclassify") == "on",
            }

            # Classify transactions
            classification_request = TransactionClassificationRequest(**classification_data)
            results = classifier.classify_transactions(
                request=classification_request,
                tenant_context=tenant_context,
                db=db
            )

            messages.success(request, f"Successfully classified {len(results)} transactions")
            return redirect("classification:dashboard")

    except Exception as e:
        logger.error(f"Error classifying transactions: {str(e)}")
        messages.error(request, f"Error classifying transactions: {str(e)}")
        return render(request, "classification/classify.html")


# Analytics Views Management
@login_required
def analytics_views_list(request):
    """List all saved analytics views."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("dashboard:home")

            from app.tagging_models import AnalyticsView
            from app.core.tenant import TenantType

            views = (
                db.query(AnalyticsView)
                .filter(
                    AnalyticsView.tenant_type == TenantType(tenant_context["tenant_type"]),
                    AnalyticsView.tenant_id == tenant_context["tenant_id"],
                    AnalyticsView.is_active == True,
                )
                .order_by(AnalyticsView.created_at.desc())
                .all()
            )

            context = {
                "analytics_views": views,
                "total_views": len(views),
            }

            return render(request, "analytics/views_list.html", context)

    except Exception as e:
        logger.error(f"Error loading analytics views: {str(e)}")
        messages.error(request, "Error loading analytics views")
        return render(request, "analytics/views_list.html", {"analytics_views": [], "total_views": 0})


@login_required
@require_http_methods(["GET", "POST"])
def analytics_view_create(request):
    """Create a new analytics view."""
    if request.method == "GET":
        return render(request, "analytics/view_create.html")

    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("analytics:views_list")

            from app.tagging_service import AnalyticsService
            from app.schemas import AnalyticsViewCreate

            analytics_service = AnalyticsService(db=db)

            # Extract form data
            view_data = {
                "view_name": request.POST.get("view_name"),
                "view_description": request.POST.get("view_description"),
                "tag_filters": request.POST.get("tag_filters", "{}"),
                "resource_types": request.POST.getlist("resource_types"),
                "period_start": request.POST.get("period_start"),
                "period_end": request.POST.get("period_end"),
            }

            # Create the analytics view
            view_create = AnalyticsViewCreate(**view_data)
            view = analytics_service.create_analytics_view(
                view_name=view_create.view_name,
                tag_filters=view_create.tag_filters,
                resource_types=view_create.resource_types,
                tenant_type=tenant_context["tenant_type"],
                tenant_id=tenant_context["tenant_id"],
                description=view_create.view_description,
                period_start=view_create.period_start,
                period_end=view_create.period_end,
            )

            messages.success(request, f"Analytics view '{view.view_name}' created successfully")
            return redirect("analytics:views_list")

    except Exception as e:
        logger.error(f"Error creating analytics view: {str(e)}")
        messages.error(request, f"Error creating analytics view: {str(e)}")
        return render(request, "analytics/view_create.html")


# Anomaly Detection Views
@login_required
def anomaly_detection(request):
    """Anomaly detection dashboard."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("dashboard:home")

            from app.transaction_analytics import TransactionAnalyticsService
            from app.schemas import AnomalyDetectionRequest

            analytics_service = TransactionAnalyticsService(db=db)

            # Get anomaly detection data
            sensitivity = request.GET.get("sensitivity", "medium")
            anomaly_request = AnomalyDetectionRequest(sensitivity=sensitivity)
            
            anomaly_data = analytics_service.get_anomaly_detection(
                tenant_type=tenant_context["tenant_type"],
                tenant_id=tenant_context["tenant_id"],
                sensitivity=anomaly_request.sensitivity,
            )

            context = {
                "anomalies": anomaly_data["anomalies"],
                "sensitivity": anomaly_data["sensitivity"],
                "analysis_period": anomaly_data["analysis_period"],
                "total_anomalies": anomaly_data["total_anomalies"],
                "current_sensitivity": sensitivity,
            }

            return render(request, "analytics/anomaly_detection.html", context)

    except Exception as e:
        logger.error(f"Error loading anomaly detection: {str(e)}")
        messages.error(request, "Error loading anomaly detection data")
        return render(request, "analytics/anomaly_detection.html", {})


# Classification Configuration Views
@login_required
def classification_config(request):
    """Classification configuration management."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("dashboard:home")

            from app.transaction_classifier import TransactionClassifierService

            classifier = TransactionClassifierService(db=db)

            # Get current configuration
            config = classifier.get_classification_config()

            context = {
                "classification_patterns": config["classification_patterns"],
                "category_patterns": config["category_patterns"],
                "updated_at": config["updated_at"],
            }

            return render(request, "classification/config.html", context)

    except Exception as e:
        logger.error(f"Error loading classification config: {str(e)}")
        messages.error(request, "Error loading classification configuration")
        return render(request, "classification/config.html", {})


@login_required
@require_http_methods(["GET", "POST"])
def classification_config_update(request):
    """Update classification configuration."""
    if request.method == "GET":
        return redirect("classification:config")

    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect("classification:config")

            from app.transaction_classifier import TransactionClassifierService
            from app.schemas import ClassificationConfigRequest

            classifier = TransactionClassifierService(db=db)

            # Extract form data
            config_data = {
                "classification_patterns": request.POST.get("classification_patterns", "{}"),
                "category_patterns": request.POST.get("category_patterns", "{}"),
            }

            # Update configuration
            config_request = ClassificationConfigRequest(**config_data)
            updated_config = classifier.update_classification_config(
                request=config_request,
                tenant_context=tenant_context,
                db=db
            )

            messages.success(request, "Classification configuration updated successfully")
            return redirect("classification:config")

    except Exception as e:
        logger.error(f"Error updating classification config: {str(e)}")
        messages.error(request, f"Error updating classification configuration: {str(e)}")
        return redirect("classification:config")


# Documentation Views
@login_required
def documentation_home(request):
    """Main documentation page with system overview."""
    try:
        from app.documentation_service import DocumentationService
        
        doc_service = DocumentationService()
        comprehensive_docs = doc_service.get_comprehensive_documentation()
        
        context = {
            "system_overview": comprehensive_docs["system_overview"],
            "quick_start": comprehensive_docs["quick_start"],
            "architecture": comprehensive_docs["architecture"],
            "feature_count": len(comprehensive_docs["feature_documentation"]),
            "api_count": len(comprehensive_docs["api_documentation"]),
            "example_count": len(comprehensive_docs["code_examples"]),
        }
        
        return render(request, "documentation/home.html", context)
        
    except Exception as e:
        logger.error(f"Error loading documentation: {str(e)}")
        messages.error(request, "Error loading documentation")
        return render(request, "documentation/home.html", {})


@login_required
def documentation_features(request):
    """Feature documentation page."""
    try:
        from app.documentation_service import DocumentationService
        
        doc_service = DocumentationService()
        feature_docs = doc_service.get_feature_documentation()
        
        context = {
            "features": feature_docs,
            "feature_count": len(feature_docs),
        }
        
        return render(request, "documentation/features.html", context)
        
    except Exception as e:
        logger.error(f"Error loading feature documentation: {str(e)}")
        messages.error(request, "Error loading feature documentation")
        return render(request, "documentation/features.html", {})


@login_required
def documentation_api(request):
    """API documentation page."""
    try:
        from app.documentation_service import DocumentationService
        
        doc_service = DocumentationService()
        api_docs = doc_service.get_api_documentation()
        
        # Group APIs by tags
        apis_by_tag = {}
        for path, api_doc in api_docs.items():
            tags = api_doc.get('tags', ['general'])
            for tag in tags:
                if tag not in apis_by_tag:
                    apis_by_tag[tag] = []
                apis_by_tag[tag].append(api_doc)
        
        context = {
            "apis_by_tag": apis_by_tag,
            "total_apis": len(api_docs),
            "tags": list(apis_by_tag.keys()),
        }
        
        return render(request, "documentation/api.html", context)
        
    except Exception as e:
        logger.error(f"Error loading API documentation: {str(e)}")
        messages.error(request, "Error loading API documentation")
        return render(request, "documentation/api.html", {})


@login_required
def documentation_examples(request):
    """Code examples documentation page."""
    try:
        from app.documentation_service import DocumentationService
        
        doc_service = DocumentationService()
        code_examples = doc_service.get_code_examples()
        
        context = {
            "examples": code_examples,
            "total_examples": len(code_examples),
        }
        
        return render(request, "documentation/examples.html", context)
        
    except Exception as e:
        logger.error(f"Error loading code examples: {str(e)}")
        messages.error(request, "Error loading code examples")
        return render(request, "documentation/examples.html", {})


@login_required
def documentation_search(request):
    """Search documentation."""
    query = request.GET.get('q', '')
    results = []
    
    if query:
        try:
            from app.documentation_service import DocumentationService
            
            doc_service = DocumentationService()
            results = doc_service.search_documentation(query)
            
        except Exception as e:
            logger.error(f"Error searching documentation: {str(e)}")
            messages.error(request, "Error searching documentation")
    
    context = {
        "query": query,
        "results": results,
        "result_count": len(results),
    }
    
    return render(request, "documentation/search.html", context)


@login_required
def documentation_feature_detail(request, feature_name):
    """Detailed feature documentation."""
    try:
        from app.documentation_service import DocumentationService
        
        doc_service = DocumentationService()
        feature_doc = doc_service.get_feature_documentation(feature_name)
        
        if not feature_doc:
            messages.error(request, f"Feature '{feature_name}' not found")
            return redirect("documentation:features")
        
        context = {
            "feature": feature_doc,
            "feature_name": feature_name,
        }
        
        return render(request, "documentation/feature_detail.html", context)
        
    except Exception as e:
        logger.error(f"Error loading feature detail: {str(e)}")
        messages.error(request, "Error loading feature details")
        return redirect("documentation:features")


@login_required
def documentation_api_detail(request, api_path):
    """Detailed API documentation."""
    try:
        from app.documentation_service import DocumentationService
        
        doc_service = DocumentationService()
        api_doc = doc_service.get_api_documentation(api_path)
        
        if not api_doc:
            messages.error(request, f"API '{api_path}' not found")
            return redirect("documentation:api")
        
        context = {
            "api": api_doc,
            "api_path": api_path,
        }
        
        return render(request, "documentation/api_detail.html", context)
        
    except Exception as e:
        logger.error(f"Error loading API detail: {str(e)}")
        messages.error(request, "Error loading API details")
        return redirect("documentation:api")


def home_redirect(request):
    """Redirect to appropriate home page."""
    if request.user.is_authenticated:
        return redirect("/dashboard/")
    return redirect("/accounts/login/")
