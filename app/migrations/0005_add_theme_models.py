"""
Migration to add theme customization models.

Created by: Team Alpha (Atlas & Athena)
Date: 2025-01-02
"""

from django.db import migrations, models
import django.db.models.deletion
import django.contrib.postgres.fields.jsonb
import uuid


def create_default_templates(apps, schema_editor):
    """Create default theme templates."""
    ThemeTemplate = apps.get_model('app', 'ThemeTemplate')
    User = apps.get_model('app', 'User')
    
    # Get system user or skip if not exists
    system_user = User.objects.filter(email='system@financialstronghold.com').first()
    if not system_user:
        return
    
    templates = [
        {
            'name': 'Ocean Breeze',
            'description': 'A calming blue theme inspired by the ocean',
            'category': 'light',
            'is_featured': True,
            'theme_data': {
                'colors': {
                    'primary': '#006994',
                    'secondary': '#40A9FF',
                    'success': '#52C41A',
                    'danger': '#FF4D4F',
                    'warning': '#FAAD14',
                    'info': '#1890FF',
                    'light': '#F0F2F5',
                    'dark': '#001529',
                    'background': '#FFFFFF',
                    'surface': '#FAFAFA',
                    'text-primary': '#262626',
                    'text-secondary': '#8C8C8C'
                }
            }
        },
        {
            'name': 'Midnight Dark',
            'description': 'A sophisticated dark theme for reduced eye strain',
            'category': 'dark',
            'is_featured': True,
            'theme_data': {
                'colors': {
                    'primary': '#177DDC',
                    'secondary': '#5A5A5A',
                    'success': '#49AA19',
                    'danger': '#A8071A',
                    'warning': '#D89614',
                    'info': '#1890FF',
                    'light': '#1F1F1F',
                    'dark': '#000000',
                    'background': '#141414',
                    'surface': '#1F1F1F',
                    'text-primary': '#FFFFFF',
                    'text-secondary': '#BFBFBF'
                }
            }
        },
        {
            'name': 'Forest Green',
            'description': 'A nature-inspired theme with calming green tones',
            'category': 'colorful',
            'theme_data': {
                'colors': {
                    'primary': '#237804',
                    'secondary': '#52C41A',
                    'success': '#389E0D',
                    'danger': '#CF1322',
                    'warning': '#FA8C16',
                    'info': '#13C2C2',
                    'light': '#F6FFED',
                    'dark': '#092B00',
                    'background': '#FFFFFF',
                    'surface': '#F6FFED',
                    'text-primary': '#262626',
                    'text-secondary': '#595959'
                }
            }
        },
        {
            'name': 'High Contrast',
            'description': 'Maximum contrast for improved accessibility',
            'category': 'high_contrast',
            'theme_data': {
                'colors': {
                    'primary': '#0000FF',
                    'secondary': '#800080',
                    'success': '#008000',
                    'danger': '#FF0000',
                    'warning': '#FFD700',
                    'info': '#00FFFF',
                    'light': '#FFFFFF',
                    'dark': '#000000',
                    'background': '#FFFFFF',
                    'surface': '#F0F0F0',
                    'text-primary': '#000000',
                    'text-secondary': '#404040'
                }
            }
        },
        {
            'name': 'Minimal Gray',
            'description': 'A clean, minimal theme with subtle gray tones',
            'category': 'minimal',
            'theme_data': {
                'colors': {
                    'primary': '#595959',
                    'secondary': '#8C8C8C',
                    'success': '#52C41A',
                    'danger': '#FF4D4F',
                    'warning': '#FAAD14',
                    'info': '#1890FF',
                    'light': '#FAFAFA',
                    'dark': '#262626',
                    'background': '#FFFFFF',
                    'surface': '#F5F5F5',
                    'text-primary': '#262626',
                    'text-secondary': '#8C8C8C'
                }
            }
        }
    ]
    
    for template_data in templates:
        # Add created_by field
        template_data['created_by'] = system_user
        # Set default theme_data structure
        if 'theme_data' in template_data and 'colors' in template_data['theme_data']:
            # Extend with full theme structure
            template_data['theme_data'].update({
                'typography': {
                    'font-family-base': "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
                    'font-size-base': '1rem',
                    'line-height-base': '1.5',
                    'headings-font-weight': '500'
                },
                'spacing': {
                    'spacer': '1rem',
                    'container-padding': '1.5rem'
                },
                'borders': {
                    'radius': '0.375rem',
                    'width': '1px'
                },
                'shadows': {
                    'sm': '0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)',
                    'default': '0 0.5rem 1rem rgba(0, 0, 0, 0.15)',
                    'lg': '0 1rem 3rem rgba(0, 0, 0, 0.175)'
                }
            })
        
        ThemeTemplate.objects.create(**template_data)


def reverse_create_default_templates(apps, schema_editor):
    """Remove default templates."""
    ThemeTemplate = apps.get_model('app', 'ThemeTemplate')
    ThemeTemplate.objects.filter(
        name__in=['Ocean Breeze', 'Midnight Dark', 'Forest Green', 'High Contrast', 'Minimal Gray']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_add_import_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='ThemeTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(help_text='Template name', max_length=100, unique=True)),
                ('description', models.TextField(help_text='Description of the theme template')),
                ('category', models.CharField(choices=[('light', 'Light'), ('dark', 'Dark'), ('high_contrast', 'High Contrast'), ('colorful', 'Colorful'), ('minimal', 'Minimal'), ('custom', 'Custom')], default='light', max_length=20)),
                ('theme_data', django.contrib.postgres.fields.jsonb.JSONField(default=dict, help_text='JSON structure containing theme configuration')),
                ('preview_image', models.URLField(blank=True, help_text='URL to theme preview image', null=True)),
                ('is_public', models.BooleanField(default=True, help_text='Whether this template is available to all users')),
                ('is_featured', models.BooleanField(default=False, help_text='Whether to feature this template')),
                ('usage_count', models.IntegerField(default=0, help_text='Number of times this template has been used')),
                ('version', models.CharField(default='1.0', max_length=10)),
                ('tags', models.CharField(blank=True, help_text='Comma-separated tags for searching', max_length=200)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='themetemplate_created', to='app.user')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='themetemplate_updated', to='app.user')),
            ],
            options={
                'db_table': 'theme_templates',
                'ordering': ['-is_featured', '-usage_count', 'name'],
            },
        ),
        migrations.CreateModel(
            name='UserThemePreference',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(help_text='User-friendly name for the theme', max_length=100)),
                ('description', models.TextField(blank=True, help_text='Optional description of the theme')),
                ('category', models.CharField(choices=[('light', 'Light'), ('dark', 'Dark'), ('high_contrast', 'High Contrast'), ('colorful', 'Colorful'), ('minimal', 'Minimal'), ('custom', 'Custom')], default='custom', max_length=20)),
                ('is_active', models.BooleanField(default=False, help_text='Whether this theme is currently active for the user')),
                ('is_default', models.BooleanField(default=False, help_text="Whether this is the user's default theme")),
                ('theme_data', django.contrib.postgres.fields.jsonb.JSONField(default=dict, help_text='JSON structure containing theme configuration')),
                ('version', models.CharField(default='1.0', help_text='Theme version for compatibility', max_length=10)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='userthemepreference_created', to='app.user')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='userthemepreference_updated', to='app.user')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='theme_preferences', to='app.user')),
            ],
            options={
                'db_table': 'user_theme_preferences',
                'ordering': ['-is_active', '-is_default', '-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='ThemeAuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('action', models.CharField(choices=[('created', 'Theme Created'), ('updated', 'Theme Updated'), ('activated', 'Theme Activated'), ('deactivated', 'Theme Deactivated'), ('deleted', 'Theme Deleted'), ('imported', 'Theme Imported'), ('exported', 'Theme Exported'), ('shared', 'Theme Shared')], max_length=20)),
                ('details', django.contrib.postgres.fields.jsonb.JSONField(default=dict, help_text='Additional details about the action')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='themeauditlog_created', to='app.user')),
                ('theme', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to='app.userthemepreference')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='themeauditlog_updated', to='app.user')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='theme_audit_logs', to='app.user')),
            ],
            options={
                'db_table': 'theme_audit_logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='userthemepreference',
            index=models.Index(fields=['user', 'is_active'], name='app_userthem_user_id_7a8c3a_idx'),
        ),
        migrations.AddIndex(
            model_name='userthemepreference',
            index=models.Index(fields=['user', 'name'], name='app_userthem_user_id_7b0a8f_idx'),
        ),
        migrations.AddConstraint(
            model_name='userthemepreference',
            constraint=models.UniqueConstraint(fields=('user', 'name'), name='unique_theme_name_per_user'),
        ),
        migrations.AddConstraint(
            model_name='userthemepreference',
            constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('user', 'is_active'), name='one_active_theme_per_user'),
        ),
        migrations.AddIndex(
            model_name='themetemplate',
            index=models.Index(fields=['category', 'is_public'], name='app_themete_categor_2a5c3d_idx'),
        ),
        migrations.AddIndex(
            model_name='themetemplate',
            index=models.Index(fields=['is_featured', 'is_public'], name='app_themete_is_feat_8a9f2c_idx'),
        ),
        migrations.AddIndex(
            model_name='themeauditlog',
            index=models.Index(fields=['user', 'created_at'], name='app_themeau_user_id_6c8d9a_idx'),
        ),
        migrations.AddIndex(
            model_name='themeauditlog',
            index=models.Index(fields=['action', 'created_at'], name='app_themeau_action_9d3f4e_idx'),
        ),
        migrations.RunPython(create_default_templates, reverse_create_default_templates),
    ]