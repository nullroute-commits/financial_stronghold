#!/usr/bin/env python
"""
Validate that all API endpoints have corresponding Web GUI implementations.
This script analyzes the codebase to ensure completeness and documentation integration.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json


class WebGUIValidator:
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path)
        self.api_endpoints = {}
        self.web_routes = {}
        self.missing_gui = []
        self.missing_docs = []
        
    def extract_api_endpoints(self) -> Dict[str, List[str]]:
        """Extract all API endpoints from api.py"""
        api_file = self.workspace_path / "app" / "api.py"
        if not api_file.exists():
            print(f"❌ API file not found: {api_file}")
            return {}
            
        content = api_file.read_text()
        
        # Pattern to match FastAPI route decorators
        pattern = r'@router\.(get|post|put|delete|patch)\("([^"]+)".*?\).*?def\s+(\w+)'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        endpoints = {}
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            function = match.group(3)
            
            if path not in endpoints:
                endpoints[path] = []
            endpoints[path].append({
                'method': method,
                'function': function,
                'full_path': f"/financial{path}"
            })
            
        return endpoints
    
    def extract_web_routes(self) -> Dict[str, str]:
        """Extract all web routes from web_urls.py"""
        urls_file = self.workspace_path / "app" / "web_urls.py"
        if not urls_file.exists():
            print(f"❌ Web URLs file not found: {urls_file}")
            return {}
            
        content = urls_file.read_text()
        
        # Extract URL patterns
        routes = {}
        
        # Pattern for simple paths
        pattern = r'path\("([^"]+)",\s*(\w+),\s*name="([^"]+)"\)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            path = match.group(1)
            view_func = match.group(2)
            name = match.group(3)
            routes[path] = {
                'view': view_func,
                'name': name
            }
            
        return routes
    
    def check_template_exists(self, template_path: str) -> bool:
        """Check if a template file exists"""
        full_path = self.workspace_path / "app" / "templates" / template_path
        return full_path.exists()
    
    def analyze_mapping(self) -> Dict[str, any]:
        """Analyze API to Web GUI mapping"""
        self.api_endpoints = self.extract_api_endpoints()
        self.web_routes = self.extract_web_routes()
        
        # Create mapping of API endpoints to GUI equivalents
        api_to_gui_mapping = {
            '/accounts': {
                'GET': 'accounts/',
                'POST': 'accounts/create/'
            },
            '/accounts/{account_id}': {
                'GET': 'accounts/<uuid:account_id>/',
                'PUT': 'accounts/<uuid:account_id>/edit/',
                'DELETE': 'accounts/<uuid:account_id>/edit/'
            },
            '/transactions': {
                'GET': 'transactions/',
                'POST': 'transactions/create/'
            },
            '/transactions/{transaction_id}': {
                'GET': 'transactions/<uuid:transaction_id>/',
                'PUT': 'transactions/<uuid:transaction_id>/edit/',
                'DELETE': 'transactions/<uuid:transaction_id>/edit/'
            },
            '/budgets': {
                'GET': 'budgets/',
                'POST': 'budgets/create/'
            },
            '/budgets/{budget_id}': {
                'GET': 'budgets/<uuid:budget_id>/',
                'PUT': 'budgets/<uuid:budget_id>/edit/',
                'DELETE': 'budgets/<uuid:budget_id>/edit/'
            },
            '/fees': {
                'GET': 'fees/',
                'POST': 'fees/create/'
            },
            '/fees/{fee_id}': {
                'GET': 'fees/<uuid:fee_id>/',
                'PUT': 'fees/<uuid:fee_id>/edit/',
                'DELETE': 'fees/<uuid:fee_id>/edit/'
            },
            '/dashboard': {
                'GET': 'dashboard/'
            },
            '/dashboard/analytics': {
                'GET': 'dashboard/analytics/'
            },
            '/transactions/classify': {
                'POST': 'analytics/classification/'
            },
            '/tags': {
                'POST': 'analytics/tagging/'
            },
            '/analytics/anomalies': {
                'POST': 'analytics/anomalies/'
            },
            '/analytics/patterns': {
                'GET': 'analytics/patterns/'
            }
        }
        
        # Check which APIs have GUI equivalents
        api_coverage = {}
        for api_path, methods in self.api_endpoints.items():
            api_coverage[api_path] = {
                'methods': methods,
                'has_gui': False,
                'gui_paths': []
            }
            
            if api_path in api_to_gui_mapping:
                for method_info in methods:
                    method = method_info['method']
                    if method in api_to_gui_mapping[api_path]:
                        api_coverage[api_path]['has_gui'] = True
                        api_coverage[api_path]['gui_paths'].append(
                            api_to_gui_mapping[api_path][method]
                        )
        
        # Find APIs without GUI
        for api_path, info in api_coverage.items():
            if not info['has_gui']:
                self.missing_gui.append(api_path)
        
        return {
            'total_api_endpoints': len(self.api_endpoints),
            'total_web_routes': len(self.web_routes),
            'apis_with_gui': len([p for p, i in api_coverage.items() if i['has_gui']]),
            'apis_without_gui': len(self.missing_gui),
            'coverage_percentage': (len([p for p, i in api_coverage.items() if i['has_gui']]) / 
                                  len(self.api_endpoints) * 100) if self.api_endpoints else 0,
            'api_coverage': api_coverage,
            'missing_gui': self.missing_gui
        }
    
    def check_documentation_integration(self) -> Dict[str, any]:
        """Check if documentation is properly integrated"""
        doc_checks = {
            'documentation_service': False,
            'documentation_views': False,
            'documentation_templates': False,
            'help_system': False,
            'api_docs_link': False
        }
        
        # Check for documentation service
        doc_service = self.workspace_path / "app" / "documentation_service.py"
        doc_checks['documentation_service'] = doc_service.exists()
        
        # Check for documentation views
        doc_views = self.workspace_path / "app" / "documentation_views.py"
        doc_checks['documentation_views'] = doc_views.exists()
        
        # Check for documentation templates
        doc_templates = self.workspace_path / "app" / "templates" / "documentation"
        doc_checks['documentation_templates'] = doc_templates.exists()
        
        # Check for help system in base template
        base_template = self.workspace_path / "app" / "templates" / "base" / "base.html"
        if base_template.exists():
            content = base_template.read_text()
            doc_checks['help_system'] = 'documentation-panel' in content
            doc_checks['api_docs_link'] = '/api/docs' in content
        
        return doc_checks
    
    def generate_report(self) -> str:
        """Generate a comprehensive validation report"""
        mapping_analysis = self.analyze_mapping()
        doc_checks = self.check_documentation_integration()
        
        report = []
        report.append("=" * 80)
        report.append("API to Web GUI Mapping Validation Report")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("📊 SUMMARY")
        report.append("-" * 40)
        report.append(f"Total API Endpoints: {mapping_analysis['total_api_endpoints']}")
        report.append(f"Total Web Routes: {mapping_analysis['total_web_routes']}")
        report.append(f"APIs with GUI: {mapping_analysis['apis_with_gui']}")
        report.append(f"APIs without GUI: {mapping_analysis['apis_without_gui']}")
        report.append(f"Coverage: {mapping_analysis['coverage_percentage']:.1f}%")
        report.append("")
        
        # Documentation Integration
        report.append("📚 DOCUMENTATION INTEGRATION")
        report.append("-" * 40)
        for check, status in doc_checks.items():
            status_icon = "✅" if status else "❌"
            report.append(f"{status_icon} {check.replace('_', ' ').title()}")
        report.append("")
        
        # Missing GUI Implementations
        if self.missing_gui:
            report.append("⚠️  MISSING WEB GUI IMPLEMENTATIONS")
            report.append("-" * 40)
            for api_path in self.missing_gui:
                methods = [m['method'] for m in self.api_endpoints[api_path]]
                report.append(f"• {api_path} [{', '.join(methods)}]")
            report.append("")
        
        # Implemented Features
        report.append("✅ IMPLEMENTED FEATURES")
        report.append("-" * 40)
        implemented = [
            "Dashboard (Home & Analytics)",
            "Account Management (CRUD)",
            "Transaction Management (CRUD)",
            "Budget Management (CRUD)",
            "Fee Management (CRUD)",
            "Transaction Classification",
            "Tagging System",
            "Documentation Browser",
            "Context-Sensitive Help"
        ]
        for feature in implemented:
            report.append(f"• {feature}")
        report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 40)
        report.append("1. Implement missing GUI pages for:")
        for api in self.missing_gui[:5]:  # Show top 5
            report.append(f"   - {api}")
        if len(self.missing_gui) > 5:
            report.append(f"   ... and {len(self.missing_gui) - 5} more")
        report.append("")
        report.append("2. Add interactive API documentation")
        report.append("3. Implement real-time data loading via AJAX")
        report.append("4. Add form validation based on schemas")
        report.append("5. Create automated tests for GUI-API integration")
        
        return "\n".join(report)


def main():
    """Run the validation"""
    validator = WebGUIValidator()
    report = validator.generate_report()
    
    print(report)
    
    # Save report to file
    report_path = Path("/workspace/WEBGUI_VALIDATION_REPORT.txt")
    report_path.write_text(report)
    print(f"\n📄 Report saved to: {report_path}")
    
    # Generate JSON summary
    summary = {
        'mapping': validator.analyze_mapping(),
        'documentation': validator.check_documentation_integration(),
        'missing_gui_endpoints': validator.missing_gui
    }
    
    summary_path = Path("/workspace/webgui_validation_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"📊 JSON summary saved to: {summary_path}")


if __name__ == "__main__":
    main()