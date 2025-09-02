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
    # New views for complete API coverage
    tags_list,
    tag_create,
    tag_detail,
    classification_dashboard,
    classify_transactions,
    analytics_views_list,
    analytics_view_create,
    anomaly_detection,
    classification_config,
    classification_config_update,
    # Documentation views
    documentation_home,
    documentation_features,
    documentation_api,
    documentation_examples,
    documentation_search,
    documentation_feature_detail,
    documentation_api_detail,
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

# Tagging System URLs
tag_patterns = [
    path("", tags_list, name="list"),
    path("create/", tag_create, name="create"),
    path("<uuid:tag_id>/", tag_detail, name="detail"),
]

# Transaction Classification URLs
classification_patterns = [
    path("", classification_dashboard, name="dashboard"),
    path("classify/", classify_transactions, name="classify"),
    path("config/", classification_config, name="config"),
    path("config/update/", classification_config_update, name="config_update"),
]

# Analytics Views URLs
analytics_view_patterns = [
    path("", analytics_views_list, name="list"),
    path("create/", analytics_view_create, name="create"),
]

# Anomaly Detection URLs
anomaly_patterns = [
    path("", anomaly_detection, name="detection"),
]

# Documentation URLs
documentation_patterns = [
    path("", documentation_home, name="home"),
    path("features/", documentation_features, name="features"),
    path("api/", documentation_api, name="api"),
    path("examples/", documentation_examples, name="examples"),
    path("search/", documentation_search, name="search"),
    path("features/<str:feature_name>/", documentation_feature_detail, name="feature_detail"),
    path("api/<path:api_path>/", documentation_api_detail, name="api_detail"),
]

urlpatterns = [
    path("", home_redirect, name="home_redirect"),
    path("dashboard/", include((dashboard_patterns, "dashboard"), namespace="dashboard")),
    path("accounts/", include((account_patterns, "accounts"), namespace="accounts")),
    path("transactions/", include((transaction_patterns, "transactions"), namespace="transactions")),
    path("budgets/", include((budget_patterns, "budgets"), namespace="budgets")),
    path("fees/", include((fee_patterns, "fees"), namespace="fees")),
    # New URL patterns for complete API coverage
    path("tags/", include((tag_patterns, "tags"), namespace="tags")),
    path("classification/", include((classification_patterns, "classification"), namespace="classification")),
    path("analytics/views/", include((analytics_view_patterns, "analytics_views"), namespace="analytics_views")),
    path("anomaly/", include((anomaly_patterns, "anomaly"), namespace="anomaly")),
    # Documentation URLs
    path("docs/", include((documentation_patterns, "documentation"), namespace="documentation")),
]
