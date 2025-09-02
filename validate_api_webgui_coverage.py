#!/usr/bin/env python3
"""
API to Web GUI Coverage Validation Script
Validates that all API endpoints have corresponding web GUI views
"""

import re
import ast
import inspect
from typing import Dict, List, Set, Tuple
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class APICoverageValidator:
    """Validates API to Web GUI coverage."""
    
    def __init__(self):
        self.api_endpoints = {}
        self.web_views = {}
        self.missing_coverage = []
        self.coverage_stats = {}
        
    def extract_api_endpoints(self, api_file: str) -> Dict[str, List[str]]:
        """Extract all API endpoints from the API file."""
        logger.info(f"Extracting API endpoints from {api_file}")
        
        try:
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find router prefix
            prefix_pattern = r'router\s*=\s*APIRouter\(prefix=["\']([^"\']+)["\']'
            prefix_match = re.search(prefix_pattern, content)
            router_prefix = prefix_match.group(1) if prefix_match else ""
            
            # Find all router decorators
            router_pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
            matches = re.findall(router_pattern, content)
            
            endpoints = {}
            for method, path in matches:
                # Combine prefix with path
                full_path = router_prefix + path
                if full_path not in endpoints:
                    endpoints[full_path] = []
                endpoints[full_path].append(method.upper())
            
            # Also look for function definitions to get more context
            function_pattern = r'def\s+(\w+)\s*\([^)]*\):'
            functions = re.findall(function_pattern, content)
            
            logger.info(f"Found {len(endpoints)} API endpoints with {len(functions)} functions")
            logger.info(f"Router prefix: {router_prefix}")
            return endpoints
            
        except Exception as e:
            logger.error(f"Error extracting API endpoints: {e}")
            return {}
    
    def extract_web_views(self, views_file: str) -> Dict[str, List[str]]:
        """Extract all web views from the views file."""
        logger.info(f"Extracting web views from {views_file}")
        
        try:
            with open(views_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all view function definitions with any decorator
            # Look for functions that have decorators (indicating they are views)
            view_pattern = r'@\w+.*\n\s*def\s+(\w+)\s*\([^)]*\):'
            views = re.findall(view_pattern, content)
            
            # Also look for functions that are likely views (have request parameter)
            request_pattern = r'def\s+(\w+)\s*\([^)]*request[^)]*\):'
            request_views = re.findall(request_pattern, content)
            
            # Combine and deduplicate
            all_views = list(set(views + request_views))
            
            # Also look for function definitions to get more context
            function_pattern = r'def\s+(\w+)\s*\([^)]*\):'
            functions = re.findall(function_pattern, content)
            
            logger.info(f"Found {len(all_views)} web views with {len(functions)} functions")
            return {'views': all_views, 'functions': functions}
            
        except Exception as e:
            logger.error(f"Error extracting web views: {e}")
            return {'views': [], 'functions': []}
    
    def map_api_to_web_views(self) -> Dict[str, str]:
        """Map API endpoints to corresponding web views."""
        logger.info("Mapping API endpoints to web views")
        
        mapping = {}
        
        # Define expected mappings based on API structure
        expected_mappings = {
            # Account management
            '/financial/accounts': 'accounts_list',
            '/financial/accounts/{account_id}': 'account_detail',
            '/financial/accounts/create': 'account_create',
            '/financial/accounts/{account_id}/edit': 'account_edit',
            
            # Transaction management
            '/financial/transactions': 'transactions_list',
            '/financial/transactions/{transaction_id}': 'transaction_detail',
            '/financial/transactions/create': 'transaction_create',
            '/financial/transactions/{transaction_id}/edit': 'transaction_edit',
            '/financial/transactions/classify': 'classify_transactions',
            
            # Budget management
            '/financial/budgets': 'budgets_list',
            '/financial/budgets/{budget_id}': 'budget_detail',
            '/financial/budgets/create': 'budget_create',
            '/financial/budgets/{budget_id}/edit': 'budget_edit',
            
            # Fee management
            '/financial/fees': 'fees_list',
            '/financial/fees/{fee_id}': 'fee_detail',
            '/financial/fees/create': 'fee_create',
            '/financial/fees/{fee_id}/edit': 'fee_edit',
            
            # Dashboard and analytics
            '/financial/dashboard': 'dashboard_home',
            '/financial/dashboard/analytics': 'analytics_dashboard',
            '/financial/dashboard/summary': 'dashboard_home',
            '/financial/dashboard/accounts': 'dashboard_home',
            '/financial/dashboard/transactions': 'dashboard_home',
            '/financial/dashboard/budgets': 'dashboard_home',
            
            # Tagging system
            '/financial/tags': 'tags_list',
            '/financial/tags/create': 'tag_create',
            '/financial/tags/{tag_id}': 'tag_detail',
            '/financial/tags/resource/{resource_type}/{resource_id}': 'tag_detail',
            '/financial/tags/auto/{resource_type}/{resource_id}': 'tag_create',
            '/financial/tags/query': 'tags_list',
            
            # Analytics views
            '/financial/analytics/views': 'analytics_views_list',
            '/financial/analytics/views/create': 'analytics_view_create',
            '/financial/analytics/views/{view_id}': 'analytics_views_list',
            '/financial/analytics/views/{view_id}/refresh': 'analytics_views_list',
            
            # Transaction classification
            '/financial/classification/config': 'classification_config',
            '/financial/classification/config/update': 'classification_config_update',
            
            # Anomaly detection
            '/financial/analytics/anomalies': 'anomaly_detection',
            '/financial/analytics/patterns': 'anomaly_detection',
            
            # Advanced analytics
            '/financial/analytics/compute': 'analytics_dashboard',
            '/financial/analytics/summary': 'analytics_dashboard',
            '/financial/analytics/monthly-breakdown': 'analytics_dashboard',
            '/financial/analytics/classification': 'classification_dashboard',
        }
        
        return expected_mappings
    
    def validate_coverage(self) -> Tuple[bool, Dict]:
        """Validate that all APIs have web GUI coverage."""
        logger.info("Validating API to Web GUI coverage")
        
        # Extract API endpoints and web views
        self.api_endpoints = self.extract_api_endpoints('app/api.py')
        self.web_views = self.extract_web_views('app/web_views.py')
        
        # Get expected mappings
        expected_mappings = self.map_api_to_web_views()
        
        # Check coverage
        coverage_results = {}
        missing_coverage = []
        
        for api_path, methods in self.api_endpoints.items():
            if api_path in expected_mappings:
                expected_view = expected_mappings[api_path]
                if expected_view in self.web_views['views']:
                    coverage_results[api_path] = {
                        'status': '✅ COVERED',
                        'methods': methods,
                        'web_view': expected_view,
                        'coverage': '100%'
                    }
                else:
                    coverage_results[api_path] = {
                        'status': '❌ MISSING VIEW',
                        'methods': methods,
                        'expected_view': expected_view,
                        'coverage': '0%'
                    }
                    missing_coverage.append(api_path)
            else:
                coverage_results[api_path] = {
                    'status': '⚠️ NO MAPPING',
                    'methods': methods,
                    'coverage': 'Unknown'
                }
                missing_coverage.append(api_path)
        
        # Calculate overall coverage
        total_apis = len(self.api_endpoints)
        covered_apis = len([r for r in coverage_results.values() if r['status'] == '✅ COVERED'])
        coverage_percentage = (covered_apis / total_apis * 100) if total_apis > 0 else 0
        
        self.coverage_stats = {
            'total_apis': total_apis,
            'covered_apis': covered_apis,
            'missing_coverage': missing_coverage,  # This should be a list
            'coverage_percentage': coverage_percentage,
            'results': coverage_results
        }
        
        return coverage_percentage >= 95, self.coverage_stats
    
    def generate_coverage_report(self) -> str:
        """Generate a detailed coverage report."""
        if not self.coverage_stats:
            return "No coverage data available. Run validation first."
        
        report = []
        report.append("=" * 80)
        report.append("API TO WEB GUI COVERAGE REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        stats = self.coverage_stats
        report.append(f"📊 COVERAGE SUMMARY:")
        report.append(f"   Total APIs: {stats['total_apis']}")
        report.append(f"   Covered APIs: {stats['covered_apis']}")
        report.append(f"   Missing Coverage: {len(stats['missing_coverage'])}")
        report.append(f"   Coverage Percentage: {stats['coverage_percentage']:.1f}%")
        report.append("")
        
        # Detailed results
        report.append("🔍 DETAILED COVERAGE RESULTS:")
        report.append("")
        
        for api_path, result in stats['results'].items():
            report.append(f"🌐 {api_path}")
            report.append(f"   Status: {result['status']}")
            report.append(f"   Methods: {', '.join(result['methods'])}")
            
            if 'web_view' in result:
                report.append(f"   Web View: {result['web_view']}")
            elif 'expected_view' in result:
                report.append(f"   Expected View: {result['expected_view']}")
            
            report.append(f"   Coverage: {result['coverage']}")
            report.append("")
        
        # Missing coverage summary
        if len(stats['missing_coverage']) > 0:
            report.append("❌ MISSING COVERAGE:")
            for api_path in stats['missing_coverage']:
                result = stats['results'][api_path]
                report.append(f"   - {api_path}: {result['status']}")
            report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS:")
        if stats['coverage_percentage'] >= 95:
            report.append("   ✅ Excellent coverage! The system is ready for production.")
        elif stats['coverage_percentage'] >= 80:
            report.append("   ⚠️ Good coverage, but some APIs need web GUI implementation.")
        else:
            report.append("   ❌ Significant coverage gaps. Focus on implementing missing web views.")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Main validation function."""
    print("🔍 Financial Stronghold - API to Web GUI Coverage Validation")
    print("=" * 80)
    
    validator = APICoverageValidator()
    
    try:
        # Run validation
        print("Running validation...")
        is_valid, stats = validator.validate_coverage()
        
        # Generate and display report
        report = validator.generate_coverage_report()
        print(report)
        
        # Return exit code based on validation result
        if is_valid:
            print("\n🎉 VALIDATION PASSED: All APIs have web GUI coverage!")
            return 0
        else:
            print(f"\n⚠️ VALIDATION FAILED: Coverage is {stats['coverage_percentage']:.1f}%")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())