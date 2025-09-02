"""
Enhanced security validators for the Financial Stronghold application.
Provides comprehensive input validation and security controls.

Created based on penetration test findings.
"""

import re
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import BaseValidator
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger('security')


class SecurityValidators:
    """Enhanced security validators for financial application."""
    
    @staticmethod
    def validate_transaction_description(value):
        """Enhanced validation for transaction descriptions."""
        if not value:
            return value
        
        # Length validation
        if len(value) > 500:
            raise ValidationError(_("Description too long (maximum 500 characters)"))
        
        # Check for script injection attempts
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
            r'onmouseover\s*=',
            r'onfocus\s*=',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"XSS_ATTEMPT_BLOCKED: Pattern '{pattern}' in description", extra={
                    'input_value': value[:100],  # Log first 100 chars
                    'validation_type': 'transaction_description'
                })
                raise ValidationError(_("Invalid characters detected in description"))
        
        # Check for SQL injection patterns
        sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+.*set',
            r'or\s+1\s*=\s*1',
            r'and\s+1\s*=\s*1',
            r'having\s+1\s*=\s*1',
            r'exec\s*\(',
            r'sp_\w+',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.critical(f"SQL_INJECTION_ATTEMPT_BLOCKED: Pattern '{pattern}' in description", extra={
                    'input_value': value[:100],
                    'validation_type': 'transaction_description'
                })
                raise ValidationError(_("Invalid characters detected in description"))
        
        # Check for path traversal attempts
        path_traversal_patterns = [
            r'\.\./+',
            r'\.\.\\+',
            r'%2e%2e%2f',
            r'%2e%2e%5c',
            r'\.\.%2f',
            r'\.\.%5c',
        ]
        
        for pattern in path_traversal_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"PATH_TRAVERSAL_ATTEMPT_BLOCKED: Pattern '{pattern}' in description", extra={
                    'input_value': value[:100],
                    'validation_type': 'transaction_description'
                })
                raise ValidationError(_("Invalid characters detected in description"))
        
        return value.strip()
    
    @staticmethod
    def validate_account_name(value):
        """Validate account names for security and business rules."""
        if not value:
            raise ValidationError(_("Account name is required"))
        
        # Length validation
        if len(value) > 100:
            raise ValidationError(_("Account name too long (maximum 100 characters)"))
        
        if len(value.strip()) < 2:
            raise ValidationError(_("Account name too short (minimum 2 characters)"))
        
        # Character validation (allow alphanumeric, spaces, hyphens, underscores, periods)
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', value):
            logger.warning(f"INVALID_ACCOUNT_NAME_BLOCKED: {value}", extra={
                'validation_type': 'account_name'
            })
            raise ValidationError(_("Account name contains invalid characters"))
        
        # Business rule validation
        forbidden_names = [
            'admin', 'administrator', 'root', 'system', 'test',
            'null', 'undefined', 'void', 'temp', 'temporary'
        ]
        
        if value.lower().strip() in forbidden_names:
            raise ValidationError(_("Account name is reserved"))
        
        return value.strip()
    
    @staticmethod
    def validate_transaction_amount(value):
        """Validate transaction amounts with comprehensive business rules."""
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            raise ValidationError(_("Invalid amount format"))
        
        # Business rule validation
        if amount == 0:
            raise ValidationError(_("Transaction amount cannot be zero"))
        
        # Reasonable limits for financial transactions
        max_amount = Decimal('10000000')  # $10M limit
        min_amount = Decimal('0.01')      # 1 cent minimum
        
        if abs(amount) > max_amount:
            logger.warning(f"LARGE_TRANSACTION_BLOCKED: Amount {amount}", extra={
                'validation_type': 'transaction_amount',
                'amount': str(amount)
            })
            raise ValidationError(_("Transaction amount exceeds maximum limit ($10,000,000)"))
        
        if abs(amount) < min_amount:
            raise ValidationError(_("Transaction amount below minimum (1 cent)"))
        
        # Check for suspicious round numbers (potential fraud indicator)
        if abs(amount) >= 1000 and amount % 100 == 0:
            logger.info(f"ROUND_AMOUNT_DETECTED: {amount}", extra={
                'validation_type': 'transaction_amount',
                'amount': str(amount),
                'note': 'Suspicious round amount detected'
            })
        
        return amount
    
    @staticmethod
    def validate_email_security(email):
        """Enhanced email validation with security checks."""
        if not email:
            raise ValidationError(_("Email is required"))
        
        # Length validation
        if len(email) > 254:  # RFC 5321 limit
            raise ValidationError(_("Email address too long"))
        
        # Basic format validation (Django's EmailValidator handles most cases)
        from django.core.validators import validate_email
        validate_email(email)
        
        # Security-specific validation
        # Check for suspicious patterns
        suspicious_patterns = [
            r'[<>"\']',           # HTML/script characters
            r'javascript:',        # JavaScript protocol
            r'data:',             # Data protocol
            r'\s',                # Whitespace (not allowed in email)
            r'[^\x00-\x7F]',      # Non-ASCII characters (potential spoofing)
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                logger.warning(f"SUSPICIOUS_EMAIL_BLOCKED: {email}", extra={
                    'validation_type': 'email',
                    'pattern': pattern
                })
                raise ValidationError(_("Email contains invalid characters"))
        
        # Check for disposable email domains (basic list)
        disposable_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com'
        ]
        
        email_domain = email.split('@')[-1].lower()
        if email_domain in disposable_domains:
            logger.info(f"DISPOSABLE_EMAIL_DETECTED: {email}", extra={
                'validation_type': 'email',
                'domain': email_domain
            })
            # Don't block, but log for monitoring
        
        return email.lower().strip()


class EnhancedPasswordValidator(BaseValidator):
    """Enhanced password validation for financial application security."""
    
    def __init__(self, min_length=12):
        self.min_length = min_length
    
    def validate(self, password, user=None):
        """Comprehensive password validation."""
        errors = []
        
        # Length requirement
        if len(password) < self.min_length:
            errors.append(_(f"Password must be at least {self.min_length} characters long"))
        
        # Character requirements
        if not any(c.isupper() for c in password):
            errors.append(_("Password must contain at least one uppercase letter"))
        
        if not any(c.islower() for c in password):
            errors.append(_("Password must contain at least one lowercase letter"))
        
        if not any(c.isdigit() for c in password):
            errors.append(_("Password must contain at least one number"))
        
        special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        if not any(c in special_chars for c in password):
            errors.append(_("Password must contain at least one special character"))
        
        # Check against common weak passwords
        weak_passwords = [
            'password123', 'admin123', 'qwerty123', 'abc123456',
            'password1', 'welcome123', 'changeme123', 'temp123456'
        ]
        
        if password.lower() in [p.lower() for p in weak_passwords]:
            errors.append(_("Password is too common and easily guessable"))
        
        # Check for user information in password (if user provided)
        if user:
            user_info = [
                getattr(user, 'username', ''),
                getattr(user, 'email', '').split('@')[0],
                getattr(user, 'first_name', ''),
                getattr(user, 'last_name', ''),
            ]
            
            for info in user_info:
                if info and len(info) > 2 and info.lower() in password.lower():
                    errors.append(_("Password cannot contain personal information"))
                    break
        
        # Check for repeated characters
        if len(set(password)) < len(password) * 0.6:  # Less than 60% unique characters
            errors.append(_("Password has too many repeated characters"))
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        return _(
            f"Your password must be at least {self.min_length} characters long and contain "
            "at least one uppercase letter, one lowercase letter, one number, and one special character."
        )


class BusinessRuleValidators:
    """Business rule validators specific to financial application."""
    
    @staticmethod
    def validate_budget_amount(amount, currency='USD'):
        """Validate budget amounts with business rules."""
        try:
            budget_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            raise ValidationError(_("Invalid budget amount format"))
        
        if budget_amount <= 0:
            raise ValidationError(_("Budget amount must be positive"))
        
        # Reasonable budget limits
        max_budget = Decimal('1000000')  # $1M budget limit
        if budget_amount > max_budget:
            raise ValidationError(_("Budget amount exceeds maximum limit"))
        
        return budget_amount
    
    @staticmethod
    def validate_date_range(start_date, end_date):
        """Validate date ranges for budgets and reports."""
        if start_date >= end_date:
            raise ValidationError(_("End date must be after start date"))
        
        # Check for reasonable date ranges
        from datetime import timedelta
        max_range = timedelta(days=3650)  # 10 years
        
        if (end_date - start_date) > max_range:
            raise ValidationError(_("Date range too large (maximum 10 years)"))
        
        return start_date, end_date