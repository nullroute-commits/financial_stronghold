"""
Django views for the Financial Stronghold web interface.
Pure Django implementation using Django ORM only.

Last updated: 2025-01-02 by Team Beta (Architecture & Backend Agents)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import transaction as db_transaction, models
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from .django_models import User, Account, Transaction, Budget, Organization, UserOrganizationLink

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
        tenant_context = get_tenant_context_from_user(request.user)
        if not tenant_context:
            messages.error(request, "Unable to determine tenant context")
            return redirect("login")

        # Get user's accounts
        accounts = Account.objects.filter(created_by=request.user)[:4]
        
        # Get recent transactions
        recent_transactions = Transaction.objects.filter(
            account__created_by=request.user
        ).order_by('-date')[:5]
        
        # Calculate financial summary
        total_balance = sum(
            Transaction.objects.filter(account=account).aggregate(
                total=models.Sum('amount')
            )['total'] or 0 
            for account in accounts
        )
        
        # Get budget status
        budgets = Budget.objects.filter(created_by=request.user)[:3]
        
        context = {
            "user": request.user,
            "accounts": accounts,
            "recent_transactions": recent_transactions,
            "total_balance": total_balance,
            "budgets": budgets,
            "account_count": accounts.count(),
            "transaction_count": recent_transactions.count(),
        }

        return render(request, "dashboard/home.html", context)

    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        messages.error(request, "Error loading dashboard data")
        return render(request, "dashboard/home.html", {"user": request.user})


@login_required
def accounts_list(request):
    """List all accounts for the current user."""
    try:
        accounts = Account.objects.filter(created_by=request.user).order_by('name')
        
        # Add balance calculation for each account
        for account in accounts:
            account.balance = Transaction.objects.filter(account=account).aggregate(
                total=models.Sum('amount')
            )['total'] or 0
            account.transaction_count = Transaction.objects.filter(account=account).count()

        context = {
            "accounts": accounts,
            "total_accounts": accounts.count(),
        }

        return render(request, "accounts/list.html", context)

    except Exception as e:
        logger.error(f"Error loading accounts: {str(e)}")
        messages.error(request, "Error loading accounts")
        return redirect("dashboard:home")


@login_required
def account_detail(request, account_id):
    """Display account details and transactions."""
    try:
        account = get_object_or_404(Account, id=account_id, created_by=request.user)
        
        # Get transactions for this account
        transactions = Transaction.objects.filter(account=account).order_by('-date')
        
        # Pagination
        paginator = Paginator(transactions, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Calculate account balance and statistics
        balance = transactions.aggregate(total=models.Sum('amount'))['total'] or 0
        income = transactions.filter(amount__gt=0).aggregate(total=models.Sum('amount'))['total'] or 0
        expenses = transactions.filter(amount__lt=0).aggregate(total=models.Sum('amount'))['total'] or 0
        
        context = {
            "account": account,
            "page_obj": page_obj,
            "balance": balance,
            "income": income,
            "expenses": abs(expenses),
            "transaction_count": transactions.count(),
        }

        return render(request, "accounts/detail.html", context)

    except Exception as e:
        logger.error(f"Error loading account details: {str(e)}")
        messages.error(request, "Error loading account details")
        return redirect("accounts:list")


@login_required
@require_http_methods(["GET", "POST"])
def account_create(request):
    """Create a new account."""
    if request.method == "POST":
        try:
            name = request.POST.get("name")
            account_type = request.POST.get("account_type", "checking")
            currency = request.POST.get("currency", "USD")
            description = request.POST.get("description", "")

            if not name:
                messages.error(request, "Account name is required")
                return render(request, "accounts/create.html")

            account = Account.objects.create(
                name=name,
                account_type=account_type,
                currency=currency,
                description=description,
                created_by=request.user
            )

            messages.success(request, f"Account '{account.name}' created successfully")
            return redirect("accounts:detail", account_id=account.id)

        except Exception as e:
            logger.error(f"Error creating account: {str(e)}")
            messages.error(request, "Error creating account")

    return render(request, "accounts/create.html")


@login_required
def transactions_list(request):
    """List all transactions for the current user."""
    try:
        # Get user's accounts
        user_accounts = Account.objects.filter(created_by=request.user)
        
        # Get transactions for user's accounts
        transactions = Transaction.objects.filter(
            account__in=user_accounts
        ).order_by('-date')
        
        # Filter by account if specified
        account_id = request.GET.get('account')
        if account_id:
            transactions = transactions.filter(account_id=account_id)
        
        # Filter by date range if specified
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date:
            transactions = transactions.filter(date__gte=start_date)
        if end_date:
            transactions = transactions.filter(date__lte=end_date)

        # Pagination
        paginator = Paginator(transactions, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            "page_obj": page_obj,
            "accounts": user_accounts,
            "selected_account": account_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_transactions": transactions.count(),
        }

        return render(request, "transactions/list.html", context)

    except Exception as e:
        logger.error(f"Error loading transactions: {str(e)}")
        messages.error(request, "Error loading transactions")
        return redirect("dashboard:home")


@login_required
@require_http_methods(["GET", "POST"])
def transaction_create(request):
    """Create a new transaction."""
    user_accounts = Account.objects.filter(created_by=request.user)
    
    if request.method == "POST":
        try:
            account_id = request.POST.get("account")
            amount = request.POST.get("amount")
            description = request.POST.get("description")
            category = request.POST.get("category", "")
            date = request.POST.get("date")

            if not all([account_id, amount, description]):
                messages.error(request, "Account, amount, and description are required")
                return render(request, "transactions/create.html", {"accounts": user_accounts})

            account = get_object_or_404(Account, id=account_id, created_by=request.user)
            
            transaction = Transaction.objects.create(
                account=account,
                amount=Decimal(amount),
                description=description,
                category=category,
                date=datetime.strptime(date, '%Y-%m-%d').date() if date else datetime.now().date(),
                created_by=request.user
            )

            messages.success(request, "Transaction created successfully")
            return redirect("transactions:list")

        except ValueError as e:
            messages.error(request, "Invalid amount format")
        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}")
            messages.error(request, "Error creating transaction")

    context = {"accounts": user_accounts}
    return render(request, "transactions/create.html", context)


@login_required
def budgets_list(request):
    """List all budgets for the current user."""
    try:
        budgets = Budget.objects.filter(created_by=request.user).order_by('name')
        
        # Calculate budget status for each budget
        for budget in budgets:
            # Get transactions in budget period and category
            transactions = Transaction.objects.filter(
                account__created_by=request.user,
                date__gte=budget.start_date,
                date__lte=budget.end_date,
                category=budget.category
            )
            
            spent = sum(abs(t.amount) for t in transactions if t.amount < 0)
            budget.spent_amount = spent
            budget.remaining_amount = budget.amount - spent
            budget.percentage_used = (spent / budget.amount * 100) if budget.amount > 0 else 0
            budget.status = 'over_budget' if spent > budget.amount else 'on_track'

        context = {
            "budgets": budgets,
            "total_budgets": budgets.count(),
        }

        return render(request, "budgets/list.html", context)

    except Exception as e:
        logger.error(f"Error loading budgets: {str(e)}")
        messages.error(request, "Error loading budgets")
        return redirect("dashboard:home")


# Authentication views
def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'dashboard:home')
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password")
        else:
            messages.error(request, "Username and password are required")
    
    return render(request, "registration/login.html")


@login_required
def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, "You have been logged out successfully")
    return redirect("login")


# API endpoints for AJAX requests
@login_required
@csrf_exempt
def api_account_balance(request, account_id):
    """Get account balance via AJAX."""
    try:
        account = get_object_or_404(Account, id=account_id, created_by=request.user)
        balance = Transaction.objects.filter(account=account).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        return JsonResponse({
            'account_id': str(account.id),
            'balance': float(balance),
            'currency': account.currency,
            'last_updated': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting account balance: {str(e)}")
        return JsonResponse({'error': 'Unable to get account balance'}, status=500)


@login_required
@csrf_exempt
def api_transaction_summary(request):
    """Get transaction summary via AJAX."""
    try:
        user_accounts = Account.objects.filter(created_by=request.user)
        transactions = Transaction.objects.filter(account__in=user_accounts)
        
        # Calculate summary statistics
        total_income = transactions.filter(amount__gt=0).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        total_expenses = transactions.filter(amount__lt=0).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        net_income = total_income + total_expenses  # expenses are negative
        
        return JsonResponse({
            'total_income': float(total_income),
            'total_expenses': float(abs(total_expenses)),
            'net_income': float(net_income),
            'transaction_count': transactions.count(),
        })
    
    except Exception as e:
        logger.error(f"Error getting transaction summary: {str(e)}")
        return JsonResponse({'error': 'Unable to get transaction summary'}, status=500)