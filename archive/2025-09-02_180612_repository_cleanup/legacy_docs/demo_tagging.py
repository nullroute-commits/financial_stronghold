#!/usr/bin/env python3
"""
Demo script showing the enhanced USER_ID, ORG_ID, ROLE_ID level tagging and analytics feature
with transaction classification and categorization.

This script demonstrates:
1. Creating tags for financial resources
2. Automatic transaction classification and categorization
3. Querying resources by tag filters  
4. Computing analytics based on tags and classifications
5. Advanced analytics with anomaly detection and patterns
6. Creating saved analytics views
"""

import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from typing import Dict, Any

# Mock database session and services for demo
class MockDBSession:
    def __init__(self):
        self.data = []
        self._committed = False
        
    def add(self, obj):
        self.data.append(obj)
        
    def commit(self):
        self._committed = True
        
    def refresh(self, obj):
        pass
        
    def query(self, model_class):
        return MockQuery(self.data, model_class)

class MockQuery:
    def __init__(self, data, model_class):
        self.data = [item for item in data if isinstance(item, model_class)]
        
    def filter(self, *args):
        return self
        
    def first(self):
        return self.data[0] if self.data else None
        
    def all(self):
        return self.data

# Mock models for demo
class MockUser:
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email
        self.roles = []
        self.created_at = datetime.now(timezone.utc)

class MockRole:
    def __init__(self, id, name, is_active=True):
        self.id = id
        self.name = name
        self.is_active = is_active
        self.created_at = datetime.now(timezone.utc)

class MockTransaction:
    def __init__(self, id, amount, currency, transaction_type, tenant_type, tenant_id, description=None, category=None):
        self.id = id
        self.amount = Decimal(str(amount))
        self.currency = currency
        self.transaction_type = transaction_type
        self.tenant_type = tenant_type
        self.tenant_id = tenant_id
        self.description = description
        self.category = category
        self.created_at = datetime.now(timezone.utc)

class MockDataTag:
    def __init__(self, tag_type, tag_key, tag_value, resource_type, resource_id, 
                 tenant_type, tenant_id, tag_label=None, tag_metadata=None):
        self.id = str(uuid4())
        self.tag_type = tag_type
        self.tag_key = tag_key
        self.tag_value = tag_value
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.tenant_type = tenant_type
        self.tenant_id = tenant_id
        self.tag_label = tag_label
        self.tag_metadata = tag_metadata or {}
        self.is_active = True
        self.created_at = datetime.now(timezone.utc)

# Mock services
class MockTaggingService:
    def __init__(self):
        self.tags = []
    
    def create_user_tag(self, user_id, resource_type, resource_id, tenant_type, tenant_id, label=None, metadata=None):
        tag = MockDataTag("user", "user_id", str(user_id), resource_type, resource_id, 
                         tenant_type, tenant_id, label, metadata)
        self.tags.append(tag)
        return tag

class MockTransactionClassifier:
    def __init__(self):
        self.classification_patterns = {
            "subscription": ["netflix", "spotify", "hulu", "disney", "subscription"],
            "bill_payment": ["electric", "gas", "water", "internet", "phone", "rent"],
            "salary_income": ["salary", "payroll", "wage", "employer"],
            "food_dining": ["restaurant", "mcdonalds", "starbucks", "food", "dining"],
            "transportation": ["uber", "lyft", "gas", "fuel", "parking"],
            "large_transfer": [],  # Based on amount
            "micro_transaction": []  # Based on amount
        }
        
        self.category_patterns = {
            "entertainment": ["netflix", "spotify", "movie", "game", "concert"],
            "food_dining": ["restaurant", "mcdonalds", "starbucks", "food"],
            "transportation": ["uber", "lyft", "gas", "fuel", "taxi"],
            "utilities": ["electric", "gas", "water", "internet", "phone"],
            "salary": ["salary", "payroll", "wage"],
            "other_expense": [],
            "other_income": []
        }
    
    def classify_transaction(self, transaction):
        """Classify transaction based on patterns and amount."""
        description = (transaction.description or "").lower()
        amount = transaction.amount
        
        # Check amount-based classifications first
        if amount >= Decimal('10000'):
            return "large_transfer"
        elif amount <= Decimal('5'):
            return "micro_transaction"
        
        # Check pattern-based classifications
        for classification, patterns in self.classification_patterns.items():
            for pattern in patterns:
                if pattern in description:
                    return classification
        
        # Default based on transaction type
        if transaction.transaction_type == "credit" and amount > Decimal('1000'):
            return "salary_income"
        elif transaction.transaction_type == "debit":
            return "personal_expense"
        
        return "unknown"
    
    def categorize_transaction(self, transaction):
        """Categorize transaction based on patterns."""
        description = (transaction.description or "").lower()
        
        # Check pattern-based categories
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if pattern in description:
                    return category
        
        # Default based on transaction type
        if transaction.transaction_type == "credit":
            return "other_income"
        else:
            return "other_expense"


def demo_enhanced_tagging_and_analytics():
    """Demonstrate the enhanced tagging and analytics feature with classification."""
    
    print("🏦 Enhanced Financial Stronghold - Transaction Classification & Analytics Demo")
    print("=" * 80)
    
    # Initialize mock services
    db_session = MockDBSession()
    tagging_service = MockTaggingService()
    classifier = MockTransactionClassifier()
    
    # Create sample users and roles
    print("\n👥 Setting up Users and Roles:")
    user1 = MockUser("user-123", "John Doe", "john@example.com")
    user2 = MockUser("user-456", "Jane Smith", "jane@example.com")
    
    role1 = MockRole("role-789", "Manager")
    role2 = MockRole("role-101", "Employee")
    
    user1.roles = [role1]
    user2.roles = [role2]
    
    print(f"  👤 {user1.name} ({user1.id}) - Role: {role1.name}")
    print(f"  👤 {user2.name} ({user2.id}) - Role: {role2.name}")
    
    # Create diverse sample transactions for classification demo
    print("\n💳 Creating Diverse Sample Transactions:")
    transactions = [
        # Subscription/Entertainment
        MockTransaction("tx-001", 29.99, "USD", "debit", "user", "user-123", 
                       "Netflix Monthly Subscription", "entertainment"),
        MockTransaction("tx-002", 14.99, "USD", "debit", "user", "user-123", 
                       "Spotify Premium Subscription", "entertainment"),
        
        # Food & Dining
        MockTransaction("tx-003", 45.67, "USD", "debit", "user", "user-123", 
                       "McDonald's Restaurant Downtown", "food"),
        MockTransaction("tx-004", 8.50, "USD", "debit", "user", "user-456", 
                       "Starbucks Coffee", "food"),
        
        # Transportation
        MockTransaction("tx-005", 25.30, "USD", "debit", "user", "user-456", 
                       "Uber ride to airport", "transportation"),
        MockTransaction("tx-006", 55.00, "USD", "debit", "user", "user-123", 
                       "Gas station fuel", "transportation"),
        
        # Bills/Utilities
        MockTransaction("tx-007", 125.43, "USD", "debit", "user", "user-123", 
                       "Electric company bill payment", "utilities"),
        MockTransaction("tx-008", 89.99, "USD", "debit", "user", "user-456", 
                       "Internet service provider", "utilities"),
        
        # Income
        MockTransaction("tx-009", 5000.00, "USD", "credit", "user", "user-123", 
                       "Salary deposit from ACME Corp", "income"),
        MockTransaction("tx-010", 4500.00, "USD", "credit", "user", "user-456", 
                       "Payroll direct deposit", "income"),
        
        # Large transfer
        MockTransaction("tx-011", 15000.00, "USD", "transfer", "user", "user-123", 
                       "Wire transfer to investment account", "investment"),
        
        # Micro transactions
        MockTransaction("tx-012", 2.50, "USD", "debit", "user", "user-456", 
                       "Parking meter payment", "transportation"),
        MockTransaction("tx-013", 1.99, "USD", "debit", "user", "user-123", 
                       "Mobile app purchase", "entertainment"),
        
        # Organization transaction
        MockTransaction("tx-014", 1200.00, "USD", "debit", "organization", "org-999", 
                       "Office supplies bulk order", "business"),
    ]
    
    print(f"  📊 Created {len(transactions)} sample transactions")
    for tx in transactions[:5]:  # Show first 5
        print(f"    💰 {tx.id}: ${tx.amount} - {tx.description}")
    print(f"    ... and {len(transactions) - 5} more")
    
    # Demonstrate automatic classification and categorization
    print("\n🎯 Automatic Transaction Classification & Categorization:")
    print("-" * 60)
    
    classification_results = {}
    category_results = {}
    
    for tx in transactions:
        classification = classifier.classify_transaction(tx)
        category = classifier.categorize_transaction(tx)
        
        classification_results[tx.id] = classification
        category_results[tx.id] = category
        
        print(f"  🏷️  {tx.id}: {tx.description[:40]:<40}")
        print(f"      📋 Classification: {classification}")
        print(f"      🗂️  Category: {category}")
        print(f"      💵 Amount: ${tx.amount} ({tx.transaction_type})")
        print()
    
    # Create enhanced tags including classifications and categories
    print("\n🏷️  Creating Enhanced Tags (USER_ID, ORG_ID, ROLE_ID + Classifications):")
    tags = []
    
    # Standard tags (existing functionality)
    for tx in transactions[:3]:  # First 3 are user transactions
        user_id = tx.tenant_id if tx.tenant_type == "user" else None
        if user_id:
            tag = MockDataTag(
                tag_type="user",
                tag_key="user_id", 
                tag_value=user_id,
                resource_type="transaction",
                resource_id=tx.id,
                tenant_type="user",
                tenant_id=user_id,
                tag_label=f"User Transaction - {user_id}"
            )
            tags.append(tag)
    
    # Organization tag
    org_tag = MockDataTag(
        tag_type="organization",
        tag_key="org_id",
        tag_value="org-999", 
        resource_type="transaction",
        resource_id=transactions[-1].id,  # Last transaction is org
        tenant_type="organization",
        tenant_id="org-999",
        tag_label="Organization Transaction"
    )
    tags.append(org_tag)
    
    # Role tags for first 2 transactions (manager role)
    for tx in transactions[:2]:
        role_tag = MockDataTag(
            tag_type="role",
            tag_key="role_id",
            tag_value="role-789",
            resource_type="transaction", 
            resource_id=tx.id,
            tenant_type="user",
            tenant_id="user-123",
            tag_label=f"Manager Role Transaction"
        )
        tags.append(role_tag)
    
    # NEW: Classification tags
    for tx in transactions:
        classification = classification_results[tx.id]
        classification_tag = MockDataTag(
            tag_type="category",
            tag_key="classification",
            tag_value=classification,
            resource_type="transaction",
            resource_id=tx.id,
            tenant_type=tx.tenant_type,
            tenant_id=tx.tenant_id,
            tag_label=f"Classification: {classification.replace('_', ' ').title()}",
            tag_metadata={"auto_generated": True, "classifier_version": "1.0"}
        )
        tags.append(classification_tag)
    
    # NEW: Category tags
    for tx in transactions:
        category = category_results[tx.id]
        category_tag = MockDataTag(
            tag_type="category",
            tag_key="category",
            tag_value=category,
            resource_type="transaction",
            resource_id=tx.id,
            tenant_type=tx.tenant_type,
            tenant_id=tx.tenant_id,
            tag_label=f"Category: {category.replace('_', ' ').title()}",
            tag_metadata={"auto_generated": True, "classifier_version": "1.0"}
        )
        tags.append(category_tag)
    
    print(f"  ✅ Created {len(tags)} tags total:")
    print(f"     📍 Traditional tags (user_id, org_id, role_id): {len([t for t in tags if t.tag_key in ['user_id', 'org_id', 'role_id']])}")
    print(f"     🎯 Classification tags: {len([t for t in tags if t.tag_key == 'classification'])}")
    print(f"     🗂️  Category tags: {len([t for t in tags if t.tag_key == 'category'])}")
    
    # Enhanced Analytics - Classification Analysis
    print("\n📊 Enhanced Analytics - Classification Analysis:")
    print("-" * 60)
    
    # Count transactions by classification
    classification_counts = {}
    classification_amounts = {}
    
    for classification in classification_results.values():
        classification_counts[classification] = classification_counts.get(classification, 0) + 1
        if classification not in classification_amounts:
            classification_amounts[classification] = []
    
    for tx in transactions:
        classification = classification_results[tx.id]
        classification_amounts[classification].append(float(tx.amount))
    
    print("  🎯 Classification Distribution:")
    for classification, count in sorted(classification_counts.items()):
        amounts = classification_amounts[classification]
        total_amount = sum(amounts)
        avg_amount = total_amount / count if count > 0 else 0
        
        print(f"    📋 {classification.replace('_', ' ').title():<20}: {count:>2} transactions, ${total_amount:>8,.2f} total, ${avg_amount:>7,.2f} avg")
    
    # Enhanced Analytics - Category Analysis  
    print("\n  🗂️  Category Distribution:")
    category_counts = {}
    category_amounts = {}
    
    for category in category_results.values():
        category_counts[category] = category_counts.get(category, 0) + 1
        if category not in category_amounts:
            category_amounts[category] = []
    
    for tx in transactions:
        category = category_results[tx.id]
        category_amounts[category].append(float(tx.amount))
    
    for category, count in sorted(category_counts.items()):
        amounts = category_amounts[category]
        total_amount = sum(amounts)
        avg_amount = total_amount / count if count > 0 else 0
        
        print(f"    🗂️  {category.replace('_', ' ').title():<20}: {count:>2} transactions, ${total_amount:>8,.2f} total, ${avg_amount:>7,.2f} avg")
    
    # Advanced Analytics - Spending Insights
    print("\n💡 Advanced Spending Insights:")
    print("-" * 40)
    
    # Top spending categories
    expense_categories = {k: v for k, v in category_amounts.items() 
                         if k not in ['salary', 'other_income']}
    
    if expense_categories:
        sorted_expenses = sorted(expense_categories.items(), 
                               key=lambda x: sum(x[1]), reverse=True)
        
        total_expenses = sum(sum(amounts) for amounts in expense_categories.values())
        
        print("  💸 Top Spending Categories:")
        for i, (category, amounts) in enumerate(sorted_expenses[:5], 1):
            total = sum(amounts)
            percentage = (total / total_expenses * 100) if total_expenses > 0 else 0
            print(f"    {i}. {category.replace('_', ' ').title():<20}: ${total:>8,.2f} ({percentage:>5.1f}%)")
    
    # Income analysis
    income_categories = {k: v for k, v in category_amounts.items() 
                        if k in ['salary', 'other_income']}
    
    if income_categories:
        total_income = sum(sum(amounts) for amounts in income_categories.values())
        print(f"\n  💰 Total Income: ${total_income:,.2f}")
        for category, amounts in income_categories.items():
            total = sum(amounts)
            percentage = (total / total_income * 100) if total_income > 0 else 0
            print(f"     💵 {category.replace('_', ' ').title()}: ${total:,.2f} ({percentage:.1f}%)")
    
    # Anomaly Detection Demo
    print("\n🚨 Anomaly Detection:")
    print("-" * 30)
    
    # Calculate average amounts by category for anomaly detection
    category_averages = {}
    for category, amounts in category_amounts.items():
        if amounts:
            category_averages[category] = sum(amounts) / len(amounts)
    
    anomalies = []
    anomaly_threshold = 3.0  # 3x the average
    
    for tx in transactions:
        category = category_results[tx.id]
        if category in category_averages:
            avg_amount = category_averages[category]
            if float(tx.amount) > avg_amount * anomaly_threshold:
                anomalies.append({
                    "transaction": tx,
                    "category": category,
                    "amount": float(tx.amount),
                    "average": avg_amount,
                    "multiplier": float(tx.amount) / avg_amount
                })
    
    if anomalies:
        print("  ⚠️  Detected anomalous transactions:")
        for anomaly in anomalies:
            tx = anomaly["transaction"]
            print(f"    🔍 {tx.id}: ${anomaly['amount']:.2f} in {anomaly['category']}")
            print(f"       💡 {anomaly['multiplier']:.1f}x higher than category average (${anomaly['average']:.2f})")
            print(f"       📝 {tx.description}")
    else:
        print("  ✅ No anomalies detected in current transactions")
    
    # Multi-dimensional Analysis (existing + new)
    print("\n🔍 Multi-dimensional Analysis Examples:")
    print("-" * 50)
    
    # 1. User + Classification analysis
    print("  👤 User-123 (John Doe) Subscription Analysis:")
    user_123_subscriptions = [
        tx for tx in transactions 
        if tx.tenant_id == "user-123" and classification_results[tx.id] == "subscription"
    ]
    
    if user_123_subscriptions:
        sub_total = sum(tx.amount for tx in user_123_subscriptions)
        print(f"     💳 Subscriptions: {len(user_123_subscriptions)} transactions")
        print(f"     💰 Total subscription spending: ${sub_total}")
        for tx in user_123_subscriptions:
            print(f"       🎵 {tx.description}: ${tx.amount}")
    
    # 2. Manager role + Large transactions
    print("\n  👔 Manager Role Large Transaction Analysis:")
    manager_large_txs = [
        tx for tx in transactions 
        if any(tag.tag_key == "role_id" and tag.tag_value == "role-789" 
               and tag.resource_id == tx.id for tag in tags) 
        and classification_results[tx.id] == "large_transfer"
    ]
    
    if manager_large_txs:
        large_total = sum(tx.amount for tx in manager_large_txs)
        print(f"     🏦 Large transfers by managers: {len(manager_large_txs)} transactions")
        print(f"     💰 Total amount: ${large_total:,.2f}")
    else:
        print("     ℹ️  No large transfers by managers in this dataset")
    
    # 3. Category + Amount Range Analysis
    print("\n  💸 High-Value Entertainment Spending:")
    entertainment_txs = [
        tx for tx in transactions 
        if category_results[tx.id] == "entertainment" and tx.amount >= Decimal("25")
    ]
    
    if entertainment_txs:
        entertainment_total = sum(tx.amount for tx in entertainment_txs)
        print(f"     🎬 High-value entertainment: {len(entertainment_txs)} transactions")
        print(f"     💰 Total: ${entertainment_total}")
        for tx in entertainment_txs:
            print(f"       🎮 {tx.description}: ${tx.amount}")
    
    # Summary and API Usage Examples
    print("\n🌟 Summary & Next Steps:")
    print("=" * 50)
    
    print(f"  📈 Successfully demonstrated enhanced transaction analytics:")
    print(f"     • Created {len(transactions)} diverse transactions")
    print(f"     • Applied {len(set(classification_results.values()))} different classifications")
    print(f"     • Categorized into {len(set(category_results.values()))} categories")
    print(f"     • Generated {len(tags)} total tags (traditional + classification)")
    print(f"     • Detected {len(anomalies)} anomalous transactions")
    
    print(f"\n  🚀 API Usage Examples:")
    print(f"     POST /financial/transactions/classify")
    print(f"     POST /financial/analytics/classification")
    print(f"     POST /financial/analytics/anomalies")
    print(f"     GET  /financial/analytics/patterns")
    print(f"     GET  /financial/analytics/monthly-breakdown")
    print(f"     GET  /financial/classification/config")
    
    print(f"\n  🎯 Key Features Demonstrated:")
    print(f"     ✅ Automatic transaction classification")
    print(f"     ✅ Smart categorization with pattern matching")
    print(f"     ✅ Enhanced analytics with spending insights")
    print(f"     ✅ Anomaly detection for unusual patterns")
    print(f"     ✅ Multi-dimensional analysis capabilities")
    print(f"     ✅ Integration with existing tagging system")
    
    print(f"\n🏁 Demo completed successfully!")
    print(f"   Ready for deployment following FEATURE_DEPLOYMENT_GUIDE.md process")


if __name__ == "__main__":
    try:
        demo_enhanced_tagging_and_analytics()
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        sys.exit(1)
class MockUser:
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email
        self.roles = []

class MockRole:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.is_active = True

class MockTransaction:
    def __init__(self, id, amount, currency, transaction_type, tenant_type, tenant_id):
        self.id = id
        self.amount = Decimal(str(amount))
        self.currency = currency
        self.transaction_type = transaction_type
        self.tenant_type = tenant_type
        self.tenant_id = tenant_id
        self.created_at = datetime.now(timezone.utc)

class MockDataTag:
    def __init__(self, tag_type, tag_key, tag_value, resource_type, resource_id, 
                 tenant_type, tenant_id, tag_label=None, tag_metadata=None):
        self.id = str(uuid4())
        self.tag_type = tag_type
        self.tag_key = tag_key
        self.tag_value = tag_value
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.tenant_type = tenant_type
        self.tenant_id = tenant_id
        self.tag_label = tag_label
        self.tag_metadata = tag_metadata or {}
        self.is_active = True
        self.created_at = datetime.now(timezone.utc)

def demo_tagging_and_analytics():
    """Demonstrate the tagging and analytics feature."""
    
    print("🏷️  Financial Stronghold - Tagging & Analytics Demo")
    print("=" * 60)
    
    # Create mock data
    user1 = MockUser("user-123", "john_doe", "john@example.com")
    user2 = MockUser("user-456", "jane_smith", "jane@example.com") 
    role1 = MockRole("role-789", "manager")
    role2 = MockRole("role-012", "analyst")
    
    user1.roles = [role1]
    user2.roles = [role2]
    
    # Create transactions
    transactions = [
        MockTransaction("tx-001", 100.50, "USD", "debit", "user", "user-123"),
        MockTransaction("tx-002", 250.00, "USD", "credit", "user", "user-123"),
        MockTransaction("tx-003", 75.25, "USD", "debit", "user", "user-456"),
        MockTransaction("tx-004", 500.00, "USD", "transfer", "organization", "org-999"),
    ]
    
    print("\n📊 Sample Data Created:")
    print(f"  Users: {len([user1, user2])}")
    print(f"  Roles: {len([role1, role2])}")
    print(f"  Transactions: {len(transactions)}")
    
    # Simulate tagging
    tags = []
    
    # Tag transactions with USER_ID
    for tx in transactions[:3]:  # First 3 are user transactions
        user_id = tx.tenant_id if tx.tenant_type == "user" else None
        if user_id:
            tag = MockDataTag(
                tag_type="user",
                tag_key="user_id", 
                tag_value=user_id,
                resource_type="transaction",
                resource_id=tx.id,
                tenant_type="user",
                tenant_id=user_id,
                tag_label=f"User Transaction - {user_id}"
            )
            tags.append(tag)
    
    # Tag with ORG_ID
    org_tag = MockDataTag(
        tag_type="organization",
        tag_key="org_id",
        tag_value="org-999", 
        resource_type="transaction",
        resource_id=transactions[3].id,
        tenant_type="organization",
        tenant_id="org-999",
        tag_label="Organization Transaction"
    )
    tags.append(org_tag)
    
    # Tag with ROLE_ID
    for tx in transactions[:2]:  # First 2 transactions (user-123 with manager role)
        role_tag = MockDataTag(
            tag_type="role",
            tag_key="role_id",
            tag_value="role-789",
            resource_type="transaction", 
            resource_id=tx.id,
            tenant_type="user",
            tenant_id="user-123",
            tag_label=f"Manager Role Transaction"
        )
        tags.append(role_tag)
    
    print("\n🏷️  Tags Created:")
    for tag in tags:
        print(f"  • {tag.tag_type}: {tag.tag_key}={tag.tag_value} → {tag.resource_type}:{tag.resource_id[:8]}...")
    
    # Simulate analytics queries
    print("\n📈 Analytics Queries:")
    
    # 1. Find transactions by USER_ID
    user_123_txs = [tx for tx in transactions if any(
        tag.tag_key == "user_id" and tag.tag_value == "user-123" 
        for tag in tags if tag.resource_id == tx.id
    )]
    
    user_123_total = sum(tx.amount for tx in user_123_txs)
    print(f"\n  🔍 USER_ID=user-123 Analytics:")
    print(f"    Transactions: {len(user_123_txs)}")
    print(f"    Total Amount: ${user_123_total}")
    print(f"    Average: ${user_123_total / len(user_123_txs) if user_123_txs else 0}")
    
    # 2. Find transactions by ROLE_ID
    manager_txs = [tx for tx in transactions if any(
        tag.tag_key == "role_id" and tag.tag_value == "role-789"
        for tag in tags if tag.resource_id == tx.id
    )]
    
    manager_total = sum(tx.amount for tx in manager_txs)
    print(f"\n  🔍 ROLE_ID=role-789 (Manager) Analytics:")
    print(f"    Transactions: {len(manager_txs)}")
    print(f"    Total Amount: ${manager_total}")
    print(f"    Transaction Types: {set(tx.transaction_type for tx in manager_txs)}")
    
    # 3. Find transactions by ORG_ID  
    org_txs = [tx for tx in transactions if any(
        tag.tag_key == "org_id" and tag.tag_value == "org-999"
        for tag in tags if tag.resource_id == tx.id
    )]
    
    org_total = sum(tx.amount for tx in org_txs)
    print(f"\n  🔍 ORG_ID=org-999 Analytics:")
    print(f"    Transactions: {len(org_txs)}")
    print(f"    Total Amount: ${org_total}")
    
    # 4. Cross-dimensional analysis
    print(f"\n  🔍 Multi-dimensional Analysis:")
    print(f"    User-123 + Manager Role: ${sum(tx.amount for tx in transactions if tx.id in [tag.resource_id for tag in tags if tag.tag_key in ['user_id', 'role_id'] and tag.tag_value in ['user-123', 'role-789']])}")
    
    # Simulate analytics view creation
    analytics_view = {
        "id": str(uuid4()),
        "view_name": "Manager Role Analytics",
        "view_description": "Analytics for manager role across all tenants",
        "tag_filters": {"role_id": "role-789"},
        "resource_types": ["transaction"],
        "metrics": {
            "transaction": {
                "resource_type": "transaction",
                "total_count": len(manager_txs),
                "total_amount": float(manager_total),
                "average_amount": float(manager_total / len(manager_txs) if manager_txs else 0),
                "min_amount": float(min(tx.amount for tx in manager_txs) if manager_txs else 0),
                "max_amount": float(max(tx.amount for tx in manager_txs) if manager_txs else 0),
                "type_breakdown": {
                    tx_type: {
                        "count": len([tx for tx in manager_txs if tx.transaction_type == tx_type]),
                        "amount": float(sum(tx.amount for tx in manager_txs if tx.transaction_type == tx_type))
                    }
                    for tx_type in set(tx.transaction_type for tx in manager_txs)
                }
            }
        },
        "computation_status": "completed",
        "last_computed": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    print(f"\n📊 Analytics View Created:")
    print(f"    Name: {analytics_view['view_name']}")
    print(f"    Filters: {analytics_view['tag_filters']}")
    print(f"    Status: {analytics_view['computation_status']}")
    print(f"    Metrics Preview:")
    for resource_type, metrics in analytics_view['metrics'].items():
        print(f"      {resource_type}: {metrics['total_count']} items, ${metrics['total_amount']} total")
    
    # API endpoint examples
    print(f"\n🌐 API Endpoint Examples:")
    print(f"    POST /financial/tags")
    print(f"    GET  /financial/tags/resource/transaction/{{id}}")
    print(f"    POST /financial/tags/auto/transaction/{{id}}")
    print(f"    POST /financial/tags/query")
    print(f"    POST /financial/analytics/compute")
    print(f"    POST /financial/analytics/summary")
    print(f"    POST /financial/analytics/views")
    print(f"    GET  /financial/analytics/views")
    print(f"    GET  /financial/dashboard/analytics?user_id=user-123&role_id=role-789")
    
    # Sample API requests
    print(f"\n📝 Sample API Requests:")
    
    sample_tag_request = {
        "tag_type": "user",
        "tag_key": "user_id",
        "tag_value": "user-123",
        "resource_type": "transaction",
        "resource_id": "tx-001",
        "tag_label": "User Transaction",
        "tag_description": "Transaction tagged to specific user",
        "tag_color": "#3498db"
    }
    
    sample_analytics_request = {
        "tag_filters": {"role_id": "role-789"},
        "resource_types": ["transaction", "account", "budget"],
        "period_start": "2024-01-01T00:00:00Z",
        "period_end": "2024-12-31T23:59:59Z"
    }
    
    print(f"\n  🏷️  Create Tag:")
    print(f"    POST /financial/tags")
    print(f"    {json.dumps(sample_tag_request, indent=4)}")
    
    print(f"\n  📊 Compute Analytics:")
    print(f"    POST /financial/analytics/summary")
    print(f"    {json.dumps(sample_analytics_request, indent=4)}")
    
    print(f"\n✅ Demo completed! The tagging and analytics feature provides:")
    print(f"   • USER_ID level tagging and analysis")
    print(f"   • ORG_ID level tagging and analysis") 
    print(f"   • ROLE_ID level tagging and analysis")
    print(f"   • Multi-dimensional analytics")
    print(f"   • Saved analytics views")
    print(f"   • RESTful API endpoints")
    print(f"   • Dashboard integration")

if __name__ == "__main__":
    demo_tagging_and_analytics()