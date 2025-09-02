"""
Django views for data ingestion web interface.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from app.core.db.connection import get_db_session
from app.ingestion_service import DataIngestionService
from app.ingestion_models import DataSource, IngestionJob


@login_required
def data_sources_list(request):
    """List all data sources."""
    context = {
        'page_type': 'data_sources'
    }
    return render(request, 'ingestion/data_sources.html', context)


@login_required
def data_source_detail(request, source_id):
    """View data source details."""
    context = {
        'page_type': 'data_source_detail',
        'source_id': source_id
    }
    return render(request, 'ingestion/data_source_detail.html', context)


@login_required
def upload_data(request):
    """File upload interface."""
    context = {
        'page_type': 'upload'
    }
    return render(request, 'ingestion/upload.html', context)


@login_required
def import_jobs_list(request):
    """List all import jobs."""
    context = {
        'page_type': 'import_jobs'
    }
    return render(request, 'ingestion/import_jobs.html', context)


@login_required
def import_job_detail(request, job_id):
    """View import job details."""
    context = {
        'page_type': 'import_job_detail',
        'job_id': job_id
    }
    return render(request, 'ingestion/import_job_detail.html', context)