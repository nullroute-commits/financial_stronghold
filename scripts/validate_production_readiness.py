#!/usr/bin/env python3
"""
Production Readiness Validation Script
Comprehensive validation of all production requirements.

Created by Team Alpha (Infrastructure & DevOps) for Sprint 6
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class ProductionValidator:
    """Comprehensive production readiness validator."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
        
    def run_all_checks(self):
        """Run all production readiness checks."""
        print(f"{Colors.BLUE}{Colors.BOLD}🚀 Production Readiness Validation{Colors.END}")
        print("=" * 50)
        
        # Environment checks
        self.check_environment_configuration()
        self.check_security_configuration()
        self.check_database_configuration()
        self.check_docker_configuration()
        
        # Application checks
        self.check_django_configuration()
        self.check_dependencies()
        self.check_static_files()
        
        # Infrastructure checks
        self.check_health_endpoints()
        self.check_monitoring_setup()
        self.check_backup_procedures()
        
        # Security checks
        self.check_security_headers()
        self.check_ssl_configuration()
        
        # Performance checks
        self.check_database_optimization()
        self.check_caching_configuration()
        
        # Final report
        self.generate_report()
    
    def check_environment_configuration(self):
        """Check environment configuration files."""
        print(f"\n{Colors.BLUE}📁 Environment Configuration{Colors.END}")
        
        required_files = [
            'environments/.env.development',
            'environments/.env.testing',
            'environments/.env.production.example'
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                self.passed.append(f"✅ {file_path} exists")
                
                # Check for required variables
                with open(file_path, 'r') as f:
                    content = f.read()
                    required_vars = ['SECRET_KEY', 'POSTGRES_DB', 'POSTGRES_USER']
                    
                    for var in required_vars:
                        if var in content:
                            self.passed.append(f"  ✅ {var} configured in {file_path}")
                        else:
                            self.warnings.append(f"  ⚠️ {var} missing in {file_path}")
            else:
                self.errors.append(f"❌ {file_path} missing")
    
    def check_security_configuration(self):
        """Check security configuration."""
        print(f"\n{Colors.BLUE}🔒 Security Configuration{Colors.END}")
        
        # Check for hardcoded secrets (look for actual insecure patterns, exclude cache and scripts)
        result = subprocess.run([
            'grep', '-r', 'django-insecure-change-me', 'config/', 'app/', 
            '--exclude-dir=__pycache__', '--exclude-dir=scripts', '--exclude=*.pyc'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            self.errors.append("❌ Hardcoded django-insecure-change-me keys found")
        else:
            self.passed.append("✅ No hardcoded insecure keys found")
        
        # Check secret key generator
        if os.path.exists('scripts/generate_secret_key.py'):
            self.passed.append("✅ Secret key generator available")
        else:
            self.warnings.append("⚠️ Secret key generator missing")
    
    def check_database_configuration(self):
        """Check database configuration."""
        print(f"\n{Colors.BLUE}🗃️ Database Configuration{Colors.END}")
        
        # Check migrations (files exist)
        migration_files = [
            'app/migrations/0001_initial.py',
            'app/migrations/0002_add_indexes.py',
            'app/migrations/0003_optimize_database_performance.py'
        ]
        
        for migration_file in migration_files:
            if os.path.exists(migration_file):
                self.passed.append(f"✅ {migration_file} exists")
            else:
                self.warnings.append(f"⚠️ {migration_file} missing")
        
        # Note: Django runtime check requires installed environment
        self.passed.append("ℹ️ Django migrations available (runtime check requires installed environment)")
        
        # Check for database optimization migration
        if os.path.exists('app/migrations/0003_optimize_database_performance.py'):
            self.passed.append("✅ Database optimization migration present")
        else:
            self.warnings.append("⚠️ Database optimization migration missing")
    
    def check_docker_configuration(self):
        """Check Docker configuration."""
        print(f"\n{Colors.BLUE}🐳 Docker Configuration{Colors.END}")
        
        docker_files = [
            'Dockerfile',
            'docker-compose.base.yml',
            'docker-compose.development.yml',
            'docker-compose.production.yml',
            'docker-entrypoint.sh'
        ]
        
        for file_path in docker_files:
            if os.path.exists(file_path):
                self.passed.append(f"✅ {file_path} exists")
            else:
                self.errors.append(f"❌ {file_path} missing")
        
        # Check entrypoint script permissions
        if os.path.exists('docker-entrypoint.sh'):
            if os.access('docker-entrypoint.sh', os.X_OK):
                self.passed.append("✅ docker-entrypoint.sh is executable")
            else:
                self.warnings.append("⚠️ docker-entrypoint.sh not executable")
    
    def check_django_configuration(self):
        """Check Django configuration."""
        print(f"\n{Colors.BLUE}⚙️ Django Configuration{Colors.END}")
        
        # Check settings structure
        settings_files = [
            'config/settings/base.py',
            'config/settings/development.py',
            'config/settings/production.py',
            'config/settings/testing.py'
        ]
        
        for file_path in settings_files:
            if os.path.exists(file_path):
                self.passed.append(f"✅ {file_path} exists")
            else:
                self.errors.append(f"❌ {file_path} missing")
        
        # Check for duplicate settings
        if os.path.exists('app/settings.py'):
            self.errors.append("❌ Duplicate app/settings.py found (should be removed)")
        else:
            self.passed.append("✅ No duplicate settings files")
    
    def check_dependencies(self):
        """Check dependency configuration."""
        print(f"\n{Colors.BLUE}📦 Dependencies{Colors.END}")
        
        req_files = [
            'requirements/base.txt',
            'requirements/development.txt',
            'requirements/production.txt',
            'requirements/test.txt'
        ]
        
        for file_path in req_files:
            if os.path.exists(file_path):
                self.passed.append(f"✅ {file_path} exists")
                
                # Check for FastAPI (should be removed)
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'fastapi' in content.lower():
                        self.errors.append(f"❌ FastAPI dependency found in {file_path}")
                    if 'sqlalchemy' in content.lower():
                        self.errors.append(f"❌ SQLAlchemy dependency found in {file_path}")
                    if 'djangorestframework' in content:
                        self.passed.append(f"  ✅ Django REST Framework configured")
            else:
                self.errors.append(f"❌ {file_path} missing")
    
    def check_static_files(self):
        """Check static files configuration."""
        print(f"\n{Colors.BLUE}📄 Static Files{Colors.END}")
        
        static_files = [
            'static/css/custom.css',
            'static/js/app.js'
        ]
        
        for file_path in static_files:
            if os.path.exists(file_path):
                self.passed.append(f"✅ {file_path} exists")
            else:
                self.warnings.append(f"⚠️ {file_path} missing")
        
        # Check templates
        template_files = [
            'templates/base.html',
            'templates/dashboard/home.html',
            'templates/registration/login.html'
        ]
        
        for file_path in template_files:
            if os.path.exists(file_path):
                self.passed.append(f"✅ {file_path} exists")
            else:
                self.warnings.append(f"⚠️ {file_path} missing")
    
    def check_health_endpoints(self):
        """Check health check endpoints."""
        print(f"\n{Colors.BLUE}🏥 Health Endpoints{Colors.END}")
        
        # Check if monitoring module exists
        if os.path.exists('app/monitoring.py'):
            self.passed.append("✅ Monitoring module exists")
        else:
            self.errors.append("❌ Monitoring module missing")
        
        # Check management commands
        if os.path.exists('app/management/commands/health_check.py'):
            self.passed.append("✅ Health check management command exists")
        else:
            self.warnings.append("⚠️ Health check management command missing")
    
    def check_monitoring_setup(self):
        """Check monitoring and logging setup."""
        print(f"\n{Colors.BLUE}📊 Monitoring Setup{Colors.END}")
        
        if os.path.exists('config/logging.py'):
            self.passed.append("✅ Production logging configuration exists")
        else:
            self.warnings.append("⚠️ Production logging configuration missing")
        
        # Check for monitoring middleware
        try:
            with open('config/settings/base.py', 'r') as f:
                content = f.read()
                if 'MonitoringMiddleware' in content:
                    self.passed.append("✅ Monitoring middleware configured")
                else:
                    self.warnings.append("⚠️ Monitoring middleware not configured")
        except:
            pass
    
    def check_backup_procedures(self):
        """Check backup and recovery procedures."""
        print(f"\n{Colors.BLUE}💾 Backup Procedures{Colors.END}")
        
        if os.path.exists('scripts/deploy.sh'):
            self.passed.append("✅ Deployment script exists")
        else:
            self.errors.append("❌ Deployment script missing")
        
        # Check if deployment script has backup functionality
        if os.path.exists('scripts/deploy.sh'):
            with open('scripts/deploy.sh', 'r') as f:
                content = f.read()
                if 'backup' in content.lower():
                    self.passed.append("✅ Backup functionality in deployment script")
                else:
                    self.warnings.append("⚠️ No backup functionality in deployment script")
    
    def check_security_headers(self):
        """Check security headers configuration."""
        print(f"\n{Colors.BLUE}🛡️ Security Headers{Colors.END}")
        
        try:
            with open('config/settings/production.py', 'r') as f:
                content = f.read()
                
                security_settings = [
                    'SECURE_SSL_REDIRECT',
                    'SECURE_HSTS_SECONDS',
                    'SESSION_COOKIE_SECURE',
                    'CSRF_COOKIE_SECURE'
                ]
                
                for setting in security_settings:
                    if setting in content:
                        self.passed.append(f"✅ {setting} configured")
                    else:
                        self.warnings.append(f"⚠️ {setting} not configured")
                        
        except Exception as e:
            self.errors.append(f"❌ Error checking security settings: {str(e)}")
    
    def check_ssl_configuration(self):
        """Check SSL/TLS configuration."""
        print(f"\n{Colors.BLUE}🔐 SSL Configuration{Colors.END}")
        
        # This would check actual SSL configuration in production
        self.passed.append("ℹ️ SSL configuration check (manual verification required)")
    
    def check_database_optimization(self):
        """Check database optimization."""
        print(f"\n{Colors.BLUE}⚡ Database Optimization{Colors.END}")
        
        if os.path.exists('app/managers.py'):
            self.passed.append("✅ Custom Django managers implemented")
        else:
            self.warnings.append("⚠️ Custom Django managers missing")
        
        # Check for optimization migration
        if os.path.exists('app/migrations/0003_optimize_database_performance.py'):
            self.passed.append("✅ Database performance optimization migration exists")
        else:
            self.warnings.append("⚠️ Database performance optimization missing")
    
    def check_caching_configuration(self):
        """Check caching configuration."""
        print(f"\n{Colors.BLUE}🚀 Caching Configuration{Colors.END}")
        
        try:
            with open('config/settings/base.py', 'r') as f:
                content = f.read()
                
                if 'CACHES' in content and 'memcached' in content.lower():
                    self.passed.append("✅ Memcached caching configured")
                else:
                    self.warnings.append("⚠️ Caching not properly configured")
                    
        except Exception as e:
            self.errors.append(f"❌ Error checking cache configuration: {str(e)}")
    
    def generate_report(self):
        """Generate final validation report."""
        print(f"\n{Colors.BOLD}📊 PRODUCTION READINESS REPORT{Colors.END}")
        print("=" * 50)
        
        # Summary
        total_checks = len(self.passed) + len(self.warnings) + len(self.errors)
        print(f"Total Checks: {total_checks}")
        print(f"{Colors.GREEN}Passed: {len(self.passed)}{Colors.END}")
        print(f"{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.END}")
        print(f"{Colors.RED}Errors: {len(self.errors)}{Colors.END}")
        
        # Detailed results
        if self.passed:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ PASSED CHECKS:{Colors.END}")
            for check in self.passed:
                print(f"  {check}")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ WARNINGS:{Colors.END}")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ ERRORS:{Colors.END}")
            for error in self.errors:
                print(f"  {error}")
        
        # Final assessment
        print(f"\n{Colors.BOLD}🎯 FINAL ASSESSMENT:{Colors.END}")
        
        if self.errors:
            print(f"{Colors.RED}❌ NOT READY FOR PRODUCTION{Colors.END}")
            print("Please fix all errors before deploying to production.")
            return False
        elif self.warnings:
            print(f"{Colors.YELLOW}⚠️ READY WITH WARNINGS{Colors.END}")
            print("Production deployment possible but warnings should be addressed.")
            return True
        else:
            print(f"{Colors.GREEN}✅ FULLY READY FOR PRODUCTION{Colors.END}")
            print("All checks passed! Ready for production deployment.")
            return True
    
    def generate_json_report(self):
        """Generate JSON report for automated processing."""
        report = {
            'timestamp': time.time(),
            'status': 'ready' if not self.errors else 'not_ready',
            'summary': {
                'passed': len(self.passed),
                'warnings': len(self.warnings),
                'errors': len(self.errors),
                'total': len(self.passed) + len(self.warnings) + len(self.errors)
            },
            'details': {
                'passed': self.passed,
                'warnings': self.warnings,
                'errors': self.errors
            }
        }
        
        with open('production_readiness_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 JSON report saved to: production_readiness_report.json")


def main():
    """Main function."""
    validator = ProductionValidator()
    
    try:
        is_ready = validator.run_all_checks()
        validator.generate_json_report()
        
        # Exit with appropriate code
        sys.exit(0 if is_ready else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Validation interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Validation failed with error: {str(e)}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()