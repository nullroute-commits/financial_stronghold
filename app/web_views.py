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


def home_redirect(request):
    """Redirect to appropriate home page."""
    if request.user.is_authenticated:
        return redirect("/dashboard/")
    return redirect("/accounts/login/")
