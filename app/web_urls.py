"""
URL configuration for Django web interface.
Complete routing for all web views and functionality.

Last updated: 2025-01-02 by Team Zeta (Frontend & UX Agents)
"""

from django.urls import path, include
from . import web_views

# Dashboard URLs
dashboard_patterns = [
    path('', web_views.dashboard_home, name='home'),
]

# Account URLs  
account_patterns = [
    path('', web_views.accounts_list, name='list'),
    path('create/', web_views.account_create, name='create'),
    path('<uuid:account_id>/', web_views.account_detail, name='detail'),
    path('<uuid:account_id>/edit/', web_views.account_edit, name='edit'),
    path('<uuid:account_id>/delete/', web_views.account_delete, name='delete'),
]

# Transaction URLs
transaction_patterns = [
    path('', web_views.transactions_list, name='list'),
    path('create/', web_views.transaction_create, name='create'),
    path('<uuid:transaction_id>/', web_views.transaction_detail, name='detail'),
    path('<uuid:transaction_id>/edit/', web_views.transaction_edit, name='edit'),
    path('<uuid:transaction_id>/delete/', web_views.transaction_delete, name='delete'),
]

# Budget URLs
budget_patterns = [
    path('', web_views.budgets_list, name='list'),
    path('create/', web_views.budget_create, name='create'),
    path('<uuid:budget_id>/', web_views.budget_detail, name='detail'),
    path('<uuid:budget_id>/edit/', web_views.budget_edit, name='edit'),
    path('<uuid:budget_id>/delete/', web_views.budget_delete, name='delete'),
    path('<uuid:budget_id>/status/', web_views.budget_status, name='status'),
]

# AJAX API URLs for web interface
ajax_patterns = [
    path('account/<uuid:account_id>/balance/', web_views.api_account_balance, name='account_balance'),
    path('transaction/summary/', web_views.api_transaction_summary, name='transaction_summary'),
    path('budget/<uuid:budget_id>/status/', web_views.api_budget_status, name='budget_status'),
]

# Authentication URLs
auth_patterns = [
    path('login/', web_views.login_view, name='login'),
    path('logout/', web_views.logout_view, name='logout'),
    path('register/', web_views.register_view, name='register'),
    path('password-reset/', web_views.password_reset_view, name='password_reset'),
]

urlpatterns = [
    # Main dashboard
    path('', web_views.dashboard_home, name='dashboard_home'),
    
    # Namespaced URL patterns
    path('dashboard/', include((dashboard_patterns, 'dashboard'))),
    path('accounts/', include((account_patterns, 'accounts'))),
    path('transactions/', include((transaction_patterns, 'transactions'))),
    path('budgets/', include((budget_patterns, 'budgets'))),
    
    # AJAX endpoints for web interface
    path('ajax/', include((ajax_patterns, 'ajax'))),
    
    # Authentication
    path('auth/', include((auth_patterns, 'auth'))),
    
    # Alternative auth URLs for compatibility
    path('accounts/login/', web_views.login_view, name='login'),
    path('accounts/logout/', web_views.logout_view, name='logout'),
]