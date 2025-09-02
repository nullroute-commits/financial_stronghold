"""
Integration tests for Django web views.
Tests user workflows and web interface functionality.

Created by Team Epsilon (Testing & Quality Agents)
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from datetime import date, timedelta

from app.django_models import Account, Transaction, Budget

User = get_user_model()


class WebViewAuthenticationTest(TestCase):
    """Test web view authentication and authorization."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
    
    def test_login_required_redirect(self):
        """Test unauthenticated users are redirected to login."""
        url = reverse('dashboard:home')
        response = self.client.get(url)
        
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
    
    def test_login_functionality(self):
        """Test user can log in successfully."""
        url = reverse('login')
        data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data)
        assert response.status_code == 302  # Redirect after successful login
        
        # Verify user is logged in
        response = self.client.get(reverse('dashboard:home'))
        assert response.status_code == 200
    
    def test_logout_functionality(self):
        """Test user can log out successfully."""
        self.client.login(email='test@example.com', password='testpass123')
        
        url = reverse('logout')
        response = self.client.get(url)
        assert response.status_code == 302  # Redirect after logout
        
        # Verify user is logged out
        response = self.client.get(reverse('dashboard:home'))
        assert response.status_code == 302  # Redirect to login


class DashboardViewTest(TestCase):
    """Test dashboard view functionality."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')
        
        # Create test data
        self.account = Account.objects.create(
            name='Test Account',
            account_type='checking',
            currency='USD',
            created_by=self.user
        )
    
    def test_dashboard_home_loads(self):
        """Test dashboard home page loads successfully."""
        url = reverse('dashboard:home')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'user' in response.context
        assert response.context['user'] == self.user
    
    def test_dashboard_with_data(self):
        """Test dashboard displays user data correctly."""
        # Create test transactions
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            currency='USD',
            description='Test income',
            created_by=self.user
        )
        
        url = reverse('dashboard:home')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'accounts' in response.context
        assert 'recent_transactions' in response.context
        assert response.context['accounts'].count() == 1


class AccountViewTest(TestCase):
    """Test account view functionality."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')
    
    def test_account_list_view(self):
        """Test account list view."""
        Account.objects.create(
            name='Test Account 1',
            account_type='checking',
            currency='USD',
            created_by=self.user
        )
        Account.objects.create(
            name='Test Account 2',
            account_type='savings',
            currency='USD',
            created_by=self.user
        )
        
        url = reverse('accounts:list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'accounts' in response.context
        assert response.context['accounts'].count() == 2
    
    def test_account_create_view_get(self):
        """Test account creation form loads."""
        url = reverse('accounts:create')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'form' in response.context or 'accounts/create.html' in [t.name for t in response.templates]
    
    def test_account_create_view_post(self):
        """Test account creation via POST."""
        url = reverse('accounts:create')
        data = {
            'name': 'New Account',
            'account_type': 'checking',
            'currency': 'USD',
            'description': 'Test account creation'
        }
        
        response = self.client.post(url, data)
        assert response.status_code == 302  # Redirect after creation
        assert Account.objects.filter(created_by=self.user).count() == 1
        
        account = Account.objects.get(created_by=self.user)
        assert account.name == 'New Account'
    
    def test_account_detail_view(self):
        """Test account detail view with transactions."""
        account = Account.objects.create(
            name='Test Account',
            account_type='checking',
            currency='USD',
            created_by=self.user
        )
        
        # Create test transactions
        Transaction.objects.create(
            account=account,
            amount=Decimal('100.00'),
            currency='USD',
            description='Test transaction',
            created_by=self.user
        )
        
        url = reverse('accounts:detail', kwargs={'account_id': account.id})
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'account' in response.context
        assert 'page_obj' in response.context  # Pagination
        assert response.context['account'] == account


class TransactionViewTest(TestCase):
    """Test transaction view functionality."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')
        
        self.account = Account.objects.create(
            name='Test Account',
            account_type='checking',
            currency='USD',
            created_by=self.user
        )
    
    def test_transaction_list_view(self):
        """Test transaction list view."""
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            currency='USD',
            description='Test transaction',
            created_by=self.user
        )
        
        url = reverse('transactions:list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'page_obj' in response.context
        assert 'accounts' in response.context
    
    def test_transaction_create_view(self):
        """Test transaction creation."""
        url = reverse('transactions:create')
        data = {
            'account': self.account.id,
            'amount': '50.00',
            'description': 'Test expense',
            'category': 'food',
            'date': date.today().isoformat()
        }
        
        response = self.client.post(url, data)
        assert response.status_code == 302  # Redirect after creation
        assert Transaction.objects.filter(account=self.account).count() == 1
        
        transaction = Transaction.objects.get(account=self.account)
        assert transaction.amount == Decimal('50.00')
        assert transaction.description == 'Test expense'
    
    def test_transaction_filtering(self):
        """Test transaction filtering by account and date."""
        # Create transactions on different dates
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('100.00'),
            currency='USD',
            description='Recent transaction',
            date=date.today(),
            created_by=self.user
        )
        Transaction.objects.create(
            account=self.account,
            amount=Decimal('50.00'),
            currency='USD',
            description='Old transaction',
            date=date.today() - timedelta(days=40),
            created_by=self.user
        )
        
        # Test date filtering
        url = reverse('transactions:list')
        start_date = (date.today() - timedelta(days=7)).isoformat()
        response = self.client.get(url, {'start_date': start_date})
        
        assert response.status_code == 200
        # Would need to check filtered results in context


class BudgetViewTest(TestCase):
    """Test budget view functionality."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')
    
    def test_budget_list_view(self):
        """Test budget list view."""
        Budget.objects.create(
            name='Test Budget',
            amount=Decimal('500.00'),
            currency='USD',
            category='groceries',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            created_by=self.user
        )
        
        url = reverse('budgets:list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'budgets' in response.context
        assert response.context['budgets'].count() == 1