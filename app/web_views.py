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
        return {
            'tenant_type': 'user',
            'tenant_id': str(user.id),
            'is_organization': False
        }
    return None


@login_required
def dashboard_home(request):
    """Main dashboard view with financial overview."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect('login')
            
            dashboard_service = DashboardService(db=db)
            
            # Get dashboard data
            financial_summary = dashboard_service.get_financial_summary(
                tenant_type=tenant_context['tenant_type'],
                tenant_id=tenant_context['tenant_id']
            )
            
            account_summaries = dashboard_service.get_account_summaries(
                tenant_type=tenant_context['tenant_type'],
                tenant_id=tenant_context['tenant_id']
            )
            
            transaction_summary = dashboard_service.get_transaction_summary(
                tenant_type=tenant_context['tenant_type'],
                tenant_id=tenant_context['tenant_id']
            )
            
            budget_statuses = dashboard_service.get_budget_statuses(
                tenant_type=tenant_context['tenant_type'],
                tenant_id=tenant_context['tenant_id']
            )
            
            context = {
                'financial_summary': financial_summary,
                'account_summaries': account_summaries[:4],  # Show top 4 accounts
                'transaction_summary': transaction_summary,
                'budget_statuses': budget_statuses[:3],  # Show top 3 budgets
                'recent_transactions': transaction_summary.recent_transactions[:5] if transaction_summary.recent_transactions else [],
            }
            
            return render(request, 'dashboard/home.html', context)
            
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        messages.error(request, "Error loading dashboard data")
        return render(request, 'dashboard/home.html', {
            'financial_summary': None,
            'account_summaries': [],
            'transaction_summary': None,
            'budget_statuses': [],
            'recent_transactions': [],
        })


@login_required
def accounts_list(request):
    """List all accounts for the current user."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect('dashboard:home')
            
            service = TenantService(db=db, model=Account)
            accounts = service.get_all(
                tenant_type=tenant_context['tenant_type'],
                tenant_id=tenant_context['tenant_id']
            )
            
            # Calculate totals
            total_balance = sum(account.balance for account in accounts)
            active_accounts = [acc for acc in accounts if acc.is_active]
            
            context = {
                'accounts': accounts,
                'total_balance': total_balance,
                'total_accounts': len(accounts),
                'active_accounts': len(active_accounts),
            }
            
            return render(request, 'accounts/list.html', context)
            
    except Exception as e:
        logger.error(f"Error loading accounts: {str(e)}")
        messages.error(request, "Error loading accounts")
        return render(request, 'accounts/list.html', {'accounts': []})


@login_required
def account_detail(request, account_id):
    """Show account details and recent transactions."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect('accounts:list')
            
            # Get account
            service = TenantService(db=db, model=Account)
            account = service.get_one(
                account_id,
                tenant_type=tenant_context['tenant_type'],
                tenant_id=tenant_context['tenant_id']
            )
            
            if not account:
                messages.error(request, "Account not found")
                return redirect('accounts:list')
            
            # Get recent transactions for this account
            transaction_service = TenantService(db=db, model=Transaction)
            account_transactions = transaction_service.get_transactions_for_account(
                account_id=account.id,
                tenant_type=tenant_context['tenant_type'],
                tenant_id=tenant_context['tenant_id']
            )
            
            # Sort by date (newest first)
            account_transactions.sort(key=lambda x: x.created_at, reverse=True)
            
            # Paginate
            paginator = Paginator(account_transactions, 20)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            context = {
                'account': account,
                'transactions': page_obj,
                'transaction_count': len(account_transactions),
            }
            
            return render(request, 'accounts/detail.html', context)
            
    except Exception as e:
        logger.error(f"Error loading account detail: {str(e)}")
        messages.error(request, "Error loading account details")
        return redirect('accounts:list')


@login_required
def transactions_list(request):
    """List all transactions for the current user."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect('dashboard:home')
            
            service = TenantService(db=db, model=Transaction)
            transactions = service.get_all(
                tenant_type=tenant_context['tenant_type'],
                tenant_id=tenant_context['tenant_id']
            )
            
            # Sort by date (newest first)
            transactions.sort(key=lambda x: x.created_at, reverse=True)
            
            # Paginate
            paginator = Paginator(transactions, 25)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            # Calculate summary stats
            total_amount = sum(t.amount for t in transactions)
            transaction_count = len(transactions)
            
            context = {
                'transactions': page_obj,
                'total_amount': total_amount,
                'transaction_count': transaction_count,
            }
            
            return render(request, 'transactions/list.html', context)
            
    except Exception as e:
        logger.error(f"Error loading transactions: {str(e)}")
        messages.error(request, "Error loading transactions")
        return render(request, 'transactions/list.html', {'transactions': None})


@login_required
def transaction_detail(request, transaction_id):
    """Show transaction details."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect('transactions:list')
            
            service = TenantService(db=db, model=Transaction)
            transaction_obj = service.get_one(
                transaction_id,
                tenant_type=tenant_context['tenant_type'],
                tenant_id=tenant_context['tenant_id']
            )
            
            if not transaction_obj:
                messages.error(request, "Transaction not found")
                return redirect('transactions:list')
            
            # Get related accounts
            account_service = TenantService(db=db, model=Account)
            from_account = None
            to_account = None
            
            if transaction_obj.account_id:
                from_account = account_service.get_one(
                    transaction_obj.account_id,
                    tenant_type=tenant_context['tenant_type'],
                    tenant_id=tenant_context['tenant_id']
                )
            
            if transaction_obj.to_account_id:
                to_account = account_service.get_one(
                    transaction_obj.to_account_id,
                    tenant_type=tenant_context['tenant_type'],
                    tenant_id=tenant_context['tenant_id']
                )
            
            context = {
                'transaction': transaction_obj,
                'from_account': from_account,
                'to_account': to_account,
            }
            
            return render(request, 'transactions/detail.html', context)
            
    except Exception as e:
        logger.error(f"Error loading transaction detail: {str(e)}")
        messages.error(request, "Error loading transaction details")
        return redirect('transactions:list')


@login_required
def budgets_list(request):
    """List all budgets for the current user."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect('dashboard:home')
            
            service = TenantService(db=db, model=Budget)
            budgets = service.get_all(
                tenant_type=tenant_context['tenant_type'],
                tenant_id=tenant_context['tenant_id']
            )
            
            # Calculate budget statistics
            total_budget = sum(budget.total_amount for budget in budgets)
            total_spent = sum(budget.spent_amount for budget in budgets)
            budgets_over = len([b for b in budgets if b.spent_amount > b.total_amount])
            
            context = {
                'budgets': budgets,
                'total_budget': total_budget,
                'total_spent': total_spent,
                'budgets_over': budgets_over,
                'utilization_percentage': (total_spent / total_budget * 100) if total_budget > 0 else 0,
            }
            
            return render(request, 'budgets/list.html', context)
            
    except Exception as e:
        logger.error(f"Error loading budgets: {str(e)}")
        messages.error(request, "Error loading budgets")
        return render(request, 'budgets/list.html', {'budgets': []})


@login_required
def budget_detail(request, budget_id):
    """Show budget details and spending breakdown."""
    try:
        with get_db_session() as db:
            tenant_context = get_tenant_context_from_user(request.user)
            if not tenant_context:
                messages.error(request, "Unable to determine tenant context")
                return redirect('budgets:list')
            
            service = TenantService(db=db, model=Budget)
            budget = service.get_one(
                budget_id,
                tenant_type=tenant_context['tenant_type'],
                tenant_id=tenant_context['tenant_id']
            )
            
            if not budget:
                messages.error(request, "Budget not found")
                return redirect('budgets:list')
            
            # Calculate budget metrics
            remaining_amount = budget.total_amount - budget.spent_amount
            percentage_used = (budget.spent_amount / budget.total_amount * 100) if budget.total_amount > 0 else 0
            is_over_budget = budget.spent_amount > budget.total_amount
            
            context = {
                'budget': budget,
                'remaining_amount': remaining_amount,
                'percentage_used': percentage_used,
                'is_over_budget': is_over_budget,
            }
            
            return render(request, 'budgets/detail.html', context)
            
    except Exception as e:
        logger.error(f"Error loading budget detail: {str(e)}")
        messages.error(request, "Error loading budget details")
        return redirect('budgets:list')


def home_redirect(request):
    """Redirect to appropriate home page."""
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    return redirect('/accounts/login/')