"""Tests for transaction classification and categorization features."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.transaction_classifier import (
    TransactionClassifierService, 
    TransactionClassification, 
    TransactionCategory
)
from app.transaction_analytics import TransactionAnalyticsService
from app.financial_models import Transaction
from app.core.tenant import TenantType


class TestTransactionClassifier:
    """Test cases for TransactionClassifierService."""
    
    def test_classify_recurring_payment(self, db_session):
        """Test classification of recurring payments."""
        service = TransactionClassifierService(db_session)
        
        # Create transaction with recurring payment description
        transaction = Transaction(
            amount=Decimal("99.99"),
            currency="USD",
            description="Netflix Monthly Subscription",
            transaction_type="debit",
            tenant_type=TenantType.USER,
            tenant_id="user_123"
        )
        
        classification = service.classify_transaction(transaction)
        assert classification == TransactionClassification.SUBSCRIPTION

    def test_classify_large_transfer(self, db_session):
        """Test classification of large transfers."""
        service = TransactionClassifierService(db_session)
        
        # Create large transaction
        transaction = Transaction(
            amount=Decimal("15000.00"),
            currency="USD",
            description="Wire transfer to investment account",
            transaction_type="transfer",
            tenant_type=TenantType.USER,
            tenant_id="user_123"
        )
        
        classification = service.classify_transaction(transaction)
        assert classification == TransactionClassification.LARGE_TRANSFER

    def test_classify_micro_transaction(self, db_session):
        """Test classification of micro transactions."""
        service = TransactionClassifierService(db_session)
        
        # Create micro transaction
        transaction = Transaction(
            amount=Decimal("2.50"),
            currency="USD",
            description="Coffee shop purchase",
            transaction_type="debit",
            tenant_type=TenantType.USER,
            tenant_id="user_123"
        )
        
        classification = service.classify_transaction(transaction)
        assert classification == TransactionClassification.MICRO_TRANSACTION

    def test_classify_salary_income(self, db_session):
        """Test classification of salary income."""
        service = TransactionClassifierService(db_session)
        
        # Create salary transaction
        transaction = Transaction(
            amount=Decimal("5000.00"),
            currency="USD",
            description="Salary deposit from ACME Corp",
            transaction_type="credit",
            tenant_type=TenantType.USER,
            tenant_id="user_123"
        )
        
        classification = service.classify_transaction(transaction)
        assert classification == TransactionClassification.SALARY_INCOME

    def test_categorize_food_dining(self, db_session):
        """Test categorization of food and dining transactions."""
        service = TransactionClassifierService(db_session)
        
        # Create food transaction
        transaction = Transaction(
            amount=Decimal("45.67"),
            currency="USD",
            description="McDonald's Restaurant",
            transaction_type="debit",
            tenant_type=TenantType.USER,
            tenant_id="user_123"
        )
        
        category = service.categorize_transaction(transaction)
        assert category == TransactionCategory.FOOD_DINING

    def test_categorize_transportation(self, db_session):
        """Test categorization of transportation transactions."""
        service = TransactionClassifierService(db_session)
        
        # Create transportation transaction
        transaction = Transaction(
            amount=Decimal("65.00"),
            currency="USD",
            description="Uber ride downtown",
            transaction_type="debit",
            tenant_type=TenantType.USER,
            tenant_id="user_123"
        )
        
        category = service.categorize_transaction(transaction)
        assert category == TransactionCategory.TRANSPORTATION

    def test_categorize_utilities(self, db_session):
        """Test categorization of utility transactions."""
        service = TransactionClassifierService(db_session)
        
        # Create utility transaction
        transaction = Transaction(
            amount=Decimal("125.43"),
            currency="USD",
            description="Electric company bill payment",
            transaction_type="debit",
            tenant_type=TenantType.USER,
            tenant_id="user_123"
        )
        
        category = service.categorize_transaction(transaction)
        assert category == TransactionCategory.UTILITIES

    def test_auto_classify_and_categorize(self, db_session):
        """Test automatic classification and categorization with tag creation."""
        service = TransactionClassifierService(db_session)
        
        # Create transaction
        transaction = Transaction(
            id=uuid4(),
            amount=Decimal("29.99"),
            currency="USD",
            description="Spotify Premium Subscription",
            transaction_type="debit",
            tenant_type=TenantType.USER,
            tenant_id="user_123"
        )
        
        db_session.add(transaction)
        db_session.commit()
        
        # Auto classify and categorize
        result = service.auto_classify_and_categorize(transaction, create_tags=True)
        
        assert result["classification"] == TransactionClassification.SUBSCRIPTION.value
        assert result["category"] == TransactionCategory.ENTERTAINMENT.value
        
        # Verify tags were created
        tags = service.tagging_service.get_resource_tags(
            resource_type="transaction",
            resource_id=transaction.id,
            tenant_type="user",
            tenant_id="user_123"
        )
        
        # Should have classification and category tags
        classification_tags = [t for t in tags if t.tag_key == "classification"]
        category_tags = [t for t in tags if t.tag_key == "category"]
        
        assert len(classification_tags) == 1
        assert len(category_tags) == 1
        assert classification_tags[0].tag_value == TransactionClassification.SUBSCRIPTION.value
        assert category_tags[0].tag_value == TransactionCategory.ENTERTAINMENT.value

    def test_get_transactions_by_classification(self, db_session, sample_user):
        """Test getting transactions by classification."""
        service = TransactionClassifierService(db_session)
        
        # Create multiple transactions
        transactions = []
        for i in range(3):
            transaction = Transaction(
                id=uuid4(),
                amount=Decimal("99.99"),
                currency="USD",
                description=f"Netflix Subscription {i}",
                transaction_type="debit",
                tenant_type=TenantType.USER,
                tenant_id=str(sample_user.id)
            )
            transactions.append(transaction)
            db_session.add(transaction)
        
        db_session.commit()
        
        # Classify transactions
        for transaction in transactions:
            service.auto_classify_and_categorize(transaction, create_tags=True)
        
        # Get transactions by classification
        subscription_transactions = service.get_transactions_by_classification(
            classification=TransactionClassification.SUBSCRIPTION,
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        assert len(subscription_transactions) == 3

    def test_analyze_classification_distribution(self, db_session, sample_user):
        """Test classification distribution analysis."""
        service = TransactionClassifierService(db_session)
        
        # Create transactions with different classifications
        transactions_data = [
            ("Netflix Subscription", TransactionClassification.SUBSCRIPTION),
            ("Large wire transfer", TransactionClassification.LARGE_TRANSFER),
            ("Coffee purchase", TransactionClassification.MICRO_TRANSACTION),
        ]
        
        for desc, expected_classification in transactions_data:
            transaction = Transaction(
                id=uuid4(),
                amount=Decimal("100.00") if expected_classification != TransactionClassification.LARGE_TRANSFER else Decimal("15000.00"),
                currency="USD",
                description=desc,
                transaction_type="debit",
                tenant_type=TenantType.USER,
                tenant_id=str(sample_user.id)
            )
            db_session.add(transaction)
            db_session.commit()
            
            service.auto_classify_and_categorize(transaction, create_tags=True)
        
        # Analyze distribution
        distribution = service.analyze_classification_distribution(
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        assert distribution["total_classified"] >= 3
        assert distribution["total_categorized"] >= 3
        assert len(distribution["classifications"]) >= 3


class TestTransactionAnalytics:
    """Test cases for TransactionAnalyticsService."""
    
    def test_get_classification_analytics(self, db_session, sample_user):
        """Test classification analytics computation."""
        analytics_service = TransactionAnalyticsService(db_session)
        classifier_service = TransactionClassifierService(db_session)
        
        # Create and classify transactions
        transaction_data = [
            ("Netflix Subscription", Decimal("29.99"), "debit"),
            ("Salary deposit", Decimal("5000.00"), "credit"),
            ("Uber ride", Decimal("25.50"), "debit"),
        ]
        
        for desc, amount, tx_type in transaction_data:
            transaction = Transaction(
                id=uuid4(),
                amount=amount,
                currency="USD",
                description=desc,
                transaction_type=tx_type,
                tenant_type=TenantType.USER,
                tenant_id=str(sample_user.id)
            )
            db_session.add(transaction)
            db_session.commit()
            
            classifier_service.auto_classify_and_categorize(transaction, create_tags=True)
        
        # Get classification analytics
        analytics = analytics_service.get_classification_analytics(
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        assert "distribution" in analytics
        assert "amount_analysis" in analytics
        assert analytics["analysis_type"] == "classification"

    def test_get_category_analytics(self, db_session, sample_user):
        """Test category analytics computation."""
        analytics_service = TransactionAnalyticsService(db_session)
        classifier_service = TransactionClassifierService(db_session)
        
        # Create and classify transactions
        transaction_data = [
            ("McDonald's dinner", Decimal("45.67"), "debit"),
            ("Gas station fill-up", Decimal("65.00"), "debit"),
            ("Electric bill", Decimal("125.43"), "debit"),
        ]
        
        for desc, amount, tx_type in transaction_data:
            transaction = Transaction(
                id=uuid4(),
                amount=amount,
                currency="USD",
                description=desc,
                transaction_type=tx_type,
                tenant_type=TenantType.USER,
                tenant_id=str(sample_user.id)
            )
            db_session.add(transaction)
            db_session.commit()
            
            classifier_service.auto_classify_and_categorize(transaction, create_tags=True)
        
        # Get category analytics
        analytics = analytics_service.get_category_analytics(
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        assert "category_analysis" in analytics
        assert "spending_insights" in analytics
        assert analytics["analysis_type"] == "category"

    def test_get_anomaly_detection(self, db_session, sample_user):
        """Test anomaly detection in transactions."""
        analytics_service = TransactionAnalyticsService(db_session)
        classifier_service = TransactionClassifierService(db_session)
        
        # Create normal transactions
        for i in range(10):
            transaction = Transaction(
                id=uuid4(),
                amount=Decimal("50.00"),  # Normal amount
                currency="USD",
                description="Regular restaurant meal",
                transaction_type="debit",
                tenant_type=TenantType.USER,
                tenant_id=str(sample_user.id)
            )
            db_session.add(transaction)
            db_session.commit()
            classifier_service.auto_classify_and_categorize(transaction, create_tags=True)
        
        # Create anomalous transaction
        anomaly_transaction = Transaction(
            id=uuid4(),
            amount=Decimal("500.00"),  # Much higher than normal
            currency="USD",
            description="Expensive restaurant meal",
            transaction_type="debit",
            tenant_type=TenantType.USER,
            tenant_id=str(sample_user.id)
        )
        db_session.add(anomaly_transaction)
        db_session.commit()
        classifier_service.auto_classify_and_categorize(anomaly_transaction, create_tags=True)
        
        # Detect anomalies
        anomalies = analytics_service.get_anomaly_detection(
            tenant_type="user",
            tenant_id=str(sample_user.id),
            sensitivity="medium"
        )
        
        assert "anomalies" in anomalies
        assert "total_anomalies" in anomalies
        assert anomalies["sensitivity"] == "medium"

    def test_get_monthly_breakdown(self, db_session, sample_user):
        """Test monthly breakdown analytics."""
        analytics_service = TransactionAnalyticsService(db_session)
        classifier_service = TransactionClassifierService(db_session)
        
        # Create transactions
        transaction = Transaction(
            id=uuid4(),
            amount=Decimal("100.00"),
            currency="USD",
            description="Monthly expense",
            transaction_type="debit",
            tenant_type=TenantType.USER,
            tenant_id=str(sample_user.id)
        )
        db_session.add(transaction)
        db_session.commit()
        
        classifier_service.auto_classify_and_categorize(transaction, create_tags=True)
        
        # Get monthly breakdown
        breakdown = analytics_service.get_monthly_breakdown(
            tenant_type="user",
            tenant_id=str(sample_user.id),
            months=3
        )
        
        assert "monthly_breakdown" in breakdown
        assert "analysis_period" in breakdown
        assert breakdown["analysis_period"]["months_analyzed"] == 3

    def test_get_transaction_patterns(self, db_session, sample_user):
        """Test transaction patterns analysis."""
        analytics_service = TransactionAnalyticsService(db_session)
        classifier_service = TransactionClassifierService(db_session)
        
        # Create transactions
        transaction = Transaction(
            id=uuid4(),
            amount=Decimal("75.00"),
            currency="USD",
            description="Pattern test transaction",
            transaction_type="debit",
            tenant_type=TenantType.USER,
            tenant_id=str(sample_user.id)
        )
        db_session.add(transaction)
        db_session.commit()
        
        classifier_service.auto_classify_and_categorize(transaction, create_tags=True)
        
        # Get patterns
        patterns = analytics_service.get_transaction_patterns(
            tenant_type="user",
            tenant_id=str(sample_user.id),
            pattern_type="all"
        )
        
        # Should have both classification and category patterns
        assert isinstance(patterns, dict)


class TestTransactionClassificationAPI:
    """Test cases for transaction classification API endpoints."""
    
    def test_classify_transactions_endpoint(self, client, sample_user, auth_headers):
        """Test the classify transactions API endpoint."""
        # Create a transaction first
        transaction_data = {
            "amount": 29.99,
            "currency": "USD",
            "description": "Netflix Monthly Subscription",
            "transaction_type": "debit"
        }
        
        response = client.post(
            "/financial/transactions",
            json=transaction_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        transaction = response.json()
        
        # Classify the transaction
        classification_request = {
            "transaction_ids": [transaction["id"]],
            "auto_tag": True,
            "force_reclassify": False
        }
        
        response = client.post(
            "/financial/transactions/classify",
            json=classification_request,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["transaction_id"] == transaction["id"]
        assert "classification" in results[0]
        assert "category" in results[0]

    def test_classification_analytics_endpoint(self, client, auth_headers):
        """Test the classification analytics API endpoint."""
        request_data = {
            "analysis_type": "classification",
            "include_trends": True,
            "include_patterns": False
        }
        
        response = client.post(
            "/financial/analytics/classification",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        analytics = response.json()
        assert "distribution" in analytics
        assert "amount_analysis" in analytics
        assert analytics["analysis_type"] == "classification"

    def test_anomaly_detection_endpoint(self, client, auth_headers):
        """Test the anomaly detection API endpoint."""
        request_data = {
            "sensitivity": "medium",
            "analysis_period_days": 30
        }
        
        response = client.post(
            "/financial/analytics/anomalies",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        anomalies = response.json()
        assert "anomalies" in anomalies
        assert "sensitivity" in anomalies
        assert anomalies["sensitivity"] == "medium"

    def test_monthly_breakdown_endpoint(self, client, auth_headers):
        """Test the monthly breakdown API endpoint."""
        response = client.get(
            "/financial/analytics/monthly-breakdown?months=6",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        breakdown = response.json()
        assert "monthly_breakdown" in breakdown
        assert "analysis_period" in breakdown

    def test_transaction_patterns_endpoint(self, client, auth_headers):
        """Test the transaction patterns API endpoint."""
        response = client.get(
            "/financial/analytics/patterns?pattern_type=all",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        patterns = response.json()
        # Response should be a valid patterns object
        assert isinstance(patterns, dict)

    def test_classification_config_endpoint(self, client, auth_headers):
        """Test the classification configuration API endpoints."""
        # Get current config
        response = client.get(
            "/financial/classification/config",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        config = response.json()
        assert "classification_patterns" in config
        assert "category_patterns" in config
        
        # Update config (add new patterns)
        update_data = {
            "classification_patterns": {
                "subscription": ["(?i)(new pattern test)"]
            },
            "category_patterns": {
                "food_dining": ["(?i)(test food pattern)"]
            }
        }
        
        response = client.post(
            "/financial/classification/config",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        updated_config = response.json()
        assert "classification_patterns" in updated_config
        assert "category_patterns" in updated_config