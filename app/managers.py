"""
Django model managers for optimized queries and tenant isolation.
Replaces SQLAlchemy session management with Django ORM managers.

Last updated: 2025-01-02 by Team Gamma (Database & Performance Agents)
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta


class TenantAwareManager(models.Manager):
    """Base manager for tenant-aware models."""
    
    def for_user(self, user):
        """Get queryset filtered for specific user."""
        return self.filter(created_by=user)
    
    def for_tenant(self, tenant_type, tenant_id):
        """Get queryset filtered for specific tenant."""
        if tenant_type == 'organization':
            return self.filter(tenant_id=tenant_id)
        else:
            return self.filter(created_by_id=tenant_id)


class AccountManager(TenantAwareManager):
    """Manager for Account model with optimized queries."""
    
    def with_balances(self, user=None):
        """Get accounts with calculated balances."""
        queryset = self.get_queryset()
        if user:
            queryset = queryset.filter(created_by=user)
        
        return queryset.annotate(
            balance=models.Sum('transactions__amount'),
            transaction_count=models.Count('transactions')
        ).select_related('created_by')
    
    def by_type(self, account_type, user=None):
        """Get accounts filtered by type."""
        queryset = self.filter(account_type=account_type)
        if user:
            queryset = queryset.filter(created_by=user)
        return queryset
    
    def active_accounts(self, user=None):
        """Get accounts that have had recent activity."""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        queryset = self.filter(
            transactions__date__gte=thirty_days_ago
        ).distinct()
        
        if user:
            queryset = queryset.filter(created_by=user)
        
        return queryset


class TransactionManager(TenantAwareManager):
    """Manager for Transaction model with optimized queries."""
    
    def recent(self, days=30, user=None):
        """Get recent transactions."""
        cutoff_date = timezone.now() - timedelta(days=days)
        queryset = self.filter(date__gte=cutoff_date)
        
        if user:
            queryset = queryset.filter(account__created_by=user)
        
        return queryset.select_related('account').order_by('-date')
    
    def by_category(self, category, user=None):
        """Get transactions by category."""
        queryset = self.filter(category=category)
        if user:
            queryset = queryset.filter(account__created_by=user)
        return queryset.select_related('account')
    
    def income_transactions(self, user=None):
        """Get income transactions (positive amounts)."""
        queryset = self.filter(amount__gt=0)
        if user:
            queryset = queryset.filter(account__created_by=user)
        return queryset.select_related('account')
    
    def expense_transactions(self, user=None):
        """Get expense transactions (negative amounts)."""
        queryset = self.filter(amount__lt=0)
        if user:
            queryset = queryset.filter(account__created_by=user)
        return queryset.select_related('account')
    
    def for_account(self, account):
        """Get transactions for specific account."""
        return self.filter(account=account).order_by('-date')
    
    def monthly_summary(self, year, month, user=None):
        """Get monthly transaction summary."""
        queryset = self.filter(
            date__year=year,
            date__month=month
        )
        
        if user:
            queryset = queryset.filter(account__created_by=user)
        
        return queryset.aggregate(
            total_income=models.Sum('amount', filter=models.Q(amount__gt=0)),
            total_expenses=models.Sum('amount', filter=models.Q(amount__lt=0)),
            transaction_count=models.Count('id')
        )


class BudgetManager(TenantAwareManager):
    """Manager for Budget model with optimized queries."""
    
    def active_budgets(self, user=None):
        """Get currently active budgets."""
        today = timezone.now().date()
        queryset = self.filter(
            start_date__lte=today,
            end_date__gte=today
        )
        
        if user:
            queryset = queryset.filter(created_by=user)
        
        return queryset.prefetch_related('accounts')
    
    def with_spending_status(self, user=None):
        """Get budgets with calculated spending status."""
        queryset = self.get_queryset()
        if user:
            queryset = queryset.filter(created_by=user)
        
        # This would be optimized with database functions in production
        return queryset.prefetch_related('accounts__transactions')
    
    def by_category(self, category, user=None):
        """Get budgets by category."""
        queryset = self.filter(category=category)
        if user:
            queryset = queryset.filter(created_by=user)
        return queryset


class AuditLogManager(models.Manager):
    """Manager for AuditLog model with optimized queries."""
    
    def for_user(self, user):
        """Get audit logs for specific user."""
        return self.filter(user=user).order_by('-timestamp')
    
    def for_resource(self, resource_type, resource_id=None):
        """Get audit logs for specific resource."""
        queryset = self.filter(resource_type=resource_type)
        if resource_id:
            queryset = queryset.filter(resource_id=resource_id)
        return queryset.order_by('-timestamp')
    
    def recent_activity(self, days=7, user=None):
        """Get recent audit activity."""
        cutoff_date = timezone.now() - timedelta(days=days)
        queryset = self.filter(timestamp__gte=cutoff_date)
        
        if user:
            queryset = queryset.filter(user=user)
        
        return queryset.select_related('user').order_by('-timestamp')
    
    def security_events(self, user=None):
        """Get security-related audit events."""
        security_actions = ['login', 'logout', 'failed_login', 'password_change']
        queryset = self.filter(action__in=security_actions)
        
        if user:
            queryset = queryset.filter(user=user)
        
        return queryset.select_related('user').order_by('-timestamp')


class CachedQueryMixin:
    """Mixin for adding caching to model managers."""
    
    def cached_get(self, cache_key, timeout=300, **kwargs):
        """Get object with caching."""
        result = cache.get(cache_key)
        if result is None:
            result = self.get(**kwargs)
            cache.set(cache_key, result, timeout)
        return result
    
    def cached_filter(self, cache_key, timeout=300, **kwargs):
        """Filter queryset with caching."""
        result = cache.get(cache_key)
        if result is None:
            result = list(self.filter(**kwargs))
            cache.set(cache_key, result, timeout)
        return result


class PerformanceOptimizedManager(TenantAwareManager, CachedQueryMixin):
    """Manager with performance optimizations and caching."""
    
    def get_queryset(self):
        """Get optimized queryset with select_related."""
        return super().get_queryset().select_related('created_by')


# Custom managers for specific models
class UserManager(DjangoUserManager):
    """Manager for User model extending Django's UserManager."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email)
        # Set username to email if not provided
        if 'username' not in extra_fields:
            extra_fields['username'] = email
        
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)
    
    def active_users(self):
        """Get active users only."""
        return self.filter(is_active=True)
    
    def by_organization(self, organization):
        """Get users in specific organization."""
        from .django_models import UserOrganizationLink
        user_ids = UserOrganizationLink.objects.filter(
            organization=organization
        ).values_list('user_id', flat=True)
        return self.filter(id__in=user_ids)
    
    def with_roles(self):
        """Get users with their roles prefetched."""
        return self.prefetch_related('roles__permissions')


class OrganizationManager(models.Manager):
    """Manager for Organization model."""
    
    def for_user(self, user):
        """Get organizations that user has access to."""
        from .django_models import UserOrganizationLink
        org_ids = UserOrganizationLink.objects.filter(
            user=user
        ).values_list('organization_id', flat=True)
        return self.filter(id__in=org_ids)
    
    def with_member_count(self):
        """Get organizations with member count annotation."""
        from .django_models import UserOrganizationLink
        return self.annotate(
            member_count=models.Count('userorganizationlink')
        )