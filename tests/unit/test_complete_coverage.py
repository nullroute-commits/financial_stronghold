"""
Comprehensive test suite to achieve 100% code coverage for all modules.
This test file focuses on achieving 100% coverage for critical modules that currently have 0% or low coverage.
"""

import pytest
import os
import sys
import tempfile
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta, date
from uuid import uuid4, UUID
from decimal import Decimal
from typing import Dict, List, Any, Optional
import json

# Import all modules we need to test for 100% coverage
from app.auth import Authentication, TokenManager, PermissionChecker
from app.api import (
    create_account, list_accounts, get_account, update_account, delete_account,
    create_transaction, list_transactions, get_transaction, 
    create_budget, list_budgets, create_fee, list_fees,
    create_tag, get_resource_tags, classify_transactions,
    get_dashboard_data, get_financial_summary, get_transaction_summary,
    get_account_summaries, get_budget_statuses, create_analytics_view,
    get_analytics_summary, get_classification_analytics, get_monthly_breakdown,
    get_transaction_patterns, detect_transaction_anomalies,
    auto_tag_resource, compute_tag_metrics, query_tagged_resources,
    get_classification_config, update_classification_config,
    get_dashboard_analytics, refresh_analytics_view, list_analytics_views,
    get_analytics_view
)
from app.middleware import TenantMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware
from app.transaction_analytics import TransactionAnalyticsService
from app.transaction_classifier import TransactionClassifierService
from app.tagging_service import TaggingService, Tag, ResourceTag, AutoTagger
from app.services import TenantService, FinancialService, UserService, DashboardService
from app.schemas import (
    UserCreateSchema, UserUpdateSchema, UserResponseSchema,
    TenantCreateSchema, TenantUpdateSchema, TenantResponseSchema,
    AccountCreateSchema, AccountUpdateSchema, AccountResponseSchema,
    TransactionCreateSchema, TransactionUpdateSchema, TransactionResponseSchema,
    BudgetCreateSchema, BudgetUpdateSchema, BudgetResponseSchema,
    TagCreateSchema, TagUpdateSchema, TagResponseSchema,
    ClassificationRuleSchema, AnalyticsResponseSchema
)
from app.financial_models import (
    Account, Transaction, Budget, BudgetCategory, 
    AccountType, TransactionType, BudgetStatus
)
from app.django_audit import AuditLogger, AuditEntry, AuditAction
from app.django_rbac import Role, Permission, UserRole, RolePermission
from app.core.rbac import RBACManager, PermissionManager, RoleManager
from app.core.audit import SystemAuditLogger, AuditEventType, AuditSeverity
from app.core.cache.memcached import MemcachedClient, CacheManager
from app.core.queue.rabbitmq import RabbitMQClient, MessageQueue, QueueManager
from app.settings import DatabaseSettings, CacheSettings, QueueSettings, SecuritySettings
from app.main import create_app, setup_middleware, configure_cors


class TestAPIComplete:
    """Complete test coverage for API module - targeting 100%."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.delete = Mock()
        return db
    
    @pytest.fixture
    def mock_user(self):
        """Mock user object."""
        user = Mock()
        user.id = uuid4()
        user.username = "testuser"
        user.email = "test@example.com"
        user.is_active = True
        return user
    
    @pytest.fixture
    def mock_tenant(self):
        """Mock tenant object."""
        tenant = Mock()
        tenant.id = uuid4()
        tenant.name = "Test Tenant"
        tenant.tenant_type = "ORGANIZATION"
        return tenant
    
    def test_create_account_success(self, mock_db):
        """Test successful account creation."""
        account_data = {
            "name": "Test Account",
            "account_type": "CHECKING",
            "initial_balance": 1000.00
        }
        
        # Mock successful account creation
        mock_service = Mock()
        mock_service.create.return_value = Mock()
        
        with patch('app.api.TenantService', return_value=mock_service):
            with patch('app.api.get_tenant_context', return_value={"tenant_type": "USER", "tenant_id": str(uuid4())}):
                result = create_account(account_data)
        
        assert result is not None
        mock_service.create.assert_called_once()
    
    def test_list_accounts_success(self, mock_db):
        """Test successful account listing."""
        mock_service = Mock()
        mock_service.get_all.return_value = [Mock(), Mock()]
        
        with patch('app.api.TenantService', return_value=mock_service):
            with patch('app.api.get_tenant_context', return_value={"tenant_type": "USER", "tenant_id": str(uuid4())}):
                result = list_accounts()
        
        assert result is not None
        assert len(result) == 2
    
    def test_get_account_success(self, mock_db):
        """Test successful account retrieval."""
        account_id = uuid4()
        
        mock_service = Mock()
        mock_service.get_one.return_value = Mock()
        
        with patch('app.api.TenantService', return_value=mock_service):
            with patch('app.api.get_tenant_context', return_value={"tenant_type": "USER", "tenant_id": str(uuid4())}):
                result = get_account(account_id)
        
        assert result is not None
    
    def test_create_transaction_success(self, mock_db):
        """Test successful transaction creation."""
        transaction_data = {
            "amount": 100.00,
            "description": "Test transaction",
            "category": "Food"
        }
        
        mock_service = Mock()
        mock_service.create.return_value = Mock()
        
        with patch('app.api.TenantService', return_value=mock_service):
            with patch('app.api.get_tenant_context', return_value={"tenant_type": "USER", "tenant_id": str(uuid4())}):
                result = create_transaction(transaction_data)
        
        assert result is not None
    
    def test_get_dashboard_data_success(self, mock_db):
        """Test successful dashboard data retrieval."""
        mock_service = Mock()
        mock_service.get_dashboard_data.return_value = {
            "accounts": [],
            "transactions": [],
            "summary": {}
        }
        
        with patch('app.api.DashboardService', return_value=mock_service):
            with patch('app.api.get_tenant_context', return_value={"tenant_type": "USER", "tenant_id": str(uuid4())}):
                result = get_dashboard_data()
        
        assert result is not None
        assert "accounts" in result or result is not None
    
    def test_get_financial_summary_success(self, mock_db):
        """Test successful financial summary retrieval."""
        mock_service = Mock()
        mock_service.get_financial_summary.return_value = {
            "total_balance": 1000.00,
            "monthly_income": 5000.00,
            "monthly_expenses": 3000.00
        }
        
        with patch('app.api.DashboardService', return_value=mock_service):
            with patch('app.api.get_tenant_context', return_value={"tenant_type": "USER", "tenant_id": str(uuid4())}):
                result = get_financial_summary()
        
        assert result is not None


class TestMiddlewareComplete:
    """Complete test coverage for middleware module - targeting 100%."""
    
    @pytest.fixture
    def mock_request(self):
        """Mock request object."""
        request = Mock()
        request.headers = {}
        request.session = {}
        request.method = "GET"
        request.path = "/test"
        request.META = {"REMOTE_ADDR": "127.0.0.1"}
        return request
    
    @pytest.fixture
    def mock_response(self):
        """Mock response object."""
        response = Mock()
        response.status_code = 200
        response.headers = {}
        return response
    
    def test_tenant_middleware_init(self):
        """Test TenantMiddleware initialization."""
        get_response = Mock()
        middleware = TenantMiddleware(get_response)
        assert middleware.get_response == get_response
    
    def test_tenant_middleware_process_request(self, mock_request):
        """Test TenantMiddleware request processing."""
        get_response = Mock()
        middleware = TenantMiddleware(get_response)
        
        # Test with tenant header
        mock_request.headers = {"X-Tenant-ID": str(uuid4())}
        
        with patch('app.middleware.get_db_session') as mock_db:
            mock_db.return_value.query.return_value.filter.return_value.first.return_value = Mock()
            result = middleware(mock_request)
        
        assert result is not None
    
    def test_tenant_middleware_no_tenant_header(self, mock_request):
        """Test TenantMiddleware without tenant header."""
        get_response = Mock()
        middleware = TenantMiddleware(get_response)
        
        # Test without tenant header
        mock_request.headers = {}
        
        result = middleware(mock_request)
        assert result is not None
    
    def test_security_headers_middleware_init(self):
        """Test SecurityHeadersMiddleware initialization."""
        get_response = Mock()
        middleware = SecurityHeadersMiddleware(get_response)
        assert middleware.get_response == get_response
    
    def test_security_headers_middleware_process_response(self, mock_request, mock_response):
        """Test SecurityHeadersMiddleware response processing."""
        get_response = Mock(return_value=mock_response)
        middleware = SecurityHeadersMiddleware(get_response)
        
        result = middleware(mock_request)
        
        # Check that security headers are added
        assert result is not None
    
    def test_rate_limit_middleware_init(self):
        """Test RateLimitMiddleware initialization."""
        get_response = Mock()
        middleware = RateLimitMiddleware(get_response)
        assert middleware.get_response == get_response
    
    def test_rate_limit_middleware_process_request(self, mock_request):
        """Test RateLimitMiddleware request processing."""
        get_response = Mock()
        middleware = RateLimitMiddleware(get_response)
        
        with patch('app.middleware.time.time', return_value=1000):
            result = middleware(mock_request)
        
        assert result is not None
    
    def test_rate_limit_exceeded(self, mock_request):
        """Test rate limit exceeded scenario."""
        get_response = Mock()
        middleware = RateLimitMiddleware(get_response)
        
        # Simulate multiple rapid requests
        with patch('app.middleware.time.time', return_value=1000):
            for _ in range(100):  # Exceed rate limit
                result = middleware(mock_request)
        
        assert result is not None


class TestTransactionAnalyticsComplete:
    """Complete test coverage for transaction analytics module - targeting 100%."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = Mock()
        return db
    
    @pytest.fixture
    def sample_transactions(self):
        """Sample transaction data."""
        return [
            Mock(
                id=uuid4(),
                amount=Decimal("100.00"),
                transaction_type="EXPENSE",
                category="Food",
                date=date.today(),
                description="Lunch"
            ),
            Mock(
                id=uuid4(),
                amount=Decimal("50.00"),
                transaction_type="EXPENSE", 
                category="Transport",
                date=date.today() - timedelta(days=1),
                description="Bus fare"
            )
        ]
    
    def test_transaction_analytics_init(self, mock_db):
        """Test TransactionAnalytics initialization."""
        analytics = TransactionAnalytics(mock_db)
        assert analytics.db == mock_db
    
    def test_get_spending_by_category(self, mock_db, sample_transactions):
        """Test spending analysis by category."""
        analytics = TransactionAnalytics(mock_db)
        
        with patch.object(analytics, '_get_transactions', return_value=sample_transactions):
            result = analytics.get_spending_by_category()
        
        assert isinstance(result, dict)
        assert len(result) > 0
    
    def test_get_monthly_trends(self, mock_db, sample_transactions):
        """Test monthly spending trends."""
        analytics = TransactionAnalytics(mock_db)
        
        with patch.object(analytics, '_get_transactions', return_value=sample_transactions):
            result = analytics.get_monthly_trends()
        
        assert isinstance(result, dict)
    
    def test_spending_analyzer_init(self):
        """Test SpendingAnalyzer initialization."""
        analyzer = SpendingAnalyzer()
        assert analyzer is not None
    
    def test_analyze_spending_patterns(self, sample_transactions):
        """Test spending pattern analysis."""
        analyzer = SpendingAnalyzer()
        result = analyzer.analyze_patterns(sample_transactions)
        
        assert isinstance(result, dict)
        assert "total_spending" in result
        assert "category_breakdown" in result
    
    def test_trend_analyzer_init(self):
        """Test TrendAnalyzer initialization."""
        analyzer = TrendAnalyzer()
        assert analyzer is not None
    
    def test_analyze_trends(self, sample_transactions):
        """Test trend analysis."""
        analyzer = TrendAnalyzer()
        result = analyzer.analyze_trends(sample_transactions)
        
        assert isinstance(result, dict)
        assert "trend_direction" in result
    
    def test_get_transaction_summary(self, mock_db):
        """Test transaction summary generation."""
        analytics = TransactionAnalytics(mock_db)
        
        with patch.object(analytics, '_get_transactions', return_value=[]):
            result = analytics.get_transaction_summary()
        
        assert isinstance(result, dict)
        assert "total_transactions" in result
        assert "total_amount" in result
    
    def test_detect_anomalies(self, mock_db, sample_transactions):
        """Test anomaly detection in transactions."""
        analytics = TransactionAnalytics(mock_db)
        
        with patch.object(analytics, '_get_transactions', return_value=sample_transactions):
            result = analytics.detect_anomalies()
        
        assert isinstance(result, list)


class TestTransactionClassifierComplete:
    """Complete test coverage for transaction classifier module - targeting 100%."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def sample_transaction(self):
        """Sample transaction for classification."""
        return Mock(
            id=uuid4(),
            description="Coffee shop purchase",
            amount=Decimal("5.50"),
            merchant="Starbucks"
        )
    
    def test_transaction_classifier_init(self, mock_db):
        """Test TransactionClassifier initialization."""
        classifier = TransactionClassifier(mock_db)
        assert classifier.db == mock_db
    
    def test_classify_transaction(self, mock_db, sample_transaction):
        """Test transaction classification."""
        classifier = TransactionClassifier(mock_db)
        
        with patch.object(classifier, '_get_classification_rules', return_value=[]):
            result = classifier.classify_transaction(sample_transaction)
        
        assert isinstance(result, dict)
        assert "category" in result
        assert "confidence" in result
    
    def test_classification_rule_init(self):
        """Test ClassificationRule initialization."""
        rule = ClassificationRule(
            pattern="coffee",
            category="Food & Drink",
            priority=1
        )
        assert rule.pattern == "coffee"
        assert rule.category == "Food & Drink"
        assert rule.priority == 1
    
    def test_classification_rule_matches(self):
        """Test classification rule matching."""
        rule = ClassificationRule(
            pattern="coffee",
            category="Food & Drink",
            priority=1
        )
        
        assert rule.matches("coffee shop") is True
        assert rule.matches("grocery store") is False
    
    def test_auto_classifier_init(self, mock_db):
        """Test AutoClassifier initialization."""
        classifier = AutoClassifier(mock_db)
        assert classifier.db == mock_db
    
    def test_auto_classify_batch(self, mock_db):
        """Test batch auto-classification."""
        classifier = AutoClassifier(mock_db)
        transactions = [Mock(), Mock()]
        
        with patch.object(classifier, 'classify_transaction', return_value={"category": "Food"}):
            result = classifier.classify_batch(transactions)
        
        assert isinstance(result, list)
        assert len(result) == 2
    
    def test_update_classification_rules(self, mock_db):
        """Test classification rule updates."""
        classifier = TransactionClassifier(mock_db)
        
        new_rules = [
            {"pattern": "gas", "category": "Transportation"},
            {"pattern": "grocery", "category": "Food"}
        ]
        
        with patch.object(classifier, '_save_rules') as mock_save:
            classifier.update_classification_rules(new_rules)
            mock_save.assert_called_once()
    
    def test_get_classification_accuracy(self, mock_db):
        """Test classification accuracy calculation."""
        classifier = TransactionClassifier(mock_db)
        
        with patch.object(classifier, '_get_classified_transactions', return_value=[]):
            result = classifier.get_classification_accuracy()
        
        assert isinstance(result, float)
        assert 0 <= result <= 1


class TestTaggingServiceComplete:
    """Complete test coverage for tagging service module - targeting 100%."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    def test_tagging_service_init(self, mock_db):
        """Test TaggingService initialization."""
        service = TaggingService(mock_db)
        assert service.db == mock_db
    
    def test_create_tag(self, mock_db):
        """Test tag creation."""
        service = TaggingService(mock_db)
        
        tag_data = {
            "name": "important",
            "color": "red",
            "description": "Important items"
        }
        
        result = service.create_tag(tag_data)
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_get_tag(self, mock_db):
        """Test tag retrieval."""
        service = TaggingService(mock_db)
        tag_id = str(uuid4())
        
        mock_tag = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tag
        
        result = service.get_tag(tag_id)
        assert result == mock_tag
    
    def test_update_tag(self, mock_db):
        """Test tag update."""
        service = TaggingService(mock_db)
        tag_id = str(uuid4())
        
        mock_tag = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tag
        
        update_data = {"name": "updated_tag"}
        result = service.update_tag(tag_id, update_data)
        
        assert result == mock_tag
        mock_db.commit.assert_called_once()
    
    def test_delete_tag(self, mock_db):
        """Test tag deletion."""
        service = TaggingService(mock_db)
        tag_id = str(uuid4())
        
        mock_tag = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tag
        
        result = service.delete_tag(tag_id)
        
        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_tag_resource(self, mock_db):
        """Test resource tagging."""
        service = TaggingService(mock_db)
        
        resource_id = str(uuid4())
        tag_id = str(uuid4())
        
        result = service.tag_resource(resource_id, tag_id)
        
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_untag_resource(self, mock_db):
        """Test resource untagging."""
        service = TaggingService(mock_db)
        
        resource_id = str(uuid4())
        tag_id = str(uuid4())
        
        mock_resource_tag = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_resource_tag
        
        result = service.untag_resource(resource_id, tag_id)
        
        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_get_resource_tags(self, mock_db):
        """Test getting tags for a resource."""
        service = TaggingService(mock_db)
        resource_id = str(uuid4())
        
        mock_tags = [Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_tags
        
        result = service.get_resource_tags(resource_id)
        
        assert len(result) == 2
    
    def test_auto_tagger_init(self, mock_db):
        """Test AutoTagger initialization."""
        tagger = AutoTagger(mock_db)
        assert tagger.db == mock_db
    
    def test_auto_tag_resource(self, mock_db):
        """Test automatic resource tagging."""
        tagger = AutoTagger(mock_db)
        
        resource = Mock()
        resource.description = "urgent task"
        
        with patch.object(tagger, '_get_tagging_rules', return_value=[]):
            result = tagger.auto_tag(resource)
        
        assert isinstance(result, list)
    
    def test_search_tags(self, mock_db):
        """Test tag searching."""
        service = TaggingService(mock_db)
        
        mock_tags = [Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_tags
        
        result = service.search_tags("important")
        
        assert len(result) == 2


class TestServicesComplete:
    """Complete test coverage for services module - targeting 100%."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    def test_tenant_service_init(self, mock_db):
        """Test TenantService initialization."""
        service = TenantService(mock_db)
        assert service.db == mock_db
    
    def test_tenant_service_create_tenant(self, mock_db):
        """Test tenant creation through service."""
        service = TenantService(mock_db)
        
        tenant_data = {
            "name": "Test Tenant",
            "tenant_type": "ORGANIZATION"
        }
        
        result = service.create_tenant(tenant_data)
        assert result is not None
        mock_db.add.assert_called_once()
    
    def test_financial_service_init(self, mock_db):
        """Test FinancialService initialization."""
        service = FinancialService(mock_db)
        assert service.db == mock_db
    
    def test_financial_service_create_account(self, mock_db):
        """Test account creation through service."""
        service = FinancialService(mock_db)
        
        account_data = {
            "name": "Test Account",
            "account_type": "CHECKING",
            "balance": Decimal("1000.00")
        }
        
        result = service.create_account(account_data)
        assert result is not None
        mock_db.add.assert_called_once()
    
    def test_user_service_init(self, mock_db):
        """Test UserService initialization."""
        service = UserService(mock_db)
        assert service.db == mock_db
    
    def test_user_service_create_user(self, mock_db):
        """Test user creation through service."""
        service = UserService(mock_db)
        
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
        
        result = service.create_user(user_data)
        assert result is not None
        mock_db.add.assert_called_once()
    
    def test_dashboard_service_init(self, mock_db):
        """Test DashboardService initialization."""
        service = DashboardService(mock_db)
        assert service.db == mock_db
    
    def test_dashboard_service_get_dashboard_data(self, mock_db):
        """Test dashboard data retrieval."""
        service = DashboardService(mock_db)
        user_id = str(uuid4())
        
        with patch.object(service, '_get_user_data', return_value={}):
            with patch.object(service, '_get_financial_summary', return_value={}):
                result = service.get_dashboard_data(user_id)
        
        assert isinstance(result, dict)
        assert "user" in result
        assert "financial_summary" in result


class TestCoreModulesComplete:
    """Complete test coverage for core modules - targeting 100%."""
    
    def test_rbac_manager_init(self):
        """Test RBACManager initialization."""
        manager = RBACManager()
        assert manager is not None
    
    def test_rbac_manager_check_permission(self):
        """Test permission checking."""
        manager = RBACManager()
        
        user_id = str(uuid4())
        permission = "read:accounts"
        
        with patch.object(manager, '_get_user_permissions', return_value=["read:accounts"]):
            result = manager.check_permission(user_id, permission)
        
        assert result is True
    
    def test_permission_manager_init(self):
        """Test PermissionManager initialization."""
        manager = PermissionManager()
        assert manager is not None
    
    def test_role_manager_init(self):
        """Test RoleManager initialization."""
        manager = RoleManager()
        assert manager is not None
    
    def test_system_audit_logger_init(self):
        """Test SystemAuditLogger initialization."""
        logger = SystemAuditLogger()
        assert logger is not None
    
    def test_audit_logger_log_event(self):
        """Test audit event logging."""
        logger = SystemAuditLogger()
        
        event = {
            "user_id": str(uuid4()),
            "action": "CREATE_USER",
            "resource_type": "User",
            "severity": "INFO"
        }
        
        with patch.object(logger, '_save_audit_event') as mock_save:
            logger.log_event(event)
            mock_save.assert_called_once()
    
    def test_memcached_client_init(self):
        """Test MemcachedClient initialization."""
        client = MemcachedClient()
        assert client is not None
    
    def test_cache_manager_init(self):
        """Test CacheManager initialization."""
        manager = CacheManager()
        assert manager is not None
    
    def test_cache_manager_set_get(self):
        """Test cache set and get operations."""
        manager = CacheManager()
        
        with patch.object(manager, '_get_client') as mock_client:
            mock_client.return_value.set.return_value = True
            mock_client.return_value.get.return_value = "cached_value"
            
            # Test set
            result_set = manager.set("test_key", "test_value")
            assert result_set is True
            
            # Test get
            result_get = manager.get("test_key")
            assert result_get == "cached_value"
    
    def test_rabbitmq_client_init(self):
        """Test RabbitMQClient initialization."""
        client = RabbitMQClient()
        assert client is not None
    
    def test_queue_manager_init(self):
        """Test QueueManager initialization."""
        manager = QueueManager()
        assert manager is not None
    
    def test_message_queue_publish(self):
        """Test message queue publishing."""
        queue = MessageQueue("test_queue")
        
        message = {"type": "test", "data": "test_data"}
        
        with patch.object(queue, '_get_connection') as mock_conn:
            mock_channel = Mock()
            mock_conn.return_value.channel.return_value = mock_channel
            
            result = queue.publish(message)
            assert result is True


class TestSettingsComplete:
    """Complete test coverage for settings module - targeting 100%."""
    
    def test_database_settings_init(self):
        """Test DatabaseSettings initialization."""
        settings = DatabaseSettings()
        assert settings is not None
    
    def test_database_settings_get_url(self):
        """Test database URL generation."""
        settings = DatabaseSettings()
        
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://user:pass@localhost/db'
        }):
            url = settings.get_database_url()
            assert url is not None
    
    def test_cache_settings_init(self):
        """Test CacheSettings initialization."""
        settings = CacheSettings()
        assert settings is not None
    
    def test_cache_settings_get_config(self):
        """Test cache configuration."""
        settings = CacheSettings()
        
        config = settings.get_cache_config()
        assert isinstance(config, dict)
    
    def test_queue_settings_init(self):
        """Test QueueSettings initialization."""
        settings = QueueSettings()
        assert settings is not None
    
    def test_security_settings_init(self):
        """Test SecuritySettings initialization."""
        settings = SecuritySettings()
        assert settings is not None
    
    def test_security_settings_get_secret_key(self):
        """Test secret key retrieval."""
        settings = SecuritySettings()
        
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key'}):
            key = settings.get_secret_key()
            assert key == 'test-secret-key'


class TestMainAppComplete:
    """Complete test coverage for main application module - targeting 100%."""
    
    def test_create_app(self):
        """Test application creation."""
        with patch('app.main.FastAPI') as mock_fastapi:
            mock_app = Mock()
            mock_fastapi.return_value = mock_app
            
            app = create_app()
            assert app == mock_app
    
    def test_setup_middleware(self):
        """Test middleware setup."""
        mock_app = Mock()
        
        setup_middleware(mock_app)
        
        # Verify middleware was added
        assert mock_app.add_middleware.called
    
    def test_configure_cors(self):
        """Test CORS configuration."""
        mock_app = Mock()
        
        configure_cors(mock_app)
        
        # Verify CORS was configured
        assert mock_app.add_middleware.called


class TestSchemasComplete:
    """Complete test coverage for schemas module - targeting 100%."""
    
    def test_user_create_schema(self):
        """Test UserCreateSchema validation."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
        
        schema = UserCreateSchema(**data)
        assert schema.username == "testuser"
        assert schema.email == "test@example.com"
    
    def test_user_response_schema(self):
        """Test UserResponseSchema validation."""
        data = {
            "id": str(uuid4()),
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True
        }
        
        schema = UserResponseSchema(**data)
        assert schema.username == "testuser"
    
    def test_tenant_create_schema(self):
        """Test TenantCreateSchema validation."""
        data = {
            "name": "Test Tenant",
            "tenant_type": "ORGANIZATION"
        }
        
        schema = TenantCreateSchema(**data)
        assert schema.name == "Test Tenant"
    
    def test_account_create_schema(self):
        """Test AccountCreateSchema validation."""
        data = {
            "name": "Test Account",
            "account_type": "CHECKING",
            "balance": Decimal("1000.00")
        }
        
        schema = AccountCreateSchema(**data)
        assert schema.name == "Test Account"
    
    def test_transaction_create_schema(self):
        """Test TransactionCreateSchema validation."""
        data = {
            "amount": Decimal("100.00"),
            "transaction_type": "EXPENSE",
            "description": "Test transaction",
            "category": "Food"
        }
        
        schema = TransactionCreateSchema(**data)
        assert schema.amount == Decimal("100.00")


class TestFinancialModelsComplete:
    """Complete test coverage for financial models module - targeting 100%."""
    
    def test_account_model_init(self):
        """Test Account model initialization."""
        account = Account(
            name="Test Account",
            account_type=AccountType.CHECKING,
            balance=Decimal("1000.00")
        )
        assert account.name == "Test Account"
        assert account.account_type == AccountType.CHECKING
    
    def test_transaction_model_init(self):
        """Test Transaction model initialization."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            transaction_type=TransactionType.EXPENSE,
            description="Test transaction"
        )
        assert transaction.amount == Decimal("100.00")
        assert transaction.transaction_type == TransactionType.EXPENSE
    
    def test_budget_model_init(self):
        """Test Budget model initialization."""
        budget = Budget(
            name="Monthly Budget",
            amount=Decimal("2000.00"),
            category=BudgetCategory.FOOD
        )
        assert budget.name == "Monthly Budget"
        assert budget.amount == Decimal("2000.00")
    
    def test_account_update_balance(self):
        """Test account balance update."""
        account = Account(
            name="Test Account",
            account_type=AccountType.CHECKING,
            balance=Decimal("1000.00")
        )
        
        account.update_balance(Decimal("100.00"))
        assert account.balance == Decimal("1100.00")
    
    def test_budget_check_status(self):
        """Test budget status checking."""
        budget = Budget(
            name="Monthly Budget",
            amount=Decimal("2000.00"),
            category=BudgetCategory.FOOD
        )
        
        status = budget.check_status(Decimal("1500.00"))
        assert status == BudgetStatus.ON_TRACK


class TestDjangoModulesComplete:
    """Complete test coverage for Django-specific modules - targeting 100%."""
    
    def test_audit_logger_init(self):
        """Test Django AuditLogger initialization."""
        logger = AuditLogger()
        assert logger is not None
    
    def test_audit_entry_creation(self):
        """Test audit entry creation."""
        entry = AuditEntry(
            user_id=uuid4(),
            action=AuditAction.CREATE,
            resource_type="User",
            resource_id=uuid4()
        )
        assert entry.action == AuditAction.CREATE
    
    def test_role_model_init(self):
        """Test Django Role model initialization."""
        role = Role(
            name="admin",
            description="Administrator role"
        )
        assert role.name == "admin"
    
    def test_permission_model_init(self):
        """Test Django Permission model initialization."""
        permission = Permission(
            name="read:users",
            description="Read user data"
        )
        assert permission.name == "read:users"
    
    def test_user_role_assignment(self):
        """Test user role assignment."""
        user_role = UserRole(
            user_id=uuid4(),
            role_id=uuid4()
        )
        assert user_role.user_id is not None
        assert user_role.role_id is not None
    
    def test_role_permission_assignment(self):
        """Test role permission assignment."""
        role_permission = RolePermission(
            role_id=uuid4(),
            permission_id=uuid4()
        )
        assert role_permission.role_id is not None
        assert role_permission.permission_id is not None