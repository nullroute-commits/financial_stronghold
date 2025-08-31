"""
Django admin configuration for Financial Stronghold models.

Last updated: 2025-08-31 by AI Assistant
"""

import json

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import (
    Account,
    AuditLog,
    Budget,
    Fee,
    Organization,
    Permission,
    Role,
    SystemConfiguration,
    Transaction,
    User,
    UserOrganizationLink,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model."""

    list_display = ("email", "username", "first_name", "last_name", "is_active", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser", "date_joined")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin interface for Role model."""

    list_display = ("name", "description", "is_active", "is_system", "created_at")
    list_filter = ("is_active", "is_system", "created_at")
    search_fields = ("name", "description")
    filter_horizontal = ("users", "permissions")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("name", "description")}),
        ("Status", {"fields": ("is_active", "is_system")}),
        ("Associations", {"fields": ("users", "permissions")}),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Admin interface for Permission model."""

    list_display = ("name", "resource", "action", "is_active", "is_system", "created_at")
    list_filter = ("resource", "action", "is_active", "is_system", "created_at")
    search_fields = ("name", "resource", "action", "description")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("name", "description")}),
        ("Resource", {"fields": ("resource", "action")}),
        ("Status", {"fields": ("is_active", "is_system")}),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model."""

    list_display = ("action", "user", "resource_type", "ip_address", "created_at")
    list_filter = ("action", "resource_type", "created_at", "response_status")
    search_fields = ("action", "resource_type", "user__email", "ip_address", "message")
    readonly_fields = ("created_at", "updated_at", "formatted_old_values", "formatted_new_values", "formatted_metadata")
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("action", "user", "session_id")}),
        ("Request Info", {"fields": ("ip_address", "user_agent", "request_method", "request_path")}),
        ("Resource Info", {"fields": ("resource_type", "resource_id", "resource_repr")}),
        ("Response Info", {"fields": ("response_status", "message")}),
        ("Data Changes", {"fields": ("formatted_old_values", "formatted_new_values")}),
        ("Metadata", {"fields": ("formatted_metadata", "created_at", "updated_at")}),
    )

    def formatted_old_values(self, obj):
        """Format old values as HTML."""
        if obj.old_values:
            return format_html("<pre>{}</pre>", json.dumps(obj.old_values, indent=2))
        return "-"

    formatted_old_values.short_description = "Old Values"

    def formatted_new_values(self, obj):
        """Format new values as HTML."""
        if obj.new_values:
            return format_html("<pre>{}</pre>", json.dumps(obj.new_values, indent=2))
        return "-"

    formatted_new_values.short_description = "New Values"

    def formatted_metadata(self, obj):
        """Format metadata as HTML."""
        if obj.extra_metadata:
            return format_html("<pre>{}</pre>", json.dumps(obj.extra_metadata, indent=2))
        return "-"

    formatted_metadata.short_description = "Metadata"


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for SystemConfiguration model."""

    list_display = ("key", "description", "is_active", "is_system", "created_at")
    list_filter = ("is_active", "is_system", "created_at")
    search_fields = ("key", "description")
    readonly_fields = ("created_at", "updated_at", "formatted_value")

    fieldsets = (
        (None, {"fields": ("key", "description")}),
        ("Value", {"fields": ("formatted_value", "value")}),
        ("Status", {"fields": ("is_active", "is_system")}),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )

    def formatted_value(self, obj):
        """Format value as HTML."""
        if obj.value:
            import json

            return format_html("<pre>{}</pre>", json.dumps(obj.value, indent=2))
        return "-"

    formatted_value.short_description = "Formatted Value"


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin interface for Organization model."""

    list_display = ("name", "user_count", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at", "user_count")

    def user_count(self, obj):
        """Get user count for organization."""
        return obj.user_links.count()

    user_count.short_description = "Users"


@admin.register(UserOrganizationLink)
class UserOrganizationLinkAdmin(admin.ModelAdmin):
    """Admin interface for UserOrganizationLink model."""

    list_display = ("user", "organization", "role", "joined_at")
    list_filter = ("role", "joined_at")
    search_fields = ("user__email", "organization__name")
    readonly_fields = ("joined_at",)


# Financial Models Admin


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """Admin interface for Account model."""

    list_display = ("name", "account_type", "balance", "currency", "tenant_info", "is_active", "created_at")
    list_filter = ("account_type", "currency", "is_active", "tenant_type", "created_at")
    search_fields = ("name", "account_number", "description")
    readonly_fields = ("created_at", "updated_at", "tenant_info")

    fieldsets = (
        (None, {"fields": ("name", "account_type", "account_number")}),
        ("Financial", {"fields": ("balance", "currency")}),
        ("Tenant", {"fields": ("tenant_type", "tenant_id", "tenant_info")}),
        ("Status", {"fields": ("is_active", "description")}),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )

    def tenant_info(self, obj):
        """Display tenant information."""
        return f"{obj.tenant_type}: {obj.tenant_id}"

    tenant_info.short_description = "Tenant"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for Transaction model."""

    list_display = ("description", "amount", "currency", "transaction_type", "status", "tenant_info", "created_at")
    list_filter = ("transaction_type", "status", "currency", "tenant_type", "created_at")
    search_fields = ("description", "reference_number", "category")
    readonly_fields = ("created_at", "updated_at", "tenant_info")

    fieldsets = (
        (None, {"fields": ("description", "transaction_type", "reference_number")}),
        ("Financial", {"fields": ("amount", "currency")}),
        ("Accounts", {"fields": ("account", "to_account")}),
        ("Tenant", {"fields": ("tenant_type", "tenant_id", "tenant_info")}),
        ("Categorization", {"fields": ("category", "tags")}),
        ("Status", {"fields": ("status",)}),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )

    def tenant_info(self, obj):
        """Display tenant information."""
        return f"{obj.tenant_type}: {obj.tenant_id}"

    tenant_info.short_description = "Tenant"


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    """Admin interface for Fee model."""

    list_display = ("name", "amount", "currency", "fee_type", "status", "tenant_info", "created_at")
    list_filter = ("fee_type", "status", "currency", "frequency", "tenant_type", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at", "tenant_info")

    def tenant_info(self, obj):
        """Display tenant information."""
        return f"{obj.tenant_type}: {obj.tenant_id}"

    tenant_info.short_description = "Tenant"


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """Admin interface for Budget model."""

    list_display = (
        "name",
        "spent_amount",
        "total_amount",
        "currency",
        "progress",
        "is_active",
        "tenant_info",
        "created_at",
    )
    list_filter = ("is_active", "currency", "tenant_type", "alert_enabled", "created_at")
    search_fields = ("name", "categories")
    readonly_fields = ("created_at", "updated_at", "tenant_info", "progress")

    fieldsets = (
        (None, {"fields": ("name", "categories")}),
        ("Budget", {"fields": ("total_amount", "spent_amount", "currency", "progress")}),
        ("Period", {"fields": ("start_date", "end_date")}),
        ("Tenant", {"fields": ("tenant_type", "tenant_id", "tenant_info")}),
        ("Alerts", {"fields": ("alert_enabled", "alert_threshold")}),
        ("Status", {"fields": ("is_active",)}),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )

    def tenant_info(self, obj):
        """Display tenant information."""
        return f"{obj.tenant_type}: {obj.tenant_id}"

    tenant_info.short_description = "Tenant"

    def progress(self, obj):
        """Calculate budget progress."""
        if obj.total_amount and obj.total_amount > 0:
            percentage = (obj.spent_amount / obj.total_amount) * 100
            return f"{percentage:.1f}%"
        return "0%"

    progress.short_description = "Progress"


# Add some additional admin customizations
admin.site.site_header = "Financial Stronghold Administration"
admin.site.site_title = "Financial Stronghold Admin"
admin.site.index_title = "Welcome to Financial Stronghold Administration"
