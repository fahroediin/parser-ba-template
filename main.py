from fastapi import FastAPI, UploadFile, File, Depends, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from database import get_db, engine # Anggap setup DB standar
import models
import shutil
from services.parser_factory import ParserFactory
from services.image_extractor import ImageExtractor
from slugify import slugify
from response_utils import (
    create_success_response, create_error_response, handle_http_exception,
    create_upload_response, create_batch_response, create_batch_list_response,
    create_document_response, ResponseMessage, ResponseStatus
)
from response_schemas import ErrorDetail
from datetime import datetime
from typing import List

# Init DB Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Excel Parser API - Multi-Division Templates",
    description="Professional API for parsing Excel documents with automatic template detection for BA, UIUX, and Engineering divisions",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global exception handler for standardized error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler for standardized error responses"""
    error_response = handle_http_exception(exc, request)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global general exception handler"""
    error_response = create_error_response(
        message="Internal server error occurred",
        error_code="INTERNAL_SERVER_ERROR",
        path=str(request.url.path)
    )
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )

async def process_upload_background(batch_id: str, file_content: bytes, db: Session):
    """Background task untuk parsing dan insert DB"""
    
    # Ambil record batch
    batch = db.query(models.ImportBatch).filter(models.ImportBatch.id == batch_id).first()
    
    try:
        # Auto-detect template and parse Excel with image extraction
        detected_template_type = ParserFactory.detect_template_type(file_content)
        print(f"Auto-detected template type: {detected_template_type}")

        parser = ParserFactory.create_parser(file_content)
        result = parser.process_file(batch_id=batch.id, document_id=str(new_batch.id))

        if result['errors']:
            batch.error_log = result['errors']
            # Kita tidak langsung fail kalau ada error parsial, tapi dicatat

        # 1. Handle Category (Cari atau Buat)
        cat_name = result['category_name']
        category = db.query(models.Category).filter(models.Category.name == cat_name).first()
        if not category:
            category = models.Category(name=cat_name, slug=slugify(cat_name))
            db.add(category)
            db.flush() # Dapatkan ID

        # 2. Insert Document
        new_doc = models.Document(
            import_batch_id=batch.id,
            category_id=category.id,
            title=result['title'],
            description=f"Imported from {batch.filename}",
            metadata_content=result['metadata'], # DATA JSON DISIMPAN DISINI
            status='ACTIVE'
        )
        db.add(new_doc)
        db.flush() # Dapatkan document_id

        # 3. Handle Image Storage (NEW!)
        if result.get('extracted_images'):
            try:
                image_extractor = ImageExtractor(file_content, batch.id, str(new_doc.id))
                saved_images = image_extractor.save_images_to_database(db, result['extracted_images'])
                print(f"Saved {len(saved_images)} images to database")
            except Exception as e:
                print(f"Error saving images to database: {e}")
                # Don't fail the entire process if image saving fails
        
        # 4. Update Batch Status
        batch.status = 'COMPLETED'
        batch.success_count = 1 # Asumsi 1 file = 1 dokumen sukses
        batch.total_rows = result['metadata']['parsing_stats']['total_us'] # Contoh metric
        
        db.commit()
        print(f"Batch {batch_id} completed successfully.")

    except Exception as e:
        db.rollback()
        batch.status = 'FAILED'
        batch.error_log = {"critical_error": str(e)}
        batch.failed_count = 1
        db.commit()
        print(f"Batch {batch_id} failed: {e}")

@app.post("/upload/product-document")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Upload Excel document for parsing with standardized response"""
    try:
        # Validasi Ekstensi
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(
                status_code=400,
                detail=[
                    {
                        "type": "value_error",
                        "loc": ["body", "file"],
                        "msg": "Invalid file format. Must be .xlsx",
                        "input": file.filename,
                        "url": "https://errors.pydantic.dev/2.5/v/value_error"
                    }
                ]
            )

        # Validasi file size (optional - max 10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=413,
                detail="File size exceeds maximum allowed limit of 10MB"
            )

        # Mock User ID (Di real app ambil dari JWT Token)
        mock_user = db.query(models.User).first()
        if not mock_user:
            # Create dummy user for testing
            mock_user = models.User(email="admin@company.com", password_hash="xxx", full_name="Admin")
            db.add(mock_user)
            db.commit()

        # 1. Create Import Batch Record (Status: PROCESSING)
        new_batch = models.ImportBatch(
            user_id=mock_user.id,
            filename=file.filename,
            status='PROCESSING'
        )
        db.add(new_batch)
        db.commit()
        db.refresh(new_batch)

        # 2. Trigger Background Processing
        background_tasks.add_task(process_upload_background, new_batch.id, content, db)

        # Return standardized success response
        response = create_upload_response(
            batch_id=str(new_batch.id),
            filename=file.filename,
            status=ResponseStatus.PROCESSING
        )

        return JSONResponse(content=response.dict(), status_code=201)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during file upload: {str(e)}"
        )

@app.post("/upload/document")
async def upload_document_with_template(
    file: UploadFile = File(...),
    template_type: str = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Upload Excel document with optional template type specification"""
    try:
        # Validasi Ekstensi
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(
                status_code=400,
                detail=[
                    {
                        "type": "value_error",
                        "loc": ["body", "file"],
                        "msg": "Invalid file format. Must be .xlsx",
                        "input": file.filename,
                        "url": "https://errors.pydantic.dev/2.5/v/value_error"
                    }
                ]
            )

        # Validate template type if provided
        if template_type:
            valid_types = ParserFactory.get_supported_template_types()
            if template_type.upper() not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid template type. Must be one of: {', '.join(valid_types)}"
                )
            template_type = template_type.upper()

        # Validasi file size
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=413,
                detail="File size exceeds maximum allowed limit of 10MB"
            )

        # Mock User ID
        mock_user = db.query(models.User).first()
        if not mock_user:
            mock_user = models.User(email="admin@company.com", password_hash="xxx", full_name="Admin")
            db.add(mock_user)
            db.commit()

        # Create Import Batch Record with template info
        new_batch = models.ImportBatch(
            user_id=mock_user.id,
            filename=file.filename,
            status='PROCESSING'
        )
        db.add(new_batch)
        db.commit()
        db.refresh(new_batch)

        # Enhanced background processing with template type
        background_tasks.add_task(
            process_upload_background_with_template,
            new_batch.id, content, template_type, db
        )

        response = create_upload_response(
            batch_id=str(new_batch.id),
            filename=file.filename,
            status=ResponseStatus.PROCESSING
        )

        return JSONResponse(content=response.dict(), status_code=201)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during file upload: {str(e)}"
        )

async def process_upload_background_with_template(
    batch_id: str,
    file_content: bytes,
    template_type: str = None,
    db: Session = None
):
    """Background processing with explicit template type support"""

    batch = db.query(models.ImportBatch).filter(models.ImportBatch.id == batch_id).first()

    try:
        # Use explicit template type if provided, otherwise auto-detect
        if template_type:
            print(f"Using explicit template type: {template_type}")
            parser = ParserFactory.create_parser(file_content, template_type)
        else:
            print("Auto-detecting template type...")
            parser = ParserFactory.create_parser(file_content)

        result = parser.process_file(batch_id=batch.id, document_id=str(batch.id))

        if result['errors']:
            batch.error_log = result['errors']

        # Handle Category
        cat_name = result['category_name']
        category = db.query(models.Category).filter(models.Category.name == cat_name).first()
        if not category:
            category = models.Category(name=cat_name, slug=slugify(cat_name))
            db.add(category)
            db.flush()

        # Insert Document with enhanced metadata
        new_doc = models.Document(
            import_batch_id=batch.id,
            category_id=category.id,
            title=result['title'],
            description=f"Imported from {batch.filename} ({result.get('template_type', 'Unknown')} template)",
            metadata_content=result['metadata'],
            status='ACTIVE'
        )
        db.add(new_doc)
        db.flush()

        # Handle Image Storage
        if result.get('extracted_images'):
            try:
                image_extractor = ImageExtractor(file_content, batch.id, str(new_doc.id))
                saved_images = image_extractor.save_images_to_database(db, result['extracted_images'])
                print(f"Saved {len(saved_images)} images to database")
            except Exception as e:
                print(f"Error saving images to database: {e}")

        # Update Batch Status with enhanced metrics
        batch.status = 'COMPLETED'
        batch.success_count = 1

        # Use appropriate parsing stats based on template type
        metadata = result.get('metadata', {})
        if result.get('template_type') == 'BA':
            batch.total_rows = metadata.get('parsing_stats', {}).get('total_us', 0)
        elif result.get('template_type') == 'UIUX':
            batch.total_rows = metadata.get('parsing_stats', {}).get('total_figma_links', 0)
        elif result.get('template_type') == 'ENGINEER':
            batch.total_rows = metadata.get('parsing_stats', {}).get('total_tech_stack', 0)

        db.commit()
        print(f"Batch {batch_id} completed successfully with template type: {result.get('template_type')}")

    except Exception as e:
        db.rollback()
        batch.status = 'FAILED'
        batch.error_log = {"critical_error": str(e)}
        batch.failed_count = 1
        db.commit()
        print(f"Batch {batch_id} failed: {e}")

@app.post("/validate-template")
async def validate_template(
    file: UploadFile = File(...),
    template_type: str = None
):
    """Validate Excel file against template(s)"""
    try:
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Must be .xlsx"
            )

        content = await file.read()

        # Validate template
        validation_results = ParserFactory.validate_template(content, template_type)

        # Auto-detect template type if not specified
        if template_type is None:
            detected_type = ParserFactory.detect_template_type(content)
            validation_results['detected_template_type'] = detected_type

        return {
            "status": "success",
            "filename": file.filename,
            "validation_results": validation_results
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating template: {str(e)}"
        )

@app.get("/templates/supported")
def get_supported_templates():
    """Get list of supported template types"""
    return {
        "status": "success",
        "supported_templates": ParserFactory.get_supported_template_types()
    }

@app.get("/batches/{batch_id}")
def get_batch_status(batch_id: str, db: Session = Depends(get_db)):
    """Get batch processing status and related documents with standardized response"""
    try:
        batch = db.query(models.ImportBatch).filter(models.ImportBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(
                status_code=404,
                detail=[
                    {
                        "type": "value_error",
                        "loc": ["path", "batch_id"],
                        "msg": "Batch not found",
                        "input": batch_id,
                        "url": "https://errors.pydantic.dev/2.5/v/value_error"
                    }
                ]
            )

        # Get related documents if batch is completed
        documents = []
        if batch.status == 'COMPLETED':
            docs = db.query(models.Document).filter(models.Document.import_batch_id == batch_id).all()
            for doc in docs:
                documents.append({
                    "id": doc.id,
                    "title": doc.title,
                    "category_id": doc.category_id,
                    "status": doc.status,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
                })

        # Prepare batch data
        batch_data = {
            "batch_id": batch.id,
            "filename": batch.filename,
            "status": batch.status,
            "total_rows": batch.total_rows or 0,
            "success_count": batch.success_count or 0,
            "failed_count": batch.failed_count or 0,
            "error_log": batch.error_log,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "documents": documents,
            "progress_percentage": calculate_progress(batch.status, batch.success_count or 0, batch.failed_count or 0)
        }

        # Return standardized response
        response = create_batch_response(batch_data)
        return JSONResponse(content=response.dict(), status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while retrieving batch status: {str(e)}"
        )

def calculate_progress(status: str, success_count: int, failed_count: int) -> int:
    """Calculate progress percentage for batch processing"""
    if status == 'PROCESSING':
        return 50
    elif status == 'COMPLETED':
        return 100
    elif status == 'FAILED':
        return 75  # Partial progress before failure
    else:
        return 0

@app.get("/batches")
def list_batches(
    limit: int = 10,
    page: int = 1,
    status: str = None,
    db: Session = Depends(get_db)
):
    """List all batches with pagination and optional filtering"""
    try:
        # Validate limit and page
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100"
            )
        if page < 1:
            raise HTTPException(
                status_code=400,
                detail="Page must be greater than 0"
            )

        # Calculate offset
        offset = (page - 1) * limit

        # Build query
        query = db.query(models.ImportBatch)

        if status:
            valid_statuses = ['PROCESSING', 'COMPLETED', 'FAILED']
            status = status.upper()
            if status not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"Status must be one of: {', '.join(valid_statuses)}"
                )
            query = query.filter(models.ImportBatch.status == status)

        # Get total count
        total = query.count()

        # Get batches with pagination
        batches = query.order_by(models.ImportBatch.created_at.desc()).offset(offset).limit(limit).all()

        # Format batch data
        batch_list = [
            {
                "id": batch.id,
                "filename": batch.filename,
                "status": batch.status,
                "success_count": batch.success_count or 0,
                "failed_count": batch.failed_count or 0,
                "total_rows": batch.total_rows or 0,
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "progress_percentage": calculate_progress(batch.status, batch.success_count or 0, batch.failed_count or 0)
            }
            for batch in batches
        ]

        # Return standardized response
        response = create_batch_list_response(batch_list, page, limit, total)
        return JSONResponse(content=response.dict(), status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while retrieving batch list: {str(e)}"
        )

@app.get("/documents/{doc_id}")
def get_document_detail(doc_id: str, db: Session = Depends(get_db)):
    """Get document details with standardized response"""
    try:
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=[
                    {
                        "type": "value_error",
                        "loc": ["path", "doc_id"],
                        "msg": "Document not found",
                        "input": doc_id,
                        "url": "https://errors.pydantic.dev/2.5/v/value_error"
                    }
                ]
            )

        # Get category info
        category = db.query(models.Category).filter(models.Category.id == doc.category_id).first()

        # Prepare document data
        document_data = {
            "id": doc.id,
            "title": doc.title,
            "description": doc.description,
            "category": {
                "id": category.id,
                "name": category.name,
                "slug": category.slug
            } if category else None,
            "parsed_data": doc.metadata_content,
            "status": doc.status,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            "parsing_completeness": calculate_document_completeness(doc.metadata_content)
        }

        # Return standardized response
        response = create_document_response(document_data)
        return JSONResponse(content=response.dict(), status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while retrieving document: {str(e)}"
        )

def calculate_document_completeness(metadata: dict) -> dict:
    """Calculate document completeness metrics"""
    if not metadata:
        return {
            "percentage": 0,
            "has_product_details": False,
            "has_user_stories": False,
            "has_acceptance_criteria": False,
            "has_business_values": False,
            "has_ba_approval": False
        }

    stats = metadata.get('parsing_stats', {})
    total_sections = 5  # product_details, user_stories, acceptance_criteria, business_values, ba_approval
    completed_sections = 0

    completed_sections += 1 if metadata.get('product_details') else 0
    completed_sections += 1 if stats.get('total_us', 0) > 0 else 0
    completed_sections += 1 if stats.get('total_ac', 0) > 0 else 0
    completed_sections += 1 if stats.get('total_bv', 0) > 0 else 0
    completed_sections += 1 if stats.get('has_ba_approval', False) else 0

    percentage = int((completed_sections / total_sections) * 100)

    return {
        "percentage": percentage,
        "has_product_details": bool(metadata.get('product_details')),
        "has_user_stories": stats.get('total_us', 0) > 0,
        "has_acceptance_criteria": stats.get('total_ac', 0) > 0,
        "has_business_values": stats.get('total_bv', 0) > 0,
        "has_ba_approval": stats.get('has_ba_approval', False)
    }