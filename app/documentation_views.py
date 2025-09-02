"""
Django views for serving documentation to the web GUI.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from app.documentation_service import documentation_service


@login_required
@require_http_methods(["GET"])
def get_api_documentation(request, endpoint):
    """Get documentation for a specific API endpoint."""
    doc_data = documentation_service.get_api_documentation(endpoint)
    return JsonResponse(doc_data)


@login_required
@require_http_methods(["GET"])
def get_schema_documentation(request, schema_name):
    """Get documentation for a Pydantic schema."""
    doc_data = documentation_service.get_schema_documentation(schema_name)
    return JsonResponse(doc_data)


@login_required
@require_http_methods(["GET"])
def get_feature_documentation(request, feature):
    """Get documentation for a specific feature."""
    doc_data = documentation_service.get_feature_documentation(feature)
    return JsonResponse(doc_data)


@login_required
@require_http_methods(["GET"])
def get_context_help(request):
    """Get context-sensitive help for the current page."""
    page_type = request.GET.get('page_type', '')
    context = {
        'path': request.GET.get('path', ''),
        'params': dict(request.GET.items())
    }
    help_data = documentation_service.get_context_help(page_type, context)
    return JsonResponse(help_data)


@login_required
@require_http_methods(["GET"])
def get_field_help(request):
    """Get help text for a specific model field."""
    model_name = request.GET.get('model', '')
    field_name = request.GET.get('field', '')
    help_text = documentation_service.get_field_help(model_name, field_name)
    return JsonResponse({'help_text': help_text})


@login_required
@require_http_methods(["GET"])
def search_documentation(request):
    """Search across all documentation."""
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'results': []})
    
    results = documentation_service.search_documentation(query)
    return JsonResponse({'results': results})


@login_required
def documentation_browser(request):
    """Main documentation browser view."""
    # Get all available documentation
    features = ['tagging', 'multi-tenancy', 'testing', 'deployment', 'architecture', 'security']
    
    context = {
        'features': features,
        'api_endpoints': [
            '/financial/accounts',
            '/financial/transactions', 
            '/financial/budgets',
            '/financial/fees',
            '/financial/tags',
            '/financial/analytics',
            '/financial/dashboard'
        ]
    }
    
    return render(request, 'documentation/browser.html', context)