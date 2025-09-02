"""
FastAPI application with Django integration.
Main entry point for the FastAPI application that uses Django ORM.

Last updated: 2025-01-21 by AI Assistant
"""

import os
import django
from django.conf import settings
from fastapi import Depends, FastAPI

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from app.api_django import router as financial_router
from app.auth import get_current_user

app = FastAPI(
    title="Financial Stronghold API",
    description="Multi-tenant financial management system",
    version="1.0.0"
)

# Include routers
app.include_router(financial_router)

@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Financial Stronghold API"}

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/protected")
def protected_route(current_user=Depends(get_current_user)):
    """Example protected route."""
    user, tenant_type, tenant_id = current_user
    return {
        "message": f"Hello {user.email}",
        "tenant_type": tenant_type,
        "tenant_id": tenant_id
    }