"""
Security Headers Configuration
Team Delta - Security Sprint 4
"""

from django.conf import settings

# Security Headers Configuration
SECURITY_HEADERS = {
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:; frame-ancestors 'none';",
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
    'Pragma': 'no-cache',
    'Expires': '0',
}

# Content Security Policy for different environments
CSP_POLICIES = {
    'development': {
        'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        'style-src': ["'self'", "'unsafe-inline'"],
        'img-src': ["'self'", "data:", "https:"],
        'font-src': ["'self'", "https:"],
        'connect-src': ["'self'", "https:", "ws:", "wss:"],
    },
    'production': {
        'script-src': ["'self'"],
        'style-src': ["'self'", "'unsafe-inline'"],
        'img-src': ["'self'", "https:"],
        'font-src': ["'self'", "https:"],
        'connect-src': ["'self'", "https:"],
    }
}

# Rate Limiting Configuration
RATE_LIMIT_CONFIG = {
    'default': '100/minute',
    'api': '1000/minute',
    'auth': '5/minute',
    'upload': '10/minute',
    'admin': '1000/minute',
}

# Input Validation Rules
INPUT_VALIDATION_RULES = {
    'sql_injection': {
        'enabled': True,
        'patterns': [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(\b(script|javascript|vbscript|onload|onerror)\b)",
            r"(--|#|/\*|\*/)",
        ],
        'action': 'block'
    },
    'xss': {
        'enabled': True,
        'patterns': [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
        ],
        'action': 'sanitize'
    },
    'path_traversal': {
        'enabled': True,
        'patterns': [
            r"\.\./",
            r"\.\.\\",
            r"//",
            r"\\\\",
        ],
        'action': 'block'
    }
}

# Security Middleware Configuration
SECURITY_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

# Security Settings
SECURITY_SETTINGS = {
    'SECURE_BROWSER_XSS_FILTER': True,
    'SECURE_CONTENT_TYPE_NOSNIFF': True,
    'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
    'SECURE_HSTS_PRELOAD': True,
    'SECURE_HSTS_SECONDS': 31536000,
    'SECURE_REDIRECT_EXEMPT': [],
    'SECURE_SSL_HOST': None,
    'SECURE_SSL_REDIRECT': False,
    'SESSION_COOKIE_SECURE': True,
    'CSRF_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'CSRF_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'CSRF_COOKIE_SAMESITE': 'Lax',
    'SESSION_EXPIRE_AT_BROWSER_CLOSE': True,
    'SESSION_COOKIE_AGE': 3600,  # 1 hour
    'PASSWORD_HASHERS': [
        'django.contrib.auth.hashers.Argon2PasswordHasher',
        'django.contrib.auth.hashers.PBKDF2PasswordHasher',
        'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    ],
    'AUTH_PASSWORD_VALIDATORS': [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            'OPTIONS': {
                'min_length': 12,
            }
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ],
}
