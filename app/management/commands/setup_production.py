"""
Django management command for production setup.
Handles initial production environment configuration.

Created by Team Alpha (Infrastructure & DevOps) for Sprint 6
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings
import os
import secrets
import string

from app.django_models import Role, Permission, SystemConfiguration

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up production environment with initial configuration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Create initial superuser account',
        )
        parser.add_argument(
            '--setup-rbac',
            action='store_true',
            help='Set up initial RBAC roles and permissions',
        )
        parser.add_argument(
            '--validate-config',
            action='store_true',
            help='Validate production configuration',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all setup tasks',
        )
    
    def handle(self, *args, **options):
        """Execute production setup tasks."""
        
        if options['all']:
            options['create_superuser'] = True
            options['setup_rbac'] = True
            options['validate_config'] = True
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting production environment setup...')
        )
        
        if options['validate_config']:
            self._validate_configuration()
        
        if options['setup_rbac']:
            self._setup_rbac_system()
        
        if options['create_superuser']:
            self._create_superuser()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Production setup completed successfully!')
        )
    
    def _validate_configuration(self):
        """Validate production configuration."""
        self.stdout.write('🔍 Validating production configuration...')
        
        errors = []
        warnings = []
        
        # Check SECRET_KEY
        if settings.SECRET_KEY == 'django-insecure-change-me':
            errors.append('SECRET_KEY is using default insecure value')
        elif len(settings.SECRET_KEY) < 50:
            warnings.append('SECRET_KEY should be at least 50 characters long')
        
        # Check DEBUG setting
        if settings.DEBUG:
            errors.append('DEBUG must be False in production')
        
        # Check database configuration
        db_config = settings.DATABASES['default']
        if db_config['PASSWORD'] == 'postgres':
            warnings.append('Using default database password')
        
        # Check ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['localhost']:
            warnings.append('ALLOWED_HOSTS should be configured for production')
        
        # Check security settings
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            warnings.append('SECURE_SSL_REDIRECT should be True in production')
        
        # Report results
        if errors:
            for error in errors:
                self.stdout.write(self.style.ERROR(f'❌ ERROR: {error}'))
            raise CommandError('Configuration validation failed')
        
        if warnings:
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'⚠️  WARNING: {warning}'))
        
        self.stdout.write(self.style.SUCCESS('✅ Configuration validation passed'))
    
    def _setup_rbac_system(self):
        """Set up initial RBAC roles and permissions."""
        self.stdout.write('🔐 Setting up RBAC system...')
        
        with transaction.atomic():
            # Create basic permissions
            permissions_data = [
                ('view_account', 'account', 'view', 'Can view accounts'),
                ('create_account', 'account', 'create', 'Can create accounts'),
                ('update_account', 'account', 'update', 'Can update accounts'),
                ('delete_account', 'account', 'delete', 'Can delete accounts'),
                
                ('view_transaction', 'transaction', 'view', 'Can view transactions'),
                ('create_transaction', 'transaction', 'create', 'Can create transactions'),
                ('update_transaction', 'transaction', 'update', 'Can update transactions'),
                ('delete_transaction', 'transaction', 'delete', 'Can delete transactions'),
                
                ('view_budget', 'budget', 'view', 'Can view budgets'),
                ('create_budget', 'budget', 'create', 'Can create budgets'),
                ('update_budget', 'budget', 'update', 'Can update budgets'),
                ('delete_budget', 'budget', 'delete', 'Can delete budgets'),
                
                ('view_reports', 'report', 'view', 'Can view reports'),
                ('manage_users', 'user', 'manage', 'Can manage users'),
                ('view_audit_logs', 'audit', 'view', 'Can view audit logs'),
            ]
            
            created_permissions = {}
            for name, resource, action, description in permissions_data:
                permission, created = Permission.objects.get_or_create(
                    name=name,
                    defaults={
                        'resource': resource,
                        'action': action,
                        'description': description
                    }
                )
                created_permissions[name] = permission
                if created:
                    self.stdout.write(f'  ✅ Created permission: {name}')
            
            # Create basic roles
            roles_data = [
                ('User', 'Basic user role', [
                    'view_account', 'create_account', 'update_account',
                    'view_transaction', 'create_transaction', 'update_transaction',
                    'view_budget', 'create_budget', 'update_budget'
                ]),
                ('Manager', 'Manager role with additional permissions', [
                    'view_account', 'create_account', 'update_account', 'delete_account',
                    'view_transaction', 'create_transaction', 'update_transaction', 'delete_transaction',
                    'view_budget', 'create_budget', 'update_budget', 'delete_budget',
                    'view_reports'
                ]),
                ('Admin', 'Administrator role with full permissions', [
                    'view_account', 'create_account', 'update_account', 'delete_account',
                    'view_transaction', 'create_transaction', 'update_transaction', 'delete_transaction',
                    'view_budget', 'create_budget', 'update_budget', 'delete_budget',
                    'view_reports', 'manage_users', 'view_audit_logs'
                ])
            ]
            
            for role_name, description, permission_names in roles_data:
                role, created = Role.objects.get_or_create(
                    name=role_name,
                    defaults={'description': description}
                )
                
                if created:
                    # Add permissions to role
                    role_permissions = [created_permissions[name] for name in permission_names]
                    role.permissions.set(role_permissions)
                    self.stdout.write(f'  ✅ Created role: {role_name} with {len(role_permissions)} permissions')
        
        self.stdout.write(self.style.SUCCESS('✅ RBAC system setup completed'))
    
    def _create_superuser(self):
        """Create initial superuser if it doesn't exist."""
        self.stdout.write('👤 Setting up superuser account...')
        
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        
        if not admin_password:
            # Generate secure password
            alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
            admin_password = ''.join(secrets.choice(alphabet) for _ in range(16))
            
            self.stdout.write(
                self.style.WARNING(f'⚠️  Generated admin password: {admin_password}')
            )
            self.stdout.write(
                self.style.WARNING('⚠️  Please save this password securely!')
            )
        
        if not User.objects.filter(email=admin_email).exists():
            superuser = User.objects.create_superuser(
                email=admin_email,
                username=admin_email,
                first_name='System',
                last_name='Administrator',
                password=admin_password
            )
            
            # Assign Admin role if RBAC is set up
            try:
                admin_role = Role.objects.get(name='Admin')
                superuser.roles.add(admin_role)
                self.stdout.write(f'  ✅ Assigned Admin role to superuser')
            except Role.DoesNotExist:
                pass
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created superuser: {admin_email}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Superuser already exists: {admin_email}')
            )