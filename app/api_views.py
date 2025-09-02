"""
Django REST Framework API views to replace FastAPI endpoints.
Provides RESTful API for the Financial Stronghold application.

Last updated: 2025-01-02 by Team Beta (Architecture & Backend Agents)
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q
from decimal import Decimal
from datetime import datetime, timedelta

from .django_models import (
    User, Role, Permission, AuditLog, SystemConfiguration,
    Organization, UserOrganizationLink, Account, Transaction, Budget, Fee
)
from .serializers import (
    UserSerializer, RoleSerializer, PermissionSerializer,
    AccountSerializer, TransactionSerializer, BudgetSerializer,
    OrganizationSerializer, AuditLogSerializer
)
from .permissions import TenantPermission, RBACPermission

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API responses."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TenantViewSetMixin:
    """Mixin to add tenant filtering to viewsets."""
    
    def get_queryset(self):
        """Filter queryset by tenant context."""
        queryset = super().get_queryset()
        
        if hasattr(self.request, 'tenant_type') and hasattr(self.request, 'tenant_id'):
            if self.request.tenant_type == 'organization':
                return queryset.filter(tenant_id=self.request.tenant_id)
            else:
                return queryset.filter(created_by=self.request.user)
        
        return queryset.filter(created_by=self.request.user)


class UserViewSet(viewsets.ModelViewSet):
    """API endpoints for User management."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermission]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Filter users based on tenant context."""
        if self.request.user.is_superuser:
            return User.objects.all()
        
        # Regular users can only see themselves and users in their organizations
        if hasattr(self.request, 'tenant_type') and self.request.tenant_type == 'organization':
            org_users = UserOrganizationLink.objects.filter(
                organization__tenant_id=self.request.tenant_id
            ).values_list('user_id', flat=True)
            return User.objects.filter(id__in=org_users)
        
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Change user password."""
        user = self.get_object()
        
        # Only allow users to change their own password or admins
        if user != request.user and not request.user.is_superuser:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_password = request.data.get('new_password')
        if not new_password:
            return Response(
                {'error': 'New password required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password changed successfully'})


class AccountViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """API endpoints for Account management."""
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    pagination_class = StandardResultsSetPagination
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get account balance."""
        account = self.get_object()
        
        # Calculate balance from transactions
        transactions = Transaction.objects.filter(account=account)
        balance = sum(t.amount for t in transactions)
        
        return Response({
            'account_id': account.id,
            'balance': balance,
            'currency': account.currency,
            'last_updated': datetime.now().isoformat()
        })
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get account transactions."""
        account = self.get_object()
        transactions = Transaction.objects.filter(account=account).order_by('-date')
        
        # Apply pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(transactions, request)
        
        if page is not None:
            serializer = TransactionSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class TransactionViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """API endpoints for Transaction management."""
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Filter transactions by tenant and optional account."""
        queryset = super().get_queryset()
        
        # Filter by account if specified
        account_id = self.request.query_params.get('account_id')
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        
        # Filter by date range if specified
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get transaction summary statistics."""
        queryset = self.get_queryset()
        
        total_income = sum(
            t.amount for t in queryset if t.amount > 0
        )
        total_expenses = sum(
            abs(t.amount) for t in queryset if t.amount < 0
        )
        net_income = total_income - total_expenses
        
        return Response({
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': net_income,
            'transaction_count': queryset.count(),
            'date_range': {
                'start': queryset.last().date if queryset.exists() else None,
                'end': queryset.first().date if queryset.exists() else None,
            }
        })


class BudgetViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """API endpoints for Budget management."""
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    pagination_class = StandardResultsSetPagination
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get budget status and spending analysis."""
        budget = self.get_object()
        
        # Calculate spent amount from transactions in budget period
        transactions = Transaction.objects.filter(
            account__in=budget.accounts.all(),
            date__gte=budget.start_date,
            date__lte=budget.end_date,
            category=budget.category
        )
        
        spent_amount = sum(abs(t.amount) for t in transactions if t.amount < 0)
        remaining_amount = budget.amount - spent_amount
        percentage_used = (spent_amount / budget.amount * 100) if budget.amount > 0 else 0
        
        return Response({
            'budget_id': budget.id,
            'allocated_amount': budget.amount,
            'spent_amount': spent_amount,
            'remaining_amount': remaining_amount,
            'percentage_used': round(percentage_used, 2),
            'status': 'over_budget' if spent_amount > budget.amount else 'on_track',
            'days_remaining': (budget.end_date - datetime.now().date()).days
        })


class OrganizationViewSet(viewsets.ModelViewSet):
    """API endpoints for Organization management."""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Filter organizations by user access."""
        if self.request.user.is_superuser:
            return Organization.objects.all()
        
        # Get organizations user has access to
        user_orgs = UserOrganizationLink.objects.filter(
            user=self.request.user
        ).values_list('organization_id', flat=True)
        
        return Organization.objects.filter(id__in=user_orgs)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get organization members."""
        organization = self.get_object()
        
        members = UserOrganizationLink.objects.filter(
            organization=organization
        ).select_related('user')
        
        member_data = []
        for link in members:
            member_data.append({
                'user_id': link.user.id,
                'email': link.user.email,
                'first_name': link.user.first_name,
                'last_name': link.user.last_name,
                'role': link.role,
                'joined_date': link.created_at
            })
        
        return Response(member_data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for Audit Log viewing (read-only)."""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermission]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Filter audit logs by tenant context and permissions."""
        queryset = AuditLog.objects.all()
        
        # Only superusers can see all audit logs
        if not self.request.user.is_superuser:
            # Regular users can only see their own actions
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by date range if specified
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('-timestamp')


# Health check view
class HealthCheckViewSet(viewsets.ViewSet):
    """Health check endpoints for monitoring."""
    permission_classes = []  # No authentication required
    
    def list(self, request):
        """Basic health check."""
        return Response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'framework': 'Django 5.1.3'
        })
    
    @action(detail=False, methods=['get'])
    def detailed(self, request):
        """Detailed health check with dependencies."""
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'framework': 'Django 5.1.3',
            'dependencies': {}
        }
        
        # Check database connectivity
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_data['dependencies']['database'] = 'healthy'
        except Exception as e:
            health_data['dependencies']['database'] = f'unhealthy: {str(e)}'
            health_data['status'] = 'degraded'
        
        # Check cache connectivity
        try:
            from django.core.cache import cache
            cache.set('health_check', 'test', 10)
            cache.get('health_check')
            health_data['dependencies']['cache'] = 'healthy'
        except Exception as e:
            health_data['dependencies']['cache'] = f'unhealthy: {str(e)}'
            health_data['status'] = 'degraded'
        
        return Response(health_data)