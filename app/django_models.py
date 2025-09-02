"""
Django models to replace SQLAlchemy models.
This implements the same functionality using Django ORM for consistency.

Last updated: 2025-08-31 by AI Assistant
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# Use Django's built-in JSONField for Django 3.1+
JSONField = models.JSONField

# Import custom managers
from .managers import (
    TenantAwareManager, AccountManager, TransactionManager, 
    BudgetManager, AuditLogManager, UserManager, OrganizationManager,
    PerformanceOptimizedManager
)


class BaseModel(models.Model):
    """
    Base model with common fields for all entities.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "User", on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_created"
    )
    updated_by = models.ForeignKey(
        "User", on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_updated"
    )

    class Meta:
        abstract = True


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(default=timezone.now)

    # Override username to be optional
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    
    # Custom manager
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    @property
    def full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    def has_permission(self, permission_name: str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            permission_name: Name of the permission to check

        Returns:
            True if user has permission, False otherwise
        """
        if self.is_superuser:
            return True

        return (
            self.user_permissions.filter(
                content_type__app_label="app", codename=permission_name, is_active=True
            ).exists()
            or self.groups.filter(
                permissions__content_type__app_label="app",
                permissions__codename=permission_name,
                permissions__is_active=True,
            ).exists()
        )

    def has_role(self, role_name: str) -> bool:
        """
        Check if user has a specific role (group).

        Args:
            role_name: Name of the role to check

        Returns:
            True if user has role, False otherwise
        """
        return self.groups.filter(name=role_name).exists()


class Role(models.Model):
    """
    Extended Group model for RBAC roles.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)  # System roles cannot be deleted
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    users = models.ManyToManyField(User, related_name="custom_roles", blank=True)
    permissions = models.ManyToManyField("Permission", related_name="custom_roles", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"


class Permission(models.Model):
    """
    Extended Permission model for RBAC.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    resource = models.CharField(max_length=100)  # e.g., 'user', 'role', 'permission'
    action = models.CharField(max_length=50)  # e.g., 'create', 'read', 'update', 'delete'
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)  # System permissions cannot be deleted
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.resource}:{self.action})"

    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        unique_together = ["resource", "action"]


class AuditLog(BaseModel):
    """
    Audit log model for tracking all system activities.
    """

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    session_id = models.CharField(max_length=40, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    # Action details
    action = models.CharField(max_length=50)  # e.g., 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT'
    resource_type = models.CharField(max_length=100, blank=True, null=True)  # Model name or resource type
    resource_id = models.UUIDField(blank=True, null=True)
    resource_repr = models.CharField(max_length=255, blank=True, null=True)  # String representation

    # Change tracking
    old_values = JSONField(blank=True, null=True)  # Previous values for updates
    new_values = JSONField(blank=True, null=True)  # New values for creates/updates

    # Request details
    request_method = models.CharField(max_length=10, blank=True, null=True)  # HTTP method
    request_path = models.CharField(max_length=255, blank=True, null=True)  # URL path
    request_data = JSONField(blank=True, null=True)  # Request data (sanitized)

    # Response details
    response_status = models.IntegerField(blank=True, null=True)  # HTTP status code

    # Additional metadata
    extra_metadata = JSONField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} - {self.resource_type} by {self.user}"

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]


class SystemConfiguration(BaseModel):
    """
    System configuration model for storing application settings.
    """

    key = models.CharField(max_length=100, unique=True)
    value = JSONField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)

    def __str__(self):
        return self.key

    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configurations"


# User preference and UI settings
class UserPreference(BaseModel):
    """
    Per-user UI and experience preferences.

    Stores primary fields for quick lookup along with a JSON blob for
    forward-compatible settings. Designed to support theme selection and
    related UI preferences.
    """

    THEME_LIGHT = "light"
    THEME_DARK = "dark"
    THEME_SYSTEM = "system"
    THEME_HIGH_CONTRAST = "high-contrast"

    THEME_CHOICES = [
        (THEME_LIGHT, "Light"),
        (THEME_DARK, "Dark"),
        (THEME_SYSTEM, "System"),
        (THEME_HIGH_CONTRAST, "High Contrast"),
    ]

    user = models.OneToOneField("User", on_delete=models.CASCADE, related_name="preference")

    # Primary theme selector for quick access
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default=THEME_SYSTEM)

    # Additional UI preferences stored as JSON for flexibility
    ui_preferences = JSONField(blank=True, null=True, default=dict)

    def __str__(self):
        return f"Preferences for {self.user.email}"

    class Meta:
        verbose_name = "User Preference"
        verbose_name_plural = "User Preferences"
        indexes = [
            models.Index(fields=["theme"], name="idx_userpref_theme"),
        ]

# Multi-tenancy models
class TenantType(models.TextChoices):
    USER = "user", "User"
    ORGANIZATION = "organization", "Organization"


class TenantMixin(models.Model):
    """Mixin that adds tenant scoping fields to any model."""

    tenant_type = models.CharField(max_length=20, choices=TenantType.choices, default=TenantType.USER)
    tenant_id = models.CharField(max_length=50, db_index=True)

    class Meta:
        abstract = True

    @property
    def tenant_key(self):
        """Convenient tuple used for filtering."""
        return (self.tenant_type, self.tenant_id)


class Organization(BaseModel):
    """Top-level container for a group of users."""

    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"


class UserOrganizationLink(models.Model):
    """Association table for user-organization membership with roles."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organization_links")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="user_links")
    role = models.CharField(max_length=20, default="member")
    joined_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"

    class Meta:
        unique_together = ["user", "organization"]
        verbose_name = "User Organization Link"
        verbose_name_plural = "User Organization Links"


# Financial models
class Account(BaseModel, TenantMixin):
    """Financial account model with tenant scoping."""

    name = models.CharField(max_length=120)
    account_type = models.CharField(max_length=50)  # checking, savings, credit, investment, etc.
    account_number = models.CharField(max_length=50, blank=True, null=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.account_type}) - {self.balance} {self.currency}"

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"


class Transaction(BaseModel, TenantMixin):
    """Financial transaction model with tenant scoping."""

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    description = models.TextField(blank=True, null=True)
    transaction_type = models.CharField(max_length=50)  # debit, credit, transfer, etc.
    reference_number = models.CharField(max_length=100, blank=True, null=True)

    # Account associations
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions", null=True, blank=True)
    to_account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="incoming_transactions", null=True, blank=True
    )

    # Status tracking
    status = models.CharField(max_length=20, default="completed")  # pending, completed, failed, cancelled

    # Categorization
    category = models.CharField(max_length=100, blank=True, null=True)
    tags = models.TextField(blank=True, null=True)  # JSON or comma-separated

    def __str__(self):
        return f"{self.transaction_type}: {self.amount} {self.currency} - {self.status}"

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"


class Fee(BaseModel, TenantMixin):
    """Fee model for tracking various fees with tenant scoping."""

    name = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    fee_type = models.CharField(max_length=50)  # monthly, transaction, overdraft, etc.
    description = models.TextField(blank=True, null=True)

    # Optional associations
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, null=True, blank=True, related_name="fees")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name="fees")

    # Status
    status = models.CharField(max_length=20, default="active")  # active, waived, refunded

    # Frequency for recurring fees
    frequency = models.CharField(max_length=20, blank=True, null=True)  # monthly, yearly, per_transaction

    def __str__(self):
        return f"{self.name}: {self.amount} {self.currency} - {self.fee_type}"

    class Meta:
        verbose_name = "Fee"
        verbose_name_plural = "Fees"


class Budget(BaseModel, TenantMixin):
    """Budget tracking model with tenant scoping."""

    name = models.CharField(max_length=120)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")

    # Time period
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    # Categories this budget applies to
    categories = models.TextField(blank=True, null=True)  # JSON or comma-separated

    # Status
    is_active = models.BooleanField(default=True)

    # Alert settings
    alert_threshold = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # percentage
    alert_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}: {self.spent_amount}/{self.total_amount} {self.currency}"

    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
