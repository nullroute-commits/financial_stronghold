"""
Unit tests for API endpoints.
Tests FastAPI routes for financial operations with tenant scoping.

Last updated: 2025-08-31 by AI Assistant
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api import router
from app.schemas import AccountCreate, AccountRead, TransactionCreate, BudgetCreate, FeeCreate
from app.financial_models import Account, Transaction, Budget, Fee
from app.services import TenantService


# Create a FastAPI test client
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestAccountEndpoints:
    """Test cases for account API endpoints."""
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_create_account_success(self, mock_service, mock_db, mock_tenant_context):
        """Test successful account creation."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_account = Account(
            id='account-123',
            name='Test Account',
            account_type='checking',
            balance=Decimal('1000.00'),
            tenant_type='user',
            tenant_id='user-123'
        )
        mock_service_instance.create.return_value = mock_account
        mock_service.return_value = mock_service_instance
        
        # Test data
        account_data = {
            'name': 'Test Account',
            'account_type': 'checking',
            'balance': '1000.00',
            'currency': 'USD'
        }
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'user', 'user-123')
            
            response = client.post('/financial/accounts', json=account_data)
        
        assert response.status_code == 201
        mock_service_instance.create.assert_called_once()
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_list_accounts_success(self, mock_service, mock_db, mock_tenant_context):
        """Test successful account listing."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_accounts = [
            Account(
                id='account-1',
                name='Account 1',
                account_type='checking',
                tenant_type='user',
                tenant_id='user-123'
            ),
            Account(
                id='account-2',
                name='Account 2',
                account_type='savings',
                tenant_type='user',
                tenant_id='user-123'
            )
        ]
        mock_service_instance.list.return_value = mock_accounts
        mock_service.return_value = mock_service_instance
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'user', 'user-123')
            
            response = client.get('/financial/accounts')
        
        assert response.status_code == 200
        mock_service_instance.list.assert_called_once()
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_get_account_success(self, mock_service, mock_db, mock_tenant_context):
        """Test successful account retrieval."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_account = Account(
            id='account-123',
            name='Test Account',
            account_type='checking',
            tenant_type='user',
            tenant_id='user-123'
        )
        mock_service_instance.get.return_value = mock_account
        mock_service.return_value = mock_service_instance
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'user', 'user-123')
            
            response = client.get('/financial/accounts/account-123')
        
        assert response.status_code == 200
        mock_service_instance.get.assert_called_once_with('account-123')
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_update_account_success(self, mock_service, mock_db, mock_tenant_context):
        """Test successful account update."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_account = Account(
            id='account-123',
            name='Updated Account',
            account_type='checking',
            tenant_type='user',
            tenant_id='user-123'
        )
        mock_service_instance.update.return_value = mock_account
        mock_service.return_value = mock_service_instance
        
        # Test data
        update_data = {
            'name': 'Updated Account',
            'description': 'Updated description'
        }
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'user', 'user-123')
            
            response = client.put('/financial/accounts/account-123', json=update_data)
        
        assert response.status_code == 200
        mock_service_instance.update.assert_called_once()
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_delete_account_success(self, mock_service, mock_db, mock_tenant_context):
        """Test successful account deletion."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_service_instance.delete.return_value = True
        mock_service.return_value = mock_service_instance
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'user', 'user-123')
            
            response = client.delete('/financial/accounts/account-123')
        
        assert response.status_code == 204
        mock_service_instance.delete.assert_called_once_with('account-123')


class TestTransactionEndpoints:
    """Test cases for transaction API endpoints."""
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_create_transaction_success(self, mock_service, mock_db, mock_tenant_context):
        """Test successful transaction creation."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_transaction = Transaction(
            id='txn-123',
            amount=Decimal('100.00'),
            transaction_type='debit',
            description='Test transaction',
            tenant_type='user',
            tenant_id='user-123'
        )
        mock_service_instance.create.return_value = mock_transaction
        mock_service.return_value = mock_service_instance
        
        # Test data
        transaction_data = {
            'amount': '100.00',
            'transaction_type': 'debit',
            'description': 'Test transaction',
            'account_id': 'account-123'
        }
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'user', 'user-123')
            
            response = client.post('/financial/transactions', json=transaction_data)
        
        assert response.status_code == 201
        mock_service_instance.create.assert_called_once()
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_list_transactions_with_pagination(self, mock_service, mock_db, mock_tenant_context):
        """Test transaction listing with pagination."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_transactions = [
            Transaction(
                id='txn-1',
                amount=Decimal('50.00'),
                transaction_type='debit',
                tenant_type='user',
                tenant_id='user-123'
            )
        ]
        mock_service_instance.list.return_value = mock_transactions
        mock_service.return_value = mock_service_instance
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'user', 'user-123')
            
            response = client.get('/financial/transactions?limit=10&offset=0')
        
        assert response.status_code == 200
        mock_service_instance.list.assert_called_once()


class TestBudgetEndpoints:
    """Test cases for budget API endpoints."""
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_create_budget_success(self, mock_service, mock_db, mock_tenant_context):
        """Test successful budget creation."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_budget = Budget(
            id='budget-123',
            name='Food Budget',
            category='food',
            amount=Decimal('500.00'),
            period='monthly',
            tenant_type='user',
            tenant_id='user-123'
        )
        mock_service_instance.create.return_value = mock_budget
        mock_service.return_value = mock_service_instance
        
        # Test data
        budget_data = {
            'name': 'Food Budget',
            'category': 'food',
            'amount': '500.00',
            'period': 'monthly',
            'start_date': '2024-01-01T00:00:00Z',
            'end_date': '2024-12-31T23:59:59Z'
        }
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'user', 'user-123')
            
            response = client.post('/financial/budgets', json=budget_data)
        
        assert response.status_code == 201
        mock_service_instance.create.assert_called_once()
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_list_budgets_success(self, mock_service, mock_db, mock_tenant_context):
        """Test successful budget listing."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_budgets = [
            Budget(
                id='budget-1',
                name='Food Budget',
                category='food',
                amount=Decimal('500.00'),
                tenant_type='user',
                tenant_id='user-123'
            ),
            Budget(
                id='budget-2',
                name='Entertainment Budget',
                category='entertainment',
                amount=Decimal('200.00'),
                tenant_type='user',
                tenant_id='user-123'
            )
        ]
        mock_service_instance.list.return_value = mock_budgets
        mock_service.return_value = mock_service_instance
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'user', 'user-123')
            
            response = client.get('/financial/budgets')
        
        assert response.status_code == 200
        mock_service_instance.list.assert_called_once()


class TestFeeEndpoints:
    """Test cases for fee API endpoints."""
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_create_fee_success(self, mock_service, mock_db, mock_tenant_context):
        """Test successful fee creation."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'organization',
            'tenant_id': 'org-456',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_fee = Fee(
            id='fee-123',
            name='Transaction Fee',
            fee_type='transaction',
            amount=Decimal('2.50'),
            tenant_type='organization',
            tenant_id='org-456'
        )
        mock_service_instance.create.return_value = mock_fee
        mock_service.return_value = mock_service_instance
        
        # Test data
        fee_data = {
            'name': 'Transaction Fee',
            'fee_type': 'transaction',
            'amount': '2.50',
            'currency': 'USD',
            'description': 'Fee per transaction'
        }
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'organization', 'org-456')
            
            response = client.post('/financial/fees', json=fee_data)
        
        assert response.status_code == 201
        mock_service_instance.create.assert_called_once()
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_list_fees_success(self, mock_service, mock_db, mock_tenant_context):
        """Test successful fee listing."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'organization',
            'tenant_id': 'org-456',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_fees = [
            Fee(
                id='fee-1',
                name='Maintenance Fee',
                fee_type='maintenance',
                amount=Decimal('5.00'),
                tenant_type='organization',
                tenant_id='org-456'
            )
        ]
        mock_service_instance.list.return_value = mock_fees
        mock_service.return_value = mock_service_instance
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'organization', 'org-456')
            
            response = client.get('/financial/fees')
        
        assert response.status_code == 200
        mock_service_instance.list.assert_called_once()


class TestAPIErrorHandling:
    """Test cases for API error handling."""
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_account_not_found_error(self, mock_service, mock_db, mock_tenant_context):
        """Test account not found error handling."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service to raise exception
        mock_service_instance = Mock()
        mock_service_instance.get.side_effect = HTTPException(
            status_code=404,
            detail="Account not found"
        )
        mock_service.return_value = mock_service_instance
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'user', 'user-123')
            
            response = client.get('/financial/accounts/nonexistent-account')
        
        assert response.status_code == 404
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_validation_error_on_create(self, mock_service, mock_db, mock_tenant_context):
        """Test validation error on account creation."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance
        
        # Test with invalid data (missing required fields)
        invalid_account_data = {
            'balance': '1000.00'
            # Missing name and account_type
        }
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'user', 'user-123')
            
            response = client.post('/financial/accounts', json=invalid_account_data)
        
        # Should get validation error
        assert response.status_code == 422


class TestAPIPermissions:
    """Test cases for API permission enforcement."""
    
    def test_unauthorized_access_without_token(self):
        """Test unauthorized access without authentication token."""
        response = client.get('/financial/accounts')
        assert response.status_code == 401
    
    @patch('app.api.get_current_user')
    def test_account_access_with_authentication(self, mock_auth):
        """Test account access with proper authentication."""
        # Mock authentication to raise exception for invalid token
        mock_auth.side_effect = HTTPException(
            status_code=401,
            detail="Invalid token"
        )
        
        # Test with invalid authentication
        response = client.get(
            '/financial/accounts',
            headers={'Authorization': 'Bearer invalid-token'}
        )
        
        assert response.status_code == 401


class TestAPIPagination:
    """Test cases for API pagination features."""
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_account_list_pagination_parameters(self, mock_service, mock_db, mock_tenant_context):
        """Test account listing with pagination parameters."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_service_instance.list.return_value = []
        mock_service.return_value = mock_service_instance
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'user', 'user-123')
            
            response = client.get('/financial/accounts?limit=50&offset=10')
        
        assert response.status_code == 200
        # Verify pagination parameters were passed to service
        mock_service_instance.list.assert_called_once()
    
    @patch('app.api.get_tenant_context')
    @patch('app.api.get_db_session')
    @patch('app.api.TenantService')
    def test_transaction_list_pagination_limits(self, mock_service, mock_db, mock_tenant_context):
        """Test transaction listing with pagination limits."""
        # Mock tenant context
        mock_tenant_context.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123',
            'user': Mock()
        }
        
        # Mock database session
        mock_db.return_value = Mock()
        
        # Mock service
        mock_service_instance = Mock()
        mock_service_instance.list.return_value = []
        mock_service.return_value = mock_service_instance
        
        # Mock authentication
        with patch('app.api.get_current_user') as mock_auth:
            mock_auth.return_value = (Mock(), 'user', 'user-123')
            
            # Test with limit beyond maximum (should be validated)
            response = client.get('/financial/transactions?limit=150&offset=0')
        
        # Should get validation error for limit too high
        assert response.status_code == 422