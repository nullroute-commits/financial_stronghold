"""
Documentation Service for Financial Stronghold Web GUI
Provides comprehensive documentation extracted from the codebase and API specifications.
"""

import inspect
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DocumentationService:
    """Service for generating comprehensive documentation from the codebase."""

    def __init__(self):
        """Initialize the documentation service."""
        self.api_docs = {}
        self.feature_docs = {}
        self.code_examples = {}
        self._load_documentation()

    def _load_documentation(self):
        """Load and parse documentation from various sources."""
        self._load_api_documentation()
        self._load_feature_documentation()
        self._load_code_examples()

    def _load_api_documentation(self):
        """Load API documentation from the API module."""
        try:
            from app.api import router
            
            # Extract route information
            for route in router.routes:
                if hasattr(route, 'endpoint'):
                    endpoint = route.endpoint
                    if hasattr(endpoint, '__doc__') and endpoint.__doc__:
                        # Extract endpoint information
                        path = route.path
                        methods = [method for method in ['GET', 'POST', 'PUT', 'DELETE'] 
                                 if hasattr(route, method.lower())]
                        
                        # Parse docstring for parameters and responses
                        doc = endpoint.__doc__.strip()
                        params = self._extract_parameters(doc)
                        responses = self._extract_responses(doc)
                        
                        self.api_docs[path] = {
                            'path': path,
                            'methods': methods,
                            'description': doc,
                            'parameters': params,
                            'responses': responses,
                            'endpoint_name': endpoint.__name__,
                            'tags': getattr(route, 'tags', []),
                        }
        except Exception as e:
            logger.error(f"Error loading API documentation: {str(e)}")
            self.api_docs = {}

    def _load_feature_documentation(self):
        """Load feature documentation from markdown files and codebase."""
        self.feature_docs = {
            'accounts': {
                'title': 'Account Management',
                'description': 'Manage financial accounts with balance tracking and categorization',
                'features': [
                    'Create and manage multiple account types',
                    'Track account balances and transactions',
                    'Categorize accounts by type and purpose',
                    'Monitor account status and activity'
                ],
                'api_endpoints': [
                    'POST /financial/accounts - Create account',
                    'GET /financial/accounts - List accounts',
                    'GET /financial/accounts/{id} - Get account details',
                    'PUT /financial/accounts/{id} - Update account',
                    'DELETE /financial/accounts/{id} - Delete account'
                ]
            },
            'transactions': {
                'title': 'Transaction Management',
                'description': 'Track and manage financial transactions with automatic classification',
                'features': [
                    'Record income and expenses',
                    'Automatic transaction classification',
                    'Category-based organization',
                    'Transfer between accounts',
                    'Transaction history and reporting'
                ],
                'api_endpoints': [
                    'POST /financial/transactions - Create transaction',
                    'GET /financial/transactions - List transactions',
                    'GET /financial/transactions/{id} - Get transaction details',
                    'PUT /financial/transactions/{id} - Update transaction',
                    'DELETE /financial/transactions/{id} - Delete transaction',
                    'POST /financial/transactions/classify - Classify transactions'
                ]
            },
            'budgets': {
                'title': 'Budget Management',
                'description': 'Create and track budgets with spending analysis',
                'features': [
                    'Set budget limits by category',
                    'Track spending against budgets',
                    'Budget utilization analytics',
                    'Budget alerts and notifications'
                ],
                'api_endpoints': [
                    'POST /financial/budgets - Create budget',
                    'GET /financial/budgets - List budgets',
                    'GET /financial/budgets/{id} - Get budget details',
                    'PUT /financial/budgets/{id} - Update budget',
                    'DELETE /financial/budgets/{id} - Delete budget'
                ]
            },
            'fees': {
                'title': 'Fee Management',
                'description': 'Manage recurring fees and charges',
                'features': [
                    'Track recurring fees and charges',
                    'Fee categorization and scheduling',
                    'Due date management',
                    'Fee history and reporting'
                ],
                'api_endpoints': [
                    'POST /financial/fees - Create fee',
                    'GET /financial/fees - List fees',
                    'GET /financial/fees/{id} - Get fee details',
                    'PUT /financial/fees/{id} - Update fee',
                    'DELETE /financial/fees/{id} - Delete fee'
                ]
            },
            'tagging': {
                'title': 'Data Tagging System',
                'description': 'Organize and categorize data with flexible tagging',
                'features': [
                    'Flexible tag creation and management',
                    'Resource-based tagging',
                    'Tag-based queries and filtering',
                    'Metadata and label support'
                ],
                'api_endpoints': [
                    'POST /financial/tags - Create tag',
                    'GET /financial/tags/resource/{type}/{id} - Get resource tags',
                    'POST /financial/tags/auto/{type}/{id} - Auto-tag resource',
                    'POST /financial/tags/query - Query by tags'
                ]
            },
            'analytics': {
                'title': 'Analytics and Reporting',
                'description': 'Comprehensive financial analytics and insights',
                'features': [
                    'Financial performance metrics',
                    'Spending pattern analysis',
                    'Budget utilization tracking',
                    'Custom analytics views',
                    'Monthly breakdowns and trends'
                ],
                'api_endpoints': [
                    'GET /financial/dashboard - Complete dashboard data',
                    'GET /financial/dashboard/summary - Financial summary',
                    'GET /financial/dashboard/accounts - Account summaries',
                    'GET /financial/dashboard/transactions - Transaction summary',
                    'GET /financial/dashboard/budgets - Budget statuses',
                    'POST /financial/analytics/compute - Compute metrics',
                    'POST /financial/analytics/summary - Analytics summary',
                    'GET /financial/analytics/monthly-breakdown - Monthly analysis'
                ]
            },
            'classification': {
                'title': 'Transaction Classification',
                'description': 'Automatic transaction classification and categorization',
                'features': [
                    'Pattern-based classification',
                    'Automatic category assignment',
                    'Custom classification rules',
                    'Classification analytics'
                ],
                'api_endpoints': [
                    'POST /financial/transactions/classify - Classify transactions',
                    'POST /financial/analytics/classification - Classification analytics',
                    'GET /financial/classification/config - Get configuration',
                    'POST /financial/classification/config - Update configuration'
                ]
            },
            'anomaly_detection': {
                'title': 'Anomaly Detection',
                'description': 'Detect unusual patterns in financial transactions',
                'features': [
                    'Transaction pattern analysis',
                    'Anomaly scoring and detection',
                    'Configurable sensitivity levels',
                    'Anomaly reporting and alerts'
                ],
                'api_endpoints': [
                    'POST /financial/analytics/anomalies - Detect anomalies',
                    'GET /financial/analytics/patterns - Transaction patterns'
                ]
            }
        }

    def _load_code_examples(self):
        """Load code examples for common operations."""
        self.code_examples = {
            'create_account': {
                'title': 'Create a New Account',
                'description': 'Example of creating a new financial account',
                'python': '''
from app.schemas import AccountCreate
from app.services import TenantService

# Create account data
account_data = AccountCreate(
    name="Savings Account",
    account_type="savings",
    balance=1000.00,
    currency="USD",
    description="Primary savings account"
)

# Create the account
service = TenantService(db=db, model=Account)
account = service.create(
    account_data, 
    tenant_type="user", 
    tenant_id=user_id
)
                ''',
                'javascript': '''
// Using the FinancialAPI class
const accountData = {
    name: "Savings Account",
    account_type: "savings",
    balance: 1000.00,
    currency: "USD",
    description: "Primary savings account"
};

const account = await FinancialAPI.createAccount(accountData);
                ''',
                'curl': '''
curl -X POST "http://localhost:8000/financial/accounts" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{
    "name": "Savings Account",
    "account_type": "savings",
    "balance": 1000.00,
    "currency": "USD",
    "description": "Primary savings account"
  }'
                '''
            },
            'create_transaction': {
                'title': 'Create a New Transaction',
                'description': 'Example of creating a new financial transaction',
                'python': '''
from app.schemas import TransactionCreate

# Create transaction data
transaction_data = TransactionCreate(
    account_id=account_id,
    amount=50.00,
    currency="USD",
    description="Grocery shopping",
    transaction_type="expense",
    category="food"
)

# Create the transaction
service = TenantService(db=db, model=Transaction)
transaction = service.create(
    transaction_data, 
    tenant_type="user", 
    tenant_id=user_id
)
                ''',
                'javascript': '''
const transactionData = {
    account_id: accountId,
    amount: 50.00,
    currency: "USD",
    description: "Grocery shopping",
    transaction_type: "expense",
    category: "food"
};

const transaction = await FinancialAPI.createTransaction(transactionData);
                ''',
                'curl': '''
curl -X POST "http://localhost:8000/financial/transactions" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{
    "account_id": "ACCOUNT_UUID",
    "amount": 50.00,
    "currency": "USD",
    "description": "Grocery shopping",
    "transaction_type": "expense",
    "category": "food"
  }'
                '''
            },
            'dashboard_data': {
                'title': 'Get Dashboard Data',
                'description': 'Example of retrieving dashboard data',
                'python': '''
from app.dashboard_service import DashboardService

# Get dashboard service
dashboard_service = DashboardService(db=db)

# Get complete dashboard data
dashboard_data = dashboard_service.get_complete_dashboard_data(
    tenant_type="user",
    tenant_id=user_id
)

# Access specific data
financial_summary = dashboard_data.financial_summary
account_summaries = dashboard_data.account_summaries
transaction_summary = dashboard_data.transaction_summary
                ''',
                'javascript': '''
// Get dashboard data
const dashboardData = await FinancialAPI.getDashboardData();

// Access specific data
const financialSummary = dashboardData.financial_summary;
const accountSummaries = dashboardData.account_summaries;
const transactionSummary = dashboardData.transaction_summary;
                ''',
                'curl': '''
curl -X GET "http://localhost:8000/financial/dashboard" \\
  -H "Authorization: Bearer YOUR_TOKEN"
                '''
            }
        }

    def _extract_parameters(self, doc: str) -> List[Dict[str, str]]:
        """Extract parameters from docstring."""
        params = []
        # Simple parameter extraction - can be enhanced
        param_pattern = r'(\w+):\s*([^,\n]+)'
        matches = re.findall(param_pattern, doc)
        for param_name, param_desc in matches:
            params.append({
                'name': param_name,
                'description': param_desc.strip(),
                'type': 'string'  # Default type
            })
        return params

    def _extract_responses(self, doc: str) -> List[Dict[str, str]]:
        """Extract response information from docstring."""
        responses = []
        # Look for response patterns in docstring
        if 'response_model' in doc:
            response_match = re.search(r'response_model=(\w+)', doc)
            if response_match:
                responses.append({
                    'type': response_match.group(1),
                    'description': 'Success response'
                })
        return responses

    def get_api_documentation(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Get API documentation for a specific path or all APIs."""
        if path:
            return self.api_docs.get(path, {})
        return self.api_docs

    def get_feature_documentation(self, feature: Optional[str] = None) -> Dict[str, Any]:
        """Get feature documentation for a specific feature or all features."""
        if feature:
            return self.feature_docs.get(feature, {})
        return self.feature_docs

    def get_code_examples(self, example: Optional[str] = None) -> Dict[str, Any]:
        """Get code examples for a specific operation or all examples."""
        if example:
            return self.code_examples.get(example, {})
        return self.code_examples

    def get_comprehensive_documentation(self) -> Dict[str, Any]:
        """Get comprehensive documentation for the entire system."""
        return {
            'system_overview': {
                'title': 'Financial Stronghold System',
                'description': 'A comprehensive financial management system with multi-tenancy support',
                'version': '1.0.0',
                'last_updated': datetime.now().isoformat(),
                'features': list(self.feature_docs.keys()),
                'total_apis': len(self.api_docs),
                'total_examples': len(self.code_examples)
            },
            'api_documentation': self.api_docs,
            'feature_documentation': self.feature_docs,
            'code_examples': self.code_examples,
            'quick_start': {
                'title': 'Quick Start Guide',
                'steps': [
                    '1. Set up your development environment',
                    '2. Configure your database and services',
                    '3. Create your first account',
                    '4. Add your first transaction',
                    '5. Explore the dashboard and analytics'
                ]
            },
            'architecture': {
                'title': 'System Architecture',
                'components': [
                    'Django 5.1.3 Web Framework',
                    'FastAPI for REST API',
                    'PostgreSQL 17.2 Database',
                    'SQLAlchemy ORM',
                    'Memcached Caching',
                    'RabbitMQ Message Queue',
                    'Multi-tenant Architecture',
                    'RBAC Security System'
                ]
            }
        }

    def search_documentation(self, query: str) -> List[Dict[str, Any]]:
        """Search documentation for specific terms."""
        results = []
        query_lower = query.lower()
        
        # Search in API docs
        for path, api_doc in self.api_docs.items():
            if (query_lower in path.lower() or 
                query_lower in api_doc.get('description', '').lower() or
                query_lower in api_doc.get('endpoint_name', '').lower()):
                results.append({
                    'type': 'api',
                    'title': f"API: {api_doc.get('endpoint_name', 'Unknown')}",
                    'description': api_doc.get('description', ''),
                    'path': path,
                    'relevance': 'high'
                })
        
        # Search in feature docs
        for feature, feature_doc in self.feature_docs.items():
            if (query_lower in feature.lower() or
                query_lower in feature_doc.get('title', '').lower() or
                query_lower in feature_doc.get('description', '').lower()):
                results.append({
                    'type': 'feature',
                    'title': feature_doc.get('title', ''),
                    'description': feature_doc.get('description', ''),
                    'feature': feature,
                    'relevance': 'high'
                })
        
        # Search in code examples
        for example, example_doc in self.code_examples.items():
            if (query_lower in example.lower() or
                query_lower in example_doc.get('title', '').lower() or
                query_lower in example_doc.get('description', '').lower()):
                results.append({
                    'type': 'example',
                    'title': example_doc.get('title', ''),
                    'description': example_doc.get('description', ''),
                    'example': example,
                    'relevance': 'medium'
                })
        
        return results[:20]  # Limit results