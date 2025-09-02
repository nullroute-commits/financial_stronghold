"""
Input Validation Configuration
Team Delta - Security Sprint 4
"""

import re
import html
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

class SecurityValidator:
    """Comprehensive input validation and sanitization"""
    
    def __init__(self):
        self.sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(\b(script|javascript|vbscript|onload|onerror)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(declare|cast|convert|exec|execute|fetch|open|close|deallocate|print|raiserror|waitfor|delay|shutdown)\b)",
        ]
        
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<form[^>]*>",
            r"<input[^>]*>",
            r"<textarea[^>]*>",
            r"<button[^>]*>",
            r"<select[^>]*>",
        ]
        
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"//",
            r"\\\\",
            r"\.\.%2f",
            r"\.\.%5c",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
        ]
        
        self.command_injection_patterns = [
            r"[;&|`$()]",
            r"\b(cat|chmod|curl|wget|nc|netcat|bash|sh|python|perl|ruby|php)\b",
            r"\b(rm|del|erase|format|fdisk|mkfs|dd|cp|mv|ln)\b",
        ]
    
    def validate_and_sanitize(self, value, validation_type='strict'):
        """Validate and sanitize input based on type"""
        if not value:
            return value
        
        # Convert to string if needed
        if not isinstance(value, str):
            value = str(value)
        
        # Apply validation based on type
        if validation_type == 'strict':
            value = self.strict_validation(value)
        elif validation_type == 'moderate':
            value = self.moderate_validation(value)
        elif validation_type == 'permissive':
            value = self.permissive_validation(value)
        
        return value
    
    def strict_validation(self, value):
        """Strict validation - block suspicious patterns"""
        # Check for SQL injection
        if self.contains_sql_injection(value):
            raise ValidationError("Input contains potentially dangerous SQL patterns")
        
        # Check for XSS
        if self.contains_xss(value):
            raise ValidationError("Input contains potentially dangerous XSS patterns")
        
        # Check for path traversal
        if self.contains_path_traversal(value):
            raise ValidationError("Input contains potentially dangerous path traversal patterns")
        
        # Check for command injection
        if self.contains_command_injection(value):
            raise ValidationError("Input contains potentially dangerous command injection patterns")
        
        # HTML escape for safety
        return html.escape(value)
    
    def moderate_validation(self, value):
        """Moderate validation - sanitize suspicious patterns"""
        # Remove dangerous patterns
        value = self.remove_sql_injection(value)
        value = self.remove_xss(value)
        value = self.remove_path_traversal(value)
        value = self.remove_command_injection(value)
        
        # HTML escape for safety
        return html.escape(value)
    
    def permissive_validation(self, value):
        """Permissive validation - minimal sanitization"""
        # Only HTML escape
        return html.escape(value)
    
    def contains_sql_injection(self, value):
        """Check for SQL injection patterns"""
        for pattern in self.sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def contains_xss(self, value):
        """Check for XSS patterns"""
        for pattern in self.xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def contains_path_traversal(self, value):
        """Check for path traversal patterns"""
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def contains_command_injection(self, value):
        """Check for command injection patterns"""
        for pattern in self.command_injection_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def remove_sql_injection(self, value):
        """Remove SQL injection patterns"""
        for pattern in self.sql_patterns:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        return value
    
    def remove_xss(self, value):
        """Remove XSS patterns"""
        for pattern in self.xss_patterns:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        return value
    
    def remove_path_traversal(self, value):
        """Remove path traversal patterns"""
        for pattern in self.path_traversal_patterns:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        return value
    
    def remove_command_injection(self, value):
        """Remove command injection patterns"""
        for pattern in self.command_injection_patterns:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        return value

# Global validator instance
security_validator = SecurityValidator()

# Validation decorator for views
def validate_input(validation_type='strict'):
    """Decorator to validate input in views"""
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            # Validate GET parameters
            for key, value in request.GET.items():
                try:
                    sanitized_value = security_validator.validate_and_sanitize(value, validation_type)
                    request.GET = request.GET.copy()
                    request.GET[key] = sanitized_value
                except ValidationError as e:
                    return HttpResponseBadRequest(f"Invalid input in GET parameter '{key}': {e}")
            
            # Validate POST parameters
            if request.method == 'POST':
                for key, value in request.POST.items():
                    try:
                        sanitized_value = security_validator.validate_and_sanitize(value, validation_type)
                        request.POST = request.POST.copy()
                        request.POST[key] = sanitized_value
                    except ValidationError as e:
                        return HttpResponseBadRequest(f"Invalid input in POST parameter '{key}': {e}")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator
