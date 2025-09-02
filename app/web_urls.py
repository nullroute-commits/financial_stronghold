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
    # New analytics views
    transaction_classification,
    tagging_management,
    anomaly_detection,
    transaction_patterns,
)
from app.documentation_views import (
    documentation_browser,
    get_api_documentation,
    get_schema_documentation,
    get_feature_documentation,
    get_context_help,
    get_field_help,
    search_documentation,
)
from app.ingestion_views import (
    data_sources_list,
    data_source_detail,
    upload_data,
    import_jobs_list,
    import_job_detail,
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
    
    # Analytics URLs
    path("analytics/classification/", transaction_classification, name="classification"),
    path("analytics/tagging/", tagging_management, name="tagging"),
    path("analytics/anomalies/", anomaly_detection, name="anomalies"),
    path("analytics/patterns/", transaction_patterns, name="patterns"),
    
    # Documentation URLs
    path("docs/", documentation_browser, name="docs"),
    path("docs/api/endpoint/", get_api_documentation, name="api_doc"),
    path("docs/api/schema/<str:schema_name>/", get_schema_documentation, name="schema_doc"),
    path("docs/api/feature/<str:feature>/", get_feature_documentation, name="feature_doc"),
    path("docs/api/context-help/", get_context_help, name="context_help"),
    path("docs/api/field-help/", get_field_help, name="field_help"),
    path("docs/api/search/", search_documentation, name="doc_search"),
    
    # Data Ingestion URLs
    path("data-sources/", data_sources_list, name="data_sources"),
    path("data-sources/<uuid:source_id>/", data_source_detail, name="data_source_detail"),
    path("upload/", upload_data, name="upload_data"),
    path("import-jobs/", import_jobs_list, name="import_jobs"),
    path("import-jobs/<uuid:job_id>/", import_job_detail, name="import_job_detail"),
]
