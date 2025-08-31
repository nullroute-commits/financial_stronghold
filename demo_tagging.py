#!/usr/bin/env python3
"""
Demo script showing the USER_ID, ORG_ID, ROLE_ID level tagging and analytics feature.

This script demonstrates:
1. Creating tags for financial resources
2. Querying resources by tag filters  
3. Computing analytics based on tags
4. Creating saved analytics views
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