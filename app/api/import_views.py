"""
Django REST Framework API views for file import functionality.
Provides RESTful endpoints for file upload and import management.

Created by Team Sigma (Data Processing & Import) - Sprint 7
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.http import Http404
import logging

from ..models.import_models import (
    ImportJob, FileUpload, ImportedTransaction, 
    ImportTemplate, ImportValidationError
)
from ..serializers.import_serializers import (
    ImportJobSerializer, FileUploadSerializer, ImportedTransactionSerializer,
    ImportTemplateSerializer, ImportValidationErrorSerializer
)
from ..services.file_import_service import FileImportService
from ..tasks.import_tasks import process_file_import_task
from ..permissions import TenantPermission

logger = logging.getLogger('import.api')


class FileUploadViewSet(viewsets.ModelViewSet):
    """API endpoints for file upload management."""
    
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """Filter uploads by current user."""
        return FileUpload.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        """Handle file upload creation."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def validate_file(self, request, pk=None):
        """Validate uploaded file security and format."""
        file_upload = self.get_object()
        
        try:
            is_valid = file_upload.validate_file_security()
            
            return Response({
                'is_valid': is_valid,
                'validation_results': file_upload.validation_results,
                'status': file_upload.status
            })
            
        except Exception as e:
            logger.error(f"File validation failed for {file_upload.id}: {str(e)}")
            return Response(
                {'error': 'File validation failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def start_import(self, request, pk=None):
        """Start import process for validated file."""
        file_upload = self.get_object()
        
        if file_upload.status != FileUpload.Status.VALIDATED:
            return Response(
                {'error': 'File must be validated before import'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create import job
            import_settings = request.data.get('import_settings', {})
            
            import_job = ImportJob.objects.create(
                user=request.user,
                filename=file_upload.file.name,
                original_filename=file_upload.original_filename,
                file_type=self._determine_file_type(file_upload.mime_type),
                file_size=file_upload.file_size,
                file_hash=file_upload.file_hash,
                import_settings=import_settings
            )
            
            # Link file upload to import job
            file_upload.import_job = import_job
            file_upload.status = FileUpload.Status.PROCESSED
            file_upload.processed_at = timezone.now()
            file_upload.save()
            
            # Start background processing
            task = process_file_import_task.delay(str(import_job.id))
            
            logger.info(f"Import started for file {file_upload.id}", extra={
                'file_upload_id': str(file_upload.id),
                'import_job_id': str(import_job.id),
                'task_id': task.id,
                'user_id': str(request.user.id)
            })
            
            return Response({
                'import_job_id': import_job.id,
                'task_id': task.id,
                'status': 'Import started',
                'estimated_processing_time': self._estimate_processing_time(file_upload)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Failed to start import for {file_upload.id}: {str(e)}")
            return Response(
                {'error': 'Failed to start import', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _determine_file_type(self, mime_type):
        """Determine ImportJob file type from MIME type."""
        if mime_type in ['text/csv', 'application/csv']:
            return ImportJob.FileType.CSV
        elif 'excel' in mime_type:
            return ImportJob.FileType.EXCEL
        elif mime_type == 'application/pdf':
            return ImportJob.FileType.PDF
        else:
            return ImportJob.FileType.CSV  # Default
    
    def _estimate_processing_time(self, file_upload):
        """Estimate processing time based on file size."""
        # Rough estimate: 1000 transactions per second
        estimated_rows = file_upload.file_size / 100  # Rough estimate
        estimated_seconds = max(5, int(estimated_rows / 1000))
        
        return f"{estimated_seconds} seconds"


class ImportJobViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for import job management and monitoring."""
    
    queryset = ImportJob.objects.all()
    serializer_class = ImportJobSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        """Filter import jobs by current user."""
        return ImportJob.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get real-time import progress."""
        import_job = self.get_object()
        
        # Get task status if available
        task_status = None
        if hasattr(import_job, 'task_id'):
            from celery.result import AsyncResult
            task = AsyncResult(import_job.task_id)
            task_status = {
                'state': task.state,
                'info': task.info if task.info else {}
            }
        
        return Response({
            'import_job_id': import_job.id,
            'status': import_job.status,
            'progress': import_job.progress,
            'processed_rows': import_job.processed_rows,
            'total_rows': import_job.total_rows,
            'successful_imports': import_job.successful_imports,
            'failed_imports': import_job.failed_imports,
            'duplicate_count': import_job.duplicate_count,
            'duration': str(import_job.duration) if import_job.duration else None,
            'task_status': task_status
        })
    
    @action(detail=True, methods=['get'])
    def validation_errors(self, request, pk=None):
        """Get validation errors for import job."""
        import_job = self.get_object()
        
        errors = ImportValidationError.objects.filter(
            import_job=import_job
        ).order_by('row_number', 'severity')
        
        serializer = ImportValidationErrorSerializer(errors, many=True)
        
        return Response({
            'import_job_id': import_job.id,
            'total_errors': errors.count(),
            'errors_by_severity': {
                'ERROR': errors.filter(severity='ERROR').count(),
                'WARNING': errors.filter(severity='WARNING').count(),
                'INFO': errors.filter(severity='INFO').count(),
            },
            'validation_errors': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def imported_transactions(self, request, pk=None):
        """Get imported transactions for review."""
        import_job = self.get_object()
        
        # Get query parameters
        status_filter = request.query_params.get('status', None)
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        
        # Filter imported transactions
        queryset = ImportedTransaction.objects.filter(import_job=import_job)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Pagination
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        
        page = paginator.paginate_queryset(queryset, request)
        serializer = ImportedTransactionSerializer(page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve_transactions(self, request, pk=None):
        """Approve selected imported transactions."""
        import_job = self.get_object()
        
        transaction_ids = request.data.get('transaction_ids', [])
        if not transaction_ids:
            return Response(
                {'error': 'No transaction IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        approved_count = 0
        errors = []
        
        for transaction_id in transaction_ids:
            try:
                imported_transaction = ImportedTransaction.objects.get(
                    id=transaction_id,
                    import_job=import_job,
                    status=ImportedTransaction.Status.PENDING
                )
                
                # Assign account if not already assigned
                if not imported_transaction.account:
                    account_id = request.data.get('account_id')
                    if account_id:
                        account = get_object_or_404(
                            Account, 
                            id=account_id, 
                            created_by=request.user
                        )
                        imported_transaction.account = account
                        imported_transaction.save()
                
                # Approve and create transaction
                transaction = imported_transaction.approve_and_create_transaction()
                approved_count += 1
                
                logger.info(f"Transaction approved and created", extra={
                    'imported_transaction_id': str(imported_transaction.id),
                    'transaction_id': str(transaction.id),
                    'user_id': str(request.user.id)
                })
                
            except ImportedTransaction.DoesNotExist:
                errors.append(f"Transaction {transaction_id} not found or not pending")
            except Exception as e:
                errors.append(f"Failed to approve transaction {transaction_id}: {str(e)}")
        
        return Response({
            'approved_count': approved_count,
            'total_requested': len(transaction_ids),
            'errors': errors
        })


class ImportTemplateViewSet(viewsets.ModelViewSet):
    """API endpoints for import template management."""
    
    queryset = ImportTemplate.objects.all()
    serializer_class = ImportTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        """Filter templates by current user and public templates."""
        return ImportTemplate.objects.filter(
            models.Q(user=self.request.user) | models.Q(is_public=True)
        ).order_by('-usage_count', 'name')
    
    def perform_create(self, serializer):
        """Create template for current user."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Use template for import job."""
        template = self.get_object()
        
        # Increment usage counter
        template.increment_usage()
        
        return Response({
            'template_id': template.id,
            'column_mappings': template.column_mappings,
            'data_transformations': template.data_transformations,
            'validation_rules': template.validation_rules
        })


class ImportAnalyticsViewSet(viewsets.ViewSet):
    """API endpoints for import analytics and insights."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get import analytics for current user."""
        
        from django.db.models import Count, Sum, Avg
        from datetime import timedelta
        
        # Time range filter
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # User's import jobs
        user_jobs = ImportJob.objects.filter(
            user=request.user,
            created_at__gte=start_date
        )
        
        analytics = {
            'time_period': f"Last {days} days",
            'total_imports': user_jobs.count(),
            'successful_imports': user_jobs.filter(status=ImportJob.Status.COMPLETED).count(),
            'failed_imports': user_jobs.filter(status=ImportJob.Status.FAILED).count(),
            'pending_imports': user_jobs.filter(status=ImportJob.Status.PENDING).count(),
            'processing_imports': user_jobs.filter(status=ImportJob.Status.PROCESSING).count(),
            'total_transactions_imported': user_jobs.aggregate(
                total=Sum('successful_imports')
            )['total'] or 0,
            'file_type_breakdown': list(user_jobs.values('file_type').annotate(
                count=Count('id')
            )),
            'success_rate': self._calculate_success_rate(user_jobs),
            'average_processing_time': self._calculate_avg_processing_time(user_jobs),
        }
        
        return Response(analytics)
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent import activity."""
        
        recent_jobs = ImportJob.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
        
        serializer = ImportJobSerializer(recent_jobs, many=True)
        
        return Response({
            'recent_imports': serializer.data,
            'total_lifetime_imports': ImportJob.objects.filter(user=request.user).count()
        })
    
    def _calculate_success_rate(self, queryset):
        """Calculate import success rate."""
        completed_jobs = queryset.filter(status=ImportJob.Status.COMPLETED)
        if not queryset.exists():
            return 0
        
        return round((completed_jobs.count() / queryset.count()) * 100, 2)
    
    def _calculate_avg_processing_time(self, queryset):
        """Calculate average processing time."""
        completed_jobs = queryset.filter(
            status=ImportJob.Status.COMPLETED,
            processing_started_at__isnull=False,
            processing_completed_at__isnull=False
        )
        
        if not completed_jobs.exists():
            return None
        
        total_duration = sum(
            (job.processing_completed_at - job.processing_started_at).total_seconds()
            for job in completed_jobs
        )
        
        avg_seconds = total_duration / completed_jobs.count()
        return round(avg_seconds, 2)


class ImportedTransactionViewSet(viewsets.ModelViewSet):
    """API endpoints for managing imported transactions."""
    
    queryset = ImportedTransaction.objects.all()
    serializer_class = ImportedTransactionSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        """Filter imported transactions by current user."""
        return ImportedTransaction.objects.filter(
            import_job__user=self.request.user
        ).order_by('import_job', 'row_number')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve individual imported transaction."""
        imported_transaction = self.get_object()
        
        if imported_transaction.status != ImportedTransaction.Status.PENDING:
            return Response(
                {'error': 'Transaction is not pending approval'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Assign account if provided
            account_id = request.data.get('account_id')
            if account_id:
                account = get_object_or_404(
                    Account, 
                    id=account_id, 
                    created_by=request.user
                )
                imported_transaction.account = account
                imported_transaction.save()
            
            # Approve and create transaction
            transaction = imported_transaction.approve_and_create_transaction()
            
            return Response({
                'status': 'approved',
                'transaction_id': transaction.id,
                'message': 'Transaction approved and created successfully'
            })
            
        except Exception as e:
            logger.error(f"Failed to approve transaction {imported_transaction.id}: {str(e)}")
            return Response(
                {'error': 'Failed to approve transaction', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject individual imported transaction."""
        imported_transaction = self.get_object()
        
        if imported_transaction.status != ImportedTransaction.Status.PENDING:
            return Response(
                {'error': 'Transaction is not pending review'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', 'Rejected by user')
        imported_transaction.reject_with_reason(reason)
        
        return Response({
            'status': 'rejected',
            'reason': reason,
            'message': 'Transaction rejected successfully'
        })
    
    @action(detail=False, methods=['post'])
    def bulk_approve(self, request):
        """Approve multiple imported transactions."""
        transaction_ids = request.data.get('transaction_ids', [])
        account_id = request.data.get('account_id')
        
        if not transaction_ids:
            return Response(
                {'error': 'No transaction IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        approved_count = 0
        errors = []
        
        # Get account if specified
        account = None
        if account_id:
            try:
                account = Account.objects.get(id=account_id, created_by=request.user)
            except Account.DoesNotExist:
                return Response(
                    {'error': 'Account not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Process each transaction
        for transaction_id in transaction_ids:
            try:
                imported_transaction = ImportedTransaction.objects.get(
                    id=transaction_id,
                    import_job__user=request.user,
                    status=ImportedTransaction.Status.PENDING
                )
                
                # Assign account if provided
                if account:
                    imported_transaction.account = account
                    imported_transaction.save()
                
                # Approve transaction
                transaction = imported_transaction.approve_and_create_transaction()
                approved_count += 1
                
            except ImportedTransaction.DoesNotExist:
                errors.append(f"Transaction {transaction_id} not found or not pending")
            except Exception as e:
                errors.append(f"Failed to approve {transaction_id}: {str(e)}")
        
        return Response({
            'approved_count': approved_count,
            'total_requested': len(transaction_ids),
            'errors': errors
        })


# Health check for import system
class ImportHealthCheckViewSet(viewsets.ViewSet):
    """Health check endpoints for import system."""
    
    permission_classes = []  # No authentication required for health checks
    
    def list(self, request):
        """Basic import system health check."""
        
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'import_system': 'operational',
            'background_processing': 'available'
        }
        
        # Check Celery worker availability
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            active_workers = inspect.active()
            
            if active_workers:
                health_data['celery_workers'] = len(active_workers)
                health_data['background_processing'] = 'operational'
            else:
                health_data['celery_workers'] = 0
                health_data['background_processing'] = 'degraded'
                health_data['status'] = 'degraded'
                
        except Exception as e:
            health_data['celery_workers'] = 'unknown'
            health_data['background_processing'] = 'unknown'
            health_data['celery_error'] = str(e)
        
        # Check file storage
        try:
            test_file_path = 'health_check_test.txt'
            default_storage.save(test_file_path, 'test')
            default_storage.delete(test_file_path)
            health_data['file_storage'] = 'operational'
        except Exception as e:
            health_data['file_storage'] = 'failed'
            health_data['storage_error'] = str(e)
            health_data['status'] = 'degraded'
        
        return Response(health_data)