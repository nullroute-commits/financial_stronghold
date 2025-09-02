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
from .django_models import UserPreference
from .services import ThemeService

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
@require_http_methods(["GET", "POST"])
def theme_settings(request):
    """Allow users to select and save their UI theme preference."""
    if request.method == "POST":
        selected_theme = request.POST.get("theme", "system")
        if selected_theme not in {"light", "dark", "system", "high-contrast"}:
            messages.error(request, "Invalid theme selection")
            return redirect("settings_theme")

        pref, _ = UserPreference.objects.get_or_create(user=request.user, defaults={"created_by": request.user})
        pref.theme = selected_theme
        # Merge any other UI preferences if needed later
        pref.updated_by = request.user
        pref.save()

        messages.success(request, "Theme preference updated")
        response = redirect("settings_theme")
        # Also set cookie so guest pages or pre-login pages honor selection
        response.set_cookie(
            ThemeService.COOKIE_NAME,
            selected_theme,
            max_age=60 * 60 * 24 * 365,
            samesite="Lax",
            secure=False,
        )
        return response

    # GET request
    current_theme = ThemeService.get_user_theme(request.user) or ThemeService.get_system_default_theme()
    return render(request, "settings/theme.html", {"current_theme": current_theme})


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


# Additional view functions for complete web interface
@login_required
@require_http_methods(["GET", "POST"])
def account_edit(request, account_id):
    """Edit account details."""
    account = get_object_or_404(Account, id=account_id, created_by=request.user)
    
    if request.method == "POST":
        try:
            account.name = request.POST.get("name", account.name)
            account.account_type = request.POST.get("account_type", account.account_type)
            account.currency = request.POST.get("currency", account.currency)
            account.description = request.POST.get("description", account.description)
            account.save()
            
            messages.success(request, f"Account '{account.name}' updated successfully")
            return redirect("accounts:detail", account_id=account.id)
            
        except Exception as e:
            logger.error(f"Error updating account: {str(e)}")
            messages.error(request, "Error updating account")
    
    context = {"account": account}
    return render(request, "accounts/edit.html", context)


@login_required
@require_http_methods(["POST"])
def account_delete(request, account_id):
    """Delete account (with confirmation)."""
    account = get_object_or_404(Account, id=account_id, created_by=request.user)
    
    try:
        account_name = account.name
        account.delete()
        messages.success(request, f"Account '{account_name}' deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        messages.error(request, "Error deleting account")
    
    return redirect("accounts:list")


@login_required
def transaction_detail(request, transaction_id):
    """Display transaction details."""
    transaction = get_object_or_404(
        Transaction, 
        id=transaction_id, 
        account__created_by=request.user
    )
    
    context = {"transaction": transaction}
    return render(request, "transactions/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def transaction_edit(request, transaction_id):
    """Edit transaction details."""
    transaction = get_object_or_404(
        Transaction, 
        id=transaction_id, 
        account__created_by=request.user
    )
    
    if request.method == "POST":
        try:
            transaction.amount = Decimal(request.POST.get("amount", transaction.amount))
            transaction.description = request.POST.get("description", transaction.description)
            transaction.category = request.POST.get("category", transaction.category)
            date_str = request.POST.get("date")
            if date_str:
                transaction.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            transaction.save()
            
            messages.success(request, "Transaction updated successfully")
            return redirect("transactions:detail", transaction_id=transaction.id)
            
        except Exception as e:
            logger.error(f"Error updating transaction: {str(e)}")
            messages.error(request, "Error updating transaction")
    
    context = {"transaction": transaction}
    return render(request, "transactions/edit.html", context)


@login_required
@require_http_methods(["POST"])
def transaction_delete(request, transaction_id):
    """Delete transaction (with confirmation)."""
    transaction = get_object_or_404(
        Transaction, 
        id=transaction_id, 
        account__created_by=request.user
    )
    
    try:
        transaction.delete()
        messages.success(request, "Transaction deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting transaction: {str(e)}")
        messages.error(request, "Error deleting transaction")
    
    return redirect("transactions:list")


@login_required
def budget_detail(request, budget_id):
    """Display budget details and status."""
    budget = get_object_or_404(Budget, id=budget_id, created_by=request.user)
    
    # Calculate budget status
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
    
    context = {
        "budget": budget,
        "transactions": transactions[:10],  # Recent transactions
        "total_transactions": transactions.count(),
    }
    return render(request, "budgets/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def budget_create(request):
    """Create a new budget."""
    user_accounts = Account.objects.filter(created_by=request.user)
    
    if request.method == "POST":
        try:
            budget = Budget.objects.create(
                name=request.POST.get("name"),
                description=request.POST.get("description", ""),
                amount=Decimal(request.POST.get("amount")),
                currency=request.POST.get("currency", "USD"),
                category=request.POST.get("category"),
                start_date=datetime.strptime(request.POST.get("start_date"), '%Y-%m-%d').date(),
                end_date=datetime.strptime(request.POST.get("end_date"), '%Y-%m-%d').date(),
                created_by=request.user
            )
            
            # Add selected accounts to budget
            account_ids = request.POST.getlist("accounts")
            if account_ids:
                accounts = Account.objects.filter(id__in=account_ids, created_by=request.user)
                budget.accounts.set(accounts)
            
            messages.success(request, f"Budget '{budget.name}' created successfully")
            return redirect("budgets:detail", budget_id=budget.id)
            
        except Exception as e:
            logger.error(f"Error creating budget: {str(e)}")
            messages.error(request, "Error creating budget")
    
    context = {"accounts": user_accounts}
    return render(request, "budgets/create.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def budget_edit(request, budget_id):
    """Edit budget details."""
    budget = get_object_or_404(Budget, id=budget_id, created_by=request.user)
    user_accounts = Account.objects.filter(created_by=request.user)
    
    if request.method == "POST":
        try:
            budget.name = request.POST.get("name", budget.name)
            budget.description = request.POST.get("description", budget.description)
            budget.amount = Decimal(request.POST.get("amount", budget.amount))
            budget.category = request.POST.get("category", budget.category)
            
            start_date = request.POST.get("start_date")
            if start_date:
                budget.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
            end_date = request.POST.get("end_date")
            if end_date:
                budget.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            budget.save()
            
            # Update associated accounts
            account_ids = request.POST.getlist("accounts")
            if account_ids:
                accounts = Account.objects.filter(id__in=account_ids, created_by=request.user)
                budget.accounts.set(accounts)
            
            messages.success(request, f"Budget '{budget.name}' updated successfully")
            return redirect("budgets:detail", budget_id=budget.id)
            
        except Exception as e:
            logger.error(f"Error updating budget: {str(e)}")
            messages.error(request, "Error updating budget")
    
    context = {
        "budget": budget,
        "accounts": user_accounts,
        "selected_accounts": budget.accounts.all()
    }
    return render(request, "budgets/edit.html", context)


@login_required
@require_http_methods(["POST"])
def budget_delete(request, budget_id):
    """Delete budget (with confirmation)."""
    budget = get_object_or_404(Budget, id=budget_id, created_by=request.user)
    
    try:
        budget_name = budget.name
        budget.delete()
        messages.success(request, f"Budget '{budget_name}' deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting budget: {str(e)}")
        messages.error(request, "Error deleting budget")
    
    return redirect("budgets:list")


@login_required
@csrf_exempt
def budget_status(request, budget_id):
    """Get budget status via AJAX."""
    try:
        budget = get_object_or_404(Budget, id=budget_id, created_by=request.user)
        
        # Calculate budget status
        transactions = Transaction.objects.filter(
            account__created_by=request.user,
            date__gte=budget.start_date,
            date__lte=budget.end_date,
            category=budget.category
        )
        
        spent = sum(abs(t.amount) for t in transactions if t.amount < 0)
        remaining = budget.amount - spent
        percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0
        
        return JsonResponse({
            'budget_id': str(budget.id),
            'allocated_amount': float(budget.amount),
            'spent_amount': float(spent),
            'remaining_amount': float(remaining),
            'percentage_used': round(percentage, 2),
            'status': 'over_budget' if spent > budget.amount else 'on_track',
            'days_remaining': (budget.end_date - datetime.now().date()).days
        })
    
    except Exception as e:
        logger.error(f"Error getting budget status: {str(e)}")
        return JsonResponse({'error': 'Unable to get budget status'}, status=500)


@require_http_methods(["GET", "POST"])
def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    
    if request.method == "POST":
        try:
            email = request.POST.get("email")
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")
            password = request.POST.get("password")
            password_confirm = request.POST.get("password_confirm")
            
            # Validation
            if not all([email, first_name, last_name, password]):
                messages.error(request, "All fields are required")
                return render(request, "registration/register.html")
            
            if password != password_confirm:
                messages.error(request, "Passwords do not match")
                return render(request, "registration/register.html")
            
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered")
                return render(request, "registration/register.html")
            
            # Create user
            user = User.objects.create_user(
                email=email,
                username=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            messages.error(request, "Error creating account")
    
    return render(request, "registration/register.html")


@require_http_methods(["GET", "POST"])
def password_reset_view(request):
    """Password reset view (simplified)."""
    if request.method == "POST":
        email = request.POST.get("email")
        
        if email and User.objects.filter(email=email).exists():
            # In production, this would send an email
            messages.success(request, "Password reset instructions sent to your email")
        else:
            messages.error(request, "Email not found")
    
    return render(request, "registration/password_reset.html")


@login_required
@csrf_exempt
def api_budget_status(request, budget_id):
    """Get budget status via AJAX (alias for budget_status)."""
    return budget_status(request, budget_id)