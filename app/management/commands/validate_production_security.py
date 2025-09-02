"""
Django management command for production security validation.
Comprehensive validation of all production security requirements.

Created based on penetration test findings and security analysis.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import re
import sys


class Command(BaseCommand):
    help = 'Validate production security configuration and requirements'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Use strict validation (fail on warnings)',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix configuration issues automatically',
        )
    
    def handle(self, *args, **options):
        """Execute comprehensive production security validation."""
        
        self.stdout.write(
            self.style.SUCCESS('🔒 Production Security Validation Starting...')
        )
        
        errors = []
        warnings = []
        passed = []
        
        # Critical security validations
        self._validate_debug_setting(errors, warnings, passed)
        self._validate_secret_key(errors, warnings, passed)
        self._validate_https_configuration(errors, warnings, passed)
        self._validate_security_middleware(errors, warnings, passed)
        self._validate_database_security(errors, warnings, passed)
        self._validate_session_security(errors, warnings, passed)
        self._validate_csrf_protection(errors, warnings, passed)
        self._validate_allowed_hosts(errors, warnings, passed)
        self._validate_logging_configuration(errors, warnings, passed)
        
        # Generate report
        self._generate_validation_report(errors, warnings, passed, options)
        
        # Determine exit status
        if errors:
            raise CommandError("❌ Production security validation FAILED")
        elif warnings and options['strict']:
            raise CommandError("⚠️ Production security validation failed strict mode")
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Production security validation PASSED")
            )
    
    def _validate_debug_setting(self, errors, warnings, passed):
        """Validate DEBUG setting for production."""
        debug_setting = getattr(settings, 'DEBUG', True)
        
        if debug_setting:
            errors.append("CRITICAL: DEBUG=True in production environment")
            errors.append("  Impact: Debug information disclosure, performance impact")
            errors.append("  Fix: Set DEBUG=False in production settings")
        else:
            passed.append("✅ DEBUG=False (production safe)")
    
    def _validate_secret_key(self, errors, warnings, passed):
        """Validate SECRET_KEY security."""
        secret_key = getattr(settings, 'SECRET_KEY', '')
        
        if not secret_key:
            errors.append("CRITICAL: SECRET_KEY not configured")
        elif len(secret_key) < 50:
            errors.append(f"CRITICAL: SECRET_KEY too short ({len(secret_key)} chars, minimum 50)")
        elif 'django-insecure' in secret_key:
            errors.append("CRITICAL: Using Django default insecure SECRET_KEY")
        elif 'dev-only' in secret_key:
            warnings.append("WARNING: Using development SECRET_KEY pattern")
        elif secret_key == 'change-me' or secret_key == 'your-secret-key':
            errors.append("CRITICAL: Using placeholder SECRET_KEY")
        else:
            passed.append("✅ SECRET_KEY properly configured")
            
            # Check key entropy
            unique_chars = len(set(secret_key))
            if unique_chars < 20:
                warnings.append(f"WARNING: SECRET_KEY has low entropy ({unique_chars} unique chars)")
            else:
                passed.append("✅ SECRET_KEY has good entropy")
    
    def _validate_https_configuration(self, errors, warnings, passed):
        """Validate HTTPS and SSL security settings."""
        ssl_redirect = getattr(settings, 'SECURE_SSL_REDIRECT', False)
        hsts_seconds = getattr(settings, 'SECURE_HSTS_SECONDS', 0)
        session_secure = getattr(settings, 'SESSION_COOKIE_SECURE', False)
        csrf_secure = getattr(settings, 'CSRF_COOKIE_SECURE', False)
        
        if not ssl_redirect:
            warnings.append("WARNING: SECURE_SSL_REDIRECT not enabled")
        else:
            passed.append("✅ HTTPS redirect enabled")
        
        if hsts_seconds < 31536000:  # 1 year
            warnings.append(f"WARNING: HSTS timeout too short ({hsts_seconds}s, recommend 31536000s)")
        else:
            passed.append("✅ HSTS properly configured")
        
        if not session_secure:
            warnings.append("WARNING: SESSION_COOKIE_SECURE not enabled")
        else:
            passed.append("✅ Secure session cookies enabled")
        
        if not csrf_secure:
            warnings.append("WARNING: CSRF_COOKIE_SECURE not enabled")
        else:
            passed.append("✅ Secure CSRF cookies enabled")
    
    def _validate_security_middleware(self, errors, warnings, passed):
        """Validate security middleware configuration."""
        middleware = getattr(settings, 'MIDDLEWARE', [])
        
        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'app.middleware.SecurityHeadersMiddleware',
            'app.middleware.RateLimitMiddleware',
        ]
        
        for required in required_middleware:
            if required not in middleware:
                errors.append(f"CRITICAL: Required security middleware missing: {required}")
            else:
                passed.append(f"✅ Security middleware present: {required.split('.')[-1]}")
        
        # Check middleware order
        security_index = -1
        csrf_index = -1
        
        for i, mw in enumerate(middleware):
            if 'SecurityMiddleware' in mw:
                security_index = i
            elif 'CsrfViewMiddleware' in mw:
                csrf_index = i
        
        if security_index > 2:
            warnings.append("WARNING: SecurityMiddleware should be first in middleware stack")
        
        if csrf_index < security_index:
            warnings.append("WARNING: CsrfViewMiddleware should come after SecurityMiddleware")
    
    def _validate_database_security(self, errors, warnings, passed):
        """Validate database security configuration."""
        db_config = settings.DATABASES.get('default', {})
        
        # Check for default passwords
        db_password = db_config.get('PASSWORD', '')
        weak_passwords = ['postgres', 'password', 'admin', '123456', 'root']
        
        if db_password in weak_passwords:
            errors.append(f"CRITICAL: Using weak database password: {db_password}")
        elif len(db_password) < 12:
            warnings.append(f"WARNING: Database password is short ({len(db_password)} chars)")
        else:
            passed.append("✅ Database password appears secure")
        
        # Check database host
        db_host = db_config.get('HOST', 'localhost')
        if db_host in ['localhost', '127.0.0.1']:
            passed.append("✅ Database host is local/internal")
        else:
            warnings.append(f"WARNING: Database host is external: {db_host}")
        
        # Check connection settings
        conn_max_age = db_config.get('CONN_MAX_AGE', 0)
        if conn_max_age > 600:  # 10 minutes
            warnings.append(f"WARNING: CONN_MAX_AGE is high ({conn_max_age}s)")
        else:
            passed.append("✅ Database connection timeout properly configured")
    
    def _validate_session_security(self, errors, warnings, passed):
        """Validate session security settings."""
        session_age = getattr(settings, 'SESSION_COOKIE_AGE', 1209600)  # 2 weeks default
        session_httponly = getattr(settings, 'SESSION_COOKIE_HTTPONLY', False)
        session_samesite = getattr(settings, 'SESSION_COOKIE_SAMESITE', None)
        
        if session_age > 86400:  # 24 hours
            warnings.append(f"WARNING: Session timeout is long ({session_age}s)")
        else:
            passed.append("✅ Session timeout properly configured")
        
        if not session_httponly:
            errors.append("CRITICAL: SESSION_COOKIE_HTTPONLY not enabled")
        else:
            passed.append("✅ HttpOnly session cookies enabled")
        
        if session_samesite != 'Strict':
            warnings.append(f"WARNING: SESSION_COOKIE_SAMESITE not set to Strict")
        else:
            passed.append("✅ SameSite session cookies properly configured")
    
    def _validate_csrf_protection(self, errors, warnings, passed):
        """Validate CSRF protection configuration."""
        csrf_httponly = getattr(settings, 'CSRF_COOKIE_HTTPONLY', False)
        csrf_samesite = getattr(settings, 'CSRF_COOKIE_SAMESITE', None)
        
        if not csrf_httponly:
            warnings.append("WARNING: CSRF_COOKIE_HTTPONLY not enabled")
        else:
            passed.append("✅ HttpOnly CSRF cookies enabled")
        
        if csrf_samesite != 'Strict':
            warnings.append("WARNING: CSRF_COOKIE_SAMESITE not set to Strict")
        else:
            passed.append("✅ SameSite CSRF cookies properly configured")
    
    def _validate_allowed_hosts(self, errors, warnings, passed):
        """Validate ALLOWED_HOSTS configuration."""
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        
        if not allowed_hosts:
            errors.append("CRITICAL: ALLOWED_HOSTS is empty")
        elif '*' in allowed_hosts:
            errors.append("CRITICAL: ALLOWED_HOSTS contains wildcard '*'")
        elif 'localhost' in allowed_hosts or '127.0.0.1' in allowed_hosts:
            warnings.append("WARNING: ALLOWED_HOSTS contains localhost (development setting)")
        else:
            passed.append("✅ ALLOWED_HOSTS properly configured")
    
    def _validate_logging_configuration(self, errors, warnings, passed):
        """Validate logging configuration for security."""
        logging_config = getattr(settings, 'LOGGING', {})
        
        if not logging_config:
            warnings.append("WARNING: No logging configuration found")
            return
        
        # Check for security logging
        loggers = logging_config.get('loggers', {})
        
        if 'security' not in loggers and 'django.security' not in loggers:
            warnings.append("WARNING: No security-specific logging configured")
        else:
            passed.append("✅ Security logging configured")
        
        # Check log levels
        root_level = logging_config.get('root', {}).get('level', 'INFO')
        if root_level == 'DEBUG':
            warnings.append("WARNING: Root logging level is DEBUG (verbose for production)")
        else:
            passed.append("✅ Logging level appropriate for production")
    
    def _generate_validation_report(self, errors, warnings, passed, options):
        """Generate comprehensive validation report."""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("🔒 PRODUCTION SECURITY VALIDATION REPORT")
        self.stdout.write("=" * 60)
        
        total_checks = len(errors) + len(warnings) + len(passed)
        
        self.stdout.write(f"📊 Summary:")
        self.stdout.write(f"  Total Checks: {total_checks}")
        self.stdout.write(f"  ❌ Errors: {len(errors)}")
        self.stdout.write(f"  ⚠️ Warnings: {len(warnings)}")
        self.stdout.write(f"  ✅ Passed: {len(passed)}")
        
        if errors:
            self.stdout.write(f"\n{self.style.ERROR('❌ CRITICAL SECURITY ISSUES:')}")
            for error in errors:
                self.stdout.write(f"  {self.style.ERROR(error)}")
        
        if warnings:
            self.stdout.write(f"\n{self.style.WARNING('⚠️ SECURITY WARNINGS:')}")
            for warning in warnings:
                self.stdout.write(f"  {self.style.WARNING(warning)}")
        
        if passed:
            self.stdout.write(f"\n{self.style.SUCCESS('✅ SECURITY CONTROLS VALIDATED:')}")
            for check in passed:
                self.stdout.write(f"  {self.style.SUCCESS(check)}")
        
        # Final assessment
        self.stdout.write(f"\n{self.style.HTTP_INFO('🎯 SECURITY ASSESSMENT:')}")
        
        if errors:
            self.stdout.write(
                self.style.ERROR("❌ PRODUCTION DEPLOYMENT BLOCKED - Fix critical issues")
            )
        elif warnings:
            self.stdout.write(
                self.style.WARNING("⚠️ PRODUCTION DEPLOYMENT ALLOWED WITH WARNINGS")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ PRODUCTION DEPLOYMENT APPROVED - All checks passed")
            )
        
        # Save report to file
        report_data = {
            'timestamp': f"{datetime.now().isoformat()}",
            'total_checks': total_checks,
            'errors': errors,
            'warnings': warnings,
            'passed': passed,
            'deployment_approved': len(errors) == 0
        }
        
        import json
        with open('production_security_validation.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.stdout.write(f"\n📄 Detailed report saved to: production_security_validation.json")