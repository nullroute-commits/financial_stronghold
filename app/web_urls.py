"""
URL configuration for the web interface.
Maps URLs to Django views for the HTML interface.
"""

from django.urls import path, include
from app.web_views import (
    dashboard_home,
    accounts_list, account_detail,
    transactions_list, transaction_detail,
    budgets_list, budget_detail,
    home_redirect
)

app_name = 'web'

# Dashboard URLs
dashboard_patterns = [
    path('', dashboard_home, name='home'),
]

# Account URLs
account_patterns = [
    path('', accounts_list, name='list'),
    path('<uuid:account_id>/', account_detail, name='detail'),
]

# Transaction URLs
transaction_patterns = [
    path('', transactions_list, name='list'),
    path('<uuid:transaction_id>/', transaction_detail, name='detail'),
]

# Budget URLs
budget_patterns = [
    path('', budgets_list, name='list'),
    path('<uuid:budget_id>/', budget_detail, name='detail'),
]

urlpatterns = [
    path('', home_redirect, name='home_redirect'),
    path('dashboard/', include((dashboard_patterns, 'dashboard'), namespace='dashboard')),
    path('accounts/', include((account_patterns, 'accounts'), namespace='accounts')),
    path('transactions/', include((transaction_patterns, 'transactions'), namespace='transactions')),
    path('budgets/', include((budget_patterns, 'budgets'), namespace='budgets')),
]