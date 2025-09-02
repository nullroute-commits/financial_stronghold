#!/usr/bin/env python3
"""
Multi-tenancy demonstration script for Financial Stronghold.

This script demonstrates how to use the multi-tenant API with different tenant types.
"""

import requests
import json
from datetime import datetime, timedelta
from jose import jwt

# Configuration
API_BASE = "http://localhost:8000"
SECRET_KEY = "your-secret-key-here"  # Should match the one in app/auth.py
ALGORITHM = "HS256"

def create_jwt_token(user_id: str, tenant_type: str, tenant_id: str) -> str:
    """Create a JWT token for testing."""
    payload = {
        "sub": user_id,
        "tenant_type": tenant_type,
        "tenant_id": tenant_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def make_request(method: str, endpoint: str, token: str, data=None):
    """Make an API request with proper authentication."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{API_BASE}{endpoint}"
    
    if method.upper() == "GET":
        response = requests.get(url, headers=headers)
    elif method.upper() == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method.upper() == "PUT":
        response = requests.put(url, headers=headers, json=data)
    elif method.upper() == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    return response

def demo_user_tenant():
    """Demonstrate user tenant functionality."""
    print("\\n" + "="*50)
    print("USER TENANT DEMONSTRATION")
    print("="*50)
    
    # Create token for user tenant
    user_id = "550e8400-e29b-41d4-a716-446655440000"  # Example UUID
    token = create_jwt_token(user_id, "user", user_id)
    
    print(f"Created JWT token for user: {user_id}")
    
    # Get tenant info
    print("\\n1. Getting tenant information...")
    response = make_request("GET", "/tenant/info", token)
    if response.status_code == 200:
        print("✅ Tenant info:", json.dumps(response.json(), indent=2))
    else:
        print("❌ Failed to get tenant info:", response.status_code, response.text)
        return
    
    # Create personal account
    print("\\n2. Creating personal checking account...")
    account_data = {
        "name": "Personal Checking",
        "account_type": "checking",
        "balance": 1500.00,
        "currency": "USD",
        "description": "Main checking account"
    }
    
    response = make_request("POST", "/financial/accounts", token, account_data)
    if response.status_code == 201:
        account = response.json()
        print("✅ Created account:", account["name"], f"(ID: {account['id']})")
        account_id = account["id"]
    else:
        print("❌ Failed to create account:", response.status_code, response.text)
        return
    
    # Create transaction
    print("\\n3. Creating a transaction...")
    transaction_data = {
        "amount": 50.00,
        "currency": "USD",
        "description": "Grocery shopping",
        "transaction_type": "debit",
        "account_id": account_id,
        "category": "food"
    }
    
    response = make_request("POST", "/financial/transactions", token, transaction_data)
    if response.status_code == 201:
        transaction = response.json()
        print("✅ Created transaction:", transaction["description"], f"(${transaction['amount']})")
    else:
        print("❌ Failed to create transaction:", response.status_code, response.text)
    
    # List accounts
    print("\\n4. Listing all accounts...")
    response = make_request("GET", "/financial/accounts", token)
    if response.status_code == 200:
        accounts = response.json()
        print(f"✅ Found {len(accounts)} account(s):")
        for acc in accounts:
            print(f"   - {acc['name']}: ${acc['balance']} ({acc['account_type']})")
    else:
        print("❌ Failed to list accounts:", response.status_code, response.text)
    
    # List transactions
    print("\\n5. Listing all transactions...")
    response = make_request("GET", "/financial/transactions", token)
    if response.status_code == 200:
        transactions = response.json()
        print(f"✅ Found {len(transactions)} transaction(s):")
        for txn in transactions:
            print(f"   - {txn['description']}: ${txn['amount']} ({txn['transaction_type']})")
    else:
        print("❌ Failed to list transactions:", response.status_code, response.text)

def demo_organization_tenant():
    """Demonstrate organization tenant functionality."""
    print("\\n" + "="*50)
    print("ORGANIZATION TENANT DEMONSTRATION")
    print("="*50)
    
    # Create token for organization tenant
    user_id = "550e8400-e29b-41d4-a716-446655440001"  # Different user
    org_id = "123"  # Organization ID
    token = create_jwt_token(user_id, "organization", org_id)
    
    print(f"Created JWT token for organization: {org_id} (user: {user_id})")
    
    # Get tenant info
    print("\\n1. Getting organization tenant information...")
    response = make_request("GET", "/tenant/info", token)
    if response.status_code == 200:
        print("✅ Tenant info:", json.dumps(response.json(), indent=2))
    else:
        print("❌ Failed to get tenant info:", response.status_code, response.text)
        return
    
    # Create business account
    print("\\n2. Creating business account...")
    account_data = {
        "name": "Business Checking",
        "account_type": "business",
        "balance": 25000.00,
        "currency": "USD",
        "description": "Main business account"
    }
    
    response = make_request("POST", "/financial/accounts", token, account_data)
    if response.status_code == 201:
        account = response.json()
        print("✅ Created business account:", account["name"], f"(ID: {account['id']})")
        account_id = account["id"]
    else:
        print("❌ Failed to create account:", response.status_code, response.text)
        return
    
    # Create business transaction
    print("\\n3. Creating business transaction...")
    transaction_data = {
        "amount": 1200.00,
        "currency": "USD",
        "description": "Office rent payment",
        "transaction_type": "debit",
        "account_id": account_id,
        "category": "rent"
    }
    
    response = make_request("POST", "/financial/transactions", token, transaction_data)
    if response.status_code == 201:
        transaction = response.json()
        print("✅ Created transaction:", transaction["description"], f"(${transaction['amount']})")
    else:
        print("❌ Failed to create transaction:", response.status_code, response.text)
    
    # Create budget
    print("\\n4. Creating monthly budget...")
    budget_data = {
        "name": "Monthly Operating Budget",
        "total_amount": 10000.00,
        "currency": "USD",
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2025-01-31T23:59:59",
        "categories": "rent,utilities,supplies",
        "alert_threshold": 80.0,
        "alert_enabled": True
    }
    
    response = make_request("POST", "/financial/budgets", token, budget_data)
    if response.status_code == 201:
        budget = response.json()
        print("✅ Created budget:", budget["name"], f"(${budget['total_amount']})")
    else:
        print("❌ Failed to create budget:", response.status_code, response.text)
    
    # List organization data
    print("\\n5. Listing organization financial data...")
    
    # Accounts
    response = make_request("GET", "/financial/accounts", token)
    if response.status_code == 200:
        accounts = response.json()
        print(f"✅ Organization accounts ({len(accounts)}):")
        for acc in accounts:
            print(f"   - {acc['name']}: ${acc['balance']} ({acc['account_type']})")
    
    # Budgets
    response = make_request("GET", "/financial/budgets", token)
    if response.status_code == 200:
        budgets = response.json()
        print(f"✅ Organization budgets ({len(budgets)}):")
        for budget in budgets:
            print(f"   - {budget['name']}: ${budget['total_amount']} (spent: ${budget['spent_amount']})")

def demo_data_isolation():
    """Demonstrate data isolation between tenants."""
    print("\\n" + "="*50)
    print("DATA ISOLATION DEMONSTRATION")
    print("="*50)
    
    # Create tokens for different tenants
    user1_id = "550e8400-e29b-41d4-a716-446655440000"
    user2_id = "550e8400-e29b-41d4-a716-446655440001"
    org_id = "123"
    
    user1_token = create_jwt_token(user1_id, "user", user1_id)
    user2_token = create_jwt_token(user2_id, "user", user2_id)
    org_token = create_jwt_token(user1_id, "organization", org_id)
    
    print("Created tokens for:")
    print(f"  - User 1 (personal): {user1_id}")
    print(f"  - User 2 (personal): {user2_id}")
    print(f"  - Organization: {org_id}")
    
    print("\\nTesting data isolation...")
    
    # Each tenant should only see their own data
    tokens = [
        ("User 1", user1_token),
        ("User 2", user2_token), 
        ("Organization", org_token)
    ]
    
    for name, token in tokens:
        response = make_request("GET", "/financial/accounts", token)
        if response.status_code == 200:
            accounts = response.json()
            print(f"✅ {name} sees {len(accounts)} account(s)")
        else:
            print(f"❌ {name} failed to get accounts: {response.status_code}")

def main():
    """Run the multi-tenancy demonstration."""
    print("Financial Stronghold Multi-Tenancy Demo")
    print("=======================================")
    print("\\nThis demo requires the FastAPI server to be running on localhost:8000")
    print("Start it with: uvicorn app.main:app --reload")
    print("\\nNote: This demo uses mock data and may not work without a database setup.")
    
    try:
        # Test basic connectivity
        response = requests.get(f"{API_BASE}/health")
        if response.status_code != 200:
            print("❌ Server is not responding. Please start the FastAPI server first.")
            return
        print("✅ Server is running")
        
        # Run demonstrations
        demo_user_tenant()
        demo_organization_tenant()
        demo_data_isolation()
        
        print("\\n" + "="*50)
        print("DEMONSTRATION COMPLETE")
        print("="*50)
        print("\\nKey points demonstrated:")
        print("• User and organization tenants work independently")
        print("• Each tenant only sees their own data")
        print("• Role-based permissions (would require proper setup)")
        print("• Comprehensive financial operations")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Please start the FastAPI server first:")
        print("   uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")

if __name__ == "__main__":
    main()