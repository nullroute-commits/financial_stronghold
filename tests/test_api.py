"""
Integration tests for Django REST Framework API endpoints.
Tests actual API functionality rather than artificial coverage.

Created by Team Epsilon (Testing & Quality Agents)
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta

from app.django_models import Account, Transaction, Budget, Organization

User = get_user_model()


class APIAuthenticationTest(TestCase):
    """Test API authentication and authorization."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
    
    def test_unauthenticated_access_denied(self):
        """Test unauthenticated requests are denied."""
        url = reverse('account-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_authenticated_access_allowed(self):
        """Test authenticated requests are allowed."""
        self.client.force_authenticate(user=self.user)
        url = reverse('account-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
    
    def test_session_authentication(self):
        """Test session-based authentication works."""
        self.client.login(email='test@example.com', password='testpass123')
        url = reverse('account-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK


class AccountAPITest(TestCase):
    """Test Account API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.account = Account.objects.create(
            name='Test Account',
            account_type='checking',
            currency='USD',
            description='Test account',
            created_by=self.user
        )
    
    def test_list_accounts(self):
        """Test listing user's accounts."""
        url = reverse('account-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Test Account'
    
    def test_create_account(self):
        """Test creating new account."""
        url = reverse('account-list')
        data = {
            'name': 'New Account',
            'account_type': 'savings',
            'currency': 'USD',
            'description': 'New test account'
        }
        
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Account'
        assert Account.objects.filter(created_by=self.user).count() == 2
    
    def test_account_balance_endpoint(self):
        """Test account balance calculation."""
        # Create some transactions
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            currency='USD',
            description='Income',
            created_by=self.user
        )
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('-50.00'),
            currency='USD',
            description='Expense',
            created_by=self.user
        )
        
        url = reverse('account-balance', kwargs={'pk': self.account.id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['balance'] == 50.0
        assert response.data['account_id'] == str(self.account.id)
    
    def test_account_tenant_isolation(self):
        """Test users can only access their own accounts."""
        # Create another user and account
        other_user = User.objects.create_user(
            email='other@example.com',
            first_name='Other',
            last_name='User',
            password='otherpass123'
        )
        other_account = Account.objects.create(
            name='Other Account',
            account_type='checking',
            currency='USD',
            created_by=other_user
        )
        
        # Try to access other user's account
        url = reverse('account-detail', kwargs={'pk': other_account.id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TransactionAPITest(TestCase):
    """Test Transaction API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.account = Account.objects.create(
            name='Test Account',
            account_type='checking',
            currency='USD',
            created_by=self.user
        )
    
    def test_create_transaction(self):
        """Test creating new transaction."""
        url = reverse('transaction-list')
        data = {
            'account': self.account.id,
            'amount': '100.50',
            'currency': 'USD',
            'description': 'Test transaction',
            'category': 'income',
            'date': date.today().isoformat()
        }
        
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['amount'] == '100.50'
        assert Transaction.objects.filter(account=self.account).count() == 1
    
    def test_transaction_summary_endpoint(self):
        """Test transaction summary calculation."""
        # Create test transactions
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            currency='USD',
            description='Income 1',
            created_by=self.user
        )
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('200.00'),
            currency='USD',
            description='Income 2',
            created_by=self.user
        )
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('-75.00'),
            currency='USD',
            description='Expense 1',
            created_by=self.user
        )
        
        url = reverse('transaction-summary')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_income'] == 300.0
        assert response.data['total_expenses'] == 75.0
        assert response.data['net_income'] == 225.0
        assert response.data['transaction_count'] == 3


class BudgetAPITest(TestCase):
    """Test Budget API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.account = Account.objects.create(
            name='Test Account',
            account_type='checking',
            currency='USD',
            created_by=self.user
        )
    
    def test_create_budget(self):
        """Test creating new budget."""
        url = reverse('budget-list')
        data = {
            'name': 'Monthly Budget',
            'description': 'Test budget',
            'amount': '500.00',
            'currency': 'USD',
            'category': 'groceries',
            'start_date': date.today().isoformat(),
            'end_date': (date.today() + timedelta(days=30)).isoformat(),
            'account_ids': [str(self.account.id)]
        }
        
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Monthly Budget'
        assert Budget.objects.filter(created_by=self.user).count() == 1
    
    def test_budget_status_calculation(self):
        """Test budget status calculation with spending."""
        budget = Budget.objects.create(
            name='Test Budget',
            amount=Decimal('500.00'),
            currency='USD',
            category='groceries',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            created_by=self.user
        )
        budget.accounts.add(self.account)
        
        # Create spending transaction
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('-150.00'),
            currency='USD',
            description='Grocery shopping',
            category='groceries',
            date=date.today(),
            created_by=self.user
        )
        
        url = reverse('budget-status', kwargs={'pk': budget.id})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['allocated_amount'] == 500.0
        assert response.data['spent_amount'] == 150.0
        assert response.data['remaining_amount'] == 350.0
        assert response.data['percentage_used'] == 30.0
        assert response.data['status'] == 'on_track'


class HealthCheckAPITest(TestCase):
    """Test health check endpoints."""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_basic_health_check(self):
        """Test basic health check endpoint."""
        url = reverse('health-list')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'healthy'
        assert 'timestamp' in response.data
        assert response.data['framework'] == 'Django 5.1.3'
    
    def test_detailed_health_check(self):
        """Test detailed health check with dependencies."""
        url = reverse('health-detailed')
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'dependencies' in response.data
        assert 'database' in response.data['dependencies']
        assert 'cache' in response.data['dependencies']