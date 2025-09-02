# Generated for Theme Option Sprint - Add UserPreference and UI defaults

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_default_ui_settings(apps, schema_editor):
    SystemConfiguration = apps.get_model('app', 'SystemConfiguration')
    # Create default theme setting if not exists
    try:
        SystemConfiguration.objects.get_or_create(
            key='ui.default_theme',
            defaults={
                'value': 'system',
                'description': 'Default UI theme for users without explicit preference',
                'is_active': True,
                'is_system': True,
            },
        )
    except Exception:
        # Best-effort; avoid failing migration if model or constraints differ
        pass


def remove_default_ui_settings(apps, schema_editor):
    SystemConfiguration = apps.get_model('app', 'SystemConfiguration')
    try:
        obj = SystemConfiguration.objects.filter(key='ui.default_theme').first()
        if obj:
            obj.delete()
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_add_import_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='userpreference_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='userpreference_updated', to=settings.AUTH_USER_MODEL)),
                ('theme', models.CharField(choices=[('light', 'Light'), ('dark', 'Dark'), ('system', 'System'), ('high-contrast', 'High Contrast')], default='system', max_length=20)),
                ('ui_preferences', models.JSONField(blank=True, default=dict, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='preference', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Preference',
                'verbose_name_plural': 'User Preferences',
            },
        ),
        migrations.AddIndex(
            model_name='userpreference',
            index=models.Index(fields=['theme'], name='idx_userpref_theme'),
        ),
        migrations.RunPython(create_default_ui_settings, remove_default_ui_settings),
    ]

