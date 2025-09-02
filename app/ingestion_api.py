"""
API endpoints for data ingestion feature.
This will be imported and included in the main API router.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session

from app.auth import get_current_user, get_tenant_context
from app.core.db.connection import get_db_session
from app.ingestion_service import DataIngestionService
from app.ingestion_models import DataSource, IngestionJob
from app.ingestion_schemas import (
    DataSourceCreate, DataSourceRead, DataSourceUpdate,
    IngestionJobCreate, IngestionJobRead,
    DataPreviewRequest, DataPreviewResponse,
    FileUploadRequest, ImportConfigRequest, ImportResult
)

router = APIRouter(prefix="/financial/data-ingestion", tags=["data-ingestion"])


# Data Source Management Endpoints
@router.post("/sources", response_model=DataSourceRead, status_code=status.HTTP_201_CREATED)
def create_data_source(
    payload: DataSourceCreate,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session)
):
    """Create a new data source for financial data ingestion."""
    data_source = DataSource(
        **payload.dict(),
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"]
    )
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    return data_source


@router.get("/sources", response_model=List[DataSourceRead])
def list_data_sources(
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
    is_active: Optional[bool] = Query(None),
    source_type: Optional[str] = Query(None)
):
    """List all data sources for the tenant."""
    query = db.query(DataSource).filter(
        DataSource.tenant_type == tenant_context["tenant_type"],
        DataSource.tenant_id == tenant_context["tenant_id"]
    )
    
    if is_active is not None:
        query = query.filter(DataSource.is_active == is_active)
    
    if source_type:
        query = query.filter(DataSource.source_type == source_type)
    
    return query.all()


@router.get("/sources/{source_id}", response_model=DataSourceRead)
def get_data_source(
    source_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session)
):
    """Get a specific data source."""
    data_source = db.query(DataSource).filter(
        DataSource.id == source_id,
        DataSource.tenant_type == tenant_context["tenant_type"],
        DataSource.tenant_id == tenant_context["tenant_id"]
    ).first()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    return data_source


@router.put("/sources/{source_id}", response_model=DataSourceRead)
def update_data_source(
    source_id: UUID,
    payload: DataSourceUpdate,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session)
):
    """Update a data source configuration."""
    data_source = db.query(DataSource).filter(
        DataSource.id == source_id,
        DataSource.tenant_type == tenant_context["tenant_type"],
        DataSource.tenant_id == tenant_context["tenant_id"]
    ).first()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # Update fields
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(data_source, field, value)
    
    db.commit()
    db.refresh(data_source)
    return data_source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_data_source(
    source_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session)
):
    """Delete a data source."""
    data_source = db.query(DataSource).filter(
        DataSource.id == source_id,
        DataSource.tenant_type == tenant_context["tenant_type"],
        DataSource.tenant_id == tenant_context["tenant_id"]
    ).first()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    db.delete(data_source)
    db.commit()


# Data Preview Endpoints
@router.post("/sources/{source_id}/preview", response_model=DataPreviewResponse)
def preview_data_source(
    source_id: UUID,
    preview_rows: int = Query(10, ge=1, le=100),
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session)
):
    """Preview data from a configured data source."""
    data_source = db.query(DataSource).filter(
        DataSource.id == source_id,
        DataSource.tenant_type == tenant_context["tenant_type"],
        DataSource.tenant_id == tenant_context["tenant_id"]
    ).first()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    ingestion_service = DataIngestionService(
        db=db,
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"]
    )
    
    try:
        preview_data = ingestion_service.preview_data(data_source, preview_rows)
        return DataPreviewResponse(**preview_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/preview", response_model=DataPreviewResponse)
def preview_data_without_source(
    request: DataPreviewRequest,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session)
):
    """Preview data from a URL without creating a data source."""
    # Create temporary data source object
    temp_source = DataSource(
        name="Preview",
        source_type=request.source_type,
        source_url=str(request.source_url) if request.source_url else None,
        auth_type=request.auth_type or "none",
        auth_config=request.auth_config or {},
        data_format=request.data_format,
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"]
    )
    
    ingestion_service = DataIngestionService(
        db=db,
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"]
    )
    
    try:
        preview_data = ingestion_service.preview_data(temp_source, request.preview_rows)
        return DataPreviewResponse(**preview_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Import Endpoints
@router.post("/sources/{source_id}/import", response_model=ImportResult)
def import_from_data_source(
    source_id: UUID,
    config: ImportConfigRequest,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session)
):
    """Import data from a configured data source."""
    data_source = db.query(DataSource).filter(
        DataSource.id == source_id,
        DataSource.tenant_type == tenant_context["tenant_type"],
        DataSource.tenant_id == tenant_context["tenant_id"]
    ).first()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    ingestion_service = DataIngestionService(
        db=db,
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"]
    )
    
    # Create ingestion job
    job = ingestion_service.create_ingestion_job(data_source)
    
    try:
        # Update job status
        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        
        # Fetch data
        raw_data, data_format = ingestion_service.fetch_data_from_source(data_source)
        
        # Parse data
        parsed_data = ingestion_service.parse_data(
            raw_data, data_format, data_source.field_mapping or {}
        )
        job.total_records = len(parsed_data)
        
        # Validate data
        valid_data, invalid_data = ingestion_service.validate_data(
            parsed_data, data_source.validation_rules or {}
        )
        
        # Transform data
        transformed_data = ingestion_service.transform_data(
            valid_data, data_source.transform_config or {}
        )
        
        # Import transactions
        if not config.dry_run:
            import_results = ingestion_service.import_transactions(
                transformed_data, data_source, job, config.dict()
            )
            
            job.processed_records = import_results['created'] + import_results['updated']
            job.failed_records = import_results['failed']
            job.skipped_records = import_results['skipped']
            job.transactions_created = import_results['created']
            job.transactions_updated = import_results['updated']
            job.error_summary = {
                'validation_errors': len(invalid_data),
                'import_errors': len(import_results['errors'])
            }
        else:
            # Dry run - just validate
            job.processed_records = len(valid_data)
            job.failed_records = len(invalid_data)
        
        # Update job status
        job.status = "completed" if job.failed_records == 0 else "partial"
        job.completed_at = datetime.now(timezone.utc)
        
        # Update data source last sync
        data_source.last_sync = datetime.now(timezone.utc)
        
        db.commit()
        
        return ImportResult(
            job_id=job.job_id,
            status=job.status,
            total_records=job.total_records,
            processed_records=job.processed_records,
            created_records=job.transactions_created,
            updated_records=job.transactions_updated,
            skipped_records=job.skipped_records,
            failed_records=job.failed_records,
            errors=invalid_data[:10] if invalid_data else [],  # Return first 10 errors
            processing_time=(job.completed_at - job.started_at).total_seconds(),
            dry_run=config.dry_run
        )
        
    except Exception as e:
        # Update job with error
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        job.error_summary = {'error': str(e)}
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/sources/{source_id}/upload", response_model=ImportResult)
async def upload_and_import(
    source_id: UUID,
    file: UploadFile = File(...),
    skip_duplicates: bool = Query(True),
    update_existing: bool = Query(False),
    dry_run: bool = Query(False),
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session)
):
    """Upload a file and import data using the specified data source configuration."""
    data_source = db.query(DataSource).filter(
        DataSource.id == source_id,
        DataSource.tenant_type == tenant_context["tenant_type"],
        DataSource.tenant_id == tenant_context["tenant_id"]
    ).first()
    
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    if data_source.source_type != "csv_upload":
        raise HTTPException(
            status_code=400, 
            detail="This data source is not configured for file uploads"
        )
    
    # Save uploaded file
    file_content = await file.read()
    
    ingestion_service = DataIngestionService(
        db=db,
        tenant_type=tenant_context["tenant_type"],
        tenant_id=tenant_context["tenant_id"]
    )
    
    # Create ingestion job
    job = ingestion_service.create_ingestion_job(
        data_source,
        file_name=file.filename,
        file_size=len(file_content)
    )
    
    try:
        # Process the uploaded file
        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        
        # Parse CSV data
        csv_data = file_content.decode('utf-8')
        parsed_data = ingestion_service.parse_data(
            csv_data, 'csv', data_source.field_mapping or {}
        )
        job.total_records = len(parsed_data)
        
        # Validate data
        valid_data, invalid_data = ingestion_service.validate_data(
            parsed_data, data_source.validation_rules or {}
        )
        
        # Transform data
        transformed_data = ingestion_service.transform_data(
            valid_data, data_source.transform_config or {}
        )
        
        # Import config
        config = ImportConfigRequest(
            data_source_id=source_id,
            skip_duplicates=skip_duplicates,
            update_existing=update_existing,
            dry_run=dry_run
        )
        
        # Import transactions
        if not dry_run:
            import_results = ingestion_service.import_transactions(
                transformed_data, data_source, job, config.dict()
            )
            
            job.processed_records = import_results['created'] + import_results['updated']
            job.failed_records = import_results['failed']
            job.skipped_records = import_results['skipped']
            job.transactions_created = import_results['created']
            job.transactions_updated = import_results['updated']
        else:
            job.processed_records = len(valid_data)
            job.failed_records = len(invalid_data)
        
        # Update job status
        job.status = "completed" if job.failed_records == 0 else "partial"
        job.completed_at = datetime.now(timezone.utc)
        
        db.commit()
        
        # Return results
        return ImportResult(
            job_id=job.job_id,
            status=job.status,
            total_records=job.total_records,
            processed_records=job.processed_records,
            created_records=job.transactions_created,
            updated_records=job.transactions_updated,
            skipped_records=job.skipped_records,
            failed_records=job.failed_records,
            errors=[],
            processing_time=(job.completed_at - job.started_at).total_seconds(),
            dry_run=dry_run
        )
        
    except Exception as e:
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        job.error_summary = {'error': str(e)}
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# Job Management Endpoints
@router.get("/jobs", response_model=List[IngestionJobRead])
def list_ingestion_jobs(
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session),
    data_source_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List ingestion jobs for the tenant."""
    query = db.query(IngestionJob).filter(
        IngestionJob.tenant_type == tenant_context["tenant_type"],
        IngestionJob.tenant_id == tenant_context["tenant_id"]
    )
    
    if data_source_id:
        query = query.filter(IngestionJob.data_source_id == data_source_id)
    
    if status:
        query = query.filter(IngestionJob.status == status)
    
    # Order by created_at descending
    query = query.order_by(IngestionJob.created_at.desc())
    
    # Apply pagination
    jobs = query.offset(offset).limit(limit).all()
    
    # Convert to response model
    return [
        IngestionJobRead(
            id=job.id,
            job_id=job.job_id,
            data_source_id=job.data_source_id,
            data_source_name=job.data_source.name,
            status=job.status,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            file_name=job.file_name,
            file_size=job.file_size,
            total_records=job.total_records,
            processed_records=job.processed_records,
            failed_records=job.failed_records,
            skipped_records=job.skipped_records,
            transactions_created=job.transactions_created,
            transactions_updated=job.transactions_updated,
            error_summary=job.error_summary,
            duration=job.duration,
            success_rate=job.success_rate
        )
        for job in jobs
    ]


@router.get("/jobs/{job_id}", response_model=IngestionJobRead)
def get_ingestion_job(
    job_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session)
):
    """Get details of a specific ingestion job."""
    job = db.query(IngestionJob).filter(
        IngestionJob.job_id == job_id,
        IngestionJob.tenant_type == tenant_context["tenant_type"],
        IngestionJob.tenant_id == tenant_context["tenant_id"]
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    
    return IngestionJobRead(
        id=job.id,
        job_id=job.job_id,
        data_source_id=job.data_source_id,
        data_source_name=job.data_source.name,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        file_name=job.file_name,
        file_size=job.file_size,
        total_records=job.total_records,
        processed_records=job.processed_records,
        failed_records=job.failed_records,
        skipped_records=job.skipped_records,
        transactions_created=job.transactions_created,
        transactions_updated=job.transactions_updated,
        error_summary=job.error_summary,
        duration=job.duration,
        success_rate=job.success_rate
    )


@router.post("/jobs/{job_id}/cancel", response_model=IngestionJobRead)
def cancel_ingestion_job(
    job_id: UUID,
    tenant_context: dict = Depends(get_tenant_context),
    db: Session = Depends(get_db_session)
):
    """Cancel a running ingestion job."""
    job = db.query(IngestionJob).filter(
        IngestionJob.job_id == job_id,
        IngestionJob.tenant_type == tenant_context["tenant_type"],
        IngestionJob.tenant_id == tenant_context["tenant_id"]
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    
    if job.status not in ["pending", "processing", "validating"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel job with status: {job.status}"
        )
    
    job.status = "cancelled"
    job.completed_at = datetime.now(timezone.utc)
    db.commit()
    
    return IngestionJobRead(
        id=job.id,
        job_id=job.job_id,
        data_source_id=job.data_source_id,
        data_source_name=job.data_source.name,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        file_name=job.file_name,
        file_size=job.file_size,
        total_records=job.total_records,
        processed_records=job.processed_records,
        failed_records=job.failed_records,
        skipped_records=job.skipped_records,
        transactions_created=job.transactions_created,
        transactions_updated=job.transactions_updated,
        error_summary=job.error_summary,
        duration=job.duration,
        success_rate=job.success_rate
    )