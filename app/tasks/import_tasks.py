"""
Celery tasks for background file import processing.
Handles asynchronous file processing and analysis.

Created by Team Phi (Infrastructure & Performance) - Sprint 7
"""

import logging
try:
    from celery import shared_task, current_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    # Create dummy decorators for when Celery is not available
    def shared_task(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    current_task = None
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..import_models import ImportJob, FileUpload
from ..services.file_import_service import FileImportService

User = get_user_model()
logger = logging.getLogger('import.tasks')


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_file_import_task(self, import_job_id):
    """
    Background task for processing file imports.
    
    Args:
        import_job_id: UUID of the ImportJob to process
    """
    
    try:
        # Get import job
        import_job = ImportJob.objects.get(id=import_job_id)
        user = import_job.user
        
        logger.info(f"Starting import job {import_job_id}", extra={
            'import_job_id': str(import_job_id),
            'user_id': str(user.id),
            'filename': import_job.original_filename,
            'file_type': import_job.file_type
        })
        
        # Update task progress
        current_task.update_state(
            state='PROCESSING',
            meta={
                'import_job_id': str(import_job_id),
                'progress': 0,
                'status': 'Starting file processing...'
            }
        )
        
        # Mark job as started
        import_job.mark_started()
        
        # Create file import service
        import_service = FileImportService(user)
        
        # Get file upload
        file_upload = import_job.file_upload
        
        # Process file based on type
        if import_job.file_type == ImportJob.FileType.CSV:
            process_csv_import(import_service, import_job, file_upload)
        elif import_job.file_type == ImportJob.FileType.EXCEL:
            process_excel_import(import_service, import_job, file_upload)
        elif import_job.file_type == ImportJob.FileType.PDF:
            process_pdf_import(import_service, import_job, file_upload)
        
        # Mark job as completed
        import_job.mark_completed()
        
        # Update final task state
        current_task.update_state(
            state='SUCCESS',
            meta={
                'import_job_id': str(import_job_id),
                'progress': 100,
                'status': 'Import completed successfully',
                'successful_imports': import_job.successful_imports,
                'failed_imports': import_job.failed_imports,
                'duplicate_count': import_job.duplicate_count
            }
        )
        
        # Send completion notification
        send_import_completion_notification.delay(import_job_id)
        
        logger.info(f"Import job {import_job_id} completed successfully", extra={
            'import_job_id': str(import_job_id),
            'successful_imports': import_job.successful_imports,
            'failed_imports': import_job.failed_imports,
            'processing_time': str(import_job.duration)
        })
        
        return {
            'status': 'completed',
            'successful_imports': import_job.successful_imports,
            'failed_imports': import_job.failed_imports,
            'duplicate_count': import_job.duplicate_count
        }
        
    except ImportJob.DoesNotExist:
        error_msg = f"Import job {import_job_id} not found"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    except Exception as exc:
        # Log error
        logger.error(f"Import job {import_job_id} failed: {str(exc)}", extra={
            'import_job_id': str(import_job_id),
            'error': str(exc),
            'retry_count': self.request.retries
        })
        
        # Mark job as failed
        try:
            import_job = ImportJob.objects.get(id=import_job_id)
            import_job.mark_failed(str(exc))
        except ImportJob.DoesNotExist:
            pass
        
        # Update task state
        current_task.update_state(
            state='FAILURE',
            meta={
                'import_job_id': str(import_job_id),
                'error': str(exc),
                'retry_count': self.request.retries
            }
        )
        
        # Retry task if retries remaining
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying import job {import_job_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc)
        
        # Send failure notification
        send_import_failure_notification.delay(import_job_id, str(exc))
        
        raise exc


async def process_csv_import(import_service, import_job, file_upload):
    """Process CSV file import."""
    
    current_task.update_state(
        state='PROCESSING',
        meta={
            'progress': 10,
            'status': 'Parsing CSV file...'
        }
    )
    
    # Parse CSV file
    df = import_service.csv_parser.parse_csv_file(file_upload.file.path)
    import_job.total_rows = len(df)
    import_job.save(update_fields=['total_rows'])
    
    current_task.update_state(
        state='PROCESSING',
        meta={
            'progress': 20,
            'status': f'Processing {len(df)} transactions...'
        }
    )
    
    # Process each row
    for index, row in df.iterrows():
        await import_service._process_transaction_row(import_job, index + 1, row.to_dict())
        
        # Update progress every 100 rows
        if (index + 1) % 100 == 0:
            progress = 20 + int(((index + 1) / len(df)) * 70)  # 20-90% range
            current_task.update_state(
                state='PROCESSING',
                meta={
                    'progress': progress,
                    'status': f'Processed {index + 1} of {len(df)} transactions...'
                }
            )
            
            import_job.update_progress(
                processed_rows=index + 1,
                successful_imports=import_job.successful_imports,
                failed_imports=import_job.failed_imports
            )
    
    # Final progress update
    current_task.update_state(
        state='PROCESSING',
        meta={
            'progress': 90,
            'status': 'Finalizing import...'
        }
    )


async def process_excel_import(import_service, import_job, file_upload):
    """Process Excel file import (Sprint 8 implementation)."""
    raise NotImplementedError("Excel import will be implemented in Sprint 8")


async def process_pdf_import(import_service, import_job, file_upload):
    """Process PDF file import (Sprint 9 implementation)."""
    raise NotImplementedError("PDF import will be implemented in Sprint 9")


@shared_task
def send_import_completion_notification(import_job_id):
    """Send notification when import is completed."""
    
    try:
        import_job = ImportJob.objects.get(id=import_job_id)
        
        # Log completion
        logger.info(f"Import completed notification sent", extra={
            'import_job_id': str(import_job_id),
            'user_id': str(import_job.user.id),
            'successful_imports': import_job.successful_imports,
            'failed_imports': import_job.failed_imports
        })
        
        # In production, this would send actual notifications
        # Email, push notifications, etc.
        
    except ImportJob.DoesNotExist:
        logger.error(f"Import job {import_job_id} not found for notification")


@shared_task
def send_import_failure_notification(import_job_id, error_message):
    """Send notification when import fails."""
    
    try:
        import_job = ImportJob.objects.get(id=import_job_id)
        
        # Log failure
        logger.error(f"Import failed notification sent", extra={
            'import_job_id': str(import_job_id),
            'user_id': str(import_job.user.id),
            'error_message': error_message
        })
        
        # In production, this would send actual notifications
        
    except ImportJob.DoesNotExist:
        logger.error(f"Import job {import_job_id} not found for failure notification")


@shared_task
def cleanup_old_import_files():
    """Clean up old import files and data."""
    
    from datetime import timedelta
    
    # Delete import jobs older than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    
    old_jobs = ImportJob.objects.filter(
        created_at__lt=cutoff_date,
        status__in=[ImportJob.Status.COMPLETED, ImportJob.Status.FAILED]
    )
    
    deleted_count = 0
    for job in old_jobs:
        # Delete associated file
        if hasattr(job, 'file_upload') and job.file_upload.file:
            job.file_upload.file.delete(save=False)
        
        # Delete job and related data
        job.delete()
        deleted_count += 1
    
    logger.info(f"Cleaned up {deleted_count} old import jobs")
    
    return {'deleted_jobs': deleted_count}


@shared_task
def generate_import_analytics():
    """Generate analytics for import feature usage."""
    
    from django.db.models import Count, Avg, Sum
    from datetime import timedelta
    
    # Calculate analytics for last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    analytics = {
        'total_imports': ImportJob.objects.filter(created_at__gte=thirty_days_ago).count(),
        'successful_imports': ImportJob.objects.filter(
            created_at__gte=thirty_days_ago,
            status=ImportJob.Status.COMPLETED
        ).count(),
        'failed_imports': ImportJob.objects.filter(
            created_at__gte=thirty_days_ago,
            status=ImportJob.Status.FAILED
        ).count(),
        'average_processing_time': ImportJob.objects.filter(
            created_at__gte=thirty_days_ago,
            status=ImportJob.Status.COMPLETED,
            processing_completed_at__isnull=False
        ).aggregate(
            avg_duration=Avg('processing_completed_at') - Avg('processing_started_at')
        )['avg_duration'],
        'total_transactions_imported': ImportJob.objects.filter(
            created_at__gte=thirty_days_ago,
            status=ImportJob.Status.COMPLETED
        ).aggregate(total=Sum('successful_imports'))['total'] or 0,
        'file_type_breakdown': ImportJob.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('file_type').annotate(count=Count('id')),
    }
    
    logger.info("Import analytics generated", extra=analytics)
    
    return analytics