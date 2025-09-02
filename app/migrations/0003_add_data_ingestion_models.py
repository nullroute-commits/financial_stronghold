"""
Django migration for data ingestion models.
"""

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_add_tagging_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataSource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(help_text='Descriptive name for the data source', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Detailed description of the data source')),
                ('source_type', models.CharField(choices=[
                    ('csv_upload', 'CSV File Upload'),
                    ('csv_url', 'CSV from URL'),
                    ('https_endpoint', 'HTTPS Endpoint'),
                    ('api_endpoint', 'API Endpoint'),
                    ('ftp', 'FTP Server'),
                    ('sftp', 'SFTP Server')
                ], help_text='Type of data source', max_length=50)),
                ('source_url', models.URLField(blank=True, help_text='URL for HTTPS/API endpoints', max_length=500)),
                ('auth_type', models.CharField(choices=[
                    ('none', 'No Authentication'),
                    ('basic', 'Basic Authentication'),
                    ('bearer', 'Bearer Token'),
                    ('api_key', 'API Key'),
                    ('oauth2', 'OAuth 2.0'),
                    ('custom_header', 'Custom Header')
                ], default='none', help_text='Authentication method', max_length=50)),
                ('auth_config', models.JSONField(blank=True, default=dict, help_text='Authentication configuration (encrypted in production)')),
                ('data_format', models.CharField(choices=[
                    ('csv', 'CSV'),
                    ('json', 'JSON'),
                    ('xml', 'XML'),
                    ('xlsx', 'Excel (XLSX)'),
                    ('ofx', 'Open Financial Exchange'),
                    ('qif', 'Quicken Interchange Format')
                ], default='csv', help_text='Format of the data', max_length=20)),
                ('field_mapping', models.JSONField(default=dict, help_text='Maps source fields to system fields')),
                ('transform_config', models.JSONField(blank=True, default=dict, help_text='Data transformation rules')),
                ('validation_rules', models.JSONField(blank=True, default=dict, help_text='Custom validation rules for imported data')),
                ('default_account_id', models.UUIDField(blank=True, help_text='Default account for imported transactions', null=True)),
                ('default_tags', models.JSONField(blank=True, default=list, help_text='Default tags to apply to imported data')),
                ('schedule_enabled', models.BooleanField(default=False, help_text='Enable automatic scheduled ingestion')),
                ('schedule_frequency', models.CharField(choices=[
                    ('manual', 'Manual Only'),
                    ('hourly', 'Every Hour'),
                    ('daily', 'Daily'),
                    ('weekly', 'Weekly'),
                    ('monthly', 'Monthly'),
                    ('custom', 'Custom Schedule')
                ], default='manual', max_length=20)),
                ('schedule_config', models.JSONField(blank=True, default=dict, help_text='Scheduling configuration (cron expression, time, etc.)')),
                ('last_sync', models.DateTimeField(blank=True, help_text='Last successful synchronization', null=True)),
                ('next_sync', models.DateTimeField(blank=True, help_text='Next scheduled synchronization', null=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this data source is active')),
                ('tenant_type', models.CharField(default='user', max_length=50)),
                ('tenant_id', models.CharField(max_length=255)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='datasource_created', to='app.user')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='datasource_updated', to='app.user')),
            ],
            options={
                'db_table': 'data_sources',
            },
        ),
        migrations.CreateModel(
            name='IngestionJob',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('job_id', models.UUIDField(default=uuid.uuid4, help_text='Unique job identifier', unique=True)),
                ('status', models.CharField(choices=[
                    ('pending', 'Pending'),
                    ('validating', 'Validating'),
                    ('processing', 'Processing'),
                    ('completed', 'Completed'),
                    ('failed', 'Failed'),
                    ('partial', 'Partially Completed'),
                    ('cancelled', 'Cancelled')
                ], default='pending', max_length=20)),
                ('started_at', models.DateTimeField(blank=True, help_text='When the job started', null=True)),
                ('completed_at', models.DateTimeField(blank=True, help_text='When the job completed', null=True)),
                ('file_name', models.CharField(blank=True, help_text='Original filename for uploads', max_length=255)),
                ('file_size', models.BigIntegerField(blank=True, help_text='File size in bytes', null=True)),
                ('file_path', models.CharField(blank=True, help_text='Storage path for uploaded files', max_length=500)),
                ('total_records', models.IntegerField(default=0, help_text='Total records in the source')),
                ('processed_records', models.IntegerField(default=0, help_text='Records successfully processed')),
                ('failed_records', models.IntegerField(default=0, help_text='Records that failed processing')),
                ('skipped_records', models.IntegerField(default=0, help_text='Records skipped (duplicates, etc.)')),
                ('transactions_created', models.IntegerField(default=0, help_text='New transactions created')),
                ('transactions_updated', models.IntegerField(default=0, help_text='Existing transactions updated')),
                ('error_summary', models.JSONField(blank=True, default=dict, help_text='Summary of errors by type')),
                ('error_details', models.JSONField(blank=True, default=list, help_text='Detailed error information')),
                ('processing_log', models.TextField(blank=True, help_text='Detailed processing log')),
                ('tenant_type', models.CharField(default='user', max_length=50)),
                ('tenant_id', models.CharField(max_length=255)),
                ('data_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingestion_jobs', to='app.datasource')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ingestionjob_created', to='app.user')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ingestionjob_updated', to='app.user')),
            ],
            options={
                'db_table': 'ingestion_jobs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='IngestionSchedule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('cron_expression', models.CharField(blank=True, help_text='Cron expression for custom schedules', max_length=100)),
                ('start_time', models.TimeField(blank=True, help_text='Daily start time for ingestion window', null=True)),
                ('end_time', models.TimeField(blank=True, help_text='Daily end time for ingestion window', null=True)),
                ('days_of_week', models.JSONField(blank=True, default=list, help_text='Days of week (0=Monday, 6=Sunday)')),
                ('day_of_month', models.IntegerField(blank=True, help_text='Day of month (1-31)', null=True)),
                ('retry_on_failure', models.BooleanField(default=True, help_text='Retry failed ingestions')),
                ('max_retries', models.IntegerField(default=3, help_text='Maximum retry attempts')),
                ('retry_delay_minutes', models.IntegerField(default=30, help_text='Delay between retries')),
                ('notify_on_success', models.BooleanField(default=False)),
                ('notify_on_failure', models.BooleanField(default=True)),
                ('notification_emails', models.JSONField(blank=True, default=list)),
                ('data_source', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='schedule', to='app.datasource')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ingestionschedule_created', to='app.user')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ingestionschedule_updated', to='app.user')),
            ],
            options={
                'db_table': 'ingestion_schedules',
            },
        ),
        migrations.CreateModel(
            name='FieldMapping',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('source_field', models.CharField(help_text='Field name in the source data', max_length=255)),
                ('source_field_type', models.CharField(help_text='Data type in source', max_length=50)),
                ('target_field', models.CharField(help_text='Field name in the system', max_length=255)),
                ('target_model', models.CharField(default='Transaction', help_text='Target model (Transaction, Account, etc.)', max_length=50)),
                ('transform_function', models.CharField(blank=True, help_text='Transformation function to apply', max_length=100)),
                ('transform_params', models.JSONField(blank=True, default=dict, help_text='Parameters for transformation')),
                ('is_required', models.BooleanField(default=False, help_text='Whether this field is required')),
                ('validation_regex', models.CharField(blank=True, help_text='Regex pattern for validation', max_length=500)),
                ('default_value', models.CharField(blank=True, help_text='Default value if source field is empty', max_length=500)),
                ('data_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='field_mappings', to='app.datasource')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fieldmapping_created', to='app.user')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fieldmapping_updated', to='app.user')),
            ],
            options={
                'db_table': 'field_mappings',
                'unique_together': {('data_source', 'source_field')},
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='datasource',
            index=models.Index(fields=['tenant_type', 'tenant_id'], name='data_source_tenant_idx'),
        ),
        migrations.AddIndex(
            model_name='datasource',
            index=models.Index(fields=['source_type'], name='data_source_type_idx'),
        ),
        migrations.AddIndex(
            model_name='datasource',
            index=models.Index(fields=['is_active'], name='data_source_active_idx'),
        ),
        migrations.AddIndex(
            model_name='datasource',
            index=models.Index(fields=['next_sync'], name='data_source_sync_idx'),
        ),
        migrations.AddIndex(
            model_name='ingestionjob',
            index=models.Index(fields=['job_id'], name='ingestion_job_id_idx'),
        ),
        migrations.AddIndex(
            model_name='ingestionjob',
            index=models.Index(fields=['status'], name='ingestion_job_status_idx'),
        ),
        migrations.AddIndex(
            model_name='ingestionjob',
            index=models.Index(fields=['started_at'], name='ingestion_job_start_idx'),
        ),
        migrations.AddIndex(
            model_name='ingestionjob',
            index=models.Index(fields=['tenant_type', 'tenant_id'], name='ingestion_job_tenant_idx'),
        ),
        # Add unique constraint
        migrations.AddConstraint(
            model_name='datasource',
            constraint=models.UniqueConstraint(fields=['name', 'tenant_type', 'tenant_id'], name='unique_data_source_name'),
        ),
    ]