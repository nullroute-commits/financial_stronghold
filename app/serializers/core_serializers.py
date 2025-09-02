"""
Core serializers for the Financial Stronghold application.
Django REST Framework serializers for core models.
"""

from rest_framework import serializers
from ..models import (
    User, Account, Transaction, Budget, Role, Permission, 
    AuditLog, Organization, UserOrganizationLink
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for Account model."""
    
    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model."""
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer for Budget model."""
    
    class Meta:
        model = Budget
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    
    class Meta:
        model = Role
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model."""
    
    class Meta:
        model = Permission
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model."""
    
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model."""
    
    class Meta:
        model = Organization
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserOrganizationLinkSerializer(serializers.ModelSerializer):
    """Serializer for UserOrganizationLink model."""
    
    class Meta:
        model = UserOrganizationLink
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']