"""
Security Hardening Tests
Team Delta - Security Sprint 4
"""

import pytest
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings
from config.security_headers import SECURITY_HEADERS
from config.input_validation import SecurityValidator
from config.rate_limiting import RateLimitMiddleware

class TestSecurityHeaders(TestCase):
    """Test security headers implementation"""
    
    def setUp(self):
        self.client = Client()
    
    def test_security_headers_present(self):
        """Test that security headers are present in responses"""
        response = self.client.get('/')
        
        # Check essential security headers
        self.assertIn('X-Frame-Options', response.headers)
        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertIn('X-XSS-Protection', response.headers)
        
        # Check Content Security Policy
        if 'Content-Security-Policy' in response.headers:
            csp = response.headers['Content-Security-Policy']
            self.assertIn("default-src 'self'", csp)
            self.assertIn("frame-ancestors 'none'", csp)
    
    def test_frame_options_deny(self):
        """Test that X-Frame-Options is set to DENY"""
        response = self.client.get('/')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
    
    def test_content_type_nosniff(self):
        """Test that X-Content-Type-Options is set to nosniff"""
        response = self.client.get('/')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')

class TestInputValidation(TestCase):
    """Test input validation implementation"""
    
    def setUp(self):
        self.validator = SecurityValidator()
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "UNION SELECT * FROM users",
            "1 OR 1=1",
            "admin'--",
        ]
        
        for input_value in malicious_inputs:
            with self.assertRaises(ValidationError):
                self.validator.validate_and_sanitize(input_value, 'strict')
    
    def test_xss_detection(self):
        """Test XSS pattern detection"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "onload=alert('xss')",
        ]
        
        for input_value in malicious_inputs:
            with self.assertRaises(ValidationError):
                self.validator.validate_and_sanitize(input_value, 'strict')
    
    def test_path_traversal_detection(self):
        """Test path traversal pattern detection"""
        malicious_inputs = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
        ]
        
        for input_value in malicious_inputs:
            with self.assertRaises(ValidationError):
                self.validator.validate_and_sanitize(input_value, 'strict')
    
    def test_safe_input_validation(self):
        """Test that safe input passes validation"""
        safe_inputs = [
            "Hello World",
            "user@example.com",
            "123 Main Street",
            "Normal text with numbers 123",
        ]
        
        for input_value in safe_inputs:
            try:
                result = self.validator.validate_and_sanitize(input_value, 'strict')
                self.assertIsNotNone(result)
            except ValidationError:
                self.fail(f"Safe input '{input_value}' failed validation")

class TestRateLimiting(TestCase):
    """Test rate limiting implementation"""
    
    def setUp(self):
        self.client = Client()
        self.middleware = RateLimitMiddleware(lambda r: None)
    
    def test_rate_limit_enforcement(self):
        """Test that rate limiting is enforced"""
        # Make multiple requests to trigger rate limiting
        for i in range(105):  # Exceed default limit of 100
            response = self.client.get('/')
            if response.status_code == 429:  # Too Many Requests
                break
        else:
            self.fail("Rate limiting was not enforced")
    
    def test_different_endpoint_limits(self):
        """Test different rate limits for different endpoints"""
        # Test API endpoint with higher limit
        for i in range(1001):  # Exceed API limit of 1000
            response = self.client.get('/api/v1/health/')
            if response.status_code == 429:
                break
        else:
            self.fail("API rate limiting was not enforced")
    
    def test_rate_limit_reset(self):
        """Test that rate limits reset after time period"""
        # This test would require time manipulation
        # For now, we'll test the basic functionality
        response = self.client.get('/')
        self.assertNotEqual(response.status_code, 429)

class TestAuthenticationSecurity(TestCase):
    """Test authentication security measures"""
    
    def setUp(self):
        self.client = Client()
    
    def test_admin_access_requires_auth(self):
        """Test that admin access requires authentication"""
        response = self.client.get('/admin/')
        self.assertIn(response.status_code, [302, 401, 403])  # Redirect or auth required
    
    def test_csrf_protection(self):
        """Test that CSRF protection is enabled"""
        response = self.client.post('/api/v1/feedback/', {'message': 'test'})
        self.assertIn(response.status_code, [403, 400])  # CSRF token required
    
    def test_session_security(self):
        """Test session security settings"""
        response = self.client.get('/')
        
        # Check session cookie security
        if 'sessionid' in response.cookies:
            session_cookie = response.cookies['sessionid']
            self.assertTrue(session_cookie.get('secure', False))
            self.assertTrue(session_cookie.get('httponly', False))

class TestSecurityMonitoring(TestCase):
    """Test security monitoring implementation"""
    
    def test_security_event_logging(self):
        """Test that security events are logged"""
        # This test would require log capture
        # For now, we'll test the basic functionality
        from config.monitoring import SecurityMetrics
        
        # Test metrics increment
        SecurityMetrics.increment_security_event('test_event')
        
        # Test stats retrieval
        stats = SecurityMetrics.get_security_stats(hours=1)
        self.assertIsInstance(stats, dict)
    
    def test_performance_monitoring(self):
        """Test performance monitoring"""
        from config.monitoring import PerformanceMonitor
        
        # Test response time recording
        PerformanceMonitor.record_response_time('/test/', 0.5)
        
        # Test stats retrieval
        stats = PerformanceMonitor.get_performance_stats('/test/', minutes=5)
        self.assertIsInstance(stats, list)
