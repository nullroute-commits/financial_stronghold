"""Enhanced analytics service for transaction classification and categorization."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.financial_models import Transaction
from app.tagging_models import DataTag
from app.tagging_service import AnalyticsService
from app.transaction_classifier import TransactionClassification, TransactionCategory, TransactionClassifierService
from app.core.tenant import TenantType


class TransactionAnalyticsService:
    """Enhanced analytics service focused on transaction classification and categorization."""

    def __init__(self, db: Session):
        self.db = db
        self.base_analytics = AnalyticsService(db)
        self.classifier = TransactionClassifierService(db)

    def get_classification_analytics(
        self,
        tenant_type: str,
        tenant_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for transaction classifications."""
        # Get classification distribution
        distribution = self.classifier.analyze_classification_distribution(tenant_type=tenant_type, tenant_id=tenant_id)

        # Get transaction amounts by classification
        classification_amounts = {}
        for classification in TransactionClassification:
            transaction_ids = self.classifier.get_transactions_by_classification(
                classification=classification, tenant_type=tenant_type, tenant_id=tenant_id
            )

            if transaction_ids:
                query = self.db.query(Transaction).filter(
                    and_(
                        Transaction.id.in_(transaction_ids),
                        Transaction.tenant_type == TenantType(tenant_type),
                        Transaction.tenant_id == tenant_id,
                    )
                )

                if period_start:
                    query = query.filter(Transaction.created_at >= period_start)
                if period_end:
                    query = query.filter(Transaction.created_at <= period_end)

                transactions = query.all()

                if transactions:
                    total_amount = sum(t.amount for t in transactions)
                    avg_amount = total_amount / len(transactions)

                    classification_amounts[classification.value] = {
                        "count": len(transactions),
                        "total_amount": float(total_amount),
                        "average_amount": float(avg_amount),
                        "min_amount": float(min(t.amount for t in transactions)),
                        "max_amount": float(max(t.amount for t in transactions)),
                    }

        return {
            "distribution": distribution,
            "amount_analysis": classification_amounts,
            "period_start": period_start.isoformat() if period_start else None,
            "period_end": period_end.isoformat() if period_end else None,
            "analysis_type": "classification",
        }

    def get_category_analytics(
        self,
        tenant_type: str,
        tenant_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for transaction categories."""
        # Get category amounts and trends
        category_amounts = {}

        for category in TransactionCategory:
            transaction_ids = self.classifier.get_transactions_by_category(
                category=category, tenant_type=tenant_type, tenant_id=tenant_id
            )

            if transaction_ids:
                query = self.db.query(Transaction).filter(
                    and_(
                        Transaction.id.in_(transaction_ids),
                        Transaction.tenant_type == TenantType(tenant_type),
                        Transaction.tenant_id == tenant_id,
                    )
                )

                if period_start:
                    query = query.filter(Transaction.created_at >= period_start)
                if period_end:
                    query = query.filter(Transaction.created_at <= period_end)

                transactions = query.all()

                if transactions:
                    total_amount = sum(t.amount for t in transactions)
                    avg_amount = total_amount / len(transactions)

                    # Calculate trend (compare with previous period)
                    trend_data = self._calculate_category_trend(
                        category=category,
                        tenant_type=tenant_type,
                        tenant_id=tenant_id,
                        current_period_start=period_start,
                        current_period_end=period_end,
                    )

                    category_amounts[category.value] = {
                        "count": len(transactions),
                        "total_amount": float(total_amount),
                        "average_amount": float(avg_amount),
                        "min_amount": float(min(t.amount for t in transactions)),
                        "max_amount": float(max(t.amount for t in transactions)),
                        "trend": trend_data,
                    }

        # Calculate spending insights
        spending_insights = self._calculate_spending_insights(category_amounts=category_amounts)

        return {
            "category_analysis": category_amounts,
            "spending_insights": spending_insights,
            "period_start": period_start.isoformat() if period_start else None,
            "period_end": period_end.isoformat() if period_end else None,
            "analysis_type": "category",
        }

    def get_transaction_patterns(
        self, tenant_type: str, tenant_id: str, pattern_type: str = "all"  # "classification", "category", "all"
    ) -> Dict[str, Any]:
        """Analyze transaction patterns for insights."""
        patterns = {}

        if pattern_type in ["classification", "all"]:
            # Analyze classification patterns
            patterns["classification_patterns"] = self._analyze_classification_patterns(
                tenant_type=tenant_type, tenant_id=tenant_id
            )

        if pattern_type in ["category", "all"]:
            # Analyze category patterns
            patterns["category_patterns"] = self._analyze_category_patterns(
                tenant_type=tenant_type, tenant_id=tenant_id
            )

        if pattern_type == "all":
            # Cross-analysis
            patterns["cross_analysis"] = self._analyze_classification_category_correlation(
                tenant_type=tenant_type, tenant_id=tenant_id
            )

        return patterns

    def get_monthly_breakdown(self, tenant_type: str, tenant_id: str, months: int = 12) -> Dict[str, Any]:
        """Get monthly breakdown of classifications and categories."""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=months * 30)

        monthly_data = {}
        current_date = start_date

        while current_date < end_date:
            month_start = current_date.replace(day=1)
            next_month = (
                month_start.replace(month=month_start.month + 1)
                if month_start.month < 12
                else month_start.replace(year=month_start.year + 1, month=1)
            )
            month_end = next_month - timedelta(days=1)

            month_key = month_start.strftime("%Y-%m")

            # Get analytics for this month
            classification_analytics = self.get_classification_analytics(
                tenant_type=tenant_type, tenant_id=tenant_id, period_start=month_start, period_end=month_end
            )

            category_analytics = self.get_category_analytics(
                tenant_type=tenant_type, tenant_id=tenant_id, period_start=month_start, period_end=month_end
            )

            monthly_data[month_key] = {
                "classifications": classification_analytics["amount_analysis"],
                "categories": category_analytics["category_analysis"],
                "period": {"start": month_start.isoformat(), "end": month_end.isoformat()},
            }

            current_date = next_month

        return {
            "monthly_breakdown": monthly_data,
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "months_analyzed": months,
            },
        }

    def get_anomaly_detection(
        self, tenant_type: str, tenant_id: str, sensitivity: str = "medium"  # "low", "medium", "high"
    ) -> Dict[str, Any]:
        """Detect anomalies in transaction patterns."""
        # Define sensitivity thresholds
        thresholds = {
            "low": {"amount_multiplier": 5.0, "frequency_multiplier": 3.0},
            "medium": {"amount_multiplier": 3.0, "frequency_multiplier": 2.0},
            "high": {"amount_multiplier": 2.0, "frequency_multiplier": 1.5},
        }

        threshold = thresholds[sensitivity]
        anomalies = []

        # Get recent transactions (last 30 days)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)

        # Analyze each category for anomalies
        for category in TransactionCategory:
            transaction_ids = self.classifier.get_transactions_by_category(
                category=category, tenant_type=tenant_type, tenant_id=tenant_id
            )

            if transaction_ids:
                query = self.db.query(Transaction).filter(
                    and_(
                        Transaction.id.in_(transaction_ids),
                        Transaction.tenant_type == TenantType(tenant_type),
                        Transaction.tenant_id == tenant_id,
                        Transaction.created_at >= start_date,
                    )
                )

                recent_transactions = query.all()

                if len(recent_transactions) >= 5:  # Need sufficient data
                    # Calculate baseline metrics
                    amounts = [float(t.amount) for t in recent_transactions]
                    avg_amount = sum(amounts) / len(amounts)

                    # Detect amount anomalies
                    for transaction in recent_transactions:
                        if float(transaction.amount) > avg_amount * threshold["amount_multiplier"]:
                            anomalies.append(
                                {
                                    "type": "high_amount",
                                    "category": category.value,
                                    "transaction_id": str(transaction.id),
                                    "amount": float(transaction.amount),
                                    "average_amount": avg_amount,
                                    "multiplier": float(transaction.amount) / avg_amount,
                                    "description": transaction.description,
                                    "date": transaction.created_at.isoformat(),
                                }
                            )

        return {
            "anomalies": anomalies,
            "sensitivity": sensitivity,
            "analysis_period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_anomalies": len(anomalies),
        }

    def _calculate_category_trend(
        self,
        category: TransactionCategory,
        tenant_type: str,
        tenant_id: str,
        current_period_start: Optional[datetime],
        current_period_end: Optional[datetime],
    ) -> Dict[str, Any]:
        """Calculate trend for a category compared to previous period."""
        if not current_period_start or not current_period_end:
            return {"trend": "insufficient_data"}

        # Calculate previous period
        period_length = current_period_end - current_period_start
        previous_period_end = current_period_start
        previous_period_start = previous_period_end - period_length

        # Get previous period transactions
        transaction_ids = self.classifier.get_transactions_by_category(
            category=category, tenant_type=tenant_type, tenant_id=tenant_id
        )

        if not transaction_ids:
            return {"trend": "no_data"}

        previous_query = self.db.query(Transaction).filter(
            and_(
                Transaction.id.in_(transaction_ids),
                Transaction.tenant_type == TenantType(tenant_type),
                Transaction.tenant_id == tenant_id,
                Transaction.created_at >= previous_period_start,
                Transaction.created_at <= previous_period_end,
            )
        )

        previous_transactions = previous_query.all()

        if not previous_transactions:
            return {"trend": "no_previous_data"}

        previous_total = sum(t.amount for t in previous_transactions)

        # Get current period transactions
        current_query = self.db.query(Transaction).filter(
            and_(
                Transaction.id.in_(transaction_ids),
                Transaction.tenant_type == TenantType(tenant_type),
                Transaction.tenant_id == tenant_id,
                Transaction.created_at >= current_period_start,
                Transaction.created_at <= current_period_end,
            )
        )

        current_transactions = current_query.all()
        current_total = sum(t.amount for t in current_transactions)

        # Calculate trend
        if previous_total > 0:
            change_percentage = ((current_total - previous_total) / previous_total) * 100
            trend_direction = (
                "increasing" if change_percentage > 5 else "decreasing" if change_percentage < -5 else "stable"
            )
        else:
            change_percentage = 0
            trend_direction = "stable"

        return {
            "trend": trend_direction,
            "change_percentage": float(change_percentage),
            "previous_amount": float(previous_total),
            "current_amount": float(current_total),
            "previous_count": len(previous_transactions),
            "current_count": len(current_transactions),
        }

    def _calculate_spending_insights(self, category_amounts: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate spending insights from category data."""
        if not category_amounts:
            return {"message": "No category data available"}

        # Find top spending categories
        sorted_categories = sorted(category_amounts.items(), key=lambda x: x[1]["total_amount"], reverse=True)

        top_categories = sorted_categories[:5]
        total_spending = sum(data["total_amount"] for _, data in category_amounts.items() if data["total_amount"] > 0)

        insights = {
            "top_spending_categories": [
                {
                    "category": cat,
                    "amount": data["total_amount"],
                    "percentage": (data["total_amount"] / total_spending * 100) if total_spending > 0 else 0,
                    "transaction_count": data["count"],
                }
                for cat, data in top_categories
            ],
            "total_spending": total_spending,
            "categories_with_spending": len([c for c in category_amounts.values() if c["total_amount"] > 0]),
            "average_transaction_amount": (
                sum(data["average_amount"] for data in category_amounts.values()) / len(category_amounts)
                if category_amounts
                else 0
            ),
        }

        return insights

    def _analyze_classification_patterns(self, tenant_type: str, tenant_id: str) -> Dict[str, Any]:
        """Analyze patterns in transaction classifications."""
        patterns = {}

        for classification in TransactionClassification:
            transaction_ids = self.classifier.get_transactions_by_classification(
                classification=classification, tenant_type=tenant_type, tenant_id=tenant_id
            )

            if transaction_ids:
                transactions = self.db.query(Transaction).filter(Transaction.id.in_(transaction_ids)).all()

                # Analyze timing patterns
                hours = [t.created_at.hour for t in transactions]
                days_of_week = [t.created_at.weekday() for t in transactions]

                patterns[classification.value] = {
                    "total_count": len(transactions),
                    "common_hours": self._get_common_values(hours),
                    "common_days": self._get_common_values(days_of_week),
                    "avg_amount": float(sum(t.amount for t in transactions) / len(transactions)),
                }

        return patterns

    def _analyze_category_patterns(self, tenant_type: str, tenant_id: str) -> Dict[str, Any]:
        """Analyze patterns in transaction categories."""
        patterns = {}

        for category in TransactionCategory:
            transaction_ids = self.classifier.get_transactions_by_category(
                category=category, tenant_type=tenant_type, tenant_id=tenant_id
            )

            if transaction_ids:
                transactions = self.db.query(Transaction).filter(Transaction.id.in_(transaction_ids)).all()

                # Analyze patterns
                patterns[category.value] = {
                    "total_count": len(transactions),
                    "frequency_per_month": len(transactions) / 12 if len(transactions) > 12 else len(transactions),
                    "avg_amount": float(sum(t.amount for t in transactions) / len(transactions)),
                    "total_amount": float(sum(t.amount for t in transactions)),
                }

        return patterns

    def _analyze_classification_category_correlation(self, tenant_type: str, tenant_id: str) -> Dict[str, Any]:
        """Analyze correlation between classifications and categories."""
        correlations = {}

        # Get all classification and category tags
        classification_tags = (
            self.db.query(DataTag)
            .filter(
                DataTag.tag_key == "classification",
                DataTag.resource_type == "transaction",
                DataTag.tenant_type == TenantType(tenant_type),
                DataTag.tenant_id == tenant_id,
                DataTag.is_active.is_(True),
            )
            .all()
        )

        category_tags = (
            self.db.query(DataTag)
            .filter(
                DataTag.tag_key == "category",
                DataTag.resource_type == "transaction",
                DataTag.tenant_type == TenantType(tenant_type),
                DataTag.tenant_id == tenant_id,
                DataTag.is_active.is_(True),
            )
            .all()
        )

        # Create resource ID to tag mappings
        resource_classifications = {tag.resource_id: tag.tag_value for tag in classification_tags}
        resource_categories = {tag.resource_id: tag.tag_value for tag in category_tags}

        # Find correlations
        for resource_id in resource_classifications:
            if resource_id in resource_categories:
                classification = resource_classifications[resource_id]
                category = resource_categories[resource_id]

                if classification not in correlations:
                    correlations[classification] = {}
                if category not in correlations[classification]:
                    correlations[classification][category] = 0

                correlations[classification][category] += 1

        return correlations

    def _get_common_values(self, values: List[int], top_n: int = 3) -> List[Tuple[int, int]]:
        """Get most common values and their counts."""
        value_counts = {}
        for value in values:
            value_counts[value] = value_counts.get(value, 0) + 1

        return sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
