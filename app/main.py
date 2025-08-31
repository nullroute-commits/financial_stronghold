"""Multi-tenancy extension for Financial Stronghold."""

from fastapi import FastAPI, Depends
from app.api import router as financial_router
from app.auth import get_tenant_context

app = FastAPI(
    title="Financial Stronghold Multi-Tenant API",
    description="A production-ready multi-tenant financial services API",
    version="1.0.0",
)

# Include financial endpoints
app.include_router(financial_router)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "Financial Stronghold Multi-Tenant API",
        "version": "1.0.0",
        "features": [
            "Multi-tenant data isolation",
            "User and Organization tenants",
            "Role-based permissions",
            "Financial account management",
            "Transaction tracking",
            "Fee management",
            "Budget tracking",
        ],
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/tenant/info")
def get_tenant_info(tenant_context: dict = Depends(get_tenant_context)):
    """Get current tenant information."""
    return {
        "tenant_type": tenant_context["tenant_type"],
        "tenant_id": tenant_context["tenant_id"],
        "user_id": str(tenant_context["user"].id),
        "user_email": tenant_context["user"].email,
        "is_organization": tenant_context["is_organization"],
        "is_user": tenant_context["is_user"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
