"""
URL configuration for the web interface.
Maps URLs to Django views for the HTML interface.
"""

from django.urls import path, include
from app.web_views import (
    dashboard_home,
    accounts_list,
    account_detail,
    account_create,
    account_edit,
    transactions_list,
    transaction_detail,
    transaction_create,
    transaction_edit,
    budgets_list,
    budget_detail,
    budget_create,
    budget_edit,
    fees_list,
    fee_detail,
    fee_create,
    fee_edit,
    analytics_dashboard,
    home_redirect,
)

app_name = "web"

# Dashboard URLs
dashboard_patterns = [
    path("", dashboard_home, name="home"),
    path("analytics/", analytics_dashboard, name="analytics"),
]

# Account URLs
account_patterns = [
    path("", accounts_list, name="list"),
    path("create/", account_create, name="create"),
    path("<uuid:account_id>/", account_detail, name="detail"),
    path("<uuid:account_id>/edit/", account_edit, name="edit"),
]

# Transaction URLs
transaction_patterns = [
    path("", transactions_list, name="list"),
    path("create/", transaction_create, name="create"),
    path("<uuid:transaction_id>/", transaction_detail, name="detail"),
    path("<uuid:transaction_id>/edit/", transaction_edit, name="edit"),
]

# Budget URLs
budget_patterns = [
    path("", budgets_list, name="list"),
    path("create/", budget_create, name="create"),
    path("<uuid:budget_id>/", budget_detail, name="detail"),
    path("<uuid:budget_id>/edit/", budget_edit, name="edit"),
]

# Fee URLs
fee_patterns = [
    path("", fees_list, name="list"),
    path("create/", fee_create, name="create"),
    path("<uuid:fee_id>/", fee_detail, name="detail"),
    path("<uuid:fee_id>/edit/", fee_edit, name="edit"),
]

urlpatterns = [
    path("", home_redirect, name="home_redirect"),
    path("dashboard/", include((dashboard_patterns, "dashboard"), namespace="dashboard")),
    path("accounts/", include((account_patterns, "accounts"), namespace="accounts")),
    path("transactions/", include((transaction_patterns, "transactions"), namespace="transactions")),
    path("budgets/", include((budget_patterns, "budgets"), namespace="budgets")),
    path("fees/", include((fee_patterns, "fees"), namespace="fees")),
]
