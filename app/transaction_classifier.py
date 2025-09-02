"""Transaction classification and categorization service for enhanced analytics."""

import re
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum as PyEnum

from sqlalchemy.orm import Session

from app.financial_models import Transaction
from app.tagging_service import TaggingService
from app.tagging_models import TagType


class TransactionClassification(PyEnum):
    """Transaction classification types based on patterns and characteristics."""

    RECURRING_PAYMENT = "recurring_payment"
    LARGE_TRANSFER = "large_transfer"
    MICRO_TRANSACTION = "micro_transaction"
    REFUND = "refund"
    FEE_CHARGE = "fee_charge"
    SALARY_INCOME = "salary_income"
    INVESTMENT_INCOME = "investment_income"
    BUSINESS_EXPENSE = "business_expense"
    PERSONAL_EXPENSE = "personal_expense"
    SUBSCRIPTION = "subscription"
    BILL_PAYMENT = "bill_payment"
    ATM_WITHDRAWAL = "atm_withdrawal"
    ONLINE_PURCHASE = "online_purchase"
    CASH_DEPOSIT = "cash_deposit"
    TRANSFER_INTERNAL = "transfer_internal"
    TRANSFER_EXTERNAL = "transfer_external"
    UNKNOWN = "unknown"


class TransactionCategory(PyEnum):
    """Enhanced transaction categories for detailed analytics."""

    # Income categories
    SALARY = "salary"
    BONUS = "bonus"
    INVESTMENT_RETURN = "investment_return"
    RENTAL_INCOME = "rental_income"
    BUSINESS_INCOME = "business_income"
    OTHER_INCOME = "other_income"

    # Expense categories
    FOOD_DINING = "food_dining"
    TRANSPORTATION = "transportation"
    UTILITIES = "utilities"
    HOUSING = "housing"
    HEALTHCARE = "healthcare"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    EDUCATION = "education"
    INSURANCE = "insurance"
    TAXES = "taxes"
    DEBT_PAYMENT = "debt_payment"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    CHARITY = "charity"
    BUSINESS_EXPENSE_CAT = "business_expense"
    FEES_CHARGES = "fees_charges"
    OTHER_EXPENSE = "other_expense"

    # Transfer categories
    INTERNAL_TRANSFER = "internal_transfer"
    EXTERNAL_TRANSFER = "external_transfer"

    # Uncategorized
    UNCATEGORIZED = "uncategorized"


class TransactionClassifierService:
    """Service for classifying and categorizing transactions automatically."""

    def __init__(self, db: Session):
        self.db = db
        self.tagging_service = TaggingService(db)

        # Classification patterns
        self.classification_patterns = {
            TransactionClassification.RECURRING_PAYMENT: [
                r"(?i)(subscription|monthly|recurring|autopay)",
                r"(?i)(netflix|spotify|amazon prime|hulu)",
                r"(?i)(insurance premium|loan payment)",
            ],
            TransactionClassification.SUBSCRIPTION: [
                r"(?i)(subscription|sub|monthly service)",
                r"(?i)(netflix|spotify|hulu|youtube|disney)",
                r"(?i)(adobe|microsoft|google)",
            ],
            TransactionClassification.BILL_PAYMENT: [
                r"(?i)(electric|electricity|gas|water|internet)",
                r"(?i)(phone|mobile|cellular|utility)",
                r"(?i)(rent|mortgage|property tax)",
            ],
            TransactionClassification.SALARY_INCOME: [
                r"(?i)(salary|payroll|wage|direct deposit)",
                r"(?i)(employer|company|inc|llc|corp)",
            ],
            TransactionClassification.REFUND: [
                r"(?i)(refund|return|credit|reimbursement)",
                r"(?i)(chargeback|dispute resolution)",
            ],
            TransactionClassification.FEE_CHARGE: [
                r"(?i)(fee|charge|penalty|interest)",
                r"(?i)(overdraft|atm fee|maintenance)",
            ],
            TransactionClassification.ATM_WITHDRAWAL: [
                r"(?i)(atm|cash withdrawal|cash advance)",
                r"(?i)(automated teller|withdrawal)",
            ],
            TransactionClassification.ONLINE_PURCHASE: [
                r"(?i)(amazon|ebay|etsy|paypal)",
                r"(?i)(online|web|e-commerce)",
            ],
        }

        # Category patterns
        self.category_patterns = {
            TransactionCategory.FOOD_DINING: [
                r"(?i)(restaurant|cafe|coffee|pizza|burger)",
                r"(?i)(grocery|supermarket|food|dining)",
                r"(?i)(mcdonalds|starbucks|subway|dominos)",
            ],
            TransactionCategory.TRANSPORTATION: [
                r"(?i)(gas|fuel|gasoline|station)",
                r"(?i)(uber|lyft|taxi|rideshare)",
                r"(?i)(parking|toll|metro|bus|train)",
            ],
            TransactionCategory.UTILITIES: [
                r"(?i)(electric|electricity|gas|water)",
                r"(?i)(internet|phone|mobile|cable)",
                r"(?i)(utility|telecom|isp)",
            ],
            TransactionCategory.HOUSING: [
                r"(?i)(rent|mortgage|property|real estate)",
                r"(?i)(home|house|apartment|condo)",
                r"(?i)(property tax|hoa|maintenance)",
            ],
            TransactionCategory.HEALTHCARE: [
                r"(?i)(doctor|medical|health|pharmacy)",
                r"(?i)(hospital|clinic|dental|vision)",
                r"(?i)(insurance|medicare|medicaid)",
            ],
            TransactionCategory.ENTERTAINMENT: [
                r"(?i)(movie|cinema|theater|concert)",
                r"(?i)(game|gaming|entertainment|sport)",
                r"(?i)(netflix|spotify|streaming)",
            ],
            TransactionCategory.SHOPPING: [
                r"(?i)(amazon|walmart|target|costco)",
                r"(?i)(mall|store|retail|shop)",
                r"(?i)(clothing|electronics|home)",
            ],
        }

    def classify_transaction(self, transaction: Transaction) -> TransactionClassification:
        """Classify a transaction based on its properties."""
        description = transaction.description or ""
        amount = transaction.amount
        transaction_type = transaction.transaction_type

        # Check for specific patterns in description
        for classification, patterns in self.classification_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description):
                    return classification

        # Classify by amount thresholds
        if amount >= Decimal("10000"):
            return TransactionClassification.LARGE_TRANSFER
        elif amount <= Decimal("5"):
            return TransactionClassification.MICRO_TRANSACTION

        # Classify by transaction type
        if transaction_type in ["transfer", "wire"]:
            to_account_id = getattr(transaction, "to_account_id", None)
            if to_account_id:
                return TransactionClassification.TRANSFER_INTERNAL
            else:
                return TransactionClassification.TRANSFER_EXTERNAL
        elif transaction_type == "credit" and amount > Decimal("1000"):
            return TransactionClassification.SALARY_INCOME
        elif transaction_type == "debit":
            return TransactionClassification.PERSONAL_EXPENSE

        return TransactionClassification.UNKNOWN

    def categorize_transaction(self, transaction: Transaction) -> TransactionCategory:
        """Categorize a transaction based on its properties."""
        description = transaction.description or ""
        amount = transaction.amount
        transaction_type = transaction.transaction_type

        # Check existing category first
        existing_category = getattr(transaction, "category", None)
        if existing_category:
            # Try to map existing category to our enum
            try:
                return TransactionCategory(existing_category.lower())
            except ValueError:
                pass

        # Check for specific patterns in description
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description):
                    return category

        # Categorize by transaction type and amount
        if transaction_type == "credit":
            if amount >= Decimal("2000"):
                return TransactionCategory.SALARY
            else:
                return TransactionCategory.OTHER_INCOME
        elif transaction_type == "debit":
            return TransactionCategory.OTHER_EXPENSE
        elif transaction_type in ["transfer", "wire"]:
            to_account_id = getattr(transaction, "to_account_id", None)
            if to_account_id:
                return TransactionCategory.INTERNAL_TRANSFER
            else:
                return TransactionCategory.EXTERNAL_TRANSFER

        return TransactionCategory.UNCATEGORIZED

    def auto_classify_and_categorize(self, transaction: Transaction, create_tags: bool = True) -> Dict[str, str]:
        """Automatically classify and categorize a transaction."""
        classification = self.classify_transaction(transaction)
        category = self.categorize_transaction(transaction)

        result = {
            "classification": classification.value,
            "category": category.value,
        }

        if create_tags:
            # Create classification tag
            self.tagging_service._create_tag(
                tag_type=TagType.CATEGORY,
                tag_key="classification",
                tag_value=classification.value,
                resource_type="transaction",
                resource_id=transaction.id,
                tenant_type=transaction.tenant_type.value,
                tenant_id=transaction.tenant_id,
                label=f"Classification: {classification.value.replace('_', ' ').title()}",
                metadata={
                    "auto_generated": True,
                    "classifier_version": "1.0",
                },
            )

            # Create category tag
            self.tagging_service._create_tag(
                tag_type=TagType.CATEGORY,
                tag_key="category",
                tag_value=category.value,
                resource_type="transaction",
                resource_id=transaction.id,
                tenant_type=transaction.tenant_type.value,
                tenant_id=transaction.tenant_id,
                label=f"Category: {category.value.replace('_', ' ').title()}",
                metadata={
                    "auto_generated": True,
                    "classifier_version": "1.0",
                },
            )

        return result

    def get_classification_patterns(self) -> Dict[str, List[str]]:
        """Get all classification patterns for debugging/configuration."""
        return {classification.value: patterns for classification, patterns in self.classification_patterns.items()}

    def get_category_patterns(self) -> Dict[str, List[str]]:
        """Get all category patterns for debugging/configuration."""
        return {category.value: patterns for category, patterns in self.category_patterns.items()}

    def add_classification_pattern(self, classification: TransactionClassification, pattern: str):
        """Add a new pattern for classification."""
        if classification not in self.classification_patterns:
            self.classification_patterns[classification] = []
        self.classification_patterns[classification].append(pattern)

    def add_category_pattern(self, category: TransactionCategory, pattern: str):
        """Add a new pattern for categorization."""
        if category not in self.category_patterns:
            self.category_patterns[category] = []
        self.category_patterns[category].append(pattern)

    def analyze_classification_distribution(self, tenant_type: str, tenant_id: str) -> Dict[str, Dict[str, int]]:
        """Analyze the distribution of classifications and categories."""
        from app.tagging_models import DataTag
        from app.core.tenant import TenantType

        # Get all classification tags
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

        # Get all category tags
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

        # Count distributions
        classification_dist = {}
        for tag in classification_tags:
            classification_dist[tag.tag_value] = classification_dist.get(tag.tag_value, 0) + 1

        category_dist = {}
        for tag in category_tags:
            category_dist[tag.tag_value] = category_dist.get(tag.tag_value, 0) + 1

        return {
            "classifications": classification_dist,
            "categories": category_dist,
            "total_classified": len(classification_tags),
            "total_categorized": len(category_tags),
        }

    def get_transactions_by_classification(
        self, classification: TransactionClassification, tenant_type: str, tenant_id: str, limit: Optional[int] = None
    ) -> List[str]:
        """Get transaction IDs by classification."""
        return (
            self.tagging_service.get_tagged_resources(
                tag_filters={"classification": classification.value},
                resource_type="transaction",
                tenant_type=tenant_type,
                tenant_id=tenant_id,
            )[:limit]
            if limit
            else self.tagging_service.get_tagged_resources(
                tag_filters={"classification": classification.value},
                resource_type="transaction",
                tenant_type=tenant_type,
                tenant_id=tenant_id,
            )
        )

    def get_transactions_by_category(
        self, category: TransactionCategory, tenant_type: str, tenant_id: str, limit: Optional[int] = None
    ) -> List[str]:
        """Get transaction IDs by category."""
        return (
            self.tagging_service.get_tagged_resources(
                tag_filters={"category": category.value},
                resource_type="transaction",
                tenant_type=tenant_type,
                tenant_id=tenant_id,
            )[:limit]
            if limit
            else self.tagging_service.get_tagged_resources(
                tag_filters={"category": category.value},
                resource_type="transaction",
                tenant_type=tenant_type,
                tenant_id=tenant_id,
            )
        )
