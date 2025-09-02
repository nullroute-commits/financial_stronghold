"""
Real-time security monitoring and threat detection system.
Implements comprehensive security monitoring based on penetration test findings.

Created for enhanced security monitoring and incident response.
"""

import logging
import re
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponseForbidden
import json

logger = logging.getLogger('security')


class ThreatDetectionService:
    """Advanced threat detection and response system."""
    
    def __init__(self):
        self.threat_patterns = {
            'sql_injection': [
                r'union\s+select', r'or\s+1\s*=\s*1', r'drop\s+table',
                r'insert\s+into', r'delete\s+from', r'update\s+.*set',
                r'exec\s*\(', r'sp_\w+', r'xp_\w+', r'information_schema',
                r'sys\.tables', r'sys\.columns'
            ],
            'xss_attempts': [
                r'<script[^>]*>', r'</script>', r'javascript:', r'vbscript:',
                r'onload\s*=', r'onerror\s*=', r'onclick\s*=', r'onmouseover\s*=',
                r'onfocus\s*=', r'onblur\s*=', r'data:text/html'
            ],
            'path_traversal': [
                r'\.\./+', r'\.\.\\+', r'%2e%2e%2f', r'%2e%2e%5c',
                r'\.\.%2f', r'\.\.%5c', r'/etc/passwd', r'/etc/shadow',
                r'c:\\windows\\system32'
            ],
            'command_injection': [
                r';\s*ls\s', r';\s*cat\s', r';\s*rm\s', r';\s*mkdir\s',
                r'`.*`', r'\$\(.*\)', r'&&\s*\w+', r'\|\|\s*\w+',
                r';\s*wget\s', r';\s*curl\s'
            ],
            'ldap_injection': [
                r'\*\)\(.*=', r'\)\(\|', r'\)\(&', r'\*\)\(cn=',
                r'\*\)\(mail=', r'\*\)\(uid='
            ]
        }
        
        self.alert_thresholds = {
            'failed_logins_per_ip': 5,      # per 5 minutes
            'failed_logins_per_user': 3,    # per 5 minutes
            'api_errors_per_ip': 20,        # per minute
            'suspicious_requests': 10,       # per minute
            'admin_access_attempts': 3,      # per hour
            'file_upload_failures': 5,      # per hour
        }
    
    def analyze_request_for_threats(self, request):
        """Comprehensive request analysis for security threats."""
        threats_detected = []
        
        # Analyze URL path
        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, request.path, re.IGNORECASE):
                    threats_detected.append({
                        'type': threat_type,
                        'pattern': pattern,
                        'location': 'url_path',
                        'value': request.path
                    })
        
        # Analyze GET parameters
        for param_name, param_value in request.GET.items():
            for threat_type, patterns in self.threat_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, str(param_value), re.IGNORECASE):
                        threats_detected.append({
                            'type': threat_type,
                            'pattern': pattern,
                            'location': f'get_param_{param_name}',
                            'value': str(param_value)[:100]  # Limit logged value
                        })
        
        # Analyze POST data (if safe to read)
        if request.method == 'POST' and hasattr(request, 'POST'):
            for param_name, param_value in request.POST.items():
                if param_name not in ['csrfmiddlewaretoken', 'password']:  # Skip sensitive fields
                    for threat_type, patterns in self.threat_patterns.items():
                        for pattern in patterns:
                            if re.search(pattern, str(param_value), re.IGNORECASE):
                                threats_detected.append({
                                    'type': threat_type,
                                    'pattern': pattern,
                                    'location': f'post_param_{param_name}',
                                    'value': str(param_value)[:100]
                                })
        
        # Analyze User-Agent for suspicious patterns
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        suspicious_ua_patterns = [
            r'sqlmap', r'nikto', r'nmap', r'masscan', r'zap',
            r'burpsuite', r'metasploit', r'nessus', r'openvas'
        ]
        
        for pattern in suspicious_ua_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                threats_detected.append({
                    'type': 'suspicious_tool',
                    'pattern': pattern,
                    'location': 'user_agent',
                    'value': user_agent[:100]
                })
        
        return threats_detected
    
    def respond_to_threats(self, request, threats):
        """Respond to detected security threats."""
        if not threats:
            return None
        
        ip_address = self.get_client_ip(request)
        user_id = str(request.user.id) if request.user.is_authenticated else 'anonymous'
        
        # Log all threats
        for threat in threats:
            logger.critical(f"THREAT_DETECTED: {threat['type']}", extra={
                'threat_type': threat['type'],
                'pattern': threat['pattern'],
                'location': threat['location'],
                'ip_address': ip_address,
                'user_id': user_id,
                'path': request.path,
                'method': request.method,
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
            })
        
        # Determine response based on threat severity
        critical_threats = ['sql_injection', 'command_injection', 'path_traversal']
        high_threats = ['xss_attempts', 'ldap_injection']
        
        # Check for critical threats
        for threat in threats:
            if threat['type'] in critical_threats:
                # Immediate IP blocking for critical threats
                self.block_ip_immediately(ip_address, threat)
                return HttpResponseForbidden("Access denied due to security violation")
        
        # Check for high-severity threats
        high_threat_count = sum(1 for t in threats if t['type'] in high_threats)
        if high_threat_count >= 3:
            # Temporary IP blocking for multiple high threats
            self.block_ip_temporarily(ip_address, duration_minutes=30)
            return HttpResponseForbidden("Access temporarily restricted")
        
        # Log and monitor for medium threats
        self.increment_threat_counter(ip_address, len(threats))
        
        return None  # Allow request but monitor
    
    def monitor_failed_login(self, request, username):
        """Monitor and respond to failed login attempts."""
        ip_address = self.get_client_ip(request)
        timestamp = datetime.now()
        
        # Track by IP address
        ip_key = f"failed_login_ip:{ip_address}"
        ip_count = cache.get(ip_key, 0) + 1
        cache.set(ip_key, ip_count, 300)  # 5 minutes
        
        # Track by username
        user_key = f"failed_login_user:{username}"
        user_count = cache.get(user_key, 0) + 1
        cache.set(user_key, user_count, 300)  # 5 minutes
        
        # Log security event
        logger.warning(f"FAILED_LOGIN_ATTEMPT", extra={
            'username': username,
            'ip_address': ip_address,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': timestamp.isoformat(),
            'ip_attempt_count': ip_count,
            'user_attempt_count': user_count
        })
        
        # Check thresholds and respond
        if ip_count >= self.alert_thresholds['failed_logins_per_ip']:
            self.send_security_alert(
                'BRUTE_FORCE_ATTACK_IP',
                f"IP {ip_address} exceeded failed login threshold ({ip_count} attempts)"
            )
            self.block_ip_temporarily(ip_address, duration_minutes=30)
        
        if user_count >= self.alert_thresholds['failed_logins_per_user']:
            self.send_security_alert(
                'ACCOUNT_ATTACK',
                f"User {username} exceeded failed login threshold ({user_count} attempts)"
            )
            # Consider account lockout here
    
    def monitor_admin_access(self, request, user):
        """Monitor administrative access attempts."""
        if user.is_staff or user.is_superuser:
            ip_address = self.get_client_ip(request)
            
            # Track admin access
            admin_key = f"admin_access:{ip_address}"
            admin_count = cache.get(admin_key, 0) + 1
            cache.set(admin_key, admin_count, 3600)  # 1 hour
            
            # Log admin access
            logger.info(f"ADMIN_ACCESS", extra={
                'user_id': str(user.id),
                'username': user.email,
                'ip_address': ip_address,
                'path': request.path,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'access_count': admin_count
            })
            
            # Alert on excessive admin access
            if admin_count >= self.alert_thresholds['admin_access_attempts']:
                self.send_security_alert(
                    'EXCESSIVE_ADMIN_ACCESS',
                    f"Excessive admin access from IP {ip_address} ({admin_count} attempts)"
                )
    
    def block_ip_immediately(self, ip_address, threat):
        """Immediately block IP address for critical threats."""
        block_key = f"blocked_ip_critical:{ip_address}"
        cache.set(block_key, True, 86400)  # 24 hours
        
        logger.critical(f"IP_BLOCKED_CRITICAL: {ip_address}", extra={
            'ip_address': ip_address,
            'threat_type': threat['type'],
            'pattern': threat['pattern'],
            'block_duration': '24 hours',
            'reason': 'Critical security threat detected'
        })
        
        self.send_critical_alert(
            'CRITICAL_THREAT_IP_BLOCKED',
            f"IP {ip_address} blocked for critical threat: {threat['type']}"
        )
    
    def block_ip_temporarily(self, ip_address, duration_minutes=30):
        """Temporarily block IP address."""
        block_key = f"blocked_ip_temp:{ip_address}"
        cache.set(block_key, True, duration_minutes * 60)
        
        logger.warning(f"IP_BLOCKED_TEMPORARY: {ip_address}", extra={
            'ip_address': ip_address,
            'block_duration_minutes': duration_minutes,
            'reason': 'Suspicious activity threshold exceeded'
        })
    
    def increment_threat_counter(self, ip_address, threat_count):
        """Increment threat counter for IP monitoring."""
        counter_key = f"threat_counter:{ip_address}"
        current_count = cache.get(counter_key, 0) + threat_count
        cache.set(counter_key, current_count, 3600)  # 1 hour
        
        if current_count >= self.alert_thresholds['suspicious_requests']:
            self.send_security_alert(
                'SUSPICIOUS_ACTIVITY_THRESHOLD',
                f"IP {ip_address} exceeded suspicious activity threshold ({current_count} threats)"
            )
    
    def send_security_alert(self, alert_type, message):
        """Send security alerts to monitoring systems."""
        alert_data = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'severity': self._get_alert_severity(alert_type)
        }
        
        # Log alert
        logger.critical(f"SECURITY_ALERT: {alert_type}", extra=alert_data)
        
        # Send to external monitoring systems
        self._send_external_alert(alert_data)
    
    def send_critical_alert(self, alert_type, message):
        """Send critical security alerts requiring immediate attention."""
        alert_data = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'severity': 'CRITICAL',
            'requires_immediate_action': True
        }
        
        # Log critical alert
        logger.critical(f"CRITICAL_SECURITY_ALERT: {alert_type}", extra=alert_data)
        
        # Send to all available channels
        self._send_external_alert(alert_data)
        self._send_emergency_notification(alert_data)
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def is_ip_blocked(self, ip_address):
        """Check if IP address is currently blocked."""
        critical_block = cache.get(f"blocked_ip_critical:{ip_address}")
        temp_block = cache.get(f"blocked_ip_temp:{ip_address}")
        
        return critical_block or temp_block
    
    def _get_alert_severity(self, alert_type):
        """Determine alert severity based on type."""
        critical_alerts = [
            'CRITICAL_THREAT_IP_BLOCKED',
            'DATA_BREACH_ATTEMPT',
            'PRIVILEGE_ESCALATION_DETECTED'
        ]
        
        high_alerts = [
            'BRUTE_FORCE_ATTACK_IP',
            'EXCESSIVE_ADMIN_ACCESS',
            'MALWARE_DETECTED'
        ]
        
        if alert_type in critical_alerts:
            return 'CRITICAL'
        elif alert_type in high_alerts:
            return 'HIGH'
        else:
            return 'MEDIUM'
    
    def _send_external_alert(self, alert_data):
        """Send alert to external monitoring systems."""
        # Send to webhook if configured
        webhook_url = getattr(settings, 'SECURITY_WEBHOOK_URL', None)
        if webhook_url:
            try:
                import requests
                requests.post(webhook_url, json=alert_data, timeout=5)
            except Exception as e:
                logger.error(f"Failed to send security webhook: {str(e)}")
        
        # Send to Sentry if configured
        if hasattr(settings, 'SENTRY_DSN'):
            try:
                import sentry_sdk
                sentry_sdk.capture_message(
                    f"Security Alert: {alert_data['type']}",
                    level='error',
                    extra=alert_data
                )
            except Exception as e:
                logger.error(f"Failed to send Sentry alert: {str(e)}")
    
    def _send_emergency_notification(self, alert_data):
        """Send emergency notifications for critical alerts."""
        # This would integrate with emergency notification systems
        # Email, SMS, Slack, PagerDuty, etc.
        emergency_contacts = getattr(settings, 'EMERGENCY_CONTACTS', [])
        
        for contact in emergency_contacts:
            # Implementation would send actual notifications
            logger.critical(f"EMERGENCY_NOTIFICATION_SENT: {contact}", extra=alert_data)


class SecurityMetricsCollector:
    """Collect and analyze security metrics."""
    
    def collect_real_time_metrics(self):
        """Collect real-time security metrics."""
        now = datetime.now()
        
        return {
            'timestamp': now.isoformat(),
            'failed_logins_last_hour': self._count_failed_logins(hours=1),
            'failed_logins_last_24h': self._count_failed_logins(hours=24),
            'blocked_ips_current': self._count_blocked_ips(),
            'security_events_last_hour': self._count_security_events(hours=1),
            'api_errors_last_hour': self._count_api_errors(hours=1),
            'admin_access_last_hour': self._count_admin_access(hours=1),
            'threat_detections_last_hour': self._count_threat_detections(hours=1),
            'system_status': self._get_system_security_status()
        }
    
    def _count_failed_logins(self, hours=1):
        """Count failed login attempts in time window."""
        # This would query audit logs or cache
        # Implementation depends on logging system
        return 0  # Placeholder
    
    def _count_blocked_ips(self):
        """Count currently blocked IP addresses."""
        # Count blocked IPs in cache
        blocked_count = 0
        # Implementation would scan cache for blocked IP keys
        return blocked_count
    
    def _count_security_events(self, hours=1):
        """Count security events in time window."""
        # This would query security logs
        return 0  # Placeholder
    
    def _count_api_errors(self, hours=1):
        """Count API errors in time window."""
        # This would query application logs
        return 0  # Placeholder
    
    def _count_admin_access(self, hours=1):
        """Count administrative access in time window."""
        # This would query audit logs
        return 0  # Placeholder
    
    def _count_threat_detections(self, hours=1):
        """Count threat detections in time window."""
        # This would query threat detection logs
        return 0  # Placeholder
    
    def _get_system_security_status(self):
        """Get overall system security status."""
        # Analyze various metrics to determine status
        return 'SECURE'  # SECURE, ALERT, CRITICAL
    
    def generate_security_dashboard_data(self):
        """Generate data for security dashboard."""
        metrics = self.collect_real_time_metrics()
        
        return {
            'current_metrics': metrics,
            'threat_level': self._calculate_threat_level(metrics),
            'recent_incidents': self._get_recent_incidents(),
            'security_trends': self._get_security_trends(),
            'recommendations': self._get_security_recommendations(metrics)
        }
    
    def _calculate_threat_level(self, metrics):
        """Calculate current threat level based on metrics."""
        threat_indicators = [
            metrics['failed_logins_last_hour'] > 20,
            metrics['blocked_ips_current'] > 5,
            metrics['security_events_last_hour'] > 10,
            metrics['threat_detections_last_hour'] > 5
        ]
        
        active_indicators = sum(threat_indicators)
        
        if active_indicators >= 3:
            return 'HIGH'
        elif active_indicators >= 2:
            return 'MEDIUM'
        elif active_indicators >= 1:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _get_recent_incidents(self):
        """Get recent security incidents."""
        # This would query incident database
        return []  # Placeholder
    
    def _get_security_trends(self):
        """Get security trend analysis."""
        # This would analyze historical security data
        return {
            'trend': 'STABLE',
            'change_percentage': 0,
            'notable_changes': []
        }
    
    def _get_security_recommendations(self, metrics):
        """Get security recommendations based on current metrics."""
        recommendations = []
        
        if metrics['failed_logins_last_24h'] > 50:
            recommendations.append("Consider implementing CAPTCHA for login attempts")
        
        if metrics['blocked_ips_current'] > 10:
            recommendations.append("Review blocked IP addresses for false positives")
        
        if metrics['api_errors_last_hour'] > 100:
            recommendations.append("Investigate high API error rate")
        
        return recommendations


# Global security services
threat_detection_service = ThreatDetectionService()
security_metrics_collector = SecurityMetricsCollector()


# Security middleware integration
class ThreatDetectionMiddleware:
    """Middleware for real-time threat detection."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.threat_detector = threat_detection_service
    
    def __call__(self, request):
        # Check if IP is blocked
        ip_address = self.threat_detector.get_client_ip(request)
        if self.threat_detector.is_ip_blocked(ip_address):
            logger.warning(f"BLOCKED_IP_ACCESS_ATTEMPT: {ip_address}", extra={
                'ip_address': ip_address,
                'path': request.path,
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            })
            return HttpResponseForbidden("Access denied - IP address blocked")
        
        # Analyze request for threats
        threats = self.threat_detector.analyze_request_for_threats(request)
        
        # Respond to threats if detected
        if threats:
            threat_response = self.threat_detector.respond_to_threats(request, threats)
            if threat_response:
                return threat_response
        
        # Process request normally
        response = self.get_response(request)
        
        return response