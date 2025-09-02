#!/usr/bin/env python3
"""
Comprehensive Validation Script for Financial Stronghold
Validates API to Web GUI coverage and built-in documentation system
"""

import sys
import os
import re
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ComprehensiveValidator:
    """Comprehensive validation for API coverage and documentation system."""
    
    def __init__(self):
        self.api_coverage_results = {}
        self.documentation_results = {}
        self.web_gui_results = {}
        self.overall_score = 0
        
    def validate_api_coverage(self) -> Tuple[bool, Dict]:
        """Validate API to Web GUI coverage."""
        logger.info("Validating API to Web GUI coverage...")
        
        try:
            # Import and run the API coverage validator
            from validate_api_webgui_coverage import APICoverageValidator
            
            validator = APICoverageValidator()
            is_valid, stats = validator.validate_coverage()
            
            self.api_coverage_results = {
                'valid': is_valid,
                'coverage_percentage': stats['coverage_percentage'],
                'total_apis': stats['total_apis'],
                'covered_apis': stats['covered_apis'],
                'missing_coverage': len(stats['missing_coverage'])
            }
            
            logger.info(f"API coverage validation completed: {stats['coverage_percentage']:.1f}%")
            return is_valid, self.api_coverage_results
            
        except Exception as e:
            logger.error(f"Error in API coverage validation: {e}")
            self.api_coverage_results = {
                'valid': False,
                'error': str(e)
            }
            return False, self.api_coverage_results
    
    def validate_documentation_system(self) -> Tuple[bool, Dict]:
        """Validate the built-in documentation system."""
        logger.info("Validating built-in documentation system...")
        
        try:
            from app.documentation_service import DocumentationService
            
            ds = DocumentationService()
            
            # Check if documentation service loads
            if not ds:
                raise Exception("Documentation service failed to initialize")
            
            # Check feature documentation
            feature_docs = ds.get_feature_documentation()
            feature_count = len(feature_docs) if feature_docs else 0
            
            # Check code examples
            code_examples = ds.get_code_examples()
            example_count = len(code_examples) if code_examples else 0
            
            # Check comprehensive documentation
            comprehensive_docs = ds.get_comprehensive_documentation()
            has_comprehensive = bool(comprehensive_docs)
            
            # Check search functionality
            search_results = ds.search_documentation("account")
            search_working = len(search_results) > 0
            
            self.documentation_results = {
                'valid': True,
                'feature_docs_count': feature_count,
                'code_examples_count': example_count,
                'has_comprehensive_docs': has_comprehensive,
                'search_functionality': search_working,
                'total_documentation_items': feature_count + example_count
            }
            
            logger.info(f"Documentation system validation completed: {feature_count} features, {example_count} examples")
            return True, self.documentation_results
            
        except Exception as e:
            logger.error(f"Error in documentation system validation: {e}")
            self.documentation_results = {
                'valid': False,
                'error': str(e)
            }
            return False, self.documentation_results
    
    def validate_web_gui_documentation_views(self) -> Tuple[bool, Dict]:
        """Validate that web GUI has documentation views."""
        logger.info("Validating web GUI documentation views...")
        
        try:
            # Check if documentation views exist in web_views.py
            with open('app/web_views.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for documentation-related views
            doc_views = [
                'documentation_home',
                'documentation_features', 
                'documentation_api',
                'documentation_examples',
                'documentation_search',
                'documentation_feature_detail',
                'documentation_api_detail'
            ]
            
            found_views = []
            for view in doc_views:
                if f'def {view}(' in content:
                    found_views.append(view)
            
            # Check if documentation URLs exist in web_urls.py
            with open('app/web_urls.py', 'r', encoding='utf-8') as f:
                urls_content = f.read()
            
            # Look for documentation patterns and URLs
            doc_urls = [
                'docs/',  # Main docs path
                'features/',  # Features subpath
                'api/',  # API subpath
                'examples/',  # Examples subpath
                'search/'  # Search subpath
            ]
            
            found_urls = []
            for url in doc_urls:
                if url in urls_content:
                    found_urls.append(url)
            
            # Also check if documentation_patterns is defined
            has_documentation_patterns = 'documentation_patterns' in urls_content
            has_docs_include = 'path("docs/", include((documentation_patterns' in urls_content
            
            self.web_gui_results = {
                'valid': len(found_views) >= 5 and has_documentation_patterns,  # At least 5 documentation views and patterns
                'documentation_views_found': len(found_views),
                'documentation_views_total': len(doc_views),
                'documentation_urls_found': len(found_urls),
                'documentation_urls_total': len(doc_urls),
                'has_documentation_patterns': has_documentation_patterns,
                'has_docs_include': has_docs_include,
                'found_views': found_views,
                'found_urls': found_urls
            }
            
            logger.info(f"Web GUI documentation validation completed: {len(found_views)}/{len(doc_views)} views, {len(found_urls)}/{len(doc_urls)} URLs")
            return self.web_gui_results['valid'], self.web_gui_results
            
        except Exception as e:
            logger.error(f"Error in web GUI documentation validation: {e}")
            self.web_gui_results = {
                'valid': False,
                'error': str(e)
            }
            return False, self.web_gui_results
    
    def calculate_overall_score(self) -> int:
        """Calculate overall validation score."""
        score = 0
        
        # API coverage (40 points)
        if self.api_coverage_results.get('valid', False):
            coverage = self.api_coverage_results.get('coverage_percentage', 0)
            if coverage >= 100:
                score += 40
            elif coverage >= 95:
                score += 35
            elif coverage >= 90:
                score += 30
            elif coverage >= 80:
                score += 25
            else:
                score += 20
        
        # Documentation system (30 points)
        if self.documentation_results.get('valid', False):
            docs_score = 0
            if self.documentation_results.get('feature_docs_count', 0) >= 5:
                docs_score += 10
            if self.documentation_results.get('code_examples_count', 0) >= 3:
                docs_score += 10
            if self.documentation_results.get('has_comprehensive_docs', False):
                docs_score += 5
            if self.documentation_results.get('search_functionality', False):
                docs_score += 5
            score += docs_score
        
        # Web GUI documentation views (30 points)
        if self.web_gui_results.get('valid', False):
            views_score = 0
            views_ratio = self.web_gui_results.get('documentation_views_found', 0) / self.web_gui_results.get('documentation_views_total', 1)
            if views_ratio >= 0.8:
                views_score += 20
            elif views_ratio >= 0.6:
                views_score += 15
            elif views_ratio >= 0.4:
                views_score += 10
            else:
                views_score += 5
            
            urls_ratio = self.web_gui_results.get('documentation_urls_found', 0) / self.web_gui_results.get('documentation_urls_total', 1)
            if urls_ratio >= 0.8:
                views_score += 10
            elif urls_ratio >= 0.6:
                views_score += 8
            elif urls_ratio >= 0.4:
                views_score += 5
            else:
                views_score += 2
            
            score += views_score
        
        self.overall_score = score
        return score
    
    def generate_comprehensive_report(self) -> str:
        """Generate a comprehensive validation report."""
        report = []
        report.append("=" * 100)
        report.append("FINANCIAL STRONGHOLD - COMPREHENSIVE VALIDATION REPORT")
        report.append("=" * 100)
        report.append("")
        
        # Overall Score
        score = self.calculate_overall_score()
        report.append(f"🏆 OVERALL VALIDATION SCORE: {score}/100")
        report.append("")
        
        # API Coverage Results
        report.append("🔍 1. API TO WEB GUI COVERAGE VALIDATION")
        report.append("-" * 50)
        if self.api_coverage_results.get('valid', False):
            coverage = self.api_coverage_results.get('coverage_percentage', 0)
            report.append(f"✅ Status: PASSED")
            report.append(f"📊 Coverage: {coverage:.1f}%")
            report.append(f"🌐 Total APIs: {self.api_coverage_results.get('total_apis', 0)}")
            report.append(f"✅ Covered APIs: {self.api_coverage_results.get('covered_apis', 0)}")
            report.append(f"❌ Missing Coverage: {self.api_coverage_results.get('missing_coverage', 0)}")
        else:
            report.append(f"❌ Status: FAILED")
            if 'error' in self.api_coverage_results:
                report.append(f"🚨 Error: {self.api_coverage_results['error']}")
        report.append("")
        
        # Documentation System Results
        report.append("📚 2. BUILT-IN DOCUMENTATION SYSTEM VALIDATION")
        report.append("-" * 50)
        if self.documentation_results.get('valid', False):
            report.append(f"✅ Status: PASSED")
            report.append(f"📖 Feature Documentation: {self.documentation_results.get('feature_docs_count', 0)} items")
            report.append(f"💻 Code Examples: {self.documentation_results.get('code_examples_count', 0)} items")
            report.append(f"🔍 Search Functionality: {'✅ Working' if self.documentation_results.get('search_functionality', False) else '❌ Not Working'}")
            report.append(f"📋 Comprehensive Docs: {'✅ Available' if self.documentation_results.get('has_comprehensive_docs', False) else '❌ Not Available'}")
        else:
            report.append(f"❌ Status: FAILED")
            if 'error' in self.documentation_results:
                report.append(f"🚨 Error: {self.documentation_results['error']}")
        report.append("")
        
        # Web GUI Documentation Views Results
        report.append("🌐 3. WEB GUI DOCUMENTATION VIEWS VALIDATION")
        report.append("-" * 50)
        if self.web_gui_results.get('valid', False):
            report.append(f"✅ Status: PASSED")
            report.append(f"👁️ Documentation Views: {self.web_gui_results.get('documentation_views_found', 0)}/{self.web_gui_results.get('documentation_views_total', 0)}")
            report.append(f"🔗 Documentation URLs: {self.web_gui_results.get('documentation_urls_found', 0)}/{self.web_gui_results.get('documentation_urls_total', 0)}")
            report.append(f"📋 Documentation Patterns: {'✅ Defined' if self.web_gui_results.get('has_documentation_patterns', False) else '❌ Not Defined'}")
            report.append(f"🔗 Docs Include: {'✅ Configured' if self.web_gui_results.get('has_docs_include', False) else '❌ Not Configured'}")
            report.append(f"📱 Found Views: {', '.join(self.web_gui_results.get('found_views', []))}")
            report.append(f"🔗 Found URLs: {', '.join(self.web_gui_results.get('found_urls', []))}")
        else:
            report.append(f"❌ Status: FAILED")
            if 'error' in self.web_gui_results:
                report.append(f"🚨 Error: {self.web_gui_results['error']}")
        report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 50)
        if score >= 90:
            report.append("🎉 EXCELLENT! The system is production-ready with comprehensive coverage and documentation.")
        elif score >= 80:
            report.append("✅ GOOD! The system has good coverage and documentation, minor improvements needed.")
        elif score >= 70:
            report.append("⚠️ FAIR! The system has basic coverage and documentation, significant improvements needed.")
        else:
            report.append("❌ POOR! The system needs major improvements in coverage and documentation.")
        
        if score < 100:
            report.append("")
            report.append("🔧 Areas for improvement:")
            if self.api_coverage_results.get('coverage_percentage', 0) < 100:
                report.append("   - Complete API to Web GUI coverage")
            if not self.documentation_results.get('valid', False):
                report.append("   - Fix documentation system issues")
            if not self.web_gui_results.get('valid', False):
                report.append("   - Implement missing documentation views")
        
        report.append("")
        report.append("=" * 100)
        
        return "\n".join(report)
    
    def run_all_validations(self) -> Tuple[bool, Dict]:
        """Run all validation checks."""
        logger.info("Starting comprehensive validation...")
        
        # Run all validations
        api_valid, api_results = self.validate_api_coverage()
        docs_valid, docs_results = self.validate_documentation_system()
        gui_valid, gui_results = self.validate_web_gui_documentation_views()
        
        # Calculate overall score
        overall_score = self.calculate_overall_score()
        
        # Determine overall success (at least 80% score)
        overall_success = overall_score >= 80
        
        results = {
            'overall_success': overall_success,
            'overall_score': overall_score,
            'api_coverage': api_results,
            'documentation_system': docs_results,
            'web_gui_documentation': gui_results
        }
        
        return overall_success, results


def main():
    """Main validation function."""
    print("🔍 Financial Stronghold - Comprehensive Validation")
    print("=" * 100)
    
    validator = ComprehensiveValidator()
    
    try:
        # Run all validations
        print("Running comprehensive validation...")
        success, results = validator.run_all_validations()
        
        # Generate and display report
        report = validator.generate_comprehensive_report()
        print(report)
        
        # Return exit code based on validation result
        if success:
            print(f"\n🎉 VALIDATION PASSED: Overall score {results['overall_score']}/100")
            return 0
        else:
            print(f"\n⚠️ VALIDATION FAILED: Overall score {results['overall_score']}/100")
            return 1
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())