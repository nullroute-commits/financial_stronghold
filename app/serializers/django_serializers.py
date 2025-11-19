"""
Django REST Framework serializers for API endpoints.
Replaces FastAPI Pydantic models with DRF serializers.

Last updated: 2025-01-02 by Team Beta (Architecture & Backend Agents)
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..django_models import (
    Role, Permission, AuditLog, SystemConfiguration,
    Organization, UserOrganizationLink, Account, Transaction, Budget, Fee
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def create(self, validated_data):
        """Create user with proper password hashing."""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    permissions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all(), required=False
    )
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model."""
    
    class Meta:
        model = Permission
        fields = ['id', 'name', 'resource', 'action', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model."""
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'description', 'tenant_id', 'tenant_type',
            'created_at', 'updated_at', 'member_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'member_count']
    
    def get_member_count(self, obj):
        """Get number of organization members."""
        return UserOrganizationLink.objects.filter(organization=obj).count()


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for Account model."""
    balance = serializers.SerializerMethodField()
    transaction_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            'id', 'name', 'account_type', 'currency', 'description',
            'created_at', 'updated_at', 'balance', 'transaction_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'balance', 'transaction_count']
    
    def get_balance(self, obj):
        """Calculate account balance from transactions."""
        transactions = Transaction.objects.filter(account=obj)
        return sum(t.amount for t in transactions)
    
    def get_transaction_count(self, obj):
        """Get number of transactions for this account."""
        return Transaction.objects.filter(account=obj).count()


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model."""
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'account', 'account_name', 'amount', 'currency', 'date',
            'description', 'category', 'tags', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'account_name']
    
    def validate_amount(self, value):
        """Validate transaction amount."""
        if value == 0:
            raise serializers.ValidationError("Transaction amount cannot be zero")
        return value


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer for Budget model."""
    accounts = AccountSerializer(many=True, read_only=True)
    account_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )
    spent_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Budget
        fields = [
            'id', 'name', 'description', 'amount', 'currency', 'category',
            'start_date', 'end_date', 'accounts', 'account_ids',
            'spent_amount', 'remaining_amount', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'spent_amount', 'remaining_amount']
    
    def create(self, validated_data):
        """Create budget with associated accounts."""
        account_ids = validated_data.pop('account_ids', [])
        budget = Budget.objects.create(**validated_data)
        
        if account_ids:
            accounts = Account.objects.filter(id__in=account_ids)
            budget.accounts.set(accounts)
        
        return budget
    
    def update(self, instance, validated_data):
        """Update budget with associated accounts."""
        account_ids = validated_data.pop('account_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if account_ids is not None:
            accounts = Account.objects.filter(id__in=account_ids)
            instance.accounts.set(accounts)
        
        return instance
    
    def get_spent_amount(self, obj):
        """Calculate spent amount for budget period."""
        transactions = Transaction.objects.filter(
            account__in=obj.accounts.all(),
            date__gte=obj.start_date,
            date__lte=obj.end_date,
            category=obj.category
        )
        return sum(abs(t.amount) for t in transactions if t.amount < 0)
    
    def get_remaining_amount(self, obj):
        """Calculate remaining budget amount."""
        spent = self.get_spent_amount(obj)
        return obj.amount - spent


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model (read-only)."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_email', 'action', 'resource_type',
            'resource_id', 'changes', 'timestamp', 'ip_address', 'user_agent'
        ]
        read_only_fields = ['__all__']


class SystemConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for SystemConfiguration model."""
    
    class Meta:
        model = SystemConfiguration
        fields = ['id', 'key', 'value', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']