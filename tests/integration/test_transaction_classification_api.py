"""Integration tests for transaction classification and analytics API."""

import pytest
from decimal import Decimal
from uuid import uuid4

from app.financial_models import Transaction
from app.core.tenant import TenantType


class TestTransactionClassificationAPI:
    """Integration tests for transaction classification API endpoints."""
    
    @pytest.fixture
    def sample_transactions(self, db_session, sample_user):
        """Create sample transactions for testing."""
        transactions_data = [
            {
                "amount": Decimal("29.99"),
                "description": "Netflix Monthly Subscription",
                "transaction_type": "debit",
                "category": "entertainment"
            },
            {
                "amount": Decimal("5000.00"),
                "description": "Salary deposit from ACME Corp",
                "transaction_type": "credit",
                "category": "income"
            },
            {
                "amount": Decimal("45.67"),
                "description": "McDonald's Restaurant",
                "transaction_type": "debit", 
                "category": "food"
            },
            {
                "amount": Decimal("125.43"),
                "description": "Electric company bill payment",
                "transaction_type": "debit",
                "category": "utilities"
            },
            {
                "amount": Decimal("15000.00"),
                "description": "Wire transfer to investment account",
                "transaction_type": "transfer",
                "category": "investment"
            }
        ]
        
        transactions = []
        for tx_data in transactions_data:
            transaction = Transaction(
                id=uuid4(),
                amount=tx_data["amount"],
                currency="USD",
                description=tx_data["description"],
                transaction_type=tx_data["transaction_type"],
                category=tx_data["category"],
                tenant_type=TenantType.USER,
                tenant_id=str(sample_user.id)
            )
            transactions.append(transaction)
            db_session.add(transaction)
        
        db_session.commit()
        return transactions

    def test_create_transaction_with_auto_classification(self, client, auth_headers):
        """Test creating a transaction with automatic classification."""
        transaction_data = {
            "amount": 99.99,
            "currency": "USD",
            "description": "Spotify Premium Subscription",
            "transaction_type": "debit"
        }
        
        response = client.post(
            "/financial/transactions?auto_classify=true&auto_tag=true",
            json=transaction_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        transaction = response.json()
        assert transaction["amount"] == "99.99"
        assert transaction["description"] == "Spotify Premium Subscription"

    def test_classify_existing_transactions(self, client, auth_headers, sample_transactions):
        """Test classifying existing transactions."""
        # Get transaction IDs
        transaction_ids = [str(tx.id) for tx in sample_transactions[:3]]
        
        request_data = {
            "transaction_ids": transaction_ids,
            "auto_tag": True,
            "force_reclassify": False
        }
        
        response = client.post(
            "/financial/transactions/classify",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 3
        
        for result in results:
            assert "transaction_id" in result
            assert "classification" in result
            assert "category" in result
            assert "auto_generated" in result
            assert result["transaction_id"] in transaction_ids

    def test_classify_all_transactions(self, client, auth_headers, sample_transactions):
        """Test classifying all transactions for a tenant."""
        request_data = {
            "auto_tag": True,
            "force_reclassify": True
        }
        
        response = client.post(
            "/financial/transactions/classify",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= len(sample_transactions)
        
        # Verify all results have required fields
        for result in results:
            assert "transaction_id" in result
            assert "classification" in result
            assert "category" in result

    def test_classification_analytics(self, client, auth_headers, sample_transactions):
        """Test getting classification analytics."""
        # First classify the transactions
        client.post(
            "/financial/transactions/classify",
            json={"auto_tag": True, "force_reclassify": True},
            headers=auth_headers
        )
        
        # Get classification analytics
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
        
        # Verify distribution structure
        distribution = analytics["distribution"]
        assert "classifications" in distribution
        assert "categories" in distribution
        assert "total_classified" in distribution
        assert "total_categorized" in distribution

    def test_category_analytics(self, client, auth_headers, sample_transactions):
        """Test getting category analytics."""
        # First classify the transactions
        client.post(
            "/financial/transactions/classify",
            json={"auto_tag": True, "force_reclassify": True},
            headers=auth_headers
        )
        
        # Get category analytics
        request_data = {
            "analysis_type": "category",
            "include_trends": True
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
        assert analytics["analysis_type"] == "category"
        
        # May have spending insights
        if "spending_insights" in analytics and analytics["spending_insights"]:
            insights = analytics["spending_insights"]
            assert "top_spending_categories" in insights
            assert "total_spending" in insights

    def test_anomaly_detection(self, client, auth_headers, sample_transactions):
        """Test anomaly detection functionality."""
        # First classify the transactions
        client.post(
            "/financial/transactions/classify",
            json={"auto_tag": True, "force_reclassify": True},
            headers=auth_headers
        )
        
        # Test different sensitivity levels
        for sensitivity in ["low", "medium", "high"]:
            request_data = {
                "sensitivity": sensitivity,
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
            assert "analysis_period" in anomalies
            assert "total_anomalies" in anomalies
            assert anomalies["sensitivity"] == sensitivity

    def test_monthly_breakdown(self, client, auth_headers, sample_transactions):
        """Test monthly breakdown analytics."""
        # First classify the transactions
        client.post(
            "/financial/transactions/classify",
            json={"auto_tag": True, "force_reclassify": True},
            headers=auth_headers
        )
        
        # Test different month ranges
        for months in [3, 6, 12]:
            response = client.get(
                f"/financial/analytics/monthly-breakdown?months={months}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            breakdown = response.json()
            
            assert "monthly_breakdown" in breakdown
            assert "analysis_period" in breakdown
            
            analysis_period = breakdown["analysis_period"]
            assert "start" in analysis_period
            assert "end" in analysis_period
            assert "months_analyzed" in analysis_period

    def test_transaction_patterns(self, client, auth_headers, sample_transactions):
        """Test transaction pattern analysis."""
        # First classify the transactions
        client.post(
            "/financial/transactions/classify",
            json={"auto_tag": True, "force_reclassify": True},
            headers=auth_headers
        )
        
        # Test different pattern types
        for pattern_type in ["classification", "category", "all"]:
            response = client.get(
                f"/financial/analytics/patterns?pattern_type={pattern_type}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            patterns = response.json()
            
            # Response should be a dictionary
            assert isinstance(patterns, dict)
            
            if pattern_type == "classification":
                # May have classification_patterns
                pass
            elif pattern_type == "category":
                # May have category_patterns
                pass
            elif pattern_type == "all":
                # May have both plus cross_analysis
                pass

    def test_classification_config_get(self, client, auth_headers):
        """Test getting classification configuration."""
        response = client.get(
            "/financial/classification/config",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        config = response.json()
        
        assert "classification_patterns" in config
        assert "category_patterns" in config
        assert "updated_at" in config
        
        # Verify structure of patterns
        assert isinstance(config["classification_patterns"], dict)
        assert isinstance(config["category_patterns"], dict)

    def test_classification_config_update(self, client, auth_headers):
        """Test updating classification configuration."""
        # Add new patterns
        update_data = {
            "classification_patterns": {
                "subscription": ["(?i)(test subscription pattern)"],
                "recurring_payment": ["(?i)(test recurring pattern)"]
            },
            "category_patterns": {
                "food_dining": ["(?i)(test food pattern)"],
                "transportation": ["(?i)(test transport pattern)"]
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
        assert "updated_at" in updated_config

    def test_enhanced_dashboard_analytics(self, client, auth_headers, sample_transactions):
        """Test enhanced dashboard with classification filtering."""
        # First classify the transactions
        client.post(
            "/financial/transactions/classify",
            json={"auto_tag": True, "force_reclassify": True},
            headers=auth_headers
        )
        
        # Test dashboard with no filters
        response = client.get(
            "/financial/dashboard/analytics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        dashboard = response.json()
        
        assert "tenant_info" in dashboard
        assert "tag_filters" in dashboard
        assert "resource_metrics" in dashboard
        assert "generated_at" in dashboard

    def test_transaction_tags_after_classification(self, client, auth_headers):
        """Test that transactions get proper tags after classification."""
        # Create a transaction
        transaction_data = {
            "amount": 29.99,
            "currency": "USD",
            "description": "Netflix Monthly Subscription",
            "transaction_type": "debit"
        }
        
        response = client.post(
            "/financial/transactions?auto_classify=true&auto_tag=true",
            json=transaction_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        transaction = response.json()
        transaction_id = transaction["id"]
        
        # Get tags for the transaction
        response = client.get(
            f"/financial/tags/resource/transaction/{transaction_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        tags = response.json()
        
        # Should have classification and category tags
        tag_keys = [tag["tag_key"] for tag in tags]
        assert "classification" in tag_keys
        assert "category" in tag_keys
        
        # Find the classification and category tags
        classification_tag = next(tag for tag in tags if tag["tag_key"] == "classification")
        category_tag = next(tag for tag in tags if tag["tag_key"] == "category")
        
        assert classification_tag["tag_type"] == "category"
        assert category_tag["tag_type"] == "category"
        assert classification_tag["is_active"] is True
        assert category_tag["is_active"] is True

    def test_query_transactions_by_classification(self, client, auth_headers, sample_transactions):
        """Test querying transactions by classification tags."""
        # First classify the transactions
        client.post(
            "/financial/transactions/classify",
            json={"auto_tag": True, "force_reclassify": True},
            headers=auth_headers
        )
        
        # Query for subscription transactions
        query_data = {
            "classification": "subscription"
        }
        
        response = client.post(
            "/financial/tags/query?resource_type=transaction",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        results = response.json()
        
        assert "resource_ids" in results
        assert "resource_count" in results
        assert "tag_filters" in results
        assert "resource_type" in results
        assert results["resource_type"] == "transaction"

    def test_error_handling_invalid_transaction_ids(self, client, auth_headers):
        """Test error handling for invalid transaction IDs."""
        request_data = {
            "transaction_ids": ["invalid-uuid", "another-invalid-uuid"],
            "auto_tag": True,
            "force_reclassify": False
        }
        
        response = client.post(
            "/financial/transactions/classify",
            json=request_data,
            headers=auth_headers
        )
        
        # Should handle gracefully - may return empty results or error
        # The exact behavior depends on validation implementation
        assert response.status_code in [200, 400, 422]

    def test_error_handling_invalid_analysis_type(self, client, auth_headers):
        """Test error handling for invalid analysis type."""
        request_data = {
            "analysis_type": "invalid_type",
            "include_trends": True
        }
        
        response = client.post(
            "/financial/analytics/classification",
            json=request_data,
            headers=auth_headers
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_error_handling_invalid_sensitivity(self, client, auth_headers):
        """Test error handling for invalid sensitivity level."""
        request_data = {
            "sensitivity": "invalid_sensitivity",
            "analysis_period_days": 30
        }
        
        response = client.post(
            "/financial/analytics/anomalies",
            json=request_data,
            headers=auth_headers
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


class TestTransactionClassificationPerformance:
    """Performance tests for transaction classification."""
    
    def test_bulk_classification_performance(self, client, auth_headers, db_session, sample_user):
        """Test performance of bulk transaction classification."""
        import time
        
        # Create many transactions
        transaction_ids = []
        for i in range(100):
            transaction_data = {
                "amount": 50.00 + (i % 10),
                "currency": "USD",
                "description": f"Test transaction {i}",
                "transaction_type": "debit"
            }
            
            response = client.post(
                "/financial/transactions?auto_classify=false&auto_tag=false",
                json=transaction_data,
                headers=auth_headers
            )
            
            if response.status_code == 201:
                transaction_ids.append(response.json()["id"])
        
        # Measure classification time
        start_time = time.time()
        
        request_data = {
            "transaction_ids": transaction_ids,
            "auto_tag": True,
            "force_reclassify": False
        }
        
        response = client.post(
            "/financial/transactions/classify",
            json=request_data,
            headers=auth_headers
        )
        
        end_time = time.time()
        classification_time = end_time - start_time
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == len(transaction_ids)
        
        # Performance assertion - should complete within reasonable time
        # Allow 5 seconds for 100 transactions (flexible for CI environments)
        assert classification_time < 5.0, f"Classification took {classification_time:.2f} seconds"
        
        print(f"Classified {len(transaction_ids)} transactions in {classification_time:.2f} seconds")

    def test_analytics_computation_performance(self, client, auth_headers, sample_transactions):
        """Test performance of analytics computation."""
        import time
        
        # First classify the transactions
        client.post(
            "/financial/transactions/classify",
            json={"auto_tag": True, "force_reclassify": True},
            headers=auth_headers
        )
        
        # Measure analytics computation time
        start_time = time.time()
        
        request_data = {
            "analysis_type": "all",
            "include_trends": True,
            "include_patterns": True
        }
        
        response = client.post(
            "/financial/analytics/classification",
            json=request_data,
            headers=auth_headers
        )
        
        end_time = time.time()
        analytics_time = end_time - start_time
        
        assert response.status_code == 200
        
        # Performance assertion - should complete within reasonable time
        assert analytics_time < 3.0, f"Analytics computation took {analytics_time:.2f} seconds"
        
        print(f"Analytics computation completed in {analytics_time:.2f} seconds")