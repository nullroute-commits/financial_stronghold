"""
Documentation extraction and integration service.
Extracts documentation from code, schemas, and markdown files for web GUI integration.
"""

import ast
import inspect
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import markdown
from django.conf import settings
from django.core.cache import cache

from app.schemas import (
    AccountCreate, AccountRead, AccountUpdate,
    TransactionCreate, TransactionRead, TransactionUpdate,
    BudgetCreate, BudgetRead, BudgetUpdate,
    FeeCreate, FeeRead, FeeUpdate,
    DataTagCreate, DataTagRead,
    AnalyticsViewCreate, AnalyticsViewRead,
)


class DocumentationService:
    """Service for extracting and managing documentation from the codebase."""
    
    def __init__(self):
        self.base_path = Path(settings.BASE_DIR)
        self.cache_timeout = 3600  # 1 hour
        self.markdown_processor = markdown.Markdown(extensions=['extra', 'codehilite', 'toc'])
    
    def get_api_documentation(self, endpoint: str) -> Dict[str, Any]:
        """
        Get documentation for a specific API endpoint.
        
        Args:
            endpoint: API endpoint path (e.g., '/financial/accounts')
            
        Returns:
            Dictionary containing endpoint documentation
        """
        cache_key = f"api_doc_{endpoint}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Extract from API module
        from app import api
        
        doc_data = {
            'endpoint': endpoint,
            'methods': [],
            'description': '',
            'parameters': {},
            'responses': {},
            'examples': {}
        }
        
        # Parse the API module to find matching routes
        api_file = self.base_path / 'app' / 'api.py'
        if api_file.exists():
            content = api_file.read_text()
            # Find router decorators matching the endpoint
            pattern = rf'@router\.(get|post|put|delete|patch)\("{re.escape(endpoint)}[^"]*".*?\)'
            matches = re.finditer(pattern, content, re.DOTALL)
            
            for match in matches:
                method = match.group(1).upper()
                doc_data['methods'].append(method)
                
                # Extract function documentation
                func_pattern = rf'{match.group(0)}.*?def\s+(\w+)\(.*?\):\s*"""(.*?)"""'
                func_match = re.search(func_pattern, content[match.start():], re.DOTALL)
                if func_match:
                    doc_data['description'] = func_match.group(2).strip()
        
        cache.set(cache_key, doc_data, self.cache_timeout)
        return doc_data
    
    def get_schema_documentation(self, schema_name: str) -> Dict[str, Any]:
        """
        Get documentation for a Pydantic schema.
        
        Args:
            schema_name: Name of the schema class
            
        Returns:
            Dictionary containing schema documentation
        """
        cache_key = f"schema_doc_{schema_name}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        schema_map = {
            'AccountCreate': AccountCreate,
            'AccountRead': AccountRead,
            'AccountUpdate': AccountUpdate,
            'TransactionCreate': TransactionCreate,
            'TransactionRead': TransactionRead,
            'TransactionUpdate': TransactionUpdate,
            'BudgetCreate': BudgetCreate,
            'BudgetRead': BudgetRead,
            'BudgetUpdate': BudgetUpdate,
            'FeeCreate': FeeCreate,
            'FeeRead': FeeRead,
            'FeeUpdate': FeeUpdate,
            'DataTagCreate': DataTagCreate,
            'DataTagRead': DataTagRead,
            'AnalyticsViewCreate': AnalyticsViewCreate,
            'AnalyticsViewRead': AnalyticsViewRead,
        }
        
        schema_class = schema_map.get(schema_name)
        if not schema_class:
            return {}
        
        doc_data = {
            'name': schema_name,
            'description': schema_class.__doc__ or '',
            'fields': {}
        }
        
        # Extract field information from schema
        if hasattr(schema_class, '__fields__'):
            for field_name, field_info in schema_class.__fields__.items():
                doc_data['fields'][field_name] = {
                    'type': str(field_info.type_),
                    'required': field_info.required,
                    'description': field_info.field_info.description if hasattr(field_info.field_info, 'description') else '',
                    'default': field_info.default if field_info.default is not None else None
                }
        
        cache.set(cache_key, doc_data, self.cache_timeout)
        return doc_data
    
    def get_feature_documentation(self, feature: str) -> Dict[str, Any]:
        """
        Get documentation for a specific feature from markdown files.
        
        Args:
            feature: Feature name (e.g., 'tagging', 'multi-tenancy')
            
        Returns:
            Dictionary containing feature documentation
        """
        cache_key = f"feature_doc_{feature}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        feature_files = {
            'tagging': 'TAGGING_ANALYTICS_GUIDE.md',
            'multi-tenancy': 'MULTI_TENANCY.md',
            'testing': 'COMPREHENSIVE_TESTING_GUIDE.md',
            'deployment': 'DEPLOYMENT_PIPELINE.md',
            'architecture': 'ARCHITECTURE.md',
            'security': 'SECURITY_MODEL.md',
        }
        
        doc_file = feature_files.get(feature)
        if not doc_file:
            return {}
        
        file_path = self.base_path / doc_file
        if not file_path.exists():
            return {}
        
        content = file_path.read_text()
        html_content = self.markdown_processor.convert(content)
        
        # Extract sections
        sections = {}
        current_section = None
        for line in content.split('\n'):
            if line.startswith('## '):
                current_section = line[3:].strip()
                sections[current_section] = []
            elif current_section and line.strip():
                sections[current_section].append(line)
        
        doc_data = {
            'feature': feature,
            'title': content.split('\n')[0].replace('#', '').strip() if content else feature,
            'html': html_content,
            'sections': {k: '\n'.join(v) for k, v in sections.items()},
            'raw': content
        }
        
        cache.set(cache_key, doc_data, self.cache_timeout)
        return doc_data
    
    def get_context_help(self, page_type: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get context-sensitive help for a specific page type.
        
        Args:
            page_type: Type of page (e.g., 'dashboard', 'accounts_list', 'transaction_create')
            context: Additional context information
            
        Returns:
            Dictionary containing relevant help information
        """
        help_mapping = {
            'dashboard': {
                'title': 'Dashboard Help',
                'description': 'The dashboard provides an overview of your financial status.',
                'tips': [
                    'Click on any item to view details',
                    'Use the refresh button to update data',
                    'Hover over charts for detailed information',
                    'Export data using the export button'
                ],
                'related_docs': ['architecture', 'multi-tenancy']
            },
            'accounts_list': {
                'title': 'Accounts Management',
                'description': 'Manage all your financial accounts in one place.',
                'tips': [
                    'Click "Create Account" to add a new account',
                    'Use filters to find specific accounts',
                    'Click on an account name to view details',
                    'Edit or delete accounts from the detail page'
                ],
                'related_docs': ['multi-tenancy']
            },
            'transaction_create': {
                'title': 'Create Transaction',
                'description': 'Record a new financial transaction.',
                'tips': [
                    'Select the account for this transaction',
                    'Use negative amounts for expenses',
                    'Add tags for better categorization',
                    'Transactions are automatically classified'
                ],
                'related_docs': ['tagging']
            },
            'analytics': {
                'title': 'Analytics Dashboard',
                'description': 'Analyze your financial patterns and trends.',
                'tips': [
                    'Use date filters to focus on specific periods',
                    'Click on chart elements for details',
                    'Export charts as images or data',
                    'Create custom analytics views'
                ],
                'related_docs': ['tagging', 'architecture']
            }
        }
        
        base_help = help_mapping.get(page_type, {
            'title': 'Help',
            'description': 'Context-sensitive help for this page.',
            'tips': [],
            'related_docs': []
        })
        
        # Add API endpoint information
        api_endpoints = {
            'dashboard': ['/financial/dashboard', '/financial/dashboard/summary'],
            'accounts_list': ['/financial/accounts'],
            'transaction_create': ['/financial/transactions'],
            'analytics': ['/financial/analytics/summary', '/financial/analytics/views']
        }
        
        base_help['api_endpoints'] = api_endpoints.get(page_type, [])
        
        # Add schema information for forms
        schema_mapping = {
            'account_create': 'AccountCreate',
            'transaction_create': 'TransactionCreate',
            'budget_create': 'BudgetCreate',
            'fee_create': 'FeeCreate'
        }
        
        if page_type in schema_mapping:
            base_help['schema'] = self.get_schema_documentation(schema_mapping[page_type])
        
        return base_help
    
    def get_field_help(self, model_name: str, field_name: str) -> str:
        """
        Get help text for a specific model field.
        
        Args:
            model_name: Name of the model
            field_name: Name of the field
            
        Returns:
            Help text for the field
        """
        field_help = {
            'Account': {
                'name': 'A descriptive name for your account (e.g., "Main Checking", "Savings")',
                'account_type': 'Type of account: checking, savings, credit_card, or investment',
                'currency': 'Three-letter currency code (e.g., USD, EUR, GBP)',
                'initial_balance': 'Starting balance when the account was created',
                'is_active': 'Whether this account is currently active'
            },
            'Transaction': {
                'description': 'Brief description of the transaction',
                'amount': 'Transaction amount (negative for expenses, positive for income)',
                'category': 'Category for organizing transactions',
                'date': 'Date when the transaction occurred',
                'account_id': 'Account associated with this transaction'
            },
            'Budget': {
                'name': 'Name for your budget (e.g., "Monthly Groceries", "Entertainment")',
                'amount': 'Total amount allocated for this budget',
                'period': 'Budget period: monthly, quarterly, or yearly',
                'category': 'Category this budget applies to',
                'start_date': 'When this budget period starts',
                'end_date': 'When this budget period ends'
            },
            'Fee': {
                'name': 'Name of the fee (e.g., "Monthly Account Fee")',
                'amount': 'Fee amount',
                'frequency': 'How often the fee occurs: one_time, monthly, quarterly, or yearly',
                'account_id': 'Account this fee applies to'
            }
        }
        
        return field_help.get(model_name, {}).get(field_name, '')
    
    def search_documentation(self, query: str) -> List[Dict[str, Any]]:
        """
        Search across all documentation.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        results = []
        query_lower = query.lower()
        
        # Search in markdown files
        for md_file in self.base_path.glob('*.md'):
            if md_file.is_file():
                content = md_file.read_text().lower()
                if query_lower in content:
                    # Find context around the match
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if query_lower in line:
                            context = '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                            results.append({
                                'type': 'documentation',
                                'title': md_file.stem.replace('_', ' ').title(),
                                'file': md_file.name,
                                'context': context,
                                'url': f'/docs/{md_file.stem}'
                            })
                            break
        
        # Search in API endpoints
        api_file = self.base_path / 'app' / 'api.py'
        if api_file.exists():
            content = api_file.read_text()
            if query_lower in content.lower():
                # Find relevant endpoints
                pattern = r'@router\.\w+\("([^"]+)".*?\).*?def\s+(\w+)'
                matches = re.finditer(pattern, content, re.DOTALL)
                for match in matches:
                    if query_lower in match.group(0).lower():
                        results.append({
                            'type': 'api',
                            'title': f'API: {match.group(1)}',
                            'endpoint': match.group(1),
                            'function': match.group(2),
                            'url': f'/api/docs#{match.group(1)}'
                        })
        
        return results[:10]  # Limit to 10 results


# Singleton instance
documentation_service = DocumentationService()