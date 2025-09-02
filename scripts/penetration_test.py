#!/usr/bin/env python3
"""
Comprehensive Penetration Testing Suite
Tests application security according to repository documentation.

Created for comprehensive security assessment and validation.
"""

import requests
import json
import time
import subprocess
import socket
import ssl
import sys
from urllib.parse import urljoin
from datetime import datetime
import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class PenetrationTestSuite:
    """Comprehensive penetration testing suite."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': [],
            'passed': []
        }
        
    def run_comprehensive_test(self):
        """Run complete penetration testing suite."""
        print(f"{Colors.BLUE}{Colors.BOLD}🔒 Comprehensive Penetration Test Suite{Colors.END}")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Infrastructure tests
        self.test_network_security()
        self.test_ssl_tls_configuration()
        self.test_service_enumeration()
        
        # Application tests
        self.test_authentication_security()
        self.test_authorization_bypass()
        self.test_session_management()
        
        # Input validation tests
        self.test_sql_injection()
        self.test_xss_vulnerabilities()
        self.test_csrf_protection()
        
        # API security tests
        self.test_api_security()
        self.test_rate_limiting()
        
        # Data security tests
        self.test_sensitive_data_exposure()
        self.test_file_upload_security()
        
        # Infrastructure security
        self.test_container_security()
        self.test_configuration_security()
        
        # Generate comprehensive report
        self.generate_security_report()
    
    def test_network_security(self):
        """Test network-level security controls."""
        print(f"\n{Colors.BLUE}🌐 Network Security Testing{Colors.END}")
        
        # Port scanning
        print("  🔍 Port scanning...")
        common_ports = [22, 80, 443, 3306, 5432, 6379, 5672, 8000, 8080]
        open_ports = []
        
        for port in common_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        
        if 22 in open_ports:
            self.results['medium'].append("SSH port 22 is open - ensure proper access controls")
        
        if 3306 in open_ports:
            self.results['high'].append("MySQL port 3306 is exposed - should be internal only")
        
        if 5432 in open_ports:
            self.results['medium'].append("PostgreSQL port 5432 is exposed - verify access controls")
        
        if 6379 in open_ports:
            self.results['high'].append("Redis port 6379 is exposed - should be internal only")
        
        self.results['info'].append(f"Open ports detected: {open_ports}")
        
        # Service banner grabbing
        print("  🔍 Service enumeration...")
        if 8000 in open_ports:
            try:
                response = requests.get(f"{self.base_url}/", timeout=5)
                server_header = response.headers.get('Server', 'Not disclosed')
                self.results['info'].append(f"Web server: {server_header}")
                
                if 'nginx' in server_header.lower() and '/' in server_header:
                    self.results['low'].append("Web server version disclosed in headers")
                else:
                    self.results['passed'].append("Web server version properly hidden")
                    
            except Exception as e:
                self.results['medium'].append(f"Unable to connect to web application: {str(e)}")
    
    def test_ssl_tls_configuration(self):
        """Test SSL/TLS configuration security."""
        print(f"\n{Colors.BLUE}🔐 SSL/TLS Configuration Testing{Colors.END}")
        
        if self.base_url.startswith('https'):
            try:
                # Test SSL certificate
                hostname = self.base_url.replace('https://', '').split('/')[0]
                context = ssl.create_default_context()
                
                with socket.create_connection((hostname, 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        
                        # Check certificate validity
                        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        days_until_expiry = (not_after - datetime.now()).days
                        
                        if days_until_expiry < 30:
                            self.results['high'].append(f"SSL certificate expires in {days_until_expiry} days")
                        elif days_until_expiry < 90:
                            self.results['medium'].append(f"SSL certificate expires in {days_until_expiry} days")
                        else:
                            self.results['passed'].append("SSL certificate validity is good")
                        
                        # Check cipher suite
                        cipher = ssock.cipher()
                        if cipher:
                            cipher_name = cipher[0]
                            if 'RC4' in cipher_name or 'DES' in cipher_name:
                                self.results['high'].append(f"Weak cipher suite in use: {cipher_name}")
                            else:
                                self.results['passed'].append(f"Strong cipher suite: {cipher_name}")
                
            except Exception as e:
                self.results['medium'].append(f"SSL/TLS test failed: {str(e)}")
        else:
            self.results['critical'].append("Application not using HTTPS - critical security risk")
    
    def test_service_enumeration(self):
        """Test for service enumeration vulnerabilities."""
        print(f"\n{Colors.BLUE}🔍 Service Enumeration Testing{Colors.END}")
        
        # Test common endpoints
        test_endpoints = [
            '/admin/',
            '/api/',
            '/api/v1/',
            '/health/',
            '/api/v1/health/',
            '/.env',
            '/config/',
            '/backup/',
            '/logs/',
            '/static/',
            '/media/',
            '/robots.txt',
            '/sitemap.xml',
        ]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(urljoin(self.base_url, endpoint), timeout=5)
                
                if endpoint in ['/.env', '/config/', '/backup/', '/logs/']:
                    if response.status_code == 200:
                        self.results['critical'].append(f"Sensitive endpoint accessible: {endpoint}")
                    else:
                        self.results['passed'].append(f"Sensitive endpoint properly protected: {endpoint}")
                
                elif endpoint == '/admin/':
                    if response.status_code == 200:
                        self.results['info'].append("Django admin interface is accessible")
                        # Check if admin requires authentication
                        if 'login' not in response.text.lower():
                            self.results['critical'].append("Django admin accessible without authentication")
                        else:
                            self.results['passed'].append("Django admin requires authentication")
                
                elif endpoint in ['/api/', '/api/v1/']:
                    if response.status_code == 200:
                        self.results['info'].append(f"API endpoint accessible: {endpoint}")
                        # Check for API documentation exposure
                        if 'swagger' in response.text.lower() or 'openapi' in response.text.lower():
                            self.results['low'].append("API documentation may be publicly accessible")
                
            except Exception as e:
                self.results['info'].append(f"Endpoint {endpoint} not accessible: {str(e)}")
    
    def test_authentication_security(self):
        """Test authentication mechanisms for vulnerabilities."""
        print(f"\n{Colors.BLUE}🔑 Authentication Security Testing{Colors.END}")
        
        # Test login endpoint
        login_url = urljoin(self.base_url, '/auth/login/')
        
        try:
            # Test for login endpoint existence
            response = requests.get(login_url, timeout=5)
            if response.status_code == 200:
                self.results['info'].append("Login endpoint accessible")
                
                # Test for username enumeration
                print("  🔍 Testing username enumeration...")
                self._test_username_enumeration(login_url)
                
                # Test for brute force protection
                print("  🔍 Testing brute force protection...")
                self._test_brute_force_protection(login_url)
                
                # Test for weak password policies
                print("  🔍 Testing password policies...")
                self._test_password_policies()
                
            else:
                self.results['info'].append(f"Login endpoint returned status {response.status_code}")
                
        except Exception as e:
            self.results['medium'].append(f"Authentication testing failed: {str(e)}")
    
    def _test_username_enumeration(self, login_url):
        """Test for username enumeration vulnerability."""
        test_usernames = ['admin', 'administrator', 'test', 'user', 'nonexistent']
        
        for username in test_usernames:
            try:
                data = {
                    'username': username,
                    'password': 'wrongpassword'
                }
                response = requests.post(login_url, data=data, timeout=5)
                
                # Check response time and content for enumeration
                if 'user does not exist' in response.text.lower():
                    self.results['medium'].append("Username enumeration possible - different error messages")
                    break
                    
            except Exception:
                pass
        else:
            self.results['passed'].append("Username enumeration protection appears effective")
    
    def _test_brute_force_protection(self, login_url):
        """Test for brute force attack protection."""
        # Attempt multiple failed logins
        for i in range(10):
            try:
                data = {
                    'username': 'testuser',
                    'password': f'wrongpassword{i}'
                }
                response = requests.post(login_url, data=data, timeout=5)
                
                if response.status_code == 429:  # Too Many Requests
                    self.results['passed'].append("Rate limiting detected for login attempts")
                    break
                elif 'blocked' in response.text.lower() or 'locked' in response.text.lower():
                    self.results['passed'].append("Account lockout mechanism detected")
                    break
                    
            except Exception:
                pass
        else:
            self.results['high'].append("No brute force protection detected")
    
    def _test_password_policies(self):
        """Test password policy enforcement."""
        # This would test registration endpoint if available
        register_url = urljoin(self.base_url, '/auth/register/')
        
        try:
            response = requests.get(register_url, timeout=5)
            if response.status_code == 200:
                self.results['info'].append("Registration endpoint accessible")
                
                # Test weak password acceptance
                weak_passwords = ['123456', 'password', 'admin', 'test']
                # This would require implementing actual registration tests
                self.results['info'].append("Password policy testing requires manual validation")
            else:
                self.results['info'].append("Registration endpoint not accessible")
                
        except Exception:
            self.results['info'].append("Registration endpoint testing failed")
    
    def test_authorization_bypass(self):
        """Test for authorization bypass vulnerabilities."""
        print(f"\n{Colors.BLUE}🛡️ Authorization Testing{Colors.END}")
        
        # Test direct object reference
        print("  🔍 Testing direct object references...")
        
        # Test API endpoints without authentication
        api_endpoints = [
            '/api/v1/users/',
            '/api/v1/accounts/',
            '/api/v1/transactions/',
            '/api/v1/budgets/',
        ]
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(urljoin(self.base_url, endpoint), timeout=5)
                
                if response.status_code == 200:
                    self.results['critical'].append(f"API endpoint accessible without authentication: {endpoint}")
                elif response.status_code == 401:
                    self.results['passed'].append(f"API endpoint properly protected: {endpoint}")
                elif response.status_code == 403:
                    self.results['passed'].append(f"API endpoint access forbidden: {endpoint}")
                else:
                    self.results['info'].append(f"API endpoint {endpoint} returned status {response.status_code}")
                    
            except Exception as e:
                self.results['info'].append(f"API endpoint test failed for {endpoint}: {str(e)}")
    
    def test_session_management(self):
        """Test session management security."""
        print(f"\n{Colors.BLUE}🍪 Session Management Testing{Colors.END}")
        
        try:
            # Test session cookie security
            response = requests.get(self.base_url, timeout=5)
            
            # Check for secure cookie flags
            set_cookie = response.headers.get('Set-Cookie', '')
            
            if 'HttpOnly' not in set_cookie and set_cookie:
                self.results['medium'].append("Session cookies missing HttpOnly flag")
            elif set_cookie:
                self.results['passed'].append("Session cookies have HttpOnly flag")
            
            if 'Secure' not in set_cookie and set_cookie and self.base_url.startswith('https'):
                self.results['medium'].append("Session cookies missing Secure flag for HTTPS")
            elif set_cookie and self.base_url.startswith('https'):
                self.results['passed'].append("Session cookies have Secure flag")
            
            if 'SameSite' not in set_cookie and set_cookie:
                self.results['low'].append("Session cookies missing SameSite attribute")
            elif set_cookie:
                self.results['passed'].append("Session cookies have SameSite attribute")
                
        except Exception as e:
            self.results['medium'].append(f"Session management testing failed: {str(e)}")
    
    def test_sql_injection(self):
        """Test for SQL injection vulnerabilities."""
        print(f"\n{Colors.BLUE}💉 SQL Injection Testing{Colors.END}")
        
        # SQL injection payloads
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "1' AND (SELECT COUNT(*) FROM users) > 0 --",
            "' OR 1=1#",
        ]
        
        # Test endpoints that might be vulnerable
        test_endpoints = [
            '/api/v1/users/?search=',
            '/api/v1/accounts/?search=',
            '/api/v1/transactions/?search=',
        ]
        
        for endpoint in test_endpoints:
            for payload in sql_payloads:
                try:
                    url = urljoin(self.base_url, endpoint + payload)
                    response = requests.get(url, timeout=5)
                    
                    # Check for SQL error messages
                    error_indicators = [
                        'sql', 'database', 'mysql', 'postgresql', 'sqlite',
                        'syntax error', 'column', 'table', 'select', 'from'
                    ]
                    
                    response_text = response.text.lower()
                    if any(indicator in response_text for indicator in error_indicators):
                        self.results['critical'].append(f"Potential SQL injection at {endpoint}")
                        break
                        
                except Exception:
                    pass
        else:
            self.results['passed'].append("No obvious SQL injection vulnerabilities detected")
    
    def test_xss_vulnerabilities(self):
        """Test for Cross-Site Scripting vulnerabilities."""
        print(f"\n{Colors.BLUE}🚨 XSS Vulnerability Testing{Colors.END}")
        
        # XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//",
            "<svg onload=alert('XSS')>",
        ]
        
        # Test search and input endpoints
        test_endpoints = [
            '/api/v1/users/?search=',
            '/dashboard/?message=',
        ]
        
        for endpoint in test_endpoints:
            for payload in xss_payloads:
                try:
                    url = urljoin(self.base_url, endpoint + payload)
                    response = requests.get(url, timeout=5)
                    
                    # Check if payload is reflected unescaped
                    if payload in response.text and 'text/html' in response.headers.get('Content-Type', ''):
                        self.results['high'].append(f"Potential XSS vulnerability at {endpoint}")
                        break
                        
                except Exception:
                    pass
        else:
            self.results['passed'].append("No obvious XSS vulnerabilities detected")
    
    def test_csrf_protection(self):
        """Test CSRF protection mechanisms."""
        print(f"\n{Colors.BLUE}🛡️ CSRF Protection Testing{Colors.END}")
        
        try:
            # Test if CSRF tokens are required
            response = requests.get(urljoin(self.base_url, '/auth/login/'), timeout=5)
            
            if 'csrfmiddlewaretoken' in response.text:
                self.results['passed'].append("CSRF tokens present in forms")
                
                # Test POST without CSRF token
                post_response = requests.post(
                    urljoin(self.base_url, '/auth/login/'),
                    data={'username': 'test', 'password': 'test'},
                    timeout=5
                )
                
                if post_response.status_code == 403:
                    self.results['passed'].append("CSRF protection is enforced")
                else:
                    self.results['high'].append("CSRF protection may not be properly enforced")
            else:
                self.results['high'].append("CSRF tokens not found in forms")
                
        except Exception as e:
            self.results['medium'].append(f"CSRF testing failed: {str(e)}")
    
    def test_api_security(self):
        """Test API-specific security controls."""
        print(f"\n{Colors.BLUE}🔗 API Security Testing{Colors.END}")
        
        # Test API authentication
        api_endpoints = [
            '/api/v1/',
            '/api/v1/users/',
            '/api/v1/accounts/',
            '/api/v1/transactions/',
        ]
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(urljoin(self.base_url, endpoint), timeout=5)
                
                # Check authentication requirements
                if response.status_code == 401:
                    self.results['passed'].append(f"API endpoint requires authentication: {endpoint}")
                elif response.status_code == 200:
                    if endpoint != '/api/v1/':  # Root API might be public
                        self.results['high'].append(f"API endpoint accessible without auth: {endpoint}")
                    else:
                        self.results['info'].append("API root endpoint is accessible")
                
                # Check for API versioning
                if 'v1' in endpoint and response.status_code in [200, 401]:
                    self.results['passed'].append("API versioning implemented")
                
            except Exception as e:
                self.results['info'].append(f"API test failed for {endpoint}: {str(e)}")
    
    def test_rate_limiting(self):
        """Test rate limiting implementation."""
        print(f"\n{Colors.BLUE}⚡ Rate Limiting Testing{Colors.END}")
        
        # Test rate limiting on login endpoint
        login_url = urljoin(self.base_url, '/auth/login/')
        
        print("  🔍 Testing login rate limiting...")
        rate_limited = False
        
        for i in range(20):  # Attempt 20 rapid requests
            try:
                response = requests.post(
                    login_url,
                    data={'username': 'test', 'password': 'test'},
                    timeout=2
                )
                
                if response.status_code == 429:
                    self.results['passed'].append("Rate limiting is implemented")
                    rate_limited = True
                    break
                    
            except Exception:
                pass
        
        if not rate_limited:
            self.results['medium'].append("No rate limiting detected on login endpoint")
        
        # Test API rate limiting
        api_url = urljoin(self.base_url, '/api/v1/health/')
        
        print("  🔍 Testing API rate limiting...")
        for i in range(50):  # Rapid API requests
            try:
                response = requests.get(api_url, timeout=1)
                if response.status_code == 429:
                    self.results['passed'].append("API rate limiting is implemented")
                    break
            except Exception:
                pass
        else:
            self.results['low'].append("No API rate limiting detected")
    
    def test_sensitive_data_exposure(self):
        """Test for sensitive data exposure."""
        print(f"\n{Colors.BLUE}📊 Sensitive Data Exposure Testing{Colors.END}")
        
        # Test for debug information exposure
        try:
            response = requests.get(self.base_url, timeout=5)
            
            # Check for debug information
            debug_indicators = [
                'traceback', 'debug', 'django.core.exceptions',
                'internal server error', 'stack trace'
            ]
            
            response_text = response.text.lower()
            if any(indicator in response_text for indicator in debug_indicators):
                self.results['medium'].append("Debug information may be exposed in responses")
            else:
                self.results['passed'].append("No debug information exposed")
            
            # Check for sensitive headers
            sensitive_headers = [
                'X-Powered-By', 'Server', 'X-AspNet-Version'
            ]
            
            for header in sensitive_headers:
                if header in response.headers:
                    self.results['low'].append(f"Sensitive header exposed: {header}")
                else:
                    self.results['passed'].append(f"Sensitive header properly hidden: {header}")
            
        except Exception as e:
            self.results['medium'].append(f"Sensitive data exposure testing failed: {str(e)}")
    
    def test_file_upload_security(self):
        """Test file upload security controls."""
        print(f"\n{Colors.BLUE}📁 File Upload Security Testing{Colors.END}")
        
        # This would test the import feature if it exists
        upload_endpoints = [
            '/api/v1/import/upload/',
            '/upload/',
            '/media/upload/',
        ]
        
        for endpoint in upload_endpoints:
            try:
                # Test if endpoint exists
                response = requests.get(urljoin(self.base_url, endpoint), timeout=5)
                
                if response.status_code in [200, 405]:  # Exists but might require POST
                    self.results['info'].append(f"File upload endpoint found: {endpoint}")
                    
                    # Test malicious file upload (would need authentication)
                    self.results['info'].append("File upload security testing requires authentication")
                
            except Exception:
                pass
        
        self.results['info'].append("File upload endpoints not found or require authentication")
    
    def test_container_security(self):
        """Test container security configuration."""
        print(f"\n{Colors.BLUE}🐳 Container Security Testing{Colors.END}")
        
        try:
            # Check if Docker is accessible
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.results['info'].append("Docker containers detected")
                
                # Check for privileged containers
                if '--privileged' in result.stdout:
                    self.results['high'].append("Privileged containers detected")
                else:
                    self.results['passed'].append("No privileged containers detected")
                
                # Check for root user in containers
                container_inspect = subprocess.run([
                    'docker', 'inspect', '--format={{.Config.User}}', 'financial-stronghold_web_1'
                ], capture_output=True, text=True, timeout=5)
                
                if container_inspect.returncode == 0:
                    user = container_inspect.stdout.strip()
                    if user == '' or user == 'root' or user == '0':
                        self.results['medium'].append("Container running as root user")
                    else:
                        self.results['passed'].append(f"Container running as non-root user: {user}")
                
            else:
                self.results['info'].append("Docker not accessible for security testing")
                
        except Exception as e:
            self.results['info'].append(f"Container security testing failed: {str(e)}")
    
    def test_configuration_security(self):
        """Test configuration security."""
        print(f"\n{Colors.BLUE}⚙️ Configuration Security Testing{Colors.END}")
        
        # Test for exposed configuration files
        config_files = [
            '/.env',
            '/config/.env',
            '/app/.env',
            '/docker-compose.yml',
            '/docker-compose.override.yml',
        ]
        
        for config_file in config_files:
            try:
                response = requests.get(urljoin(self.base_url, config_file), timeout=5)
                
                if response.status_code == 200:
                    self.results['critical'].append(f"Configuration file exposed: {config_file}")
                else:
                    self.results['passed'].append(f"Configuration file properly protected: {config_file}")
                    
            except Exception:
                pass
        
        # Test for default credentials
        self.results['info'].append("Default credentials testing requires manual validation")
    
    def generate_security_report(self):
        """Generate comprehensive security report."""
        print(f"\n{Colors.BOLD}🔒 PENETRATION TEST RESULTS{Colors.END}")
        print("=" * 60)
        
        # Summary
        total_issues = (len(self.results['critical']) + len(self.results['high']) + 
                       len(self.results['medium']) + len(self.results['low']))
        
        print(f"🎯 Security Assessment Summary:")
        print(f"  {Colors.RED}Critical: {len(self.results['critical'])}{Colors.END}")
        print(f"  {Colors.RED}High: {len(self.results['high'])}{Colors.END}")
        print(f"  {Colors.YELLOW}Medium: {len(self.results['medium'])}{Colors.END}")
        print(f"  {Colors.YELLOW}Low: {len(self.results['low'])}{Colors.END}")
        print(f"  {Colors.BLUE}Info: {len(self.results['info'])}{Colors.END}")
        print(f"  {Colors.GREEN}Passed: {len(self.results['passed'])}{Colors.END}")
        print(f"  Total Issues: {total_issues}")
        
        # Detailed findings
        for severity in ['critical', 'high', 'medium', 'low']:
            if self.results[severity]:
                color = Colors.RED if severity in ['critical', 'high'] else Colors.YELLOW
                print(f"\n{color}{Colors.BOLD}{severity.upper()} SEVERITY FINDINGS:{Colors.END}")
                for finding in self.results[severity]:
                    print(f"  {color}• {finding}{Colors.END}")
        
        if self.results['info']:
            print(f"\n{Colors.BLUE}{Colors.BOLD}INFORMATIONAL FINDINGS:{Colors.END}")
            for finding in self.results['info']:
                print(f"  {Colors.BLUE}• {finding}{Colors.END}")
        
        if self.results['passed']:
            print(f"\n{Colors.GREEN}{Colors.BOLD}SECURITY CONTROLS VALIDATED:{Colors.END}")
            for finding in self.results['passed']:
                print(f"  {Colors.GREEN}• {finding}{Colors.END}")
        
        # Risk assessment
        print(f"\n{Colors.BOLD}🎯 RISK ASSESSMENT:{Colors.END}")
        
        if self.results['critical']:
            print(f"{Colors.RED}❌ CRITICAL RISK: Immediate action required{Colors.END}")
            risk_level = "CRITICAL"
        elif self.results['high']:
            print(f"{Colors.RED}⚠️ HIGH RISK: Address high severity issues{Colors.END}")
            risk_level = "HIGH"
        elif self.results['medium']:
            print(f"{Colors.YELLOW}⚠️ MEDIUM RISK: Address medium severity issues{Colors.END}")
            risk_level = "MEDIUM"
        elif self.results['low']:
            print(f"{Colors.YELLOW}ℹ️ LOW RISK: Consider addressing low severity issues{Colors.END}")
            risk_level = "LOW"
        else:
            print(f"{Colors.GREEN}✅ LOW RISK: No significant security issues found{Colors.END}")
            risk_level = "MINIMAL"
        
        # Generate JSON report
        report = {
            'timestamp': datetime.now().isoformat(),
            'target': self.base_url,
            'risk_level': risk_level,
            'total_issues': total_issues,
            'findings': self.results,
            'summary': {
                'critical': len(self.results['critical']),
                'high': len(self.results['high']),
                'medium': len(self.results['medium']),
                'low': len(self.results['low']),
                'info': len(self.results['info']),
                'passed': len(self.results['passed'])
            }
        }
        
        with open('penetration_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: penetration_test_report.json")
        
        return risk_level, total_issues


def main():
    """Main penetration testing function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive Penetration Testing Suite')
    parser.add_argument('--target', default='http://localhost:8000', 
                       help='Target URL for testing (default: http://localhost:8000)')
    parser.add_argument('--output', default='penetration_test_report.json',
                       help='Output file for detailed report')
    
    args = parser.parse_args()
    
    # Run penetration test
    pentest = PenetrationTestSuite(args.target)
    
    try:
        risk_level, total_issues = pentest.run_comprehensive_test()
        
        # Exit with appropriate code
        if risk_level in ['CRITICAL', 'HIGH']:
            sys.exit(1)  # Fail for critical/high risk
        else:
            sys.exit(0)  # Pass for medium/low risk
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Penetration test interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Penetration test failed: {str(e)}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()